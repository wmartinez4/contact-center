#!/usr/bin/env python3
"""Supervisor app "Call with AI" (poc/ai-call-launcher): Lambda with a function URL, registered as a third-party
app of the Connect instance and granted only to the CallCenterManager (supervisor) and Admin security profiles.

Re-runnable.

    AWS_PROFILE=cs-admin python3 poc/infra/ai-call-launcher/setup.py
"""
import io
import json
import os
import time
import zipfile

import boto3

REGION, ACCOUNT = "us-east-1", "383799408374"
IID = "c2f9ca2b-eb05-4a82-9809-1d7c914333ba"
INSTANCE_ARN = f"arn:aws:connect:{REGION}:{ACCOUNT}:instance/{IID}"
DOMAIN = "amazon-connect-cs-connect-demo"
NAME = "ai-call-launcher"
APP_NAME = "Call with AI"
NAMESPACE = "ai-call-launcher"
FLOW_NAME = "CS - Inbound - Sofia AI"
CALLER_ID = "+17752550671"
# Account 10 (sandbox line, rings demo.caller2), account 2 (caller3's line, rings demo.caller3), both after
# customer_line.py ring, and the real phone of account 9 (Mauricio Ordonez), who takes part in the demo.
TEST_DESTINATIONS = ["+17752491708", "+17752585298", "+16787079207"]
SECURITY_PROFILES = ("CallCenterManager", "Admin")
CODE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ai-call-launcher"))

s = boto3.Session(region_name=REGION)
assert s.client("sts").get_caller_identity()["Account"] == ACCOUNT
iam, lam, connect, apps, kms = (s.client(n) for n in ("iam", "lambda", "connect", "appintegrations", "kms"))


def log(m):
    print(m, flush=True)


def ensure_role():
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    try:
        arn = iam.create_role(RoleName=f"{NAME}-role", AssumeRolePolicyDocument=json.dumps(trust), Tags=[{"Key": "project", "Value": NAME}])["Role"]["Arn"]
        time.sleep(10)
    except iam.exceptions.EntityAlreadyExistsException:
        arn = iam.get_role(RoleName=f"{NAME}-role")["Role"]["Arn"]
    iam.attach_role_policy(RoleName=f"{NAME}-role", PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    key_arn = s.client("customer-profiles").get_domain(DomainName=DOMAIN)["DefaultEncryptionKey"]
    iam.put_role_policy(RoleName=f"{NAME}-role", PolicyName="access", PolicyDocument=json.dumps({"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["connect:StartOutboundVoiceContact", "connect:DescribeContact", "connect:GetContactAttributes",
                                       "connect:DescribeUser", "connect:GetCurrentUserData"],
         "Resource": [INSTANCE_ARN, f"{INSTANCE_ARN}/*"]},
        {"Effect": "Allow", "Action": ["profile:SearchProfiles"], "Resource": f"arn:aws:profile:{REGION}:{ACCOUNT}:domains/{DOMAIN}*"},
        {"Effect": "Allow", "Action": ["kms:Decrypt", "kms:GenerateDataKey"], "Resource": key_arn,
         "Condition": {"StringEquals": {"kms:ViaService": f"profile.{REGION}.amazonaws.com"}}},
    ]}))
    return arn


