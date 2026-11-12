#!/usr/bin/env python3
"""Configures the ElevenLabs collections agent for route B: workspace secret, five webhook tools,
prompt, languages, system tools, overrides and the conversation initiation webhook.

Re-runnable. Needs setup_api.py first (reads poc/elevenlabs-ruta-b/.state.json) and
ELEVENLABS_API_KEY in the project .env.

    AWS_PROFILE=cs-admin python3 poc/infra/elevenlabs-route-b/setup_agent.py
"""
import json
import os
import urllib.error
import urllib.request

import boto3

AGENT_ID = "agent_3401m773nf9gekbsv9eqeypdajc5"
VOICE_ID = "ut2XM2wJyIZLTtW6lFzZ"  # "Eliza - Conversational Podcast Host", saved in the workspace (female, American English)
SECRET_NAME = "voice-agent-api-secret"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ROUTE = os.path.join(ROOT, "poc", "elevenlabs-ruta-b")
STATE = json.load(open(os.path.join(ROUTE, ".state.json")))
PROMPT = open(os.path.join(ROUTE, "agent", "prompt.md"), encoding="utf-8").read()

FIRST_MESSAGE_ES = "Hola, le habla Sofía, asistente virtual del área de cuentas. ¿Hablo con el titular de la cuenta?"
FIRST_MESSAGE_EN = "Hi, this is Sofia, a virtual assistant from the accounts team. Am I speaking with the account holder?"


def env_key():
    for line in open(os.path.join(ROOT, ".env")):
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("ELEVENLABS_API_KEY missing in .env")


KEY = env_key()


def el(method, path, body=None):
    req = urllib.request.Request("https://api.elevenlabs.io" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:800]}")


WEBHOOK_NAME = "voice-agent-post-call"
WEBHOOK_SECRET_NAME = "voice-agent/elevenlabs-webhook-secret"


def ensure_post_call_webhook(secret_id):
    """Workspace webhook used only by this agent (set in its overrides). ElevenLabs returns the HMAC secret
    once, at creation; it is kept in AWS Secrets Manager for the Lambda to verify signatures."""
    url = f"{STATE['apiUrl']}/elevenlabs/post-call"
    found = next((w for w in el("GET", "/v1/workspace/webhooks").get("webhooks", []) if w["name"] == WEBHOOK_NAME), None)
    if found:
        if found["webhook_url"] != url:
            print("WARNING: webhook URL differs; delete it in the dashboard and re-run:", found["webhook_url"])
        return found["webhook_id"]
    sm = boto3.Session(region_name="us-east-1").client("secretsmanager")
    # Webhook headers only take plain strings, so this sends a token valid for the post-call route alone.
    token = sm.get_secret_value(SecretId="voice-agent/post-call-token")["SecretString"]
    created = el("POST", "/v1/workspace/webhooks", {"settings": {
        "auth_type": "hmac", "name": WEBHOOK_NAME, "webhook_url": url, "request_headers": {"x-post-call-token": token}}})
    if created.get("webhook_secret"):
        try:
            sm.create_secret(Name=WEBHOOK_SECRET_NAME, SecretString=created["webhook_secret"],
                             Description="HMAC secret of the ElevenLabs post-call webhook", Tags=[{"Key": "project", "Value": "elevenlabs"}])
        except sm.exceptions.ResourceExistsException:
            sm.put_secret_value(SecretId=WEBHOOK_SECRET_NAME, SecretString=created["webhook_secret"])
    print("post-call webhook created:", created["webhook_id"])
    return created["webhook_id"]


def ensure_secret():
    value = boto3.Session(region_name="us-east-1").client("secretsmanager").get_secret_value(
        SecretId=STATE["secretArn"])["SecretString"]
    found = next((s for s in el("GET", "/v1/convai/secrets").get("secrets", []) if s["name"] == SECRET_NAME), None)
    if found:
        el("PATCH", f"/v1/convai/secrets/{found['secret_id']}", {"type": "update", "name": SECRET_NAME, "value": value})
        return found["secret_id"]
    return el("POST", "/v1/convai/secrets", {"type": "new", "name": SECRET_NAME, "value": value})["secret_id"]


def contact_id():
    return {"type": "string", "description": "", "dynamic_variable": "contact_id"}


def text(description, enum=None):
    prop = {"type": "string", "description": description}
    if enum:
        prop["enum"] = enum
    return prop


PLAN_PROPS = {
    "contact_id": contact_id(),
    "plan_type": text("full = pay the whole balance today or on a date; promise = pay the whole balance on a later date; "
                      "installments = several payments", ["full", "promise", "installments"]),
    "installments": {"type": "integer", "description": "Number of installments, only for plan_type installments"},
    "first_payment_date": text("Date of the payment, or of the first installment, as YYYY-MM-DD. Omit for today."),
}

