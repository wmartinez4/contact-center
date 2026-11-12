#!/bin/bash
# Publishes the Lambdas, uploads the zip and updates the backend stack with the new code key.
set -euo pipefail
cd "$(dirname "$0")/.."
export AWS_PROFILE=connect-demo AWS_REGION=us-east-1 AWS_PAGER=""
BUCKET=connect-demo-artifacts-200845568816
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
if [ "$ACCOUNT" != "200845568816" ]; then echo "Refusing deployment outside the demo sandbox" >&2; exit 1; fi
# Preserve voice-comparison and presentation audio.
rm -rf build/publish
mkdir -p build
rm -f build/lambdas.zip
dotnet publish src/Olive.Business.Connect.Lambdas/Olive.Business.Connect.Lambdas.csproj -c Release -r linux-arm64 --self-contained false -o build/publish -v q
(cd build/publish && zip -qr ../lambdas.zip .)
KEY="lambdas/lambdas-$(date +%Y%m%d%H%M%S).zip"
aws s3 cp build/lambdas.zip "s3://$BUCKET/$KEY" --only-show-errors
umask 077
PARAMS_FILE=$(mktemp)
trap 'rm -f "$PARAMS_FILE"' EXIT
python3 infra/backend_parameters.py "$KEY" > "$PARAMS_FILE"
aws cloudformation update-stack --stack-name connect-demo-02-backend --template-body file://infra/02-backend.yaml --capabilities CAPABILITY_IAM --parameters "file://$PARAMS_FILE" --output text --query StackId
aws cloudformation wait stack-update-complete --stack-name connect-demo-02-backend
echo "deployed $KEY"
