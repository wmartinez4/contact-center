# Integración nativa Connect–ElevenLabs: pruebas reales frente a las investigaciones

Fecha: 2026-11-12. Compara lo que mostraron las llamadas de prueba en el sandbox con dos informes de investigación profunda: [ChatGPT](deep-research-report-ChatGPT.md) y [Gemini](deep-research-report-Gemini.md). Cuando un informe contradice una prueba, gana la prueba.

## Estado actual

- **Lado de AWS: funciona de punta a punta.** La llamada pasa por Connect, la sesión de Q in Connect, Lex y el agente de orquestación, y AWS intenta abrir el WebSocket hacia ElevenLabs. No hubo que pedirle nada a AWS.
- **Lado de ElevenLabs: bloqueado.** Al conectarnos al WebSocket del agente con las mismas cabeceras que envía Connect (`Authorization: Bearer`, `A2A-Extensions: https://docs.aws.amazon.com/connect/a2a/ext/v1`), ElevenLabs acepta la clave y cierra con el código **3000: "Amazon Connect transport is not enabled for this workspace."** No hay opción en el panel del workspace para activarlo; lo activa ElevenLabs.
- El workspace está en el plan **Starter**. **Respuesta de soporte de ElevenLabs (2026-11-12, por correo; redactada por su agente de IA):** el transporte se activa por workspace **solo como parte de un plan Enterprise**, también para una PoC; no hay prueba en Starter. Precio por minuto sobre Connect y concurrencia se definen en el acuerdo Enterprise, vía https://elevenlabs.io/enterprise. Consecuencia: la integración nativa es un costo de licencia a incluir en la propuesta, no algo que se pueda demostrar con la cuenta actual.

## Cadena de errores y cómo se resolvió (verificado)

| # | Error en el registro del flujo | Causa comprobada | Arreglo |
|---|---|---|---|
| 1 | `Amazon Lex needs active session for Q In Connect` (400) | El bloque "Connect assistant" del diseñador son **dos acciones**. El flujo creado por API solo tenía `CreateWisdomSession`. CloudTrail mostró que la sesión sí se creaba; nadie la pasaba a Lex | Agregar `UpdateContactData` con `WisdomSessionArn = $.Wisdom.SessionArn` después de `CreateWisdomSession` |
| 2 | `Passthrough init failed: agent=…:1 has no Connect instance; cannot resolve 3P` (502) | Solo aparece al pasar una sesión creada a mano con `CreateSession`, que no está ligada al contacto. Con la sesión que crea Connect no ocurre | No crear sesiones a mano |
| 3 | `A2A WebSocket upgrade to the Q In Connect Assistant failed (HTTP 403)` | CloudTrail: `wisdom:SendMessage` negado al rol de servicio de Lex (`AWSServiceRoleForLexV2Bots`). Lex nunca le agregó la política de Q in Connect que promete su documentación | Rol propio con los cuatro permisos de `wisdom`, confianza en `lexv2.amazonaws.com` y `lexv2.aws.internal`, y **una versión nueva del bot** (la versión anterior seguía usando el rol viejo) |
| 4 | `the hand-off to the target agent could not be completed` (424) | ElevenLabs rechaza la conexión: transporte no habilitado en el workspace | Pendiente: lo activa ElevenLabs |

CloudTrail también confirmó que Connect lee la clave de ElevenLabs en Secrets Manager sin error.

## Comparación de los informes

