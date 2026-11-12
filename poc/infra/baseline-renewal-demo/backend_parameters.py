#!/usr/bin/env python3
"""Write backend stack parameters to stdout; redirect to a private file, never a terminal."""
import json
import os
from pathlib import Path
import shlex
import sys

root = Path(__file__).resolve().parent.parent
values = {}
if (root / '.env').exists():
    for line in (root / '.env').read_text().splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, raw = line.split('=', 1)
        if key.strip() not in {'EMAIL_ROUTER_URL', 'EMAIL_ROUTER_API_KEY', 'DEMO_EMAIL_RECIPIENT', 'DEMO_RENEWAL_URL', 'DEMO_MAX_ATTEMPTS'}:
            continue
        value = shlex.split(raw, comments=True)
        values[key.strip()] = value[0] if value else ''

parameters = [{'ParameterKey': 'CodeKey', 'ParameterValue': sys.argv[1]}]
for name in ['DemoPhoneNumber', 'DemoPhoneWilliam', 'DemoPhoneHector', 'ConnectInstanceId',
             'ConnectInstanceArn', 'SourcePhoneNumber', 'ConnectFlowId', 'CodeBucket']:
    parameters.append({'ParameterKey': name, 'UsePreviousValue': True})
for name, key in [('EmailRouterUrl', 'EMAIL_ROUTER_URL'), ('EmailRouterApiKey', 'EMAIL_ROUTER_API_KEY'),
                  ('DemoEmailRecipient', 'DEMO_EMAIL_RECIPIENT'), ('DemoRenewalUrl', 'DEMO_RENEWAL_URL'),
                  ('DemoMaxAttempts', 'DEMO_MAX_ATTEMPTS')]:
    value = os.environ.get(key, values.get(key, '3' if key == 'DEMO_MAX_ATTEMPTS' else None))
    parameters.append({'ParameterKey': name, **({'ParameterValue': value} if value is not None else {'UsePreviousValue': True})})
print(json.dumps(parameters))
