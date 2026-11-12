"""Texts of every fixed prompt of the demo, in English and Spanish.

build_prompts.py turns them into audio (ElevenLabs), uploads them and creates Connect prompts named
<prefix>-p-<key>. The flow plays a prompt when it exists and falls back to the same text read by Polly.
"""

# queue -> (English, Spanish) spoken name; keep in sync with lookup_handler.SPOKEN
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

FIXED = {
    "notice_en": "This call may be recorded.",
    "notice_es": "Esta llamada puede ser grabada.",
    "menu_both": "Thank you for calling. For English, press one. Para español, oprima dos.",
    "menu_en": "Thank you for calling. For English, press one.",
    "menu_es": "Para español, oprima dos.",
    "case_en": "Please enter your account number.",
    "case_es": "Por favor, marque su número de cuenta.",
    "cb_offer_en": "Press 1 if you want to receive a callback when an agent is available. Press 2 to stay in the queue.",
    "cb_offer_es": "Oprima 1 si desea que le devolvamos la llamada cuando haya un agente disponible. Oprima 2 para permanecer en la fila.",
    "cb_invalid_en": "The number entered is invalid. Please try again.",
    "cb_invalid_es": "El número ingresado no es válido. Inténtelo de nuevo.",
    "cb_enter_en": "Enter the number you would like to be called back at.",
    "cb_enter_es": "Marque el número al que desea que le llamemos.",
    "cb_error_en": "Something went wrong. Goodbye.",
    "cb_error_es": "Algo salió mal. Hasta luego.",
    "cb_confirm_en": "You will be called back when the next agent is available.",
    "cb_confirm_es": "Le llamaremos cuando el próximo agente esté disponible.",
}


def announcements():
    out = {
        # Generic transfer announcements (2026-11-11): no queue name
        "ann_generic_en": "Account found. Transferring you to the collections area.",
        "ann_generic_es": "Cuenta encontrada. Lo comunico con el área de cobranza.",
        "ann_notfound_en": "We could not find the account. Transferring you to an agent.",
        "ann_notfound_es": "No encontramos la cuenta. Lo comunico con un agente.",
    }
    for queue, (en, es) in SPOKEN.items():
        if queue == "Q-Fallback":
            out[f"ann_{queue}_en"] = f"We could not find the account. Connecting you to {en}."
            out[f"ann_{queue}_es"] = f"No encontramos la cuenta. Lo comunico con {es}."
        else:
            out[f"ann_{queue}_en"] = f"Account found. Connecting you to {en}."
            out[f"ann_{queue}_es"] = f"Cuenta encontrada. Lo comunico con {es}."
    return out


def all_prompts():
    d = dict(FIXED)
    d.update(announcements())
    return d
