# Demo preparation: ready-made calls, timing and checklist

Prepared on 2026-11-11 at about 09:00 (Colombia) for the 10:30 CT meeting. All data is invented. Complements `demo-runbook.md` (the step-by-step of the demo) and `guia-tanda-de-pruebas.md` (how the clean test batch was run).

- Instance `cs-connect-demo`, account `383799408374`. Supervisor links use `https://cs-connect-demo.my.connect.aws/contact-trace-records/details/<contact id>` (log in as `demo.supervisor`; agents cannot open Contact details, they get a 403).
- Clean batch started **08:21:45 Colombia (13:21:45 UTC)**; the time is also in `tanda-inicio.txt`.

## 1. When does each thing show up after a call ends

Measured in this instance on Nov 10 and 11:

| What | Appears after hang-up | Note |
|---|---|---|
| Contact record (Contact search, queue, agent, attributes, disposition) | seconds to 2 min | |
| Recording (audio) | 1 to 2 min | |
| Transcript, AI summary, categories | **about 5 to 12 min** | Calls with no conversation (0 to 3 turns) get no summary |
| Flow trace of the AI part ("Automated interaction") | about 30 min | Shows the flow and prompts, **not** the bot's dialogue |
| Bot dialogue | immediate | CloudWatch log group `/aws/lex/demo-assistant` |
| Historical reports | not measured yet | Create them after the batch; real-time reports are immediate |

**Consequence for the demo: a call placed live during the meeting will not have a transcript or summary while you show it.** Show one of the ready-made calls below. The recording and the contact record are available within a couple of minutes.

## 2. Calls ready to show (analysis already published)

Open each link as `demo.supervisor` → **Agent interaction** tab. **Verified 2026-11-11 09:40: `demo.admin` sees, for each call, the AI Summary, the Categories, the Key highlights (Issue/Outcome tags), the transcript and the audio. `demo.supervisor` sees only the audio, the transcript with the Key highlights and the user-defined attributes**: the summary, the categories and the Insights panel do not show with the supervisor profile (it lacks the Contact search permissions `ContactSearchWithCharacteristics` and `ContactSearchWithKeywords` that `Admin` has). Until the supervisor profile is fixed, **show the analysis from `demo.admin`** (Contact search → expand the row, or Contact details). Do **not** open "Automated interaction" or the Insights panel (see section 5). The "Categories shown" and "summary" notes in the table are what the analysis files contain; show them as text only after the admin check.

