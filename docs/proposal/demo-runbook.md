# Demo runbook: MEI discovery meeting, Nov 11, 2026

Step by step for the agreed order: basic call and who is calling, transfer, disposition, AI agent, flows, reports, pricing. Slides: `MEI_Demo_Flows_Guide.pptx` (guide) and `MEI_Amazon_Connect_Options_DRAFT.pptx` (deck: slide 13 introduces the demo; slides 10 to 12 are marked internal-only: platform cost, suggested price, operations cost).

All data is invented. Say so first.

## 0. Setup (before 10:00 CT)

| Item | Value |
|---|---|
| AWS account | 383799408374, profile `cs-admin` (check the account ID first) |
| Instance | `cs-connect-demo` (c2f9ca2b-eb05-4a82-9809-1d7c914333ba) |
| Main number (routing flow `CS - Inbound - Collections Routing`) | +1 775 245 6050 |
| AI number (flow `CS - Inbound - AI Agent`, Nova 2 Sonic) | +1 775 249 1758 |
| Sandbox number (flow `CS - Sandbox - Simple Flow`, for live edits) | +1 775 249 1708 |
| Agent workspace (customer profile appears here) | https://cs-connect-demo.my.connect.aws/agent/ |
| Admin user for the flow designer | `demo.admin` |
| Passwords | `poc/.credentials.local` only. Never on screen |

Browsers (one user per browser or profile, headphones on):

| Window | User | State |
|---|---|---|
| Browser 1 | `demo.agent1` (front line: delinquency queues, fallback) in `/agent/` | Available, mic allowed |
| Browser 2 | `demo.agent2` (specialist: Redemptions, EPD) | Available, mic allowed |
| Browser 3 | `demo.supervisor` (manager, no Collections queue) | Available, softphone open |
| Spare | `demo.caller` (dials from a browser softphone) | Logged in, only if no phone is available |

Checklist:

- [ ] Account ID checked; all four users logged in.
- [ ] Each part run once by voice (all seven routing cases and the AI language switch and hand-over passed on scripted test calls on Nov 10), with `demo.agent1` Available.
- [x] Wrap-up form (part 3) saved end to end (verified Nov 10: disposition, follow-up, resolved, summary and notes land on the call). Press **Submit**, not Cancel.
- [ ] One finished call (with a transfer) in Contact search. Saved reports: `CS - Real-time - Queues` and `CS - Real-time - Agents` (done Nov 10); the historical ones (by queue, by agent, transfers) are created after the clean test batch, using its start time as the range.
- [ ] Video of the full run recorded as fallback; `poc/samples/call-ai-130738af.mp3` ready to play.
- [ ] Mauricio Ordonez's number tested (greeting by name, no menu, profile shown in `/agent/`) and Mauricio Cuevas calling through the menu (his number is not registered, so he hears the menu and can pick any account).
- [ ] One finished call with real conversation, in English and one in Spanish, shows recording, transcript, AI summary, categories and the Key highlights (Issue/Outcome) in Contact details **as `demo.admin`** (the supervisor profile shows only the transcript and the highlights; see `preparacion-demo.md` section 2) (supervisor). Calls with too little conversation get no summary. The "Automated interaction" tab shows the IVR/flow trace and the recording of the AI part, but not the bot's dialogue (under review on Nov 10), and the Insights panel is empty: do not open either of them in the demo.
- [ ] Only softphone and result windows shared. AWS console closed.

## 1. Basic call and who is calling (2 min)

1. **Who calls:** Mauricio Ordonez dials +1 775 245 6050 from his own phone, on speaker. His number is loaded as a customer with simulated account data (English, 10 days past due). Mauricio Cuevas's number is not registered on purpose (since Nov 10): he hears the menu and is used for part 5.
2. **What happens:** no menu. The system recognizes the number, plays the recording notice in his language, greets him by name with his days past due and routes him (Ordonez to 9-15).
3. **Show:** browser 1, `demo.agent1` in `/agent/` rings and auto-accepts; the customer profile opens (name, account, phone, days past due, status, balance, due date, vehicle).
4. **Say:** "In production the caller's number is looked up in iDMS. Unknown numbers get the language and account menu."
   - Fallback caller (unknown number): press 1, then 3. The profile of account 3 opens by account number.
