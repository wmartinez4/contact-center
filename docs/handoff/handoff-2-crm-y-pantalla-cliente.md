# Hand-off 2: real CRM connection and customer-info screen

Paste this as the first message of a new chat. Project: `/Users/willianmartinez/contact-center`. Read `AGENTS.md` first. Chat in Spanish (neutral Latin American, "tu"); code and docs in English.
Context: demo for MEI/Automax on Wed Nov 11, 2026 (contact center, EN/ES, collections). It is Nov 10: scope must fit a one-evening build.

## Goals from Willian
1. **Connect to a real CRM** instead of the simulated lookup.
2. **Show on an agent screen the customer information and the call traceability** ("who is calling", account data, days past due, special status, call ID, transfer/callback history).
3. **Remove ads/messages from the agents' and supervisor's start window** in Connect (the CCP/agent workspace home shows promotional messages).
4. **iDMS check**: verify what MEI's iDMS exposes (API? DB? file export?) and how our lookup would call it. MEI's system is not accessible yet: prepare the integration contract and the question list, keep the simulated iDMS as the demo source.

## Current state
- Instance `cs-connect-demo` (id c2f9ca2b-eb05-4a82-9809-1d7c914333ba), account 383799408374, profile `cs-admin` (check the account id before any call), prefix `demo`, region us-east-1.
- Lookup: Lambda `demo-lookup` (`poc/infra/mei-demo/lookup_handler.py`) reads `poc/data/personas.json` (simulated iDMS). Returns customerName, daysPastDue, specialStatus, balance, paymentDue, queueName, queueArn, announcePromptArn. Same data is used by the AI agent (`ai_dialog.py`, Lambda `demo-ai-dialog`).
- Flow `demo-inbound` sets contact attributes (master_call_id, language, department, customer data), which show in Contact details and could feed an agent screen. `chain.py` rebuilds all legs of a call by master_call_id.
- Customer-facing numbers: AI line +1 775 249 1758; inbound demo number in the instance.

## Options to evaluate (recommend one, short)
- A. Real CRM with a free/dev tier (e.g. Salesforce Developer Edition, HubSpot free, Zoho) fed with the invented personas; Lambda looks up by phone number/account code; Connect shows the record via **Amazon Connect Agent Workspace** with a CRM screen-pop (iframe/third-party app) or via a custom page with the contact attributes.
- B. Keep the simulated iDMS behind an API and build a small agent-facing web page (customer card + call trace timeline) opened as a third-party app in the agent workspace.
- Evaluate cost, time to build, and what is credible for MEI. Real customer data must NOT be used; invented personas only.
- For the screen: also consider Connect's own **Customer Profiles** / agent app views if quicker.

## Rules (do not break)
- Never delete anything in AWS without explicit confirmation; never work around a blocked action (a security-profile update was blocked this session: ask Willian).
- Credentials only in `.env` / `poc/.credentials.local`, never printed or pasted. Do not copy other projects' .env files.
- No "mei" or "claude" in resource/user names; neutral names with prefix `demo`. Do not mention other projects in AGENTS.md.
- New third-party accounts or signups for a CRM: ask Willian first (he creates accounts and keys himself).
- Python needs boto3: no system boto3, create a venv.
- Keep Twilio test calls short. Short summaries, simple step-by-step instructions.

## Known problem to be aware of
Supervisor does not see recordings/transcripts in Contact details because `CallCenterManager` lacks the new permissions (see Hand-off 1); do not change security profiles without Willian's approval, and remember `update-security-profile` replaces the whole permission list.
