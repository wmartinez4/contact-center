#!/usr/bin/env python3
"""Generates the outbound demo contact flow and writes infra/04-flow.yaml.

Run from anywhere:  python3 infra/flows/build_flow.py
The flow JSON is embedded in the CloudFormation template; ${...} tokens are resolved by Fn::Sub.
"""
import json
import os

NM = "NoMatchingError"
NC = "NoMatchingCondition"
TIMEOUT = "InputTimeLimitExceeded"
QUEUE_FULL = "QueueAtCapacity"


def err(target, *types):
    return [{"NextAction": target, "ErrorType": t} for t in types]


def action(identifier, type_, params, next_action=None, errors=None, conditions=None):
    transitions = {}
    if next_action is not None:
        transitions = {"NextAction": next_action, "Errors": errors or [], "Conditions": conditions or []}
    return {"Identifier": identifier, "Type": type_, "Parameters": params, "Transitions": transitions}


def equals(target, value):
    return {"NextAction": target, "Condition": {"Operator": "Equals", "Operands": [value]}}


def message(identifier, text, next_action):
    return action(identifier, "MessageParticipant", {"Text": text}, next_action, err("ErrorMsg", NM))


def write_outcome(identifier, disposition, next_action):
    return action(identifier, "InvokeLambdaFunction", {
        "LambdaFunctionARN": "${WriteOutcomeArn}",
        "InvocationTimeLimitSeconds": "8",
        "LambdaInvocationAttributes": {"customerId": "$.Attributes.customerId", "disposition": disposition},
        "ResponseValidation": {"ResponseType": "STRING_MAP"},
    }, next_action, err(next_action, NM))


STATE_ATTRS = ["step", "language", "retries", "mileageAttempts", "pendingMileage", "mileage"]

actions = [
    # 0. Per-block execution log in CloudWatch: the only way to see what the flow did on a call
    action("LogOn", "UpdateFlowLoggingBehavior", {"FlowLoggingBehavior": "Enabled"}, "AmdCheck", []),

    # 1. Voicemail detection (enabled on StartOutboundVoiceContact)
    action("AmdCheck", "CheckOutboundCallStatus", {}, "GetCustomer", err("GetCustomer", NM), [
        equals("VoicemailWrite", "VoicemailBeep"),
        equals("VoicemailWrite", "VoicemailNoBeep"),
        equals("GetCustomer", "CallAnswered"),
        equals("GetCustomer", "NotDetected"),
    ]),
    write_outcome("VoicemailWrite", "Voicemail", "Bye"),

    # 2. Who are we calling and what do we say
    action("GetCustomer", "InvokeLambdaFunction", {
        "LambdaFunctionARN": "${GetCustomerArn}",
        "InvocationTimeLimitSeconds": "8",
        "LambdaInvocationAttributes": {"customerId": "$.Attributes.customerId"},
        "ResponseValidation": {"ResponseType": "STRING_MAP"},
    }, "SetAttrs", err("ErrorMsg", NM)),
    action("SetAttrs", "UpdateContactAttributes", {"Attributes": {
        "firstName": "$.External.firstName",
        "language": "$.External.language",
        "step": "$.External.step",
        "retries": "$.External.retries",
        "mileageAttempts": "$.External.mileageAttempts",
        "pendingMileage": "$.External.pendingMileage",
        "mileage": "$.External.mileage",
        "pid": "$.External.pid",
        "customerSummary": "$.External.customerSummary",
        "promptMessage": "$.External.openingMessage",
    }}, "LangCheck", err("ErrorMsg", NM)),

    # 3. Voice + Lex locale follow the contact language
    action("LangCheck", "Compare", {"ComparisonValue": "$.Attributes.language"}, "VoiceEn",
           err("VoiceEn", NC), [equals("VoiceEs", "es")]),
    action("VoiceEn", "UpdateContactTextToSpeechVoice",
           {"TextToSpeechVoice": "Danielle", "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"},
           "LangEn", err("ErrorMsg", NM)),
    action("LangEn", "UpdateContactData", {"LanguageCode": "en-US"}, "Lex", err("ErrorMsg", NM)),
    action("VoiceEs", "UpdateContactTextToSpeechVoice",
           {"TextToSpeechVoice": "Lupe", "TextToSpeechEngine": "Generative", "TextToSpeechStyle": "None"},
           "LangEs", err("ErrorMsg", NM)),
    action("LangEs", "UpdateContactData", {"LanguageCode": "es-US"}, "Lex", err("ErrorMsg", NM)),

    # 4. The whole conversation happens inside one Lex block; the dialog Lambda runs the script
    action("Lex", "ConnectParticipantWithLexBot", {
        "Text": "$.Attributes.promptMessage",
        "LexV2Bot": {"AliasArn": "${LexAliasArn}"},
        "LexSessionAttributes": {
            "customerId": "$.Attributes.customerId",
            "step": "$.Attributes.step",
            "language": "$.Attributes.language",
            "retries": "$.Attributes.retries",
            "mileageAttempts": "$.Attributes.mileageAttempts",
            "pendingMileage": "$.Attributes.pendingMileage",
            "mileage": "$.Attributes.mileage",
        },
        "LexTimeoutSeconds": {"Text": "300"},
    }, "AfterLex", [
        {"NextAction": "AfterLex", "ErrorType": NC},       # any finished intent lands here
        {"NextAction": "NoResponseWrite", "ErrorType": TIMEOUT},
        {"NextAction": "ErrorMsg", "ErrorType": NM},
    ]),
    write_outcome("NoResponseWrite", "NoResponse", "Bye"),

    # 5. What did the script decide?
    action("AfterLex", "UpdateContactAttributes", {"Attributes": {
        "outcome": "$.Lex.SessionAttributes.outcome",
        "step": "$.Lex.SessionAttributes.step",
        "language": "$.Lex.SessionAttributes.language",
        "retries": "$.Lex.SessionAttributes.retries",
        "mileageAttempts": "$.Lex.SessionAttributes.mileageAttempts",
        "pendingMileage": "$.Lex.SessionAttributes.pendingMileage",
        "mileage": "$.Lex.SessionAttributes.mileage",
        "promptMessage": "$.Lex.SessionAttributes.resumeMessage",
    }}, "OutcomeCheck", err("ErrorMsg", NM)),
    action("OutcomeCheck", "Compare", {"ComparisonValue": "$.Attributes.outcome"}, "Bye", err("Bye", NC), [
        equals("LangCheck", "SwitchLanguage"),
        equals("QueueTarget", "TransferAgent"),
    ]),

    # 6. Transfer to a human, only if somebody is there to take it
    action("QueueTarget", "UpdateContactTargetQueue", {"QueueId": "${AgentQueueArn}"}, "StaffCheck", err("ErrorMsg", NM)),
    action("StaffCheck", "CheckMetricData", {"MetricType": "NumberOfAgentsAvailable"}, "NoAgentsCheck", [
        {"NextAction": "NoAgentsCheck", "ErrorType": NC},
        {"NextAction": "NoAgentsCheck", "ErrorType": NM},
    ], [{"NextAction": "Transfer", "Condition": {"Operator": "NumberGreaterThan", "Operands": ["0"]}}]),
    action("Transfer", "TransferContactToQueue", {}, "NoAgentsCheck", err("NoAgentsCheck", NM, QUEUE_FULL)),
    action("NoAgentsCheck", "Compare", {"ComparisonValue": "$.Attributes.language"}, "NoAgentsEn",
           err("NoAgentsEn", NC), [equals("NoAgentsEs", "es")]),
    message("NoAgentsEn", "Sorry, none of our team members is available right now. Please visit our website or call us back. Goodbye.", "NoAgentWrite"),
    message("NoAgentsEs", "Lo sentimos, ningún miembro de nuestro equipo está disponible en este momento. Visite nuestro sitio web o vuelva a llamarnos. Hasta luego.", "NoAgentWrite"),
    write_outcome("NoAgentWrite", "NoAgentAvailable", "Bye"),

    # 7. Endings
    message("ErrorMsg", "Sorry, we are having technical difficulties. Goodbye.", "Bye"),
    action("Bye", "DisconnectParticipant", {}, None),
]

