"""Fulfillment of the demo AI agent (Lex V2 bot with a speech-to-speech model).

A multi-turn conversation: after every answer the agent asks if there is anything else and keeps listening.
Intents: AccountInfo (asks for the account code), Balance, DueDate, PaymentOptions, TalkToAgent, EndCall, fallback.
It answers with data of an invented account, or hands over to a person with a summary, a reason and the queue
chosen by the same rules as the inbound flow. The Connect flow reads the session attributes
`outcome` (resolved or escalate), `reason`, `summary` and `queueArn` when the conversation ends.
"""
import datetime

import lookup_handler as lk

MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MORE = ("Is there anything else I can help you with?", "¿Hay algo más en lo que pueda ayudarle?")


def _t(lang, en, es):
    return en if lang == "en" else es


def _date(s, lang):
    d = datetime.date.fromisoformat(s)
    return f"{MONTHS_EN[d.month - 1]} {d.day}" if lang == "en" else f"{d.day} de {MONTHS_ES[d.month - 1]}"


def _msg(text):
    return [{"contentType": "PlainText", "content": text}]


def _close(intent, attrs, text, state="Fulfilled"):
    out = {"sessionState": {"dialogAction": {"type": "Close"}, "intent": {"name": intent["name"], "state": state, "slots": intent.get("slots") or {}}, "sessionAttributes": attrs}}
    if text:  # no text: the flow's next greeting (in the new voice) is the only thing the caller hears
        out["messages"] = _msg(text)
    return out


def _more(attrs, text, lang):
    """Answer, then ask if there is anything else and keep the conversation open."""
    attrs["fallbacks"] = "0"
    return {"sessionState": {"dialogAction": {"type": "ElicitIntent"}, "sessionAttributes": attrs},
            "messages": _msg(f"{text} {_t(lang, *MORE)}")}


def _ask_code(attrs, lang):
    return {"sessionState": {"dialogAction": {"type": "ElicitSlot", "slotToElicit": "accountCode"},
                             "intent": {"name": "AccountInfo", "state": "InProgress", "slots": {"accountCode": None}}, "sessionAttributes": attrs},
            "messages": _msg(_t(lang, "Sure. What is your account code?", "Claro. ¿Cuál es su código de cuenta?"))}


def _escalate(intent, attrs, lang, reason, code=""):
    code = code or attrs.get("accountCode", "")
    queue = lk.route(lk.PERSONAS.get(code) if code else None)
    persona = lk.PERSONAS.get(code) if code else None
    why = {"requested_agent": "Customer asked for a person", "not_found": "Account not found",
           "not_understood": "The AI could not understand the request"}[reason]
    if persona and persona.get("daysPastDue") is not None:
        status = f", special status {persona['specialStatus']}" if persona.get("specialStatus") else ""
        summary = (f"{persona['name']}, account {code}: {persona['daysPastDue']} days past due{status}, "
                   f"balance ${persona['balance']:,.2f}, payment due {persona['paymentDue']}. {why}.")
    else:
        summary = f"No account identified. {why}."
    # Shown to the agent in the "Transferred by the AI assistant" guide (setup_guide_flow.py)
    attrs.update({
        "outcome": "escalate", "reason": why, "language": lang, "languageLabel": "English" if lang == "en" else "Spanish",
        "queueName": lk.SPOKEN[queue][0], "queueArn": lk.QUEUE_ARNS.get(queue, ""),
        "accountCode": code or "none", "summary": summary,
    })
    text = {
        "requested_agent": ("Of course. I will connect you with a team member.", "Claro. Le comunico con un compañero del equipo."),
        "not_found": ("I could not find that account. I will connect you with a team member.", "No encontré esa cuenta. Le comunico con un compañero del equipo."),
        "not_understood": ("Sorry, I did not catch that. I will connect you with a team member.", "Lo siento, no le entendí. Le comunico con un compañero del equipo."),
    }[reason][0 if lang == "en" else 1]
    return _close(intent, attrs, text, "Failed" if reason == "not_understood" else "Fulfilled")


def _persona(attrs):
    p = lk.PERSONAS.get(attrs.get("accountCode", ""))
    return p if p and p.get("balance") is not None else None


def _balance_text(p, lang):
    return _t(lang, f"Your balance is {p['balance']:,.2f} dollars.", f"Su saldo es de {p['balance']:,.2f} dólares.")


def _due_text(p, lang):
    past = datetime.date.fromisoformat(p["paymentDue"]) < datetime.date.today()
    when = _date(p["paymentDue"], lang)
    return _t(lang, f"Your payment {'was due' if past else 'is due'} on {when}.", f"Su pago {'venció' if past else 'vence'} el {when}.")


