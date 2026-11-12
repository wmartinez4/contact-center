#!/usr/bin/env python3
"""Run call-tester scenarios: Connect calls a demo line from a claimed number and the simulated customer talks to it.

For each scenario: starts the outbound call, waits for it to end, prints the dialogue the tester heard and said
(from its Lambda logs), finds the inbound contact it produced on the line under test and compares that contact's
attributes with the scenario's `expect`. Route B scenarios also show the saved agreement and the S3 transcript.

    AWS_PROFILE=cs-admin python3 poc/infra/call-tester/run.py maria-installments [more ...]
"""
import datetime as dt
import json
import os
import sys
import time

import boto3

REGION, IID = "us-east-1", "c2f9ca2b-eb05-4a82-9809-1d7c914333ba"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CODE = os.path.join(ROOT, "poc", "call-tester")
SCENARIOS = json.load(open(os.path.join(CODE, "scenarios.json"), encoding="utf-8"))
STATE = json.load(open(os.path.join(CODE, ".state.json")))

s = boto3.Session(region_name=REGION)
connect, logs, lam = s.client("connect"), s.client("logs"), s.client("lambda")


def wait_end(contact_id, limit=420):
    for _ in range(limit // 5):
        c = connect.describe_contact(InstanceId=IID, ContactId=contact_id)["Contact"]
        if c.get("DisconnectTimestamp"):
            return c
        time.sleep(5)
    connect.stop_contact(InstanceId=IID, ContactId=contact_id)
    return connect.describe_contact(InstanceId=IID, ContactId=contact_id)["Contact"]


def dialogue(contact_id, started):
    time.sleep(10)  # log delivery
    events = logs.filter_log_events(logGroupName="/aws/lambda/call-tester", startTime=int(started.timestamp() * 1000),
                                    filterPattern=f'"{contact_id}"').get("events", [])
    turns = [json.loads(e["message"]) for e in events if e["message"].startswith("{")]
    for t in sorted(turns, key=lambda t: t["turn"]):
        print(f"  line : {t['heard'] or '(silence)'}")
        if t["said"]:
            print(f"  me   : {t['said']}")
    return turns


def inbound_contact(started, ended, tester_id):
    r = connect.search_contacts(InstanceId=IID, TimeRange={"Type": "INITIATION_TIMESTAMP", "StartTime": started - dt.timedelta(seconds=5),
                                                           "EndTime": ended}, SearchCriteria={"Channels": ["VOICE"]}, MaxResults=20)
    ids = [c["Id"] for c in r["Contacts"] if c["InitiationMethod"] == "INBOUND" and c["Id"] != tester_id]
    return ids[0] if ids else None


def route_b_extras(attrs, started):
    env = lam.get_function_configuration(FunctionName="voice-agent-api")["Environment"]["Variables"]
    if attrs.get("agreementId"):
        item = s.resource("dynamodb").Table(env["AGREEMENTS_TABLE"]).get_item(Key={"agreementId": attrs["agreementId"]}).get("Item")
        print("  agreement:", json.dumps(item, default=str, ensure_ascii=False) if item else "not found")
    print("  transcript in S3:", attrs.get("transcriptS3") or "(not yet: the post-call webhook can take a minute)")


def run(name):
    sc = SCENARIOS[name]
    started = dt.datetime.now(dt.timezone.utc)
    tester_id = connect.start_outbound_voice_contact(
        InstanceId=IID, ContactFlowId=STATE["flowId"], DestinationPhoneNumber=sc["line"], SourcePhoneNumber=sc["from"],
        Attributes={"scenario": name, "lang": sc["locale"][:2], "testRun": started.strftime("%Y%m%dT%H%M%S")})["ContactId"]
    print(f"\n== {name}: {sc['description']}\n  tester contact {tester_id}", flush=True)
    tester = wait_end(tester_id)
    turns = dialogue(tester_id, started)
    target = inbound_contact(started, dt.datetime.now(dt.timezone.utc), tester_id)
    attrs = {}
    if target:
        time.sleep(int(os.environ.get("POST_CALL_WAIT", "45")))  # route B writes attributes after the call
        attrs = connect.get_contact_attributes(InstanceId=IID, InitialContactId=target)["Attributes"]
    got = {k: attrs.get(k) for k in sc["expect"]}
    ok = bool(turns) and got == sc["expect"]
    print(f"  line contact {target} | tester ended: {tester.get('DisconnectReason')} | turns: {len(turns)}")
    print(f"  expected {sc['expect']} got {got} -> {'OK' if ok else 'FAIL'}")
    if sc["line"] == "+17752550671":
        route_b_extras(attrs, started)
    return ok


if __name__ == "__main__":
    results = {n: run(n) for n in (sys.argv[1:] or list(SCENARIOS))}
    print("\n", json.dumps(results))
    sys.exit(0 if all(results.values()) else 1)
