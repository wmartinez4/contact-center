# Glosario

Siglas y términos que aparecen en el pedido de MEI y en la evaluación.

## Del mensaje de MEI

| Sigla | Significado | Qué es, en simple |
|---|---|---|
| **SOW** | *Statement of Work*, "declaración de trabajo" | Documento que define qué se hará, quién hace qué, entregables, tiempos y responsabilidades. Es la parte del contrato que describe el trabajo, no solo el precio |
| **PBX** | *Private Branch Exchange*, "central telefónica privada" | El sistema telefónico de la empresa: extensiones, llamadas internas y salida a la red. Aquí es Zultys |
| **QA** | *Quality Assurance*, "aseguramiento de calidad" | Revisar la calidad de las llamadas: ¿el agente siguió el guion, fue cortés, cumplió las reglas? |
| **AI QA** | QA con inteligencia artificial | Un sistema de IA que escucha o lee las llamadas grabadas y las puntúa, en lugar de una persona |
| **AI** | *Artificial Intelligence*, "inteligencia artificial" | |
| **iDMS** | *Dealer Management System* de DealerSocket | Software donde el concesionario o financiera guarda cuentas, contratos, pagos y mora. Es el sistema de registro de MEI |
| **DMS** | *Dealer Management System*, "sistema de gestión de concesionarios" | El tipo de software al que pertenece iDMS |
| **EPD** | *Early Payment Default*, "incumplimiento temprano de pago" | El cliente no paga las primeras cuotas, poco después de comprar. Es un grupo de cobranza con trato especial |
| **OFR/Skip** | Ver nota abajo | Dos categorías de cuentas especiales |
| **Text-to-Pay** | "Pagar por mensaje de texto" | Se envía un SMS al cliente con un enlace para pagar. No es una sigla, pero es un producto que MEI quiere conservar |

## Términos que no son siglas

- **Redemptions:** un cliente cuyo vehículo fue recuperado (embargado) y que puede recuperarlo pagando lo adeudado.
- **Skip:** *skip tracing*, localizar a un cliente que dejó de responder o que cambió de domicilio o teléfono sin avisar.
- **Titles/payoffs:** títulos de propiedad y cifras de liquidación, es decir, cuánto falta para saldar el contrato.
- **Call-leg:** cada tramo de una llamada. Una llamada que pasa del cliente a la IA, de ahí a un agente y luego a un supervisor tiene varios tramos.
- **Contact center:** área de atención con agentes dedicados a llamadas, distinta de los usuarios normales de teléfono de la oficina.

## Pendiente de aclarar

- **OFR:** no está confirmado qué significa en el contexto de MEI. Aparece junto a "Skip" como categoría de cuenta especializada, pero su significado exacto es interno de la empresa o del sector. Preguntar en la reunión de descubrimiento: "¿qué significa OFR y qué reglas de ruteo tiene?".

## Siglas de la investigación

| Sigla | Significado |
|---|---|
| **SIP** | *Session Initiation Protocol*: protocolo estándar para llamadas por internet |
| **DTMF** | Tonos del teclado telefónico (cuando el cliente teclea números) |
| **TCPA** | *Telephone Consumer Protection Act*: ley de EE. UU. sobre llamadas y mensajes automatizados, que exige consentimiento |
| **FDCPA** | *Fair Debt Collection Practices Act*: ley de EE. UU. sobre prácticas justas de cobranza de deudas |
| **Reg F** | Regla del CFPB que desarrolla la FDCPA (límites de llamadas, horarios) |
| **UDAAP** | Prácticas desleales, engañosas o abusivas |
| **PCI** | Estándar de seguridad para datos de tarjetas de pago |
| **CTR** | *Contact Trace Record*: registro de Amazon Connect con los datos de cada contacto |
| **BHPH** | *Buy Here Pay Here*: concesionarios que financian directamente al cliente |
| **PoC** | *Proof of Concept*: prueba de concepto |
| **SLA** | *Service Level Agreement*: acuerdo de nivel de servicio (disponibilidad, tiempos de respuesta) |
| **LLM** | *Large Language Model*: el modelo de lenguaje detrás de la IA conversacional |
| **API** | Interfaz para que un sistema consulte o envíe datos a otro |

## Agregados el 2026-11-09

| Término | Qué es |
|---|---|
| A2A (agent-to-agent) | Función de Connect (documentada ~sept. 2026) para que un agente de IA externo hable con el cliente o apoye al agente de Connect. Cuota por defecto: 5 conexiones simultáneas |
| SIPREC | Protocolo estándar para copiar el audio de una llamada a un sistema de grabación o análisis. Connect lo recibe desde un SBC para analizar llamadas de otro sistema |
| SBC (Session Border Controller) | Equipo o servicio que se pone entre la PBX y la red de telefonía; puede emitir SIPREC |
| Segment attributes | Atributos de Connect que pertenecen a un solo tramo de la llamada, a diferencia de los atributos de usuario, que se comparten y pueden sobrescribirse en una transferencia |
| Agentic CX designer | Lienzo sin código de Connect (disponible desde 2026-09-02) que mezcla pasos fijos y pasos de IA |
| Nova 2 Sonic | Versión más reciente del modelo de voz de Amazon; agrega voces es-US y polyglot |
| es-US / es-MX | Locales de español. En Connect, es-US tiene voz agéntica y analítica; es-MX no |
| Revocación de consentimiento | Cuando el cliente pide no recibir más llamadas; la FCC publicó una orden vigente desde 2026-11-25 |
