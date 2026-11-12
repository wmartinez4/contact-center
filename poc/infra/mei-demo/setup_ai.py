#!/usr/bin/env python3
"""The demo AI agent: a Lex V2 bot using an Amazon Nova Sonic speech-to-speech model, in English and Spanish (US),
plus its fulfillment Lambda. Additive; nothing here is attached to a phone number (see setup_ai_flow in setup_part_a).

    AWS_PROFILE=<profile> CONNECT_INSTANCE_ID=<id> DEMO_PREFIX=demo python3 setup_ai.py
"""
import io
import json
import os
import time
import zipfile

import boto3

from names import queue_key
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_REGION", "us-east-1")
IID = os.environ["CONNECT_INSTANCE_ID"]
PREFIX = os.environ.get("DEMO_PREFIX", "demo")
MODEL = os.environ.get("SPEECH_MODEL", "amazon.nova-2-sonic-v1:0")
HERE = os.path.dirname(os.path.abspath(__file__))
POC = os.path.abspath(os.path.join(HERE, "..", ".."))

sess = boto3.Session(region_name=REGION)
account = sess.client("sts").get_caller_identity()["Account"]
if os.environ.get("EXPECTED_ACCOUNT"):
    assert account == os.environ["EXPECTED_ACCOUNT"], account
lex, lam, iam, connect = (sess.client(n) for n in ("lexv2-models", "lambda", "iam", "connect"))
INSTANCE_ARN = f"arn:aws:connect:{REGION}:{account}:instance/{IID}"
# A parallel bot (e.g. to try another speech model) gets its own name and record file; the Lambda is shared.
BOT_NAME = os.environ.get("BOT_NAME", f"{PREFIX}-assistant")
BOT_FILE = os.environ.get("BOT_FILE", ".ai_bot.json")
LOCALES = {
    "en_US": {"voice": "tiffany", "greet": "What is your account code?",
              "AccountInfo": ["I want to check my account", "check my account", "my account", "account information", "I need help with my account"],
              "Balance": ["what is my balance", "how much do I owe", "my balance", "balance", "what do I owe"],
              "DueDate": ["when is my payment due", "what is my due date", "due date", "when do I have to pay", "when is it due"],
              "PaymentOptions": ["how can I pay", "I want to pay", "pay my bill", "payment options", "how do I make a payment"],
              "TalkToAgent": ["agent", "representative", "I want to talk to a person", "let me speak to someone", "human", "operator"],
              "EndCall": ["no that is all", "that is all", "no thanks", "nothing else", "goodbye", "I am done", "no that's all"],
              "SwitchLanguage": ["Spanish please", "in Spanish", "can we speak in Spanish", "do you speak Spanish", "I prefer Spanish",
                                 "speak Spanish", "español", "en español", "habla español", "hablas español", "puede hablar en español"]},
    "es_US": {"voice": "lupe", "greet": "¿Cuál es su código de cuenta?",
              "AccountInfo": ["quiero revisar mi cuenta", "revisar mi cuenta", "mi cuenta", "información de mi cuenta", "necesito ayuda con mi cuenta"],
              "Balance": ["cuál es mi saldo", "cuánto debo", "mi saldo", "saldo", "qué debo"],
              "DueDate": ["cuándo vence mi pago", "cuál es mi fecha de pago", "fecha de pago", "cuándo tengo que pagar", "cuándo vence"],
              "PaymentOptions": ["cómo puedo pagar", "quiero pagar", "opciones de pago", "cómo hago un pago", "pagar mi cuenta"],
              "TalkToAgent": ["agente", "representante", "quiero hablar con una persona", "quiero hablar con alguien", "humano", "operador"],
              "EndCall": ["no eso es todo", "eso es todo", "no gracias", "nada más", "adiós", "ya terminé"],
              "SwitchLanguage": ["en inglés", "inglés por favor", "puede hablar en inglés", "habla inglés", "prefiero inglés",
                                 "hablemos en inglés", "English please", "in English", "do you speak English", "speak English"]},
}


def log(m):
    print(m, flush=True)


