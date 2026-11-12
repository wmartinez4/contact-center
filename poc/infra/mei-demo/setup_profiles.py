"""Enable Customer Profiles on the demo instance and load test customers from CSV.

Idempotent: reuses the KMS alias, domain and integration when they exist, and
updates profiles that already have the same account number.

Usage:
  AWS_PROFILE=<profile> AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=<id> \
  EXPECTED_ACCOUNT=<account> python setup_profiles.py [path/to/customers.csv]
"""
import csv
import json
import os
import sys

import boto3

# Connect's service-linked role only reaches domains named "amazon-connect-*" (the agent workspace shows
# "review your Amazon Connect Role Policy" otherwise).
DOMAIN = "amazon-connect-cs-connect-demo"
KEY_ALIAS = "alias/demo-profiles-key"
CSV_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "customers.csv")
STANDARD = {"accountNumber", "firstName", "lastName", "phone", "email", "birthDate", "gender",
            "address", "city", "state", "postalCode", "additionalInfo"}
ASSET_TYPE = "DemoVehicleLoan"  # shows in "Product purchase history"


session = boto3.Session()
account = session.client("sts").get_caller_identity()["Account"]
if account != os.environ["EXPECTED_ACCOUNT"]:
    sys.exit(f"Wrong account {account}")
region = session.region_name
instance_id = os.environ["CONNECT_INSTANCE_ID"]
instance_arn = f"arn:aws:connect:{region}:{account}:instance/{instance_id}"
kms = session.client("kms")
cp = session.client("customer-profiles")


def ensure_key():
    for a in kms.list_aliases()["Aliases"]:
        if a["AliasName"] == KEY_ALIAS:
            return kms.describe_key(KeyId=a["TargetKeyId"])["KeyMetadata"]["Arn"]
    arn = kms.create_key(Description="demo customer profiles encryption")["KeyMetadata"]["Arn"]
    kms.create_alias(AliasName=KEY_ALIAS, TargetKeyId=arn)
    print("created KMS key", KEY_ALIAS)
    return arn


def ensure_domain(key_arn):
    names = [d["DomainName"] for d in cp.list_domains()["Items"]]
    if DOMAIN not in names:
        cp.create_domain(DomainName=DOMAIN, DefaultExpirationDays=366, DefaultEncryptionKey=key_arn)
        print("created domain", DOMAIN)
    uris = [i["Uri"] for i in cp.list_integrations(DomainName=DOMAIN)["Items"]]
    if instance_arn not in uris:
        # Connect expects the object type to be called "CTR" (any other name shows "Customer Profiles hasn't been
        # set up" in the agent workspace). Built from the associate-only template: calls attach to existing
        # profiles and never create empty ones.
        cp.put_profile_object_type(DomainName=DOMAIN, ObjectTypeName="CTR", TemplateId="CTR-AutoAssociateOnly",
                                   Description="Connect contacts: associate to existing profiles only")
        cp.put_integration(DomainName=DOMAIN, Uri=instance_arn, ObjectTypeName="CTR")
        print("associated instance with", DOMAIN)


def load(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        fields = {
            "AccountNumber": r["accountNumber"],
            "FirstName": r["firstName"],
            "LastName": r["lastName"],
            "PhoneNumber": r["phone"],
            "EmailAddress": r["email"],
            "BirthDate": r["birthDate"],
            "GenderString": r["gender"],
            "Address": address(r),
            "MailingAddress": address(r),
            "BillingAddress": address(r),
            "AdditionalInformation": r["additionalInfo"],
            "Attributes": {k: v for k, v in r.items() if k not in STANDARD and v},
        }
        found = cp.search_profiles(DomainName=DOMAIN, KeyName="_account", Values=[r["accountNumber"]])["Items"]
        if found:
            cp.update_profile(DomainName=DOMAIN, ProfileId=found[0]["ProfileId"], **fields)
            print("updated", r["accountNumber"], r["firstName"], r["lastName"])
        else:
            cp.create_profile(DomainName=DOMAIN, **fields)
            print("created", r["accountNumber"], r["firstName"], r["lastName"])
        put_vehicle(r)


def address(r):
    return {"Address1": r["address"], "City": r["city"], "State": r["state"], "PostalCode": r["postalCode"], "Country": "US"}


def ensure_asset_type():
    f = lambda src, tgt: {"Source": f"_source.{src}", "Target": tgt, "ContentType": "STRING"}
    cp.put_profile_object_type(
        DomainName=DOMAIN, ObjectTypeName=ASSET_TYPE, Description="Simulated vehicle loan per customer",
        AllowProfileCreation=False, ExpirationDays=366,
        Fields={"accountNumber": f("AccountNumber", "_profile.AccountNumber"),
                "assetId": {"Source": "_source.AssetId", "Target": "_asset.Attributes.LoanId", "ContentType": "STRING"}, "assetName": f("AssetName", "_asset.AssetName"),
                "serialNumber": f("SerialNumber", "_asset.SerialNumber"), "purchaseDate": f("PurchaseDate", "_asset.PurchaseDate"),
                "price": f("Price", "_asset.Price"), "status": f("Status", "_asset.Status"),
                "firstName": f("FirstName", "_profile.FirstName"), "lastName": f("LastName", "_profile.LastName"),
                "firstNameLc": f("FirstNameLc", "_profile.Attributes.firstNameLc"),
                "lastNameLc": f("LastNameLc", "_profile.Attributes.lastNameLc")},
        Keys={"_account": [{"StandardIdentifiers": ["PROFILE", "LOOKUP_ONLY"], "FieldNames": ["accountNumber"]}],
              "loanId": [{"StandardIdentifiers": ["ASSET", "UNIQUE"], "FieldNames": ["assetId"]}],
              # Search keys so a profile is found by first or last name alone. Values are matched exactly and
              # case-sensitively, so the lowercase copy lets "willian" and "Willian" both work.
              "firstName": [{"FieldNames": ["firstName"]}, {"FieldNames": ["firstNameLc"]}],
              "lastName": [{"FieldNames": ["lastName"]}, {"FieldNames": ["lastNameLc"]}]})
    print("object type set:", ASSET_TYPE)


def put_vehicle(r):
    """One simulated financed vehicle per customer; invented VIN and price."""
    n = int(r["accountNumber"])
    status = {"Redemptions": "Repossessed - in redemption", "EPD": "Active loan - first payment returned"}.get(r["specialStatus"], "Active loan")
    obj = {"AccountNumber": r["accountNumber"], "FirstName": r["firstName"], "LastName": r["lastName"],
           "FirstNameLc": r["firstName"].lower(), "LastNameLc": r["lastName"].lower(),
           "AssetId": f"LOAN-{n:05d}", "AssetName": r["vehicle"],
           "SerialNumber": f"1DEMO{n:02d}VIN{n * 7919:07d}"[:17], "PurchaseDate": f"2025-{(n % 12) + 1:02d}-15",
           "Price": f"{14000 + n * 1350:.2f}", "Status": status}
    cp.put_profile_object(DomainName=DOMAIN, ObjectTypeName=ASSET_TYPE, Object=json.dumps(obj))


if __name__ == "__main__":
    ensure_domain(ensure_key())
    ensure_asset_type()
    load(sys.argv[1] if len(sys.argv) > 1 else CSV_DEFAULT)