5. **Keep the call open** for part 2.
6. **If it fails:** agent not Available → set Available and call again. No customer panel → open the contact in Contact search and show its attributes. Nothing rings → play the video.

## 2. Transfer, one call ID (3 min)

1. In browser 1, `demo.agent1` opens Quick connects and chooses `CS - Transfer to Redemptions`.
2. Browser 2, `demo.agent2` rings and answers. In a consult transfer, agent 1 presses Join and then hangs up.
3. Talk a few seconds, then hang up.
4. **Show:** Contact search (both legs) or run, from `poc/infra/mei-demo` in a venv with boto3:

   ```bash
   AWS_PROFILE=cs-admin CONNECT_INSTANCE_ID=c2f9ca2b-eb05-4a82-9809-1d7c914333ba DEMO_PREFIX=demo python3 chain.py --hours 1
   ```

   Point at the same `master_call_id` and department on both legs.
5. **Say:** "Every transfer is a new contact in Connect. We stamp one call ID on the first leg, so the whole conversation is one record for reporting."
6. **If it fails:** records take one to two minutes; show the finished call prepared earlier.

## 3. Disposition (1 min)

Verified end to end on Nov 10: after the agent presses **Submit**, five attributes are written on the call (`disposition`, `followUp`, `resolved`, `wrapUpSummary`, `wrapUpNotes`).

1. End the call from part 2 (or any call). The agent sees **Call wrap-up** (60 s of after-call work).
2. Show the disposition list (Promise to pay, Payment made, Payment arrangement set, Callback requested, Dispute, Hardship - referred, Refused to pay, Information only, Wrong party, Transferred), then follow-up, resolved, the editable summary, date and notes. Pick one, for example Promise to pay, follow-up Yes, resolved No, a date in the notes, and press **Submit** (Cancel saves nothing). Submit inside the 60 s.
3. **Say:** "Every call closes with an outcome chosen by the agent, stored with the call and reported. These codes are a starting point; we will configure MEI's own."
4. **Show (optional):** in Contact search → the call → Contact details → Attributes: the five values. Then the automatic categories (part 6): the agent records the official outcome, the analysis flags what was actually said (Promise_to_pay, Payment_arrangement, Financial_hardship, Dispute, Callback_requested, Collection_notice_given), so supervisors can spot mismatches.
5. **If it fails:** the form only appears during the 60 s of after-call work; if it is gone, show the guide's Part 3 slide and say it is configured. Without Submit nothing is stored.

## 4. AI agent (3 min)

1. **Who calls:** you, from your phone, on speaker: +1 775 249 1758.
2. There is no menu (since Nov 11): the call plays "This call may be recorded." and the assistant answers. A registered number (Mauricio Ordonez, `demo.caller2`) is greeted by name in its language and the account is already known ("Hi Mauricio, thanks for calling. How can I help you today?"); any other number hears "Thank you for calling. How can I help you today?" in English and is asked for the account code when it needs it. Wait for the assistant to finish before speaking (it cannot be interrupted). Say, waiting for each answer:
   - "What is my balance?"
   - "My account code is 3." (only for an unknown number)
   - "When is my payment due?"
   - "No, that is all."
3. Optional (both passed on scripted calls on Nov 10): say "Spanish please" and continue in Spanish (the account is kept); or say "I want to talk to a person" and show `demo.agent1` ringing with the panel "Transferred by the AI assistant" (reason, AI summary, account, language, queue).
4. **Say:** "This is Amazon Nova 2 Sonic, included in the Connect voice price. It only informs: no payments and no card data. When it cannot help, it hands the caller to the right queue with context, and it never just hangs up."
5. **If it fails:** play `poc/samples/call-ai-130738af.mp3` (Nov 10 test, 64 seconds) and say it is a recording.

