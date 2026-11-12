#!/usr/bin/env python3
"""Makes the sandbox line (+1 775 249 1708, the phone of customer account 10) ring demo.caller2's softphone,
so outbound tests have a "customer" to call. `restore` puts the line back on "CS - Sandbox - Simple Flow".

    AWS_PROFILE=cs-admin python3 poc/infra/outbound/customer_line.py ring|restore
"""
import json
import sys

import boto3

REGION, ACCOUNT = "us-east-1", "383799408374"
IID = "c2f9ca2b-eb05-4a82-9809-1d7c914333ba"
LINE = "+17752491708"
USER = "demo.caller2"
FLOW_NAME = "CS - Test - Customer Phone (caller2)"
SANDBOX_FLOW = "CS - Sandbox - Simple Flow"

s = boto3.Session(region_name=REGION)
assert s.client("sts").get_caller_identity()["Account"] == ACCOUNT
c = s.client("connect")


def flows():
    return {f["Name"]: f["Id"] for p in c.get_paginator("list_contact_flows").paginate(InstanceId=IID, ContactFlowTypes=["CONTACT_FLOW"])
            for f in p["ContactFlowSummaryList"]}


def ensure_flow():
    user = next(u for u in c.list_users(InstanceId=IID)["UserSummaryList"] if u["Username"] == USER)
    # The agent queue of one user: the call rings only that softphone.
    content = json.dumps({"Version": "2019-10-30", "StartAction": "Queue", "Actions": [
        {"Identifier": "Queue", "Type": "UpdateContactTargetQueue", "Parameters": {"AgentId": user["Arn"]},
         "Transitions": {"NextAction": "Transfer", "Errors": [{"NextAction": "End", "ErrorType": "NoMatchingError"}], "Conditions": []}},
        {"Identifier": "Transfer", "Type": "TransferContactToQueue", "Parameters": {},
         "Transitions": {"NextAction": "End", "Errors": [{"NextAction": "End", "ErrorType": "QueueAtCapacity"},
                                                         {"NextAction": "End", "ErrorType": "NoMatchingError"}], "Conditions": []}},
        {"Identifier": "End", "Type": "DisconnectParticipant", "Parameters": {}, "Transitions": {}},
    ]})
    existing = flows().get(FLOW_NAME)
    if existing:
        c.update_contact_flow_content(InstanceId=IID, ContactFlowId=existing, Content=content)
        return existing
    return c.create_contact_flow(InstanceId=IID, Name=FLOW_NAME, Type="CONTACT_FLOW", Content=content,
                                 Description="Outbound tests: the customer's phone rings demo.caller2")["ContactFlowId"]


def attach(flow_id):
    number = next(n for n in c.list_phone_numbers_v2(InstanceId=IID)["ListPhoneNumbersSummaryList"] if n["PhoneNumber"] == LINE)
    c.associate_phone_number_contact_flow(PhoneNumberId=number["PhoneNumberId"], InstanceId=IID, ContactFlowId=flow_id)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "ring"
    target = ensure_flow() if mode == "ring" else flows()[SANDBOX_FLOW]
    attach(target)
    print(f"{LINE} -> {FLOW_NAME if mode == 'ring' else SANDBOX_FLOW}")
