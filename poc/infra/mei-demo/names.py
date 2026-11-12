"""Names agents and supervisors see in Connect (queues, quick connects, routing profiles, hours, flows).

Internal keys (Q-16-30, front-line, ...) stay in code. Every display name starts with "CS - " so the demo's
resources stand apart from the instance's AWS samples. Older names are renamed on the next run:
"<prefix>-<key>" (before 2026-11-10) and the unprefixed display names used briefly on 2026-11-10.
"""
DISPLAY_PREFIX = "CS - "

_QUEUES = {
    "Q-Current": "Collections - Current",
    "Q-1-8": "Collections - 1 to 8 days",
    "Q-9-15": "Collections - 9 to 15 days",
    "Q-16-30": "Collections - 16 to 30 days",
    "Q-31Plus": "Collections - 31+ days",
    "Q-Redemptions": "Redemptions",
    "Q-EPD": "Early Payment Default",
    "Q-Fallback": "General Assistance",
    "Q-CallerOnly": "Test Caller Only",
}
_PROFILES = {"front-line": "Front Line", "specialist": "Specialist", "caller": "Test Caller"}
_HOURS = "Open 24/7"

QUEUE_NAMES = {k: DISPLAY_PREFIX + v for k, v in _QUEUES.items()}
ROUTING_PROFILE_NAMES = {k: DISPLAY_PREFIX + v for k, v in _PROFILES.items()}
HOURS_NAME = DISPLAY_PREFIX + _HOURS


def quick_connect_name(queue_key):
    return f"{DISPLAY_PREFIX}Transfer to {_QUEUES[queue_key]}"


def old_queue_names(key, prefix):
    return (f"{prefix}-{key}", _QUEUES[key])


def old_profile_names(key, prefix):
    return (f"{prefix}-{key}", _PROFILES[key])


def old_quick_connect_names(queue_key, prefix):
    return (f"{prefix}-to-{queue_key}", f"Transfer to {_QUEUES[queue_key]}")


def old_hours_names(prefix):
    return (f"{prefix}-always", _HOURS)


def queue_key(name, prefix):
    """Internal key for a queue, by current or older name; None if not a demo queue."""
    for key, display in QUEUE_NAMES.items():
        if name == display or name in old_queue_names(key, prefix):
            return key
    return None

_FLOWS = {
    "inbound": "Inbound - Collections Routing",
    "ai-inbound": "Inbound - AI Agent",
    "ai-inbound-next": "Sandbox - AI Agent (Nova 2.5 Sonic)",
    "sandbox-simple": "Sandbox - Simple Flow",
    "sandbox-inbound": "Sandbox - Copy of Collections Routing",
    "queue-callback-en": "Queue - Callback Offer (English)",
    "queue-callback-es": "Queue - Callback Offer (Spanish)",
    "outbound-whisper": "Outbound Whisper - Recording",
    "guide-transfer": "Guide - Transfer Reason",
    "guide-agent-transfer": "Guide - Agent Transfer",
    "guide-customer": "Guide - Customer On The Line",
    "guide-wrapup": "Guide - Wrap-up",
    "queue-transfer": "Queue Transfer - With Context",
}
FLOW_NAMES = {k: DISPLAY_PREFIX + v for k, v in _FLOWS.items()}


def rename_legacy_flows(connect, iid, prefix):
    """Flows under an older name get their current display name; safe to call on every run."""
    legacy = {f"{prefix}-{k}": v for k, v in FLOW_NAMES.items()}
    legacy.update({_FLOWS[k]: v for k, v in FLOW_NAMES.items()})
    tok = None
    while True:
        r = connect.list_contact_flows(InstanceId=iid, MaxResults=1000, **({"NextToken": tok} if tok else {}))
        for f in r["ContactFlowSummaryList"]:
            if f["Name"] in legacy:
                connect.update_contact_flow_name(InstanceId=iid, ContactFlowId=f["Id"], Name=legacy[f["Name"]])
                print(f"flow renamed: {f['Name']} -> {legacy[f['Name']]}")
        tok = r.get("NextToken")
        if not tok:
            return
