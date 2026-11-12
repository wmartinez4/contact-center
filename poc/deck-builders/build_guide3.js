const pptxgen = require("pptxgenjs");
const SKILL = "/Users/willianmartinez/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/fe112ec4-93e2-448b-8146-17b065462965/740ff72a-525b-4b03-b948-01aba0ced011/skills/pptx";
const { applyTheme } = require(`${SKILL}/scripts/apply_theme.js`);

const THEME = {
  name: "MEI Neutral", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: "1F2A30", lt1: "FFFFFF", dk2: "3B4A54", lt2: "F2F4F5", accent1: "3E6E8E", accent2: "2E7D5B", accent3: "A9690F", accent4: "A04040", accent5: "6B7A84", accent6: "5B8C85", hlink: "3E6E8E", folHlink: "6B7A84" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "MEI demo: run order and test guide";
const C = pres.SchemeColor;

// Slide status marks: native sections (visible in the slide sorter) plus a colored tag placed just
// above the slide, visible when editing and absent from slideshow, print and PDF export.
const TOTAL = 11, INTERNAL = new Set([1,2,3,4,5,6,7,8,9,10,11]);
(() => {
  let from = 1;
  const runs = [];
  for (let i = 1; i <= TOTAL + 1; i++) {
    if (i === TOTAL + 1 || INTERNAL.has(i) !== INTERNAL.has(from)) { runs.push([from, i - 1, INTERNAL.has(from)]); from = i; }
  }
  const titleOf = (n) => { const r = runs.find((q) => n >= q[0] && n <= q[1]); return (r[2] ? "Internal only" : "Client-ready") + ` (${r[0]}-${r[1]})`; };
  runs.forEach((r) => pres.addSection({ title: (r[2] ? "Internal only" : "Client-ready") + ` (${r[0]}-${r[1]})` }));
  let n = 0;
  const add = pres.addSlide.bind(pres);
  pres.addSlide = (o) => {
    n++;
    const internal = INTERNAL.has(n);
    const s = add(Object.assign({}, o, { sectionTitle: titleOf(n) }));
    s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: -0.42, w: 2.6, h: 0.32, rectRadius: 0.08, fill: { color: internal ? "E8B923" : "2E9E6B" }, line: { color: internal ? "E8B923" : "2E9E6B", width: 0 }, objectName: "Status tag" });
    s.addText(internal ? "INTERNAL ONLY" : "CLIENT-READY", { x: 0.6, y: -0.42, w: 2.6, h: 0.32, fontSize: 12, bold: true, color: internal ? "1F2A30" : "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Status tag text" });
    const notes = s.addNotes.bind(s);
    s.addNotes = (t) => notes((internal ? "[INTERNAL ONLY - do not show to the client] " : "[CLIENT-READY] ") + t);
    return s;
  };
})();
const OUT = process.env.OUT || "/private/tmp/claude-501/-Users-willianmartinez--claude-spares-spare-AT5JJd/8122a2a7-74aa-4d4a-9206-3e8b2f6fd869/scratchpad/guide3.pptx";

pres.defineSlideMaster({
  title: "TITLE", background: { color: "1F2A30" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 2.3, w: 11.5, h: 1.3, fontSize: 44, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.9, y: 3.8, w: 11.5, h: 1.2, fontSize: 20, color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 9.4, h: 0.85, fontSize: 30, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "MEI demo guide  |  Simulated data only  |  Draft", options: { x: 0.6, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: C.accent5, margin: 0, isTextBox: true } } },
  ],
  slideNumber: { x: 12.1, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent5 },
});

const BORDER = { type: "solid", pt: 0.75, color: "D5DADD" };
const colorOf = { green: C.accent2, amber: C.accent3, red: C.accent4, blue: C.accent1, teal: C.accent6 };
function chip(s, name, text, x, y, w, color) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h: 0.36, rectRadius: 0.18, objectName: name, fill: { color: colorOf[color], transparency: 85 }, line: { color: colorOf[color], width: 0.75 } });
  s.addText(text, { x, y, w, h: 0.36, fontSize: 12, bold: true, color: colorOf[color], align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: name + " text" });
}
const KIND = {
  step: { fill: C.background2, ft: 0, line: "D5DADD", color: C.text1 },
  decision: { fill: C.accent1, ft: 88, line: C.accent1, color: C.text1 },
  good: { fill: C.accent2, ft: 88, line: C.accent2, color: C.text1 },
  bad: { fill: C.accent4, ft: 88, line: C.accent4, color: C.text1 },
  ai: { fill: C.accent6, ft: 82, line: C.accent6, color: C.text1 },
  note: { fill: C.background1, ft: 0, line: "D5DADD", color: C.text1 },
};
function box(s, name, text, x, y, w, h, kind, o) {
  const k = KIND[kind || "step"];
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, objectName: name, fill: { color: k.fill, transparency: k.ft }, line: { color: k.line, width: 1 } });
  s.addText(text, Object.assign({ x: x + 0.08, y, w: w - 0.16, h, fontSize: 13, bold: kind !== "note", color: k.color, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: name + " text" }, o || {}));
}
function arrow(s, name, x1, y1, x2, y2, head) {
  s.addShape(pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), objectName: name, flipH: x2 < x1, flipV: y2 < y1, line: { color: C.accent5, width: 1.75, endArrowType: head === false ? "none" : "triangle" } });
}
function label(s, name, text, x, y, w) {
  s.addText(text, { x, y, w: w || 0.6, h: 0.28, fontSize: 11, bold: true, color: C.accent1, margin: 0, isTextBox: true, align: "center", objectName: name });
}
function head(s, title, statusText, statusColor) {
  s.addText(title, { placeholder: "title" });
  chip(s, "Status chip", statusText, 10.2, 0.5, 2.5, statusColor);
}
const W = 2.1, H = 0.85, XS = [0.6, 3.1, 5.6, 8.1, 10.6];
function row5(s, prefix, texts, y, kinds) {
  texts.forEach((t, i) => box(s, prefix + (i + 1), t, XS[i], y, W, H, (kinds && kinds[i]) || "step"));
  for (let i = 0; i < texts.length - 1; i++) arrow(s, `${prefix}arrow ${i + 1}`, XS[i] + W, y + H / 2, XS[i + 1], y + H / 2);
}
function hdr(t) { return { text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 12, valign: "middle" } }; }
function cell(t, o) { return { text: t, options: Object.assign({ fontSize: 12, color: C.text1, valign: "middle" }, o || {}) }; }
function bullets(s, name, items, x, y, w, h, size) {
  s.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })), { x, y, w, h, fontSize: size || 16, color: C.text1, valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true, objectName: name });
}

