// Builds docs/proposal/MEI_Demo_Flows_Guide.pptx (5-slide quick guide). Run from a folder with pptxgenjs installed:
//   SKILL=<pptx skill dir> NODE_PATH=<node_modules> node build_quick_guide.js && mv guide.pptx docs/proposal/MEI_Demo_Flows_Guide.pptx
// Demo quick guide: numbers, customers, call flows. Same theme as the previous MEI_Demo_Flows_Guide.pptx.
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(`${process.env.SKILL}/scripts/apply_theme.js`);

const THEME = {
  name: "MEI Demo", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: "1F2A30", lt1: "FFFFFF", dk2: "3B4A54", lt2: "F2F4F5", accent1: "3E6E8E", accent2: "2E7D5B",
            accent3: "A9690F", accent4: "A04040", accent5: "6B7A84", accent6: "5B8C85", hlink: "3E6E8E", folHlink: "6B7A84" },
};
const K = THEME.colors;
const TINT = { in: "E4EDF3", out: "E3F0E9", test: "F6EEE1", grey: "F2F4F5", line: "D5DADD", chip: "E8B923" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "MEI demo quick guide";
const C = pres.SchemeColor;

// Title placeholder on the layout
pres.defineSlideMaster({
  title: "GUIDE_T",
  background: { color: "FFFFFF" },
  objects: [
    { rect: { x: 0.45, y: 0.32, w: 1.35, h: 0.28, fill: { color: TINT.chip } } },
    { text: { text: "INTERNAL ONLY", options: { x: 0.45, y: 0.32, w: 1.35, h: 0.28, fontSize: 10, bold: true, color: K.dk1, align: "center", valign: "middle", margin: 0 } } },
    { text: { text: "Simulated data · instance cs-connect-demo · passwords only in poc/.credentials.local", options: { x: 0.45, y: 7.08, w: 9, h: 0.26, fontSize: 10, color: K.accent5, margin: 0 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.45, y: 0.66, w: 12.4, h: 0.6, fontSize: 28, bold: true, color: K.dk1, margin: 0, valign: "top" }, text: "" } },
    { placeholder: { options: { name: "sub", type: "body", x: 0.45, y: 1.22, w: 12.4, h: 0.32, fontSize: 13, color: K.dk2, margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.45, y: 7.06, w: 0.45, h: 0.3, fontSize: 10, color: K.accent5, align: "right" },
});

pres.addSection({ title: "Guide" });

const cell = (text, o = {}) => ({ text, options: { fontSize: 11.5, color: K.dk1, valign: "middle", margin: [2, 5, 2, 5], ...o } });
const head = (text) => cell(text, { bold: true, color: "FFFFFF", fill: { color: K.dk1 }, fontSize: 11.5 });

// ---------- Slide 1: numbers and users ----------
{
  const s = pres.addSlide({ masterName: "GUIDE_T", sectionTitle: "Guide" });
  s.addText("Who is who: numbers and users", { placeholder: "title" });
  s.addText("Every phone number in the demo, what answers it and what it is for", { placeholder: "sub" });
  const rows = [
    ["+1 775 245 6050", "Main collections line", "CS - Inbound - Collections Routing", "Routing by language, special status and days past due to human agents. Caller ID of the agents' outbound calls", K.accent1],
    ["+1 775 249 1758", "AI line (Amazon Nova)", "CS - Inbound - AI Agent", "Nova 2 Sonic assistant: balance and due date, switches EN/ES by voice, hands over to a person", K.accent1],
    ["+1 775 255 0671", "Sofia line (ElevenLabs)", "CS - Inbound - Sofia AI", "Sofia negotiates payment arrangements. Also the caller ID of outbound AI calls", K.accent2],
    ["+1 952 866 1775", "Sofia's Twilio number", "Answered by ElevenLabs", "Internal target of the hand-off. Do not dial it in the demo (Sofia would not know who is calling)", K.accent5],
    ["+1 775 249 1708", "Willian's phone (account 10)", "CS - Test - Customer Phone (caller2)", "Rings demo.caller2: the customer for outbound tests. Also demo.caller2's caller ID", K.accent3],
    ["+1 775 258 5298", "Maria's phone (account 2)", "CS - Test - Customer Phone (caller3)", "Rings demo.caller3. Also the caller ID of demo.caller3 and the call tester, so every line recognizes Maria", K.accent3],
  ];
  const data = [[head("Number"), head("What it is"), head("Connect flow / who answers"), head("Use in the demo")]];
  rows.forEach(([n, what, flow, use, col], i) => {
    const fill = { color: i % 2 ? "FFFFFF" : TINT.grey };
    data.push([cell(n, { bold: true, color: col, fill }), cell(what, { bold: true, fill }), cell(flow, { fill, color: K.dk2 }), cell(use, { fill })]);
  });
  s.addTable(data, { x: 0.45, y: 1.7, w: 12.43, colW: [1.75, 2.45, 3.0, 5.23], rowH: 0.46, border: { type: "solid", pt: 0.5, color: TINT.line }, objectName: "Numbers table" });

  s.addText("Users (one browser or profile each, headphones)", { x: 0.45, y: 5.12, w: 8, h: 0.3, fontSize: 14, bold: true, color: K.dk1, margin: 0, isTextBox: true });
  const users = [
    ["demo.agent1", "Front line: delinquency queues and General Assistance", K.accent1],
    ["demo.agent2", "Specialist: Redemptions and EPD", K.accent1],
    ["demo.supervisor", "Monitors; opens the app \"Call with AI\" (Apps menu)", K.accent2],
    ["demo.admin", "Administration; also sees the app", K.accent2],
    ["demo.caller", "Calls from the browser as an unknown customer", K.accent3],
    ["demo.caller2", "Is Willian; receives the outbound test calls", K.accent3],
    ["demo.caller3", "Is Maria: calls as her and receives her outbound calls", K.accent3],
  ];
  const w = 1.69, gap = 0.1;
  users.forEach(([u, d, col], i) => {
    const x = 0.45 + i * (w + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.5, w, h: 1.05, fill: { color: TINT.grey }, line: { color: TINT.line, width: 0.75 }, rectRadius: 0.08, objectName: `User ${u}` });
    s.addText([{ text: u, options: { bold: true, color: col, fontSize: 12, breakLine: true } }, { text: d, options: { color: K.dk1, fontSize: 10.5 } }],
      { x: x + 0.08, y: 5.56, w: w - 0.16, h: 0.93, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 3 });
  });
  s.addNotes("Numbers claimed on cs-connect-demo (account 383799408374) plus Sofia's Twilio number. The sandbox line +1 775 249 1708 is temporarily the customer phone of outbound tests; poc/infra/outbound/customer_line.py restore puts it back on 'CS - Sandbox - Simple Flow'. Agents must be Available to receive calls; they auto-accept. Scripts and commands: poc/README.md, section 'Demos de la ruta B'.");
}

// ---------- Slide 2: customers ----------
{
  const s = pres.addSlide({ masterName: "GUIDE_T", sectionTitle: "Guide" });
  s.addText("Demo customers", { placeholder: "title" });
  s.addText("Customer Profiles in Connect, invented account data. Special status wins over days past due", { placeholder: "sub" });
  const custs = [
    ["1", "Michael Johnson", "EN", "+1 713 555 0101", "fictional", "0", "$412.50", "Current", "Unknown caller: menus, then account 1"],
    ["2", "Maria Hernandez", "ES", "+1 775 258 5298", "rings caller3", "5", "$1,180.00", "1 to 8 days", "Known caller from demo.caller3 on every line; asks Sofia for installments (call tester scenario)"],
    ["3", "Robert Miller", "EN", "+1 214 555 0103", "fictional", "22", "$2,640.75", "16 to 30 days", "Broken promise to pay"],
    ["4", "Luisa Ramirez", "ES", "+1 915 555 0104", "fictional", "47", "$5,210.30", "31+ days", "Over 30 days: Sofia offers at most 2 installments"],
    ["5", "David Thompson", "EN", "+1 512 555 0105", "fictional", "12", "$7,890.00", "Redemptions ★", "Special status: straight to agent2, never to the AI"],
    ["6", "Sofia Castillo", "ES", "+1 956 555 0106", "fictional", "3", "$980.00", "EPD ★", "Special status: straight to agent2, never to the AI"],
    ["7", "(does not exist)", "", "", "", "", "", "General Assistance", "Account not found: the fallback queue"],
    ["8", "Mauricio Cuevas", "ES", "+1 713 555 0108", "fictional", "18", "$3,125.40", "16 to 30 days", "Calls from his real phone: not recognized, gets the menus"],
    ["9", "Mauricio Ordonez", "EN", "+1 678 707 9207", "real", "10", "$1,460.00", "9 to 15 days", "Recognized by phone, no menus. Sofia can call him from the supervisor app"],
    ["10", "Willian Martinez", "ES", "+1 775 249 1708", "rings caller2", "12", "$6,240.00", "9 to 15 days", "Outbound AI calls: answer on demo.caller2"],
  ];
  const data = [[head("Acct"), head("Customer"), head("Lang"), head("Phone"), head("Days late"), head("Balance"), head("Queue"), head("How to use it in the demo")]];
  custs.forEach((r, i) => {
    const fill = { color: i % 2 ? "FFFFFF" : TINT.grey };
    const special = r[7].includes("★");
    const tagColor = r[4] === "real" ? K.accent2 : r[4].startsWith("rings") ? K.accent3 : K.accent5;
    data.push([
      cell(r[0], { bold: true, align: "center", fill }), cell(r[1], { bold: true, fill }), cell(r[2], { align: "center", fill }),
      cell(r[3] ? [{ text: r[3], options: { breakLine: true } }, { text: r[4], options: { fontSize: 9.5, color: tagColor, bold: r[4] !== "fictional" } }] : "", { fill }),
      cell(r[5], { align: "center", fill }), cell(r[6], { align: "right", fill }),
      cell(r[7], { fill, bold: special, color: special ? K.accent4 : K.dk1 }), cell(r[8], { fill }),
    ]);
  });
  s.addTable(data, { x: 0.45, y: 1.7, w: 12.43, colW: [0.55, 1.75, 0.55, 1.6, 0.85, 1.05, 1.68, 4.4], rowH: 0.43, border: { type: "solid", pt: 0.5, color: TINT.line }, objectName: "Customers table" });

  // Sofia's rules strip
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 6.48, w: 12.43, h: 0.5, fill: { color: TINT.out }, line: { color: TINT.out }, rectRadius: 0.06, objectName: "Rules strip" });
  s.addText([
    { text: "Sofia's rules: ", options: { bold: true, color: K.accent2 } },
    { text: "pay in full · promise within 7 days · up to 3 installments, 14 days apart (2 if over 30 days late) · no discounts · overrides under [config] in the profile · ★ special status" },
  ], { x: 0.6, y: 6.48, w: 12.2, h: 0.5, fontSize: 11.5, color: K.dk1, valign: "middle", margin: 0, isTextBox: true });
  s.addNotes("Source: poc/data/customers.csv, loaded into Customer Profiles. Account 7 does not exist on purpose. Account 10 moved on 2026-11-12 from Redemptions to 12 days late (9 to 15 days queue) so the AI can negotiate on outbound tests. Only phones on the supervisor app's test list can be dialed (+1 775 249 1708 and +1 678 707 9207); fictional 555-01xx numbers never are.");
}

// ---------- Slide 3: call flow map ----------
{
  const s = pres.addSlide({ masterName: "GUIDE_T", sectionTitle: "Guide" });
  s.addText("Every call path in the demo", { placeholder: "title" });
  s.addText("Who starts the call, which number it uses, what happens and where it ends", { placeholder: "sub", w: 9.2 });

  const X = { start: 0.45, num: 2.3, s1: 3.95, s2: 6.85, end: 9.95 };
  const W = { start: 1.65, num: 1.45, s1: 2.6, s2: 2.8, end: 2.93 };
  const H = 0.66, top = 1.95, step = 0.74;

  // column headers
  [["Who starts", "start"], ["Number", "num"], ["What happens", "s1"], ["", "s2"], ["Ends in", "end"]].forEach(([t, k]) => {
    if (t) s.addText(t, { x: X[k], y: 1.62, w: W[k], h: 0.26, fontSize: 11, bold: true, color: K.accent5, margin: 0, isTextBox: true });
  });

  const box = (x, y, w, text, fill, opts = {}) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: H, fill: { color: fill }, line: { color: opts.line || fill, width: 0.75 }, rectRadius: 0.06 });
    s.addText(text, { x: x + 0.07, y, w: w - 0.14, h: H, fontSize: opts.size || 10.5, color: opts.color || K.dk1, valign: "middle", margin: 0, isTextBox: true, bold: !!opts.bold });
  };
  const arrow = (x1, x2, y) => s.addShape(pres.shapes.LINE, { x: x1, y, w: x2 - x1, h: 0, line: { color: K.accent5, width: 1.25, endArrowType: "triangle" } });

  const bands = [
    { label: "INBOUND", color: K.accent1, tint: TINT.in, rows: [
      { start: "Customer calls (or demo.caller / caller2)", num: "245 6050", s1: "Known number: greeting by name, no menus. Unknown: language menu + account number", s2: "Rules: special status first, then days past due → queue", end: "agent1 (delinquency) or agent2 (Redemptions, EPD). Transfer keeps context; wrap-up form" },
      { start: "Customer calls", num: "249 1758", s1: "Recording notice; recognized by phone or asked for the account", s2: "Nova 2 Sonic: balance, due date, payment options; EN ↔ ES by voice", end: "Resolved and hangs up, or to the account's queue with an AI summary for the agent" },
      { start: "Customer calls (demo.caller3 = Maria)", num: "255 0671", s1: "Connect records and identifies silently. Special status → specialist, no AI", s2: "Sofia (ElevenLabs): confirms identity, explains the balance, validates every plan with the rules", end: "Agreement saved (contact, profile, table) + email announced; or queue with summary. Transcript and audio in S3" },
    ]},
    { label: "OUTBOUND", color: K.accent2, tint: TINT.out, rows: [
      { start: "Supervisor: app \"Call with AI\" (or a script)", num: "from 255 0671", s1: "Connect dials the customer (test numbers only: Willian → caller2, Maria → caller3, Ordonez → his phone)", s2: "When answered, the same conversation with Sofia as the row above", end: "Agreement or queue; the app shows the result live" },
      { start: "Agent (agent1, agent2)", num: "from 245 6050", s1: "Dials from the softphone or the profile's phone link; profile opens by phone", s2: "Recorded (CS - Outbound Whisper - Recording)", end: "Human conversation and wrap-up" },
    ]},
    { label: "TESTS", color: K.accent3, tint: TINT.test, rows: [
      { start: "Call tester (run.py) · menus: twilio_test_calls.py", num: "from 258 5298", s1: "Lex bot with Nova Sonic voice plays a scripted customer (Bedrock writes each reply)", s2: "Calls the Sofia line or the AI line by voice; key presses only via Twilio", end: "Report: dialogue, contact attributes, agreement, S3 transcript" },
    ]},
  ];

  let y = top;
  bands.forEach((band) => {
    const bandH = band.rows.length * step - (step - H);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.3, y: y - 0.06, w: 12.73, h: bandH + 0.12, fill: { color: band.tint }, line: { color: band.tint }, rectRadius: 0.06, objectName: `Band ${band.label}` });
    band.rows.forEach((r) => {
      box(X.start, y, W.start, r.start, "FFFFFF", { line: TINT.line, bold: true, size: 10.5 });
      // Small prefix line, then the local number in large type
      const out = r.num.startsWith("from ");
      const local = r.num.replace("from ", "");
      box(X.num, y, W.num, [
        { text: (out ? "from " : "") + "+1 775", options: { fontSize: 10, bold: false, breakLine: true } },
        { text: local, options: { fontSize: 15, bold: true } },
      ], band.color, { color: "FFFFFF" });
      box(X.s1, y, W.s1, r.s1, "FFFFFF", { line: TINT.line });
      box(X.s2, y, W.s2, r.s2, "FFFFFF", { line: TINT.line });
      box(X.end, y, W.end, r.end, "FFFFFF", { line: band.color });
      const my = y + H / 2;
      arrow(X.start + W.start, X.num, my); arrow(X.num + W.num, X.s1, my); arrow(X.s1 + W.s1, X.s2, my); arrow(X.s2 + W.s2, X.end, my);
      y += step;
    });
    y += 0.16;
  });

  // legend
  [["Inbound", K.accent1], ["Outbound", K.accent2], ["Tests", K.accent3]].forEach(([t, col], i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 9.95 + i * 1.0, y: 1.28, w: 0.18, h: 0.18, fill: { color: col }, line: { color: col }, rectRadius: 0.03 });
    s.addText(t, { x: 10.18 + i * 1.0, y: 1.24, w: 0.8, h: 0.26, fontSize: 10, color: K.dk2, margin: 0, isTextBox: true });
  });
  s.addNotes("Numbers are shortened: 245 6050, 249 1758 and 255 0671 are +1 775 numbers. Sofia's line sends the call to her Twilio number (+1 952 866 1775) and, when she escalates, takes it back to the customer's queue. Outbound AI calls reuse the Sofia flow: Connect dials, then hands the call to Sofia. Confirmation email is announced but not sent yet. The call tester cannot press keys, so the menus of the main line are tested with poc/infra/mei-demo/twilio_test_calls.py.");
}

