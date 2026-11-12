# Libreto de pruebas: una llamada a la vez

Yo (Claude) lanzo cada llamada con Twilio. Tú contestas como agente en tu navegador. No se cambia nada del sistema durante las pruebas. Todos los datos son inventados.

**Cómo trabajamos**
1. Una prueba a la vez. Tú me dices "listo", yo lanzo la llamada.
2. El "cliente" es una voz sintética que habla sola, con pausas fijas de ~7 s entre frases. Háblale cuando termine cada frase.
3. Al colgar tienes **60 s** para llenar el formulario de cierre y pulsar **Submit** (no Cancel).
4. Después de cada prueba me dices qué viste y yo reviso por API la cola, el agente y la disposición.

**Antes de empezar** (una sola vez)
- [ ] Un navegador con `demo.agent1` en `/agent/`, **Available**, micrófono permitido, audífonos puestos.
- [ ] Para las pruebas de transferencia: otro navegador o perfil con `demo.agent2`, **Available**.
- [ ] Cierra las demás pestañas (la consola de Connect es pesada).
- [ ] Ya no se usa el agente simulado ni se cambia ningún perfil. El número de Twilio **no está registrado**, así que a esta línea siempre le sale el menú y **no se abre el perfil del cliente** en la línea de IA (solo el panel guía).

---

## Prueba 1: Agente de IA (inglés)

**Quién llama:** Twilio, a la línea de IA **+1 775 249 1758**. Dura ~100 s.
**Comando (lo lanzo yo):** `twilio_test_calls.py routing conv-ai`

### Parte A: el cliente habla con el bot (tú solo escuchas, ~60 s; comprobado en la llamada real de las 09:31)

| Quién | Dice |
|---|---|
| Sistema | "This call may be recorded." (ya no hay menú de idioma) |
| Bot | "Thank you for calling. How can I help you today?" (si tu número estuviera registrado: "Hi <nombre>, thanks for calling. How can I help you today?" y ya conoce tu cuenta) |
| Cliente | "Hi, I want to check my account." |
| Bot | "Sure. What is your account code?" |
| Cliente | "Three." |
| Bot | "Thank you, Robert. Your balance is 2,640.75 dollars. Your payment was due on October 18. Is there anything else I can help you with?" |
| Cliente | "When is my payment due?" |
| Bot | "Your payment was due on October 18. Is there anything else I can help you with?" |
| Bot | (silencio) "I am still here. You can ask about your balance, your due date, how to pay…" (dos veces: las dos frases siguientes del cliente caen mientras el bot habla y no las oye) |
| Cliente | "I need a payment arrangement. I want to talk to a person." (el bot oye "person") |
| Bot | "Of course. I will connect you with a team member." |

### Parte B: la llamada llega a ti (tú eres agent1)

Suena **agent1** y contesta solo. Debes ver el panel **"Transferred by the AI assistant"** con:
- Motivo: **Customer asked for a person**
- Resumen: Robert Miller, account 3: 22 days past due, balance $2,640.75, payment due 2026-10-18.
- Cuenta 3 · Idioma English · Cola 16 to 30 days past due

El cliente te dice 3 frases (~7 s entre ellas). Responde justo después de cada una:

| Cliente | Tú (agente) |
|---|---|
| "Hi, the assistant said you can help me set up a payment plan." | "Yes, I can help. This is an attempt to collect a debt. I see your account is 22 days past due." |
| "I can pay half now and the rest on the twenty eighth." | "That works: half today and the rest on the 28th, with no extra fees. The arrangement is noted." |
| "Great, thank you. That's all." | "You're welcome. Thank you for calling, have a great day." |

Tu primera frase incluye "attempt to collect a debt": así queda la categoría `Collection_notice_given`.

### Parte C: al colgar (60 s)

Aparece **Call wrap-up**. Elige:
- Disposition: **Payment arrangement set**
- Follow Up: **Yes**
- Resolved: **No**
- Notas: `Half now, rest on 2026-11-28`
- Pulsa **Submit**.

### Qué reviso yo después
- La cola y el agente (16 a 30 días, agent1), `outcome=escalate`, motivo y resumen.
- Los cinco datos del cierre: `disposition`, `followUp`, `resolved`, `wrapUpSummary`, `wrapUpNotes`.
- El diálogo del bot en CloudWatch.
- A los ~10 minutos, la transcripción, el resumen y las categorías (se ven con `demo.admin`).

### Está OK si
- El bot contestó cada frase y te pasó con una persona.
- Te sonó a ti y viste el panel con el motivo y el resumen.
- El formulario guardó los cinco datos.

---

## Pruebas siguientes (una por una, cuando termines la anterior)

| # | Qué probamos | Cliente | Marca | Va a | Lo que haces tú |
|---|---|---|---|---|---|
| 2 | Menú en inglés | Twilio, línea principal +1 775 245 6050 | 1, cuenta 3 | agent1 (16–30 días) | Conversación de cobranza (6 frases del cliente) y cierre con Submit |
| 3 | Menú en español | igual | 2, cuenta 2 | agent1 (1–8 días) | Igual, en español |
| 4 | Estatus especial (Redemptions) | igual | 1, cuenta 5 | **agent2** | Contestas con agent2 |
| 5 | **Transferencia agent1 → agent2** | igual (cuenta 3, inglés) | 1, cuenta 3 | agent1 y luego agent2 | A mitad de la llamada: Quick connects → **"CS - Transfer to Redemptions"**; agent2 contesta; agent1 pulsa Join y cuelga |
| 6 | Disputa | igual | 1, cuenta 4 | agent1 (31+ días) | El cliente dice que ya pagó; disposición **Dispute** |
| 7 | IA en español | línea de IA | 2 | agent1 | Como la prueba 1, en español |
| 8 | Cuenta que no existe | línea principal | 1, cuenta 7 | agent1 (atención general) | "We could not find the account…" |

Para cada una te doy el libreto corto antes de lanzarla.

## Si algo falla
- No suena: agent1 no está Available o el micrófono está bloqueado. Corrígelo y me avisas; no repito la llamada hasta que me digas.
- No ves el formulario: solo aparece durante los 60 s después de colgar.
- Si te equivocas con una disposición: no pasa nada, es una prueba. Dime cuál elegiste.
- Si la consola va lenta: cierra pestañas y espera a que cargue antes de pulsar.