| Use it for (runbook part) | Contact | Language | Queue → agent | Duration | Categories shown | Notes |
|---|---|---|---|---|---|---|
| **3 Disposition** | `b54b788b-0f8d-42d2-9d45-eb9a0c485ed5` (08:17) | EN | 16-30 → agent1 | 84 s | Financial_hardship, Payment_arrangement, Collection_notice_given | **Has a saved disposition (Promise to pay)**, summary and transcript: the best single example. Attributes tab shows the five wrap-up values |
| **1 and 2 Known caller + transfer** | `a3750f20-b2b3-49db-b03e-a42cc1511581` (Nov 10, 23:00) | EN | 9-15 → agent1, transferred to agent2 (`387a6731-883e-44fc-9ac0-aa0838e8f4a2`) | 273 s | none | Mauricio Ordonez's own number, identified by phone, disposition Promise to pay. Summary says "No key points": it is a long call with the demo talk, not a collections script. Use it for the **transfer chain** (same `master_call_id` on both legs), not for the summary |
| **2 Transfer (second example)** | `64160643-8c9f-453f-b651-8cbe58f29d00` (Nov 10, 23:16) | EN | 16-30 → agent1, then agent2 (`eb72e75b-264e-426c-93af-c673c45567a2`) | 295 s | none | Disposition Promise to pay. Same remark about the summary |
| **4 AI agent (English)** | `4be1fd68-0b40-41d6-818a-c8b408f5e20a` (08:37) | EN | AI → 16-30 → agent1 | 103 s | Promise_to_pay, Payment_arrangement, Collection_notice_given | Only the agent's part is transcribed (4 turns). Attributes: `outcome=escalate`, `reason=Customer asked for a person`, `summary`. The bot dialogue is in CloudWatch |
| **4 AI agent (Spanish)** | `23629138-c5cf-4614-9ad3-e539d586eaf1` (08:52) | ES | AI → 1-8 → agent1 | 114 s | pending | Analysis should be there about 09:05 |
| **4 AI fallback if all fails** | `poc/samples/call-ai-130738af.mp3` | EN | | 64 s | | Play it and say it is a recording |
| **5 Flows, special status** | `730ee8fb-5860-4dca-a00e-10acd219c4ab` (08:27) | EN | **Redemptions** → **agent2** | 84 s | Financial_hardship, Payment_arrangement, Collection_notice_given | Account 5 has 12 days past due: without the rule it would go to 9-15. Second example: `bc12391a-bcec-4f94-8dd6-7a9ed979630d` (Early Payment Default, ES, agent2) |
| **6 Analysis, English** | `dfa0fa96-5566-40b2-8c7b-c33ccd111da1` (Nov 10, 20:29) | EN | 16-30 → agent1 | 96 s | Financial_hardship, Payment_arrangement | 12 turns; the summary tells the whole story |
| **6 Analysis, dispute** | `91648a9a-b673-4348-885f-d025d3318af8` (Nov 10, 20:35) | EN | 31+ → agent1 | 87 s | **Dispute**, Callback_requested, Collection_notice_given, Payment_arrangement | Customer says he already paid at the dealership |
| **6 Analysis, Spanish** | `f52d46d3-6c0e-490a-a9f9-6ed115358e91` (Nov 10, 20:38) | ES | 1-8 → agent1 | 101 s | Promise_to_pay, Financial_hardship, Payment_arrangement | Summary in Spanish. Second example: `ac46a539-b51d-4de5-88db-1b810b4f733b` (today 08:24) |
| **Fallback routing** | `0a892388-75d8-4d6c-a142-9e28cd367dfc` (08:35) | EN | General Assistance → agent1 | 84 s | Financial_hardship, Payment_arrangement | Account 7 does not exist: "We could not find the account..." |

Other contacts of today's batch (all published): `1d358161…` (f3, 16-30), `e3fbe79e…` (f4, 31+). The simulated agent never presses Submit, so the batch calls have **no disposition**; only `b54b788b…`, `a3750f20…` and `64160643…` do.

Contact search is at `https://cs-connect-demo.my.connect.aws/contact-search` (menu Analytics and optimization → Contact search). Expanding a row shows the audio and the transcript with Key highlights.

## 3. State to restore before the meeting

The scripted tests leave agent1 and agent2 **signed out (Offline)**. Before the demo:

- [ ] Browser 1: `demo.agent1` at `/agent/`, **Available**, microphone allowed (the call must ring there, not on a desk phone).
- [ ] Browser 2: `demo.agent2` at `/agent/`, **Available**.
- [ ] Browser 3: `demo.supervisor` (Contact search and reports). The reports and the calls above are viewed from here.
- [ ] Spare: `demo.caller` (menu, unknown number) and `demo.caller2` (known caller, Redemptions) only if no phone is available.
- [ ] Verify by API that agents are on the softphone and that the sandbox line points to "CS - Sandbox - Simple Flow" (read only):

```bash
cd /Users/willianmartinez/contact-center/poc/infra/mei-demo
export AWS_PROFILE=cs-admin AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=c2f9ca2b-eb05-4a82-9809-1d7c914333ba EXPECTED_ACCOUNT=383799408374 DEMO_PREFIX=demo
```

