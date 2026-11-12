#!/usr/bin/env python3
"""Contact flow "ElevenLabs Transfer" (route B) and its phone number.

The first voice the caller hears is the ElevenLabs agent: Connect records and identifies silently.
- Known caller with a special status (Redemptions, EPD): straight to a person, no AI.
- Anyone else, known or not: prepare the hand-off and transfer to the ElevenLabs Twilio number with
  "resume flow after disconnect". The agent gives the recording notice, and asks unknown callers for their
  account number.
- When ElevenLabs hangs up: escalate goes to the customer's queue (or general assistance), anything else ends.
Re-runnable; attaches the flow to the "ElevenLabs" number.

    AWS_PROFILE=cs-admin python3 poc/infra/elevenlabs-route-b/setup_flow.py
"""
import json

import boto3

REGION = "us-east-1"
EXPECTED_ACCOUNT = "383799408374"
INSTANCE_ID = "c2f9ca2b-eb05-4a82-9809-1d7c914333ba"
FLOW_NAME = "ElevenLabs Transfer"
ELEVENLABS_NUMBER = "+19528661775"     # Twilio number answered by collections-agent
CONNECT_NUMBER = "+17752550671"        # Connect number described "ElevenLabs"
FALLBACK_QUEUE = "CS - General Assistance"
VOICES = {"es": "Lupe", "en": "Danielle"}

session = boto3.Session(region_name=REGION)
assert session.client("sts").get_caller_identity()["Account"] == EXPECTED_ACCOUNT
connect = session.client("connect")
lam_arn = session.client("lambda").get_function(FunctionName="voice-agent-api")["Configuration"]["FunctionArn"]
fallback_arn = next(q["Arn"] for q in connect.list_queues(InstanceId=INSTANCE_ID, QueueTypes=["STANDARD"])["QueueSummaryList"]
                    if q["Name"] == FALLBACK_QUEUE)

NM, NC = "NoMatchingError", "NoMatchingCondition"
actions = []


def act(ident, kind, params, nxt=None, errors=(), conditions=None):
    transitions = {}
    if nxt:
        transitions["NextAction"] = nxt
    if errors:
        transitions["Errors"] = [{"NextAction": target, "ErrorType": kind_} for kind_, target in errors]
    if conditions:
        transitions["Conditions"] = [{"NextAction": target, "Condition": {"Operator": "Equals", "Operands": [value]}}
                                     for value, target in conditions]
    actions.append({"Identifier": ident, "Type": kind, "Parameters": params, "Transitions": transitions})


def lam(ident, action, nxt, on_error, extra=None):
    act(ident, "InvokeLambdaFunction", {"LambdaFunctionARN": lam_arn, "InvocationTimeLimitSeconds": "8",
                                        "LambdaInvocationAttributes": {"action": action, **(extra or {})},
                                        "ResponseValidation": {"ResponseType": "STRING_MAP"}},
        nxt, [(NM, on_error)])


def say(ident, es, en, nxt):
    """Speaks in the contact's language (attribute "language", English by default) with a matching voice."""
    act(ident, "Compare", {"ComparisonValue": "$.Attributes.language"}, f"{ident}VoiceEn", [(NC, f"{ident}VoiceEn")],
        [("es", f"{ident}VoiceEs")])
    for code, text in (("Es", es), ("En", en)):
        act(f"{ident}Voice{code}", "UpdateContactTextToSpeechVoice",
            {"TextToSpeechVoice": VOICES[code.lower()], "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"},
            f"{ident}{code}", [(NM, f"{ident}{code}")])
        act(f"{ident}{code}", "MessageParticipant", {"Text": text}, nxt, [(NM, nxt)])


act("Start", "UpdateFlowLoggingBehavior", {"FlowLoggingBehavior": "Enabled"}, "Rec")
act("Rec", "UpdateContactRecordingAndAnalyticsBehavior",
    {"VoiceBehavior": {"VoiceRecordingBehavior": {"RecordedParticipants": ["Agent", "Customer"], "IVRRecordingBehavior": "Enabled"}}},
    "Identify", [(NM, "Identify"), ("ChannelMismatch", "Identify")])
