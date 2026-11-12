#!/usr/bin/env python3
"""Route B backend: API secret, DynamoDB tables, IAM role, the voice-agent-api Lambda and an HTTP API.

Re-runnable: creates what is missing and updates the Lambda code. Writes the API URL to
poc/elevenlabs-ruta-b/.state.json (git-ignored).

    AWS_PROFILE=cs-admin python3 poc/infra/elevenlabs-route-b/setup_api.py
"""
import io
import json
import os
import secrets
import time
import zipfile

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
EXPECTED_ACCOUNT = "383799408374"
INSTANCE_ID = "c2f9ca2b-eb05-4a82-9809-1d7c914333ba"
PROFILES_DOMAIN = "amazon-connect-cs-connect-demo"
NAME = "voice-agent-api"
CALLS_TABLE, AGREEMENTS_TABLE = "voice-calls", "payment-agreements"
SECRET_NAME = "voice-agent/api-secret"
WEBHOOK_SECRET_NAME = "voice-agent/elevenlabs-webhook-secret"  # written by setup_agent.py when it registers the webhook
POST_CALL_TOKEN_NAME = "voice-agent/post-call-token"            # header token of the post-call webhook only
BUCKET = f"voice-agent-artifacts-{EXPECTED_ACCOUNT}"
TAGS = {"project": "elevenlabs"}
# Route B test phones -> demo account. The caller3 softphone (number claimed by setup_caller3.py) acts as
# Maria Hernandez (account 2). Change the account to test another customer; caller2 stays Willian (Redemptions).

HERE = os.path.dirname(os.path.abspath(__file__))
API_SRC = os.path.abspath(os.path.join(HERE, "..", "..", "elevenlabs-ruta-b", "api"))
STATE = os.path.abspath(os.path.join(API_SRC, "..", ".state.json"))

session = boto3.Session(region_name=REGION)
account = session.client("sts").get_caller_identity()["Account"]
assert account == EXPECTED_ACCOUNT, f"wrong account {account}"
ddb, iam, lam, sm, apigw, connect = (session.client(n) for n in ("dynamodb", "iam", "lambda", "secretsmanager", "apigatewayv2", "connect"))


def ensure_post_call_token():
    try:
        sm.describe_secret(SecretId=POST_CALL_TOKEN_NAME)
    except sm.exceptions.ResourceNotFoundException:
        sm.create_secret(Name=POST_CALL_TOKEN_NAME, SecretString=secrets.token_urlsafe(32),
                         Description="Header token ElevenLabs sends with the post-call webhook",
                         Tags=[{"Key": k, "Value": v} for k, v in TAGS.items()])
        print("post-call token created")


def ensure_secret():
    try:
        return sm.describe_secret(SecretId=SECRET_NAME)["ARN"]
    except sm.exceptions.ResourceNotFoundException:
        arn = sm.create_secret(Name=SECRET_NAME, SecretString=secrets.token_urlsafe(32),
                               Description="Shared secret ElevenLabs sends to the voice agent API",
                               Tags=[{"Key": k, "Value": v} for k, v in TAGS.items()])["ARN"]
        print("secret created")
        return arn


def ensure_tables():
    tags = [{"Key": k, "Value": v} for k, v in TAGS.items()]
    existing = ddb.list_tables()["TableNames"]
    if CALLS_TABLE not in existing:
        ddb.create_table(TableName=CALLS_TABLE, BillingMode="PAY_PER_REQUEST", Tags=tags,
                         AttributeDefinitions=[{"AttributeName": "contactId", "AttributeType": "S"},
                                               {"AttributeName": "phone", "AttributeType": "S"},
                                               {"AttributeName": "createdAt", "AttributeType": "N"}],
                         KeySchema=[{"AttributeName": "contactId", "KeyType": "HASH"}],
                         GlobalSecondaryIndexes=[{"IndexName": "phone-createdAt", "Projection": {"ProjectionType": "ALL"},
                                                  "KeySchema": [{"AttributeName": "phone", "KeyType": "HASH"},
                                                                {"AttributeName": "createdAt", "KeyType": "RANGE"}]}])
        print("table created:", CALLS_TABLE)
    if AGREEMENTS_TABLE not in existing:
        ddb.create_table(TableName=AGREEMENTS_TABLE, BillingMode="PAY_PER_REQUEST", Tags=tags,
                         AttributeDefinitions=[{"AttributeName": "agreementId", "AttributeType": "S"}],
                         KeySchema=[{"AttributeName": "agreementId", "KeyType": "HASH"}])
        print("table created:", AGREEMENTS_TABLE)
    for t in (CALLS_TABLE, AGREEMENTS_TABLE):
        ddb.get_waiter("table_exists").wait(TableName=t)


def profiles_key_arn():
    return session.client("customer-profiles").get_domain(DomainName=PROFILES_DOMAIN)["DefaultEncryptionKey"]


