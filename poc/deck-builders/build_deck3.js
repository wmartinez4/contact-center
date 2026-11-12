const pptxgen = require("pptxgenjs");
const SKILL = "/Users/willianmartinez/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/fe112ec4-93e2-448b-8146-17b065462965/740ff72a-525b-4b03-b948-01aba0ced011/skills/pptx";
const { applyTheme } = require(`${SKILL}/scripts/apply_theme.js`);

const THEME = {
  name: "Contact Center Neutral", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: "1F2A30", lt1: "FFFFFF", dk2: "3B4A54", lt2: "F2F4F5", accent1: "3E6E8E", accent2: "2E7D5B", accent3: "A9690F", accent4: "A04040", accent5: "6B7A84", accent6: "5B8C85", hlink: "3E6E8E", folHlink: "6B7A84" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Moving MEI's contact center to Amazon Connect (draft)";
const C = pres.SchemeColor;

// Slide status marks: native sections (visible in the slide sorter) plus a colored tag placed just
// above the slide, visible when editing and absent from slideshow, print and PDF export.
const TOTAL = 14, INTERNAL = new Set([10, 11, 12]);
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
const OUT = process.env.OUT || "/private/tmp/claude-501/-Users-willianmartinez--claude-spares-spare-AT5JJd/8122a2a7-74aa-4d4a-9206-3e8b2f6fd869/scratchpad/deck3.pptx";

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
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontSize: 30, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Contact center migration to Amazon Connect  |  Draft for discussion", options: { x: 0.6, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: C.accent5, margin: 0, isTextBox: true } } },
  ],
  slideNumber: { x: 12.1, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent5 },
});

const BORDER = { type: "solid", pt: 0.75, color: "D5DADD" };
const statusColor = (s) => ({ green: C.accent2, amber: C.accent3, red: C.accent4, blue: C.accent1 }[s]);
function card(slide, name, x, y, w, h, tint) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, objectName: name, fill: { color: tint || C.background2 }, line: { color: "D5DADD", width: 0.75 } });
}
function chip(slide, name, text, x, y, w, color) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h: 0.34, rectRadius: 0.17, objectName: name, fill: { color: statusColor(color), transparency: 85 }, line: { color: statusColor(color), width: 0.75 } });
  slide.addText(text, { x, y, w, h: 0.34, fontSize: 12, bold: true, color: statusColor(color), align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: name + " text" });
}
function hdr(text) { return { text, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 12, valign: "middle" } }; }
function cell(text, o) { return { text, options: Object.assign({ fontSize: 12, color: C.text1, valign: "middle" }, o || {}) }; }
function st(text, color) { return cell(text, { bold: true, color: statusColor(color) }); }
function bullets(s, name, items, x, y, w, h, size) {
  s.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })), { x, y, w, h, fontSize: size || 14, color: C.text1, valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true, objectName: name });
}
function sub(s, name, text, x, y, w) {
  s.addText(text, { x, y, w, h: 0.4, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: name });
}

// 1. Title
{
  const s = pres.addSlide({ masterName: "TITLE" });
  s.addText("Moving MEI's contact center to Amazon Connect", { placeholder: "title" });
  s.addText("Coverage of requirements, systems and payments, delivery, costs and demo\nDiscovery meeting  |  November 11, 2026  |  Draft for discussion", { placeholder: "body" });
  s.addNotes("PURPOSE. MEI asked what Amazon Connect would replace, what additional components are needed, and how we would deliver and support it. This deck answers those three questions for MEI's contact center and sets up the estimate and SOW.\n\nFOCUS. The contact center: inbound and outbound customer calls, routing, transfers and callbacks, supervisor reporting, optional AI agents, and the systems and payments the agents need. One question stays open about the 210 planned users: who takes or makes customer calls.\n\nBASIS. Everything comes from public AWS documentation and pricing pages (prices re-checked on November 10, 2026), MEI's emails, and our own planning assumptions, which are flagged where they appear. No MEI data is used and nothing is integrated with iDMS.\n\nTIMING. The slot is 10:30 to 11:30 CT. Spend about two minutes per slide on slides 3 to 6, keep the demo (slide 13) and the questions (slide 14). If the slot is shortened, skip slide 9 unless asked; show slides 10 and 11 (platform cost, then the suggested price) at the end of the demo, as its pricing step. Slide 12 (operations cost and support fee) is internal only: do not show it unless the client asks about support.");
}

