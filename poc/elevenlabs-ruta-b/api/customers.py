"""Loads demo customers from Amazon Connect Customer Profiles, the single source of truth at call time.

The demo profiles carry the account data as custom attributes (balance, daysPastDue, language,
paymentDue, specialStatus) and the rule overrides in Additional info under [config].
"""
from decimal import Decimal, InvalidOperation

from config_block import parse_overrides
from rules import Customer


def customer_from_profile(profile):
    attrs = profile.get("Attributes") or {}
    overrides, ignored = parse_overrides(profile.get("AdditionalInformation"))
    try:
        balance = Decimal(attrs.get("balance") or "0")
    except InvalidOperation:
        balance = Decimal("0")
    days = attrs.get("daysPastDue") or "0"
    customer = Customer(
        account=profile.get("AccountNumber") or "",
        first_name=profile.get("FirstName") or "",
        last_name=profile.get("LastName") or "",
        language=(attrs.get("language") or "en").lower(),
        balance=balance,
        days_past_due=int(days) if days.lstrip("-").isdigit() else 0,
        payment_due=attrs.get("paymentDue") or None,
        special_status=attrs.get("specialStatus") or None,
        overrides=overrides,
        profile_id=profile.get("ProfileId"),
    )
    return customer, ignored


def find_by_phone(client, domain, phone):
    """First profile whose phone fields match (Customer Profiles' _phone key covers all of them)."""
    return _first(client, domain, "_phone", phone)


def find_by_account(client, domain, account):
    return _first(client, domain, "_account", account)


def _first(client, domain, key, value):
    if not value:
        return None, []
    items = client.search_profiles(DomainName=domain, KeyName=key, Values=[value]).get("Items", [])
    return customer_from_profile(items[0]) if items else (None, [])
