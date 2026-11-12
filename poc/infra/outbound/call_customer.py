#!/usr/bin/env python3
"""Outbound collections call with the ElevenLabs agent: Connect dials the customer's phone (from Customer Profiles)
and, when it is answered, runs the route B flow, which hands the call to Sofia.

For tests the customer is account 10, whose phone is the sandbox line; `customer_line.py ring` makes it ring
demo.caller2's softphone, so whoever is logged in as demo.caller2 plays the customer.
After the call it shows how the hand-off was matched, the outcome and the agreement.

    AWS_PROFILE=cs-admin python3 poc/infra/outbound/call_customer.py [account]
"""
import json
import sys
import time

import boto3

REGION, ACCOUNT = "us-east-1", "383799408374"
IID = "c2f9ca2b-eb05-4a82-9809-1d7c914333ba"
DOMAIN = "amazon-connect-cs-connect-demo"
CALLER_ID = "+17752550671"  # the "ElevenLabs" Connect number
FLOW_NAME = "ElevenLabs Transfer"
CUSTOMER_AGENT = "demo.caller2"

s = boto3.Session(region_name=REGION)
assert s.client("sts").get_caller_identity()["Account"] == ACCOUNT
c, profiles = s.client("connect"), s.client("customer-profiles")
calls = s.resource("dynamodb").Table("voice-calls")


def customer_phone(account):
    p = profiles.search_profiles(DomainName=DOMAIN, KeyName="_account", Values=[account])["Items"][0]
    return p.get("PhoneNumber") or p.get("MobilePhoneNumber"), f"{p.get('FirstName')} {p.get('LastName')}"


def agent_status(username):
    user = next(u for u in c.list_users(InstanceId=IID)["UserSummaryList"] if u["Username"] == username)
    data = c.get_current_user_data(InstanceId=IID, Filters={"Agents": [user["Id"]]})["UserDataList"]
    return data[0]["Status"]["StatusName"] if data else "Offline"


def main(account):
    phone, name = customer_phone(account)
    status = agent_status(CUSTOMER_AGENT)
    if status != "Available":
        sys.exit(f"{CUSTOMER_AGENT} is {status}: log in and go Available to answer as the customer")
    flow_id = next(f["Id"] for f in c.list_contact_flows(InstanceId=IID, ContactFlowTypes=["CONTACT_FLOW"])["ContactFlowSummaryList"]
                   if f["Name"] == FLOW_NAME)
    started = int(time.time())
    cid = c.start_outbound_voice_contact(InstanceId=IID, ContactFlowId=flow_id, DestinationPhoneNumber=phone,
                                         SourcePhoneNumber=CALLER_ID,
                                         Attributes={"direction": "outbound", "campaign": "manual-test"})["ContactId"]
    print(f"calling {name} (account {account}) at {phone}: contact {cid}", flush=True)
    while not c.describe_contact(InstanceId=IID, ContactId=cid)["Contact"].get("DisconnectTimestamp"):
        time.sleep(5)
    time.sleep(40)  # post-call webhook
    item = calls.get_item(Key={"contactId": cid}).get("Item") or {}
    print("hand-off record:", json.dumps({k: item.get(k) for k in ("phone", "status", "account", "outcome", "summary", "conversationId")},
                                         default=str, ensure_ascii=False))
    direct = [i for i in calls.scan(FilterExpression="#s = :d AND createdAt >= :t", ExpressionAttributeNames={"#s": "source"},
                                    ExpressionAttributeValues={":d": "direct", ":t": started})["Items"]]
    if direct:
        print("NOT MATCHED: ElevenLabs saw caller id", [d.get("phone") for d in direct])
    attrs = c.get_contact_attributes(InstanceId=IID, InitialContactId=cid)["Attributes"]
    print("contact attributes:", json.dumps({k: attrs.get(k) for k in ("customerName", "account", "aiOutcome", "agreementSummary",
                                                                      "aiCallSummary", "transcriptS3")}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "10")