// 2. Today
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Where MEI is today", { placeholder: "title" });
  const stats = [
    ["210", "planning users", "123 standard, 85 contact center, 2 premium. Who takes customer calls: to confirm"],
    ["~27%", "Collections transfer rate", "Historical figure, to validate"],
    ["5 + 3", "routing groups", "Delinquency 0, 1-8, 9-15, 16-30, 31+ plus Redemptions, OFR/Skip, EPD"],
    ["EN / ES", "bilingual routing", "Specialized status takes precedence"],
  ];
  stats.forEach((d, i) => {
    const x = 0.6 + (i % 2) * 3.55, y = 1.6 + Math.floor(i / 2) * 2.55;
    card(s, "Stat card " + (i + 1), x, y, 3.35, 2.3);
    s.addText(d[0], { x: x + 0.25, y: y + 0.2, w: 2.9, h: 0.9, fontSize: 44, bold: true, color: C.accent1, margin: 0, isTextBox: true, valign: "middle", objectName: "Stat value " + (i + 1) });
    s.addText(d[1], { x: x + 0.25, y: y + 1.1, w: 2.9, h: 0.35, fontSize: 14, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Stat label " + (i + 1) });
    s.addText(d[2], { x: x + 0.25, y: y + 1.45, w: 2.9, h: 0.75, fontSize: 12, color: C.accent5, margin: 0, isTextBox: true, valign: "top", objectName: "Stat note " + (i + 1) });
  });
  card(s, "Systems panel", 7.9, 1.6, 4.8, 5.05, C.background1);
  sub(s, "Systems title", "Systems in play", 8.2, 1.8, 4.2);
  const items = [["Zultys MX 18.4", "Supported by BrevAll"], ["iDMS / DealerSocket", "Account identification and routing"], ["Text-to-Pay", "Existing option to preserve"], ["Telephony carriers", "Numbers and minutes: to confirm"], ["Zultys 19 / AI Receptionist", "Upgrade under evaluation"]];
  items.forEach((d, i) => {
    const y = 2.4 + i * 0.84;
    s.addText(d[0], { x: 8.2, y, w: 4.2, h: 0.34, fontSize: 14, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "System " + (i + 1) });
    s.addText(d[1], { x: 8.2, y: y + 0.34, w: 4.2, h: 0.34, fontSize: 12, color: C.accent5, margin: 0, isTextBox: true, objectName: "System note " + (i + 1) });
  });
  s.addNotes("WHERE THE NUMBERS COME FROM. All figures are from Jacob Long's Nov 6 email. 210 users is a planning baseline (123 standard, 85 contact center, 2 premium) and the active-user review is still open.\n\nTHE OPEN QUESTION ABOUT USERS. The email lists the areas Finance/Collections, Corporate, Sales and Service. We do not know how many of the 210 take or make customer calls. The answer matters for sizing: Amazon Connect is billed by usage, not per seat, so it does not change the per-minute price, but it changes total minutes, the concurrent-call quota we must request and the migration and training effort.\n\nTHE 27%. A September 30 vendor review reported about 27% of Collections calls transferred. Jacob calls it a historical reference to validate. We do not know how a transfer was counted. Reducing unnecessary transfers is a stated goal, so the definition matters.\n\nROUTING GROUPS. Five delinquency buckets plus three specialized statuses, with the specialized status winning over delinquency. We do not know what OFR stands for or whether there are more statuses.\n\nSYSTEMS. iDMS/DealerSocket is central: routing by delinquency depends on reading account data from it. If iDMS has no usable interface, no platform can route by delinquency automatically. Text-to-Pay must be preserved. The carriers, numbers and minutes are unknown and decide the porting plan. Zultys 19 is an alternative under evaluation, and MEI says its AI workflows are requirements under evaluation, not something operating today.");
}

// 3. Bottom line
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Bottom line: Amazon Connect can run MEI's contact center", { placeholder: "title" });
  const cols = [
    ["Call handling", "Routing, transfers, callbacks", "Strong fit", "green", ["English and Spanish routing", "Delinquency and special-status rules", "Supervisor views, recordings and AI summaries"]],
    ["AI self-service", "Bilingual voice agent", "Working in a demo", "blue", ["English and Spanish; switches language on request", "Answers balance and due date", "Hands over to a person with context"]],
    ["Systems and payments", "iDMS, Text-to-Pay, pay by phone", "Depends on MEI", "amber", ["iDMS access decides account-based routing", "Text-to-Pay must be preserved", "Pay by phone needs a processor and PCI design"]],
  ];
  cols.forEach((c, i) => {
    const x = 0.6 + i * 4.15, y = 1.55, w = 3.85, h = 3.75;
    card(s, "Column card " + (i + 1), x, y, w, h);
    s.addText(c[0], { x: x + 0.25, y: y + 0.2, w: w - 0.5, h: 0.4, fontSize: 20, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Column title " + (i + 1) });
    s.addText(c[1], { x: x + 0.25, y: y + 0.6, w: w - 0.5, h: 0.3, fontSize: 12, color: C.accent5, margin: 0, isTextBox: true, objectName: "Column sub " + (i + 1) });
    chip(s, "Chip " + (i + 1), c[2], x + 0.25, y + 1.0, 2.2, c[3]);
    bullets(s, "Column bullets " + (i + 1), c[4], x + 0.25, y + 1.5, w - 0.5, 2.1, 14);
  });
  s.addShape(pres.ShapeType.rect, { x: 0.6, y: 5.55, w: 12.1, h: 1.1, fill: { color: C.text1 }, line: { color: C.text1, width: 0 }, objectName: "Conclusion banner" });
  s.addText("Amazon Connect covers the contact-center requirements MEI listed. What we need from MEI: iDMS access, how customers pay today, and call volumes.", { x: 0.9, y: 5.55, w: 11.5, h: 1.1, fontSize: 18, bold: true, color: C.background1, valign: "middle", margin: 0, isTextBox: true, objectName: "Conclusion text" });
  s.addNotes("WHY WE SAY THIS. The three areas have different strengths of evidence.\n\nCALL HANDLING (strong). Queues, routing profiles, contact flows, callbacks, transfers and supervisor monitoring are documented, mature features. We built and tested a real inbound flow in a test environment: language choice, a simulated account lookup, special-status-first routing and delivery to an agent. A transferred call keeps one call ID across all its legs; we proved it on real calls.\n\nAI SELF-SERVICE (working in a demo). We built a voice agent on Amazon Nova 2 Sonic, Amazon's speech-to-speech model, which is included in the Connect Customer voice price. On a real call it held a multi-turn conversation in English: balance, due date, how to pay, goodbye. It also switches between English and Spanish when the caller asks, keeping the account, and hands over to a person with the reason, a summary and the language. Scripted test calls on November 10 passed 8 of 8, including the hand-over and the language switch. It is a demo with invented accounts, not a measured production result.\n\nSYSTEMS AND PAYMENTS (depends on MEI). Connect can call any system through a Lambda function, but we have not seen iDMS. Whether iDMS offers an interface, and what data we can read or write, decides how much of the account-based routing is possible. Text-to-Pay is an existing option that must be preserved. Taking payments by phone is possible on Connect but needs MEI's payment processor and a PCI design. Slides 5 and 6 go into this.\n\nTHE BANNER. The three asks are what turn an evaluation into an estimate.");
}

// 4. Coverage
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Requirements: call handling and AI", { placeholder: "title" });
  const rows = [
    [hdr("Requirement"), hdr("How Amazon Connect covers it"), hdr("Status")],
    [cell("English and Spanish routing"), cell("Contact flows with a language attribute and bilingual queues"), st("Native", "green")],
    [cell("Collections by delinquency; special status first"), cell("Lookup returns status and days past due; flow checks status first"), st("Native + iDMS link", "green")],
    [cell("Sales and Service routing (vehicle service, insurance, titles, dealers)"), cell("Department menus or caller recognition, routed to queues"), st("Native", "green")],
    [cell("Transfers and callbacks with context"), cell("Quick connects, queue transfers and queued callbacks; one call ID across every leg"), st("Tested on a call", "green")],
    [cell("Supervisor reporting and monitoring"), cell("Real-time and historical metrics, listen-in; recordings, transcript, sentiment and AI summary (EN/ES)"), st("Tested on a call", "green")],
    [cell("Call outcome codes (disposition)"), cell("Wrap-up form after each call; the code is saved on the call and reported"), st("Configured", "amber")],
    [cell("Caller recognition and verification"), cell("Known numbers matched and greeted by name (simulated data); verification against iDMS"), st("Demo + iDMS", "amber")],
    [cell("Bilingual AI voice agent"), cell("Nova 2 Sonic: English and Spanish, switches language, hands over to a person with context"), st("Tested in a demo", "blue")],
  ];
  s.addTable(rows, { x: 0.6, y: 1.5, w: 12.1, colW: [4.4, 5.9, 1.8], rowH: 0.56, border: BORDER });
  s.addNotes("HOW TO READ. Green means documented and standard. Amber means it depends on something we have not seen yet. Blue means optional and shown in a demo.\n\nLANGUAGE AND DELINQUENCY ROUTING. Flows set a language attribute from the caller's choice or the account, then call a lookup that returns the special status and days past due; the flow routes on the special status first, which is how MEI's precedence rule is met. We built and tested this in a test environment with invented accounts.\n\nSALES AND SERVICE. The same mechanism: a menu or a lookup chooses a queue. The business rules (who calls, what they hear, who answers) must come from MEI. This was in MEI's email and we have not yet demonstrated it.\n\nTRANSFERS AND CALLBACKS. Both are native and both were tested on real calls. Each transfer creates a new contact in Connect, so we set one call ID on the first leg and carry it through; context travels as contact attributes. It reached the second leg after a consult transfer, a direct transfer and a callback.\n\nSUPERVISOR REPORTING. Real-time dashboards (queue and agent state), historical reports and listen-in. We tested the dashboard and listen-in on a live call. Supervisors can open the recording, transcript, sentiment and an AI summary of each call, in English and Spanish; the summary is skipped when a call has too little conversation. Joining the call and scheduled reports are standard but were not tested.\n\nDISPOSITION. When a call ends the agent sees a wrap-up form (outcome such as promise to pay, payment arrangement, callback requested, dispute; follow-up; resolved; summary and notes) and it is saved on the call for reports. It is configured; say so unless the end-to-end save has been confirmed. Separately, the analysis flags what was actually said (automatic categories), so supervisors can spot mismatches with the recorded outcome.\n\nRECOGNITION AND VERIFICATION. In the demo, a known caller is recognized by phone number (caller ID), skips the menus and hears a personal greeting in the right language; unknown callers get a language menu and are asked for an account number. The data is simulated. In production this lookup reads iDMS, and the verification questions and rules are MEI's to define.\n\nAI VOICE AGENT. Amazon Nova 2 Sonic through a Lex bot, English and Spanish (US) voices. Tested on a real call in English, multi-turn, and by scripted calls for the language switch and the hand-over. It only informs; it takes no payments. Escalation hands the caller to the routing queues; the agent sees the reason, an AI summary, the account, the language and the queue. If the AI cannot continue, the caller goes to a person instead of being hung up on.");
}

// 5. Systems and payments: what Connect offers
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Systems and payments: what Amazon Connect offers", { placeholder: "title" });
  const rows = [
    [hdr("Need"), hdr("What Amazon Connect offers"), hdr("Status")],
    [cell("iDMS / DealerSocket"), cell("A function reads the account (status, days past due) and can write back notes or promises to pay"), st("Needs iDMS API", "red")],
    [cell("Agent screen and CRM"), cell("Customer profile and call panel shown when the call rings (in the demo); an existing CRM page can open beside it"), st("Native + design", "green")],
    [cell("Phone numbers and carriers"), cell("Local and toll-free numbers ported into Connect; transfers out to any number"), st("Native", "green")],
    [cell("Pay by phone in the IVR"), cell("Keypad card entry, encrypted in the flow and sent to the processor; agent never hears it"), st("Needs processor", "amber")],
    [cell("Agent-assisted payment"), cell("Agent sends the caller to the secure payment step, then the call returns"), st("To design", "amber")],
    [cell("Payment links (Text-to-Pay)"), cell("Keep today's service, or send the link by SMS from Connect"), st("To confirm", "amber")],
    [cell("Payment arrangements"), cell("Rules, approvals, update in iDMS and confirmation to the customer"), st("MEI rules", "red")],
  ];
  s.addTable(rows, { x: 0.6, y: 1.5, w: 12.1, colW: [3.2, 7.1, 1.8], rowH: 0.62, border: BORDER });
  s.addNotes("WHY THIS SECTION. MEI's requirements include account information, payments and payment arrangements, and Text-to-Pay must be preserved. Before estimating we must know what the contact center has to connect to and whether it must take payments itself.\n\niDMS. Connect calls external systems through AWS Lambda functions from the contact flow. If iDMS (DealerSocket) offers an API or a data feed, the same function that simulates iDMS in our demo would read the real account. Writing back (notes, promises to pay, payments) depends on what iDMS allows. Any DealerSocket fee for API use is unknown.\n\nAGENT SCREEN. When a call rings, the agent workspace can show the data the flow collected (name, account, status, days past due, language). If MEI uses a CRM, it can open beside the softphone or embed the softphone. The demo shows who is calling in its first step.\n\nNUMBERS. Existing numbers can be ported to Connect; porting takes two to four weeks. Toll-free per-minute rates must be confirmed before quoting.\n\nPAY BY PHONE. Connect's 'Store customer input' block can encrypt keypad digits with a key MEI controls, so the card number is not stored or logged in clear; a function hands it to MEI's payment processor. AWS lists Amazon Connect as a PCI DSS compliant service, but the whole design (processor, encryption, what agents hear, what is recorded) must be reviewed for PCI scope. Third-party pay-by-phone services that integrate with Connect also exist.\n\nAGENT-ASSISTED PAYMENT. The usual pattern is that the agent moves the caller to a secure payment step and the call returns to the agent afterwards, so the agent never hears the card number. It needs design and testing; we have not built it.\n\nTEXT-TO-PAY. We do not know which vendor runs it. It can stay as it is. If the link were sent from Connect, SMS costs $0.014 per message plus carrier fees and needs US carrier registration of the number, which can take up to 15 business days.\n\nPAYMENT ARRANGEMENTS. Business rules, approvals and the confirmation to the customer must come from MEI. Connect only executes them.");
}

