#!/usr/bin/env python3
"""Call tester: a Lex V2 bot with Nova Sonic speech whose code hook (poc/call-tester/tester.py) plays a customer with a
Bedrock model, plus the outbound flow "CS - Outbound - Call Tester" that connects the callee to it.

Re-runnable. Writes poc/call-tester/.state.json (gitignored).

    AWS_PROFILE=cs-admin python3 poc/infra/call-tester/setup.py
"""
import io
import json
import os
import sys
import time
import zipfile

import boto3
from botocore.exceptions import ClientError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mei-demo"))
from flow_layout import layout  # noqa: E402

REGION, ACCOUNT = "us-east-1", "383799408374"
IID = "c2f9ca2b-eb05-4a82-9809-1d7c914333ba"
NAME = "call-tester"
FLOW_NAME = "CS - Outbound - Call Tester"
SPEECH_MODEL = "amazon.nova-2-sonic-v1:0"
LOCALES = {"es_US": "lupe", "en_US": "tiffany"}
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CODE = os.path.join(ROOT, "poc", "call-tester")

s = boto3.Session(region_name=REGION)
assert s.client("sts").get_caller_identity()["Account"] == ACCOUNT
iam, lam, lex, connect = (s.client(n) for n in ("iam", "lambda", "lexv2-models", "connect"))


def log(m):
    print(m, flush=True)


def wait(fn, ok, what, tries=100):
    for _ in range(tries):
        try:
            state = fn()
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
                raise
            state = "Pending"  # a new bot version is not readable for a few seconds
        if state in ok:
            return
        if "Failed" in state:
            raise RuntimeError(f"{what}: {state}")
        time.sleep(3)
    raise RuntimeError(f"timeout: {what}")


