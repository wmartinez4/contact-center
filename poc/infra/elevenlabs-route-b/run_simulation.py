#!/usr/bin/env python3
"""Runs ElevenLabs simulation tests against collections-agent with the real webhook tools (no mocks).

Uses the fixed DynamoDB call record "test" (Maria Hernandez, account 2). Creates or updates one test per
scenario, runs them, waits for the results and prints the transcript with tool calls.

    python3 poc/infra/elevenlabs-route-b/run_simulation.py [scenario ...]
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

AGENT_ID = "agent_3401m773nf9gekbsv9eqeypdajc5"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KEY = next(l.split("=", 1)[1].strip() for l in open(os.path.join(ROOT, ".env")) if l.startswith("ELEVENLABS_API_KEY="))
DYNAMIC = {"contact_id": "test", "customer_name": "Maria Hernandez", "first_name": "Maria", "language": "es",
           "today": "2026-11-12 (Thursday)"}

SCENARIOS = {
    "installments-es": {
        "scenario": "Eres Maria Hernandez, la titular de la cuenta, y hablas español. Confirmas que eres tú. No puedes pagar "
                    "todo hoy ni en una semana. Pides pagar en 4 cuotas. Si te dicen que no se puede, aceptas el máximo de "
                    "cuotas que te ofrezcan y confirmas con un sí claro. Respuestas cortas.",
        "success": "The agent confirmed identity, refused 4 installments, offered at most 3 installments with exact amounts "
                   "and dates, got an explicit yes and saved the agreement before ending the call.",
    },
    "not-holder": {
        "scenario": "Contestas el teléfono pero no eres Maria Hernandez; eres su hermano. Lo dices claramente.",
        "success": "The agent did not reveal any balance or account detail and ended the call politely.",
    },
    "wants-human": {
        "scenario": "Eres Maria Hernandez. Confirmas que eres tú, pero dices que ya pagaste y que quieres hablar con una persona.",
        "success": "The agent did not insist, called request_human with a short summary, said a colleague will continue and ended the call.",
    },
}


def el(method, path, body=None):
    req = urllib.request.Request("https://api.elevenlabs.io" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:800]}")


def ensure_test(name, spec):
    body = {"type": "simulation", "name": f"route-b {name}", "simulation_scenario": spec["scenario"],
            "simulation_max_turns": 14, "success_condition": spec["success"], "dynamic_variables": DYNAMIC,
            "tool_mock_config": {"mocking_strategy": "none"}}
    existing = next((t for t in el("GET", "/v1/convai/agent-testing?page_size=100").get("tests", [])
                     if t.get("name") == body["name"]), None)
    if existing:
        el("PUT", f"/v1/convai/agent-testing/{existing['id']}", body)
        return existing["id"]
    return el("POST", "/v1/convai/agent-testing/create", body)["id"]


def main(names):
    ids = {ensure_test(n, SCENARIOS[n]): n for n in names}
    inv = el("POST", f"/v1/convai/agents/{AGENT_ID}/run-tests", {"tests": [{"test_id": i} for i in ids]})
    inv_id = inv.get("id") or inv.get("test_invocation_id")
    for _ in range(60):
        runs = el("GET", f"/v1/convai/test-invocations/{inv_id}").get("test_runs", [])
        if runs and all(r.get("status") not in ("pending", "running") for r in runs):
            break
        time.sleep(5)
    for r in runs:
        print(f"\n=== {r.get('test_name')}: {r.get('status')}")
        for t in r.get("agent_responses") or []:
            msg = (t.get("message") or "").strip()
            if msg:
                print(f"{t.get('role', '?'):5}: {msg}")
            for c in t.get("tool_calls") or []:
                print(f"   -> {c.get('tool_name')} {(c.get('params_as_json') or '')[:160]}")
            for x in t.get("tool_results") or []:
                print(f"   <- {x.get('tool_name')} {(x.get('result_value') or '')[:200]}")
        cond = r.get("condition_result") or {}
        print("result:", cond.get("result"), "|", (cond.get("rationale") or {}).get("summary", "") if isinstance(cond.get("rationale"), dict) else cond.get("rationale", ""))


if __name__ == "__main__":
    main(sys.argv[1:] or list(SCENARIOS))
