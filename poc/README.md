# PoC de Amazon Connect para MEI

Prueba de concepto exploratoria. Mide capacidades con datos inventados antes de invertir en algo más complejo.

- Flujos: [../docs/proposal/flujos-poc.md](../docs/proposal/flujos-poc.md)
- Plan de pruebas: [TEST_PLAN.md](TEST_PLAN.md)
- Casos de prueba: [data/personas.json](data/personas.json)

## Alcance: tres PoC, seis demos (propuesta pendiente de aprobación)

- **PoC 1, contact center:** D1 ruteo, D2 ID único y grabaciones, D3 saliente.
- **PoC 2, voz con IA:** D4, variantes Nova Sonic, diseñador agéntico, Deepgram + ElevenLabs y A2A.
- **PoC 3, oficina e híbrido:** D5 oficina (extensiones, buzón, menú, softphone, 911 con el 933) y D6 modelo de dos sistemas (transferencia externa e importación de grabaciones).

La meta es reemplazar todo con Connect como núcleo, pero la oficina se decide con la PoC 3.

**Demo adicional, agente de cobranza de ElevenLabs:** Connect transfiere la llamada a un número atendido por ElevenLabs, que negocia el acuerdo y lo guarda. Diseño en [elevenlabs-ruta-b/diseno.md](elevenlabs-ruta-b/diseno.md). La integración nativa (A2A) queda como investigación: requiere plan Enterprise de ElevenLabs. Detalle en [TEST_PLAN.md](TEST_PLAN.md). Ver [AGENTS.md](../AGENTS.md). Idioma fijo: es-US, no es-MX.

## Demos de la ruta B (ElevenLabs), instancia `cs-connect-demo`

Todos los scripts se corren desde la raíz del repo con `AWS_PROFILE=cs-admin poc/.venv/bin/python <script>`. Son re-ejecutables.

| Qué | Código | Despliegue / uso |
|---|---|---|
| API del agente (Lambda `voice-agent-api`, reglas, perfiles, acuerdos, post-call a S3) | `elevenlabs-ruta-b/api/` | `infra/elevenlabs-route-b/setup_api.py` |
| Agente de ElevenLabs (prompt, herramientas, voz, webhooks) | `elevenlabs-ruta-b/agent/prompt.md` | `infra/elevenlabs-route-b/setup_agent.py` |
| Flujo "CS - Inbound - Sofia AI" en +1 775 255 0671 ("Sofia AI line") | — | `infra/elevenlabs-route-b/setup_flow.py` |
| Usuario `demo.caller3` (+1 775 258 5298, que es el teléfono de María, cuenta 2, en Customer Profiles) | — | `infra/elevenlabs-route-b/setup_caller3.py` |
| **Saliente:** Connect llama al cliente y pasa la llamada a Sofía | — | `infra/outbound/call_customer.py [cuenta]` |
| **Teléfonos de los clientes de prueba:** +1 775 249 1708 (cuenta 10, Willian) timbra en `demo.caller2`; +1 775 258 5298 (cuenta 2, María) timbra en `demo.caller3` | — | `infra/outbound/customer_line.py ring caller2` o `ring caller3`; `restore` devuelve caller2 a "CS - Sandbox - Simple Flow" y deja caller3 sin flujo |
| **App del supervisor "Call with AI"** (Lambda `ai-call-launcher` con URL pública, app de terceros del espacio de trabajo) | `ai-call-launcher/` | `infra/ai-call-launcher/setup.py` |
| **Probador automático:** bot de Lex `call-tester` (voz Nova Sonic) + Bedrock (Claude Haiku 4.5) que hace de cliente | `call-tester/` (guiones en `scenarios.json`) | `infra/call-tester/setup.py`; correr: `infra/call-tester/run.py <escenario>` |

Notas:

- **App del supervisor:** se abre desde el menú **Apps** del espacio de trabajo de agente. Por eso el espacio "Supervisors" ya no tiene página de agente personalizada (la vista `agent-workspace-modern` no tiene menú de apps). Solo la ven los perfiles CallCenterManager y Admin. Llama únicamente a números de `TEST_DESTINATIONS` en su `setup.py` (hoy las líneas de caller2 y caller3 y el celular real de la cuenta 9, que participa en el demo). El acceso se controla con el ARN del usuario que da el SDK del espacio de trabajo, que no viene firmado: suficiente para el sandbox, no para producción (haría falta Cognito o el IdP delante). El navegador del espacio de trabajo bloquea `confirm()`, así que la llamada se confirma con un segundo clic. Debajo de la tabla, "Recent AI calls" muestra las últimas 20 llamadas salientes con Sofía (de la tabla `voice-calls`, campo `direction = outbound`): hora, cliente, resultado y quién la inició (el supervisor o `call-tester`). Las salientes anteriores al 2026-11-12 no tienen ese campo y no aparecen.
- **Cuenta 10 (Willian):** desde el 2026-11-12 tiene 12 días de mora en la cola "Collections - 9 to 15 days", sin estatus especial (antes era Redemptions), para que la IA pueda negociar en las pruebas salientes.
- **Cuenta 2 (María):** desde el 2026-11-12 su teléfono es la línea de `demo.caller3` (+1 775 258 5298), así que todas las líneas la reconocen cuando llama caller3, y esa línea timbra en caller3 para las salientes. Reemplaza el mapeo fijo `TEST_CALLERS` que tenía la API de la ruta B.
- **Probador:** el primer escenario (`maria-installments`, ruta B desde el número de caller3) pasó el 2026-11-12. Límites: no marca teclas (los menús de la línea principal se prueban con `infra/mei-demo/twilio_test_calls.py`), a veces responde a media frase, y cada `setup.py` crea una versión nueva del bot. Cada corrida guarda un acuerdo real en la tabla de pruebas.
- **Transcripción en Connect (2026-11-12):** el flujo "CS - Inbound - Sofia AI" activa Contact Lens después de identificar al cliente (idioma del cliente; resumen generativo solo en inglés). Contact Lens transcribe la grabación completa: Sofía aparece como *System* y el cliente como *Customer*. La copia de ElevenLabs sigue en S3.
- **Presentación de Sofía (2026-11-12):** se presenta como "Sofía, del área de cuentas", sin decir que es un asistente virtual (si le preguntan, responde que es un asistente de IA). Distingue la dirección de la llamada: el flujo pasa el atributo `direction` (las salientes lo ponen en `outbound`) y en las salientes agrega "Te llamo por un tema de tu cuenta", sin dar detalles hasta confirmar al titular. Tutea en español.
- **Nombres neutrales (2026-11-12):** lo que se ve en Connect no nombra al proveedor de voz: atributo `aiAgent = Sofia AI`, `aiConversationId` (antes `elevenlabsConversationId`), flujo "CS - Inbound - Sofia AI" (antes "ElevenLabs Transfer") y número "Sofia AI line". Los contactos anteriores conservan los nombres viejos. Los recursos de la prueba nativa (`elevenlabs-bot`, flujo "ElevenLabs Agent") no se renombraron: no se pueden renombrar sin recrearlos y solo los ve el admin.
- **Pendiente:** envío real de correo o SMS de confirmación; revisión legal antes de llamar a clientes reales con IA (incluido si hay que avisar que es una IA).

