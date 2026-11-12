# Evaluación de contact center para MEI

## Qué es este proyecto

Evaluación (no implementación) de una nueva plataforma de contact center para MEI. Cualquier implementación requeriría aprobación aparte. El cliente pidió una reunión de descubrimiento, una demostración con sus flujos reales y una propuesta escrita con costos itemizados y un SOW.

## Situación actual del cliente

- Plataforma: Zultys MX (versión 18.4), soportada por BrevAll Technologies.
- Tamaño de planificación: 210 usuarios (123 estándar, 85 de contact center, 2 premium). Pendiente la revisión de usuarios activos.
- Áreas: Finanzas/Cobranza, Corporativo, Ventas y Servicio.
- Sistema central: iDMS / DealerSocket (identificación de cuenta y ruteo). Existe un Text-to-Pay que se debe conservar.
- Referencia histórica: ~27% de las llamadas de Cobranza se transfieren (revisión del 30 de septiembre, por validar).
- Volúmenes, minutos y picos reales: sin validar.

## Requisitos a evaluar

- Ruteo en inglés y español.
- Cobranza por mora (0, 1–8, 9–15, 16–30, 31+ días) y por estatus especializado (Redemptions, OFR/Skip, Early Payment Default). El estatus especializado tiene prioridad.
- Ruteo de servicio del vehículo, seguros, títulos/payoffs y ventas en concesionarios.
- Reconocimiento y verificación del cliente, conversación bilingüe natural, información de cuenta y pagos.
- Acuerdos de pago con reglas de negocio, aprobaciones, actualización de sistemas y confirmación.
- Transferencias y callbacks que conserven el contexto.
- Grabación de todas las llamadas de Cobranza (entrantes, salientes y transferidas, sin importar la duración).
- Metadata consistente: agente, cola/departamento, número, fecha/hora, duración, call ID, tramos de llamada y archivo de grabación, para el QA con IA.
- Los flujos con IA son requisitos en evaluación; no se asumen operando hoy.

## Opciones bajo evaluación

1. **Amazon Connect** con su IA nativa (Nova Sonic, Lex, Contact Lens).
2. **ElevenLabs** como capa de voz conversacional (sobre Connect o telefonía existente).
3. **Zultys 19 / AI Receptionist** (actualización del sistema actual).

## Dirección del proyecto (actualizada 2026-11-09)

La meta planteada es **reemplazar todo lo que MEI tiene hoy con Amazon Connect como núcleo** (contact center de ~85 agentes y ~125 usuarios de oficina), con voz de ElevenLabs u otro proveedor según los resultados de las PoC.

Lo que mostró la investigación ([connect-como-pbx-oficina.md](docs/research/connect-como-pbx-oficina.md)): Connect es sólido para el contact center, pero **no trae de fábrica** extensiones, buzón por persona, teléfonos de escritorio SIP, paging, fax ni estacionar/recoger llamadas. El puente hacia un PBX existente cuesta ~$100 por conector al día y conectar un operador externo no es un patrón soportado sin revisión de AWS. Por eso la postura de trabajo es **por fases**: contact center primero (PoC 1 y 2), oficina decidida con una PoC corta (PoC D). "Todo en Connect" solo es creíble si la PoC D pasa y se cumplen las condiciones del informe. No prometer el reemplazo total antes de probarlo.

## Estado