// 1. Title
{
  const s = pres.addSlide({ masterName: "TITLE" });
  s.addText("MEI demo: run order and test guide", { placeholder: "title" });
  s.addText("Seven parts on Amazon Connect, with simulated data\nWhat to run, what to show, what to say, what to do if it fails  |  Draft", { placeholder: "body" });
  s.addNotes("PURPOSE. The working companion for the demo on November 11, 2026. The order is the one agreed: basic call and who is calling, transfer, disposition, AI agent, flows, reports, pricing. Each slide shows one part; the notes say how to run it and what to say. The step-by-step runbook is docs/proposal/demo-runbook.md.\n\nSTATUS RULE. Every part carries a status chip. 'Tested' means a real call went through it and the result was read from the records. 'Not built' means designed only. Do not describe something as working unless a real call has proved it.\n\nDATA RULE. Everything uses invented accounts. Nothing touches MEI data or iDMS. Say this at the start of the demo.");
}

// 2. Overview
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("The seven parts at a glance", { placeholder: "title" });
  const parts = [
    ["1", "Basic call", "Known number greeted by name; profile on screen", "Tested", "green"],
    ["2", "Transfer", "One call ID across every leg", "Tested", "green"],
    ["3", "Disposition", "Wrap-up form after the call", "Configured", "amber"],
    ["4", "AI agent", "Nova 2 Sonic, EN and ES, hand-over", "Tested", "green"],
    ["5", "Flows", "Status before delinquency", "Tested", "green"],
    ["6", "Reports", "Real-time, history, recordings, summaries", "Tested", "green"],
    ["7", "Pricing", "Platform cost, then suggested price", "Draft", "amber"],
  ];
  const w = 1.6;
  parts.forEach((d, i) => {
    const x = 0.6 + i * 1.75, y = 1.6;
    box(s, "Part box " + d[0], "", x, y, w, 3.5, "step");
    s.addText(d[0], { x: x + 0.15, y: y + 0.15, w: 0.5, h: 0.5, fontSize: 28, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "Part number " + d[0] });
    s.addText(d[1], { x: x + 0.15, y: y + 0.75, w: w - 0.3, h: 0.45, fontSize: 16, bold: true, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "Part name " + d[0] });
    s.addText(d[2], { x: x + 0.15, y: y + 1.25, w: w - 0.3, h: 1.5, fontSize: 13, color: C.accent5, margin: 0, valign: "top", isTextBox: true, objectName: "Part what " + d[0] });
    chip(s, "Part chip " + d[0], d[3], x + 0.08, y + 2.95, w - 0.16, d[4]);
  });
  s.addText("Parts 1 to 3 and 5 to 6 replace what MEI has today. Part 4 adds AI. Part 7 closes on cost.", { x: 0.6, y: 5.4, w: 12.1, h: 0.4, fontSize: 16, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Parts caption" });
  s.addText("Before the meeting: save one wrap-up form end to end, and run each part once by voice.", { x: 0.6, y: 5.85, w: 12.1, h: 0.4, fontSize: 14, color: C.accent3, bold: true, margin: 0, isTextBox: true, objectName: "Todo caption" });
  s.addNotes("1. BASIC CALL. A known caller dials +1 775 245 6050, is recognized by phone number, skips the menus, hears a personal greeting in their language and rings an agent, who sees the customer profile and a 'Customer on the line' panel (simulated data). Unknown callers get the language and account menus.\n\n2. TRANSFER. A transferred call keeps one call ID across legs. Confirmed on real calls, with a consult transfer and a direct transfer.\n\n3. DISPOSITION. When the call ends the agent fills a 'Call wrap-up' form (disposition, follow-up, resolved, summary, notes) saved on the call. Configured; the end-to-end save is not yet confirmed.\n\n4. AI AGENT. Amazon Nova 2 Sonic through a Lex bot on +1 775 249 1758. Tested on a real call in English, multi-turn (November 10, 2026), and by scripted calls for the language switch and the hand-over to a person. Outbound AI is not part of the demo.\n\n5. FLOWS. Routing by language, special status and days past due. All seven cases passed on test calls on November 10.\n\n6. REPORTS. Real-time agents and queues, listen-in, historical metrics and contact search, then one finished call with recording, transcript, sentiment, AI summary (English and Spanish) and automatic categories.\n\n7. PRICING. Slides 10 and 11 of the options deck: platform cost on AWS, then the suggested price (a draft).");
}

// 3. Setup
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Setup: who is who", { placeholder: "title" });
  const xs = [0.6, 2.66, 4.72, 6.78, 8.84, 10.9], w = 1.8;
  const items = [
    ["Caller\nphone, Twilio or demo.caller", "step"], ["Main number\n+1 775 245 6050", "step"], ["Flow\nCS - Inbound -\nCollections Routing", "decision"],
    ["Queue\nby case", "decision"], ["Agent 1\ndemo.agent1\nbrowser 1", "good"], ["Agent 2\ndemo.agent2\nbrowser 2", "good"],
  ];
  items.forEach((it, i) => box(s, "Setup box " + (i + 1), it[0], xs[i], 1.7, w, 1.3, it[1]));
  for (let i = 0; i < 5; i++) arrow(s, "Setup arrow " + (i + 1), xs[i] + w, 2.35, xs[i + 1], 2.35);
  box(s, "AI number box", "AI number\n+1 775 249 1758", 2.66, 3.4, w, 1.1, "ai");
  box(s, "AI flow box", "Flow\nCS - Inbound -\nAI Agent", 4.72, 3.4, w, 1.1, "ai");
  arrow(s, "AI arrow", 2.66 + w, 3.95, 4.72, 3.95);
  box(s, "Supervisor box", "Supervisor\ndemo.supervisor\nbrowser 3", 8.84, 3.4, w, 1.1, "ai");
  bullets(s, "Setup bullets", ["Each user in its own browser or profile. Use headphones", "Agents Available; they auto-accept. The supervisor is not in the Collections queues", "AI hand-over rings demo.agent1: keep it Available during part 4", "Known callers: Mauricio Cuevas (Spanish, 18 days) and Mauricio Ordonez (English, 10 days) skip the menus", "Share only the softphone and result windows, never the AWS console or the credentials file"], 0.6, 4.8, 12.1, 2.0, 15);
  s.addNotes("ACCOUNT. Demo account 383799408374, profile cs-admin, instance cs-connect-demo. Always check the account ID before running any script.\n\nWHY THESE USERS. A call needs someone to answer and, for the transfer, a second agent. The supervisor is a third session. Connect allows one session per browser, so each user needs its own browser or profile. With one computer, headphones prevent echo.\n\nTHE USERS. demo.agent1 is the front-line agent: it receives the delinquency queues and the fallback queue. demo.agent2 is the specialist: it only receives Redemptions and EPD. demo.supervisor has the manager profile but no Collections queue. demo.caller can dial the number from a browser softphone if no phone is at hand. Passwords are only in poc/.credentials.local.\n\nTWO NUMBERS. +1 775 245 6050 runs the routing flow (parts 1, 2, 5). +1 775 249 1758 runs the AI agent (part 4).\n\nAVAILABLE AND AUTO-ACCEPT. Agents must be Available or they never receive calls. Closing a finished contact returns the agent to Available.");
}