// ---------- Slide 4: infrastructure, route B vs native A2A ----------
{
  const s = pres.addSlide({ masterName: "GUIDE_T", sectionTitle: "Guide" });
  s.addText("What runs the demo", { placeholder: "title" });
  s.addText("AWS account 383799408374, us-east-1. Everything is in the sandbox with simulated data", { placeholder: "sub" });

  const cards = [
    { title: "Amazon Connect · cs-connect-demo", color: K.accent1, items: [
      "5 phone numbers, contact flows, queues and routing profiles",
      "Agent workspace: \"Agents\" and \"Supervisors\" workspaces, app \"Call with AI\"",
      "Customer Profiles (encrypted with its own KMS key)",
      "Recordings in S3; Contact Lens: transcripts, summaries, categories, evaluations",
    ]},
    { title: "AWS services around it", color: K.accent2, items: [
      "Lex + Nova 2 Sonic: AI line bot (demo-assistant) and call tester bot",
      "Lambda: routing lookup, AI dialog, Sofia's API (voice-agent-api), supervisor app, tester",
      "API Gateway, DynamoDB (calls, payment agreements), S3 (transcripts, audio), Secrets Manager",
      "Bedrock (Claude Haiku 4.5) writes the call tester's replies",
    ]},
    { title: "Outside AWS", color: K.accent3, items: [
      "ElevenLabs agent \"collections-agent\" (Sofia, Eliza voice): 6 tools that call our API, start and post-call webhooks",
      "Twilio number +1 952 866 1775, answered by ElevenLabs (route B only)",
      "ElevenLabs plan: Starter",
    ]},
  ];
  const cw = 4.03, cg = 0.17, cy = 1.68, ch = 2.3;
  cards.forEach((c, i) => {
    const x = 0.45 + i * (cw + cg);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cy, w: cw, h: ch, fill: { color: TINT.grey }, line: { color: TINT.line, width: 0.75 }, rectRadius: 0.08, objectName: `Card ${c.title}` });
    s.addText(c.title, { x: x + 0.15, y: cy + 0.1, w: cw - 0.3, h: 0.34, fontSize: 13, bold: true, color: c.color, margin: 0, isTextBox: true });
    s.addText(c.items.map((t, j) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: j < c.items.length - 1 } })),
      { x: x + 0.15, y: cy + 0.5, w: cw - 0.3, h: ch - 0.6, fontSize: 11, color: K.dk1, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true });
  });

  const rows = [
    ["How the call reaches Sofia", "Connect transfers it by phone to the Twilio number: a second phone call", "Connect connects Sofia inside, as a Connect AI agent: no second call, no Twilio"],
    ["How Sofia knows the caller", "Our API matches the call by the customer's phone number", "Connect passes the contact's context directly"],
    ["Transcript and analytics", "In Connect via Contact Lens (Sofia shows as System); ElevenLabs copy also in S3", "Expected in Connect as an automated interaction (not verified: never enabled)"],
    ["What we maintain", "Our API, phone matching, webhooks, the Twilio number", "Mostly Connect and ElevenLabs configuration"],
    ["Status", "Built and tested: inbound, outbound, supervisor app", "AWS side wired and tested; blocked: ElevenLabs enables it only on Enterprise"],
  ];
  const data = [[head(""), head("Route B (what the demo uses)"), head("Native A2A integration")]];
  rows.forEach(([a, b, c], i) => {
    const fill = { color: i % 2 ? "FFFFFF" : TINT.grey };
    data.push([cell(a, { bold: true, fill, fontSize: 11 }), cell(b, { fill, fontSize: 11 }), cell(c, { fill, fontSize: 11 })]);
  });
  s.addTable(data, { x: 0.45, y: 4.25, w: 12.43, colW: [2.4, 5.0, 5.03], rowH: 0.4, border: { type: "solid", pt: 0.5, color: TINT.line }, objectName: "Route B vs A2A" });
  s.addNotes("Native A2A was tested end to end on the AWS side on 2026-11-12 (Q in Connect assistant ai-assistant, AI agent elevenlabs-handoff, Lex bot elevenlabs-bot, flow 'ElevenLabs Agent'). ElevenLabs closes the connection because the Amazon Connect transport is not enabled on the workspace; their support confirmed it requires an Enterprise plan, even for a PoC. Details: docs/research/comparacion-investigaciones-a2a.md. Route B: Contact Lens transcribes the recorded call, Sofia as SYSTEM and the customer as CUSTOMER (verified 2026-11-12); the generative summary is English only.");
}

