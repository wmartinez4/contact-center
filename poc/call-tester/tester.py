"""Lex V2 code hook of the call tester: a simulated customer that calls the demo lines.

Connect places an outbound call and connects the callee to this bot (Nova Sonic speech). Every utterance the bot
hears is what the system under test said; a Bedrock model playing the scenario's persona writes the reply.
The bot ends the call when the model marks [END], after MAX_TURNS, or after several silent turns.
Each turn is logged as one JSON line (contactId, heard, said) so the runner can print the dialogue.
"""
import json
import os

import boto3

MODEL = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
MAX_TURNS = int(os.environ.get("MAX_TURNS", "14"))
SCENARIOS = json.load(open(os.path.join(os.path.dirname(__file__), "scenarios.json"), encoding="utf-8"))
BEDROCK = boto3.client("bedrock-runtime")

RULES = (
    "You are the CUSTOMER on a phone call, never the agent. The other side's words reach you as text.\n"
    "Speak in the language the other side uses. Reply with one or two short spoken sentences, like a real person on the phone: "
    "no lists, no stage directions, no emojis.\n"
    "If the other side has not finished (for example it only greeted you or is still reading something), reply briefly, "
    "for example 'Sí' or 'Okay'.\n"
    "When the call is over (the other side says goodbye, or you were transferred and told to wait), say a short goodbye "
    "and end your reply with [END]."
)


def _messages(history):
    """Agent lines are 'user' turns and the customer's lines 'assistant' turns; Bedrock needs strict alternation."""
    out = []
    for h in history:
        role = "user" if h["who"] == "agent" else "assistant"
        if out and out[-1]["role"] == role:
            out[-1]["content"][0]["text"] += " " + h["text"]
        else:
            out.append({"role": role, "content": [{"text": h["text"]}]})
    return out


def _reply(persona, history):
    r = BEDROCK.converse(modelId=MODEL, system=[{"text": RULES + "\n\nYour persona:\n" + persona}],
                         messages=_messages(history), inferenceConfig={"maxTokens": 120, "temperature": 0.4})
    text = r["output"]["message"]["content"][0]["text"].strip()
    return text.replace("[END]", "").strip(), "[END]" in text


def _response(event, attrs, text, close):
    intent = event["sessionState"]["intent"]
    state = {"sessionAttributes": attrs}
    if close:
        state["dialogAction"] = {"type": "Close"}
        state["intent"] = {"name": intent["name"], "state": "Fulfilled"}
    else:
        state["dialogAction"] = {"type": "ElicitIntent"}
    out = {"sessionState": state}
    if text:
        out["messages"] = [{"contentType": "PlainText", "content": text}]
    return out


def handler(event, context):
    attrs = event["sessionState"].get("sessionAttributes") or {}
    scenario = SCENARIOS[attrs.get("scenario") or "maria-installments"]
    heard = (event.get("inputTranscript") or "").strip()
    history = json.loads(attrs.get("history") or "[]")
    turn = int(attrs.get("turn") or "0") + 1
    attrs["turn"] = str(turn)

    if not heard:
        silent = int(attrs.get("silent") or "0") + 1
        attrs["silent"] = str(silent)
        print(json.dumps({"contactId": event.get("sessionId"), "turn": turn, "heard": "", "said": ""}))
        return _response(event, attrs, "", close=silent >= 4)

    attrs["silent"] = "0"
    history.append({"who": "agent", "text": heard})
    said, done = _reply(scenario["persona"], history)
    history.append({"who": "me", "text": said})
    attrs["history"] = json.dumps(history[-30:], ensure_ascii=False)
    print(json.dumps({"contactId": event.get("sessionId"), "turn": turn, "heard": heard, "said": said, "end": done},
                     ensure_ascii=False))
    return _response(event, attrs, said, close=done or turn >= MAX_TURNS)
