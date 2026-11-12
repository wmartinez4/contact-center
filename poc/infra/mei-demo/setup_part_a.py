#!/usr/bin/env python3
"""Part A of the contact-center demo on a Connect instance: queues, routing, agents,
recording storage, mock lookup Lambda and the inbound flow. Additive and re-runnable;
everything new is prefixed with DEMO_PREFIX (default `demo`). Never deletes anything.

Run:  AWS_PROFILE=connect-demo python3 setup_part_a.py
Test credentials are written to poc/.credentials.local (not printed).
"""
import copy
import io
import json
import os
import secrets
import string
import time
import zipfile

import boto3
from botocore.exceptions import ClientError

from flow_layout import layout
from names import (FLOW_NAMES, HOURS_NAME, QUEUE_NAMES, ROUTING_PROFILE_NAMES, old_hours_names, old_profile_names, queue_key,
                   old_queue_names, old_quick_connect_names, quick_connect_name, rename_legacy_flows)

REGION = os.environ.get("AWS_REGION", "us-east-1")
# Portable: point these at any Connect instance (see README.md). Defaults = the sandbox instance.
IID = os.environ.get("CONNECT_INSTANCE_ID", "9c58815e-2730-408e-b29d-ce7e52692cdc")
# Neutral prefix for every resource name. The first sandbox was built with DEMO_PREFIX=mei; keep using that value there.
PREFIX = os.environ.get("DEMO_PREFIX", "demo")
HERE = os.path.dirname(os.path.abspath(__file__))
POC = os.path.abspath(os.path.join(HERE, "..", ".."))

sess = boto3.Session(region_name=REGION)
account = sess.client("sts").get_caller_identity()["Account"]
if os.environ.get("EXPECTED_ACCOUNT"):
    assert account == os.environ["EXPECTED_ACCOUNT"], "Wrong AWS account: " + account
connect = sess.client("connect")
lam = sess.client("lambda")
iam = sess.client("iam")
s3 = sess.client("s3")
INSTANCE_ARN = f"arn:aws:connect:{REGION}:{account}:instance/{IID}"
# Every number claimed on the instance gets the inbound flow; the first one is the outbound caller ID.
PHONE_IDS = [p["PhoneNumberId"] for p in connect.list_phone_numbers_v2(TargetArn=INSTANCE_ARN)["ListPhoneNumbersSummaryList"]]
assert PHONE_IDS, "Claim at least one phone number on the instance first"
PHONE_ID = PHONE_IDS[0]

QUEUES = ["Q-Current", "Q-1-8", "Q-9-15", "Q-16-30", "Q-31Plus", "Q-Redemptions", "Q-EPD", "Q-Fallback", "Q-CallerOnly"]
FRONT = ["Q-Current", "Q-1-8", "Q-9-15", "Q-16-30", "Q-31Plus", "Q-Fallback"]
SPECIALIST = ["Q-Redemptions", "Q-EPD"]


def log(msg):
    print(msg, flush=True)


