"""Voice agent API for the ElevenLabs collections demo (route B, see ../diseno.md).

One Lambda serves three callers:
- Amazon Connect flows invoke it directly (event has "Details"): identify, prepare_handoff, outcome.
- ElevenLabs calls it over API Gateway: the conversation initiation webhook and the agent's webhook tools.
- ElevenLabs post-call webhook: transcript and audio to S3, summary onto the Connect contact.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import boto3
from boto3.dynamodb.conditions import Key

from customers import find_by_account, find_by_phone
from rules import case_view, propose_plan

log = logging.getLogger()
log.setLevel(logging.INFO)

DOMAIN = os.environ["PROFILES_DOMAIN"]
INSTANCE_ID = os.environ["CONNECT_INSTANCE_ID"]
CALLS = boto3.resource("dynamodb").Table(os.environ["CALLS_TABLE"])
AGREEMENTS = boto3.resource("dynamodb").Table(os.environ["AGREEMENTS_TABLE"])
PROFILES = boto3.client("customer-profiles")
CONNECT = boto3.client("connect")
SECRETS = boto3.client("secretsmanager")
S3 = boto3.client("s3")
BUCKET = os.environ.get("ARTIFACTS_BUCKET", "")
LOCAL_TZ = ZoneInfo("America/Chicago")
PENDING_SECONDS = 300
# Route B only: test phones that should act as a given demo account (e.g. the caller2 softphone as Maria),
# without changing the profiles the main Connect demo relies on.
_api_secret = None

FIRST_MESSAGE = {
    "es": "Hola, le habla Sofía, asistente virtual del área de cuentas. Esta llamada puede ser grabada. "
          "¿Hablo con {name}, titular de la cuenta?",
    "en": "Hi, this is Sofia, a virtual assistant from the accounts team. This call may be recorded. "
          "Am I speaking with {name}, the account holder?",
}
# Caller not recognized by phone: English by default, with a short offer to switch to Spanish.
FIRST_MESSAGE_UNKNOWN = ("Hi, this is Sofia, a virtual assistant from the accounts team. This call may be recorded. "
                         "Could you tell me your account number, please? Si prefiere español, solo dígamelo.")


def handler(event, _context):
    if "Details" in event:
        return _connect(event)
    return _http(event)


# ---------- Amazon Connect (direct invocation, flat string map out) ----------

def _connect(event):
    params = event["Details"].get("Parameters", {})
    contact = event["Details"]["ContactData"]
    action = params.get("action")
    if action == "identify":
        phone = contact.get("CustomerEndpoint", {}).get("Address")
        # An account typed on the keypad (callers the flow did not recognize) wins over the phone number.
        typed_account = (params.get("accountInput") or "").strip()
        customer, _ = (find_by_account(PROFILES, DOMAIN, typed_account) if typed_account
                       else find_by_phone(PROFILES, DOMAIN, phone))
        if not customer:
            return {"found": "false", "queueArn": _queue_arn("Q-Fallback")}
        return {"found": "true", "account": customer.account, "customerName": customer.full_name,
                "language": customer.language, "canNegotiate": "false" if customer.special_status else "true",
                "queueArn": _queue_arn(_expected_queue(customer.account))}
    if action == "prepare_handoff":
        phone = contact.get("CustomerEndpoint", {}).get("Address", "")
        now = int(time.time())
        CALLS.put_item(Item={"contactId": contact["ContactId"], "phone": phone, "account": params.get("account", ""),
                             "language": params.get("language", "en"), "status": "pending", "createdAt": now,
                             "source": "connect"})
        return {"ok": "true"}
    if action == "outcome":
        item = CALLS.get_item(Key={"contactId": contact["ContactId"]}).get("Item") or {}
        queue = _queue_arn(_expected_queue(item["account"])) if item.get("account") else _queue_arn("Q-Fallback")
        return {"outcome": item.get("outcome", "none"), "summary": item.get("summary", "")[:250],
                "language": item.get("language", "en"), "queueArn": queue}
    return {"error": f"unknown action {action}"}


# Demo queue keys (profile attribute expectedQueue) and their names in the instance.
QUEUE_NAMES = {"Q-Current": "CS - Collections - Current", "Q-1-8": "CS - Collections - 1 to 8 days",
               "Q-9-15": "CS - Collections - 9 to 15 days", "Q-16-30": "CS - Collections - 16 to 30 days",
               "Q-31Plus": "CS - Collections - 31+ days", "Q-Redemptions": "CS - Redemptions",
               "Q-EPD": "CS - Early Payment Default", "Q-Fallback": "CS - General Assistance"}
_queue_arns = None


def _queue_arn(key):
    global _queue_arns
    if _queue_arns is None:
        pages = CONNECT.get_paginator("list_queues").paginate(InstanceId=INSTANCE_ID, QueueTypes=["STANDARD"])
        _queue_arns = {q["Name"]: q["Arn"] for page in pages for q in page["QueueSummaryList"]}
    return _queue_arns.get(QUEUE_NAMES.get(key, ""), _queue_arns.get(QUEUE_NAMES["Q-Fallback"], ""))


def _expected_queue(account):
    items = PROFILES.search_profiles(DomainName=DOMAIN, KeyName="_account", Values=[account]).get("Items", [])
    return (items[0].get("Attributes") or {}).get("expectedQueue", "Q-Fallback") if items else "Q-Fallback"


# ---------- HTTP (ElevenLabs) ----------

def _http(event):
    path = event.get("rawPath", "")
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode()
    body = json.loads(raw)
    allowed = _post_call_authorized(event, raw) if path == "/elevenlabs/post-call" else _authorized(event)
    if not allowed:
        return _resp(401, {"error": "unauthorized"})
    try:
        if path == "/elevenlabs/init":
            return _resp(200, _init(body))
        if path == "/elevenlabs/post-call":
            return _resp(200, _post_call(body))
        if path.startswith("/tools/"):
            return _resp(200, TOOLS[path.removeprefix("/tools/")](body))
    except KeyError as missing:
        return _resp(400, {"error": f"missing {missing}"})
    return _resp(404, {"error": "not found"})


def _authorized(event):
    global _api_secret
    if _api_secret is None:
        _api_secret = SECRETS.get_secret_value(SecretId=os.environ["API_SECRET_ARN"])["SecretString"]
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    return headers.get("x-api-secret") == _api_secret


def _init(body):
    """Conversation initiation webhook: links the call to its Connect contact and briefs the agent."""
    phone, call_sid = body.get("caller_id", ""), body.get("call_sid", "")
    call = _take_pending(phone, call_sid)
    customer, _ = (find_by_account(PROFILES, DOMAIN, call["account"]) if call.get("account")
                   else find_by_phone(PROFILES, DOMAIN, phone))
    today = _today()
    today_text = f"{today.isoformat()} ({today:%A})"
    if not customer:
        return {"type": "conversation_initiation_client_data",
                "dynamic_variables": {"contact_id": call["contactId"], "customer_name": "", "first_name": "",
                                      "language": "en", "today": today_text, "caller_known": "false"},
                "conversation_config_override": {"agent": {"language": "en", "first_message": FIRST_MESSAGE_UNKNOWN}}}
    lang = customer.language if customer.language in FIRST_MESSAGE else "en"
    CALLS.update_item(Key={"contactId": call["contactId"]}, UpdateExpression="SET account = :a, #l = :l",
                      ExpressionAttributeNames={"#l": "language"}, ExpressionAttributeValues={":a": customer.account, ":l": lang})
    return {
        "type": "conversation_initiation_client_data",
        "dynamic_variables": {"contact_id": call["contactId"], "customer_name": customer.full_name,
                              "first_name": customer.first_name, "language": lang, "today": today_text,
                              "caller_known": "true"},
        "conversation_config_override": {"agent": {"language": lang,
                                                   "first_message": FIRST_MESSAGE[lang].format(name=customer.full_name)}},
    }


def _post_call(body):
    """Post-call webhook: full transcript (with analysis) and the MP3 go to S3 under the conversation id;
    the Connect contact gets the conversation id, the S3 locations and the AI summary."""
    data = body.get("data") or {}
    conversation = data.get("conversation_id", "unknown")
    prefix = f"conversations/{conversation}"
    if body.get("type") == "post_call_audio":
        S3.put_object(Bucket=BUCKET, Key=f"{prefix}/audio.mp3", Body=base64.b64decode(data.get("full_audio", "")),
                      ContentType="audio/mpeg")
        return {"ok": True, "stored": f"{prefix}/audio.mp3"}
    if body.get("type") != "post_call_transcription":
        return {"ok": True, "ignored": body.get("type")}
    variables = (data.get("conversation_initiation_client_data") or {}).get("dynamic_variables") or {}
    contact_id = variables.get("contact_id", "")
    S3.put_object(Bucket=BUCKET, Key=f"{prefix}/transcript.json", ContentType="application/json",
                  Body=json.dumps(data, ensure_ascii=False, default=str).encode(), Metadata={"contact-id": contact_id})
    summary = ((data.get("analysis") or {}).get("transcript_summary") or "")[:1000]
    if contact_id:
        try:
            _set_call(contact_id, conversationId=conversation, transcriptKey=f"{prefix}/transcript.json", aiSummary=summary,
                      status="done")
            call = CALLS.get_item(Key={"contactId": contact_id}).get("Item") or {}
            _contact_attributes(call, {"elevenlabsConversationId": conversation, "aiCallSummary": summary,
                                       "transcriptS3": f"s3://{BUCKET}/{prefix}/transcript.json",
                                       "audioS3": f"s3://{BUCKET}/{prefix}/audio.mp3"})
        except Exception:  # an unknown contact id must not make ElevenLabs retry forever
            log.exception("post-call update failed for %s", contact_id)
    return {"ok": True, "stored": f"{prefix}/transcript.json"}


def _secret(name):
    try:
        return SECRETS.get_secret_value(SecretId=name)["SecretString"]
    except Exception:
        log.exception("secret %s not readable", name)
        return None


def _post_call_authorized(event, raw):
    """The post-call webhook carries its own token header (only valid for this route). The ElevenLabs HMAC
    signature (header "t=...,v0=...") is also accepted, and its result is logged."""
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    token = _secret(os.environ.get("POST_CALL_TOKEN_SECRET", ""))
    token_ok = bool(token) and hmac.compare_digest(headers.get("x-post-call-token", ""), token)
    signature_ok = False
    secret = _secret(os.environ.get("WEBHOOK_SECRET_ARN", "")) if headers.get("elevenlabs-signature") else None
    if secret:
        parts = dict(p.split("=", 1) for p in headers["elevenlabs-signature"].split(",") if "=" in p)
        expected = hmac.new(secret.encode(), f"{parts.get('t', '')}.{raw}".encode(), hashlib.sha256).hexdigest()
        signature_ok = hmac.compare_digest(expected, parts.get("v0", ""))
    log.info("post-call auth: token=%s signature=%s", token_ok, signature_ok)
    return token_ok or signature_ok


def _take_pending(phone, call_sid):
    """The newest pending handoff from this phone in the last few minutes. A call that reaches the
    Twilio number directly (no Connect contact) gets a synthetic id so the tools still work."""
    since = int(time.time()) - PENDING_SECONDS
    items = CALLS.query(IndexName="phone-createdAt", KeyConditionExpression=Key("phone").eq(phone) & Key("createdAt").gte(since),
                        ScanIndexForward=False, Limit=5).get("Items", [])
    pending = next((i for i in items if i.get("status") == "pending"), None)
    if pending:
        CALLS.update_item(Key={"contactId": pending["contactId"]}, UpdateExpression="SET #s = :s, callSid = :c",
                          ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":s": "in_progress", ":c": call_sid})
        return pending
    item = {"contactId": f"direct-{call_sid or uuid.uuid4().hex}", "phone": phone, "status": "in_progress",
            "createdAt": int(time.time()), "callSid": call_sid, "source": "direct"}
    CALLS.put_item(Item=item)
    return item


def _call_and_customer(body):
    call = CALLS.get_item(Key={"contactId": body["contact_id"]}).get("Item")
    if not call:
        raise KeyError("contact_id")
    customer, _ = find_by_account(PROFILES, DOMAIN, call.get("account", ""))
    if not customer:
        customer, _ = find_by_phone(PROFILES, DOMAIN, call.get("phone", ""))
    return call, customer


def _today():
    return datetime.now(LOCAL_TZ).date()


def _plan_args(body):
    first = body.get("first_payment_date") or None
    count = body.get("installments")
    return {"installments": int(count) if str(count or "").isdigit() else None,
            "first_payment_date": date.fromisoformat(first) if first else None}


# ---------- Tools ----------

def tool_lookup_account(body):
    """Caller not recognized by phone: links the call to the account number they said."""
    digits = "".join(ch for ch in str(body.get("account_number", "")) if ch.isdigit())
    customer, _ = find_by_account(PROFILES, DOMAIN, digits) if digits else (None, [])
    if not customer:
        return {"found": False, "accountNumber": digits}
    _set_call(body["contact_id"], account=customer.account, language=customer.language, identityConfirmed=False)
    call = CALLS.get_item(Key={"contactId": body["contact_id"]}).get("Item") or {}
    _contact_attributes(call, {"customerName": customer.full_name, "account": customer.account})
    return {"found": True, "accountNumber": digits, "customerName": customer.full_name,
            "canNegotiate": not customer.special_status}


def tool_confirm_identity(body):
    confirmed = str(body.get("confirmed", "")).lower() in ("true", "yes", "1")
    _set_call(body["contact_id"], identityConfirmed=confirmed)
    return {"ok": True, "confirmed": confirmed}


def tool_get_case(body):
    call, customer = _call_and_customer(body)
    if not call.get("identityConfirmed"):
        return {"error": "identity_not_confirmed"}
    return case_view(customer, _today())


def tool_propose_plan(body):
    call, customer = _call_and_customer(body)
    if not call.get("identityConfirmed"):
        return {"error": "identity_not_confirmed"}
    result = propose_plan(customer, body["plan_type"], _today(), **_plan_args(body))
    return _plan_json(result, customer.language)


def tool_save_agreement(body):
    call, customer = _call_and_customer(body)
    if not call.get("identityConfirmed"):
        return {"error": "identity_not_confirmed"}
    result = propose_plan(customer, body["plan_type"], _today(), **_plan_args(body))
    if not result.accepted:
        return _plan_json(result, customer.language)
    agreement_id = f"AGR-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
    AGREEMENTS.put_item(Item={
        "agreementId": agreement_id, "account": customer.account, "customerName": customer.full_name,
        "contactId": call["contactId"], "planType": result.plan_type, "status": "active", "source": "ai",
        "total": Decimal(sum(a for _, a in result.payments)),
        "payments": [{"date": d.isoformat(), "amount": a} for d, a in result.payments],
        "summary": result.summary_en, "createdAt": datetime.now(timezone.utc).isoformat()})
    _set_call(call["contactId"], outcome="agreement", agreementId=agreement_id, summary=result.summary_en)
    _contact_attributes(call, {"aiOutcome": "agreement", "agreementId": agreement_id, "agreementSummary": result.summary_en})
    if customer.profile_id:  # visible to agents in the profile's "More information" tab
        try:
            PROFILES.update_profile(DomainName=DOMAIN, ProfileId=customer.profile_id,
                                    Attributes={"lastAgreementId": agreement_id, "lastAgreement": result.summary_en})
        except Exception:
            log.exception("profile update failed for %s", customer.account)
    return {"saved": True, "agreementId": agreement_id, **_plan_json(result, customer.language)}


def tool_request_human(body):
    call, _ = _call_and_customer(body)
    summary = f"{body.get('reason', '')}: {body.get('summary', '')}".strip(": ")[:500]
    _set_call(call["contactId"], outcome="escalate", summary=summary)
    _contact_attributes(call, {"aiOutcome": "escalate", "handoffSummary": summary})
    return {"ok": True, "next": "Say a short goodbye line that a colleague will continue, then call end_call."}


TOOLS = {"lookup_account": tool_lookup_account, "confirm_identity": tool_confirm_identity, "get_case": tool_get_case, "propose_plan": tool_propose_plan,
         "save_agreement": tool_save_agreement, "request_human": tool_request_human}


def _plan_json(result, language):
    if not result.accepted:
        return {"accepted": False, "reason": result.reason}
    return {"accepted": True, "planType": result.plan_type,
            "payments": [{"date": d.isoformat(), "amount": f"{a:.2f}"} for d, a in result.payments],
            "summary": result.summary_es if language == "es" else result.summary_en}


def _set_call(contact_id, **fields):
    names = {f"#{k}": k for k in fields}
    CALLS.update_item(Key={"contactId": contact_id}, UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in fields),
                      ExpressionAttributeNames=names, ExpressionAttributeValues={f":{k}": v for k, v in fields.items()})


def _contact_attributes(call, attributes):
    """Best effort: attributes on the real Connect contact so the result shows in the portal."""
    if call.get("source") != "connect":
        return
    try:
        CONNECT.update_contact_attributes(InstanceId=INSTANCE_ID, InitialContactId=call["contactId"],
                                          Attributes={k: str(v)[:1000] for k, v in attributes.items()})
    except Exception:  # never break the conversation because of the portal
        log.exception("update_contact_attributes failed for %s", call["contactId"])


def _resp(status, payload):
    return {"statusCode": status, "headers": {"content-type": "application/json"},
            "body": json.dumps(payload, default=str)}
