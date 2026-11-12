# Handoff 4: progress as of 2026-11-10 ~22:15 (America/Bogota)

Continues `handoff-4-pruebas-reportes-y-pendientes.md`.

## Done
- Disposition verified end to end (agent pressed Submit; `disposition`, `followUp`, `resolved`, `wrapUpSummary`, `wrapUpNotes` on the voice contact). Fix in `poc/infra/mei-demo/setup_wrapup.py`: Submit condition on the ShowView block, fields at `$.Views.ViewResultData.<Name>` (custom view), dropdowns read with `.0`, `DefaultValue: [""]`. Documented in the mei-demo README.
- Permissions ruled out for the empty "Automated interaction" tab and Insights panel: `CallCenterManager` already has the unredacted automated-interaction and post-contact-summary permissions.
- Instance attributes `AUTOMATED_INTERACTION_LOG` and `ENABLE_BOT_ANALYTICS_AND_TRANSCRIPTS` set to `true` (were `false`). Since then an `AUTOMATED_INTERACTION_LOG/` folder is written to S3, but so far only for the agent-simulator leg, not for the AI flow contact.
- AWS side checked: no stuck contacts, agents Available, demo Lambdas 0 errors, no demo resources running that cost money. Month-to-date account cost ~$42, mostly other projects (Bedrock, Lightsail, RDS `cs-prospecting-flow`). Connect/Lex/Polly cost not visible yet (billing lag); look again tomorrow.

## Update 22:30
- Mac rebooted: built-in pane now renders Connect's reports. Saved real-time reports `CS - Real-time - Queues` and `CS - Real-time - Agents` (published to the organization at 22:40, Read-only left off; new reports need Actions > Share > Publish).
- `AUTOMATED_INTERACTION_LOG/` files take ~30 min to appear. "Automated interaction" tab now shows the flow tree for `325faf7f`, but no bot utterances.
- Lex alias `live` (bot S2MLDJBHYT, v4): enabled text conversation logs to CloudWatch `/aws/lex/demo-assistant` (14-day retention, prefix `conv-`), alias config otherwise unchanged. Verified on call `e2d9bb6a-ebfb-4ee8-8b8a-5635e61c06b2`: the full dialog is in the log group. Open: does the Connect "Automated interaction" tab show the utterances for that call (check after ~23:05)?
- Historical reports (by queue, by agent, transfers): create after the clean batch, with the batch start time as the range.

## Open
1. Check contact `e92b13f0-8dba-42bc-b2cf-4d6540afbebc` (AI call placed ~22:08): is there an `AUTOMATED_INTERACTION_LOG/` file for it in `s3://amazon-connect-demo-recordings-383799408374/demo/CallRecordings/`, and does the "Automated interaction" tab show a transcript? Previous AI call `325faf7f-194f-4096-ab82-7a3ddd9494a0` had none (it started right after the settings changed). No background polling: the user asks for the check.
2. Reports (1-5: real-time queues/agents, historical by queue/agent, transfers). The built-in browser pane renders "Dashboards and reports" and "Real-time metrics" blank (`<lily-real-time-metrics>` stays empty). Plan: after the user reboots the Mac, retry in the pane; otherwise use Claude in Chrome (a Chrome tab is open at the AWS sign-in; the user logs in as demo.supervisor, never type passwords).
3. Reports 6-7 (AI agent resolved vs handed over; conversational analytics) after the above.
4. Clean test batch: user will press Submit on dispositions during it; note the exact start time and filter the reports from it. Do not delete historical data (Connect contact records cannot be deleted; S3 recordings are not deleted).
5. Re-run the `full` suite, leave agents on softphone, update runbook sections (reports, disposition, categories). Do not touch the decks.

## Still pending cleanup (ask first)
`demo-profiles` Customer Profiles domain, "CS - Sandbox - Copy of Collections Routing", "CS - Test - Agent Simulator (EN/ES)" flows, old instance `olive-connect-demo-530c` (account 200845568816, claimed numbers).

## Local machine
Mac was at 15 days uptime, swap full, 66 Chrome processes; the user is rebooting it to rule it out as the cause of slow consoles.