// 4. Part 1 basic call
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  head(s, "Part 1: basic call, who is calling", "Tested", "green");
  row5(s, "P1 step ", ["Known caller dials +1 775 245 6050", "Number recognized", "Recording notice, greeting by name", "Routed by account", "Agent 1 rings and answers"], 1.5, ["step", "decision", "step", "decision", "good"]);
  box(s, "P1 shows", "", 0.6, 2.85, 12.1, 2.6, "note");
  s.addText("What the agent should see", { x: 0.9, y: 3.0, w: 6, h: 0.4, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "P1 shows title" });
  bullets(s, "P1 shows bullets", ["The agent workspace opens by itself (branded, no AWS home page)", "Customer profile (simulated): address, vehicle loan, notes, contact history", "Panel 'Customer on the line': name, account, status, days past due, language"], 0.9, 3.5, 11.5, 1.8, 16);
  s.addText("Unknown number: 'Thank you for calling', language menu, 'Please enter your account number' (press 1, then 3). Fallback: open the contact in Contact search and show its attributes.", { x: 0.6, y: 5.7, w: 12.1, h: 0.7, fontSize: 14, bold: true, color: C.accent3, margin: 0, isTextBox: true, objectName: "P1 fallback" });
  s.addNotes("WHAT IT SHOWS. The everyday call: someone calls, the system identifies the account and routes it, an agent answers and knows who is on the line before speaking.\n\nHOW TO RUN. Ask Mauricio Cuevas (Spanish, 18 days past due, routed to 16-30) or Mauricio Ordonez (English, 10 days, routed to 9-15) to dial +1 775 245 6050 from their own phone. Their numbers are loaded as customers with simulated account data. The system recognizes the number, plays the recording notice, greets them by name in their language and routes them with no menu. A rehearsal persona on demo.caller2 does the same. An unknown number gets the language menu and is asked for an account number: press 1, then 3.\n\nWHAT THE AGENT SEES. Agents land directly on the agent workspace. It shows the customer profile from Amazon Connect Customer Profiles (address, a vehicle loan under product purchase history, notes, contact history) and a panel 'Customer on the line'.\n\nWHAT TO SAY. 'In production the account comes from iDMS by the caller's number or an account code. Here a simulated lookup plays that role with invented accounts.' Do not promise a CRM integration: say the agent screen is configurable and MEI's CRM can open beside it.\n\nIF IT FAILS. Agent not Available, or the call lands elsewhere: check the agent's routing profile. No panel: open the contact in Contact search and show its attributes. No ring at all: call from a second phone; then fall back to the recorded video.");
}

