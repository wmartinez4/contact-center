"""Simulated account lookup + routing rules for the demo.

Stands in for iDMS plus the routing rules. Input comes from the contact flow
(Details.Parameters.caseCode, language); output is a flat string map.
Special status is evaluated BEFORE days past due.
"""
import json
import os

with open(os.path.join(os.path.dirname(__file__), "personas.json"), encoding="utf-8") as f:
    PERSONAS = {p["code"]: p for p in json.load(f)["personas"]}

QUEUE_ARNS = json.loads(os.environ.get("QUEUE_ARNS", "{}"))
PROMPT_IDS = json.loads(os.environ.get("PROMPT_IDS", "{}"))  # announcement prompts, by key


def prompt_arn(key):
    pid = PROMPT_IDS.get(key)
    if not pid or not QUEUE_ARNS:
        return ""
    instance_arn = next(iter(QUEUE_ARNS.values())).split("/queue/")[0]
    return f"{instance_arn}/prompt/{pid}"

SPOKEN = {
    "Q-Current": ("current accounts", "cuentas al corriente"),
    "Q-1-8": ("1 to 8 days past due", "1 a 8 días de mora"),
    "Q-9-15": ("9 to 15 days past due", "9 a 15 días de mora"),
    "Q-16-30": ("16 to 30 days past due", "16 a 30 días de mora"),
    "Q-31Plus": ("31 plus days past due", "más de 31 días de mora"),
    "Q-Redemptions": ("Redemptions", "Redemptions"),
    "Q-EPD": ("Early Payment Default", "pago temprano fallido"),
    "Q-Fallback": ("general assistance", "atención general"),
}
STATUS_QUEUE = {"Redemptions": "Q-Redemptions", "EPD": "Q-EPD"}


def route(persona):
    if persona is None or persona.get("daysPastDue") is None:
        return "Q-Fallback"
    status = persona.get("specialStatus")
    if status in STATUS_QUEUE:  # special status wins over delinquency
        return STATUS_QUEUE[status]
    days = persona["daysPastDue"]
    if days <= 0:
        return "Q-Current"
    if days <= 8:
        return "Q-1-8"
    if days <= 15:
        return "Q-9-15"
    if days <= 30:
        return "Q-16-30"
    return "Q-31Plus"


BY_PHONE = {p["phone"]: p for p in PERSONAS.values() if p.get("phone")}


def summary(persona):
    """One line for the agent's transfer panel (English, like the rest of the agent workspace)."""
    if persona is None or persona.get("daysPastDue") is None:
        return "Account not found."
    status = f", special status {persona['specialStatus']}" if persona.get("specialStatus") else ""
    return (f"{persona['name']}, account {persona['code']}: {persona['daysPastDue']} days past due{status}, "
            f"balance ${persona['balance']:,.2f}, payment due {persona['paymentDue']}.")


def greeting(persona, lang):
    first = persona["name"].split()[0]
    days = persona["daysPastDue"]
    if lang == "es":
        return (f"Hola {first}, gracias por llamar. Vemos que su cuenta tiene {days} días de atraso. "
                "Lo comunico con un agente de cobranza.")
    return (f"Hi {first}, thanks for calling. I see your account is {days} days past due. "
            "Let me connect you with a collections agent.")


def ai_greeting(persona, lang):
    """First line of the AI agent for a caller recognized by number."""
    first = persona["name"].split()[0]
    if lang == "es":
        return f"Hola {first}, gracias por llamar. ¿En qué puedo ayudarle hoy?"
    return f"Hi {first}, thanks for calling. How can I help you today?"


def by_phone(phone):
    """Caller identified by number (ANI), as iDMS would do in production: no case menu."""
    persona = BY_PHONE.get(phone)
    if persona is None:
        return {"found": "false"}
    lang = persona["language"]
    queue = route(persona)
    return {
        "found": "true",
        "accountCode": persona["code"],
        "language": lang,
        "customerName": persona["name"],
        "daysPastDue": str(persona["daysPastDue"]),
        "specialStatus": persona.get("specialStatus") or "None",
        "balance": str(persona["balance"]),
        "paymentDue": persona["paymentDue"],
        "queueName": queue,
        "queueArn": QUEUE_ARNS.get(queue, ""),
        "announceText": greeting(persona, lang),
        "customerSummary": summary(persona),
        "queueLabel": SPOKEN[queue][0],
        "firstName": persona["name"].split()[0],
        "aiGreeting": ai_greeting(persona, lang),
    }


PROFILES_DOMAIN = os.environ.get("PROFILES_DOMAIN", "")


def link_phone(code, phone):
    """The agent workspace finds the customer profile by the caller's number. A caller who picked an account in the menu
    from a number that is not registered would find none, so the number is kept as the profile's mobile phone (and
    removed from any other profile it was linked to). Best effort: a failure never affects the routing."""
    persona = PERSONAS.get(code)
    if not (PROFILES_DOMAIN and phone and persona and persona.get("daysPastDue") is not None) or phone in BY_PHONE:
        return
    try:
        import boto3
        cp = boto3.client("customer-profiles")
        mine = cp.search_profiles(DomainName=PROFILES_DOMAIN, KeyName="_account", Values=[code])["Items"]
        if not mine:
            return
        for other in cp.search_profiles(DomainName=PROFILES_DOMAIN, KeyName="_phone", Values=[phone])["Items"]:
            if other["ProfileId"] != mine[0]["ProfileId"] and other.get("MobilePhoneNumber") == phone:
                cp.update_profile(DomainName=PROFILES_DOMAIN, ProfileId=other["ProfileId"], MobilePhoneNumber="")
        if mine[0].get("MobilePhoneNumber") != phone:
            cp.update_profile(DomainName=PROFILES_DOMAIN, ProfileId=mine[0]["ProfileId"], MobilePhoneNumber=phone)
    except Exception as e:  # noqa: BLE001
        print("link_phone failed:", repr(e))


def handler(event, context):
    params = event.get("Details", {}).get("Parameters", {})
    if params.get("phone"):
        return by_phone(str(params["phone"]).strip())
    code = str(params.get("caseCode", "")).strip()
    lang = "es" if params.get("language") == "es" else "en"
    link_phone(code, str(params.get("callerPhone", "")).strip())
    persona = PERSONAS.get(code)
    queue = route(persona)
    spoken = SPOKEN[queue][1 if lang == "es" else 0]
    if persona is None or persona.get("daysPastDue") is None:
        announce = "No encontramos la cuenta. Lo comunico con un agente." if lang == "es" else "We could not find the account. Transferring you to an agent."
    else:
        announce = "Cuenta encontrada. Lo comunico con el área de cobranza." if lang == "es" else "Account found. Transferring you to the collections area."  # generic: no queue name (2026-11-11)
    return {
        "customerName": (persona or {}).get("name") or "",
        "daysPastDue": str((persona or {}).get("daysPastDue") if (persona or {}).get("daysPastDue") is not None else ""),
        "specialStatus": (persona or {}).get("specialStatus") or "None",
        "balance": str((persona or {}).get("balance") or ""),
        "paymentDue": (persona or {}).get("paymentDue") or "",
        "queueName": queue,
        "queueArn": QUEUE_ARNS.get(queue, ""),
        "announceText": announce,
        "announcePromptArn": prompt_arn(f"ann_{'notfound' if persona is None or persona.get('daysPastDue') is None else 'generic'}_{lang}"),
        "customerSummary": summary(persona),
        "queueLabel": SPOKEN[queue][0],
    }
