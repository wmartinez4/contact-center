#!/usr/bin/env python3
"""Queue transfer flow for the quick connects: Connect's "Default queue transfer" plus one step that opens
"CS - Guide - Agent Transfer" for the agent who answers. Points the demo quick connects at it. Re-runnable.

    AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> EXPECTED_ACCOUNT=<account> DEMO_PREFIX=demo python3 setup_transfer_flow.py
"""
import json

import setup_guide_flow
import setup_part_a as s
from names import DISPLAY_PREFIX

c, IID = s.connect, s.IID
NAME = s.FLOW_NAMES["queue-transfer"]


def ensure():
    guide_arn = setup_guide_flow.ensure("guide-agent-transfer")
    flows = c.list_contact_flows(InstanceId=IID, ContactFlowTypes=["QUEUE_TRANSFER"], MaxResults=1000)["ContactFlowSummaryList"]
    default = next(f for f in flows if f["Name"] == "Default queue transfer")
    base = json.loads(c.describe_contact_flow(InstanceId=IID, ContactFlowId=default["Id"])["ContactFlow"]["Content"])
    import setup_wrapup
    hooks = {"DefaultAgentUI": guide_arn, "DisconnectAgentUI": setup_wrapup.ensure()}
    base["Actions"].insert(0, s.act("GuideHook", "UpdateContactEventHooks", {"EventHooks": hooks},
                                    base["StartAction"], s.err(base["StartAction"], s.NM)))
    # Flow logging is per contact: without this the transferred leg and its guides leave no log (2026-11-11)
    base["Actions"].insert(0, s.act("LogOn", "UpdateFlowLoggingBehavior", {"FlowLoggingBehavior": "Enabled"}, "GuideHook", []))
    base["StartAction"] = "LogOn"
    content = json.dumps(s.layout(base))
    existing = next((f for f in flows if f["Name"] == NAME), None)
    if existing:
        c.update_contact_flow_content(InstanceId=IID, ContactFlowId=existing["Id"], Content=content)
        print("flow updated:", NAME)
        return existing["Id"]
    fid = c.create_contact_flow(InstanceId=IID, Name=NAME, Type="QUEUE_TRANSFER", Content=content,
                                Description="Default queue transfer plus the agent-transfer guide")["ContactFlowId"]
    print("flow created:", NAME)
    return fid


def point_quick_connects(fid):
    for qc in c.list_quick_connects(InstanceId=IID)["QuickConnectSummaryList"]:
        if not qc["Name"].startswith(DISPLAY_PREFIX):
            continue
        cfg = c.describe_quick_connect(InstanceId=IID, QuickConnectId=qc["Id"])["QuickConnect"]["QuickConnectConfig"]
        if cfg["QuickConnectType"] != "QUEUE":
            continue
        cfg["QueueConfig"]["ContactFlowId"] = fid
        c.update_quick_connect_config(InstanceId=IID, QuickConnectId=qc["Id"], QuickConnectConfig=cfg)
        print("quick connect uses it:", qc["Name"])


if __name__ == "__main__":
    point_quick_connects(ensure())
