#!/usr/bin/env python3
"""Workspaces that replace Connect's default home page (with AWS news and links) for the demo users.

- demo-agents: home and agent experience are the agent workspace, so agents land on it after login.
- demo-supervisors: a short welcome page (detail view, no buttons) with what to open for the demo.
Both use a neutral theme. Re-runnable: existing workspaces are updated, pages and users added if missing.

    AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> EXPECTED_ACCOUNT=<account> python3 setup_workspaces.py
"""
import base64
import json
import os
import sys

import boto3
from botocore.exceptions import ClientError

s = boto3.Session()
account = s.client("sts").get_caller_identity()["Account"]
if account != os.environ["EXPECTED_ACCOUNT"]:
    sys.exit("Wrong account")
c = s.client("connect")
IID = os.environ["CONNECT_INSTANCE_ID"]
PREFIX = os.environ.get("DEMO_PREFIX", "demo")
ALIAS = c.describe_instance(InstanceId=IID)["Instance"]["InstanceAlias"]
BASE = f"https://{ALIAS}.my.connect.aws"
AGENT_VIEW = f"arn:aws:connect:{s.region_name}:aws:view/agent-workspace-modern"
HOME_VIEW = f"arn:aws:connect:{s.region_name}:aws:view/detail"
TITLE = "Committed Staff · Contact Center"
# Optional header logo (white, for the dark header): LOGO_PATH=/path/to/logo.svg
LOGO_PATH = os.environ.get("LOGO_PATH")

# Only the top bar is branded (deep purple, white logo); everything else keeps Connect's default look.
# Dark mode is left to Connect's default: a custom dark palette made the user-settings panel unreadable.
THEME = {"Light": {"Palette": {
    "Header": {"Background": "#2A0F5E", "Text": "#FFFFFF", "TextHover": "#C7C8FF", "InvertActionsColors": True}}}}

SUPERVISOR_HOME = {
    "Heading": "Welcome to the contact center",
    "Description": "All customer data on this instance is simulated.",
    "Style": {"--container-background-color": "transparent", "--container-border-width": "0px"},
}


def users():
    out = {}
    for u in c.list_users(InstanceId=IID)["UserSummaryList"]:
        out[u["Username"]] = u["Arn"]
    return out


def ensure_workspace(name, description, old_name):
    """Visible names carry no prefix; old_name finds workspaces created before the rename."""
    for w in c.list_workspaces(InstanceId=IID).get("WorkspaceSummaryList", []):
        if w["Name"] in (name, old_name):
            c.update_workspace_metadata(InstanceId=IID, WorkspaceId=w["Id"], Name=name, Description=description)
            c.update_workspace_theme(InstanceId=IID, WorkspaceId=w["Id"], Theme=THEME)
            c.update_workspace_metadata(InstanceId=IID, WorkspaceId=w["Id"], Title=TITLE)
            print("workspace updated:", name)
            return w["Id"]
    wid = c.create_workspace(InstanceId=IID, Name=name, Description=description, Title=TITLE, Theme=THEME)["WorkspaceId"]
    print("workspace created:", name)
    return wid


def ensure_page(wid, page, view_arn, input_data=None):
    existing = {p["Page"]: p for p in c.list_workspace_pages(InstanceId=IID, WorkspaceId=wid).get("WorkspacePageList", [])}
    kwargs = {"InstanceId": IID, "WorkspaceId": wid, "ResourceArn": view_arn, "Page": page}
    if input_data is not None:
        kwargs["InputData"] = json.dumps(input_data)
    if page in existing:
        c.update_workspace_page(**kwargs)
    else:
        c.create_workspace_page(**kwargs)
    print("  page set:", page)


def set_logo(wid):
    if not LOGO_PATH:
        return
    ext = LOGO_PATH.rsplit(".", 1)[-1].lower()
    mime = {"svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}[ext]
    with open(LOGO_PATH, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    for media_type in ("IMAGE_LOGO_LIGHT_HORIZONTAL", "IMAGE_LOGO_DARK_HORIZONTAL"):  # header is dark in both modes
        c.import_workspace_media(InstanceId=IID, WorkspaceId=wid, MediaType=media_type, MediaSource=f"data:{mime};base64,{data}")
    print("  logo set")


def assign(wid, usernames):
    arns = users()
    targets = [arns[u] for u in usernames if u in arns]
    try:
        c.associate_workspace(InstanceId=IID, WorkspaceId=wid, ResourceArns=targets)
    except ClientError as e:
        if e.response["Error"]["Code"] not in ("ResourceConflictException", "DuplicateResourceException"):
            raise
    c.update_workspace_visibility(InstanceId=IID, WorkspaceId=wid, Visibility="ASSIGNED")
    print("  assigned:", [u for u in usernames if u in arns])


agents = ensure_workspace("Agents", "Agents land directly on the agent workspace", f"{PREFIX}-agents")
ensure_page(agents, "connect:HOME", AGENT_VIEW)
ensure_page(agents, "connect:AGENT", AGENT_VIEW)
set_logo(agents)
assign(agents, [f"{PREFIX}.agent1", f"{PREFIX}.agent2", f"{PREFIX}.caller", f"{PREFIX}.caller2"])

sup = ensure_workspace("Supervisors", "Supervisor and admin: clean home page", f"{PREFIX}-supervisors")
ensure_page(sup, "connect:HOME", HOME_VIEW, SUPERVISOR_HOME)
ensure_page(sup, "connect:AGENT", AGENT_VIEW)
set_logo(sup)
assign(sup, [f"{PREFIX}.supervisor", f"{PREFIX}.admin"])
