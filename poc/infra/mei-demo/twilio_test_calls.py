#!/usr/bin/env python3
"""Place scripted test calls from a Twilio number to the demo lines, then check each in Connect.

Each case dials, waits, presses digits or speaks (Twilio <Say>), stays on the line a while and hangs up.
Afterwards the Connect contact started by that call is read back: queue, agent, disconnect reason and
the attributes the flow set. Agents with auto-accept who are Available answer automatically.

Credentials come from the project .env (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER); never printed.

    AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> python3 twilio_test_calls.py routing|ai|all [case ...]
"""
import base64
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import boto3

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".env"))
MAIN = "+17752456050"
AI = os.environ.get("AI_NUMBER", "+17752491758")  # the sandbox line when trying a parallel bot


def env():
    out = {}
    for line in open(ENV, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


E = env()
SID, TOKEN, FROM = E["TWILIO_ACCOUNT_SID"], E["TWILIO_AUTH_TOKEN"], E.get("TWILIO_PHONE_NUMBER", "")
AUTH = "Basic " + base64.b64encode(f"{SID}:{TOKEN}".encode()).decode()


def twilio(method, path, data=None):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{SID}/{path}"
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method, headers={"Authorization": AUTH})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def say(text, lang="en-US"):
    voice = "Polly.Joanna" if lang == "en-US" else "Polly.Lupe"
    return f'<Say voice="{voice}" language="{lang}">{text}</Say>'


def pause(s):
    return f'<Pause length="{s}"/>'


def digit(d):
    return f'<Play digits="{d}"/>'


def menu(lang_digit, account, talk=25):
    # notice + bilingual menu ~8 s; after the language, the account prompt ~3 s (Spanish adds its notice)
    after = 6 if lang_digit == "1" else 8
    return pause(7) + digit(lang_digit) + pause(after) + digit(account) + pause(talk)


CASES = {
    # routing (main line, unknown caller number -> menus)
    "r3": (MAIN, menu("1", "3"), {"queue": "Q-16-30", "account": "3"}),
    "r2": (MAIN, menu("2", "2"), {"queue": "Q-1-8", "account": "2"}),
    "r5": (MAIN, menu("1", "5"), {"queue": "Q-Redemptions", "account": "5"}),
    "r6": (MAIN, menu("2", "6"), {"queue": "Q-EPD", "account": "6"}),
    "r4": (MAIN, menu("1", "4"), {"queue": "Q-31Plus", "account": "4"}),
    "r7": (MAIN, menu("1", "7"), {"queue": "Q-Fallback", "account": "7"}),
    # AI line
    "ai-en": (AI, pause(7) + digit("1") + pause(9) + say("What is my balance?") + pause(7) + say("Three.") + pause(12)
              + say("I want to talk to a person.") + pause(25), {"outcome": "escalate"}),
    "ai-switch": (AI, pause(7) + digit("1") + pause(9) + say("Spanish please.") + pause(12)
                  + say("Sí, en español.", "es-US") + pause(8) + say("Quiero hablar con una persona.", "es-US") + pause(25),
                  {"outcome": "escalate", "language": "es"}),
}


def dialog(lines, lang="en-US", gap=7):
    """Customer side of a conversation, with a pause after each line for the agent to answer."""
    return "".join(say(t, lang) + pause(gap) for t in lines)