TOOLS = {
    "lookup_account": ("Find the customer by the account number the caller said. Only for callers that were not recognized "
                       "by phone, after repeating the digits back and getting a confirmation.",
                       {"contact_id": contact_id(),
                        "account_number": text("The account number digits only, for example 4 or 1234")},
                       ["contact_id", "account_number"]),
    "confirm_identity": ("Record whether the person on the line confirmed being the account holder. Call it right after they answer.",
                         {"contact_id": contact_id(),
                          "confirmed": {"type": "boolean", "description": "true if they confirmed being the account holder"}},
                         ["contact_id", "confirmed"]),
    "get_case": ("Get the customer's balance, days past due and the options allowed today. Only after identity is confirmed.",
                 {"contact_id": contact_id()}, ["contact_id"]),
    "propose_plan": ("Check whether a payment plan is allowed and get its exact amounts and dates. Call before mentioning any amount or date.",
                     PLAN_PROPS, ["contact_id", "plan_type"]),
    "save_agreement": ("Save the payment arrangement after the customer explicitly said yes. Use the same values you validated.",
                       PLAN_PROPS, ["contact_id", "plan_type"]),
    "request_human": ("Hand the customer to a human colleague. Call before end_call.",
                      {"contact_id": contact_id(),
                       "reason": text("Short reason, for example: asked for a person, disputes the debt"),
                       "summary": text("One or two sentences summarizing the conversation for the colleague")},
                      ["contact_id", "reason", "summary"]),
}


def tool_config(name, description, props, required, secret_id):
    return {"type": "webhook", "name": name, "description": description, "response_timeout_secs": 10,
            "api_schema": {"url": f"{STATE['apiUrl']}/tools/{name}", "method": "POST",
                           "request_headers": {"x-api-secret": {"secret_id": secret_id}},
                           "request_body_schema": {"type": "object", "description": f"{name} request",
                                                   "properties": props, "required": required}}}


def ensure_tools(secret_id):
    existing = {t["tool_config"]["name"]: t["id"] for t in el("GET", "/v1/convai/tools").get("tools", [])}
    ids = []
    for name, (description, props, required) in TOOLS.items():
        body = {"tool_config": tool_config(name, description, props, required, secret_id)}
        if name in existing:
            el("PATCH", f"/v1/convai/tools/{existing[name]}", body)
            ids.append(existing[name])
        else:
            ids.append(el("POST", "/v1/convai/tools", body)["id"])
        print("tool", name, ids[-1])
    return ids


def configure_agent(tool_ids, secret_id, webhook_id):
    system = lambda kind, **params: {"type": "system", "name": kind, "description": "",
                                     "params": {"system_tool_type": kind, **params}}
    body = {
        "name": "collections-agent",
        "conversation_config": {
            "agent": {
                "language": "es",
                "first_message": FIRST_MESSAGE_ES,
                "dynamic_variables": {"dynamic_variable_placeholders": {
                    "contact_id": "test", "customer_name": "Maria Hernandez", "first_name": "Maria",
                    "language": "es", "today": "2026-11-12 (Thursday)", "caller_known": "true"}},
                "prompt": {"prompt": PROMPT, "tool_ids": tool_ids, "enable_parallel_tool_calls": False,
                           "built_in_tools": {"end_call": system("end_call"),
                                              "language_detection": system("language_detection",
                                                                           only_at_conversation_start=False)}},
            },
            "tts": {"voice_id": VOICE_ID},
            "language_presets": {"en": {"overrides": {"agent": {"first_message": FIRST_MESSAGE_EN}}}},
        },
        "platform_settings": {
            # Without the flag ElevenLabs never calls the initiation webhook on phone calls, and the call fails
            # with "Missing required dynamic variables in tools: contact_id".
            "overrides": {"enable_conversation_initiation_client_data_from_webhook": True,
                          "conversation_config_override": {"agent": {"first_message": True, "language": True}}},
            "workspace_overrides": {
                "conversation_initiation_client_data_webhook": {
                    "url": f"{STATE['apiUrl']}/elevenlabs/init",
                    "request_headers": {"x-api-secret": {"secret_id": secret_id}}},
                "webhooks": {"post_call_webhook_id": webhook_id, "events": ["transcript", "audio"], "send_audio": True}},
        },
    }
    el("PATCH", f"/v1/convai/agents/{AGENT_ID}", body)
    agent = el("GET", f"/v1/convai/agents/{AGENT_ID}")
    cfg = agent["conversation_config"]
    print("agent:", agent["name"], "| language:", cfg["agent"]["language"], "| presets:", list(cfg.get("language_presets", {})),
          "| tools:", len(cfg["agent"]["prompt"].get("tool_ids", [])),
          "| built-in:", [k for k, v in cfg["agent"]["prompt"].get("built_in_tools", {}).items() if v])


if __name__ == "__main__":
    sid = ensure_secret()
    configure_agent(ensure_tools(sid), sid, ensure_post_call_webhook(sid))
