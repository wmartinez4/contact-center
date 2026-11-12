# Q&A script for the MEI discovery meeting and demo (Nov 11, 2026)

Internal. Not for the client. Answers to say aloud are in English ("Say"). The notes marked "Para ti" are in Spanish and tell you how solid the answer is, what not to claim and what to do if the question goes further.

**Status key.** *Verified* = shown on a call or read on the AWS page. *Assumption* = ours. *Open* = we do not know yet; say so and take it as an action item.

## 0. Ground rules

1. **Say it is an evaluation.** Any implementation needs a separate approval, and this is separate from MEI's AI QA project (Jacob's emails).
2. **All demo data is invented.** A simulated lookup plays the role of iDMS. Say it at the start and again before the AI call.
3. **Never promise** (from the meeting prep): a fixed price or a migration date without the data; that Connect replaces the office phones by itself; that the AI Spanish sounds natural with real accents; that iDMS will integrate; legal compliance.
4. **When you do not know, say what you need.** "We don't know yet; we need X from you and we will confirm in the summary within 24 hours."
5. **This is not a quote.** No prices, ranges or margins are offered to MEI today; the itemized estimate and SOW come after the data arrives.
6. **Keep a list of open items** during the meeting (section 13 has the usual ones).

## 1. Opening frame (30 seconds)

> "Today is an evaluation, not a commitment. We'll cover what Amazon Connect would replace, what else you'd need, and how we'd deliver and support it. The demo uses invented accounts and a simulated lookup in place of iDMS, so you can see the behaviors, not your data. Anything we can't answer today, we'll list and come back to within 24 hours."

*Para ti:* Antes de empezar, aclara con Jacob tres cosas: (1) si esperan la demo hoy o después (su correo la describe como paso posterior), (2) qué es el "AI QA existente" y quién es el proveedor, (3) si "reemplazar" es solo el contact center o también la oficina.

## 2. Scope and positioning

**Q: What exactly would Amazon Connect replace?**
Say: "For the contact center: call routing in English and Spanish, queues, transfers, callbacks, recording, supervisor reporting, and optionally an AI voice agent. It does not by itself replace extensions, per-person voicemail or desk phones for the rest of the office. First we need to know which of the 210 planned users actually take or make customer calls."
*Para ti:* Verificado en la investigación (Connect no trae extensiones, buzón por persona, teléfonos SIP, paging, fax ni park). No prometas el reemplazo total. La oficina se decide en una fase 2.

**Q: Why Amazon Connect and not upgrading Zultys or another contact-center vendor?**
Say: "We evaluated three paths: Connect with its native AI, ElevenLabs as the voice layer, and Zultys 19. Connect is where the contact-center evidence is strongest and it is usage-based, with no seat licences. We haven't done a head-to-head against other vendors such as Genesys, NICE or Five9, and we can add that if you want it."
*Para ti:* Abierto. Zultys 19.0.20 salió el 13 de octubre sin detalle público, y BrevAll ya no menciona Zultys en su sitio. No hay comparación con otros proveedores: no inventes diferencias. Zultys anunció licencias de pago a futuro (dato de su release 19).

**Q: What is the role of ElevenLabs?**
Say: "It's an option for the AI voice layer. In the demo, the fixed announcements use ElevenLabs audio imported as prompts, and the live AI agent uses Amazon's own Nova 2 Sonic. ElevenLabs inside Connect for live conversation is in limited availability today."
*Para ti:* Hecho (documentación de ElevenLabs, 9-nov). ElevenLabs cuesta ~$0.08/min más el modelo de lenguaje, aparte de Connect.

**Q: Is this the same project as the AI QA work?**
Say: "No. We treat it as separate. What we need to confirm is that Connect can deliver the recordings and metadata your AI QA vendor needs."

## 3. Call handling

**Q: Can you route by days past due and still give priority to special statuses like Redemptions or EPD?**
Say: "Yes. The flow asks a lookup for the account's status and days past due and checks the special status first. In the demo, a Redemptions account 12 days past due goes to Redemptions, not to the 9 to 15 queue."
*Para ti:* Verificado: los 7 casos pasaron en llamadas de prueba (10-nov). Depende de que iDMS entregue esos datos. OFR/Skip sigue sin definirse: pregunta qué significa.