def ensure_role():
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    try:
        arn = iam.create_role(RoleName=f"{NAME}-role", AssumeRolePolicyDocument=json.dumps(trust),
                              Tags=[{"Key": "project", "Value": NAME}])["Role"]["Arn"]
        time.sleep(10)
    except iam.exceptions.EntityAlreadyExistsException:
        arn = iam.get_role(RoleName=f"{NAME}-role")["Role"]["Arn"]
    iam.attach_role_policy(RoleName=f"{NAME}-role", PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    iam.put_role_policy(RoleName=f"{NAME}-role", PolicyName="bedrock", PolicyDocument=json.dumps({"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["bedrock:InvokeModel"], "Resource": "*"}]}))
    return arn


def ensure_lambda(role_arn):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("tester.py", "scenarios.json"):
            z.write(os.path.join(CODE, f), f)
    try:
        lam.update_function_code(FunctionName=NAME, ZipFile=buf.getvalue())
    except lam.exceptions.ResourceNotFoundException:
        for _ in range(5):
            try:
                lam.create_function(FunctionName=NAME, Runtime="python3.13", Role=role_arn, Handler="tester.handler",
                                    Code={"ZipFile": buf.getvalue()}, Timeout=20, MemorySize=256,
                                    Description="Simulated customer for scripted test calls", Tags={"project": NAME})
                break
            except lam.exceptions.InvalidParameterValueException:
                time.sleep(5)  # the new role is not yet assumable
        log("lambda created")
    lam.get_waiter("function_active_v2").wait(FunctionName=NAME)
    lam.get_waiter("function_updated_v2").wait(FunctionName=NAME)
    return lam.get_function(FunctionName=NAME)["Configuration"]["FunctionArn"]


def ensure_bot():
    found = next((b["botId"] for b in lex.list_bots()["botSummaries"] if b["botName"] == NAME), None)
    if found:
        return found
    role = next(r["Arn"] for r in iam.list_roles(PathPrefix="/aws-service-role/lexv2.amazonaws.com/")["Roles"])
    bot_id = lex.create_bot(botName=NAME, roleArn=role, dataPrivacy={"childDirected": False}, idleSessionTTLInSeconds=300,
                            description="Simulated customer for scripted test calls", botTags={"project": NAME})["botId"]
    wait(lambda: lex.describe_bot(botId=bot_id)["botStatus"], ("Available",), "bot")
    log("bot created")
    return bot_id


def build_locale(bot_id, loc, voice):
    base = dict(botId=bot_id, botVersion="DRAFT", localeId=loc)
    if loc not in {l["localeId"] for l in lex.list_bot_locales(botId=bot_id, botVersion="DRAFT")["botLocaleSummaries"]}:
        # A high threshold sends everything to FallbackIntent; the placeholder intent exists only because Lex needs one.
        lex.create_bot_locale(nluIntentConfidenceThreshold=0.99, unifiedSpeechSettings={"speechFoundationModel": {
            "modelArn": f"arn:aws:bedrock:{REGION}::foundation-model/{SPEECH_MODEL}", "voiceId": voice}}, **base)
        wait(lambda: lex.describe_bot_locale(**base)["botLocaleStatus"], ("NotBuilt",), f"locale {loc}")
    intents = {i["intentName"]: i["intentId"] for i in lex.list_intents(**base)["intentSummaries"]}
    hook = {"fulfillmentCodeHook": {"enabled": True}}
    if "Placeholder" not in intents:
        lex.create_intent(intentName="Placeholder", sampleUtterances=[{"utterance": "placeholder intent for the call tester"}], **hook, **base)
    lex.update_intent(intentId=intents["FallbackIntent"], intentName="FallbackIntent", parentIntentSignature="AMAZON.FallbackIntent", **hook, **base)
    lex.build_bot_locale(**base)
    wait(lambda: lex.describe_bot_locale(**base)["botLocaleStatus"], ("Built",), f"build {loc}")
    log(f"locale built: {loc}")


def publish(bot_id, fn_arn):
    ver = lex.create_bot_version(botId=bot_id, botVersionLocaleSpecification={l: {"sourceBotVersion": "DRAFT"} for l in LOCALES})["botVersion"]
    wait(lambda: lex.describe_bot_version(botId=bot_id, botVersion=ver)["botStatus"], ("Available",), "bot version")
    settings = {l: {"enabled": True, "codeHookSpecification": {"lambdaCodeHook": {"lambdaARN": fn_arn, "codeHookInterfaceVersion": "1.0"}}} for l in LOCALES}
    alias_id = next((a["botAliasId"] for a in lex.list_bot_aliases(botId=bot_id)["botAliasSummaries"] if a["botAliasName"] == "live"), None)
    if alias_id:
        lex.update_bot_alias(botId=bot_id, botAliasId=alias_id, botAliasName="live", botVersion=ver, botAliasLocaleSettings=settings)
    else:
        alias_id = lex.create_bot_alias(botId=bot_id, botAliasName="live", botVersion=ver, botAliasLocaleSettings=settings)["botAliasId"]
    alias_arn = f"arn:aws:lex:{REGION}:{ACCOUNT}:bot-alias/{bot_id}/{alias_id}"
    try:
        lam.add_permission(FunctionName=NAME, StatementId="lex-invoke", Action="lambda:InvokeFunction",
                           Principal="lexv2.amazonaws.com", SourceArn=f"arn:aws:lex:{REGION}:{ACCOUNT}:bot-alias/{bot_id}/*", SourceAccount=ACCOUNT)
    except lam.exceptions.ResourceConflictException:
        pass
    try:
        connect.associate_bot(InstanceId=IID, LexV2Bot={"AliasArn": alias_arn})
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("ResourceConflictException", "InvalidRequestException"):
            raise
    log(f"bot version {ver}, alias live")
    return alias_arn


def flow_content(alias_arn):
    end = [{"NextAction": "End", "ErrorType": t} for t in ("NoMatchingCondition", "NoMatchingError", "InputTimeLimitExceeded")]
    flow = {"Version": "2019-10-30", "StartAction": "Log", "Actions": [
        {"Identifier": "Log", "Type": "UpdateFlowLoggingBehavior", "Parameters": {"FlowLoggingBehavior": "Enabled"},
         "Transitions": {"NextAction": "Lang", "Errors": [], "Conditions": []}},
        # The contact's language picks the Lex locale.
        {"Identifier": "Lang", "Type": "Compare", "Parameters": {"ComparisonValue": "$.Attributes.lang"},
         "Transitions": {"NextAction": "CodeEn", "Errors": [{"NextAction": "CodeEn", "ErrorType": "NoMatchingCondition"}],
                         "Conditions": [{"NextAction": "CodeEs", "Condition": {"Operator": "Equals", "Operands": ["es"]}}]}},
        {"Identifier": "CodeEs", "Type": "UpdateContactData", "Parameters": {"LanguageCode": "es-US"},
         "Transitions": {"NextAction": "Bot", "Errors": [{"NextAction": "Bot", "ErrorType": "NoMatchingError"}], "Conditions": []}},
        {"Identifier": "CodeEn", "Type": "UpdateContactData", "Parameters": {"LanguageCode": "en-US"},
         "Transitions": {"NextAction": "Bot", "Errors": [{"NextAction": "Bot", "ErrorType": "NoMatchingError"}], "Conditions": []}},
        # The callee speaks first: the block needs a prompt, so it gets a silent one and then listens.
        {"Identifier": "Bot", "Type": "ConnectParticipantWithLexBot", "Parameters": {
            "SSML": '<speak><break time="500ms"/></speak>',
            "LexV2Bot": {"AliasArn": alias_arn},
            "LexSessionAttributes": {"scenario": "$.Attributes.scenario",
                                     "x-amz-lex:audio:start-timeout-ms:*:*": "20000"},
            "LexTimeoutSeconds": {"Text": "300"}},
         "Transitions": {"NextAction": "End", "Errors": end, "Conditions": []}},
        {"Identifier": "End", "Type": "DisconnectParticipant", "Parameters": {}, "Transitions": {}},
    ]}
    return json.dumps(layout(flow))


def ensure_flow(alias_arn):
    content = flow_content(alias_arn)
    flows = {f["Name"]: f["Id"] for p in connect.get_paginator("list_contact_flows").paginate(InstanceId=IID, ContactFlowTypes=["CONTACT_FLOW"])
             for f in p["ContactFlowSummaryList"]}
    if FLOW_NAME in flows:
        connect.update_contact_flow_content(InstanceId=IID, ContactFlowId=flows[FLOW_NAME], Content=content)
        return flows[FLOW_NAME]
    fid = connect.create_contact_flow(InstanceId=IID, Name=FLOW_NAME, Type="CONTACT_FLOW", Content=content,
                                      Description="Outbound test call: a simulated customer talks to the line it dials",
                                      Tags={"project": NAME})["ContactFlowId"]
    log("flow created")
    return fid


if __name__ == "__main__":
    fn = ensure_lambda(ensure_role())
    bot = ensure_bot()
    for loc, voice in LOCALES.items():
        build_locale(bot, loc, voice)
    alias = publish(bot, fn)
    flow_id = ensure_flow(alias)
    json.dump({"botId": bot, "aliasArn": alias, "flowId": flow_id}, open(os.path.join(CODE, ".state.json"), "w"), indent=2)
    log(f"flow {FLOW_NAME}: {flow_id}")
