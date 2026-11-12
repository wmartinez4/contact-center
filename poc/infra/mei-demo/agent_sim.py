#!/usr/bin/env python3
"""Simulated agent for unattended test calls, so Contact Lens gets both sides of a conversation.

`start en|es` points demo.agent1's and demo.agent2's phones at the sandbox line (desk phone mode) and the sandbox line at a flow that
speaks an agent script with pauses. `stop` puts them back on the softphone and the sandbox line back on
"CS - Sandbox - Simple Flow". Always run `stop` after the test.

    AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> EXPECTED_ACCOUNT=<account> DEMO_PREFIX=demo python3 agent_sim.py start en|es | stop
"""
import json
import sys

import setup_part_a as s
from names import DISPLAY_PREFIX

c, IID = s.connect, s.IID
AGENTS = [f"{s.PREFIX}.agent1", f"{s.PREFIX}.agent2"]
# Generic agent side, valid for any account (the customer side says the specifics)
SCRIPTS = {
    "en": ("Danielle", [
        "Thank you for calling, this is the Collections team. This is an attempt to collect a debt. Who am I speaking with?",
        "Thank you. I have your account open, and I can see your balance and your due date.",
        "I understand, that happens. Would you like to set up a payment arrangement today?",
        "Yes, I can do that. Half today, and the rest on the twenty eighth, with no extra fees.",
        "Done. The arrangement is noted and you will receive a confirmation email shortly.",
        "You're welcome. Thank you for calling, have a great day.",
    ]),
    "es": ("Lupe", [
        "Gracias por llamar, le atiende el equipo de Cobranza. Esta es una gestión de cobro. ¿Con quién tengo el gusto?",
        "Gracias. Tengo su cuenta abierta y veo su saldo y su fecha de pago.",
        "Entiendo, no se preocupe. ¿Quiere que hagamos un acuerdo de pago hoy?",
        "Claro. Una parte hoy y el resto el veinte de noviembre, sin cargos adicionales.",
        "Listo, el acuerdo queda registrado y le llegará una confirmación por correo.",
        "Con gusto. Gracias por llamar, que tenga buen día.",
    ]),
}


def sim_flow(lang, gap=8):
    voice, lines = SCRIPTS[lang]
    # 2 s of silence first: the start of the first line was lost while the agent leg connected
    ssml = "<speak><break time=\"2s\"/>" + "".join(f'{t}<break time="{gap}s"/>' for t in lines) + "</speak>"
    a = [
        s.act("Voice", "UpdateContactTextToSpeechVoice", {"TextToSpeechVoice": voice, "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"},
              "Talk", s.err("Talk", s.NM)),
        s.act("Talk", "MessageParticipant", {"SSML": ssml}, "Bye", s.err("Bye", s.NM)),
        s.act("Bye", "DisconnectParticipant", {}),
    ]
    name = f"{DISPLAY_PREFIX}Test - Agent Simulator ({lang.upper()})"
    content = json.dumps(s.layout({"Version": "2019-10-30", "StartAction": "Voice", "Metadata": {}, "Actions": a}))
    flows = c.list_contact_flows(InstanceId=IID, ContactFlowTypes=["CONTACT_FLOW"], MaxResults=1000)["ContactFlowSummaryList"]
    f = next((f for f in flows if f["Name"] == name), None)
    if f:
        c.update_contact_flow_content(InstanceId=IID, ContactFlowId=f["Id"], Content=content)
        return f["Id"]
    return c.create_contact_flow(InstanceId=IID, Name=name, Type="CONTACT_FLOW", Content=content,
                                 Description="Test only: speaks an agent script when a test call reaches agent1")["ContactFlowId"]


def sandbox():
    for pid in s.PHONE_IDS:
        n = c.describe_phone_number(PhoneNumberId=pid)["ClaimedPhoneNumberSummary"]
        if n.get("PhoneNumberDescription", "").lower().startswith(f"{s.PREFIX} sandbox"):
            return pid, n["PhoneNumber"]
    sys.exit("sandbox number not found")


def agents():
    for u in c.list_users(InstanceId=IID)["UserSummaryList"]:
        if u["Username"] in AGENTS:
            yield u["Id"], c.describe_user(InstanceId=IID, UserId=u["Id"])["User"]["PhoneConfig"]


def start(lang):
    pid, number = sandbox()
    c.associate_phone_number_contact_flow(PhoneNumberId=pid, InstanceId=IID, ContactFlowId=sim_flow(lang))
    for uid, cfg in agents():
        cfg.update({"PhoneType": "DESK_PHONE", "DeskPhoneNumber": number, "AutoAccept": True})
        c.update_user_phone_config(InstanceId=IID, UserId=uid, PhoneConfig=cfg)
    print(f"agents now answer on the sandbox line with the {lang} agent script")


def stop():
    pid, _ = sandbox()
    simple = next(f["Id"] for f in c.list_contact_flows(InstanceId=IID, ContactFlowTypes=["CONTACT_FLOW"], MaxResults=1000)["ContactFlowSummaryList"]
                  if f["Name"] == s.FLOW_NAMES["sandbox-simple"])
    c.associate_phone_number_contact_flow(PhoneNumberId=pid, InstanceId=IID, ContactFlowId=simple)
    for uid, cfg in agents():
        cfg = {k: v for k, v in cfg.items() if k != "DeskPhoneNumber"}
        cfg["PhoneType"] = "SOFT_PHONE"
        c.update_user_phone_config(InstanceId=IID, UserId=uid, PhoneConfig=cfg)
    print("agents back on the softphone; sandbox line back on the simple flow")


if __name__ == "__main__":
    if sys.argv[1] == "start":
        start(sys.argv[2])
    else:
        stop()