**Q: How does it recognize who is calling?**
Say: "By caller ID, in the demo with invented customers. A known number skips the menus and gets a personal greeting; an unknown number gets a language menu and is asked for an account number. In production the lookup would read iDMS."
*Para ti:* Verificado en la demo. La verificación de identidad (preguntas de seguridad) es regla de MEI y no está construida.

**Q: Can transfers keep context and a single call ID?**
Say: "Every transfer is a new contact in Connect. We stamp one call ID on the first leg and carry it, so the whole conversation is one record for reporting. The agent who receives it sees who the customer is and where the call came from."
*Para ti:* Verificado en llamadas reales (consulta y directa). Documentado por AWS: los atributos se comparten entre los contactos con el mismo contacto inicial.

**Q: What about callbacks?**
Say: "Connect supports queued callbacks, so the customer keeps their place without waiting on the line. We tested it on a call."
*Para ti:* Verificado (confirmado por Willian). Pendiente de precios, no de funcionamiento: en Basic, AWS lista "customer callback" como no incluido y no está claro si es este callback de cola (ver sección 13, punto 12).

**Q: How do you measure the 27% transfer rate and reduce it?**
Say: "From the contact records, which link every leg of a call, by queue and by agent. First we need to agree what counts as a transfer; the 27% figure needs a definition. Reducing unnecessary ones comes from routing to the right team first and giving the receiving agent context."
*Para ti:* Hecho en lo técnico. No sabemos cómo midieron el 27% (30-sep, por validar).

**Q: Do you support outbound calling and dialers?**
Say: "Yes. Connect can place outbound calls, including campaigns. The compliance rules for outbound collections, calling hours, frequency and consent, need your legal team's input and shape the design."
*Para ti:* Campañas: $0.045/min en Connect Customer. La prueba real fue una llamada saliente a Colombia. No hay marcador en la demo. No sabemos si MEI hace llamadas salientes automáticas hoy (pregunta 12 de la preparación).

**Q: Sales and Service routing: vehicle service, insurance, titles and payoffs, dealer sales?**
Say: "Same mechanism: a menu or a lookup picks a queue. We need your rules for who answers each and during which hours."
*Para ti:* Lo pidió Jacob y no está en la demo. Es estándar, no probado.

## 4. Recording, metadata and AI QA

**Q: Will you record all Collections calls: inbound, outbound and transferred, whatever the length?**
Say: "Connect records at the queue and agent level and stores the files in an S3 bucket you control. We've verified inbound recordings. We'd test outbound, transferred and very short calls in discovery so we can promise it for every case."
*Para ti:* Entrantes verificadas. Salientes, transferencias externas y llamadas muy cortas sin probar. Matiz de AWS: una transferencia externa hecha por el agente corta la grabación cuando el agente se va.

**Q: Can you supply the metadata our AI QA vendor needs: agent, queue, number, date and time, duration, call ID, call legs and recording file?**
Say: "The contact record has those fields: agent, queue, the customer's number, timestamps, duration, contact IDs and the recording location, plus our call ID across legs. We need your vendor's exact field names and format to match them."
*Para ti:* Abierto y es el requisito que más les duele. No sabemos quién es el proveedor ni qué campos exige. Pregunta: cómo recibe hoy las grabaciones, nombres exactos de campos, cómo define "tramo".

**Q: Do you have your own call analytics or QA?**
Say: "Yes, Connect includes conversational analytics: transcript, sentiment, an AI summary in English and Spanish, and automatic categories such as promise to pay, payment arrangement, hardship, dispute and callback. It is optional and priced per minute. The supervisor sees them in the demo."
*Para ti:* Verificado en llamadas de prueba (10-nov). Resumen se omite si hay muy poca conversación. No presentes esto como sección de QA con IA: la decisión de Willian es mostrarlo en Reportes y como complemento del nivel 2.

**Q: How long do you keep recordings and can we keep the old ones?**
Say: "Retention is configurable on the storage side. Historical Zultys recordings can stay where they are, or be imported for analysis; we'd decide that with you."
*Para ti:* Connect conserva el registro de contacto 24 meses. AWS permite importar grabaciones de otros sistemas (julio de 2026); no sabemos si Zultys exporta ni emite SIPREC.

## 5. iDMS, CRM and payments

**Q: Can you integrate with iDMS / DealerSocket?**
Say: "Connect calls external systems through a function, so if iDMS has an API or a data feed we can read the account and, if it allows, write back notes or promises to pay. We haven't seen iDMS. That is the biggest dependency: without a usable interface no platform can route by days past due automatically."
*Para ti:* Abierto. Pide: ¿API o base de datos?, ¿quién la administra?, ¿qué podemos leer y escribir?, ¿cargo de DealerSocket?