# ---------- recording storage ----------
def setup_recordings():
    bucket = f"amazon-connect-{PREFIX}-recordings-{account}"
    try:
        s3.create_bucket(Bucket=bucket)
        s3.put_public_access_block(Bucket=bucket, PublicAccessBlockConfiguration={
            "BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True})
        log(f"bucket created: {bucket}")
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou",):
            raise
    existing = connect.list_instance_storage_configs(InstanceId=IID, ResourceType="CALL_RECORDINGS")["StorageConfigs"]
    if not existing:
        connect.associate_instance_storage_config(InstanceId=IID, ResourceType="CALL_RECORDINGS", StorageConfig={
            "StorageType": "S3", "S3Config": {"BucketName": bucket, "BucketPrefix": f"{PREFIX}/CallRecordings"}})
        log("CALL_RECORDINGS storage associated")
    else:
        log("CALL_RECORDINGS storage already configured")


# ---------- queues, routing profiles ----------
def hours_id():
    old = old_hours_names(PREFIX)
    for h in connect.list_hours_of_operations(InstanceId=IID)["HoursOfOperationSummaryList"]:
        if h["Name"] in (HOURS_NAME,) + old:
            if h["Name"] in old:
                connect.update_hours_of_operation(InstanceId=IID, HoursOfOperationId=h["Id"], Name=HOURS_NAME)
            return h["Id"]
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    r = connect.create_hours_of_operation(
        InstanceId=IID, Name=HOURS_NAME, Description="Open 24/7", TimeZone="America/Chicago",
        Config=[{"Day": d, "StartTime": {"Hours": 0, "Minutes": 0}, "EndTime": {"Hours": 23, "Minutes": 59}} for d in days])
    log("hours of operation created: 24/7")
    return r["HoursOfOperationId"]


def ensure_queue(name, hours):
    full, old = QUEUE_NAMES[name], old_queue_names(name, PREFIX)
    for q in connect.list_queues(InstanceId=IID, QueueTypes=["STANDARD"])["QueueSummaryList"]:
        if q["Name"] in (full,) + old:
            if q["Name"] != full:
                connect.update_queue_name(InstanceId=IID, QueueId=q["Id"], Name=full, Description=full)
                log(f"queue renamed: {q['Name']} -> {full}")
            return q["Id"], q["Arn"]
    kwargs = dict(InstanceId=IID, Name=full, Description=full, HoursOfOperationId=hours)
    try:
        r = connect.create_queue(OutboundCallerConfig={"OutboundCallerIdName": "Collections", "OutboundCallerIdNumberId": PHONE_ID}, **kwargs)
    except ClientError as e:
        log(f"  outbound caller config rejected ({e.response['Error']['Code']}); creating without")
        r = connect.create_queue(**kwargs)
    log(f"queue created: {full}")
    return r["QueueId"], r["QueueArn"]


def ensure_routing_profile(name, queue_ids, names, default_outbound):
    full, old = ROUTING_PROFILE_NAMES[name], old_profile_names(name, PREFIX)
    for p in connect.list_routing_profiles(InstanceId=IID)["RoutingProfileSummaryList"]:
        if p["Name"] in (full,) + old:
            if p["Name"] != full:
                connect.update_routing_profile_name(InstanceId=IID, RoutingProfileId=p["Id"], Name=full, Description=full)
                log(f"routing profile renamed: {p['Name']} -> {full}")
            return p["Id"]
    r = connect.create_routing_profile(
        InstanceId=IID, Name=full, Description=full,
        DefaultOutboundQueueId=default_outbound,
        MediaConcurrencies=[{"Channel": "VOICE", "Concurrency": 1}],
        QueueConfigs=[{"QueueReference": {"QueueId": queue_ids[n], "Channel": "VOICE"}, "Priority": 1, "Delay": 0} for n in names])
    log(f"routing profile created: {full}")
    return r["RoutingProfileId"]


# ---------- agents ----------
def ensure_user(username, first, last, routing_id, security_id, creds):
    for u in connect.list_users(InstanceId=IID)["UserSummaryList"]:
        if u["Username"] == username:
            return u["Id"]
    alphabet = string.ascii_letters + string.digits
    pwd = "".join(secrets.choice(string.ascii_uppercase) for _ in range(2)) + "".join(secrets.choice(alphabet) for _ in range(10)) + \
        "".join(secrets.choice(string.digits) for _ in range(2)) + "!x"
    r = connect.create_user(
        InstanceId=IID, Username=username, Password=pwd, IdentityInfo={"FirstName": first, "LastName": last},
        PhoneConfig={"PhoneType": "SOFT_PHONE", "AutoAccept": True, "AfterContactWorkTimeLimit": 60},
        SecurityProfileIds=[security_id], RoutingProfileId=routing_id)
    creds[username] = pwd
    log(f"user created: {username}")
    return r["UserId"]


# ---------- lambda ----------
def ensure_lambda_role():
    name = f"{PREFIX}-lambda-role"
    try:
        return iam.get_role(RoleName=name)["Role"]["Arn"]
    except ClientError:
        pass
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    arn = iam.create_role(RoleName=name, AssumeRolePolicyDocument=json.dumps(trust), Description="Demo lookup Lambda")["Role"]["Arn"]
    iam.attach_role_policy(RoleName=name, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    log("lambda role created; waiting for propagation")
    time.sleep(12)
    return arn


def build_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(HERE, "lookup_handler.py"), "lookup_handler.py")
        z.write(os.path.join(POC, "data", "personas.json"), "personas.json")
    return buf.getvalue()


def ensure_lambda(queue_arns, prompts):
    name = f"{PREFIX}-lookup"
    role = ensure_lambda_role()
    ann_ids = {k: a.split("/")[-1] for k, a in prompts.items() if k.startswith("ann_")}
    env = {"Variables": {"QUEUE_ARNS": json.dumps(queue_arns), "PROMPT_IDS": json.dumps(ann_ids), "PROFILES_DOMAIN": "amazon-connect-cs-connect-demo"}}
    code = build_zip()
    try:
        lam.get_function(FunctionName=name)
        lam.update_function_code(FunctionName=name, ZipFile=code)
        lam.get_waiter("function_updated").wait(FunctionName=name)
        lam.update_function_configuration(FunctionName=name, Environment=env)
        log("lambda updated")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        lam.create_function(FunctionName=name, Runtime="python3.13", Role=role, Handler="lookup_handler.handler",
                            Code={"ZipFile": code}, Timeout=8, MemorySize=128, Environment=env,
                            Description="Demo simulated lookup and routing rules")
        log("lambda created")
    arn = lam.get_function(FunctionName=name)["Configuration"]["FunctionArn"]
    lam.get_waiter("function_active_v2").wait(FunctionName=name)
    try:
        lam.add_permission(FunctionName=name, StatementId=f"{PREFIX}-connect-invoke", Action="lambda:InvokeFunction",
                           Principal="connect.amazonaws.com", SourceArn=INSTANCE_ARN, SourceAccount=account)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceConflictException":
            raise
    try:
        connect.associate_lambda_function(InstanceId=IID, FunctionArn=arn)
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("ResourceConflictException", "InvalidRequestException"):
            raise
    return arn


# ---------- inbound flow ----------
NM, NC, TO = "NoMatchingError", "NoMatchingCondition", "InputTimeLimitExceeded"


def err(target, *types):
    return [{"NextAction": target, "ErrorType": t} for t in types]


def act(ident, typ, params, nxt=None, errors=None, conds=None):
    tr = {}
    if nxt is not None:
        tr = {"NextAction": nxt, "Errors": errors or [], "Conditions": conds or []}
    return {"Identifier": ident, "Type": typ, "Parameters": params, "Transitions": tr}


def eq(target, value):
    return {"NextAction": target, "Condition": {"Operator": "Equals", "Operands": [value]}}


def say(prompts, key, text):
    """Play the imported audio prompt when it exists; otherwise read the same text with Polly."""
    arn = prompts.get(key)
    return {"PromptId": arn} if arn else {"Text": text}


# Generative post-contact summary in both languages: AWS lists es-US as supported for post-contact summaries
# (adminguide/supported-languages, read 2026-11-10). SUMMARY_ES=0 turns it off for Spanish.
SUMMARY_ES = os.environ.get("SUMMARY_ES", "1") == "1"


def lens(ident, lang, nxt, summary):
    """Recording plus Contact Lens post-call analytics (transcript, sentiment and, optionally, a generative summary)."""
    analytics = {"Enabled": "True", "AnalyticsLanguage": lang, "AnalyticsModes": ["PostContact"],
                 "SentimentConfiguration": {"Enabled": "False"}}  # sentiment off since 2026-11-10; transcript, summary and categories stay on
    if summary:
        analytics["SummaryConfiguration"] = {"SummaryModes": ["PostContact"]}
    return act(ident, "UpdateContactRecordingAndAnalyticsBehavior", {"VoiceBehavior": {
        "VoiceRecordingBehavior": {"RecordedParticipants": ["Agent", "Customer"], "IVRRecordingBehavior": "Enabled"},
        "VoiceAnalyticsBehavior": analytics}}, nxt, err(nxt, NM, "ChannelMismatch"))


def build_flow(lookup_arn, hook_arns, prompts, guide_arn, wrapup_arn):
    P = lambda key, text: say(prompts, key, text)

    def menu(key, text, secs):
        d = P(key, text)
        d.update({"StoreInput": "False", "InputTimeLimitSeconds": secs})
        return d

    a = [
        act("LogOn", "UpdateFlowLoggingBehavior", {"FlowLoggingBehavior": "Enabled"}, "Rec", []),
        # Recording of agent, customer and the automated part (menu, queue). Syntax read back from a flow saved in the designer.
        act("Rec", "UpdateContactRecordingAndAnalyticsBehavior", {"VoiceBehavior": {
            "VoiceRecordingBehavior": {"RecordedParticipants": ["Agent", "Customer"], "IVRRecordingBehavior": "Enabled"},
            "VoiceAnalyticsBehavior": {"Enabled": "False"}}}, "Master", err("Master", NM, "ChannelMismatch")),
        # master call id, written once on the first leg
        act("Master", "UpdateContactAttributes", {"Attributes": {"master_call_id": "$.ContactId", "language": "en", "department": "Collections"}}, "ByPhone", err("Bye", NM)),
        # Known caller (ANI lookup, as iDMS would do): personal greeting in the customer's language, no menus
        act("ByPhone", "InvokeLambdaFunction", {
            "LambdaFunctionARN": lookup_arn, "InvocationTimeLimitSeconds": "8",
            "LambdaInvocationAttributes": {"phone": "$.CustomerEndpoint.Address"},
            "ResponseValidation": {"ResponseType": "STRING_MAP"}}, "IsKnown", err("NoticeEn", NM)),
        act("IsKnown", "Compare", {"ComparisonValue": "$.External.found"}, "NoticeEn", err("NoticeEn", NC), [eq("KnownSet", "true")]),
        act("KnownSet", "UpdateContactAttributes", {"Attributes": {
            "identifiedBy": "phone", "caseCode": "$.External.accountCode", "language": "$.External.language",
            "customerName": "$.External.customerName", "daysPastDue": "$.External.daysPastDue",
            "specialStatus": "$.External.specialStatus", "queueName": "$.External.queueName",
            "queueArn": "$.External.queueArn", "announceText": "$.External.announceText",
            "customerSummary": "$.External.customerSummary", "queueLabel": "$.External.queueLabel"}}, "KnownLang", err("NoticeEn", NM)),
        # No profileSearchKey here: the agent workspace's default search by caller number finds the profile
        # (with "_account" it showed "Cannot search for customer identifier" on 2026-11-10).
        act("KnownLang", "Compare", {"ComparisonValue": "$.Attributes.language"}, "KVoiceEn", err("KVoiceEn", NC), [eq("KVoiceEs", "es")]),
        act("KVoiceEn", "UpdateContactTextToSpeechVoice", {"TextToSpeechVoice": "Danielle", "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"}, "KLensEn", err("KLensEn", NM)),
        act("KVoiceEs", "UpdateContactTextToSpeechVoice", {"TextToSpeechVoice": "Lupe", "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"}, "KLensEs", err("KLensEs", NM)),
        lens("KLensEn", "en-US", "KNoticeEn", summary=True),
        lens("KLensEs", "es-US", "KNoticeEs", summary=SUMMARY_ES),
        act("KNoticeEn", "MessageParticipant", P("notice_en", "This call may be recorded."), "KGreet", err("KGreet", NM)),
        act("KNoticeEs", "MessageParticipant", P("notice_es", "Esta llamada puede ser grabada."), "KGreet", err("KGreet", NM)),
        act("KGreet", "MessageParticipant", {"Text": "$.Attributes.announceText"}, "SetQueue", err("SetQueue", NM)),
        act("NoticeEn", "MessageParticipant", P("notice_en", "This call may be recorded."), "LangMenu", err("LangMenu", NM)),
        # One audio with both languages, so there is no dead air between them
        act("LangMenu", "GetParticipantInput", menu("menu_both", "Thank you for calling. For English, press one. Para español, oprima dos.", "8"),
            "LangMenu", err("LangMenu", NM, NC, TO), [eq("LangEn", "1"), eq("LangEs", "2")]),
        act("LangEn", "UpdateContactAttributes", {"Attributes": {"language": "en"}}, "VoiceEn", err("Bye", NM)),
        act("LangEs", "UpdateContactAttributes", {"Attributes": {"language": "es"}}, "NoticeEsAfter", err("Bye", NM)),
        act("NoticeEsAfter", "MessageParticipant", P("notice_es", "Esta llamada puede ser grabada."), "VoiceEs", err("VoiceEs", NM)),
        act("VoiceEn", "UpdateContactTextToSpeechVoice", {"TextToSpeechVoice": "Danielle", "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"}, "LensEn", err("LensEn", NM)),
        act("VoiceEs", "UpdateContactTextToSpeechVoice", {"TextToSpeechVoice": "Lupe", "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"}, "LensEs", err("LensEs", NM)),
        lens("LensEn", "en-US", "CaseMenuEn", summary=True),
        lens("LensEs", "es-US", "CaseMenuEs", summary=SUMMARY_ES),
    ]
    for lang, key, text in (("En", "case_en", "Please enter your account number."), ("Es", "case_es", "Por favor, marque su número de cuenta.")):
        a.append(act(f"CaseMenu{lang}", "GetParticipantInput", menu(key, text, "10"),
                     f"CaseMenu{lang}", err(f"CaseMenu{lang}", NM, NC, TO), [eq(f"Case{lang}{k}", str(k)) for k in range(1, 8)]))
        for k in range(1, 8):
            a.append(act(f"Case{lang}{k}", "UpdateContactAttributes", {"Attributes": {
                # No profileSearchKey: the workspace's profile search by account failed ("t.includes is not a
                # function", 2026-11-10). The "Customer on the line" guide shows the account instead.
                # profileSearchKey / profileSearchValue are NOT set: on 2026-11-11 the agent workspace received them as
                # objects ("Cannot search for customer identifier: [object Object]") and left the search box empty.
                "caseCode": str(k), "identifiedBy": "case menu"}}, "Lookup", err("Bye", NM)))
    a += [
        act("Lookup", "InvokeLambdaFunction", {
            "LambdaFunctionARN": lookup_arn, "InvocationTimeLimitSeconds": "8",
            "LambdaInvocationAttributes": {"caseCode": "$.Attributes.caseCode", "language": "$.Attributes.language",
                                          "callerPhone": "$.CustomerEndpoint.Address"},  # the Lambda links it to the profile (lookup_handler.link_phone)
            "ResponseValidation": {"ResponseType": "STRING_MAP"}}, "SetAttrs", err("Bye", NM)),
        act("SetAttrs", "UpdateContactAttributes", {"Attributes": {
            "customerName": "$.External.customerName", "daysPastDue": "$.External.daysPastDue",
            "specialStatus": "$.External.specialStatus", "queueName": "$.External.queueName",
            "queueArn": "$.External.queueArn", "announceText": "$.External.announceText",
            "announcePromptArn": "$.External.announcePromptArn",
            "customerSummary": "$.External.customerSummary", "queueLabel": "$.External.queueLabel"}}, "Announce", err("Bye", NM)),
    ]
    # Generic announcement (no queue name, 2026-11-11): the Lambda returns the audio ann_generic_* / ann_notfound_*; the text is the fallback
    a.append(act("Announce", "MessageParticipant", {"PromptId": "$.Attributes.announcePromptArn"}, "SetQueue", err("AnnounceText", NM)))
    a.append(act("AnnounceText", "MessageParticipant", {"Text": "$.Attributes.announceText"}, "SetQueue", err("SetQueue", NM)))
    a += [
        act("SetQueue", "UpdateContactTargetQueue", {"QueueId": "$.Attributes.queueArn"}, "HookSwitch", err("Bye", NM)),
        act("HookSwitch", "Compare", {"ComparisonValue": "$.Attributes.language"}, "HookEn", err("HookEn", NC), [eq("HookEs", "es")]),
        act("HookEn", "UpdateContactEventHooks", {"EventHooks": {"CustomerQueue": hook_arns["en"]}}, "GuideHook", err("GuideHook", NM)),
        act("HookEs", "UpdateContactEventHooks", {"EventHooks": {"CustomerQueue": hook_arns["es"]}}, "GuideHook", err("GuideHook", NM)),
        # The agent who answers sees "Customer on the line" (summary, account, status) in the workspace
        act("GuideHook", "UpdateContactEventHooks", {"EventHooks": {"DefaultAgentUI": guide_arn, "DisconnectAgentUI": wrapup_arn}},
            "Transfer", err("Transfer", NM)),
        act("Transfer", "TransferContactToQueue", {}, "Bye", err("Bye", NM, "QueueAtCapacity")),
        act("Bye", "DisconnectParticipant", {}),
    ]
    return json.dumps(layout({"Version": "2019-10-30", "StartAction": "LogOn", "Metadata": {}, "Actions": a}))


def load_prompt_arns():
    out, tok = {}, None
    while True:
        r = connect.list_prompts(InstanceId=IID, **({"NextToken": tok} if tok else {}))
        for p in r["PromptSummaryList"]:
            if p["Name"].startswith(f"{PREFIX}-p-"):
                out[p["Name"][len(f"{PREFIX}-p-"):]] = p["Arn"]
        tok = r.get("NextToken")
        if not tok:
            return out


def ensure_queue_flows(prompts):
    """Customer queue flows (offer a callback while waiting) in English and Spanish, derived from the AWS sample."""
    sample = next(f for f in connect.list_contact_flows(InstanceId=IID, ContactFlowTypes=["CUSTOMER_QUEUE"])["ContactFlowSummaryList"]
                  if f["Name"] == "Sample interruptible queue flow with callback")
    if not prompts.get("cb_offer_en"):
        return {"en": sample["Arn"], "es": sample["Arn"]}
    base = json.loads(connect.describe_contact_flow(InstanceId=IID, ContactFlowId=sample["Id"])["ContactFlow"]["Content"])
    texts = {"Press 1 if you want to receieve a callback when an agent is available. Press 2 to remain in queue": "cb_offer",
             "The number entered is invalid. Please try again.": "cb_invalid",
             "Enter the number you would like to be called back at.": "cb_enter",
             "Something went wrong. Goodbye.": "cb_error",
             "You will be called back when the next agent is available.": "cb_confirm"}
    out = {}
    for lang in ("en", "es"):
        content = copy.deepcopy(base)
        for act_ in content["Actions"]:
            key = texts.get(act_["Parameters"].get("Text"))
            if key and prompts.get(f"{key}_{lang}"):
                del act_["Parameters"]["Text"]
                act_["Parameters"]["PromptId"] = prompts[f"{key}_{lang}"]
        name = FLOW_NAMES[f"queue-callback-{lang}"]
        existing = next((f for f in connect.list_contact_flows(InstanceId=IID, ContactFlowTypes=["CUSTOMER_QUEUE"])["ContactFlowSummaryList"] if f["Name"] == name), None)
        if existing:
            connect.update_contact_flow_content(InstanceId=IID, ContactFlowId=existing["Id"], Content=json.dumps(content))
            out[lang] = existing["Arn"]
        else:
            r = connect.create_contact_flow(InstanceId=IID, Name=name, Type="CUSTOMER_QUEUE", Content=json.dumps(content), Description="Demo: callback offer while waiting")
            out[lang] = r["ContactFlowArn"]
            log(f"customer queue flow created: {name}")
    return out


def ensure_flow(name, content):
    for f in connect.list_contact_flows(InstanceId=IID, ContactFlowTypes=["CONTACT_FLOW"])["ContactFlowSummaryList"]:
        if f["Name"] == name:
            connect.update_contact_flow_content(InstanceId=IID, ContactFlowId=f["Id"], Content=content)
            log(f"flow updated: {name}")
            return f["Id"]
    r = connect.create_contact_flow(InstanceId=IID, Name=name, Type="CONTACT_FLOW", Content=content,
                                    Description="Demo inbound: language, case, lookup, routing")
    log(f"flow created: {name}")
    return r["ContactFlowId"]


def ensure_outbound_whisper(qids):
    """Recording for contacts the system dials (callbacks): turned on in the queues' outbound whisper flow."""
    name = FLOW_NAMES["outbound-whisper"]
    content = json.dumps({"Version": "2019-10-30", "StartAction": "Rec", "Metadata": {}, "Actions": [
        act("Rec", "UpdateContactRecordingBehavior", {"RecordingBehavior": {"RecordedParticipants": ["Agent", "Customer"]}}, "End", []),
        act("End", "EndFlowExecution", {}),
    ]})
    fid = next((f["Id"] for f in connect.list_contact_flows(InstanceId=IID, ContactFlowTypes=["OUTBOUND_WHISPER"])["ContactFlowSummaryList"] if f["Name"] == name), None)
    if fid:
        connect.update_contact_flow_content(InstanceId=IID, ContactFlowId=fid, Content=content)
    else:
        fid = connect.create_contact_flow(InstanceId=IID, Name=name, Type="OUTBOUND_WHISPER", Content=content, Description="Demo: record callbacks")["ContactFlowId"]
        log(f"outbound whisper flow created: {name}")
    for qn, qid in qids.items():
        cfg = connect.describe_queue(InstanceId=IID, QueueId=qid)["Queue"].get("OutboundCallerConfig", {})
        cfg = {k: v for k, v in cfg.items() if k in ("OutboundCallerIdName", "OutboundCallerIdNumberId")}
        cfg["OutboundFlowId"] = fid
        cfg["OutboundCallerIdName"] = "Collections"
        connect.update_queue_outbound_caller_config(InstanceId=IID, QueueId=qid, OutboundCallerConfig=cfg)
    log(f"outbound whisper flow set on {len(qids)} queues")


def main():
    rename_legacy_flows(connect, IID, PREFIX)
    setup_recordings()
    hours = hours_id()
    qids, qarns = {}, {}
    for n in QUEUES:
        qids[n], qarns[n] = ensure_queue(n, hours)
    ensure_outbound_whisper(qids)
    front = ensure_routing_profile("front-line", qids, FRONT, qids["Q-Fallback"])
    spec = ensure_routing_profile("specialist", qids, SPECIALIST, qids["Q-Redemptions"])
    sec = next(p["Id"] for p in connect.list_security_profiles(InstanceId=IID)["SecurityProfileSummaryList"] if p["Name"] == "Agent")
    creds = {}
    ensure_user(f"{PREFIX}.agent1", "Agent 1", "Front Line", front, sec, creds)
    ensure_user(f"{PREFIX}.agent2", "Agent 2", "Specialist", spec, sec, creds)
    sup_sec = next((p["Id"] for p in connect.list_security_profiles(InstanceId=IID)["SecurityProfileSummaryList"] if p["Name"] == "CallCenterManager"), sec)
    basic_rp = next((p["Id"] for p in connect.list_routing_profiles(InstanceId=IID)["RoutingProfileSummaryList"] if p["Name"] == "Basic Routing Profile"), front)  # supervisor must not receive Collections calls
    sup_id = ensure_user(f"{PREFIX}.supervisor", "Supervisor", "Collections", basic_rp, sup_sec, creds)
    connect.update_user_security_profiles(InstanceId=IID, UserId=sup_id, SecurityProfileIds=sorted({sec, sup_sec}))  # manager + agent (CCP access)
    # Test caller: dials the instance's own number from the browser (no phone needed). No inbound queues,
    # so it never catches its own call.
    caller_rp = ensure_routing_profile("caller", qids, ["Q-CallerOnly"], qids["Q-CallerOnly"])
    ensure_user(f"{PREFIX}.caller", "Test Caller", "Line", caller_rp, sec, creds)
    if creds:
        path = os.path.join(POC, ".credentials.local")
        with open(path, "a") as f:
            for u, p in creds.items():
                f.write(f"{u}\t{p}\n")
        os.chmod(path, 0o600)
        log(f"credentials for {list(creds)} written to {path}")
    # quick connects: front line -> specialist queues
    qt = next(f["Id"] for f in connect.list_contact_flows(InstanceId=IID, ContactFlowTypes=["QUEUE_TRANSFER"])["ContactFlowSummaryList"] if f["Name"] == "Default queue transfer")
    existing = {q["Name"]: q["Id"] for q in connect.list_quick_connects(InstanceId=IID)["QuickConnectSummaryList"]}
    qcs = []
    for qn in SPECIALIST + ["Q-9-15"]:
        nm = quick_connect_name(qn)
        for legacy in old_quick_connect_names(qn, PREFIX):
            if legacy in existing and nm not in existing:
                connect.update_quick_connect_name(InstanceId=IID, QuickConnectId=existing[legacy], Name=nm, Description=nm)
                existing[nm] = existing.pop(legacy)
                log(f"quick connect renamed: {legacy} -> {nm}")
        if nm not in existing:
            existing[nm] = connect.create_quick_connect(InstanceId=IID, Name=nm, Description=f"Transfer to {qn}", QuickConnectConfig={
                "QuickConnectType": "QUEUE", "QueueConfig": {"QueueId": qids[qn], "ContactFlowId": qt}})["QuickConnectId"]
            log(f"quick connect created: {nm}")
        qcs.append(existing[nm])
    for qn in FRONT + SPECIALIST:
        try:
            connect.associate_queue_quick_connects(InstanceId=IID, QueueId=qids[qn], QuickConnectIds=qcs)
        except ClientError as e:
            log(f"  quick connect association on {qn}: {e.response['Error']['Code']}")
    prompts = load_prompt_arns()
    log(f"audio prompts found: {len(prompts)}" + ("" if prompts else " (run build_prompts.py to use recorded voices; Polly reads the text meanwhile)"))
    lam_arn = ensure_lambda(qarns, prompts)
    hooks = ensure_queue_flows(prompts)
    import setup_guide_flow  # imported here: it imports this module
    import setup_wrapup
    guide_arn = setup_guide_flow.ensure("guide-customer")
    flow_id = ensure_flow(FLOW_NAMES["inbound"], build_flow(lam_arn, hooks, prompts, guide_arn, setup_wrapup.ensure()))
    ai_file = os.path.join(POC, ".ai_bot.json")
    ai_phone = json.load(open(ai_file)).get("phoneId") if os.path.exists(ai_file) else None  # that number belongs to the AI flow
    # Numbers described as the AI line or the sandbox line keep their own flows
    def own_flow(pid):
        desc = connect.describe_phone_number(PhoneNumberId=pid)["ClaimedPhoneNumberSummary"].get("PhoneNumberDescription", "").lower()
        return desc.startswith(f"{PREFIX} sandbox") or desc.startswith(f"{PREFIX} ai")
    routed = [pid for pid in PHONE_IDS if pid != ai_phone and not own_flow(pid)]
    for pid in routed:
        connect.associate_phone_number_contact_flow(PhoneNumberId=pid, InstanceId=IID, ContactFlowId=flow_id)
    log(f"{len(routed)} phone number(s) now point to the inbound flow")
    log("done")


if __name__ == "__main__":
    main()
