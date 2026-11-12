import os
import sys
import unittest
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config_block import parse_overrides, split_notes  # noqa: E402
from customers import customer_from_profile  # noqa: E402
from rules import Customer, case_view, effective_rules, propose_plan  # noqa: E402

TODAY = date(2026, 11, 12)


def customer(days=5, balance="1180.00", overrides=None, special=None):
    return Customer("2", "Maria", "Hernandez", "es", Decimal(balance), days, "2026-11-04", special, overrides or {})


class ConfigBlockTests(unittest.TestCase):
    def test_reads_value_on_its_own_line(self):
        self.assertEqual(parse_overrides("Notes.\n[config]\nmaxInstallments: 4")[0], {"maxInstallments": 4})

    def test_reads_value_without_space_as_saved_in_connect(self):
        self.assertEqual(parse_overrides("Notes.\n[config]\nmaxInstallments:2")[0], {"maxInstallments": 2})

    def test_reads_pairs_on_one_line(self):
        text = "Notes. [CONFIG] MaxInstallments: 4 maxPromiseDays: 5"
        self.assertEqual(parse_overrides(text)[0], {"maxInstallments": 4, "maxPromiseDays": 5})

    def test_empty_value_does_not_swallow_next_line(self):
        self.assertEqual(parse_overrides("[config]\nmaxInstallments:\nmaxPromiseDays: 5")[0], {"maxPromiseDays": 5})

    def test_invalid_and_unknown_entries_are_ignored(self):
        overrides, ignored = parse_overrides("[config]\nmaxInstallments: cuatro\ncolor: red")
        self.assertEqual(overrides, {})
        self.assertEqual(len(ignored), 2)

    def test_colons_in_notes_are_not_config(self):
        self.assertEqual(parse_overrides("Llamar a las 5:00 pm. maxInstallments: 9")[0], {})

    def test_split_keeps_notes(self):
        self.assertEqual(split_notes("Prefiere español.\n[config]\nmaxInstallments:")[0], "Prefiere español.")


class RuleTests(unittest.TestCase):
    def test_default_limit_is_three(self):
        self.assertEqual(effective_rules(customer())["maxInstallments"], 3)

    def test_high_delinquency_lowers_limit_to_two(self):
        self.assertEqual(effective_rules(customer(days=47))["maxInstallments"], 2)

    def test_customer_override_beats_high_delinquency(self):
        self.assertEqual(effective_rules(customer(days=47, overrides={"maxInstallments": 4}))["maxInstallments"], 4)

    def test_full_payment_today(self):
        result = propose_plan(customer(), "full", TODAY)
        self.assertTrue(result.accepted)
        self.assertEqual(result.payments, [(TODAY, Decimal("1180.00"))])

    def test_promise_within_seven_days(self):
        self.assertTrue(propose_plan(customer(), "promise", TODAY, first_payment_date=date(2026, 11, 19)).accepted)

    def test_promise_after_seven_days_is_rejected(self):
        result = propose_plan(customer(), "promise", TODAY, first_payment_date=date(2026, 11, 20))
        self.assertEqual(result.reason, "date_after_2026-11-19")

    def test_three_installments_add_up_to_balance(self):
        result = propose_plan(customer(), "installments", TODAY, installments=3)
        self.assertTrue(result.accepted)
        self.assertEqual([a for _, a in result.payments], [Decimal("393.33"), Decimal("393.33"), Decimal("393.34")])
        self.assertEqual([d for d, _ in result.payments], [date(2026, 11, 12), date(2026, 11, 26), date(2026, 12, 10)])
        self.assertIn("3 cuotas de $393.33", result.summary_es)

    def test_four_installments_rejected_by_default(self):
        self.assertEqual(propose_plan(customer(), "installments", TODAY, installments=4).reason, "installments_max_3")

    def test_four_installments_allowed_by_override(self):
        self.assertTrue(propose_plan(customer(overrides={"maxInstallments": 4}), "installments", TODAY, installments=4).accepted)

    def test_special_status_never_negotiates(self):
        self.assertEqual(propose_plan(customer(special="Redemptions"), "full", TODAY).reason, "special_status")
        self.assertFalse(case_view(customer(special="EPD"), TODAY)["canNegotiate"])

    def test_case_view_shows_limits(self):
        view = case_view(customer(days=47, balance="5210.30"), TODAY)
        self.assertEqual(view["maxInstallments"], 2)
        self.assertEqual(view["latestPromiseDate"], "2026-11-19")


class ProfileMappingTests(unittest.TestCase):
    def test_maps_live_profile_shape(self):
        profile = {"AccountNumber": "4", "FirstName": "Luisa", "LastName": "Ramirez",
                   "AdditionalInformation": "Prefiere español.\n[config]\nmaxInstallments:2",
                   "Attributes": {"balance": "5210.30", "daysPastDue": "47", "language": "es", "paymentDue": "2026-09-23"}}
        c, ignored = customer_from_profile(profile)
        self.assertEqual((c.full_name, c.balance, c.days_past_due, c.overrides), ("Luisa Ramirez", Decimal("5210.30"), 47, {"maxInstallments": 2}))
        self.assertIsNone(c.special_status)
        self.assertEqual(ignored, [])


if __name__ == "__main__":
    unittest.main()