// 5. Part 2 transfer
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  head(s, "Part 2: transfer with one call ID", "Tested", "green");
  const xs = [0.6, 2.66, 4.72, 6.78, 8.84, 10.9], w = 1.8;
  const t = ["Call lands in 16-30 queue", "Agent 1 answers", "Quick connect: Transfer to Redemptions", "Agent 2 answers", "Both hang up", "Run chain.py"];
  t.forEach((x, i) => box(s, "P2 step " + (i + 1), x, xs[i], 1.6, w, 1.1, i === 5 ? "good" : (i === 2 ? "decision" : "step")));
  for (let i = 0; i < 5; i++) arrow(s, "P2 arrow " + (i + 1), xs[i] + w, 2.15, xs[i + 1], 2.15);
  box(s, "P2 pass card", "", 0.6, 3.3, 12.1, 2.4, "note");
  s.addText("Pass if", { x: 0.9, y: 3.45, w: 4, h: 0.4, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Pass title" });
  bullets(s, "Pass bullets", ["Both legs show the same master_call_id and department", "Leg 2 points back to leg 1 (initial and previous contact IDs)", "Agent 2 sees the panel 'Transferred by another agent': customer summary, where the call came from, account, status, language"], 0.9, 3.95, 11.5, 1.6, 16);
  s.addText("Confirmed on real calls, with a consult transfer and a direct transfer.", { x: 0.6, y: 5.95, w: 12.1, h: 0.4, fontSize: 14, bold: true, color: C.accent2, margin: 0, isTextBox: true, objectName: "Result line" });
  s.addNotes("WHY IT MATTERS. MEI wants fewer unnecessary transfers and context that survives them. In Connect every transfer creates a new contact with its own record, so there is no single ID for the whole conversation by default. We set master_call_id on the first leg and it carries over.\n\nSTEPS. Use case 3 so the call rings Agent 1. While connected, Agent 1 opens Quick connects and chooses 'CS - Transfer to Redemptions'. Agent 2 sees the panel 'Transferred by another agent'. A consult transfer leaves both agents connected (Join and Swap): Agent 1 joins and hangs up. A direct transfer completes by itself. Talk briefly, then hang up.\n\nTHE CHECK. Wait a minute or two (contact records are not instant) and run: AWS_PROFILE=cs-admin CONNECT_INSTANCE_ID=c2f9ca2b-eb05-4a82-9809-1d7c914333ba DEMO_PREFIX=demo python3 chain.py --hours 1 (from poc/infra/mei-demo, in a venv with boto3). It prints every leg with IDs, times, queue, agent, department and master ID. Or open Contact search and show both legs.\n\nIF IT FAILS. Agent 2 not Available: the transfer waits in queue. Records not there yet: show the finished call prepared before the meeting.");
}

// 6. Part 3 disposition
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  head(s, "Part 3: disposition (wrap-up)", "Configured", "amber");
  row5(s, "P3 step ", ["Call ends", "Agent sees 'Call wrap-up' (60 s)", "Picks a disposition", "Saved on the call", "Visible in search and reports"], 1.5, ["step", "step", "decision", "good", "good"]);
  box(s, "P3 codes", "", 0.6, 2.7, 5.9, 3.4, "note");
  s.addText("The form the agent fills", { x: 0.85, y: 2.85, w: 5.4, h: 0.4, fontSize: 16, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "P3 codes title" });
  bullets(s, "P3 codes left", ["Promise to pay", "Payment made", "Payment arrangement set", "Callback requested", "Dispute"], 0.85, 3.3, 2.7, 1.9, 13);
  bullets(s, "P3 codes right", ["Hardship - referred", "Refused to pay", "Information only", "Wrong party", "Transferred"], 3.6, 3.3, 2.7, 1.9, 13);
  s.addText("Plus follow-up, resolved, an editable summary, date and notes.", { x: 0.85, y: 5.3, w: 5.4, h: 0.6, fontSize: 13, color: C.accent5, margin: 0, isTextBox: true, valign: "top", objectName: "P3 codes extra" });
  box(s, "P3 build", "", 6.8, 2.7, 5.9, 3.4, "note");
  s.addText("Automatic categories (from the analysis)", { x: 7.05, y: 2.85, w: 5.4, h: 0.4, fontSize: 16, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "P3 build title" });
  bullets(s, "P3 build bullets", ["Promise to pay, Payment arrangement", "Financial hardship, Dispute", "Callback requested", "Collection notice given (compliance check)"], 7.05, 3.3, 5.4, 1.5, 13);
  s.addText("The agent records the official outcome; the analysis flags what was actually said, so supervisors can spot mismatches. English and Spanish phrases; part of conversational analytics.", { x: 7.05, y: 4.85, w: 5.4, h: 1.1, fontSize: 13, bold: true, color: C.accent1, margin: 0, isTextBox: true, valign: "top", objectName: "P3 message" });
  s.addText("Status: configured. The save was shown on screen but not confirmed end to end: say 'configured' until it is.", { x: 0.6, y: 6.3, w: 12.1, h: 0.45, fontSize: 14, bold: true, color: C.accent3, margin: 0, isTextBox: true, objectName: "P3 fallback" });
  s.addNotes("STATUS. Configured on November 10, 2026. The form was shown on screen, but saving it end to end (disposition stored on the call and visible in reports) has not been confirmed. Until it is, say 'configured', not 'working'. Run one call and check before the meeting.\n\nWHAT IT IS. When the call ends the agent sees 'Call wrap-up': a disposition (Promise to pay, Payment made, Payment arrangement set, Callback requested, Dispute, Hardship - referred, Refused to pay, Information only, Wrong party, Transferred), a follow-up, resolved, an editable summary, a date and notes. It is saved on the call so reports can use it. Agents have 60 seconds of after-call work.\n\nCODES. This list is a starting point built for the demo; MEI must give its own list. Collections teams usually already have one.\n\nAUTOMATIC CATEGORIES. Separately, Contact Lens rules (English and Spanish phrases) tag what was actually said: Promise_to_pay, Payment_arrangement, Financial_hardship, Dispute, Callback_requested and Collection_notice_given (the agent said the debt-collection notice, a compliance check). The message: the agent records the official outcome; the analysis flags what was said, so supervisors can spot mismatches. Categories belong to conversational analytics (tier 2 or 3 of the pricing); no separate price line was found.\n\nWHAT TO SAY. 'Every call closes with an outcome chosen by the agent; it is stored with the call and reported. We will configure MEI's own codes.'");
}

