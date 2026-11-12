#!/usr/bin/env python3
"""Contact flow of the AI agent: notice, language, the Lex bot (Nova Sonic) and, if it asks, a hand-over to a person.
Created but NOT attached to any number. To try it, point a number at it (see the printed id).

    AWS_PROFILE=<profile> CONNECT_INSTANCE_ID=<id> DEMO_PREFIX=demo python3 setup_ai_flow.py
"""
import json
import os

import setup_part_a as s

import setup_guide_flow

bot = json.load(open(os.path.join(s.POC, os.environ.get("BOT_FILE", ".ai_bot.json"))))
guide_arn = setup_guide_flow.ensure()
import setup_wrapup
wrapup_arn = setup_wrapup.ensure()
fallback_arn = next(q["Arn"] for q in s.connect.list_queues(InstanceId=s.IID, QueueTypes=["STANDARD"])["QueueSummaryList"]
                    if s.queue_key(q["Name"], s.PREFIX) == "Q-Fallback")
prompts = s.load_prompt_arns()
lookup_arn = s.lam.get_function(FunctionName=f"{s.PREFIX}-lookup")["Configuration"]["FunctionArn"]
hooks = s.ensure_queue_flows(prompts)
act, err, eq, NM, NC, TO, P = s.act, s.err, s.eq, s.NM, s.NC, s.TO, (lambda k, t: s.say(prompts, k, t))


def lex_block(ident, nxt, retry):
    retry_text = {"en": "I did not hear you. How can I help?", "es": "No le escuché. ¿En qué puedo ayudarle?"}
    greeting = {"en": "Hi, I am the automated assistant. I can tell you your balance and due date. How can I help?",
                "es": "Hola, soy el asistente automático. Puedo decirle su saldo y la fecha de pago. ¿En qué puedo ayudarle?"}
    return act(ident, "ConnectParticipantWithLexBot", {
        "Text": retry_text["es" if ident.endswith("Es") else "en"] if ident.startswith("LexRetry") else "$.Attributes.aiGreeting",
        "LexV2Bot": {"AliasArn": bot["aliasArn"]},
        "LexSessionAttributes": {"language": "$.Attributes.language", "accountCode": "$.Attributes.accountCode"},
        "LexTimeoutSeconds": {"Text": "120"}}, nxt, [
            {"NextAction": nxt, "ErrorType": NC}, {"NextAction": f"Check{ident}", "ErrorType": TO}, {"NextAction": f"Check{ident}", "ErrorType": NM}])


def lex_check(ident, retry):
    """The voice bot can end with "Error" even after it decided (2026-11-10: it said "I will connect you",
    then the block failed). Trust the outcome the bot left in its session; only retry when there is none."""
    return act(f"Check{ident}", "Compare", {"ComparisonValue": "$.Lex.SessionAttributes.outcome"}, retry, err(retry, NC),
               [eq("AfterLex", "escalate"), eq("AfterLex", "resolved"), eq("AfterLex", "switch_language")])


def lens(ident, lang, nxt):
    """Recording plus Contact Lens analytics for both parts of the call: the conversation with the AI agent
    ("Automated interaction") and the one with the person it hands over to, each with transcript, sentiment and summary."""
    block = s.lens(ident, lang, nxt, summary=(lang == "en-US" or s.SUMMARY_ES))
    va = block["Parameters"]["VoiceBehavior"]["VoiceAnalyticsBehavior"]
    va["AnalyticsModes"] = ["PostContact", "AutomatedInteraction"]
    if "SummaryConfiguration" in va:
        va["SummaryConfiguration"]["SummaryModes"] = ["PostContact", "AutomatedInteraction"]
    return block