CASES.update({
    # long calls so Contact Lens has enough conversation for transcript, sentiment and summary
    "conv-en": (MAIN, menu("1", "3", talk=14) + dialog([
        "Hi, this is Robert Miller. I got a message that my account is past due.",
        "Yes, I know I am late. I had an unexpected car repair this month and money is tight.",
        "How much do I owe right now, and when was it due?",
        "I can't pay the full balance today. Could I pay half now and the rest at the end of the month?",
        "OK, that works for me. Please send me the confirmation by email.",
        "No, that's all. Thank you for your help, I appreciate it.",
    ]), {"queue": "Q-16-30", "account": "3"}),
    "conv-es": (MAIN, menu("2", "2", talk=16) + dialog([
        "Hola, habla María Hernández. Recibí un mensaje de que mi pago está atrasado.",
        "Sí, lo sé. Este mes me redujeron las horas en el trabajo y no alcancé a pagar.",
        "¿Cuánto debo exactamente y para cuándo era el pago?",
        "Hoy puedo pagar una parte. ¿Me pueden dar unos días más para el resto?",
        "Perfecto, me funciona. Por favor envíenme la confirmación por correo.",
        "No, eso es todo. Muchas gracias por la ayuda.",
    ], "es-US"), {"queue": "Q-1-8", "account": "2"}),
    "conv-ai": (AI, pause(7) + digit("1") + pause(9) + say("Hi, I want to check my account.") + pause(7) + say("Three.")
                + pause(12) + say("When is my payment due?") + pause(10) + say("How can I pay?") + pause(12)
                + say("I need a payment arrangement. I want to talk to a person.") + pause(8)
                + dialog(["Hi, the assistant said you can help me set up a payment plan.",
                          "I can pay half now and the rest on the twenty eighth.",
                          "Great, thank you. That's all."]), {"outcome": "escalate"}),
})
CUSTOMER = {
    "en": ["Hi, I'm calling about my account. I got a notice that my payment is late.",
           "Yes, I had some unexpected expenses this month.",
           "Yes, please. Can I pay half now and the rest at the end of the month?",
           "Great, that works for me.",
           "No, that's all. Thank you."],
    "es": ["Hola, llamo por mi cuenta. Me llegó un aviso de que mi pago está atrasado.",
           "Sí, tuve unos gastos inesperados este mes.",
           "Sí, por favor. ¿Puedo pagar una parte hoy y el resto después?",
           "Perfecto, me funciona.",
           "No, eso es todo. Gracias."],
}


def full(lang_digit, account):
    lang = "en" if lang_digit == "1" else "es"
    return menu(lang_digit, account, talk=14 if lang == "en" else 16) + dialog(CUSTOMER[lang], "en-US" if lang == "en" else "es-US", gap=8)


# The whole suite with a full conversation; the agent side comes from agent_sim.py. Value: (case, agent script language)
for key, (dig, acct, exp) in {"f3": ("1", "3", "Q-16-30"), "f2": ("2", "2", "Q-1-8"), "f5": ("1", "5", "Q-Redemptions"),
                              "f6": ("2", "6", "Q-EPD"), "f4": ("1", "4", "Q-31Plus"), "f7": ("1", "7", "Q-Fallback")}.items():
    CASES[key] = (MAIN, full(dig, acct), {"queue": exp, "account": acct})
# Spanish adds the recording notice and a longer greeting: wait longer before each line so the bot is listening
# The "¿Cuándo vence mi pago?" step was dropped on 2026-11-11: the bot's answer plus its "Sigo aquí" prompt (not interruptible)
# overlapped the request for a person, which then went unheard and the bot ended the call. Ask right after the balance answer.
CASES["f-ai-es"] = (AI, pause(7) + digit("2") + pause(14) + say("Quiero revisar mi cuenta.", "es-US") + pause(9) + say("Dos.", "es-US")
                    + pause(14) + say("Quiero hablar con una persona.", "es-US")
                    + pause(8) + dialog(CUSTOMER["es"], "es-US", gap=8), {"outcome": "escalate", "language": "es"})
CASES["conv-dispute"] = (MAIN, menu("1", "4", talk=14) + dialog([
    "Hi, I got a letter saying I owe money on my account, but I think there is a mistake.",
    "I don't owe this amount. I already paid last week at the dealership.",
    "No, I'm not going to pay again. I need someone to check the payment first.",
    "I can't talk right now. Please call me back tomorrow afternoon.",
    "Thank you. Goodbye.",
], gap=8), {"queue": "Q-31Plus", "account": "4"})
SIM_LANG = {"conv-dispute": "en", "f3": "en", "f2": "es", "f5": "en", "f6": "es", "f4": "en", "f7": "en", "conv-ai": "en", "f-ai-es": "es",
            "conv-en": "en", "conv-es": "es"}