// 7. Part 4 AI
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  head(s, "Part 4: AI voice agent", "Tested EN and ES", "green");
  row5(s, "P4 step ", ["Call +1 775 249 1758", "Notice, language 1 EN / 2 ES", "Nova 2 Sonic: how can I help?", "Account code, lookup (simulated)", "Balance, due date, how to pay"], 1.5, ["step", "decision", "ai", "step", "ai"]);
  arrow(s, "P4 arrow down", 11.65, 2.35, 11.65, 3.2);
  box(s, "P4 more", "Anything else? (multi-turn)", 10.6, 3.2, W, H, "ai");
  arrow(s, "P4 no arrow", 10.6, 3.625, 10.2, 3.625); label(s, "P4 esc label", "Agent", 10.1, 3.3, 0.6);
  box(s, "P4 escalate", "Hand-over: reason, language, queue", 8.1, 3.2, W, H, "ai");
  arrow(s, "P4 escalate arrow", 8.1, 3.625, 7.7, 3.625);
  box(s, "P4 agent", "Agent 1 sees reason, AI summary, queue", 5.6, 3.2, W, H, "good");
  arrow(s, "P4 yes arrow", 11.65, 4.05, 11.65, 4.9); label(s, "P4 done label", "Done", 11.7, 4.3, 0.6);
  box(s, "P4 end", "Goodbye; outcome resolved", 10.6, 4.9, W, H, "good");
  box(s, "P4 note", "AI informs only: no payments, no card data. Switches EN/ES on request", 0.6, 3.2, 4.6, H, "note", { fontSize: 13, bold: true, color: C.accent1 });
  box(s, "P4 tested", "Tested Nov 10: 64-second English call (balance, due date, how to pay); scripted calls for the language switch and the hand-over", 0.6, 4.9, 9.6, H, "note", { fontSize: 14, bold: true, color: C.accent2 });
  s.addNotes("STATUS. Tested on a real call on November 10, 2026 (contact 130738af): 1 minute 4 seconds, English, multi-turn. The caller asked for the balance, gave account code 3, asked for the due date and how to pay, then ended. Outcome: resolved. Audio and transcript: poc/samples/call-ai-130738af.mp3 and its transcript.\n\nHOW IT IS BUILT. Flow demo-ai-inbound on +1 775 249 1758: notice and language menu, then a Lex bot (demo-assistant) configured with the speech model Amazon Nova 2 Sonic (amazon.nova-2-sonic-v1:0), voice Tiffany in English (en_US) and Lupe in Spanish (es_US). A function answers with the invented accounts. The bot can give balance and due date, explain payment options (the Text-to-Pay link or a person) and ask whether there is anything else. If the caller asks for a person, the account is not found or it does not understand, it hands over: the flow sets the queue from the same rules as part 5 and passes reason, language and summary as attributes.\n\nALSO TESTED. Scripted calls on November 10: the hand-over to a person (the agent sees the panel 'Transferred by the AI assistant' with reason, AI summary, account, language and queue) and the language switch ('Spanish please' / 'en inglés'), which keeps the account. If the voice bot ends in an error, the flow falls back to a person instead of hanging up. Outbound AI is not part of the demo. The hand-over needs demo.agent1 Available.\n\nGUARDRAILS. The AI only informs: no payments, card numbers or payment plans. It says it is automated, and the call starts with the notice.\n\nHOW TO RUN. Dial +1 775 249 1758 on speaker so the room hears it. Press 1. Say: 'What is my balance?', then 'My account code is 3', then 'When is my payment due?', 'How can I pay?', and 'No, that is all'. For the language switch say 'Spanish please'. For the hand-over say 'I want to talk to a person'.\n\nIF IT FAILS. Play the recording of the November 10 call and say it is a recording.");
}
// 8. Part 5 flows
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  head(s, "Part 5: routing flows", "Tested", "green");
  row5(s, "D1 step ", ["Call arrives", "Notice; call ID set", "Language: 1 EN, 2 ES", "Case 1 to 7 (keypad)", "Lookup (simulated iDMS)"], 1.5, ["step", "step", "decision", "decision", "step"]);
  arrow(s, "D1 arrow down", 11.65, 2.35, 11.65, 3.2);
  box(s, "D1 found", "Account found?", 10.6, 3.2, W, H, "decision");
  box(s, "D1 special", "Special status?", 8.1, 3.2, W, H, "decision");
  box(s, "D1 days", "Days past due", 5.6, 3.2, W, H, "decision");
  box(s, "D1 delay queues", "Current, 1-8, 9-15, 16-30, 31+", 3.1, 3.2, W, H, "good");
  arrow(s, "D1 found yes", 10.6, 3.625, 10.2, 3.625); label(s, "D1 yes label", "Yes", 10.15, 3.3, 0.5);
  arrow(s, "D1 special no", 8.1, 3.625, 7.7, 3.625); label(s, "D1 no label", "No", 7.65, 3.3, 0.5);
  arrow(s, "D1 days arrow", 5.6, 3.625, 5.2, 3.625);
  box(s, "D1 fallback", "Fallback queue", 10.6, 4.9, W, H, "bad");
  arrow(s, "D1 not found", 11.65, 4.05, 11.65, 4.9); label(s, "D1 not found label", "No", 11.7, 4.3, 0.5);
  box(s, "D1 special queue", "Redemptions or EPD queue", 8.1, 4.9, W, H, "good");
  arrow(s, "D1 special yes", 9.15, 4.05, 9.15, 4.9); label(s, "D1 special yes label", "Yes", 9.2, 4.3, 0.5);
  box(s, "D1 collector", "Announce the queue, transfer, agent rings", 3.1, 4.9, 4.6, H, "step");
  arrow(s, "D1 delay down", 4.15, 4.05, 4.15, 4.9);
  arrow(s, "D1 special to collector", 8.1, 5.325, 7.7, 5.325);
  arrow(s, "D1 fb down", 11.65, 5.75, 11.65, 6.4, false);
  arrow(s, "D1 fb across", 11.65, 6.4, 5.4, 6.4, false);
  arrow(s, "D1 fb up", 5.4, 6.4, 5.4, 5.75);
  box(s, "D1 rule", "Rule: special status is checked BEFORE days past due", 0.6, 3.2, W, 2.55, "note", { fontSize: 14, bold: true, color: C.accent1 });
  s.addNotes("WHAT HAPPENS, STEP BY STEP.\n1. The call reaches the number and the flow turns on flow logging, so every block can be inspected afterwards.\n2. Recording is switched on for the agent, the customer and the automated part of the call (menu and queue).\n3. The flow writes the attribute master_call_id with the ID of this first contact, and department = Collections. This is the seed of the single call ID; it is written once here.\n4. A notice says the call may be recorded, first in English and then in Spanish.\n5. The caller hears one bilingual audio, 'For English, press 1. Para español, oprima 2', and presses 1 or 2. The flow switches the language.\n6. The caller types a case number from 1 to 7. This is a test mechanism: in production the account would be found from the caller's number or an account number.\n7. The flow calls the Lambda demo-lookup, which plays the role of iDMS plus MEI's routing rules. It evaluates in this order: not found goes to Fallback; a special status (Redemptions or EPD) goes to that queue; otherwise days past due choose Current, 1-8, 9-15, 16-30 or 31 plus.\n8. The flow stores the result, announces the queue, sets it dynamically and transfers the call. An available agent in that queue rings and auto-accepts.\n\nVOICE. Every fixed message (notice, menus, queue announcements and the callback offer) is audio generated with ElevenLabs, voice Sarah, and imported into Amazon Connect as a prompt, in English and Spanish with the same voice. If a prompt is missing, Connect reads the same text with Amazon Polly. We use Sarah because the free ElevenLabs plan only allows its standard voices through the API; library voices need a paid plan. Audio is regenerated with build_prompts.py.\n\nTHE KEY RULE. MEI said specialized status must take precedence. Case 5 is a Redemptions account 12 days past due: without the rule it would land in the 9-15 queue.\n\nSTATUS. All seven cases have gone through the notice, menus, lookup, dynamic queue and agent on test calls (case 3 on many real calls; cases 2 to 7 on scripted calls on November 10, with the expected queue each time). Known callers skip the menus and are routed by the same rules from their account.\n\nIF IT FAILS. Check the flow logs in CloudWatch, then confirm the agent is Available and in a routing profile that contains that queue.\n\nSAY. 'The routing logic lives in one lookup service. In production that service reads iDMS, which we have not seen yet.'");
}