a = [
    act("LogOn", "UpdateFlowLoggingBehavior", {"FlowLoggingBehavior": "Enabled"}, "Rec", []),
    act("Rec", "UpdateContactRecordingAndAnalyticsBehavior", {"VoiceBehavior": {
        "VoiceRecordingBehavior": {"RecordedParticipants": ["Agent", "Customer"], "IVRRecordingBehavior": "Enabled"},
        "VoiceAnalyticsBehavior": {"Enabled": "False"}}}, "Master", err("Master", NM, "ChannelMismatch")),
    act("Master", "UpdateContactAttributes", {"Attributes": {"master_call_id": "$.ContactId", "language": "en", "department": "Collections", "channelType": "ai-agent"}}, "ByPhone", err("Bye", NM)),
    # No language menu (2026-11-11): only the recording notice. A caller recognized by number is greeted by name in
    # their language and the bot already knows the account; otherwise a generic greeting in English (the caller can say "Spanish please").
    act("ByPhone", "InvokeLambdaFunction", {
        "LambdaFunctionARN": lookup_arn, "InvocationTimeLimitSeconds": "8",
        "LambdaInvocationAttributes": {"phone": "$.CustomerEndpoint.Address"},
        "ResponseValidation": {"ResponseType": "STRING_MAP"}}, "IsKnown", err("UnkSet", NM)),
    act("IsKnown", "Compare", {"ComparisonValue": "$.External.found"}, "UnkSet", err("UnkSet", NC), [eq("KnownSet", "true")]),
    act("KnownSet", "UpdateContactAttributes", {"Attributes": {
        "identifiedBy": "phone", "accountCode": "$.External.accountCode", "language": "$.External.language",
        "customerName": "$.External.customerName", "firstName": "$.External.firstName", "aiGreeting": "$.External.aiGreeting"}},
        "KnownLang", err("UnkSet", NM)),
    act("KnownLang", "Compare", {"ComparisonValue": "$.Attributes.language"}, "NoticeEn", err("NoticeEn", NC), [eq("NoticeEs", "es")]),
    act("NoticeEs", "MessageParticipant", P("notice_es", "Esta llamada puede ser grabada."), "CodeEs", err("CodeEs", NM)),
    act("UnkSet", "UpdateContactAttributes", {"Attributes": {
        "identifiedBy": "none", "language": "en", "aiGreeting": "Thank you for calling. How can I help you today?"}}, "NoticeEn", err("NoticeEn", NM)),
    act("NoticeEn", "MessageParticipant", P("notice_en", "This call may be recorded."), "CodeEn", err("CodeEn", NM)),
    act("CodeEn", "UpdateContactData", {"LanguageCode": "en-US"}, "LensEn", err("Bye", NM)),
    act("CodeEs", "UpdateContactData", {"LanguageCode": "es-US"}, "LensEs", err("Bye", NM)),
    lens("LensEn", "en-US", "VoiceEn"),
    lens("LensEs", "es-US", "VoiceEs"),
    act("VoiceEn", "UpdateContactTextToSpeechVoice", {"TextToSpeechVoice": "Danielle", "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"}, "LexEn", err("LexEn", NM)),
    act("VoiceEs", "UpdateContactTextToSpeechVoice", {"TextToSpeechVoice": "Lupe", "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"}, "LexEs", err("LexEs", NM)),
    lex_block("LexEn", "AfterLex", "LexRetryEn"),
    lex_block("LexEs", "AfterLex", "LexRetryEs"),
    lex_block("LexRetryEn", "AfterLex", "Bye"),
    lex_block("LexRetryEs", "AfterLex", "Bye"),
    lex_check("LexEn", "LexRetryEn"),
    lex_check("LexEs", "LexRetryEs"),
    lex_check("LexRetryEn", "AfterLex"),
    lex_check("LexRetryEs", "AfterLex"),
    act("AfterLex", "UpdateContactAttributes", {"Attributes": {
        "outcome": "$.Lex.SessionAttributes.outcome", "reason": "$.Lex.SessionAttributes.reason",
        "summary": "$.Lex.SessionAttributes.summary", "queueArn": "$.Lex.SessionAttributes.queueArn",
        "queueName": "$.Lex.SessionAttributes.queueName", "accountCode": "$.Lex.SessionAttributes.accountCode",
        "languageLabel": "$.Lex.SessionAttributes.languageLabel", "switchTo": "$.Lex.SessionAttributes.switchTo"}}, "OutcomeCheck", err("Bye", NM)),
    act("OutcomeCheck", "Compare", {"ComparisonValue": "$.Attributes.outcome"}, "Fallback", err("Fallback", NC),
        [eq("SetQueue", "escalate"), eq("Bye", "resolved"), eq("SwitchCheck", "switch_language")]),
    # The caller asked for the other language: same call, bot and voice in that language, account kept
    act("SwitchCheck", "Compare", {"ComparisonValue": "$.Attributes.switchTo"}, "SwitchEn", err("SwitchEn", NC), [eq("SwitchEs", "es")]),
    act("SwitchEs", "UpdateContactAttributes", {"Attributes": {"language": "es", "outcome": "switched", "aiGreeting": "Claro. ¿En qué puedo ayudarle?"}}, "CodeEs", err("CodeEs", NM)),
    act("SwitchEn", "UpdateContactAttributes", {"Attributes": {"language": "en", "outcome": "switched", "aiGreeting": "Sure. How can I help you?"}}, "CodeEn", err("CodeEn", NM)),
    act("SetQueue", "UpdateContactTargetQueue", {"QueueId": "$.Attributes.queueArn"}, "HookSwitch", err("Fallback", NM)),
    # No outcome or no queue: a person in General Assistance takes the call instead of hanging up
    act("Fallback", "UpdateContactAttributes", {"Attributes": {
        "outcome": "escalate", "reason": "The AI session ended without a result",
        "summary": "The AI assistant could not finish the conversation. Ask the customer how you can help.",
        "queueName": "general assistance"}}, "SetFallbackQueue", err("SetFallbackQueue", NM)),
    act("SetFallbackQueue", "UpdateContactTargetQueue", {"QueueId": fallback_arn}, "HookSwitch", err("Bye", NM)),
    act("HookSwitch", "Compare", {"ComparisonValue": "$.Attributes.language"}, "HookEn", err("HookEn", NC), [eq("HookEs", "es")]),
    act("HookEn", "UpdateContactEventHooks", {"EventHooks": {"CustomerQueue": hooks["en"]}}, "GuideHook", err("GuideHook", NM)),
    act("HookEs", "UpdateContactEventHooks", {"EventHooks": {"CustomerQueue": hooks["es"]}}, "GuideHook", err("GuideHook", NM)),
    # The agent who answers sees a "Transferred by the AI assistant" panel (reason, summary, account) in the workspace
    act("GuideHook", "UpdateContactEventHooks", {"EventHooks": {"DefaultAgentUI": guide_arn, "DisconnectAgentUI": wrapup_arn}},
        "Transfer", err("Transfer", NM)),
    act("Transfer", "TransferContactToQueue", {}, "Bye", err("Bye", NM, "QueueAtCapacity")),
    act("Bye", "DisconnectParticipant", {}),
]
content = json.dumps(s.layout({"Version": "2019-10-30", "StartAction": "LogOn", "Metadata": {}, "Actions": a}))
s.rename_legacy_flows(s.connect, s.IID, s.PREFIX)
name = s.FLOW_NAMES[os.environ.get("AI_FLOW_KEY", "ai-inbound")]
fid = next((f["Id"] for f in s.connect.list_contact_flows(InstanceId=s.IID, ContactFlowTypes=["CONTACT_FLOW"])["ContactFlowSummaryList"] if f["Name"] == name), None)
if fid:
    s.connect.update_contact_flow_content(InstanceId=s.IID, ContactFlowId=fid, Content=content)
    print("flow updated:", name, fid)
else:
    r = s.connect.create_contact_flow(InstanceId=s.IID, Name=name, Type="CONTACT_FLOW", Content=content, Description="Demo: AI agent (Nova Sonic), escalates to a person")
    print("flow created:", name, r["ContactFlowId"])