// ---------- Slide 5: technology stack and estimated costs ----------
{
  const s = pres.addSlide({ masterName: "GUIDE_T", sectionTitle: "Guide" });
  s.addText("Technical summary: stack and estimated costs", { placeholder: "title" });
  s.addText("List prices read on 2026-11-09 and 10; not a quote: MEI's volumes are still unknown", { placeholder: "sub" });

  const small = (t, o = {}) => cell(t, { fontSize: 10.5, ...o });
  const stack = [
    ["Amazon Connect", "Phone numbers, call flows, queues, agent softphone and workspace"],
    ["Customer Profiles", "Customer records the agents and the AI read (stands in for iDMS)"],
    ["Amazon Lex V2", "Runs the voice bots: the AI line and the call tester"],
    ["Amazon Nova 2 Sonic", "Hears and speaks for the bots (speech to speech)"],
    ["Amazon Polly", "Generative voices for menus and announcements"],
    ["Contact Lens", "Transcripts, AI summaries, categories and quality evaluations"],
    ["AWS Lambda", "Routing rules, AI dialog, Sofia's API, supervisor app, call tester"],
    ["API Gateway, function URL", "HTTPS endpoints that ElevenLabs and the supervisor app call"],
    ["Amazon DynamoDB", "Call hand-offs and the payment agreements"],
    ["Amazon S3", "Call recordings, Contact Lens output, Sofia's transcripts and audio"],
    ["Secrets Manager, KMS", "API keys and webhook secrets; encryption of customer profiles"],
    ["Amazon Bedrock", "Claude Haiku 4.5 writes the call tester's replies"],
    ["Amazon Q in Connect", "AI agent used for the native A2A test with ElevenLabs"],
    ["ElevenLabs Agents", "Sofia: negotiates payment arrangements by voice"],
    ["Twilio", "Phone number that Connect transfers to so Sofia answers"],
    ["CloudWatch, IAM", "Logs of flows and functions; permissions between services"],
  ];
  const left = [[head("Technology"), head("Used for")]];
  stack.forEach(([a, b], i) => {
    const fill = { color: i % 2 ? "FFFFFF" : TINT.grey };
    left.push([small(a, { bold: true, fill, fontSize: 10 }), small(b, { fill, fontSize: 10 })]);
  });
  s.addTable(left, { x: 0.45, y: 1.68, w: 6.75, colW: [2.0, 4.75], rowH: 0.3, border: { type: "solid", pt: 0.5, color: TINT.line }, objectName: "Technology stack" });

  const costs = [
    ["Human agent", "≈ $0.04", "Connect voice $0.038 + US telephony $0.002 to $0.005"],
    ["Nova AI agent", "≈ $0.04", "Same minute: Lex and Nova Sonic are included in the voice price"],
    ["Sofia, route B", "≈ $0.14 to $0.18", "Connect with two phone legs ≈ $0.045 + ElevenLabs $0.08 + LLM $0.005 to $0.045 + Twilio ≈ $0.01*"],
    ["Sofia, native A2A", "≈ $0.13 to $0.18", "Connect $0.04 + third-party AI agent $0.01 + ElevenLabs $0.08 + LLM"],
  ];
  const right = [[head("Call handled by"), head("Per minute"), head("Made of")]];
  costs.forEach(([a, b, c], i) => {
    const fill = { color: i % 2 ? "FFFFFF" : TINT.grey };
    right.push([small(a, { bold: true, fill }), small(b, { bold: true, fill, color: K.accent2 }), small(c, { fill })]);
  });
  s.addTable(right, { x: 7.4, y: 1.68, w: 5.48, colW: [1.35, 1.15, 2.98], rowH: 0.5, border: { type: "solid", pt: 0.5, color: TINT.line }, objectName: "Cost per minute" });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.4, y: 4.3, w: 5.48, h: 2.0, fill: { color: TINT.out }, line: { color: TINT.out }, rectRadius: 0.06, objectName: "Other costs" });
  s.addText([
    { text: "Other costs", options: { bold: true, color: K.accent2, fontSize: 12, breakLine: true } },
    { text: "Outbound campaign minute: $0.045 instead of $0.038", options: { bullet: { indent: 12 }, breakLine: true } },
    { text: "Phone number: $0.03 a day (≈ $0.90 a month)", options: { bullet: { indent: 12 }, breakLine: true } },
    { text: "Per agent, all-inclusive tier: ≈ $100 to $199 a month at 2 to 4 hours of calls a day", options: { bullet: { indent: 12 }, breakLine: true } },
    { text: "ElevenLabs in production: Business plan $990 a month (12,375 min, 40 calls at once)", options: { bullet: { indent: 12 }, breakLine: true } },
    { text: "Lambda, DynamoDB, S3, API Gateway, Secrets Manager: cents in the sandbox (not measured)", options: { bullet: { indent: 12 }, breakLine: true } },
    { text: "* Twilio rate and LLM cost are assumptions, not verified prices", options: { italic: true, color: K.dk2 } },
  ], { x: 7.55, y: 4.38, w: 5.2, h: 1.85, fontSize: 10.5, color: K.dk1, valign: "top", margin: 0, paraSpaceAfter: 3, isTextBox: true });

  s.addNotes("Sources: docs/proposal/modelo-de-costos.md (Amazon Connect list prices, verified 2026-11-10: voice $0.038/min on Connect Customer including Nova Sonic, Lex, generative voices, analytics and evaluations; telephony $0.0022 in and $0.0048 out per minute in the US; local number $0.03/day; outbound campaigns $0.045/min; third-party AI agents $0.01/min) and docs/research/verificacion-supuestos-2026-11-09.md (ElevenLabs $0.08/min plus LLM, Business $990/month). The LLM range ($0.005 to $0.045/min) and SIP or Twilio telephony are researchers' assumptions. Per-agent figures assume 20 days a month at $0.0415/min. The sandbox's own AWS services are not measured: check Cost Explorer before quoting.");
}

(async () => {
  await pres.writeFile({ fileName: "guide.pptx" });
  await applyTheme("guide.pptx", THEME);
  console.log("written");
})();