// 6. Systems and payments: questions
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Systems and payments: questions for MEI", { placeholder: "title" });
  const qs = [
    ["Paying today", "How do customers pay: with an agent, in the phone menu, by link, or all three? Card, ACH or debit?"],
    ["Processor", "Which processor or gateway, and does it offer an API?"],
    ["Text-to-Pay", "Which vendor runs it, who sends the link, and how is the payment posted in iDMS?"],
    ["PCI today", "Do agents hear card numbers? Who owns PCI compliance?"],
    ["iDMS", "DealerSocket: API or data feed? Read only, or can we write notes and promises to pay?"],
    ["Agent screen", "What do agents look at when a call arrives? Is there a CRM?"],
    ["Numbers", "Which carriers, how many numbers, which are toll-free?"],
    ["Arrangements", "Payment arrangements: who approves, what limits, how is the customer told?"],
  ];
  qs.forEach((q, i) => {
    const col = i % 4, row = Math.floor(i / 4);
    const x = 0.6 + col * 3.075, y = 1.55 + row * 2.6, w = 2.85, h = 2.35;
    card(s, "Question card " + (i + 1), x, y, w, h, row === 0 ? C.background2 : C.background1);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.2, y: y + 0.2, w: 0.45, h: 0.45, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: "Question circle " + (i + 1) });
    s.addText(String(i + 1), { x: x + 0.2, y: y + 0.2, w: 0.45, h: 0.45, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Question number " + (i + 1) });
    s.addText(q[0], { x: x + 0.8, y: y + 0.2, w: w - 1.0, h: 0.45, fontSize: 15, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "Question title " + (i + 1) });
    s.addText(q[1], { x: x + 0.2, y: y + 0.85, w: w - 0.4, h: 1.35, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "Question text " + (i + 1) });
  });
  s.addNotes("HOW TO USE. Ask these in the meeting and write down who owns each answer. We do not assume any of them.\n\n1. HOW CUSTOMERS PAY. Decides whether the contact center must take payments at all, and whether by agent, by phone menu or only by link.\n2. PROCESSOR. A pay-by-phone flow sends the payment to MEI's processor; without an API there is no automated payment.\n3. TEXT-TO-PAY. It must be preserved. We need to know the vendor, who triggers the link (agent, system, AI) and how the payment reaches iDMS.\n4. PCI. If agents hear card numbers today, a secure payment step reduces PCI scope. MEI's compliance owner must take part.\n5. iDMS. The single biggest dependency: routing by account, verification, balances and payment arrangements all read or write iDMS.\n6. AGENT SCREEN. What the agent sees when the call rings; it decides whether we show data in the Connect workspace, open a CRM page, or both.\n7. CARRIERS AND NUMBERS. The porting plan and the toll-free rates depend on it.\n8. PAYMENT ARRANGEMENTS. MEI listed them as a requirement with business rules and approvals. The rules are MEI's.");
}

// 7. KPIs
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Measuring MEI's goals", { placeholder: "title" });
  const rows = [
    [hdr("MEI goal"), hdr("How it is measured in Amazon Connect"), hdr("Status")],
    [cell("Fewer unnecessary transfers"), cell("Transfer rate from contact records, by queue and agent"), st("Standard data", "green")],
    [cell("Wait times, abandonment"), cell("Queue metrics in real-time and historical reports"), st("Native", "green")],
    [cell("Callback completion"), cell("Callback contacts and their outcome, per queue"), st("Native", "green")],
    [cell("Repeat contacts"), cell("Contact search and export, grouped by customer number"), st("Custom report", "amber")],
    [cell("Self-service completion"), cell("Outcome attribute set by the AI or IVR flow, reported by us"), st("Custom report", "amber")],
    [cell("Supervisor view"), cell("Real-time dashboard and listen-in tested; reports can be scheduled"), st("Tested on a call", "green")],
    [cell("Call outcomes"), cell("Disposition code saved on each call, plus automatic categories from the analysis"), st("Configured", "amber")],
  ];
  s.addTable(rows, { x: 0.6, y: 1.5, w: 12.1, colW: [3.4, 6.9, 1.8], rowH: 0.62, border: BORDER });
  s.addNotes("WHY THIS SLIDE EXISTS. Jacob's email lists the goals: reduce unnecessary transfers, improve wait times, abandonment, repeat contacts, self-service completion and callback completion, and asks for supervisor reporting. We need to show how each would be measured, because a goal that cannot be measured cannot be improved.\n\nNATIVE. Queue wait time, abandonment, agent and queue states, and callback activity are standard metrics in the Amazon Connect dashboards and reports, in real time and historically. Supervisors can listen in on calls; we tested the dashboard and the listen-in on a live call.\n\nSTANDARD DATA. The transfer rate is not a button; it is computed from contact records, which mark transferred contacts and link the legs. We can report it by queue and agent. The 27% baseline needs a definition from MEI to be comparable.\n\nCUSTOM REPORT. Repeat contacts and self-service completion are not standard metrics. Repeat contacts need grouping contact records by customer number over a period. Self-service completion needs the AI or IVR flow to set an outcome attribute, which we then report. Both are small, but they are work, and belong in the SOW.\n\nDEMO. We will show the real-time dashboard and a report during the demo if time allows.");
}