## De dónde viene

Esta PoC **transforma** el demo de renovaciones de `~/olive.business.connect` (archivado el 2026-11-09). Reutiliza su cuenta de AWS de pruebas, su instancia de Connect y su número reclamado. Una copia de la infraestructura de ese demo queda en `infra/baseline-renewal-demo/` como punto de partida y referencia, sin secretos.

## Entorno de AWS

- **Actualización 2026-11-12:** la instancia de trabajo es `cs-connect-demo` (perfil `cs-admin`, cuenta `383799408374`). Lo que sigue en esta sección describe la instancia personal anterior (`connect-demo`), que ya no se usa; ver `AGENTS.md`.
- Perfil `connect-demo`, región `us-east-1`. Cuenta de pruebas, **no es una cuenta de Olive**. Antes de cualquier operación: `aws sts get-caller-identity --profile connect-demo --query Account --output text`.
- Instancia de Connect `olive-connect-demo-530c`, creada por el stack `connect-demo-01-connect`. Tiene un número de EE. UU. reclamado y **las llamadas salientes a Colombia habilitadas por AWS** (verificado con una llamada real el 2026-11-09).
- **No borrar el stack `connect-demo-01-connect`**: borra la instancia y se pierden el número y la habilitación de Colombia.

## Mapa de transformación

| Pieza del demo anterior | Qué hacer | Destino |
|---|---|---|
| Stack 01 (instancia, horario 24/7, número, cola, perfil de ruteo) | **Conservar tal cual.** Agregar colas y perfiles de ruteo de MEI en un stack nuevo | Stack nuevo `mei-02-routing` |
| Stack 02 (DynamoDB, rol, 4 Lambdas de renovaciones) | **Reemplazar** por Lambdas de MEI: consulta de cuenta simulada, registro de resultados, recordatorio saliente | Stack nuevo `mei-03-backend` |
| Stack 03 (bot Lex en/es, voces generativas) | **Reemplazar** por un bot con las intenciones de MEI. Misma estructura en_US y es_US | Stack nuevo `mei-04-lex` |
| Stack 04 y `build_flow.py` (flujo saliente) | **Reutilizar el generador** (funciones `action`, `equals`, `message`, `write_outcome`). Generar los flujos F1 a F4 | Stack nuevo `mei-05-flows` |
| Lógica de campaña: destinos permitidos, consentimiento, no llamar, intentos, horario | **Reutilizar la idea** en el recordatorio saliente | Lambda de MEI |
| Precios, correo de renovación, repetición de cotización, presentación, audios de renovación | **Descartar** | No se lleva |
| Herramienta de comparación de voces (A/B a ciegas) | **Reutilizar** para la escucha a ciegas, cuando llegue el momento | Copiar de `~/olive.business.connect/tools/voice-comparison` |
| Usuario de agente `demo.agent` y bucket de artefactos | **Reutilizar** | Sin cambios |

Los recursos de AWS que no se reutilicen (stacks 02, 03 y 04 del demo de renovaciones) se borrarán **después** de validar los nuevos, y solo con confirmación explícita. **Hoy no se ha borrado ni cambiado nada en AWS.**

## Reglas

- ~~Prefijo `mei-` en todo lo nuevo.~~ Reemplazado el 2026-11-12: nombres genéricos y descriptivos, sin `mei` ni `demo` (ver `AGENTS.md`). No modificar los stacks `connect-demo-02/03/04` hasta decidir su borrado.
- No ejecutar `infra/baseline-renewal-demo/deploy-code.sh`: es del demo anterior y actualizaría el stack viejo.
- Destinos de llamadas salientes: solo teléfonos del equipo, en la lista permitida de la Lambda.
- Sin tarjetas ni datos reales. Los `.env` de los otros proyectos no se copian aquí.
- Lenguaje de las Lambdas nuevas: por definir (Python para el servicio simulado, o .NET para mantener el patrón anterior).

## Próximos pasos

1. Escribir las plantillas de los stacks `mei-` (rutas, backend, Lex, flujos).
2. Revisarlas contigo antes de desplegar nada.
3. Desplegar y ejecutar [TEST_PLAN.md](TEST_PLAN.md).