def wait(fn, ok, what, tries=60):
    for _ in range(tries):
        try:
            s = fn()
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
                raise
            time.sleep(3)
            continue
        if s in ok:
            return s
        if s.endswith("Failed") or s == "Failed":
            raise RuntimeError(f"{what} failed")
        time.sleep(3)
    raise RuntimeError(f"timeout waiting for {what}")


def lambda_arn():
    name = f"{PREFIX}-ai-dialog"
    role = f"{PREFIX}-lambda-role"
    role_arn = iam.get_role(RoleName=role)["Role"]["Arn"]
    queues = connect.list_queues(InstanceId=IID, QueueTypes=["STANDARD"])["QueueSummaryList"]
    qarns = {queue_key(q["Name"], PREFIX): q["Arn"] for q in queues if queue_key(q["Name"], PREFIX)}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("ai_dialog.py", "lookup_handler.py"):
            z.write(os.path.join(HERE, f), f)
        z.write(os.path.join(POC, "data", "personas.json"), "personas.json")
    env = {"Variables": {"QUEUE_ARNS": json.dumps(qarns)}}
    try:
        lam.get_function(FunctionName=name)
        lam.update_function_code(FunctionName=name, ZipFile=buf.getvalue())
        lam.get_waiter("function_updated").wait(FunctionName=name)
        lam.update_function_configuration(FunctionName=name, Environment=env)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        lam.create_function(FunctionName=name, Runtime="python3.13", Role=role_arn, Handler="ai_dialog.handler", Code={"ZipFile": buf.getvalue()},
                            Timeout=8, MemorySize=128, Environment=env, Description="Demo AI agent fulfillment")
        log("lambda created")
    lam.get_waiter("function_active_v2").wait(FunctionName=name)
    return lam.get_function(FunctionName=name)["Configuration"]["FunctionArn"]


def ensure_bot():
    for b in lex.list_bots()["botSummaries"]:
        if b["botName"] == BOT_NAME:
            return b["botId"]
    try:
        iam.create_service_linked_role(AWSServiceName="lexv2.amazonaws.com")
        time.sleep(8)
    except ClientError as e:
        if e.response["Error"]["Code"] != "InvalidInput":
            raise
    role = next(r["Arn"] for r in iam.list_roles(PathPrefix="/aws-service-role/lexv2.amazonaws.com/")["Roles"])
    bot_id = lex.create_bot(botName=BOT_NAME, roleArn=role, dataPrivacy={"childDirected": False}, idleSessionTTLInSeconds=300,
                            description="Demo AI agent: balance and due date, escalates to a person")["botId"]
    wait(lambda: lex.describe_bot(botId=bot_id)["botStatus"], ("Available",), "bot")
    log(f"bot created: {BOT_NAME}")
    return bot_id


def msg(text):
    return {"messageGroups": [{"message": {"plainTextMessage": {"value": text}}}], "maxRetries": 2, "allowInterrupt": True}


