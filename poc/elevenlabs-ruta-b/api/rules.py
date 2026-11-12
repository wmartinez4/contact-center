"""Negotiation rules of the collections demo (assumptions in ../diseno.md, section 8).

The agent never decides terms: it asks this module what is allowed and only offers validated plans.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN

DEFAULTS = {
    "maxPromiseDays": 7,                 # latest date for a promise, or for the first installment
    "maxInstallments": 3,
    "highDelinquencyDays": 30,           # more days past due than this lowers the installment limit
    "maxInstallmentsHighDelinquency": 2,
    "installmentIntervalDays": 14,
}
CENT = Decimal("0.01")


@dataclass
class Customer:
    account: str
    first_name: str
    last_name: str
    language: str
    balance: Decimal
    days_past_due: int
    payment_due: str | None = None
    special_status: str | None = None
    overrides: dict = field(default_factory=dict)
    profile_id: str | None = None

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class PlanResult:
    accepted: bool
    reason: str | None = None
    plan_type: str | None = None
    payments: list = field(default_factory=list)   # [(date, Decimal)]
    summary_en: str = ""
    summary_es: str = ""


def effective_rules(customer):
    """Default rules, then the customer's overrides. A customer's own maxInstallments beats the
    high-delinquency limit; otherwise the high-delinquency limit applies when days past due exceed it."""
    rules = {**DEFAULTS, **customer.overrides}
    if "maxInstallments" not in customer.overrides and customer.days_past_due > rules["highDelinquencyDays"]:
        rules["maxInstallments"] = rules["maxInstallmentsHighDelinquency"]
    return rules


def case_view(customer, today):
    """What the agent may say and offer for this customer today."""
    rules = effective_rules(customer)
    latest = today + timedelta(days=rules["maxPromiseDays"])
    return {
        "customerName": customer.full_name,
        "language": customer.language,
        "balance": f"{customer.balance:.2f}",
        "daysPastDue": customer.days_past_due,
        "paymentDue": customer.payment_due or "",
        "specialStatus": customer.special_status or "",
        "canNegotiate": not customer.special_status,
        "latestPromiseDate": latest.isoformat(),
        "maxInstallments": rules["maxInstallments"],
        "installmentIntervalDays": rules["installmentIntervalDays"],
        "latestFirstInstallmentDate": latest.isoformat(),
        "discountsAllowed": False,
    }


def propose_plan(customer, plan_type, today, installments=None, first_payment_date=None):
    """Validates a plan. plan_type: full (pay the balance now or by a date), promise (pay the balance by a
    date) or installments. Returns the schedule when accepted, or a machine-readable reason."""
    if customer.special_status:
        return PlanResult(False, "special_status")
    rules = effective_rules(customer)
    latest = today + timedelta(days=rules["maxPromiseDays"])
    pay_date = first_payment_date or today
    if pay_date < today:
        return PlanResult(False, "date_in_past")
    if pay_date > latest:
        return PlanResult(False, f"date_after_{latest.isoformat()}")

    if plan_type in ("full", "promise"):
        if plan_type == "promise" and first_payment_date is None:
            return PlanResult(False, "promise_needs_date")
        payments = [(pay_date, customer.balance)]
    elif plan_type == "installments":
        if not isinstance(installments, int) or installments < 2:
            return PlanResult(False, "installments_min_2")
        if installments > rules["maxInstallments"]:
            return PlanResult(False, f"installments_max_{rules['maxInstallments']}")
        payments = _schedule(customer.balance, installments, pay_date, rules["installmentIntervalDays"])
    else:
        return PlanResult(False, "unknown_plan_type")

    en, es = _summaries(plan_type, payments)
    return PlanResult(True, None, plan_type, payments, en, es)


def _schedule(balance, count, first, interval_days):
    """Equal installments rounded down to the cent; the last one absorbs the remainder (no discounts)."""
    amount = (balance / count).quantize(CENT, rounding=ROUND_DOWN)
    amounts = [amount] * (count - 1) + [balance - amount * (count - 1)]
    return [(first + timedelta(days=interval_days * i), a) for i, a in enumerate(amounts)]


def _summaries(plan_type, payments):
    first_date, first_amount = payments[0]
    if plan_type != "installments":
        return (f"Pay ${first_amount:.2f} on {first_date.isoformat()}",
                f"Pago de ${first_amount:.2f} el {first_date.isoformat()}")
    count, last_amount = len(payments), payments[-1][1]
    tail_en = f" (last ${last_amount:.2f})" if last_amount != first_amount else ""
    tail_es = f" (la última de ${last_amount:.2f})" if last_amount != first_amount else ""
    return (f"{count} installments of ${first_amount:.2f}{tail_en} from {first_date.isoformat()}",
            f"{count} cuotas de ${first_amount:.2f}{tail_es} desde el {first_date.isoformat()}")
