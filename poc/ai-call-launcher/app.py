"""Supervisor app "Call with AI" for the Amazon Connect workspace: lists the demo customers and starts an outbound
call in which Connect dials the customer and hands the call to the ElevenLabs agent (route B flow).

Served by a Lambda function URL:
  GET  /                  the page (loaded inside the workspace as a third-party app)
  GET  /customers?agent=  the customers and whether each one can be called
  POST /call              {"account", "agent"} starts the call
  GET  /status?contact=   the call's progress and outcome
  GET  /history?agent=    the latest outbound AI calls (from the route B calls table)

Demo-grade access check: the page sends the user's ARN from the workspace SDK and the call is only placed when that
user has a supervisor or admin security profile and is logged in. The ARN is not signed, so production needs real
authentication (for example Cognito or the identity provider) in front of this API.
"""
import json
import os
import re

import boto3

IID = os.environ["CONNECT_INSTANCE_ID"]
DOMAIN = os.environ["PROFILES_DOMAIN"]
FLOW_ID = os.environ["FLOW_ID"]
CALLER_ID = os.environ["CALLER_ID"]
ALLOWED_PROFILES = set(json.loads(os.environ["ALLOWED_SECURITY_PROFILES"]))
MAX_ACCOUNT = 15
HISTORY_SIZE = 20
FICTIONAL = re.compile(r"^\+1\d{3}55501\d{2}$")  # 555-01xx numbers do not exist
# Only these numbers may be dialed: some demo profiles carry real people's phones.
TEST_DESTINATIONS = set(json.loads(os.environ.get("TEST_DESTINATIONS", "[]")))

connect = boto3.client("connect")
calls = boto3.resource("dynamodb").Table(os.environ["CALLS_TABLE"])
profiles = boto3.client("customer-profiles")
PAGE = open(os.path.join(os.path.dirname(__file__), "page.html"), encoding="utf-8").read()


def _json(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body, ensure_ascii=False)}


def _supervisor(agent_arn):
    """Username when the ARN is a logged-in user of this instance with an allowed security profile."""
    if not agent_arn or f"instance/{IID}/agent/" not in agent_arn:
        return None
    user_id = agent_arn.rsplit("/", 1)[1]
    user = connect.describe_user(InstanceId=IID, UserId=user_id)["User"]
    if not ALLOWED_PROFILES & set(user["SecurityProfileIds"]):
        return None
    data = connect.get_current_user_data(InstanceId=IID, Filters={"Agents": [user_id]})["UserDataList"]
    return user["Username"] if data else None


def _customers():
    out = []
    for account in range(1, MAX_ACCOUNT + 1):
        items = profiles.search_profiles(DomainName=DOMAIN, KeyName="_account", Values=[str(account)])["Items"]
        if not items:
            continue
        p, attrs = items[0], items[0].get("Attributes") or {}
        phone = p.get("PhoneNumber") or p.get("MobilePhoneNumber") or ""
        special = attrs.get("specialStatus") or ""
        if special:
            blocked = "Special status: handled by a specialist"
        elif not phone or FICTIONAL.match(phone):
            blocked = "Fictional phone number"
        elif phone not in TEST_DESTINATIONS:
            blocked = "Not on the test number list"
        else:
            blocked = ""
        out.append({"account": str(account), "name": f"{p.get('FirstName', '')} {p.get('LastName', '')}".strip(),
                    "phone": phone, "daysPastDue": attrs.get("daysPastDue", ""), "balance": attrs.get("balance", ""),
                    "specialStatus": special, "blocked": blocked})
    return out


def _call(body):
    user = _supervisor(body.get("agent"))
    if not user:
        return _json(403, {"error": "Only a logged-in supervisor can start AI calls."})
    customer = next((c for c in _customers() if c["account"] == str(body.get("account"))), None)
    if not customer:
        return _json(404, {"error": "Account not found."})
    if customer["blocked"]:
        return _json(409, {"error": customer["blocked"]})
    contact = connect.start_outbound_voice_contact(
        InstanceId=IID, ContactFlowId=FLOW_ID, DestinationPhoneNumber=customer["phone"], SourcePhoneNumber=CALLER_ID,
        Attributes={"direction": "outbound", "requestedBy": user, "requestedAccount": customer["account"]})["ContactId"]
    print(json.dumps({"call": contact, "account": customer["account"], "requestedBy": user}))
    return _json(200, {"contactId": contact, "customer": customer["name"]})


def _status(contact_id):
    c = connect.describe_contact(InstanceId=IID, ContactId=contact_id)["Contact"]
    attrs = connect.get_contact_attributes(InstanceId=IID, InitialContactId=contact_id)["Attributes"]
    if c.get("DisconnectTimestamp"):
        state = "ended"
    elif c.get("ConnectedToSystemTimestamp"):
        state = "in_call"
    else:
        state = "dialing"
    return _json(200, {"state": state, "outcome": attrs.get("aiOutcome", ""), "agreement": attrs.get("agreementSummary", ""),
                       "summary": attrs.get("aiCallSummary", ""), "handoff": attrs.get("handoffSummary", "")})


def _history():
    """Latest outbound calls handled by Sofia, newest first. The calls table is small in the sandbox, so a scan is fine;
    production would query an index by direction and date."""
    items, kwargs = [], {"FilterExpression": "#d = :o", "ExpressionAttributeNames": {"#d": "direction"},
                     "ExpressionAttributeValues": {":o": "outbound"}}
    while True:
        page = calls.scan(**kwargs)
        items += page["Items"]
        if "LastEvaluatedKey" not in page:
            break
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    items = sorted(items, key=lambda i: int(i.get("createdAt", 0)), reverse=True)[:HISTORY_SIZE]
    names = {c["account"]: c["name"] for c in _customers()}
    out = []
    for i in items:
        try:
            attrs = connect.get_contact_attributes(InstanceId=IID, InitialContactId=i["contactId"])["Attributes"]
        except connect.exceptions.ResourceNotFoundException:
            attrs = {}
        out.append({"contactId": i["contactId"], "startedAt": int(i.get("createdAt", 0)), "account": i.get("account", ""),
                    "customer": names.get(i.get("account", ""), ""), "outcome": i.get("outcome", ""),
                    "summary": i.get("summary", ""), "startedBy": attrs.get("requestedBy") or attrs.get("campaign") or ""})
    return out


def handler(event, _context):
    method = event["requestContext"]["http"]["method"]
    path = event.get("rawPath", "/")
    query = event.get("queryStringParameters") or {}
    if method == "GET" and path == "/":
        return {"statusCode": 200, "headers": {"Content-Type": "text/html; charset=utf-8"}, "body": PAGE}
    if method == "GET" and path == "/customers":
        if not _supervisor(query.get("agent")):
            return _json(403, {"error": "Only available to logged-in supervisors."})
        return _json(200, {"customers": _customers()})
    if method == "POST" and path == "/call":
        return _call(json.loads(event.get("body") or "{}"))
    if method == "GET" and path == "/history":
        if not _supervisor(query.get("agent")):
            return _json(403, {"error": "Only available to logged-in supervisors."})
        return _json(200, {"calls": _history()})
    if method == "GET" and path == "/status" and query.get("contact"):
        if not _supervisor(query.get("agent")):
            return _json(403, {"error": "Only available to logged-in supervisors."})
        return _status(query["contact"])
    return _json(404, {"error": "not found"})