- [ ] Do not run `twilio_test_calls.py ... full` or `agent_sim.py start` after this point: they move the agents' phone to the sandbox line. If a run is interrupted: `../../.venv/bin/python agent_sim.py stop`.
- [ ] Only the softphone and the result windows are shared; the AWS console is closed. Close every other browser tab (the Connect console is heavy).

## 4. What each caller does

| Caller | Dials | Hears | Goes to |
|---|---|---|---|
| Mauricio Ordonez (EN) from his phone | +1 775 245 6050 | Recording notice, greeting by name, no menu | 9-15 → agent1. Profile opens by phone |
| Mauricio Cuevas (ES) from his phone | +1 775 245 6050 | **Menu** (his number is no longer registered). Press 2, then an account | Account 5 → Redemptions → agent2 |
| `demo.caller2` | +1 775 245 6050 | Greeting by name in Spanish, no menu | Redemptions → agent2 (rehearsal customer) |
| Anyone | **+1 775 249 1758** (AI line) | "This call may be recorded." and then the assistant, with no menu: it greets a registered number by name and asks the account code to anyone else when it needs it | "I want to talk to a person" → agent1 |

- Queue callback offer: with no agent available, the caller hears "Press 1 for a callback, 2 to stay in the queue" after **10 s** (it was 30 s).
- The customer profile opens by phone. For a menu caller the profile opens only on the main line (the number is linked to the chosen account by `demo-lookup`); the AI line does not do it, so there the agent sees the guide panel but no profile. Say it is a demo link: in production the number comes from iDMS.
- Wrap-up form: 60 s after the call, **Submit** (not Cancel); nothing is stored without it.

## 5. Do not open (known limits)

- **"Automated interaction" tab** and the **Insights panel**: they do not show the bot's dialogue and Insights stays empty.
- **Sentiment**: turned off on Nov 10. The slides and the Q&A script (`libreto-preguntas-y-respuestas.md`) may still mention it; do not promise it.
- The category `AutoEvaluateAgentInteractionOutcomeVoice` appears on most calls. It is AWS's own, not one of ours (ours: Promise_to_pay, Payment_arrangement, Financial_hardship, Dispute, Callback_requested, Collection_notice_given).
- No volumes or cost figure from MEI is validated: the "83,000 minutes last month" is second-hand and unconfirmed. Do not quote it, ask what it measures (conversation or whole call, inbound or outbound).

## 6. Reports

- Published (supervisor and admin see them): `CS - Real-time - Queues` and `CS - Real-time - Agents`.
- Still to create after the batch, with the batch start time as the range, and to publish (Actions → Share → Publish): historical by queue, by agent, transfers; AI agent resolved vs handed over; conversational analytics.
- Historical data may lag by minutes: if a report looks empty, show the real-time ones and the contact details.

## 7. Open items

- [ ] Check the Spanish AI call `23629138…` once its analysis is published (~09:05).
- [ ] Create and publish the historical reports.
- [ ] Sign agent1 and agent2 in again, set Available.
- [ ] Tell the other chat (decks, pricing, Q&A): sentiment is off; Cuevas is no longer a registered caller; the callback offer is at 10 s.
- [ ] Clean-up that needs confirmation (nothing deleted): the unused Customer Profiles domain `demo-profiles`, test flows ("CS - Test - Agent Simulator (EN/ES)", "CS - Sandbox - Copy of Collections Routing"), and the old instance `olive-connect-demo-530c` in account 200845568816.

## 8. If something fails during the demo

| Failure | Do |
|---|---|
| Nothing rings | Agent not Available or mic blocked: set Available, call again. Otherwise show a ready-made call |
| No customer panel | Open the contact in Contact search and show its attributes |
| No profile for a menu caller | Say the link is a demo shortcut; the guide panel already shows the account summary |
| A live call has no transcript yet | It takes 5 to 12 min: open one of the ready-made calls in section 2 |
| Console is slow | Close other tabs; wait for the page to load before clicking |
| Everything fails | Play the video and `poc/samples/call-ai-130738af.mp3` |