def ensure_lambda(role_arn):
    flow_id = next(f["Id"] for f in connect.list_contact_flows(InstanceId=IID, ContactFlowTypes=["CONTACT_FLOW"])["ContactFlowSummaryList"]
                   if f["Name"] == FLOW_NAME)
    sp = {p["Name"]: p["Id"] for p in connect.list_security_profiles(InstanceId=IID)["SecurityProfileSummaryList"]}
    env = {"Variables": {"CONNECT_INSTANCE_ID": IID, "PROFILES_DOMAIN": DOMAIN, "FLOW_ID": flow_id, "CALLER_ID": CALLER_ID,
                         "ALLOWED_SECURITY_PROFILES": json.dumps([sp[n] for n in SECURITY_PROFILES]),
                         "TEST_DESTINATIONS": json.dumps(TEST_DESTINATIONS)}}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("app.py", "page.html"):
            z.write(os.path.join(CODE, f), f)
    try:
        lam.update_function_code(FunctionName=NAME, ZipFile=buf.getvalue())
        lam.get_waiter("function_updated_v2").wait(FunctionName=NAME)
        lam.update_function_configuration(FunctionName=NAME, Environment=env)
    except lam.exceptions.ResourceNotFoundException:
        for _ in range(6):
            try:
                lam.create_function(FunctionName=NAME, Runtime="python3.13", Role=role_arn, Handler="app.handler", Code={"ZipFile": buf.getvalue()},
                                    Timeout=20, MemorySize=256, Environment=env, Description="Supervisor app: outbound calls with the AI agent",
                                    Tags={"project": NAME})
                break
            except lam.exceptions.InvalidParameterValueException:
                time.sleep(5)
        log("lambda created")
    lam.get_waiter("function_active_v2").wait(FunctionName=NAME)
    lam.get_waiter("function_updated_v2").wait(FunctionName=NAME)
    try:
        url = lam.get_function_url_config(FunctionName=NAME)["FunctionUrl"]
    except lam.exceptions.ResourceNotFoundException:
        url = lam.create_function_url_config(FunctionName=NAME, AuthType="NONE")["FunctionUrl"]
        lam.add_permission(FunctionName=NAME, StatementId="url-public", Action="lambda:InvokeFunctionUrl", Principal="*", FunctionUrlAuthType="NONE")
        lam.add_permission(FunctionName=NAME, StatementId="url-invoke", Action="lambda:InvokeFunction", Principal="*", InvokedViaFunctionUrl=True)
    return url.rstrip("/")


def ensure_app(url):
    origin = url
    found = next((a for a in apps.list_applications()["Applications"] if a["Namespace"] == NAMESPACE), None)
    source = {"ExternalUrlConfig": {"AccessUrl": url + "/", "ApprovedOrigins": [origin]}}
    if found:
        apps.update_application(Arn=found["Arn"], Name=APP_NAME, ApplicationSourceConfig=source, Permissions=["User.Details.View"])
        arn = found["Arn"]
    else:
        arn = apps.create_application(Name=APP_NAME, Namespace=NAMESPACE, ApplicationSourceConfig=source,
                                      Description="Supervisors start outbound calls handled by the AI agent",
                                      Permissions=["User.Details.View"], Tags={"project": NAME})["Arn"]
        log("application created")
    associated = [a["IntegrationArn"] for a in connect.list_integration_associations(InstanceId=IID, IntegrationType="APPLICATION")["IntegrationAssociationSummaryList"]]
    if arn not in associated:
        connect.create_integration_association(InstanceId=IID, IntegrationType="APPLICATION", IntegrationArn=arn)
        log("application associated with the instance")
    return arn


def grant():
    """Adds the app to the supervisor and admin security profiles, keeping the applications they already have."""
    sp = {p["Name"]: p["Id"] for p in connect.list_security_profiles(InstanceId=IID)["SecurityProfileSummaryList"]}
    for name in SECURITY_PROFILES:
        current = connect.list_security_profile_applications(InstanceId=IID, SecurityProfileId=sp[name])["Applications"]
        if any(a["Namespace"] == NAMESPACE for a in current):
            continue
        keep = [{"Namespace": a["Namespace"], "ApplicationPermissions": a["ApplicationPermissions"]} for a in current]
        connect.update_security_profile(InstanceId=IID, SecurityProfileId=sp[name],
                                        Applications=keep + [{"Namespace": NAMESPACE, "ApplicationPermissions": ["ACCESS"]}])
        log(f"granted to {name}")


if __name__ == "__main__":
    url = ensure_lambda(ensure_role())
    ensure_app(url)
    grant()
    log(f"app URL: {url}/")