// 8. Delivery
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("How we would deliver and support it", { placeholder: "title" });
  const xs = [0.6, 2.66, 4.72, 6.78, 8.84, 10.9], w = 1.8;
  const phases = [["Discover and design", "3-4 weeks"], ["Build and integrate", "4-6 weeks"], ["Test and parallel run", "3-4 weeks"], ["Train and pilot", "2 weeks"], ["Cutover", "number porting 2-4 weeks"], ["Hypercare", "2-4 weeks"]];
  phases.forEach((p, i) => {
    card(s, "Phase box " + (i + 1), xs[i], 1.55, w, 1.3, C.background2);
    s.addText(p[0], { x: xs[i] + 0.08, y: 1.6, w: w - 0.16, h: 0.7, fontSize: 14, bold: true, color: C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Phase name " + (i + 1) });
    s.addText(p[1], { x: xs[i] + 0.08, y: 2.3, w: w - 0.16, h: 0.5, fontSize: 12, color: C.accent5, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Phase time " + (i + 1) });
  });
  s.addText("Planning assumption: about 3 to 5 months end to end. To be refined after discovery.", { x: 0.6, y: 3.0, w: 12.1, h: 0.4, fontSize: 14, bold: true, color: C.accent3, margin: 0, isTextBox: true, objectName: "Duration note" });
  card(s, "MEI card", 0.6, 3.6, 3.9, 3.1, C.background1);
  sub(s, "MEI title", "MEI provides", 0.85, 3.75, 3.4);
  bullets(s, "MEI bullets", ["iDMS access and an owner", "Business rules and approvals", "Number porting authorization", "Contracts and call volumes"], 0.85, 4.25, 3.4, 2.3, 14);
  card(s, "We card", 4.7, 3.6, 3.9, 3.1, C.background1);
  sub(s, "We title", "We provide", 4.95, 3.75, 3.4);
  bullets(s, "We bullets", ["Design, build and testing", "iDMS and payment integrations", "Training and cutover plan", "Support after go-live"], 4.95, 4.25, 3.4, 2.3, 14);
  card(s, "Support card", 8.8, 3.6, 3.9, 3.1, C.background1);
  sub(s, "Support title", "Support, to define", 9.05, 3.75, 3.4);
  bullets(s, "Support bullets", ["Hours and response times", "First-level support owner", "Role of BrevAll", "Monthly review of metrics"], 9.05, 4.25, 3.4, 2.3, 14);
  s.addNotes("WHY THIS SLIDE. Jacob asked twice how our team would deliver and support the solution, and the SOW must cover integrations, migration, testing, training, support, responsibilities and timing. This is the outline.\n\nTHE PHASES. 1) Discover and design: confirm requirements, iDMS access, routing rules, the agent screen and how payments are taken. 2) Build and integrate: Amazon Connect instance, flows, queues, the iDMS lookup, the agent screen, call IDs and, if MEI needs it, the payment flow. 3) Test and parallel run: run Connect next to the current system on test and then limited live traffic. 4) Train and pilot: train agents and supervisors, then a pilot group. 5) Cutover: move the Collections numbers to Amazon Connect. Number porting takes two to four weeks and is requested at most thirty days ahead, so it is started during testing. 6) Hypercare: close monitoring after go-live.\n\nTHE DURATIONS. These are our planning assumptions, not quotes and not from a source. Discover and design is three to four weeks because it is staffed by one or two people on our side and its calendar time depends on how fast MEI names an owner, gives iDMS access and answers on statuses, verification and payment rules; the clock starts when those are in place. In week one we also start the AWS quota requests and the number inventory and porting authorization, which take weeks. The total of about three to five months depends on iDMS access, the number of agents, the number of numbers to port and how many rules MEI must still define. They will change with discovery data.\n\nRESPONSIBILITIES. MEI must provide iDMS access, define business rules (verification, payment arrangements, approvals), authorize number porting and share contracts and volumes. We provide design, build, testing, integrations, training, cutover plan and support. BrevAll, which supports Zultys today, will be needed for the coexistence period and for the call routing that remains on Zultys.\n\nSUPPORT. Hours, response times and who is the first level are open and need MEI's expectations. We should not offer a service level before we know them.\n\nWHAT WE DO NOT KNOW. The cost of the parallel run and any early-termination terms in the Zultys, BrevAll or carrier contracts.");
}

// 9. Components
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Components beyond the core platform", { placeholder: "title" });
  const rows = [
    [hdr("Need"), hdr("Options"), hdr("Status")],
    [cell("iDMS integration"), cell("Custom function that reads and writes account data"), st("Depends on iDMS", "red")],
    [cell("Payments by phone"), cell("MEI's payment processor through a secure flow, or a pay-by-phone partner that works with Connect"), st("To confirm", "red")],
    [cell("Text-to-Pay and SMS"), cell("Keep the current service; Amazon Connect SMS needs carrier registration"), st("To confirm", "red")],
    [cell("Agent screen / CRM"), cell("Connect agent workspace; MEI's CRM page beside it if one exists"), st("Native + design", "green")],
    [cell("AI voice agent"), cell("Nova 2 Sonic (native, tested in demo); Deepgram plug-in; ElevenLabs voice (live agent in limited availability)"), st("Optional", "blue")],
    [cell("Collections-specialist AI"), cell("Vendors focused on compliant collections conversations"), st("Unverified with Connect", "red")],
  ];
  s.addTable(rows, { x: 0.6, y: 1.5, w: 12.1, colW: [3.2, 6.5, 2.4], rowH: 0.65, border: BORDER });
  s.addNotes("HOW TO USE. This answers 'what additional components would be needed'.\n\nIDMS INTEGRATION. Required for account-based routing, verification, balances and payment arrangements. We build a function that calls whatever interface iDMS offers. We do not know what that is.\n\nPAYMENTS BY PHONE. Only if MEI wants the contact center to take payments. Either a secure flow that hands encrypted card data to MEI's processor, or a pay-by-phone partner. Both need a PCI review.\n\nTEXT-TO-PAY AND SMS. We must see how Text-to-Pay works today. If SMS is sent through Amazon Connect, US carriers require registration of the sending number, which can take up to 15 business days.\n\nAGENT SCREEN. The Connect agent workspace shows caller data from the flow. If MEI has a CRM, its page can open beside the softphone.\n\nAI VOICE. Optional. Nova 2 Sonic is included in the Connect Customer voice price and is what our demo uses. Deepgram can be selected as a speech provider. ElevenLabs on Connect is in limited availability and needs enabling by AWS and ElevenLabs; it costs about 8 cents per minute plus the language model and telephony. We already use ElevenLabs in the demo in a simpler way: the fixed messages are audio generated with one of its voices and imported into Amazon Connect as prompts, which needs no integration.\n\nCOLLECTIONS-SPECIALIST AI. Vendors exist that focus on automotive collections conversations. We could not verify that any integrates with Amazon Connect; it is a conversation, not a plan.");
}

// 10. Platform cost (AWS list prices)
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Platform cost (AWS list prices)", { placeholder: "title" });
  const rows = [
    [hdr("Level"), hdr("What it includes"), hdr("Voice / min"), hdr("With US telephony"), hdr("Per agent a month, 2 / 3 / 4 h a day")],
    [cell("1. Normal flow\n(Connect Customer Basic)", { bold: true }), cell("IVR, routing by days past due and special status, queues, transfers, queue callback*, recording, reports"), cell("$0.018"), cell("$0.0215"), cell("~$52 / ~$77 / ~$103", { bold: true, color: C.accent1 })],
    [cell("2. Normal flow + analytics\n(Basic + conversational analytics)", { bold: true }), cell("Adds transcript, sentiment, AI call summary, automatic categories and keyword search"), cell("$0.033"), cell("$0.0365"), cell("~$88 / ~$131 / ~$175", { bold: true, color: C.accent1 })],
    [cell("3. Everything included\n(Connect Customer)", { bold: true }), cell("Adds the AI voice agent (Nova Sonic), generative voices, automated evaluations and wait-time estimates"), cell("$0.038"), cell("$0.0415"), cell("~$100 / ~$149 / ~$199", { bold: true, color: C.accent1 })],
  ];
  s.addTable(rows, { x: 0.6, y: 1.35, w: 12.1, colW: [2.9, 4.5, 1.1, 1.4, 2.2], rowH: [0.6, 0.72, 0.72, 0.72], border: BORDER });
  card(s, "Prices card", 0.6, 4.35, 5.5, 2.15, C.background1);
  sub(s, "Prices title", "Other list prices", 0.85, 4.45, 5.0);
  bullets(s, "Prices bullets", ["US telephony: $0.0022 in, $0.0048 out per min", "Local number: $0.03 a day", "Outbound campaigns: $0.045 / min (instead of voice)", "Text message: $0.014 each + carrier fee", "Third-party AI voice agent: +$0.01 / min"], 0.85, 4.95, 5.0, 1.5, 12);
  card(s, "Billing card", 6.3, 4.35, 6.4, 2.15, C.background1);
  sub(s, "Billing title", "How it is billed", 6.55, 4.45, 5.9);
  bullets(s, "Billing bullets", ["The level applies to the whole AWS account, not to one flow", "Per second over the whole call (IVR, queue, agent); telephony 60 s minimum; no seat licence", "No separate charge for the AI agent; level 2 to 3 is +$0.005/min (~$18 per agent a month)", "AI runs on Nova 2 Sonic. Nova 2.5 is in Bedrock, but Lex accepts only Nova 2 today; switching later is a configuration change"], 6.55, 4.9, 5.9, 1.6, 12);
  s.addText("Assumptions: 20 working days a month; mixed US telephony about $0.0035/min; billed minutes include IVR, queue and transfers. Hours per agent are an assumption; no MEI volumes yet. *Queue callback in Basic: to confirm. AWS list prices read November 10, 2026; toll-free per-minute rates to confirm.", { x: 0.6, y: 6.55, w: 12.1, h: 0.45, fontSize: 11, color: C.accent5, margin: 0, isTextBox: true, valign: "top", objectName: "Price note" });
  s.addNotes("WHY NO TOTAL. MEI has not given volumes, minutes or peaks, so any total would be invented. These are AWS list prices read on the Connect Customer pricing page and its appendix on November 10, 2026, and must be re-verified before quoting. This slide is our cost basis; the next slide turns it into a suggested price. The figures per agent show how the cost scales, not a quote.\n\nTHREE LEVELS. The level is chosen per AWS account, not per flow: AWS states that Connect Customer charges apply to all channel usage in the account. It is not possible to pay the Basic rate on some calls and the Customer rate on others inside one account.\n\n1) NORMAL FLOW (Connect Customer Basic, $0.018 a minute). IVR, routing by days past due and special status, queues, transfers, recording and reports. This is what MEI does today without AI. The AWS appendix lists customer callback as not included in Basic; we need to confirm whether that means the queue callback used in the demo.\n\n2) NORMAL FLOW PLUS ANALYTICS (Basic plus conversational analytics, $0.018 + $0.015 = $0.033 a minute). Adds transcript, sentiment, the AI post-call summary (English and Spanish; AWS lists es-US as supported), automatic categories (rules on what was said) and keyword search. Sentiment and categories have no price line of their own: they come with conversational analytics. A summary is skipped when a call has too little conversation.\n\n3) EVERYTHING INCLUDED (Connect Customer, $0.038 a minute). Adds the AI voice agent (Amazon Nova Sonic), generative voices, automated evaluations and wait-time estimates. The AI flow is not a separate charge: a minute handled by the AI agent costs the same as any other voice minute plus telephony. Its value is the agent time it saves, not a lower Connect price. Going from level 2 to level 3 costs about $0.005 more per minute, roughly $18 per agent per month at three contact hours a day. Performance evaluations on Basic would cost $12 per agent per month; they are included in level 3.\n\nPER AGENT PER MONTH. Contact hours a day times 20 days times 60 minutes times the rate with telephony. At 2, 3 and 4 hours: level 1 about $52, $77 and $103; level 2 about $88, $131 and $175; level 3 about $100, $149 and $199. For reference, 85 agents at level 3 and three hours is about $12,700 a month, and 210 agents about $31,400; the hours per agent are our assumption and must be validated. Billed minutes include the IVR, the queue and every transfer leg, so they exceed talk time.\n\nBILLING RULES. Voice is billed per second with a 10-second minimum; telephony per second with a 60-second minimum, which matters for many short outbound attempts. Local numbers are $0.03 a day. Outbound campaigns are $0.045 a minute instead of the voice rate. Text messages for payment links are $0.014 each plus the carrier fee. A third-party AI voice agent adds $0.01 a minute. ElevenLabs, if used for live voice, is billed separately (about 8 cents a minute plus the language model). There is no per-seat licence and no minimum commitment; a volume discount would have to be negotiated with AWS.\n\nAI MODEL NOTE. The demo uses Nova 2 Sonic. Nova 2.5 Sonic exists in Amazon Bedrock, but Amazon Lex, which is how Connect runs the voice agent, accepted only Nova 2 Sonic as of November 10, 2026. Moving to a newer model later is a configuration change, not a rebuild. Re-verify before promising dates.\n\nNOT IN THIS SLIDE. Implementation labor, number porting, the parallel run with the current system, third-party costs, the support plan and payment-processor fees. Toll-free per-minute rates were not found on the AWS pages and must be confirmed, because collections lines are often toll-free.\n\nSource of the figures: docs/proposal/modelo-de-costos.md, section 3b.");
}

// 11. Suggested pricing for MEI (draft)
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Suggested pricing for MEI (draft)", { placeholder: "title" });
  const rows = [
    [hdr("Level"), hdr("AWS cost per agent per month at 3 h"), hdr("Suggested price at 3 h"), hdr("Suggested range at 2 to 4 h")],
    [cell("1. Normal flow", { bold: true }), cell("~$77"), cell("~$110", { bold: true, color: C.accent1 }), cell("~$75 to ~$145")],
    [cell("2. Normal flow + analytics", { bold: true }), cell("~$131"), cell("~$185", { bold: true, color: C.accent1 }), cell("~$125 to ~$250")],
    [cell("3. Everything included", { bold: true }), cell("~$149"), cell("~$215", { bold: true, color: C.accent1 }), cell("~$145 to ~$285")],
  ];
  s.addTable(rows, { x: 0.6, y: 1.35, w: 12.1, colW: [3.6, 3.2, 2.6, 2.7], rowH: [0.5, 0.5, 0.5, 0.5], border: BORDER });
  s.addText("Suggested price = AWS cost divided by 0.70 (30% margin on price), rounded to $5. This is the per-agent-per-month figure MEI can compare with what it pays today.", { x: 0.6, y: 3.45, w: 12.1, h: 0.5, fontSize: 13, bold: true, color: C.accent3, margin: 0, isTextBox: true, valign: "top", objectName: "Margin note" });
  const cols = [
    ["Also charged", ["Managed service: fixed monthly fee for standard office-hours support (see the next slide); amount to validate", "Implementation (SOW): discovery, iDMS, flows, AI agent, number porting, testing, training, parallel run. Quoted after discovery"]],
    ["Not included, passed through", ["Toll-free minutes (rate to confirm) and telephony beyond the assumed mix", "SMS for payment links; third-party voice (ElevenLabs)", "Payment processor, PCI work, iDMS / DealerSocket fees", "AWS support plan"]],
    ["Commercial terms (proposal)", ["12-month minimum term; price review once real volumes are known (about 90 days)", "Per-agent price bundles AWS usage on our account. Alternative: MEI's own AWS account, usage billed by AWS at cost, plus the managed fee", "Any AWS volume discount shared by agreement"]],
  ];
  cols.forEach((c, i) => {
    const x = 0.6 + i * 4.15, w = 3.85;
    card(s, "Terms card " + (i + 1), x, 4.0, w, 2.5, C.background1);
    s.addText(c[0], { x: x + 0.2, y: 4.1, w: w - 0.4, h: 0.38, fontSize: 16, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Terms title " + (i + 1) });
    bullets(s, "Terms bullets " + (i + 1), c[1], x + 0.2, 4.55, w - 0.4, 1.9, 11);
  });
  s.addText("Draft for internal review: margin, fees and terms are proposals to adjust. Prices are illustrative until MEI shares volumes; the current cost per agent for Zultys, BrevAll and carriers is still to be requested.", { x: 0.6, y: 6.55, w: 12.1, h: 0.45, fontSize: 11, color: C.accent5, margin: 0, isTextBox: true, valign: "top", objectName: "Draft note" });
  s.addNotes("DRAFT FOR INTERNAL REVIEW. This slide is a proposal for Willian to adjust before it is shown. Every number here is built from the previous slide plus assumptions that are ours, not facts about MEI. Do not present it as final.\n\nHOW THE PRICE IS BUILT. Suggested price per agent per month = AWS cost per agent per month (previous slide) divided by 0.70, which is a 30% gross margin on the price, rounded to the nearest $5. At 3 contact hours a day: level 1 $77 becomes about $110; level 2 $131 becomes about $185; level 3 $149 becomes about $215. At 2 and 4 hours: level 1 about $75 to $145; level 2 about $125 to $250; level 3 about $145 to $285.\n\nWHY 30%. Managed-service margins on usage-based cloud services are typically in the range of 25% to 40% (this range is a general rule of thumb, not a sourced figure). We pick 30% because the usage itself is close to a pass-through with little differentiation, and the service value is carried separately by the managed-service fee and the implementation. MEI will compare the per-agent number with Zultys plus BrevAll plus carriers, so a lean number helps. If Willian wants more room, 35% gives about $120, $200 and $230 at 3 hours; 25% gives about $105, $175 and $200 for levels 1, 2 and 3.\n\nMANAGED SERVICE FEE. We propose a separate fixed monthly fee, not folded into the per-agent price, so MEI sees what it pays for usage and what it pays for service. It would cover monitoring, changes to flows, queues and prompts, user administration, reports and a defined number of support hours with response times. The next slide builds a suggested amount (about $9,500 a month for the demo scope) from estimated hours and rates; there is no published benchmark for the hours, so validate it against real tickets after go-live. If a single price is preferred, the fee can be folded into the per-agent price at a minimum number of agents.\n\nIMPLEMENTATION. One-time, under the SOW: discovery, iDMS integration, flows and routing, AI agent, number porting, testing, training and the parallel run with Zultys. The planning duration is three to five months (slide 8). No hours or prices are given because there is no basis until iDMS access, number of agents and rules are known; quote after discovery.\n\nNOT INCLUDED, PASSED THROUGH. Toll-free minutes (the per-minute rate is not confirmed on the AWS pages); telephony beyond the assumed mix; SMS for payment links ($0.014 each plus carrier fee); third-party voice such as ElevenLabs; the payment processor, PCI work and any DealerSocket or iDMS fee; the AWS support plan.\n\nCOMMERCIAL CONSIDERATIONS (all proposals). Minimum term of 12 months for the managed service. Price review once real volumes are known, about 90 days after go-live. AWS has no minimum, so a minimum number of seats would be ours to set; we suggest none for usage and a floor only for the managed fee. Account ownership: bundled per-agent price on our AWS account is simpler for MEI; the alternative is MEI's own AWS account with usage billed by AWS at cost and our managed fee on top, which is more transparent but moves billing and quota work to MEI. If AWS grants a volume discount, share it by agreement (for example, pass it through when the account is MEI's).\n\nCOMPARISON HOOK. The number to compare is the price per agent per month. We still need what MEI pays today for Zultys licences, BrevAll support and carriers (docs/proposal/modelo-de-costos.md, section 6).\n\nSource: docs/proposal/modelo-de-costos.md, sections 3c and 3d.");
}

// 12. Operations cost and suggested support fee (draft)
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Operations cost and suggested support fee (draft)", { placeholder: "title" });
  const b = (t) => cell(t, { bold: true, fontSize: 11 });
  const c = (t, o) => cell(t, Object.assign({ fontSize: 11 }, o || {}));
  const rows = [
    [hdr("Line"), hdr("Basis"), hdr("Hours"), hdr("Rate"), hdr("Cost / mo")],
    [b("Support and administration"), c("Tickets, users, queues, prompts"), c("40"), c("$70"), c("$2,800")],
    [b("Engineering and DevOps"), c("Flows, Lambdas, releases, alarms"), c("24"), c("$90"), c("$2,160")],
    [b("Service mgmt, compliance"), c("Monthly review, PCI/TCPA input"), c("8"), c("$90"), c("$720")],
    [b("Tooling"), c("Ticketing, monitoring, alerting"), c("-"), c("-"), c("$1,000")],
    [b("Operating cost"), c(""), b("72"), c(""), b("$6,680")],
    [cell("Suggested monthly fee", { bold: true, fontSize: 12, color: C.accent1 }), c("Cost / 0.70, rounded to $500"), c(""), c(""), cell("~$9,500", { bold: true, fontSize: 12, color: C.accent1 })],
  ];
  s.addTable(rows, { x: 0.6, y: 1.35, w: 7.9, colW: [2.5, 2.7, 0.9, 0.7, 1.1], rowH: 0.4, border: BORDER });
  card(s, "Support card", 8.7, 1.35, 4.0, 2.8, C.background1);
  sub(s, "Support title", "Standard support (proposal)", 8.95, 1.45, 3.6);
  bullets(s, "Support bullets", ["Monday to Friday, 8:00 to 17:00 CT", "Response targets: service down 1 hour; major issue 4 business hours; other next business day", "Includes monitoring, flow, queue and prompt changes, user admin, reports, monthly review", "After hours and 24/7: quoted separately, hourly"], 8.95, 1.9, 3.5, 2.2, 11);
  const cols = [
    ["Passed through at cost", ["AWS support plan (Business Support+: 9% of the first $10K of monthly AWS charges, 7% to $80K): about $590 to $1,090 a month if there are 85 agents (it grows with usage)", "Other AWS services (Lex, Lambda, Customer Profiles, storage): to measure", "After-hours work"]],
    ["Cross-checks", ["Billed rates of $100 and $130 an hour, against partner rates of $125 to $250", "Fixed fee, not per agent: the work follows scope (flows, integrations, changes), not headcount", "No published agents-per-admin ratio found: the hours are our estimate"]],
    ["How the fee scales", ["Priced for the demo scope: about 10 queues, two languages, one AI flow, one iDMS integration", "Set in bands by agent count (for example up to 100, then 101 to 250), reviewed at 90 days", "Usage is billed separately, per agent (previous slide)"]],
  ];
  cols.forEach((q, i) => {
    const x = 0.6 + i * 4.15, w = 3.85;
    card(s, "Ops card " + (i + 1), x, 4.3, w, 2.15, C.background1);
    s.addText(q[0], { x: x + 0.2, y: 4.38, w: w - 0.4, h: 0.34, fontSize: 14, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Ops card title " + (i + 1) });
    bullets(s, "Ops card bullets " + (i + 1), q[1], x + 0.2, 4.78, w - 0.4, 1.62, 11);
  });
  s.addText("Suggestion prepared with AI-assisted research on public rate data; rates, hours and fees are estimates to validate, not a quote. A fixed fee for a defined scope, independent of agent count; to be banded once volumes are known. References are in the notes.", { x: 0.6, y: 6.55, w: 12.1, h: 0.45, fontSize: 11, color: C.accent5, margin: 0, isTextBox: true, valign: "top", objectName: "Ops note" });
  s.addNotes("DRAFT FOR INTERNAL REVIEW. This slide is a suggestion prepared with AI-assisted research on public data. Every rate and every hour count is an estimate for Willian to validate. It is not a quote and not a fact about MEI. Do not show it to the client as it stands.\n\nWHAT IT IS. The full cost of operating the platform after go-live, as a separate fixed monthly fee on top of the per-agent usage price (previous slide). Standard support is office hours. MEI can then compare usage (per agent) with Zultys plus carriers, and service (fixed fee) with BrevAll.\n\nHOW THE COST IS BUILT.\n1) Support and administration: 40 hours a month at a loaded cost of $70 an hour = $2,800. Tickets, user moves and changes, queue and prompt changes, reports.\n2) Engineering and DevOps: 24 hours a month at $90 = $2,160. Changes to flows and Lambda functions, releases through infrastructure as code, alarms, AWS service updates, cost review.\n3) Service management and compliance: 8 hours a month at $90 = $720. Monthly review of metrics, input to security, PCI and calling-consent (TCPA) reviews, contact with MEI and vendors.\n4) Tooling: $1,000 a month for ticketing, monitoring and alerting (midpoint of $500 to $1,500 in an MSP pricing guide; not specific to Amazon Connect).\nTotal: 72 hours and $6,680 a month. Suggested fee = $6,680 / 0.70 = $9,543, rounded to about $9,500 a month, kept as a fixed monthly fee, not a per-agent price. Same 30% margin as the usage price, for consistency.\n\nWHERE THE RATES COME FROM. Cost rates are loaded costs. Support and administration: the US Bureau of Labor Statistics mean wage for network and computer systems administrators is about $48 an hour (May 2023 figure, as reported by a search result; the BLS occupation page could not be opened directly), divided by 0.70 because wages are about 70% of employer compensation cost (BLS, 2025), which gives about $69, rounded to $70. Engineering and DevOps: the O*NET/BLS national median for software developers is about $65 an hour (year not confirmed), which loaded is about $93; Amazon Connect engineer contract postings show $70 to $85 an hour for contractors. We use $90. Service management uses the same $90. Billing these hours at cost / 0.70 gives about $100 and $130 an hour, below the $125 to $250 an hour seen in a partner rate card and MSP labor rates. If MEI's work is done in a lower-cost country the cost rates fall; keep the billed rate if the value is the same.\n\nWHERE THE HOURS COME FROM. There is no basis for these hours in a published benchmark: I searched for an agents-per-platform-administrator ratio and found none (published ratios cover supervisors, 8 to 15 agents each, and quality evaluators, about 1 per 33 agents). Partner pages describe the same scope (moves, adds, changes, troubleshooting, regular reviews, monitoring) but publish no hours or prices; they quote case by case. So 72 hours a month, about 0.45 of a full-time person, is our estimate for the demo scope. Validate it by counting change requests and tickets in the first 90 days, then adjust the fee.\n\nSTANDARD SUPPORT TERMS (proposal). Monday to Friday, 8:00 to 17:00 CT. Response targets: service down 1 hour; major issue 4 business hours; other next business day. These are typical severity tiers, not a researched benchmark. After-hours and 24/7 coverage is quoted separately by the hour: the one source found puts after-hours MSP labor at $250 to $500 an hour.\n\nPASSED THROUGH AT COST. The AWS support plan is optional but sensible for production. Business Support+ costs the greater of $29 a month or 9% of monthly AWS charges up to $10K, 7% from $10K to $80K, 5% from $80K to $250K and 3% above (AWS pricing page, read November 10, 2026). At 85 agents and 3 contact hours a day the AWS bill is about $6,600 (level 1), $11,200 (level 2) or $12,700 (level 3), so the plan costs about $590, $980 or $1,090 a month. Other AWS services that sit outside the per-minute price (Lex, Lambda, Customer Profiles, recording storage, encryption keys, monitoring) have not been measured, except recordings (under $5 a month); measure them in Cost Explorer for the demo account before quoting. After-hours work is billed hourly.\n\nWHY A FIXED FEE AND NOT PER AGENT. We do not know how many agents take calls (85 or up to 210), and most of this work does not grow with headcount: monitoring, releases, flow and prompt changes and reviews follow the scope (queues, languages, integrations, change requests). Keeping usage per agent (previous slide) and service as a fixed fee also lets MEI compare each with what it pays today (Zultys and carriers for usage, BrevAll for service). The hours below were estimated for the demo scope: about 10 queues, two languages, one AI flow and one iDMS integration.\n\nCROSS-CHECK. Billed rates of $100 and $130 an hour are below the $125 to $250 seen for partners and MSPs. (Managed-IT plans priced per user run $110 to $185 a month in two guides; they cover desktop IT, so they are not a fair comparison for a fixed fee.)\n\nSCALING. Once volumes are known, set the fee in bands by agent count (for example up to 100 agents, then 101 to 250), with a floor, and review it after 90 days of real tickets. Re-estimate the hours if the scope grows (more queues, a second AI flow, more integrations).\n\nREFERENCES (read through search results on November 10, 2026; vendor pages are marketing, treat as rough):\n- AWS Support plan pricing: https://aws.amazon.com/premiumsupport/pricing\n- BLS network and computer systems administrators (15-1244): https://www.bls.gov/OES/current/oes151244.htm\n- O*NET national wages, software developers (15-1252): https://www.onetonline.org/link/localwages/15-1252.00\n- BLS employer costs for employee compensation (wages about 70% of total): https://www.bls.gov/news.release/ecec.htm\n- Amazon Connect contract postings: https://jobs.insightglobal.com/find_a_job/maryland/job-427098 and https://www.careerbuilder.com/job-details/aws-connect-specialist-dmv-area-consultants-reqd-washington-dc--e152fd75-5f7e-4904-b6a4-b7f0b45c8278\n- Partner rate card, $125 to $250 an hour (AWS IQ): https://iq.aws.amazon.com/e/aspentgi\n- MSP pricing guides: https://www.n-able.com/blog/msp-pricing-guide, https://arphost.com/managed-it-support-pricing/, https://serenit.pages.dev/it-support-cost, https://www.flamingo.run/blog/msp-pricing-models, https://www.kaseya.com/resource/msp-pricing-managed-it-services-pricing/\n- Amazon Connect managed-service scope (no published prices): https://usan.com/managed-services-amazon-connect and https://www.ventrica.co.uk/what-is-an-amazon-connect-msp/\n- Staffing ratios (supervisors, quality): https://www.icmi.com/resources/2012/Staff-to-Supervisor-Ratio\n\nSource: docs/proposal/modelo-de-costos.md, section 3d.");
}

// 13. Demo
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("Demo, using simulated data", { placeholder: "title" });
  const demos = [
    ["1", "Basic call", "Known number greeted by name; profile on the agent screen"],
    ["2", "Transfer", "One call ID across every leg; context follows"],
    ["3", "Disposition", "Agent closes the call with a wrap-up form (configured)"],
    ["4", "AI agent", "English and Spanish, switches language, hands over with context"],
    ["5", "Flows", "Routing by language, status and delinquency"],
    ["6", "Reports", "Supervisor: live view, history, recording, transcript, summary"],
    ["7", "Pricing", "Platform cost, then suggested price per agent"],
  ];
  const pos = (i) => i < 4 ? [0.6 + i * 3.075, 1.55] : [0.6 + (i - 4) * 3.075, 3.75];
  demos.forEach((d, i) => {
    const [x, y] = pos(i), w = 2.85, h = 1.95;
    card(s, "Demo card " + d[0], x, y, w, h);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.2, y: y + 0.2, w: 0.5, h: 0.5, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: "Demo number circle " + d[0] });
    s.addText(d[0], { x: x + 0.2, y: y + 0.2, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Demo number " + d[0] });
    s.addText(d[1], { x: x + 0.85, y: y + 0.2, w: w - 1.0, h: 0.5, fontSize: 18, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "Demo title " + d[0] });
    s.addText(d[2], { x: x + 0.2, y: y + 0.9, w: w - 0.4, h: 0.9, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "Demo text " + d[0] });
  });
  card(s, "Not shown panel", 9.825, 3.75, 2.85, 1.95, C.background1);
  s.addText("Not in this demo", { x: 10.025, y: 3.95, w: 2.45, h: 0.4, fontSize: 16, bold: true, color: C.accent4, margin: 0, isTextBox: true, objectName: "Not shown title" });
  s.addText("Live iDMS data, payments and MEI's own data", { x: 10.025, y: 4.45, w: 2.45, h: 1.1, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "Not shown text" });
  s.addText("All accounts are invented. A simulated lookup plays the role of iDMS.", { x: 0.6, y: 6.0, w: 12.1, h: 0.4, fontSize: 14, color: C.accent5, margin: 0, isTextBox: true, objectName: "Demo caption" });
  s.addNotes("PURPOSE. Show with simulated data that Amazon Connect handles what MEI's contact center does every day, and what AI adds. Say at the start: invented accounts, no iDMS, no MEI data.\n\n1. BASIC CALL. A known caller (Mauricio Cuevas in Spanish, Mauricio Ordonez in English, with simulated account data) is recognized by phone number, hears the recording notice and a personal greeting in their language, skips the menus and is routed by account. An unknown caller hears 'Thank you for calling', a language menu and 'Please enter your account number'. The agent lands directly on the agent workspace and sees the customer profile (address, vehicle loan, notes, contact history) and a 'Customer on the line' panel.\n\n2. TRANSFER. The agent transfers the call to another team. Each transfer is a new contact in Connect; every leg carries the same call ID, so the whole conversation can be followed. The receiving agent sees a 'Transferred by another agent' panel with the customer summary and where the call came from.\n\n3. DISPOSITION. When the call ends the agent sees a 'Call wrap-up' form: disposition (promise to pay, payment made, payment arrangement set, callback requested, dispute, hardship, refused to pay, information only, wrong party, transferred), follow-up, resolved, an editable summary, date and notes. It is saved on the call for reports; agents get 60 seconds of after-call work. It is configured; the save was shown on screen but not confirmed end to end, so say 'configured' unless that is confirmed.\n\n4. AI AGENT. Call the AI number. Amazon Nova 2 Sonic answers in English or Spanish, switches language mid-call on request and keeps the account, gives balance and due date, explains how to pay, and hands over to a person with context (the agent sees the reason, an AI summary, the account, the language and the queue). If it cannot continue it goes to a person instead of hanging up. Tested on a real call in English and by scripted calls for the language switch and the hand-over. If a live call fails, play the recording of the test call and say it is a recording.\n\n5. FLOWS. Show the routing logic: special status before days past due. The key case is a Redemptions account 12 days late, which goes to Redemptions, not to the 9-15 queue.\n\n6. REPORTS. Real-time supervisor view (agents on calls, queues, listen-in), historical metrics and contact search. Then open one finished call: recording, transcript, sentiment, the AI summary (English and Spanish) and the automatic categories, which flag what was actually said (promise to pay, payment arrangement, hardship, dispute, callback, collection notice given) so supervisors can compare with the outcome the agent recorded.\n\n7. PRICING. Slide 10 (platform cost on AWS), then slide 11 (suggested price, a draft).\n\nPRACTICAL NOTES. Contact records take a minute or two to appear after a call ends: keep one finished call ready. Keep a recorded video of the run as a fallback.");
}

// 14. Needs and next steps
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  s.addText("What we need from MEI, and what happens next", { placeholder: "title" });
  sub(s, "Needs title", "What we need", 0.6, 1.5, 6.2);
  const needs = [
    "Call volumes, peaks and agents per shift",
    "Of the 210 planned users, who takes or makes customer calls?",
    "iDMS access: API or data feed, and an owner",
    "Meaning of OFR/Skip and other statuses",
    "How customers pay today: processor, Text-to-Pay vendor",
    "Current costs: Zultys, BrevAll, carriers",
    "Contract expiry dates and phone numbers to port",
    "Sales and Service routing rules",
    "Rules for verification and payment arrangements",
    "Compliance owner: calling consent, payments (PCI)",
  ];
  s.addText(needs.map((t, k) => ({ text: t, options: { bullet: { type: "number" }, breakLine: k < needs.length - 1 } })), { x: 0.6, y: 2.0, w: 6.5, h: 4.7, fontSize: 14, color: C.text1, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true, objectName: "Needs list" });
  card(s, "Next steps panel", 7.5, 1.5, 5.2, 5.1, C.background1);
  sub(s, "Next title", "Next steps", 7.8, 1.7, 4.6);
  const steps = [["Within 24 hours", "Meeting summary and open questions"], ["Week 1-2", "Data request answered; demo walkthrough on MEI flows"], ["After data", "Itemized estimate with ranges and assumptions"], ["Then", "Proposed SOW: integrations, migration, testing, training, support"]];
  steps.forEach((d, i) => {
    const y = 2.35 + i * 1.05;
    s.addShape(pres.ShapeType.ellipse, { x: 7.8, y: y + 0.05, w: 0.45, h: 0.45, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: "Step circle " + (i + 1) });
    s.addText(String(i + 1), { x: 7.8, y: y + 0.05, w: 0.45, h: 0.45, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Step number " + (i + 1) });
    s.addText(d[0], { x: 8.45, y, w: 4.1, h: 0.32, fontSize: 14, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "Step when " + (i + 1) });
    s.addText(d[1], { x: 8.45, y: y + 0.34, w: 4.1, h: 0.55, fontSize: 12, color: C.accent5, valign: "top", margin: 0, isTextBox: true, objectName: "Step what " + (i + 1) });
  });
  s.addNotes("WHY EACH ASK MATTERS. Each item unblocks a specific part of the estimate or the SOW.\n\n1. Volumes: sizing, the concurrent-call quota to request, and every usage-based cost.\n2. Who takes customer calls: the number of agents to size, migrate and train. Ask it exactly this way; users who only use internal office phone features stay out of the Connect sizing.\n3. iDMS: whether account-based routing, verification, balances and payment arrangements are feasible, and the integration work.\n4. OFR/Skip and other statuses: routing rules and queue design.\n5. How customers pay: whether the contact center takes payments, through which processor, and how Text-to-Pay works.\n6. Current costs: without what MEI pays today for Zultys licences, BrevAll support and carrier minutes, there is nothing to compare Amazon Connect against.\n7. Contracts and numbers: the realistic migration window, any overlap or early-termination cost, and the porting plan.\n8. Sales and Service rules: queues, menus and who answers.\n9. Verification and payment arrangements: business rules, approvals and customer confirmation, which MEI listed as requirements.\n10. Compliance owner: rules for AI calls, calling consent and payments (PCI). A new FCC order on consent revocation takes effect November 25, 2026; this needs legal review.\n\nNEXT STEPS. A meeting summary within 24 hours, then a data request with owners and dates, a demo walkthrough on MEI's own flows, an itemized estimate with ranges and assumptions once data arrives, and a proposed SOW. The timing is a proposal to agree with MEI, not a commitment.\n\nIf a fixed price is expected after this meeting, say clearly that without volumes, current costs and an iDMS path we can give ranges with explicit assumptions, not a fixed price.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
})();
