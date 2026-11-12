# Hand-off 4: continue the demo build (tests, reports, open items)

Paste this as the first message of a new chat. Project: `/Users/willianmartinez/contact-center`. Read `AGENTS.md` first, then `poc/infra/mei-demo/README.md` (its bottom sections describe everything built on Nov 10). Chat in Spanish (neutral Latin American, "tú"); code and docs in English.
Demo for MEI/Automax on Wed Nov 11, 2026. Hand-off 3 (decks and pricing) runs in another chat: do not edit the decks or `docs/proposal/*.pptx` here.

## Environment
- AWS account 383799408374, profile `cs-admin`, us-east-1 (check the account id before any change). Instance `cs-connect-demo` (c2f9ca2b-eb05-4a82-9809-1d7c914333ba).
- Scripts in `poc/infra/mei-demo/`, Python venv `poc/.venv` (boto3, pillow). Run them with `AWS_PROFILE=cs-admin AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=c2f9ca2b-eb05-4a82-9809-1d7c914333ba EXPECTED_ACCOUNT=383799408374 DEMO_PREFIX=demo`.
- Users and passwords: `poc/.credentials.local` (never print). Old sandbox instance (do not use): `poc/.credentials.old.local`.
- Numbers: main +1 775 245 6050 (flow "CS - Inbound - Collections Routing"), AI +1 775 249 1758 ("CS - Inbound - AI Agent", Lex bot `demo-assistant`, Nova 2 Sonic), sandbox +1 775 249 1708 ("CS - Sandbox - Simple Flow"; also the caller ID of `demo.caller2` = rehearsal customer account 10).
- Display names start with "CS - " (`names.py`); scripts also find older names. Agents demo.agent1 (front line) and demo.agent2 (specialist), auto-accept, 60 s after-call work.

## What exists (verified unless noted)
- Routing by account (menu) or by caller phone (known customers skip menus); EN/ES; special status before days past due.
- Customer Profiles domain `amazon-connect-cs-connect-demo` (10 customers from `poc/data/customers.csv`, `setup_profiles.py`); profile pops by phone for known numbers.
- Agent workspace guides: "Customer on the line", "Transferred by the AI assistant", "Transferred by another agent" (`setup_guide_flow.py`, `setup_transfer_flow.py`).
- AI agent: language switch mid-call, handover with context, fallback to a person.
- Contact Lens: transcript, sentiment, post-call summary EN+ES; categories `setup_categories.py` (Promise_to_pay, Payment_arrangement, Financial_hardship, Dispute, Callback_requested, Collection_notice_given) — verified on test calls.
- Disposition: view "CS - Collections Wrap-up" + flow "CS - Guide - Wrap-up" (`setup_wrapup.py`), shown at call end; writes `disposition`, `followUp`, `resolved`, `wrapUpSummary`, `wrapUpNotes` onto the call via `TargetContact: Related` — **NOT yet verified** (nobody pressed Save in the test).
- Workspaces with branding (`setup_workspaces.py`, logo `poc/assets/logo-white.png`).
- Unattended tests: `twilio_test_calls.py routing|ai|all|full|categories [case]` (Twilio creds in project `.env`, never print). `full`/`categories` use `agent_sim.py` (agents on desk phone = sandbox line speaking an agent script) and always run `agent_sim.stop()` at the end; if a run is killed, run `python3 agent_sim.py stop` yourself. Analysis lands in S3 `amazon-connect-demo-recordings-383799408374/Analysis/Voice/` ~5 min after a call.

## To do, in order
1. **Verify the AI-part analytics** just enabled (AnalyticsModes PostContact + AutomatedInteraction in the AI flow): place one AI call (`twilio_test_calls.py full conv-ai`), then check the "Automated interaction" tab has a transcript and that summaries exist. If Connect fails the analysis, revert that change in `setup_ai_flow.py` (`lens()`).
2. **Verify disposition end to end** with Willian: one call to agent1, he picks a disposition and presses Save; confirm the attributes landed on the voice contact (`get_contact_attributes`). If empty, read the guide contact's flow log to find the real path of the form output (assumed `$.Views.ViewResultData.FormData.<Name>`) and fix `setup_wrapup.py`.
3. **Supervisor "Insights" panel** showed "No insights available" on a weak test call; check on a full call (e.g. contact f52d46d3-6c0e-490a-a9f9-6ed115358e91). If still empty, compare `CallCenterManager` permissions with Admin for Contact Lens / summary items and ask Willian before changing the profile.
4. **Default reports** (Willian logs in as demo.supervisor or demo.admin in the built-in browser; you click, he types passwords). Save and share: real-time queues; real-time agents; historical by queue (handled, abandoned, avg wait, AHT, transfers); historical by agent; transfers by queue/agent; AI agent (resolved vs handed over — if the standard report cannot split it, produce a small table via API); conversational analytics (sentiment, categories, dispositions). There is no API to save reports.
5. **Re-run the full suite** once more before the demo (`full` group), confirm all OK, and leave agents on softphone.
6. Update `docs/proposal/demo-runbook.md` (reports step, disposition step, categories) — coordinate: the other chat may also touch it; edit only those sections.

## Known gaps / cleanup (ask before deleting anything)
- Unused: Customer Profiles domain `demo-profiles` (instance no longer associated), flow "CS - Sandbox - Copy of Collections Routing", test flows "CS - Test - Agent Simulator (EN/ES)".
- Old sandbox instance `olive-connect-demo-530c` (account 200845568816) still has claimed numbers.
- Nova 2.5 Sonic: Lex accepts only Nova 2 Sonic (checked Nov 10).
- Queue callback for `demo.caller` paths and toll-free pricing not verified.

## Rules (do not break)
- Never delete anything in AWS without Willian's explicit confirmation; never work around a blocked action (security profile changes need his approval; `update-security-profile` replaces the whole list — read, add, write).
- Credentials only in `.env` / `poc/.credentials.local`; never printed.
- No "mei" or "claude" in resource or user names; do not mention other projects in AGENTS.md.
- Keep Twilio test calls short and sequential; agents must be Available.
- Not a git repo: no commits.