**Q: What does the agent see when the call arrives?**
Say: "In the demo, a customer profile with simulated data and a panel with name, account, status, days past due and language. If you use a CRM, its page can open beside the softphone."
*Para ti:* Verificado en la demo. No prometas integración con un CRM que no conocemos.

**Q: Can customers pay by phone? Can the AI take payments?**
Say: "Connect can collect card digits on the keypad encrypted, without the agent hearing them, and hand them to your processor. That needs your processor and a PCI design review. The AI agent in the demo only informs: balance, due date, how to pay. It takes no payments or card data."
*Para ti:* Es un diseño, no está construido. Pregunta qué procesador usan y quién es dueño de PCI. No digas que la solución "cumple PCI".

**Q: We have Text-to-Pay. Can we keep it?**
Say: "Yes, that's our assumption. If the link were sent from Connect instead, SMS costs about $0.014 per message plus the carrier fee, and the sending number needs carrier registration that can take up to 15 business days."
*Para ti:* No sabemos qué proveedor es ni cómo se asienta el pago en iDMS.

**Q: Payment arrangements: rules, approvals, system updates and confirmation?**
Say: "The agent can record the outcome in a wrap-up form, and the rules and approvals are yours to define. Connect executes them; automating the arrangement depends on iDMS write access."
*Para ti:* Está en la lista de requisitos de Jacob y no hay demo. La disposición está **configurada**, el guardado de punta a punta **no está confirmado**: di "configured".

## 6. AI voice agent

**Q: How natural is the Spanish?**
Say: "We use the US Spanish voices and the agent can switch language on request, keeping the account. We tested English, a language switch and a hand-over on scripted calls, and we haven't measured Spanish quality with real accents. We'd test it with your callers' calls before relying on it."
*Para ti:* Nadie ha medido el español con acentos reales. Usar es-US, no es-MX (es-MX no tiene voz agéntica ni analítica en la tabla de AWS).

**Q: What happens when the AI can't help?**
Say: "It hands the caller to a person in the right queue. The agent sees why, a summary, the account, the language and the queue. If the AI itself fails, the call goes to a person instead of hanging up."
*Para ti:* Verificado en llamadas de prueba.

**Q: Is it legal for an AI voice to call or talk to debtors?**
Say: "That needs legal review. The FCC treats AI-generated voices as artificial under the TCPA, and a new FCC rule on revoking consent takes effect November 25, 2026. We'd design the disclosure and consent flow with your counsel."
*Para ti:* La regla de la FCC viene de fuentes secundarias (9-nov); no leí la orden. No des asesoría legal. En la demo el AI solo atiende llamadas entrantes y no cobra.

**Q: Does the AI add cost?**
Say: "No separate charge: a minute handled by the AI agent costs the same as any voice minute on the Connect Customer level. The benefit is agent time saved."
*Para ti:* Verificado en la página de precios (10-nov). Modelo: Nova 2 Sonic; Nova 2.5 existe en Bedrock pero Lex solo acepta Nova 2 hoy; cambiar después es configuración. Reverifica antes de prometer fechas.

## 7. Reports and supervisors

**Q: What can supervisors see?**
Say: "Real-time views of agents and queues, listen-in, historical reports (contacts handled, abandoned, average wait, transfers by queue and agent), and for each call the recording, transcript, sentiment and summary."
*Para ti:* Tiempo real y escucha verificados. Los reportes históricos hay que guardarlos antes (no hay API). Barge y reportes programados: estándar, no probados.

**Q: Can you give us repeat-contact and self-service completion numbers?**
Say: "They aren't standard metrics. We compute repeat contacts from contact records by customer number, and self-service completion from an outcome the AI or menu flow records. They are small custom reports and belong in the SOW."

## 8. Compliance

**Q: Who is responsible for TCPA, Reg F and PCI?**
Say: "You are, with your counsel; we design the system so the controls are possible: recording notices in English and Spanish, consent and revocation handling, calling hours, and keeping card data out of the agent's path. We don't give legal advice."
*Para ti:* Pregunta a MEI: ¿cobra cuentas propias o de terceros?, ¿en qué estados llama?, ¿quién es el responsable de cumplimiento? Grabación con consentimiento de todas las partes aplica en varios estados.

## 9. Pricing and commercial

