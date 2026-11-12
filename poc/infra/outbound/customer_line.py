#!/usr/bin/env python3
"""Makes a test customer's phone ring a softphone user, so outbound tests have someone to call:

- caller2: +1 775 249 1708 (sandbox line, customer account 10, Willian) rings demo.caller2.
  `restore` puts the line back on "CS - Sandbox - Simple Flow".
- caller3: +1 775 258 5298 (customer account 2, Maria) rings demo.caller3.
  `restore` removes the flow (the line had no inbound flow before).

    AWS_PROFILE=cs-admin python3 poc/infra/outbound/customer_line.py ring|restore [caller2|caller3]
"""
import json
import os
import sys

import boto3

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mei-demo"))
from flow_layout import layout  # noqa: E402  (block positions, so the flow is readable in the designer)

REGION, ACCOUNT = "us-east-1", "383799408374"
IID = "c2f9ca2b-eb05-4a82-9809-1d7c914333ba"
LINES = {
    "caller2": {"number": "+17752491708", "user": "demo.caller2", "restore_flow": "CS - Sandbox - Simple Flow"},
    "caller3": {"number": "+17752585298", "user": "demo.caller3", "restore_flow": None},
}

s = boto3.Session(region_name=REGION)
assert s.client("sts").get_caller_identity()["Account"] == ACCOUNT
c = s.client("connect")


def flows():
    return {f["Name"]: f["Id"] for p in c.get_paginator("list_contact_flows").paginate(InstanceId=IID, ContactFlowTypes=["CONTACT_FLOW"])
            for f in p["ContactFlowSummaryList"]}


def ensure_flow(username):
    name = f"CS - Test - Customer Phone ({username.split('.')[-1]})"
    user = next(u for u in c.list_users(InstanceId=IID)["UserSummaryList"] if u["Username"] == username)
    # The agent queue of one user: the call rings only that softphone.
    content = json.dumps({"Version": "2019-10-30", "StartAction": "Queue", "Actions": [
        {"Identifier": "Queue", "Type": "UpdateContactTargetQueue", "Parameters": {"AgentId": user["Arn"]},
         "Transitions": {"NextAction": "Transfer", "Errors": [{"NextAction": "End", "ErrorType": "NoMatchingError"}], "Conditions": []}},
        {"Identifier": "Transfer", "Type": "TransferContactToQueue", "Parameters": {},
         "Transitions": {"NextAction": "End", "Errors": [{"NextAction": "End", "ErrorType": "QueueAtCapacity"},
                                                         {"NextAction": "End", "ErrorType": "NoMatchingError"}], "Conditions": []}},
        {"Identifier": "End", "Type": "DisconnectParticipant", "Parameters": {}, "Transitions": {}},
    ]})
    content = json.dumps(layout(json.loads(content)))
    existing = flows().get(name)
    if existing:
        c.update_contact_flow_content(InstanceId=IID, ContactFlowId=existing, Content=content)
        return existing, name
    created = c.create_contact_flow(InstanceId=IID, Name=name, Type="CONTACT_FLOW", Content=content,
                                    Description=f"Outbound tests: the customer's phone rings {username}")
    return created["ContactFlowId"], name


def number_id(number):
    return next(n["PhoneNumberId"] for n in c.list_phone_numbers_v2(InstanceId=IID)["ListPhoneNumbersSummaryList"] if n["PhoneNumber"] == number)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "ring"
    line = LINES[sys.argv[2] if len(sys.argv) > 2 else "caller2"]
    pid = number_id(line["number"])
    if mode == "ring":
        flow_id, name = ensure_flow(line["user"])
        c.associate_phone_number_contact_flow(PhoneNumberId=pid, InstanceId=IID, ContactFlowId=flow_id)
        print(f"{line['number']} -> {name}")
    elif line["restore_flow"]:
        c.associate_phone_number_contact_flow(PhoneNumberId=pid, InstanceId=IID, ContactFlowId=flows()[line["restore_flow"]])
        print(f"{line['number']} -> {line['restore_flow']}")
    else:
        c.disassociate_phone_number_contact_flow(PhoneNumberId=pid, InstanceId=IID)
        print(f"{line['number']} -> no inbound flow")