## 5. Flows (2 min)

- **Designer:** log in as `demo.admin`, Routing → Flows. `CS - Inbound - Collections Routing` (full routing, laid out left to right) shows everything the demo does. To show an edit live, open `CS - Sandbox - Simple Flow`, change the welcome text or add a menu option, Publish, and call +1 775 249 1708. The demo flows are not touched.

1. Show the guide's Part 5 slide (routing diagram): special status before days past due.
2. **Who calls:** Mauricio Cuevas (not a registered number, so he gets the menu), to +1 775 245 6050. Press 2 for Spanish (or 1 for English), then 5 (Redemptions account, 12 days past due). Any other account works too: 3 (16-30), 4 (31+), 7 (not found → general assistance).
3. **Show:** browser 2, `demo.agent2` rings, not agent 1. Without the rule it would have gone to the 9-15 queue.
4. **Say:** "MEI's rule that special status wins is one place in the lookup. In production it reads iDMS."
5. **If it fails:** show the cases table (guide Part 5) and the video.

## 6. Reports (2 min)

1. Keep a call in progress (call the main number, case 3, agent 1 answers).
2. Browser 3, `demo.supervisor`: Analytics and optimization → Dashboards and reports → Real-time metrics → open the saved report `CS - Real-time - Agents` (or `CS - Real-time - Queues` for the 9 queues). Show agent 1 "On contact". Click the eye icon to listen in. Both reports are published (Actions → Share → Publish, Nov 10), so anyone with the report permissions (supervisor and admin profiles) sees them. A new report stays visible only to its owner until it is published the same way. Agents never see them (no report permissions).
3. Open the saved historical report (contacts handled, abandoned, average wait, transfers by queue and agent), with the time range set from the start of the clean test batch so the numbers are the planned calls only. [Created after the batch; if it does not exist yet, skip this step.]
4. **Say:** "The 27% transfer rate would be measured here, once we agree how a transfer is counted."
5. Open a finished call in Contact search → Contact details: recording, transcript and the AI Key highlights (Issue and Outcome tags), and under User defined attributes the disposition the agent saved. The AI summary and the categories (Promise_to_pay, Payment_arrangement, Financial_hardship, Dispute, Callback_requested, Collection_notice_given) are shown with **`demo.admin`** (verified 2026-11-11); `demo.supervisor` does not show them unless its security profile gets the Contact search permissions `ContactSearchWithCharacteristics` and `ContactSearchWithKeywords`. Use `demo.admin` for this step. Open the **Agent interaction** tab, not "Automated interaction" or the Insights panel. Analysis takes a few minutes after the call ends; use a call finished earlier. A call with too little conversation gets no summary.
6. **If it fails:** the eye icon only appears during a call; restart the call. Historical data takes minutes; use the saved report. The console is heavy: close other browser tabs and wait for pages to load before clicking.

## 7. Pricing (2 min)

**This is not a quote.** Slides 10 to 12 are internal-only (yellow): do not show them to MEI. Explain only how Connect is billed (no per-seat licence, per-second billing over the whole call, three levels chosen per account) using AWS list prices, and say the itemized estimate follows the data request. Give no suggested prices or fees.

1. Switch to the deck, slide 10 (platform cost on AWS), then slide 11 (suggested price, a draft: adjust or skip it if it is not agreed).
2. **Say:** "No per-seat licence; you pay per minute of the whole call. Three levels, chosen per AWS account: normal flow without AI about $77 per agent per month at 3 contact hours a day; plus analytics (transcript, sentiment, AI summary, categories) about $131; everything including the AI voice agent about $149. That is the AWS cost. Our suggested price is on the next slide. With your volumes we turn this into an estimate." Tables: `modelo-de-costos.md` sections 3b and 3c.
3. Close with the questions on slides 5, 6 and 14.

## After the demo

- Hang up every call and set agents Offline.
- Do not delete anything in AWS. Cleanup only after confirmation.
