# Hand-off 3: update the decks with today's changes (pricing first)

Paste this as the first message of a new chat. Project: `/Users/willianmartinez/contact-center`. Read `AGENTS.md` first. Chat in Spanish (neutral Latin American, "tú"); decks and notes in English.
Meeting: MEI/Automax discovery, Wed Nov 11, 2026 (contact center, EN/ES, collections). Today is Nov 10: keep scope to what can be finished tonight.

## Goal
Update both decks so they match what was built and verified on Nov 10, above all the pricing:
- `docs/proposal/MEI_Amazon_Connect_Options_DRAFT.pptx` (options deck; slide 10 = pricing, slide 11 = demo intro).
- `docs/proposal/MEI_Demo_Flows_Guide.pptx` (demo guide).
Use the pptx skill: edit, run its validation, render to PDF and look at every changed slide. Keep the existing look. Do not invent MEI facts; MEI volumes are still unknown, so prices stay illustrative with assumptions stated.

## Carried over from Hand-off 1 (`docs/handoff/handoff-1-presentacion-y-demo.md`)
An earlier chat already worked on these; `modelo-de-costos.md` section 7 records what was applied to slide 10. First check what the decks contain now, then finish only what is missing:
1. Remove recording and AI transcription/QA as separate sections — see the decision note below before touching anything about analytics.
2. A **Systems and payments** section: does MEI's contact center need payment integrations (pay by phone, payment links, PCI scope, IVR payments) and how it connects to iDMS, CRM and telephony. Questions plus what Connect offers; no invented MEI facts.
3. Remove every "out of scope" mention or slide; office telephony stays only as the question "of the 210 planned users, who takes or makes customer calls?".
4. Prices and costs: replace with the three tiers below.
5. Update the AI demo (Demo 5) as tested: Nova 2 Sonic, EN/ES, multi-turn, language switch mid-call, handover with context, number +1 775 249 1758.
Demo order (agreed): 1) basic call and who is calling, 2) transfer (one call ID, all legs), 3) disposition — built on Nov 10 (see below), 4) AI agent, 5) flows, 6) reports (historical + real-time supervisor), 7) pricing. The guide deck and `demo-runbook.md` must follow this order.

**Decision (Willian, Nov 10):** the supervisor sees recordings and AI summaries, and every call should have a summary (English and Spanish). Show recordings, transcript, sentiment and summary inside the "Reports" demo step, and analytics as the tier-2 add-on in pricing. Still no separate AI QA/evaluation section.

## Sources of truth (read these, do not re-derive)
- `docs/proposal/modelo-de-costos.md`, especially **section 3b** (three tiers) and sections 2 and 4–6.
- `docs/proposal/demo-runbook.md` (updated demo steps, numbers, users).
- `poc/infra/mei-demo/README.md` (bottom section: everything built on Nov 10).
- `docs/proposal/resumen-ejecutivo.md` (check it does not contradict the new pricing).