flow = {"Version": "2019-10-30", "StartAction": "LogOn", "Actions": actions}
body = json.dumps(flow, indent=2)

here = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(here, "outbound-demo.flow.json")
open(json_path, "w").write(body + "\n")

indented = "\n".join(("          " + line) if line else line for line in body.splitlines())
template = f"""AWSTemplateFormatVersion: '2010-09-09'
Description: olive.business.connect demo - outbound contact flow (generated by infra/flows/build_flow.py, do not edit by hand)

Parameters:
  InstanceArn:
    Type: String
  LexAliasArn:
    Type: String
  GetCustomerArn:
    Type: String
  WriteOutcomeArn:
    Type: String
  AgentQueueArn:
    Type: String

Resources:
  LexAssociation:
    Type: AWS::Connect::IntegrationAssociation
    Properties:
      InstanceId: !Ref InstanceArn
      IntegrationType: LEX_BOT
      IntegrationArn: !Ref LexAliasArn

  GetCustomerAssociation:
    Type: AWS::Connect::IntegrationAssociation
    Properties:
      InstanceId: !Ref InstanceArn
      IntegrationType: LAMBDA_FUNCTION
      IntegrationArn: !Ref GetCustomerArn

  WriteOutcomeAssociation:
    Type: AWS::Connect::IntegrationAssociation
    Properties:
      InstanceId: !Ref InstanceArn
      IntegrationType: LAMBDA_FUNCTION
      IntegrationArn: !Ref WriteOutcomeArn

  OutboundFlow:
    Type: AWS::Connect::ContactFlow
    DependsOn: [LexAssociation]
    Properties:
      InstanceArn: !Ref InstanceArn
      Name: OutboundDemoFlow
      Type: CONTACT_FLOW
      Description: Automated renewal / payment outreach call
      Content: !Sub |
{indented}

Outputs:
  ContactFlowId:
    Value: !Select [3, !Split ['/', !GetAtt OutboundFlow.ContactFlowArn]]
"""
open(os.path.join(here, "..", "04-flow.yaml"), "w").write(template)
print("wrote", json_path, "and 04-flow.yaml;", len(actions), "actions")
