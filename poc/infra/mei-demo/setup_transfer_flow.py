#!/usr/bin/env python3
"""Transfer flows for the quick connects: Connect's "Default queue transfer" and "Default agent transfer", each plus
one step that opens "CS - Guide - Agent Transfer" for whoever answers. Points the demo quick connects at them and
keeps a quick connect to the supervisor (added 2026-11-12) on every collections queue. Re-runnable.

    AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> EXPECTED_ACCOUNT=<account> DEMO_PREFIX=demo python3 setup_transfer_flow.py
"""
import json

import setup_guide_flow
import setup_part_a as s
from names import DISPLAY_PREFIX

c, IID = s.connect, s.IID
NAME = s.FLOW_NAMES["queue-transfer"]


AGENT_NAME = f"{DISPLAY_PREFIX}Agent Transfer - With Context"
SUPERVISOR = f"{s.PREFIX}.supervisor"
SUPERVISOR_QC = f"{DISPLAY_PREFIX}Transfer to Supervisor"


def ensure(kind="QUEUE_TRANSFER", name=NAME, default_name="Default queue transfer"):
    guide_arn = setup_guide_flow.ensure("guide-agent-transfer")
    flows = c.list_contact_flows(InstanceId=IID, ContactFlowTypes=[kind], MaxResults=1000)["ContactFlowSummaryList"]
    default = next(f for f in flows if f["Name"] == default_name)
    base = json.loads(c.describe_contact_flow(InstanceId=IID, ContactFlowId=default["Id"])["ContactFlow"]["Content"])
    import setup_wrapup
    hooks = {"DefaultAgentUI": guide_arn, "DisconnectAgentUI": setup_wrapup.ensure()}
    base["Actions"].insert(0, s.act("GuideHook", "UpdateContactEventHooks", {"EventHooks": hooks},
                                    base["StartAction"], s.err(base["StartAction"], s.NM)))
    # Flow logging is per contact: without this the transferred leg and its guides leave no log (2026-11-11)
    base["Actions"].insert(0, s.act("LogOn", "UpdateFlowLoggingBehavior", {"FlowLoggingBehavior": "Enabled"}, "GuideHook", []))
    base["StartAction"] = "LogOn"
    content = json.dumps(s.layout(base))
    existing = next((f for f in flows if f["Name"] == name), None)
    if existing:
        c.update_contact_flow_content(InstanceId=IID, ContactFlowId=existing["Id"], Content=content)
        print("flow updated:", name)
        return existing["Id"]
    fid = c.create_contact_flow(InstanceId=IID, Name=name, Type=kind, Content=content,
                                Description=f"{default_name} plus the agent-transfer guide")["ContactFlowId"]
    print("flow created:", name)
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


def ensure_supervisor_quick_connect(agent_flow_id):
    """Quick connect of type user: the call rings the supervisor, who sees the same transfer guide."""
    user = next(u for u in c.list_users(InstanceId=IID)["UserSummaryList"] if u["Username"] == SUPERVISOR)
    cfg = {"QuickConnectType": "USER", "UserConfig": {"UserId": user["Id"], "ContactFlowId": agent_flow_id}}
    found = next((q for q in c.list_quick_connects(InstanceId=IID)["QuickConnectSummaryList"] if q["Name"] == SUPERVISOR_QC), None)
    if found:
        c.update_quick_connect_config(InstanceId=IID, QuickConnectId=found["Id"], QuickConnectConfig=cfg)
        qc_id = found["Id"]
    else:
        qc_id = c.create_quick_connect(InstanceId=IID, Name=SUPERVISOR_QC, QuickConnectConfig=cfg,
                                       Description="Transfer the call to the supervisor")["QuickConnectId"]
        print("quick connect created:", SUPERVISOR_QC)
    # Agents see the quick connects of the queues in their routing profile: add it to every demo queue that has the others.
    for q in c.list_queues(InstanceId=IID, QueueTypes=["STANDARD"])["QueueSummaryList"]:
        names = [x["Name"] for x in c.list_queue_quick_connects(InstanceId=IID, QueueId=q["Id"])["QuickConnectSummaryList"]]
        if any(n.startswith(DISPLAY_PREFIX) for n in names) and SUPERVISOR_QC not in names:
            c.associate_queue_quick_connects(InstanceId=IID, QueueId=q["Id"], QuickConnectIds=[qc_id])
            print("on queue:", q["Name"])


if __name__ == "__main__":
    point_quick_connects(ensure())
    ensure_supervisor_quick_connect(ensure("AGENT_TRANSFER", AGENT_NAME, "Default agent transfer"))
