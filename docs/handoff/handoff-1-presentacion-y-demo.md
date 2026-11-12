# Hand-off 1: deck adjustments and demo preparation

Paste this as the first message of a new chat. Project: `/Users/willianmartinez/contact-center`. Read `AGENTS.md` first.
Meeting: MEI/Automax discovery, Wed Nov 11, 2026, 10:30-11:30 CT, in person (Mauricio Ordonez CTO, Mauricio Cuevas). Chat in Spanish (neutral Latin American, "tu"); decks and notes in English.

## Files
- `docs/proposal/MEI_Amazon_Connect_Options_DRAFT.pptx` (12 slides, from scratchpad `build_deck2.js`; the scratchpad may be gone: if so edit the pptx via unzip/XML or rebuild with pptxgenjs).
- `docs/proposal/MEI_Demo_Flows_Guide.pptx` (11 slides, `build_guide2.js`). Demo 5 (AI) says "Planned": outdated.
- `docs/proposal/modelo-de-costos.md`, `resumen-ejecutivo.md`, `docs/discovery/*`.
- Validate with the pptx skill (`validate.py`), render to PDF and look at every slide.

## Deck adjustments requested by Willian
1. Remove the slides/sections about **recording** and **AI transcription / QA** (Contact Lens style analytics).
2. Add a **Systems and payments** section: does MEI's contact center need integrations and support for payments (pay by phone, payment links, PCI scope, IVR payments), and how it connects to their systems (iDMS, CRM, telephony). Present as questions + what Connect offers; do not invent MEI facts.
3. Remove every **out of scope** mention/slide (internal office telephony stays only as one question to MEI: "of the 210 planned users, who takes or makes customer calls?").
4. **Review prices and costs** against the AWS pricing pages (Nov 10, 2026 figures: Connect Customer $0.038/min voice, telephony $0.0022 in / $0.0048 out, DID $0.03/day, campaigns $0.045/min; illustrative ~$100/$149/$199 per agent/month at 2/3/4 contact hours/day). Re-verify, state assumptions, fix `modelo-de-costos.md` and the deck together.
5. Update Demo 5 (AI agent) as tested: Nova 2 Sonic, EN/ES, multi-turn, number +1 775 249 1758.

## Demo order (agreed)
1. Basics: place a call and show who is calling (depends on Hand-off 2 for the screen).
2. Transfer (one call ID, all legs).
3. Disposition (wrap-up code): NOT built yet; needs design and setup in Connect.
4. AI agent.
5. Flows and reports.
6. Reports (historical + real-time supervisor).
7. Pricing.
Produce a step-by-step runbook for that order (who calls from where, which user logs in, what to say, what to show, fallback if something fails).

## Demo environment (account 383799408374, `cs-admin` profile, always check the account id first)
- Instance `cs-connect-demo` (id c2f9ca2b-eb05-4a82-9809-1d7c914333ba), prefix `demo`, scripts in `poc/infra/mei-demo/` (setup_part_a.py, setup_ai.py, setup_ai_flow.py, chain.py). Python needs boto3: no system boto3; create a venv.
- Users demo.agent1/agent2/supervisor/caller; passwords only in `poc/.credentials.local` (never print them). Twilio and ElevenLabs keys in `.env` (never print).
- Routing cases 1-7 are verified for 1, 3, 7; the user still has to test 2, 4, 5, 6.

## Open problems to resolve first
- **Supervisor sees no recording player or transcript in Contact details.** Cause found: `CallCenterManager` lacks the new permissions (`CallRecordings.Unredacted.Access`, `AutomatedVoiceInteraction.Recordings.Unredacted.Access`, `ContactTranscripts.Unredacted.Access`, `ContactLensPostContactSummary.View`, download buttons). `update-security-profile` REPLACES the whole list: read the current list, add the new ones, then update. The harness blocked my first attempt; ask Willian for explicit approval (or create a neutral profile `demo-supervisor`).
- Contact Lens post-call analytics was enabled in `demo-ai-inbound` (blocks LensEn/LensEs, `AnalyticsModes: PostContact`); a test call at 14:44 had produced no analysis file yet. Since the deck drops transcription/QA, decide whether to keep it (cost) or revert.
- Nova 2.5 Sonic untested (only if there is time; do not risk the demo).
- AI by voice untested: Spanish multi-turn, escalation (needs demo.agent1 Available), outbound AI.

## Rules (do not break)
- Never delete anything in AWS without explicit confirmation. Never work around a blocked action.
- No "mei" or "claude" in resource/user names; neutral names with prefix `demo`.
- Do not mention other projects in AGENTS.md. Do not copy other projects' .env files.
- Keep Twilio test calls short (1-2 min). Short summaries, simple step-by-step instructions.
- Cleanup at the end only with confirmation: cs-admin access key, Twilio/ElevenLabs keys, old sandbox stacks (never stack 01).