def build_locale(bot_id, loc, cfg, fn_arn):
    existing = {l["localeId"] for l in lex.list_bot_locales(botId=bot_id, botVersion="DRAFT")["botLocaleSummaries"]}
    if loc not in existing:
        lex.create_bot_locale(botId=bot_id, botVersion="DRAFT", localeId=loc, nluIntentConfidenceThreshold=0.4,
                              unifiedSpeechSettings={"speechFoundationModel": {"modelArn": f"arn:aws:bedrock:{REGION}::foundation-model/{MODEL}", "voiceId": cfg["voice"]}})
        wait(lambda: lex.describe_bot_locale(botId=bot_id, botVersion="DRAFT", localeId=loc)["botLocaleStatus"], ("NotBuilt",), f"locale {loc}")
        log(f"locale created: {loc}")
    intents = {i["intentName"]: i["intentId"] for i in lex.list_intents(botId=bot_id, botVersion="DRAFT", localeId=loc)["intentSummaries"]}
    hook = {"fulfillmentCodeHook": {"enabled": True}}
    base = dict(botId=bot_id, botVersion="DRAFT", localeId=loc)

    def utts(name):
        return [{"utterance": u} for u in cfg[name]]

    # AccountInfo: the only intent with a slot (the account code)
    if "AccountInfo" not in intents:
        iid = lex.create_intent(intentName="AccountInfo", sampleUtterances=utts("AccountInfo"), **hook, **base)["intentId"]
        lex.create_slot(intentId=iid, slotName="accountCode", slotTypeId="AMAZON.Number",
                        valueElicitationSetting={"slotConstraint": "Required", "promptSpecification": msg(cfg["greet"])}, **base)
    else:
        iid = intents["AccountInfo"]
    sid = lex.list_slots(intentId=iid, **base)["slotSummaries"][0]["slotId"]
    lex.update_intent(intentId=iid, intentName="AccountInfo", sampleUtterances=utts("AccountInfo"), slotPriorities=[{"priority": 1, "slotId": sid}], **hook, **base)
    for name in ("Balance", "DueDate", "PaymentOptions", "TalkToAgent", "EndCall", "SwitchLanguage"):
        if name not in intents:
            lex.create_intent(intentName=name, sampleUtterances=utts(name), **hook, **base)
        else:
            lex.update_intent(intentId=intents[name], intentName=name, sampleUtterances=utts(name), **hook, **base)
    fb = intents.get("FallbackIntent")
    if fb:
        lex.update_intent(botId=bot_id, botVersion="DRAFT", localeId=loc, intentId=fb, intentName="FallbackIntent",
                          parentIntentSignature="AMAZON.FallbackIntent", **hook)
    lex.build_bot_locale(botId=bot_id, botVersion="DRAFT", localeId=loc)
    wait(lambda: lex.describe_bot_locale(botId=bot_id, botVersion="DRAFT", localeId=loc)["botLocaleStatus"], ("Built",), f"build {loc}", tries=100)
    log(f"locale built: {loc}")


def main():
    fn_arn = lambda_arn()
    bot_id = ensure_bot()
    for loc, cfg in LOCALES.items():
        build_locale(bot_id, loc, cfg, fn_arn)
    ver = lex.create_bot_version(botId=bot_id, botVersionLocaleSpecification={l: {"sourceBotVersion": "DRAFT"} for l in LOCALES})["botVersion"]
    wait(lambda: lex.describe_bot_version(botId=bot_id, botVersion=ver)["botStatus"], ("Available",), "bot version")
    settings = {l: {"enabled": True, "codeHookSpecification": {"lambdaCodeHook": {"lambdaARN": fn_arn, "codeHookInterfaceVersion": "1.0"}}} for l in LOCALES}
    alias_id = next((a["botAliasId"] for a in lex.list_bot_aliases(botId=bot_id)["botAliasSummaries"] if a["botAliasName"] == "live"), None)
    if alias_id:
        lex.update_bot_alias(botId=bot_id, botAliasId=alias_id, botAliasName="live", botVersion=ver, botAliasLocaleSettings=settings)
    else:
        alias_id = lex.create_bot_alias(botId=bot_id, botAliasName="live", botVersion=ver, botAliasLocaleSettings=settings)["botAliasId"]
    alias_arn = f"arn:aws:lex:{REGION}:{account}:bot-alias/{bot_id}/{alias_id}"
    try:
        sid = f"{PREFIX}-lex-invoke" if BOT_NAME == f"{PREFIX}-assistant" else f"{PREFIX}-lex-invoke-{bot_id}"
        lam.add_permission(FunctionName=f"{PREFIX}-ai-dialog", StatementId=sid, Action="lambda:InvokeFunction",
                           Principal="lexv2.amazonaws.com", SourceArn=alias_arn, SourceAccount=account)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceConflictException":
            raise
    try:
        connect.associate_bot(InstanceId=IID, LexV2Bot={"AliasArn": alias_arn})
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("ResourceConflictException", "InvalidRequestException"):
            raise
    log(f"bot version {ver}, alias live: {alias_arn}")
    open(os.path.join(POC, BOT_FILE), "w").write(json.dumps({"botId": bot_id, "aliasId": alias_id, "aliasArn": alias_arn, "version": ver}))
    log("done")


if __name__ == "__main__":
    main()