def handler(event, context):
    state = event["sessionState"]
    intent = state["intent"]
    lang = "es" if event["bot"]["localeId"].startswith("es") else "en"
    attrs = dict(state.get("sessionAttributes") or {})
    attrs["language"] = lang
    for stale in ("outcome", "switchTo"):  # an outcome belongs to the turn that ends the conversation
        attrs.pop(stale, None)
    name = intent["name"]

    if name == "TalkToAgent":
        return _escalate(intent, attrs, lang, "requested_agent")
    if name == "SwitchLanguage":
        # Asking for the language already in use ("sí, en español" to the Spanish bot) is not a switch:
        # on 2026-11-10 that bounced the caller between the two bots.
        said = str(event.get("inputTranscript", "")).lower()
        wants = "es" if any(w in said for w in ("spanish", "español", "espanol")) else \
                "en" if any(w in said for w in ("english", "inglés", "ingles")) else ("es" if lang == "en" else "en")
        if wants == lang:
            return {"sessionState": {"dialogAction": {"type": "ElicitIntent"}, "sessionAttributes": attrs},
                    "messages": _msg(_t(lang, "Sure, we will continue in English. How can I help?", "Claro, seguimos en español. ¿En qué puedo ayudarle?"))}
        # The flow reconnects the caller to the bot in the other language (setup_ai_flow.py)
        attrs.update({"outcome": "switch_language", "switchTo": wants})
        return _close(intent, attrs, "")  # was "Of course. Un momento, por favor.": it was followed by the new greeting (2026-11-11)
    if name == "EndCall":
        attrs.update({"outcome": "resolved"})
        return _close(intent, attrs, _t(lang, "Thank you for calling. Goodbye.", "Gracias por llamar. Hasta luego."))
    if name == "AccountInfo":
        slot = (intent.get("slots") or {}).get("accountCode")
        code = str(((slot or {}).get("value") or {}).get("interpretedValue", "")).strip()
        if not code:
            # The slot is optional (2026-11-11): a caller recognized by number already has an account; anyone else is asked for it
            code = attrs.get("accountCode", "")
            if not (code and code != "none" and lk.PERSONAS.get(code)):
                return _ask_code(attrs, lang)
        persona = lk.PERSONAS.get(code)
        if not persona or persona.get("balance") is None:
            return _escalate(intent, attrs, lang, "not_found", code)
        attrs["accountCode"] = code
        first = persona["name"].split()[0]
        # "What is my account?" answers with the account number first (2026-11-11), then balance and due date
        return _more(attrs, _t(lang, f"{first}, your account number is {code}. ", f"{first}, su número de cuenta es el {code}. ") + _balance_text(persona, lang) + " " + _due_text(persona, lang), lang)
    if name in ("Balance", "DueDate"):
        p = _persona(attrs)
        if not p:
            return _ask_code(attrs, lang)
        return _more(attrs, _balance_text(p, lang) if name == "Balance" else _due_text(p, lang), lang)
    if name == "PaymentOptions":
        return _more(attrs, _t(lang, "You can pay with the text to pay link we send you, or I can connect you with a team member who can help you pay.",
                               "Puede pagar con el enlace de pago por mensaje de texto que le enviamos, o puedo comunicarle con un compañero que le ayude a pagar."), lang)
    # a silence is not a misunderstanding: say we are still here, and only end the call after several in a row
    if not str(event.get("inputTranscript", "")).strip():
        n = int(attrs.get("silences", "0")) + 1
        attrs["silences"] = str(n)
        if n >= 4:
            attrs["outcome"] = "resolved"
            return _close(intent, attrs, _t(lang, "I did not hear anything, so I will end the call. Goodbye.", "No escuché nada, así que terminaré la llamada. Hasta luego."))
        return {"sessionState": {"dialogAction": {"type": "ElicitIntent"}, "sessionAttributes": attrs},
                "messages": _msg(_t(lang, "I am still here. You can ask about your balance, your due date, how to pay, or ask for a person.",
                                    "Sigo aquí. Puede preguntar por su saldo, su fecha de pago, cómo pagar, o pedir hablar con una persona."))}
    attrs["silences"] = "0"
    # fallback: one more chance, then hand over to a person
    n = int(attrs.get("fallbacks", "0")) + 1
    if n >= 2:
        return _escalate(intent, attrs, lang, "not_understood")
    attrs["fallbacks"] = str(n)
    return {"sessionState": {"dialogAction": {"type": "ElicitIntent"}, "sessionAttributes": attrs},
            "messages": _msg(_t(lang, "Sorry, I did not catch that. You can ask about your balance, your due date, how to pay, or ask for a person.",
                                "Lo siento, no le entendí. Puede preguntar por su saldo, su fecha de pago, cómo pagar, o pedir hablar con una persona."))}
