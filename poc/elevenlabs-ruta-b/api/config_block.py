"""Reads the per-customer rule overrides stored under a [config] marker in a profile's Additional info.

Everything before the marker is free text for agents. After it, "key: value" pairs may be on separate
lines or on one line (the agent workspace shows the field on one line). Unknown keys, empty values and
values that are not whole numbers are ignored, so the caller falls back to the default rules.
"""
import re

KNOWN_KEYS = ("maxPromiseDays", "maxInstallments", "highDelinquencyDays",
              "maxInstallmentsHighDelinquency", "installmentIntervalDays")
_CANONICAL = {k.lower(): k for k in KNOWN_KEYS}
_MARKER = re.compile(r"\[\s*config\s*\]", re.IGNORECASE)
# The value may not cross a line break: "maxInstallments:" followed by a new line means "no value".
_PAIR = re.compile(r"([A-Za-z][A-Za-z0-9_]*)[ \t]*:[ \t]*([^\s]*)")


def split_notes(text):
    """Returns (notes, config_text). config_text is None when the marker is missing."""
    text = text or ""
    match = _MARKER.search(text)
    if not match:
        return text.strip(), None
    return text[:match.start()].strip(), text[match.end():]


def parse_overrides(text):
    """Returns {canonical key: int} with only the valid overrides, plus the list of ignored entries."""
    _, config_text = split_notes(text)
    overrides, ignored = {}, []
    if config_text is None:
        return overrides, ignored
    for raw_key, raw_value in _PAIR.findall(config_text):
        key = _CANONICAL.get(raw_key.lower())
        if key is None:
            ignored.append(f"unknown key {raw_key}")
        elif raw_value == "":
            continue
        elif raw_value.isdigit() and int(raw_value) > 0:
            overrides[key] = int(raw_value)
        else:
            ignored.append(f"invalid value {raw_key}={raw_value}")
    return overrides, ignored