| Tema | ChatGPT | Gemini | Prueba real |
|---|---|---|---|
| Bloque "Connect assistant" = dos acciones | Causa n.º 1, alta | Causa n.º 3, alta | **Correcto.** Arreglado con `UpdateContactData` |
| Pasar `session-arn` explícito a Lex | No lo menciona | Lo propone, citando un repositorio de AWS | Alternativa válida al arreglo anterior (no probada) |
| AWS debe habilitar la cuenta | Probable si persiste el 502 | Causa n.º 1, alta | **Falso.** AWS no bloqueó nada |
| ID frente a ARN de la aplicación | Revisarlo | Causa n.º 2, alta | No era el problema: usamos el ID |
| `connectInstanceArn` ausente en la versión 1 | Media-alta | Posible | **Falso.** La versión 1 lo tiene |
| Rol de servicio de Lex sin permisos | Baja, "histórico" | Lo cita como verificado, no lo pone como causa | **Era un bloqueo real** (error 3) |
| `CreateWisdomSession` falla en silencio | Solo falta la segunda acción | Por KMS o bloqueo de cuenta | **No fallaba:** `CreateSession` exitoso en CloudTrail |
| Transporte de ElevenLabs por workspace | Último paso a revisar | Mezclado con el bloqueo de AWS | **Es el bloqueo actual** |
| Texto para soporte de AWS | Propone uno | Propone uno | No hace falta |

## Lo que vale la pena tomar de los informes

- **Permiso "Access Contact Control Panel" en el perfil de seguridad del agente de IA** (Gemini, citando la guía de AWS). Sin él, Connect no envía el contexto del contacto (número del cliente, número del sistema, canal) a ElevenLabs. No bloquea la conexión, pero el agente lo necesita para identificar al cliente por su número. **Por aplicar.**
- **El idioma del contacto debe coincidir con el del bot** (Gemini). Hoy ambos son en-US. Si se usa un bot es_US, hay que fijar el idioma en el flujo antes de Lex.
- **Ruta B** (transferir a un número de Twilio asignado a ElevenLabs) como plan alternativo, con una Lambda que guarde el ID del contacto por número de quien llama y el webhook de inicio de ElevenLabs para recuperarlo (los dos informes).

## Lo que no sirve de los informes

- **A2A en modo texto con voz de ElevenLabs** (Gemini, alternativa 2): la guía de ElevenLabs dice que su integración solo admite audio, no texto.
- **Los textos para soporte de AWS**: parten de una premisa que las pruebas descartaron.
- **Calidad de fuentes:** Gemini marca como verificadas fuentes secundarias (Eveonix, Dograh, Simple AI) y fecha un cambio de KMS del 2026-10-27 con un artículo de mayo de 2026. ChatGPT trae marcas de cita sin enlaces. El asistente no usa llave KMS propia, así que el punto de KMS no aplica.

## Lo que dice la guía de ElevenLabs (revisada otra vez el 2026-11-12, sin cambios)

- Su sección de problemas describe **nuestros errores 3 y 4**: el 403 se diagnostica buscando en CloudTrail `AccessDenied` sobre `wisdom:SendMessage` del rol de Lex, y "Confirm the Amazon Connect transport is enabled for your workspace" aparece entre las causas de una sesión que termina al conectar.
- **No cubre el error 1**, porque supone que el flujo se arma en el diseñador, donde el bloque "Connect assistant" ya incluye `UpdateContactData`. Quien arma el flujo por API tiene que agregarlo.
- Diseño recomendado para datos, que coincide con el plan: webhook de inicio de conversación (por `amazon_connect_contact_id`) para dar contexto al agente; herramienta webhook que llame a `UpdateContactAttributes` para datos de ruteo; webhook de fin de llamada para todo lo demás (transcripción, audio, análisis).
- Detalles útiles: Connect entrega al agente los dígitos que el cliente marca en el teclado (DTMF); el primer mensaje solo se puede cambiar desde el webhook de inicio, no desde el flujo; la integración puede generar cargos adicionales de AWS.

## Pendientes

1. Pedir a ElevenLabs que active el transporte de Amazon Connect en el workspace y confirmar si el plan Starter alcanza.
2. Agregar "Access Contact Control Panel" al perfil de seguridad `elevenlabs-a2a`.
3. Pasar los scripts de montaje (hoy en una carpeta temporal) a `poc/infra/` con nombres genéricos, para poder reconstruir la integración.
