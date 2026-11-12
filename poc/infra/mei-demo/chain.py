#!/usr/bin/env python3
"""Rebuild the chain of legs and recordings for recent calls, grouped by master_call_id.

    AWS_PROFILE=connect-demo python3 chain.py [--hours 3]

No manual work: contact search -> describe -> attributes -> recording lookup in S3.
Contact records can take a few minutes to appear after a call ends.
"""
import argparse
import datetime as dt
from collections import defaultdict

import boto3

import os
IID = os.environ.get("CONNECT_INSTANCE_ID", "9c58815e-2730-408e-b29d-ce7e52692cdc")
PREFIX = os.environ.get("DEMO_PREFIX", "demo")
BUCKET_PREFIX = f"amazon-connect-{PREFIX}-recordings-"
REC_PREFIX = f"{PREFIX}/CallRecordings/"

ap = argparse.ArgumentParser()
ap.add_argument("--hours", type=float, default=3)
args = ap.parse_args()

sess = boto3.Session(region_name="us-east-1")
account = sess.client("sts").get_caller_identity()["Account"]
connect, s3 = sess.client("connect"), sess.client("s3")
bucket = BUCKET_PREFIX + account

end = dt.datetime.now(dt.timezone.utc)
start = end - dt.timedelta(hours=args.hours)

ids = []
token = None
while True:
    kw = dict(InstanceId=IID, TimeRange={"Type": "INITIATION_TIMESTAMP", "StartTime": start, "EndTime": end}, MaxResults=100,
              Sort={"FieldName": "INITIATION_TIMESTAMP", "Order": "ASCENDING"})
    if token:
        kw["NextToken"] = token
    r = connect.search_contacts(**kw)
    ids += [c["Id"] for c in r["Contacts"]]
    token = r.get("NextToken")
    if not token:
        break

recs = []
p = s3.get_paginator("list_objects_v2")
for page in p.paginate(Bucket=bucket, Prefix=REC_PREFIX):
    recs += [o["Key"] for o in page.get("Contents", [])]

rows = []
for cid in ids:
    c = connect.describe_contact(InstanceId=IID, ContactId=cid)["Contact"]
    attrs = connect.get_contact_attributes(InstanceId=IID, InitialContactId=cid)["Attributes"]
    rec = ", ".join(k.split(REC_PREFIX)[-1] for k in recs if cid in k)
    start_ts = c.get("InitiationTimestamp")
    end_ts = c.get("DisconnectTimestamp")
    rows.append({
        "id": cid, "initial": c.get("InitialContactId") or "(null)", "prev": c.get("PreviousContactId") or "",
        "method": c.get("InitiationMethod"), "queue": (c.get("QueueInfo") or {}).get("Id", "")[-8:],
        "agent": (c.get("AgentInfo") or {}).get("Id", "")[-8:],
        "secs": int((end_ts - start_ts).total_seconds()) if end_ts and start_ts else "",
        "master": attrs.get("master_call_id", ""), "case": attrs.get("caseCode", ""), "dept": attrs.get("department", ""), "cust": (c.get("CustomerEndpoint") or {}).get("Address", ""), "start": start_ts.strftime("%Y-%m-%d %H:%M:%S") if start_ts else "", "end": end_ts.strftime("%H:%M:%S") if end_ts else "", "rec": rec if rec else "(none)",
        "time": start_ts.strftime("%H:%M:%S") if start_ts else "",
    })

groups = defaultdict(list)
for r in rows:
    groups[r["master"] or r["initial"] if r["initial"] != "(null)" else r["id"]].append(r)
for key, legs in groups.items():
    print(f"\nCALL {key}")
    for i, r in enumerate(legs, 1):
        print(f"  leg {i}  {r['time']}  {r['method']:<10} contact={r['id']}  initial={r['initial']}  prev={r['prev'] or '-'}")
        print(f"         customer={r['cust']} start={r['start']} end={r['end']} secs={r['secs']} department={r['dept'] or '-'}")
        print(f"         queue=..{r['queue']} agent=..{r['agent']} master_call_id={r['master'] or '(missing)'} recording={r['rec']}")
if not rows:
    print("No contacts in the window yet.")