**Q: How much does it cost?**
Say: "Today is an evaluation, not a quote. What we can share is how Amazon Connect is billed: no per-seat licence, usage billed per second over the whole call (menu, queue and agent) plus telephony, with AWS's public list prices. Once we have your volumes and the data we asked for, we'll send an itemized estimate and a proposed SOW with ranges and stated assumptions."
*Para ti (interno):* Precios de lista de AWS leídos el 10-nov: Connect Customer $0.038/min, Basic $0.018/min, telefonía EE. UU. $0.0022 entrante y $0.0048 saliente. Costo AWS por agente al mes a 3 h al día: ~$77 / ~$131 / ~$149 (niveles 1, 2, 3). El precio sugerido (borrador, margen 30 %) y la cuota de operación (~$9,500 al mes) son internos y siguen sin definirse: **no los menciones ni des rangos.** Si insisten en una cifra, usa solo los precios de lista de AWS.

**Q: Which level do we need?**
Say: "The level applies to the whole account. Level 1 covers routing, queues, transfers and recording. Level 2 adds analytics. Level 3 adds the AI voice agent, generative voices and automated evaluations."

**Q: What is not included?**
Say: "Implementation labor, number porting, the parallel run with Zultys, the payment processor and PCI work, any iDMS or DealerSocket fee, third-party voice, toll-free minutes, SMS for payment links and the AWS support plan."
*Para ti:* La tarifa por minuto de los números gratuitos (800) no aparece en las páginas de AWS: sin confirmar. Es probable que cobranza use 800.

**Q: Whose AWS account is it?**
Say: "Two options: usage billed through us as a bundled per-agent price, or your own AWS account with usage billed by AWS at cost plus our fee. We'd recommend deciding that in the SOW."
*Para ti:* Decisión nuestra pendiente. Un descuento por volumen de AWS se compartiría por acuerdo.

**Q: Is there a minimum term?**
Say: "AWS has no minimum or long-term contract. For our managed service we'd propose a 12-month term and a price review after 90 days of real volumes."
*Para ti:* Propuesta tuya, ajústala. Plazo de 12 meses y bandas de agentes son borrador.

**Q: How does this compare with what we pay today?**
Say: "To compare we need what you pay today for Zultys licences, BrevAll support and carrier minutes. The number to compare is usage per agent per month, plus the support fee."

**Q: Can you give a fixed price today?**
Say: "No, and we won't quote today. Without volumes, contracts and an iDMS path, we can give ranges with explicit assumptions. After the data arrives we'll send an itemized estimate."

## 10. Delivery, support and migration

**Q: How long would it take and how would you deliver it?**
Say: "Our planning assumption is three to five months end to end: discovery and design, build and integrate, test with a parallel run, train and pilot, cutover, then hypercare. It depends on iDMS access, the number of agents, numbers to port and the rules still to define."
*Para ti:* Es supuesto nuestro, no cotización. Portabilidad de números: 2 a 4 semanas, se pide con hasta 30 días de anticipación. Cuotas por defecto: 10 llamadas simultáneas y 10 números; hay que pedir aumento con tiempo.

**Q: What support do you offer after go-live?**
Say: "Our proposal is standard support during business hours, Monday to Friday, 8:00 to 17:00 Central: monitoring, changes to flows, queues and prompts, user administration, reports and a monthly review. Response targets would be one hour if the service is down, four business hours for a major issue and the next business day otherwise. After hours or 24/7 would be quoted separately."
*Para ti:* Propuesta (lámina 12, borrador); los tiempos de respuesta son estándar de la industria, no un benchmark investigado. Aún no sabemos qué cobertura espera MEI: pregunta.

**Q: What is the role of BrevAll?**
Say: "They support Zultys today, so we'd need them for the coexistence period and for the routing that stays on Zultys until cutover. Their long-term role is yours to decide."
*Para ti:* Abierto. Su sitio ya no menciona Zultys.

**Q: What happens to the Zultys contract during the migration?**
Say: "We need the contract dates to plan the cutover window and any overlap cost. That's on our data request."

**Q: Can we start with a pilot?**
Say: "Yes. We'd suggest starting with one team and one queue group, with the old system in parallel, and widening after the numbers hold."
*Para ti:* Es una recomendación razonable; no tiene alcance ni precio definido.

## 11. Technical and risk questions

**Q: What if AWS goes down? What is the uptime?**
Say: "AWS publishes a service level for Connect and we'd confirm the current terms before quoting. We'd also design a fallback so calls reach a person if a lookup or the AI fails."
*Para ti:* No tengo el número de SLA verificado; no lo cites de memoria.

