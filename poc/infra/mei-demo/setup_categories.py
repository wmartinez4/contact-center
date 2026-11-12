#!/usr/bin/env python3
"""Contact Lens categories for collections: post-call rules that tag a call when the transcript contains one of
the phrases (English and Spanish). The rule name is the category (letters, digits, _ . - only). They complement the agent's disposition:
the agent records the official outcome, the categories flag what was actually said. Re-runnable.

    AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> python3 setup_categories.py
"""
import json
import os

import boto3

c = boto3.client("connect")
IID = os.environ["CONNECT_INSTANCE_ID"]
ACCOUNT = boto3.client("sts").get_caller_identity()["Account"]
INSTANCE_ARN = f"arn:aws:connect:{c.meta.region_name}:{ACCOUNT}:instance/{IID}"

# name -> (who says it, phrases matched exactly in the transcript)
CATEGORIES = {
    "Promise_to_pay": ("CUSTOMER", ["I will pay", "I'll pay", "I can pay", "I can make a payment", "voy a pagar", "puedo pagar", "pagaré", "hoy puedo pagar"]),
    "Payment_arrangement": ("CUSTOMER", ["payment arrangement", "pay half", "half now", "the rest at the end of the month", "acuerdo de pago",
                                     "una parte hoy", "el resto después", "unos días más"]),
    "Financial_hardship": ("CUSTOMER", ["unexpected expenses", "unexpected expense", "car repair", "money is tight", "lost my job",
                                        "gastos inesperados", "me redujeron las horas", "perdí mi trabajo", "no alcancé a pagar"]),
    "Dispute": ("CUSTOMER", ["I don't owe", "I do not owe", "not my debt", "I already paid", "no reconozco", "no debo", "ya pagué"]),
    "Callback_requested": ("CUSTOMER", ["call me back", "call me later", "llámenme después", "me pueden llamar", "llámeme más tarde"]),
    "Collection_notice_given": ("AGENT", ["attempt to collect a debt", "gestión de cobro"]),
}


def function(role, phrases):
    return json.dumps({"Version": "2022-11-25", "RuleFunction": {"Operator": "AND", "Operands": [{
        "Operator": "CONTAINS_ANY", "Operands": phrases, "ComparisonValue": "$.ContactLens.PostCall.ExactMatch.Transcript", "Negate": False,
        "FilterClause": {"LogicOperator": "AND", "Filters": [{"Type": "ParticipantRole", "Data": role}]}}]}})


def main():
    existing = {}
    tok = None
    while True:
        r = c.list_rules(InstanceId=IID, EventSourceName="OnPostCallAnalysisAvailable", **({"NextToken": tok} if tok else {}))
        existing.update({x["Name"]: x["RuleId"] for x in r["RuleSummaryList"]})
        tok = r.get("NextToken")
        if not tok:
            break
    actions = [{"ActionType": "ASSIGN_CONTACT_CATEGORY", "AssignContactCategoryAction": {}}]
    for name, (role, phrases) in CATEGORIES.items():
        if name in existing:
            c.update_rule(InstanceId=IID, RuleId=existing[name], Name=name, Function=function(role, phrases),
                          Actions=actions, PublishStatus="PUBLISHED")
            print("rule updated:", name)
        else:
            c.create_rule(InstanceId=IID, Name=name, TriggerEventSource={"EventSourceName": "OnPostCallAnalysisAvailable"},
                          Function=function(role, phrases), Actions=actions, PublishStatus="PUBLISHED")
            print("rule created:", name)


if __name__ == "__main__":
    main()
