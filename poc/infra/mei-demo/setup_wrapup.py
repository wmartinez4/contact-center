#!/usr/bin/env python3
"""Disposition (wrap-up) for collections calls.

- View "CS - Collections Wrap-up": customer, account and queue at the top; a Disposition dropdown with collections
  outcomes, follow-up, promise date and notes. Built from Connect's "After Contact Work" view.
- Flow "CS - Guide - Wrap-up": shows that view to the agent when the call ends ("Disconnect flow for agent UI")
  and writes the answers back onto the call as contact attributes (disposition, followUp, promiseDate, wrapUpNotes).
Re-runnable.

    AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> EXPECTED_ACCOUNT=<account> DEMO_PREFIX=demo python3 setup_wrapup.py
"""
import json
import os

import setup_part_a as s
from names import DISPLAY_PREFIX

c, IID = s.connect, s.IID
VIEW = DISPLAY_PREFIX + "Collections Wrap-up"
DISPOSITIONS = ["Promise to pay", "Payment made", "Payment arrangement set", "Callback requested", "Dispute",
                "Hardship - referred", "Refused to pay", "Information only", "Wrong party", "Transferred"]


BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "acw_base_template.json")  # Connect's "After Contact Work" view, as published


def template():
    """Connect's After Contact Work template with collections choices; same component structure, so it validates."""
    t = json.load(open(BASE))
    texts = {"$.ContactWrapUp_Header_Title": "Call wrap-up",
             "$.ContactWrapUp_Header_Description": "Choose how the call ended. It is saved with the call for reports.",
             "$.Disposition_Header_Title": "Disposition", "$.Disposition_Header_Description": "",
             "$.ContactSummary_Header_Title": "Summary", "$.ContactSummary_Header_Description": "",
             "$.AdditionalNotes_Header_Title": "Promise or callback", "$.AdditionalNotes_Header_Description": ""}

    def fix(node):
        if isinstance(node, list):
            return [fix(n) for n in node if not (isinstance(n, dict) and n.get("_id") in ("Driver_Dropdown", "CustomerSatisfactionRating_Dropdown"))]
        if not isinstance(node, dict):
            return texts.get(node, node) if isinstance(node, str) else node
        node = {k: fix(v) for k, v in node.items()}
        props, nid = node.get("Props", {}), node.get("_id")
        if nid == "AttributeBar":
            props["Attributes"] = [{"Label": "Customer", "Value": "$.CustomerName"}, {"Label": "Account", "Value": "$.Account"},
                                   {"Label": "Queue", "Value": "$.Queue"}]
        elif nid == "Category_Dropdown":
            props.update({"Options": [{"Label": o, "Value": o} for o in DISPOSITIONS], "Label": "Disposition", "Name": "Disposition"})
            props["DefaultValue"] = [""]
        elif nid == "FollowUp_Dropdown":
            props["DefaultValue"] = [""]
        elif nid == "Resolved_Dropdown":
            props["DefaultValue"] = [""]
        elif nid == "ContactSummary_TextArea":
            props.update({"DefaultValue": "$.Summary", "Label": "Call summary", "Name": "Summary",
                          "HelperText": "Edit if needed. Saved with the call."})
        elif nid == "AdditionalNotes_TextArea":
            props.update({"DefaultValue": "", "Label": "Date and notes", "Name": "Notes",
                          "HelperText": "For a promise to pay or a callback: the date (for example 2026-11-28) and any detail."})
        elif "description" in props and isinstance(props["description"], str) and props["description"].startswith("$."):
            props["description"] = texts.get(props["description"], "")
        return node
    return fix(t)


def ensure_view():
    content = {"Template": json.dumps(template()), "Actions": ["Submit"]}
    views = c.list_views(InstanceId=IID, Type="CUSTOMER_MANAGED").get("ViewsSummaryList", [])
    v = next((v for v in views if v["Name"] == VIEW), None)
    if v:
        c.update_view_content(InstanceId=IID, ViewId=v["Id"], Status="PUBLISHED", Content=content)
        print("view updated:", VIEW)
        return v["Arn"]
    r = c.create_view(InstanceId=IID, Name=VIEW, Status="PUBLISHED", Content=content, Description="Disposition for collections calls")
    print("view created:", VIEW)
    return r["View"]["Arn"]


def flow_content(view_arn):
    act, err, NM, NC = s.act, s.err, s.NM, s.NC
    form = "$.Views.ViewResultData"  # custom view: fields at the top level (FormData is only for the AWS-managed Form view)
    a = [
        act("WrapUp", "ShowView", {"ViewResource": {"Id": view_arn}, "InvocationTimeLimitSeconds": "1800", "ViewData": {
            "CustomerName": "$.Attributes.customerName", "Account": "$.Attributes.caseCode",
            "Queue": "$.Attributes.queueLabel", "Summary": "$.Attributes.customerSummary"}},
            "End", err("End", NM, NC, "TimeLimitExceeded"), [s.eq("Save", "Submit")]),
        # Kept on the guide contact too, to read the exact output shape in a test
        act("Save", "UpdateContactAttributes", {"Attributes": {
            "disposition": f"{form}.Disposition.0", "followUp": f"{form}.FollowUp.0", "resolved": f"{form}.Resolved.0",
            "wrapUpSummary": f"{form}.Summary", "wrapUpNotes": f"{form}.Notes"}, "TargetContact": "Related"}, "End", err("End", NM)),
        act("End", "DisconnectParticipant", {}),
    ]
    return json.dumps(s.layout({"Version": "2019-10-30", "StartAction": "WrapUp", "Metadata": {}, "Actions": a}))


def ensure_flow(view_arn):
    name = s.FLOW_NAMES["guide-wrapup"]
    flows = c.list_contact_flows(InstanceId=IID, ContactFlowTypes=["CONTACT_FLOW"], MaxResults=1000)["ContactFlowSummaryList"]
    f = next((f for f in flows if f["Name"] == name), None)
    if f:
        c.update_contact_flow_content(InstanceId=IID, ContactFlowId=f["Id"], Content=flow_content(view_arn))
        print("flow updated:", name)
        return f["Arn"]
    r = c.create_contact_flow(InstanceId=IID, Name=name, Type="CONTACT_FLOW", Content=flow_content(view_arn),
                              Description="Agent workspace guide at the end of a call: disposition saved on the call")
    print("flow created:", name)
    return r["ContactFlowArn"]


def ensure():
    return ensure_flow(ensure_view())


if __name__ == "__main__":
    print(ensure())