// 9. Part 5 cases
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  head(s, "Part 5: the seven test cases", "All 7 tested", "green");
  const rows = [
    [hdr("Press"), hdr("Language"), hdr("Account profile"), hdr("Expected queue"), hdr("Rings at"), hdr("Pass?")],
    [cell("1, then 1"), cell("English"), cell("Current, 0 days"), cell("Current"), cell("Agent 1"), cell("Tested")],
    [cell("2, then 2"), cell("Spanish"), cell("5 days past due"), cell("1-8"), cell("Agent 1"),cell("Tested")],
    [cell("1, then 3"), cell("English"), cell("22 days past due"), cell("16-30"), cell("Agent 1"), cell("Tested")],
    [cell("2, then 4"), cell("Spanish"), cell("47 days past due"), cell("31 plus"), cell("Agent 1"),cell("Tested")],
    [cell("1, then 5", { bold: true }), cell("English", { bold: true }), cell("12 days + Redemptions", { bold: true }), cell("Redemptions, not 9-15", { bold: true, color: C.accent2 }), cell("Agent 2", { bold: true }), cell("Tested", { bold: true })],
    [cell("2, then 6"), cell("Spanish"), cell("3 days + EPD"), cell("EPD"), cell("Agent 2"),cell("Tested")],
    [cell("1, then 7"), cell("English"), cell("Account not found"), cell("Fallback"), cell("Agent 1"), cell("Tested")],
  ];
  s.addTable(rows, { x: 0.6, y: 1.5, w: 12.1, colW: [1.6, 1.5, 3.2, 3.0, 1.6, 1.2], rowH: 0.52, border: BORDER });
  s.addText("Show case 5 live. All seven cases passed on test calls; these keypad cases are the unknown-caller path.", { x: 0.6, y: 5.8, w: 12.1, h: 0.4, fontSize: 14, color: C.accent5, margin: 0, isTextBox: true, objectName: "Table caption" });
  s.addNotes("HOW TO USE THIS TABLE. Press the language digit first, then the case digit, using a phone, or let Twilio send the digits. The 'Rings at' column says which agent should receive the call. Tick 'Pass?' when the announcement and the ringing agent both match.\n\nWHY THESE SEVEN. They are inventions built from MEI's requirements: five delinquency groups, two of the specialized statuses (Redemptions and Early Payment Default), and an unknown account. OFR/Skip is reserved but has no case because we do not know what OFR means.\n\nTHE ONE THAT MATTERS. Case 5. A Redemptions account at 12 days past due must go to Redemptions and not to the 9-15 queue. If only one case is shown, show this one.\n\nSPANISH CASES (2, 4, 6). They test that the Spanish voice and wording work. The Spanish is spoken by Sarah, an English-native voice using a multilingual model, so it may sound less native than a Spanish-first voice.\n\nSTATUS. All seven passed on calls. Case 3 has gone through real calls many times; the others by scripted calls on November 10.");
}