- **Verificación de supuestos al 2026-11-09:** `docs/research/verificacion-supuestos-2026-11-09.md`. Los informes de `docs/research/` llevan al inicio un recuadro de correcciones. Si un informe contradice la verificación, gana la verificación (conector: $100 al día + $0.032/min; ID único resuelto por documentación; es-US, no es-MX; A2A documentado; TCPA vigente desde 2026-11-25).
- **Integración nativa Connect–ElevenLabs (A2A), probada el 2026-11-12:** el lado de AWS funciona de punta a punta en `cs-connect-demo`. El único bloqueo es que ElevenLabs no tiene activado el transporte de Amazon Connect en el workspace. **Soporte de ElevenLabs respondió el 2026-11-12 que la integración solo se activa con plan Enterprise, incluso para una PoC** (no en Starter ni como prueba); precio y concurrencia se negocian con ventas (https://elevenlabs.io/enterprise). Mientras tanto, la vía para mostrar ElevenLabs es transferir la llamada a un número propio de ElevenLabs (ruta B), diseñada en `poc/elevenlabs-ruta-b/diseno.md`. Detalle, errores resueltos y comparación con las investigaciones de ChatGPT y Gemini: `docs/research/comparacion-investigaciones-a2a.md`.
- **Ruta B construida y probada el 2026-11-12:** entrante (+1 775 255 0671) y saliente (Connect marca al cliente y pasa la llamada a Sofía). Acuerdos en DynamoDB, transcripción y audio en S3, atributos en el contacto y en el perfil. El supervisor inicia llamadas con IA desde la app "Llamar con IA" del espacio de trabajo (solo perfiles CallCenterManager y Admin; solo a números de una lista de prueba). Un probador automático (bot de Lex con Nova Sonic + Bedrock) llama a las líneas haciendo de cliente. El correo de confirmación se anuncia pero no se envía. Comandos y recursos: sección "Demos de la ruta B" de `poc/README.md`. Revisión legal pendiente antes de llamar a clientes reales con IA (TCPA, Reg F).
- Resumen ejecutivo de una página (lo que se puede y no se puede): `docs/proposal/resumen-ejecutivo.md`.
- Informe de oficina/PBX, telefonía, 911, opciones de UCaaS, inventario de Zultys y costos: `docs/research/connect-como-pbx-oficina.md`.
- Informe de capacidades (noviembre de 2026): `docs/research/elevenlabs-connect-zultys-evaluacion.md`.
- Recomendación del informe: prueba de concepto de 4 a 6 semanas sobre Connect, comparando su IA nativa contra ElevenLabs.
- Sin datos de MEI sobre iDMS, volúmenes ni cumplimiento. Las cifras de precios deben reverificarse antes de cotizar.

## Entorno de pruebas disponible

- **Connect (sandbox actual, confirmado 2026-11-12):** perfil de AWS `cs-admin`, cuenta `383799408374`, us-east-1, instancia `cs-connect-demo` (`c2f9ca2b-eb05-4a82-9809-1d7c914333ba`). La instancia `olive-connect-demo-530c` (perfil `connect-demo`, cuenta `200845568816`) fue una prueba personal: **no usarla**. En `cs-connect-demo` ya existe el asistente de Q in Connect `ai-assistant`, asociado a la instancia (base de la integración nativa con ElevenLabs).
- **Connect (demo anterior, dato histórico):** el proyecto `~/olive.business.connect` quedó **archivado** el 2026-11-09 (ver su `docs/ARCHIVE.md`). Esa descripción sigue así, pero corresponde a la instancia personal: ya tiene Lex (inglés y español), voces Polly generativas, Lambdas .NET 10, DynamoDB y un flujo saliente. No tiene flujos entrantes, ruteo por mora, Nova Sonic ni ID único. Para MEI, crear recursos nuevos con prefijo propio y no tocar el demo de renovaciones.
- **ElevenLabs:** proyecto `~/voice_agent` (Python/FastAPI, Twilio, Supabase). Agentes de cobranza Jess y Sofia con cuatro herramientas web. Es de dic. 2025 a feb. 2026 y puede requerir ajustes. No revisé si sus endpoints tienen autenticación: usarlo solo con datos inventados.
- **Llamadas salientes a Colombia:** AWS las habilitó el 13 de oct. de 2026 y se verificó con una llamada real el 9 de nov. de 2026 (sonó y funcionó). Las pruebas salientes pueden ir a teléfonos de Colombia y de EE. UU. permitidos en la Lambda.
- Ambos proyectos tienen `.env` con secretos: no copiarlos a este proyecto.

## Estructura

- `docs/research/`: investigación y comparativas.
- `docs/discovery/`: preguntas y notas de la reunión de descubrimiento.
- `docs/proposal/`: costos, supuestos y SOW. Incluye `flujos-poc.md` (los cuatro flujos de la PoC).
- `poc/`: la PoC de Amazon Connect: `README.md` (mapa de transformación y reglas), `TEST_PLAN.md`, `data/personas.json` (casos inventados) e `infra/baseline-renewal-demo/` (copia de la infraestructura del demo anterior, sin secretos).
- `docs/glosario.md`: siglas y términos del pedido de MEI y de la investigación.

## Reglas del proyecto

- Separar siempre hechos verificados de inferencias y vacíos.
- No dar cifras de costo sin volúmenes validados; usar rangos con supuestos explícitos.
- Los temas regulatorios (TCPA, grabación, PCI, cobranza) requieren revisión legal.
- **Nombres de recursos nuevos (desde 2026-11-12):** genéricos y descriptivos (`agent1`, `caller1`, `supervisor`, `ElevenLabs`). No usar `mei`, `MEI` ni `demo` en nombres, descripciones o etiquetas. Los recursos de la integración con ElevenLabs se recrearon con nombres genéricos el 2026-11-12 (`ai-assistant`, `elevenlabs-agent`, `elevenlabs-handoff`, `elevenlabs-a2a`, `elevenlabs-bot`, secreto `elevenlabs/agent-api-key`). AWS no permite renombrar estos recursos: si hay que cambiar un nombre, se recrea.
