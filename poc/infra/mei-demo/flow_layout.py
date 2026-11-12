"""Give a flow's blocks readable positions in the flow designer.

Flows created through the API have no block positions, so the designer piles
them up. This lays blocks out left to right by distance from the start block.
Only Metadata changes; Actions stay identical (checked before writing).

Usage:
  AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> EXPECTED_ACCOUNT=<account> \
  python flow_layout.py <flow-name> --copy-to <new-flow-name>   # new flow, source untouched
  python flow_layout.py <flow-name> --in-place                  # rewrites the flow's layout
"""
import argparse
import json
import os
import sys

import boto3

COL_W, ROW_GAP, X0, Y0 = 300, 40, 220, 40


def targets(action):
    t = action.get("Transitions", {})
    out = [t.get("NextAction")]
    out += [c.get("NextAction") for c in t.get("Conditions", [])]
    out += [e.get("NextAction") for e in t.get("Errors", [])]
    return [x for x in out if x]


def height(action):
    t = action.get("Transitions", {})
    return 110 + 28 * (len(t.get("Conditions", [])) + len(t.get("Errors", [])))


def layout(flow):
    actions = {a["Identifier"]: a for a in flow["Actions"]}
    depth = {flow["StartAction"]: 0}
    queue = [flow["StartAction"]]
    while queue:
        cur = queue.pop(0)
        for nxt in targets(actions[cur]):
            if nxt in actions and nxt not in depth:
                depth[nxt] = depth[cur] + 1
                queue.append(nxt)
    last = max(depth.values(), default=0) + 1
    columns = {}
    for ident in actions:  # keep the original order inside each column
        columns.setdefault(depth.get(ident, last), []).append(ident)
    meta = {}
    for col, idents in columns.items():
        y = Y0
        for ident in idents:
            meta[ident] = {"position": {"x": X0 + col * COL_W, "y": y}}
            y += height(actions[ident]) + ROW_GAP
    flow.setdefault("Metadata", {})
    flow["Metadata"]["entryPointPosition"] = {"x": 20, "y": Y0}
    flow["Metadata"]["ActionMetadata"] = meta
    return flow


def main():
    p = argparse.ArgumentParser()
    p.add_argument("flow")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--copy-to")
    g.add_argument("--in-place", action="store_true")
    args = p.parse_args()

    s = boto3.Session()
    if s.client("sts").get_caller_identity()["Account"] != os.environ["EXPECTED_ACCOUNT"]:
        sys.exit("Wrong account")
    c, inst = s.client("connect"), os.environ["CONNECT_INSTANCE_ID"]
    flows = {f["Name"]: f for f in c.list_contact_flows(InstanceId=inst, MaxResults=1000)["ContactFlowSummaryList"]}
    src = c.describe_contact_flow(InstanceId=inst, ContactFlowId=flows[args.flow]["Id"])["ContactFlow"]
    original = json.loads(src["Content"])
    laid = layout(json.loads(src["Content"]))
    assert laid["Actions"] == original["Actions"], "actions changed"
    content = json.dumps(laid)

    if args.in_place:
        c.update_contact_flow_content(InstanceId=inst, ContactFlowId=src["Id"], Content=content)
        print("layout updated in", args.flow)
    elif args.copy_to in flows:
        c.update_contact_flow_content(InstanceId=inst, ContactFlowId=flows[args.copy_to]["Id"], Content=content)
        print("updated copy", args.copy_to)
    else:
        r = c.create_contact_flow(InstanceId=inst, Name=args.copy_to, Type=src["Type"], Content=content,
                                  Description=f"Sandbox copy of {args.flow} for live edits; not used by the demo")
        print("created copy", args.copy_to, r["ContactFlowId"])


if __name__ == "__main__":
    main()