// 10. Part 6 reports
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  head(s, "Part 6: reports for supervisors", "Tested", "green");
  const cards = [
    ["Real-time", "Real-time metrics. Agents table: who is on a call and for how long. Queues: waiting and oldest call.", "Tested on a live call"],
    ["Listen-in", "The eye icon on an agent on a call. The supervisor hears it live (softphone open, Available).", "Tested on a live call"],
    ["History", "Historical metrics: contacts handled, abandoned, average wait, transfers, by queue and agent.", "Prepare one report"],
    ["Contact search", "Every leg of a call with queue, agent, times, call ID and disposition.", "Standard"],
    ["Call analysis", "Recording, transcript, sentiment, AI summary (EN and ES) and automatic categories.", "Tested on test calls"],
  ];
  cards.forEach((c, i) => {
    const x = 0.6 + i * 2.45;
    box(s, "Report card " + (i + 1), "", x, 1.6, 2.3, 3.6, "step");
    s.addText(c[0], { x: x + 0.15, y: 1.8, w: 2.0, h: 0.45, fontSize: 16, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Report title " + (i + 1) });
    s.addText(c[1], { x: x + 0.15, y: 2.35, w: 2.0, h: 2.2, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "Report text " + (i + 1) });
    s.addText(c[2], { x: x + 0.15, y: 4.65, w: 2.0, h: 0.35, fontSize: 12, bold: true, color: C.accent2, margin: 0, isTextBox: true, objectName: "Report status " + (i + 1) });
  });
  s.addText("Keep a call in progress for live views; prepare a saved report and one finished call.", { x: 0.6, y: 5.45, w: 12.1, h: 0.45, fontSize: 15, bold: true, color: C.accent3, margin: 0, isTextBox: true, objectName: "Report tip" });
  s.addText("A summary is skipped when a call has too little conversation (silent test calls).", { x: 0.6, y: 5.95, w: 12.1, h: 0.4, fontSize: 13, color: C.accent5, margin: 0, isTextBox: true, objectName: "Report tip 2" });
  s.addNotes("WHAT IT SHOWS. MEI asked for supervisor reporting. Connect includes real-time dashboards, historical reports and listen-in; with conversational analytics the supervisor also sees what was said.\n\nREAL-TIME. Log in as demo.supervisor. Analytics and optimization, Real-time metrics, Agents table. Each row shows the agent's state (for example On contact), how long, routing profile and active contacts. The Queues table shows calls waiting and the oldest wait.\n\nLISTEN-IN. The eye icon appears only while the agent is on a call. Clicking it connects the supervisor's softphone; the supervisor must be Available with the softphone open. With a short call it is easy to miss: keep the call going while you click.\n\nHISTORY. Build and save one report before the meeting (contacts handled, abandoned, average queue time, transfers out, by queue and by agent) so it opens with one click. The 27% transfer figure MEI mentioned would be measured here once its definition is agreed.\n\nCONTACT SEARCH AND CALL ANALYSIS. Contact search lists every leg; opening a contact shows its attributes (master_call_id, department, language) and, for a finished call, the recording, the transcript, sentiment, the AI post-call summary in English or Spanish (AWS lists es-US as supported) and the automatic categories. Analysis takes a few minutes after the call ends, so use a call finished earlier. A summary is skipped when a call has too little conversation (INSUFFICIENT_CONVERSATION_CONTENT on silent test calls). Recordings, transcript, sentiment and summary belong to conversational analytics (tier 2 and 3 of the pricing).\n\nNOT DEMONSTRATED. Barge (joining the call) and scheduled reports. Standard, not tested. There is no separate AI quality-evaluation section in this demo.\n\nIF IT FAILS. Data appears a minute or two after a call; show the finished call prepared earlier.");
}

// 11. Run of show
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Run of show and checklist", { placeholder: "title" });
  const rows = [
    [hdr("Part"), hdr("Time"), hdr("Say or show")],
    [cell("Frame"), cell("1 min"), cell("Invented accounts, simulated iDMS, no MEI data")],
    [cell("1 Basic call", { bold: true }), cell("2 min"), cell("A call from MEI's phone; agent sees who it is")],
    [cell("2 Transfer", { bold: true }), cell("3 min"), cell("Transfer, then both legs with one call ID")],
    [cell("3 Disposition"), cell("1 min"), cell("The wrap-up form after a call (configured)")],
    [cell("4 AI agent", { bold: true }), cell("3 min"), cell("Call on speaker; recording as fallback")],
    [cell("5 Flows"), cell("2 min"), cell("Case 5: Redemptions wins over 9-15")],
    [cell("6 Reports"), cell("2 min"), cell("Real-time, listen-in, one finished call analysed")],
    [cell("7 Pricing"), cell("2 min"), cell("Platform cost, then suggested price (draft)")],
  ];
  s.addTable(rows, { x: 0.6, y: 1.5, w: 7.3, colW: [1.9, 1.0, 4.4], rowH: 0.55, border: BORDER });
  box(s, "Checklist card", "", 8.3, 1.5, 4.4, 5.0, "note");
  s.addText("Before the meeting", { x: 8.55, y: 1.65, w: 3.9, h: 0.4, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Checklist title" });
  bullets(s, "Checklist bullets", ["Account ID checked", "All users logged in, Available, mics allowed", "Each part run once by voice", "Wrap-up form saved end to end", "One finished call with recording, transcript, summary", "One saved historical report", "Video of the full run as fallback"], 8.55, 2.15, 3.9, 4.2, 14);
  s.addNotes("TIMING. About sixteen minutes. If the slot is cut, shorten part 3 to one sentence and part 5 to case 5 only. Keep parts 1, 2, 4 and 7.\n\nFRAME. Open with what the audience will see: invented accounts and a simulated lookup in place of iDMS. This prevents anyone mistaking the demo for an integration.\n\nORDER. The order follows a day in the contact center: a call arrives and the agent knows who it is (1), the call moves to another team without losing context (2), the agent closes it with an outcome (3); then what AI adds (4), how the rules are built (5), what the supervisor sees (6), and what it costs (7).\n\nFALLBACKS. Every part has one: the recorded video, the AI call recording, a finished call in Contact search and the saved report. PRICING. Two slides in the options deck (10 and 11): the AWS platform cost, then the suggested price, which is a draft.\n\nThe detailed runbook, with who logs in where and what to say, is docs/proposal/demo-runbook.md.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
})();
