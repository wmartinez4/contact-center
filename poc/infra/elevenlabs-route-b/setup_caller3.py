#!/usr/bin/env python3
"""Test caller 3: a softphone user whose outbound calls show their own claimed number, used to test the
ElevenLabs agent (route B). setup_api.py maps that number to a demo account in TEST_CALLERS.

Same pattern as poc/infra/mei-demo/setup_caller2.py. Re-runnable; claims the number only once and writes
the new user's password to poc/.credentials.local (git-ignored). Prints the number.

    AWS_PROFILE=cs-admin python3 poc/infra/elevenlabs-route-b/setup_caller3.py
"""
import os
import secrets
import string

import boto3

REGION = "us-east-1"
EXPECTED_ACCOUNT = "383799408374"
INSTANCE_ID = "c2f9ca2b-eb05-4a82-9809-1d7c914333ba"
NUMBER_DESCRIPTION = "Test caller 3"
QUEUE, PROFILE, USERNAME = "CS - Test Caller 3 Only", "CS - Test Caller 3", "demo.caller3"  # matches demo.caller and demo.caller2
CREDENTIALS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".credentials.local"))

session = boto3.Session(region_name=REGION)
assert session.client("sts").get_caller_identity()["Account"] == EXPECTED_ACCOUNT
c = session.client("connect")
TARGET = f"arn:aws:connect:{REGION}:{EXPECTED_ACCOUNT}:instance/{INSTANCE_ID}"


def ensure_number():
    for n in c.list_phone_numbers_v2(TargetArn=TARGET)["ListPhoneNumbersSummaryList"]:
        desc = c.describe_phone_number(PhoneNumberId=n["PhoneNumberId"])["ClaimedPhoneNumberSummary"].get("PhoneNumberDescription", "")
        if desc == NUMBER_DESCRIPTION:
            return n["PhoneNumberId"], n["PhoneNumber"]
    for number in c.search_available_phone_numbers(TargetArn=TARGET, PhoneNumberCountryCode="US", PhoneNumberType="DID",
                                                   MaxResults=10)["AvailableNumbersList"]:
        try:
            pid = c.claim_phone_number(TargetArn=TARGET, PhoneNumber=number["PhoneNumber"],
                                       PhoneNumberDescription=NUMBER_DESCRIPTION, Tags={"project": "elevenlabs"})["PhoneNumberId"]
            print("number claimed:", number["PhoneNumber"])
            return pid, number["PhoneNumber"]
        except c.exceptions.InvalidParameterException:
            continue  # taken between search and claim
    raise SystemExit("no number could be claimed")


def ensure_queue(number_id):
    queues = c.list_queues(InstanceId=INSTANCE_ID, QueueTypes=["STANDARD"])["QueueSummaryList"]
    found = next((q for q in queues if q["Name"] == QUEUE), None)
    if found:
        return found["Id"]
    caller2 = next(q for q in queues if q["Name"] == "CS - Test Caller 2 Only")
    hours = c.describe_queue(InstanceId=INSTANCE_ID, QueueId=caller2["Id"])["Queue"]["HoursOfOperationId"]
    qid = c.create_queue(InstanceId=INSTANCE_ID, Name=QUEUE, Description="Outbound only: caller ID is the Test caller 3 number",
                         HoursOfOperationId=hours, OutboundCallerConfig={"OutboundCallerIdName": "Customer",
                                                                         "OutboundCallerIdNumberId": number_id})["QueueId"]
    print("queue created:", QUEUE)
    return qid


def ensure_routing_profile(queue_id):
    found = next((p for p in c.list_routing_profiles(InstanceId=INSTANCE_ID)["RoutingProfileSummaryList"] if p["Name"] == PROFILE), None)
    if found:
        return found["Id"]
    rid = c.create_routing_profile(InstanceId=INSTANCE_ID, Name=PROFILE, Description=PROFILE, DefaultOutboundQueueId=queue_id,
                                   MediaConcurrencies=[{"Channel": "VOICE", "Concurrency": 1}],
                                   QueueConfigs=[{"QueueReference": {"QueueId": queue_id, "Channel": "VOICE"}, "Priority": 1, "Delay": 0}])["RoutingProfileId"]
    print("routing profile created:", PROFILE)
    return rid


def ensure_user(routing_id):
    if any(u["Username"] == USERNAME for u in c.list_users(InstanceId=INSTANCE_ID)["UserSummaryList"]):
        return
    agent = next(p["Id"] for p in c.list_security_profiles(InstanceId=INSTANCE_ID)["SecurityProfileSummaryList"] if p["Name"] == "Agent")
    alphabet = string.ascii_letters + string.digits
    pwd = "".join(secrets.choice(string.ascii_uppercase) for _ in range(2)) + "".join(secrets.choice(alphabet) for _ in range(10)) + \
        "".join(secrets.choice(string.digits) for _ in range(2)) + "!x"
    c.create_user(InstanceId=INSTANCE_ID, Username=USERNAME, Password=pwd, IdentityInfo={"FirstName": "Test Caller", "LastName": "Three"},
                  PhoneConfig={"PhoneType": "SOFT_PHONE", "AutoAccept": True, "AfterContactWorkTimeLimit": 60},
                  SecurityProfileIds=[agent], RoutingProfileId=routing_id, Tags={"project": "elevenlabs"})
    with open(CREDENTIALS, "a") as f:
        f.write(f"{USERNAME}\t{pwd}\n")
    print(f"user created: {USERNAME} (password written to poc/.credentials.local)")


def ensure_workspace():
    """Same branded agent workspace as the other demo users (logo and agent home page)."""
    workspace = next(w["Id"] for w in c.list_workspaces(InstanceId=INSTANCE_ID)["WorkspaceSummaryList"] if w["Name"] == "Agents")
    user_arn = next(u["Arn"] for u in c.list_users(InstanceId=INSTANCE_ID)["UserSummaryList"] if u["Username"] == USERNAME)
    try:
        c.associate_workspace(InstanceId=INSTANCE_ID, WorkspaceId=workspace, ResourceArns=[user_arn])
    except c.exceptions.ClientError as e:
        if e.response["Error"]["Code"] not in ("ResourceConflictException", "DuplicateResourceException"):
            raise


number_id, number = ensure_number()
ensure_user(ensure_routing_profile(ensure_queue(number_id)))
ensure_workspace()
print("caller3 outbound number:", number)