lam("Identify", "identify", "Remember", "Prepare")
act("Remember", "UpdateContactAttributes", {"Attributes": {
    "aiAgent": "elevenlabs", "customerFound": "$.External.found", "account": "$.External.account",
    "customerName": "$.External.customerName", "language": "$.External.language",
    "canNegotiate": "$.External.canNegotiate", "queueArn": "$.External.queueArn"}, "TargetContact": "Current"},
    "IsSpecial", [(NM, "Prepare")])
# Only a known customer that cannot negotiate skips the AI; unknown callers go to the agent, which asks the account.
act("IsSpecial", "Compare", {"ComparisonValue": "$.Attributes.canNegotiate"}, "Prepare", [(NC, "Prepare")],
    [("false", "SpecialMsg")])
lam("Prepare", "prepare_handoff", "Transfer", "FailMsg",
    {"account": "$.Attributes.account", "language": "$.Attributes.language"})
act("Transfer", "TransferParticipantToThirdParty",
    {"ThirdPartyPhoneNumber": ELEVENLABS_NUMBER, "ThirdPartyConnectionTimeLimitSeconds": "30", "ContinueFlowExecution": "True"},
    "Outcome", [("CallFailed", "FailMsg"), ("ConnectionTimeLimitExceeded", "FailMsg"), (NM, "FailMsg")])
# Sofia says goodbye herself, so a call she ended without escalating hangs up with no message from Connect.
lam("Outcome", "outcome", "AfterAi", "End")
# The agent may have identified the customer by account and switched language: refresh both before speaking.
act("AfterAi", "UpdateContactAttributes", {"Attributes": {
    "aiOutcome": "$.External.outcome", "language": "$.External.language", "queueArn": "$.External.queueArn"},
    "TargetContact": "Current"}, "IsEscalate", [(NM, "IsEscalate")])
act("IsEscalate", "Compare", {"ComparisonValue": "$.Attributes.aiOutcome"}, "End", [(NC, "End")],
    [("escalate", "HumanMsg")])
say("HumanMsg", "Le comunico con un asesor.", "Let me connect you with an agent.", "SetQueue")
say("SpecialMsg", "Esta llamada puede ser grabada. Un especialista le atenderá en un momento.",
    "This call may be recorded. A specialist will be with you shortly.", "SetQueue")
say("FailMsg", "Disculpe, no pudimos conectar con la asistente. Le comunico con un asesor.",
    "Sorry, we could not reach the assistant. Let me connect you with an agent.", "SetQueue")
act("SetQueue", "UpdateContactTargetQueue", {"QueueId": "$.Attributes.queueArn"}, "ToQueue", [(NM, "FallbackQueue")])
act("FallbackQueue", "UpdateContactTargetQueue", {"QueueId": fallback_arn}, "ToQueue", [(NM, "End")])
act("ToQueue", "TransferContactToQueue", {}, "End", [("QueueAtCapacity", "End"), (NM, "End")])
act("End", "DisconnectParticipant", {})

content = json.dumps({"Version": "2019-10-30", "StartAction": "Start", "Metadata": {}, "Actions": actions})
existing = next((f for f in connect.list_contact_flows(InstanceId=INSTANCE_ID, ContactFlowTypes=["CONTACT_FLOW"])["ContactFlowSummaryList"]
                 if f["Name"] == FLOW_NAME), None)
try:
    if existing:
        connect.update_contact_flow_content(InstanceId=INSTANCE_ID, ContactFlowId=existing["Id"], Content=content)
        flow_id = existing["Id"]
    else:
        flow_id = connect.create_contact_flow(InstanceId=INSTANCE_ID, Name=FLOW_NAME, Type="CONTACT_FLOW", Content=content,
                                              Description="Hands the call to the ElevenLabs collections agent by phone",
                                              Tags={"project": "elevenlabs"})["ContactFlowId"]
except connect.exceptions.InvalidContactFlowException as ex:
    raise SystemExit(json.dumps(ex.response.get("problems"), indent=1))

number_id = next(n["PhoneNumberId"] for n in connect.list_phone_numbers_v2(
    TargetArn=f"arn:aws:connect:{REGION}:{EXPECTED_ACCOUNT}:instance/{INSTANCE_ID}")["ListPhoneNumbersSummaryList"]
    if n["PhoneNumber"] == CONNECT_NUMBER)
connect.associate_phone_number_contact_flow(PhoneNumberId=number_id, InstanceId=INSTANCE_ID, ContactFlowId=flow_id)
print(f"flow {FLOW_NAME} ({flow_id}) published and attached to {CONNECT_NUMBER}")