GROUPS = {"routing": ["r3", "r2", "r5", "r6", "r4", "r7"], "ai": ["ai-en", "ai-switch"], "conversation": ["conv-en", "conv-es", "conv-ai"],
          "full": ["f3", "f2", "f5", "f6", "f4", "f7", "conv-ai", "f-ai-es"],
          "categories": ["conv-en", "conv-ai", "conv-dispute", "conv-es", "f-ai-es"]}


def place(case):
    to, twiml, _ = CASES[case]
    call = twilio("POST", "Calls.json", {"To": to, "From": FROM, "Twiml": f"<Response>{twiml}<Hangup/></Response>"})
    while True:
        time.sleep(5)
        st = twilio("GET", f"Calls/{call['sid']}.json")
        if st["status"] in ("completed", "failed", "busy", "no-answer", "canceled"):
            return st


def connect_contact(started):
    c = boto3.client("connect")
    iid = os.environ["CONNECT_INSTANCE_ID"]
    end = dt.datetime.now(dt.timezone.utc)
    for _ in range(12):
        r = c.search_contacts(InstanceId=iid, TimeRange={"Type": "INITIATION_TIMESTAMP", "StartTime": started - dt.timedelta(seconds=20), "EndTime": end},
                              SearchCriteria={"Channels": ["VOICE"]}, MaxResults=10, Sort={"FieldName": "INITIATION_TIMESTAMP", "Order": "ASCENDING"})
        inbound = [x for x in r["Contacts"] if x["InitiationMethod"] == "INBOUND"]
        if inbound:
            cid = inbound[0]["Id"]
            d = c.describe_contact(InstanceId=iid, ContactId=cid)["Contact"]
            a = c.get_contact_attributes(InstanceId=iid, InitialContactId=cid)["Attributes"]
            agent = d.get("AgentInfo", {}).get("Id")
            uname = c.describe_user(InstanceId=iid, UserId=agent)["User"]["Username"] if agent else "-"
            return cid, d, a, uname
        time.sleep(5)
    return None, {}, {}, "-"


def run(case):
    started = dt.datetime.now(dt.timezone.utc)
    st = place(case)
    cid, d, a, agent = connect_contact(started)
    exp = CASES[case][2]
    got = {"queue": a.get("queueName"), "account": a.get("caseCode") or a.get("accountCode"), "outcome": a.get("outcome"), "language": a.get("language")}
    ok = all(got.get(k) == v for k, v in exp.items())
    print(json.dumps({"case": case, "ok": ok, "twilio": st["status"], "duration": st.get("duration"), "contact": cid,
                      "agent": agent, "disconnect": d.get("DisconnectReason"), "got": got, "expected": exp,
                      "reason": a.get("reason"), "summary": a.get("summary") or a.get("customerSummary")}, ensure_ascii=False), flush=True)
    time.sleep(int(os.environ.get("BETWEEN_CALLS", "65")))  # agents keep 60 s of after-call work for the wrap-up


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "routing"
    cases = sys.argv[2:] or (GROUPS["routing"] + GROUPS["ai"] if which == "all" else GROUPS[which])
    if which not in ("full", "categories"):
        for case in cases:
            run(case)
        sys.exit(0)
    import agent_sim  # simulated agents: needs EXPECTED_ACCOUNT and DEMO_PREFIX too
    current = None
    try:
        for case in cases:
            if SIM_LANG[case] != current:
                current = SIM_LANG[case]
                agent_sim.start(current)
            run(case)
    finally:
        agent_sim.stop()