## Pricing: TWO consecutive slides (Willian, Nov 10)
1. **"Platform cost (AWS list prices)"**: the real cost of running it on AWS, the three tiers table below exactly, with its assumptions. This is our cost basis.
2. **"Suggested pricing for MEI"** (the next slide): what we would charge, built on slide 1 with an adequate margin and the client/business considerations. Propose it; do not present it as final. Mark it "Draft for internal review" in the notes and list every assumption so Willian can adjust it. Cover:
   - Recurring price per agent per month for each tier at 3 contact h/day (show 2 and 4 h as a range), as AWS cost + margin. Propose a margin with a short rationale (typical managed-service margins on usage are roughly 25–40%; pick one and say why), rounded to client-friendly numbers.
   - A fixed monthly managed-service fee (monitoring, changes to flows/queues/prompts, user admin, reports, support hours and response times) or explain if it is folded into the per-agent price.
   - One-time implementation (SOW): discovery, iDMS integration, flows and routing, AI agent, number porting, testing, training, parallel run with Zultys. Give ranges or "to be quoted after discovery"; no invented hours if there is no basis.
   - What is NOT included / passed through: telephony overages, toll-free minutes (rate not confirmed), SMS for payment links, third-party voice (ElevenLabs), payment processor and PCI work, DealerSocket/iDMS fees, AWS support plan.
   - Commercial considerations: minimum term or minimum seats, price review when volumes are known, usage billed at cost or bundled, who owns the AWS account (MEI's account with us managing it vs ours), how a volume discount from AWS would be shared.
   - Comparison hook: "per agent per month" is the number MEI can compare with what they pay today for Zultys + BrevAll + carriers (data still to be requested, `modelo-de-costos.md` section 6).
   Also add the same two-part structure to `docs/proposal/modelo-de-costos.md` as a new section (cost vs suggested price), consistent with the slides.

## Platform cost to show (from section 3b; list prices read on AWS pages on 2026-11-10)
The tier is chosen **per AWS account**, not per flow ("Connect Customer charges apply to all channel usage in your account").

| Tier | Includes | Voice | + mixed US telephony | Per agent / month at 2 / 3 / 4 contact h/day |
|---|---|---|---|---|
| 1. Normal flow (Customer Basic) | IVR, routing by days past due and special status, queues, transfers, queue callback*, recording, reports | $0.018/min | $0.0215/min | ~$52 / ~$77 / ~$103 |
| 2. Normal flow + analytics add-ons (Basic + conversational analytics) | + transcript, sentiment, AI post-call summary, keyword search | $0.033/min | $0.0365/min | ~$88 / ~$131 / ~$175 |
| 3. Everything included (Connect Customer) | + AI voice agent (Nova Sonic), generative voices, automated evaluations, wait-time estimates | $0.038/min | $0.0415/min | ~$100 / ~$149 / ~$199 |

Assumptions: 20 working days; mixed in/out telephony ≈ $0.0035/min; billed minutes include IVR, queue and transfers. Per-second billing, 10 s minimum (voice) and 60 s minimum (telephony). DID $0.03/day. No seat licence.
Points to make: the AI flow is not a separate charge in tier 3 (same per-minute price; its value is agent time saved); tier 2 → 3 costs ~$0.005/min more (~$18 per agent/month at 3 h/day); sentiment has no separate price line (it comes with conversational analytics); evaluations in Basic are $12/agent/month. *Confirm whether Basic's "customer callback not included" means the queue callback used in the demo.
Also show the AI-related note: Nova 2.5 Sonic exists in Bedrock but Amazon Lex (how Connect runs the voice AI) only accepts Nova 2 Sonic as of 2026-11-10; switching later is a configuration change. Re-verify before promising dates.

## What changed in the demo (Nov 10) — update slides that describe it
- Known callers are identified by phone number (ANI) and skip the menus: personal greeting in their language, routed by their account (Mauricio Cuevas ES, Mauricio Ordonez EN; rehearsal persona on `demo.caller2`).
- Unknown callers: "Thank you for calling", language menu, "Please enter your account number". Recording notice first (1.2 s lead silence).
- Agent workspace: branded workspaces (Committed Staff logo, purple top bar), agents land directly on the agent workspace; no AWS home page.
- Customer screen: Amazon Connect Customer Profiles with simulated data (address, vehicle loan in "Product purchase history", notes, contact history). Plus a panel on every call ("Customer on the line"), on AI handovers ("Transferred by the AI assistant": reason, AI summary, account, language, queue) and on agent-to-agent transfers ("Transferred by another agent").
- AI agent (Nova 2 Sonic): EN/ES, switches language mid-call on request and keeps the account, hands over to a person with context; falls back to a person instead of hanging up.
- Supervisor: recordings, transcripts, sentiment and AI post-call summary in English and Spanish (AWS lists es-US as supported). A summary is skipped when a call has too little conversation (seen on silent test calls: INSUFFICIENT_CONVERSATION_CONTENT).
- Visible names use the prefix "CS - " (queues, flows, quick connects); users stay `demo.*`.
- Automated test calls via Twilio with a simulated agent (both sides talk): all routing cases, both languages, AI handover and language switch passed; transcripts, sentiment and AI summaries generated in English and Spanish.
- Disposition (wrap-up) is built: when the call ends the agent sees "Call wrap-up" (disposition: Promise to pay, Payment made, Payment arrangement set, Callback requested, Dispute, Hardship - referred, Refused to pay, Information only, Wrong party, Transferred; follow-up; resolved; editable summary; date and notes) and it is saved on the call for reports. Agents have 60 s of after-call work. Saving was shown on screen but not yet verified end to end; say "configured" unless Willian confirms the test.
- Automatic categories (Contact Lens rules, EN/ES phrases): Promise_to_pay, Payment_arrangement, Financial_hardship, Dispute, Callback_requested, and Collection_notice_given (agent said the debt-collection notice, a compliance check). Message: the agent records the official outcome; the analysis flags what was actually said, so supervisors can spot mismatches. Categories are part of conversational analytics (tier 2/3), no extra price line found.
- Recording/QA: follow the decision note above.

## Rules (do not break)
- Never touch AWS in this chat; this task is documents only.
- No "mei" or "claude" in resource or file names you create; do not mention other projects.
- Separate verified facts from assumptions; no cost figures without stated assumptions.
- Credentials never printed or copied.
- Do not commit (not a git repo); keep files in `docs/proposal/`. Give Willian a short list of every slide changed.
