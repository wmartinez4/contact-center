#!/usr/bin/env python3
"""Step-by-step guides shown in the agent workspace when a call arrives by transfer.

- "CS - Guide - Transfer Reason": the AI agent handed the call over (reason, AI summary, account, language,
  queue). The AI flow points its "Default flow for agent UI" event hook here (setup_ai_flow.py).
- "CS - Guide - Agent Transfer": another agent transferred it (customer summary, where it came from, status).
  The queue transfer flow used by the quick connects points here (setup_transfer_flow.py).
Re-runnable.

    AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> EXPECTED_ACCOUNT=<account> DEMO_PREFIX=demo python3 setup_guide_flow.py
"""
import json

import setup_part_a as s

act, err, NM, NC = s.act, s.err, s.NM, s.NC
DETAIL_VIEW = f"arn:aws:connect:{s.REGION}:aws:view/detail"

GUIDES = {
    "guide-customer": {
        "Heading": "Customer on the line",
        "Description": "$.Attributes.customerSummary",
        "AttributeBar": [
            {"Label": "Account", "Value": "$.Attributes.caseCode", "Copyable": True},
            {"Label": "Identified by", "Value": "$.Attributes.identifiedBy"},
            {"Label": "Special status", "Value": "$.Attributes.specialStatus"},
            {"Label": "Language", "Value": "$.Attributes.language"},
        ],
    },
    "guide-transfer": {
        "Heading": "Transferred by the AI assistant",
        "Description": "$.Attributes.summary",
        "AttributeBar": [
            {"Label": "Reason", "Value": "$.Attributes.reason"},
            {"Label": "Account", "Value": "$.Attributes.accountCode", "Copyable": True},
            {"Label": "Language", "Value": "$.Attributes.languageLabel"},
            {"Label": "Queue", "Value": "$.Attributes.queueName"},
        ],
    },
    "guide-agent-transfer": {
        "Heading": "Transferred by another agent",
        "Description": "$.Attributes.customerSummary",
        "AttributeBar": [
            {"Label": "Came from", "Value": "$.Attributes.queueLabel"},
            {"Label": "Account", "Value": "$.Attributes.caseCode", "Copyable": True},
            {"Label": "Special status", "Value": "$.Attributes.specialStatus"},
            {"Label": "Language", "Value": "$.Attributes.language"},
        ],
    },
}
DESCRIPTIONS = {"guide-customer": "Agent workspace guide: who is calling, from the account lookup",
                "guide-transfer": "Agent workspace guide: why the AI agent transferred the call",
                "guide-agent-transfer": "Agent workspace guide: customer context when another agent transfers the call"}


def content(key):
    a = [
        act("Guide", "ShowView", {"ViewResource": {"Id": DETAIL_VIEW}, "InvocationTimeLimitSeconds": "1800", "ViewData": GUIDES[key]},
            "End", err("End", NM, NC, "TimeLimitExceeded")),
        act("End", "DisconnectParticipant", {}),
    ]
    return json.dumps(s.layout({"Version": "2019-10-30", "StartAction": "Guide", "Metadata": {}, "Actions": a}))


def ensure(key="guide-transfer"):
    s.rename_legacy_flows(s.connect, s.IID, s.PREFIX)
    name = s.FLOW_NAMES[key]
    flows = s.connect.list_contact_flows(InstanceId=s.IID, ContactFlowTypes=["CONTACT_FLOW"], MaxResults=1000)["ContactFlowSummaryList"]
    existing = next((f for f in flows if f["Name"] == name), None)
    if existing:
        s.connect.update_contact_flow_content(InstanceId=s.IID, ContactFlowId=existing["Id"], Content=content(key))
        print("flow updated:", name)
        return existing["Arn"]
    r = s.connect.create_contact_flow(InstanceId=s.IID, Name=name, Type="CONTACT_FLOW", Content=content(key), Description=DESCRIPTIONS[key])
    print("flow created:", name)
    return r["ContactFlowArn"]


if __name__ == "__main__":
    for k in GUIDES:
        print(ensure(k))