def ensure_role(secret_arn):
    role = f"{NAME}-role"
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    try:
        arn = iam.create_role(RoleName=role, AssumeRolePolicyDocument=json.dumps(trust),
                              Tags=[{"Key": k, "Value": v} for k, v in TAGS.items()])["Role"]["Arn"]
        created = True
    except iam.exceptions.EntityAlreadyExistsException:
        arn, created = iam.get_role(RoleName=role)["Role"]["Arn"], False
    iam.attach_role_policy(RoleName=role, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    table_arn = lambda t: f"arn:aws:dynamodb:{REGION}:{account}:table/{t}"
    policy = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query"],
         "Resource": [table_arn(CALLS_TABLE), f"{table_arn(CALLS_TABLE)}/index/*", table_arn(AGREEMENTS_TABLE)]},
        {"Effect": "Allow", "Action": ["profile:SearchProfiles", "profile:UpdateProfile"],
         "Resource": f"arn:aws:profile:{REGION}:{account}:domains/{PROFILES_DOMAIN}"},
        {"Effect": "Allow", "Action": ["connect:UpdateContactAttributes"],
         "Resource": f"arn:aws:connect:{REGION}:{account}:instance/{INSTANCE_ID}/contact/*"},
        {"Effect": "Allow", "Action": ["connect:ListQueues"],
         "Resource": [f"arn:aws:connect:{REGION}:{account}:instance/{INSTANCE_ID}",
                      f"arn:aws:connect:{REGION}:{account}:instance/{INSTANCE_ID}/queue/*"]},
        {"Effect": "Allow", "Action": ["secretsmanager:GetSecretValue"],
         "Resource": [secret_arn, f"arn:aws:secretsmanager:{REGION}:{account}:secret:{WEBHOOK_SECRET_NAME}-*",
                      f"arn:aws:secretsmanager:{REGION}:{account}:secret:{POST_CALL_TOKEN_NAME}-*"]},
        {"Effect": "Allow", "Action": ["s3:PutObject"], "Resource": f"arn:aws:s3:::{BUCKET}/*"},
        # The profiles domain is encrypted with the demo's own KMS key; only usable through Customer Profiles.
        {"Effect": "Allow", "Action": ["kms:Decrypt", "kms:GenerateDataKey"], "Resource": profiles_key_arn(),
         "Condition": {"StringEquals": {"kms:ViaService": f"profile.{REGION}.amazonaws.com"}}}]}
    iam.put_role_policy(RoleName=role, PolicyName="voice-agent-api", PolicyDocument=json.dumps(policy))
    if created:
        time.sleep(12)  # IAM propagation before Lambda can assume the role
    return arn


def code_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(API_SRC)):
            if f.endswith(".py"):
                z.write(os.path.join(API_SRC, f), f)
    return buf.getvalue()


def ensure_lambda(role_arn, secret_arn):
    env = {"Variables": {"PROFILES_DOMAIN": PROFILES_DOMAIN, "CONNECT_INSTANCE_ID": INSTANCE_ID,
                         "CALLS_TABLE": CALLS_TABLE, "AGREEMENTS_TABLE": AGREEMENTS_TABLE, "API_SECRET_ARN": secret_arn,
                         "ARTIFACTS_BUCKET": BUCKET,
                         "WEBHOOK_SECRET_ARN": WEBHOOK_SECRET_NAME, "POST_CALL_TOKEN_SECRET": POST_CALL_TOKEN_NAME}}
    try:
        lam.get_function(FunctionName=NAME)
        lam.update_function_code(FunctionName=NAME, ZipFile=code_zip())
        lam.get_waiter("function_updated_v2").wait(FunctionName=NAME)
        lam.update_function_configuration(FunctionName=NAME, Environment=env, Timeout=10, MemorySize=256)
        print("lambda updated")
    except lam.exceptions.ResourceNotFoundException:
        lam.create_function(FunctionName=NAME, Runtime="python3.13", Role=role_arn, Handler="handler.handler",
                            Code={"ZipFile": code_zip()}, Timeout=10, MemorySize=256, Environment=env, Tags=TAGS,
                            Description="Voice agent API for the ElevenLabs collections demo")
        print("lambda created")
    lam.get_waiter("function_active_v2").wait(FunctionName=NAME)
    lam.get_waiter("function_updated_v2").wait(FunctionName=NAME)
    arn = lam.get_function(FunctionName=NAME)["Configuration"]["FunctionArn"]
    _permission(arn, "connect-invoke", "connect.amazonaws.com", f"arn:aws:connect:{REGION}:{account}:instance/{INSTANCE_ID}")
    existing = connect.list_lambda_functions(InstanceId=INSTANCE_ID)["LambdaFunctions"]
    if arn not in existing:
        connect.associate_lambda_function(InstanceId=INSTANCE_ID, FunctionArn=arn)
    return arn


def _permission(fn_arn, sid, principal, source_arn):
    try:
        lam.add_permission(FunctionName=fn_arn, StatementId=sid, Action="lambda:InvokeFunction",
                           Principal=principal, SourceArn=source_arn, SourceAccount=account)
    except lam.exceptions.ResourceConflictException:
        pass


def ensure_http_api(fn_arn):
    api = next((a for a in apigw.get_apis()["Items"] if a["Name"] == NAME), None)
    if not api:
        api = apigw.create_api(Name=NAME, ProtocolType="HTTP", Target=fn_arn, Tags=TAGS)
        print("http api created")
    _permission(fn_arn, "apigw-invoke", "apigateway.amazonaws.com", f"arn:aws:execute-api:{REGION}:{account}:{api['ApiId']}/*")
    return api["ApiEndpoint"]


def ensure_bucket():
    """Private bucket for transcripts and audio (S3 default encryption, public access blocked)."""
    s3 = session.client("s3")
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET)
        s3.put_public_access_block(Bucket=BUCKET, PublicAccessBlockConfiguration={
            "BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True})
        s3.put_bucket_tagging(Bucket=BUCKET, Tagging={"TagSet": [{"Key": k, "Value": v} for k, v in TAGS.items()]})
        print("bucket created:", BUCKET)


def main():
    secret_arn = ensure_secret()
    ensure_post_call_token()
    ensure_tables()
    ensure_bucket()
    role_arn = ensure_role(secret_arn)
    fn_arn = ensure_lambda(role_arn, secret_arn)
    url = ensure_http_api(fn_arn)
    state = {"apiUrl": url, "lambdaArn": fn_arn, "secretArn": secret_arn, "bucket": BUCKET}
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