**Q: How many concurrent calls can it handle?**
Say: "Defaults are low, around ten concurrent calls, and AWS raises them on request. With your peak volumes we'd request the right quota early because increases can take weeks."
*Para ti:* Cuotas por defecto de la documentación (9-nov). Hay que conocer los picos.

**Q: Where is the data stored and who owns it?**
Say: "Recordings and contact data live in AWS in the account we agree on; in your own account you own them directly. Region and retention are configurable."
*Para ti:* Depende de la decisión de cuenta (ver sección 9).

**Q: Is the demo what you would deliver?**
Say: "It shows behaviors with invented data. A production build adds iDMS, your rules, security review, quotas, monitoring and testing. The demo isn't production code."
*Para ti:* No presumas tiempos de construcción: la demo se armó con atajos (consulta simulada).

**Q: Vendor lock-in? Can we leave?**
Say: "Connect is usage-based with no minimums, and the recordings and records are exportable. The flows and routing logic are Connect-specific, so we'd document them."
*Para ti:* Sin evidencia de costos de salida; no inventes.

## 12. Demo recovery lines

- **No ring / wrong agent:** "Let me show the same call from the records." (Contact search, one finished call.)
- **AI call fails:** "I'll play the recording of the same test from yesterday and I'll say it is a recording."
- **Wrap-up doesn't save:** "This is configured; I'll show how it looks and we'll confirm the storage in testing."
- **Customer panel empty:** "The data is also on the contact; here are its attributes."
- **Question about something not built:** "We haven't built that; here is how we would, and what we need from you."

## 13. Open items we cannot answer yet

| # | Item | Why it is open | What we need | Owner |
|---|---|---|---|---|
| 1 | iDMS/DealerSocket interface | Never seen | API or data feed, read/write scope, owner, fees | MEI |
| 2 | AI QA vendor and metadata | Unknown vendor and fields | Vendor name, field names, how recordings are delivered today | MEI |
| 3 | Volumes, peaks, agents per shift | Not provided | Calls per day and peak hour, minutes, % inbound/outbound, % Spanish | MEI |
| 4 | Who among the 210 takes or makes customer calls | Active-user review open | Count by area | MEI |
| 5 | How the 27% was measured | "Historical, to validate" | Definition of a transfer | MEI |
| 6 | Meaning of OFR/Skip and other statuses | Unknown | List, owners, update frequency | MEI |
| 7 | How customers pay today; processor; Text-to-Pay vendor | Unknown | Methods, processor API, vendor | MEI |
| 8 | Compliance owner and jurisdictions | Unknown | Own or third-party accounts, states, counsel | MEI |
| 9 | Current costs and contract dates | Not provided | Zultys, BrevAll, carriers, expiry dates | MEI |
| 10 | Target date, budget range, success criteria, approval process | Not asked yet | Dates, ranges, KPIs, decision makers | MEI |
| 11 | Toll-free per-minute telephony rate | Not on AWS pages | Confirm in the AWS calculator | Us |
| 12 | Is Basic's "customer callback not included" the queue callback? | Ambiguous | Confirm with AWS or test | Us |
| 14 | Disposition save end to end | Configured, not confirmed | One call with Save | Us |
| 15 | Outbound, transferred and very short call recording | Not tested | Test calls | Us |
| 16 | Spanish AI quality with real accents | Never measured | Test with real calls | Us |
| 17 | Zultys 19.0.20 contents; BrevAll partner level | No public detail | Ask BrevAll | MEI / BrevAll |
| 18 | Connect SLA terms | Not verified | Read the AWS SLA | Us |
| 19 | Costs of other AWS services (Lex, Lambda, Customer Profiles, storage) | Not measured | Cost Explorer on the demo account | Us |

## 14. Questions to ask MEI before closing

1. Do you expect the demo today or as a later step?
2. Who is the AI QA vendor and what do they need from the recordings?
3. Is this about the contact center only, or also the office phones? Who among the 210 users takes or makes customer calls?
4. Do you collect your own accounts or third-party accounts, and in which states?
5. How do customers pay today, and through which processor?
6. Can we get access to the iDMS interface, and who owns it?
7. What are your target date, budget range and success measures (transfers, wait, abandonment)?
8. Who decides, and how does the SOW get approved?
9. What support coverage do you expect?
