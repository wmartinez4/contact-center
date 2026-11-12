#!/usr/bin/env python3
"""Second test caller whose calls show a fixed caller ID (the sandbox line), registered as a customer.

Lets you test the known-caller path (personal greeting, no menus, profile by phone) without a customer's phone.
demo.caller keeps the main line as caller ID, so it still gets the menus. Re-runnable.

    AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> EXPECTED_ACCOUNT=<account> DEMO_PREFIX=demo python3 setup_caller2.py
"""
import setup_part_a as s
from names import DISPLAY_PREFIX

QUEUE = DISPLAY_PREFIX + "Test Caller 2 Only"
PROFILE = DISPLAY_PREFIX + "Test Caller 2"

c, IID = s.connect, s.IID
caller_id = next(pid for pid in s.PHONE_IDS
                 if c.describe_phone_number(PhoneNumberId=pid)["ClaimedPhoneNumberSummary"].get("PhoneNumberDescription", "").lower().startswith(f"{s.PREFIX} sandbox"))
hours = s.hours_id()

qid = next((q["Id"] for q in c.list_queues(InstanceId=IID, QueueTypes=["STANDARD"])["QueueSummaryList"] if q["Name"] == QUEUE), None)
if not qid:
    qid = c.create_queue(InstanceId=IID, Name=QUEUE, Description="Outbound only: caller ID is the sandbox line", HoursOfOperationId=hours,
                         OutboundCallerConfig={"OutboundCallerIdName": "Collections", "OutboundCallerIdNumberId": caller_id})["QueueId"]
    print("queue created:", QUEUE)

rp = next((p["Id"] for p in c.list_routing_profiles(InstanceId=IID)["RoutingProfileSummaryList"] if p["Name"] == PROFILE), None)
if not rp:
    rp = c.create_routing_profile(InstanceId=IID, Name=PROFILE, Description=PROFILE, DefaultOutboundQueueId=qid,
                                  MediaConcurrencies=[{"Channel": "VOICE", "Concurrency": 1}],
                                  QueueConfigs=[{"QueueReference": {"QueueId": qid, "Channel": "VOICE"}, "Priority": 1, "Delay": 0}])["RoutingProfileId"]
    print("routing profile created:", PROFILE)

sec = next(p["Id"] for p in c.list_security_profiles(InstanceId=IID)["SecurityProfileSummaryList"] if p["Name"] == "Agent")
creds = {}
s.ensure_user(f"{s.PREFIX}.caller2", "Test Caller 2", "Known Number", rp, sec, creds)
if creds:
    with open(s.os.path.join(s.POC, ".credentials.local"), "a") as f:
        for u, p in creds.items():
            f.write(f"{u}\t{p}\n")
    print("password written to .credentials.local")
