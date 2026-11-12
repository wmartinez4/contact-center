#!/usr/bin/env python3
"""Small flow for live editing on the sandbox line: greeting, a two-option menu, transfer to a queue.
It shares nothing with the demo flows except the queue, so edits in the designer cannot break the demo.

    AWS_PROFILE=<profile> CONNECT_INSTANCE_ID=<id> EXPECTED_ACCOUNT=<account> DEMO_PREFIX=demo python3 setup_sandbox_flow.py
"""
import json

import setup_part_a as s
from names import queue_key

act, err, eq, NM, NC, TO = s.act, s.err, s.eq, s.NM, s.NC, s.TO
queue_arn = next(q["Arn"] for q in s.connect.list_queues(InstanceId=s.IID, QueueTypes=["STANDARD"])["QueueSummaryList"]
                 if queue_key(q["Name"], s.PREFIX) == "Q-Current")

a = [
    act("Voice", "UpdateContactTextToSpeechVoice", {"TextToSpeechVoice": "Danielle", "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"}, "Welcome", err("Welcome", NM)),
    act("Welcome", "MessageParticipant", {"Text": "Welcome to the test line."}, "Menu", err("Menu", NM)),
    act("Menu", "GetParticipantInput", {"Text": "For billing questions, press 1. To talk to an agent, press 2.", "StoreInput": "False", "InputTimeLimitSeconds": "8"},
        "Goodbye", err("Goodbye", NM, NC, TO), [eq("Billing", "1"), eq("SetQueue", "2")]),
    act("Billing", "MessageParticipant", {"Text": "Your next payment is due on the twentieth. Goodbye."}, "Bye", err("Bye", NM)),
    act("SetQueue", "UpdateContactTargetQueue", {"QueueId": queue_arn}, "Transfer", err("Goodbye", NM)),
    act("Transfer", "TransferContactToQueue", {}, "Bye", err("Goodbye", NM, "QueueAtCapacity")),
    act("Goodbye", "MessageParticipant", {"Text": "Thank you for calling. Goodbye."}, "Bye", err("Bye", NM)),
    act("Bye", "DisconnectParticipant", {}),
]
content = json.dumps(s.layout({"Version": "2019-10-30", "StartAction": "Voice", "Metadata": {}, "Actions": a}))
s.rename_legacy_flows(s.connect, s.IID, s.PREFIX)
name = s.FLOW_NAMES["sandbox-simple"]
fid = next((f["Id"] for f in s.connect.list_contact_flows(InstanceId=s.IID, ContactFlowTypes=["CONTACT_FLOW"])["ContactFlowSummaryList"] if f["Name"] == name), None)
if fid:
    s.connect.update_contact_flow_content(InstanceId=s.IID, ContactFlowId=fid, Content=content)
    print("flow updated:", name)
else:
    fid = s.connect.create_contact_flow(InstanceId=s.IID, Name=name, Type="CONTACT_FLOW", Content=content,
                                        Description="Sandbox: simple flow for live edits; not used by the demo")["ContactFlowId"]
    print("flow created:", name)
for pid in s.PHONE_IDS:
    desc = s.connect.describe_phone_number(PhoneNumberId=pid)["ClaimedPhoneNumberSummary"].get("PhoneNumberDescription", "")
    if desc.lower().startswith(f"{s.PREFIX} sandbox"):
        s.connect.associate_phone_number_contact_flow(PhoneNumberId=pid, InstanceId=s.IID, ContactFlowId=fid)
        print("sandbox number now points to", name)
