# Diagnóstico de Causa Raíz y Arquitectura de Integración Agent-to-Agent (A2A) de Voz entre Amazon Connect y ElevenLabs

> Informe de investigación profunda generado con Gemini, copiado tal cual desde el enlace compartido el 2026-11-12.
> Es texto del modelo, no verificado. La comparación con las pruebas reales está en `comparacion-investigaciones-a2a.md`.
> Las tablas del original perdieron su formato al copiarse: cada celda quedó en su propia línea.

1. Resumen Ejecutivo: Causas Raíz Probables y Jerarquía de Evidencia

La investigación técnica sobre los cuatro síntomas observados en el entorno us-east-1 de Amazon Connect Customer —el fallo BadRequestException (HTTP 400 ValidationException) exigiendo x-amz-lex:q-in-connect:session-arn, el valor WisdomInfo = null en DescribeContact pese a que el bloque Connect assistant no toma la rama de error, el fallo BadGatewayException (HTTP 502 Passthrough init failed: agent=<ai-agent-id>:1 has no Connect instance; cannot resolve 3P) al inyectar una sesión manual, y la ausencia total de apertura de WebSocket hacia ElevenLabs— demuestra que la interrupción no reside en la telefonía básica ni en la latencia de red, sino en la intersección de un bloqueo de habilitación de plataforma (feature gate de disponibilidad limitada) y tres discrepancias críticas de vinculación entre el plano de control y el plano de ejecución de Amazon Connect, Amazon Q in Connect (wisdom/qconnect), AppIntegrations y Amazon Lex V2.

Rango	Causa Raíz Identificada	Nivel de Confianza	Síntomas Explicados	Clasificación de Evidencia
1	Falta de habilitación (Allowlist) de soporte para agentes de IA de terceros (3P A2A Audio Passthrough) en la cuenta de AWS (us-east-1) y/o en el Workspace de ElevenLabs.	Alta	Síntomas 1, 2, 3 y 4	

VERIFIED (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect y https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, nov. 2026)

2	Discrepancia entre APPLICATION_ID (UUID) y APPLICATION_ARN en agentTarget.applicationId, orden de publicación inmutable de la versión :1 del agente, o falta del permiso Access Contact Control Panel en el Security Profile.	Alta	Síntomas 3 y 4 (y fallo silencioso en 1 y 2)	

VERIFIED (Contradicción directa entre a2a-setup-external.html y ElevenLabs Docs, nov. 2026) / INFERENCE (Mecanismo interno del error 502)

3	Fallo silencioso de CreateWisdomSession en el bloque Connect assistant por política KMS (CMK) del asistente o falta de mapeo explícito de $.Wisdom.SessionArn hacia x-amz-lex:q-in-connect:session-arn.	Alta	Síntomas 1 y 2	

VERIFIED (https://aws.amazon.com/blogs/contact-center/automate-email-support-with-amazon-connect-customer-email-ai-agents/ 2026, https://github.com/aws-samples/sample-devops-agent-oncall-connect 2026, Classmethod 2026-05-11 [ANTERIOR A SEPTIEMBRE 2026])

4	Creación manual de sesión mediante qconnect:CreateSession sin vinculación de contexto de instancia/contacto (--contact-arn) fuera del ciclo de vida nativo de Amazon Connect.	Alta	Síntoma 3	

VERIFIED (https://docs.aws.amazon.com/cli/latest/reference/qconnect/create-session.html y https://docs.aws.amazon.com/lexv2/latest/dg/built-in-intent-qinconnect.html, nov. 2026) / INFERENCE

5	Configuración del rol IAM personalizado de Amazon Lex V2 (lexv2.aws.internal vs lexv2.amazonaws.com y condiciones de contexto de cifrado KMS kms:EncryptionContext:aws:wisdom:assistant:arn).	Media	Síntomas 1 y 2 (si el asistente Q usa CMK)	

VERIFIED (https://docs.aws.amazon.com/lexv2/latest/dg/built-in-intent-qinconnect.html nov. 2026 y Classmethod 2026-05-11 [ANTERIOR A SEPTIEMBRE 2026])

Análisis Detallado de las Cinco Causas Raíz Clasificadas

La primera causa raíz (Confianza: Alta) radica en el bloqueo por falta de habilitación a nivel de cuenta y región en AWS para agentes de terceros durante el período de disponibilidad limitada y pre-lanzamiento (Limited Availability / Prelaunch Period). La documentación oficial de ElevenLabs (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, vigente en noviembre de 2026) establece explícitamente: "The Amazon Connect integration is in limited availability. Amazon Connect's third-party AI agent support must be enabled for your AWS account, and the ElevenLabs transport is enabled per workspace. Contact your ElevenLabs representative before routing customer traffic" (VERIFIED). Adicionalmente, sobre el atributo de sesión x-amz-lex:qic-audio-passthrough, la misma fuente primaria documenta que "x-amz-lex:qic-audio-passthrough gates the third-party voice path during AWS's prelaunch period" (VERIFIED). Por su parte, la guía de administración de AWS (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, vigente en noviembre de 2026) exige validar previamente con el equipo de cuenta de AWS o Solutions Architect los requisitos de streaming de voz bidireccional antes del despliegue (VERIFIED). El mecanismo causal detrás de este comportamiento radica en que el plano de control de AWS (app-integrations:CreateApplication con A2A_SERVER y qconnect:CreateAIAgent con handoffAgentConfiguration) acepta las llamadas de configuración por API sin error, pero el plano de ejecución en tiempo real (tanto en CreateWisdomSession como en el puente de passthrough de audio entre Lex V2 y Q in Connect) evalúa una bandera de característica (feature flag) interna a nivel de cuenta e instancia. Al no estar activa dicha bandera en la cuenta, la inicialización de la sesión vinculada al agente 3P y la resolución del passthrough fallan sistemáticamente en tiempo de ejecución (INFERENCE basada en el comportamiento conjunto de los Síntomas 1, 2 y 3).

La segunda causa raíz (Confianza: Alta) corresponde a una discrepancia crítica en el formato del campo agentTarget.applicationId (UUID frente a ARN completo), la inmutabilidad de la versión :1 del agente de orquestación o la ausencia del permiso Access Contact Control Panel en el Security Profile. Al contrastar las fuentes primarias se observa una contradicción directa respecto a agentTarget.applicationId dentro de qconnect:CreateAIAgent: mientras la guía oficial de AWS (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, noviembre de 2026) especifica pasar el identificador corto de la aplicación ("applicationId": "YOUR_APPLICATION_ID") y no su ARN (VERIFIED), la guía de ElevenLabs (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, noviembre de 2026) indica pasar $APPLICATION_ARN en agentTarget.applicationId (VERIFIED). Asimismo, la guía de AWS (a2a-setup-external.html, Pasos 5 y 6) documenta que aws connect associate-security-profiles debe asociar el perfil de seguridad con entity-type AI_AGENT, que dicho perfil debe incluir el permiso Access Contact Control Panel para compartir el contexto del contacto (dirección del cliente, dirección del sistema y canal) con el colaborador externo, y que cualquier modificación en connectInstanceArn o en los colaboradores exige publicar una nueva versión con create-ai-agent-version debido a que las versiones de agentes en Q in Connect son inmutables (VERIFIED). Si la versión :1 del agente se publicó antes de que connectInstanceArn o la asociación del perfil de seguridad estuvieran propagados, o si el motor de resolución interno de Q in Connect intenta emparejar applicationId contra el registro de CreateIntegrationAssociation de la instancia de Connect y falla por la disparidad entre ARN e ID, el runtime arroja exactamente agent=<ai-agent-id>:1 has no Connect instance; cannot resolve 3P (INFERENCE).

La tercera causa raíz (Confianza: Alta) explica los Síntomas 1 y 2 a través del fallo silencioso de CreateWisdomSession en el bloque Connect assistant y la falta de propagación explícita de $.Wisdom.SessionArn. El blog técnico oficial de AWS Contact Center (https://aws.amazon.com/blogs/contact-center/automate-email-support-with-amazon-connect-customer-email-ai-agents/, publicado en 2026) documenta la arquitectura interna del bloque afirmando: "Important: The Connect assistant block is two flow actions, not one. CreateWisdomSession opens the session and UpdateContactData writes $.Wisdom.SessionArn onto the contact", y advierte expresamente que "Failures here are usually silent" (VERIFIED). De manera complementaria, el repositorio oficial de AWS en GitHub (https://github.com/aws-samples/sample-devops-agent-oncall-connect, 2026) instruye para los flujos con agentes de IA: "Connect AI agent flow: set the contact language to the bot locale (otherwise Lex returns 404), pass x-amz-lex:q-in-connect:session-arn explicitly" (VERIFIED). Cuando CreateWisdomSession falla internamente (ya sea porque el asistente de Q in Connect está cifrado con una clave KMS sin permisos para wisdom.us-east-1.amazonaws.com o porque el agente de orquestación asociado carece de autorización 3P), el bloque Connect assistant no desvía el contacto por la rama Error, sino que continúa por la rama normal dejando WisdomInfo = null y $.Wisdom.SessionArn vacío. Al llegar al bloque Get customer input entre 1.5 y 2 segundos después, Amazon Lex V2 rechaza la invocación con ValidationException (HTTP 400) porque no recibe un x-amz-lex:q-in-connect:session-arn válido (VERIFIED / INFERENCE).

La cuarta y quinta causas raíz (Confianza: Alta para el Síntoma 3 y Media para los Síntomas 1 y 2) explican los fallos derivados de la creación manual de sesiones y de los permisos del rol IAM personalizado de Lex V2. Por un lado, la referencia de AWS CLI v2 (https://docs.aws.amazon.com/cli/latest/reference/qconnect/create-session.html, v2.32.18, 2026) y la guía de Amazon Lex V2 (https://docs.aws.amazon.com/lexv2/latest/dg/built-in-intent-qinconnect.html, nov. 2026) establecen que en llamadas gestionadas por Amazon Connect la sesión debe ser creada por la instancia de Connect (la cual vincula internamente el contacto mediante --contact-arn y el contexto de la instancia) (VERIFIED). Crear la sesión manualmente con CreateSession fuera del motor de flujos produce una sesión desvinculada de la instancia de Connect, desencadenando el error HTTP 502 en la compuerta de passthrough (INFERENCE). Por otro lado, si el asistente de Q in Connect utiliza una clave KMS administrada por el cliente (CMK), a partir del 27 de octubre de 2026 AWS aplica una validación estricta de políticas KMS entre Amazon Lex V2 y los agentes de IA de Connect que exige una declaración QInConnectKmsCMKPolicy con contexto de cifrado específico (kms:EncryptionContext:aws:wisdom:assistant:arn) y una política de confianza (trust policy) que incluya lexv2.aws.internal (VERIFIED, built-in-intent-qinconnect.html nov. 2026 y Classmethod 2026-05-11 [ANTERIOR A SEPTIEMBRE 2026]).

2. Respuestas Detalladas a las Preguntas A–G
A. Creación de la Sesión de Q in Connect en Contactos de Voz y Condiciones Documentadas

En Amazon Connect Customer, un contacto de voz obtiene su sesión de Amazon Q in Connect (wisdom/qconnect) durante la ejecución del flujo de contacto en el instante en que atraviesa el bloque Connect assistant. De acuerdo con el análisis de arquitectura del AWS Contact Center Blog (https://aws.amazon.com/blogs/contact-center/automate-email-support-with-amazon-connect-customer-email-ai-agents/, 2026), el bloque Connect assistant no es una operación atómica simple, sino un bloque compuesto que ejecuta dos acciones internas de flujo de forma secuencial (VERIFIED). En primer lugar, la acción interna CreateWisdomSession invoca al servicio wisdom (qconnect) para abrir una sesión contextual bajo el dominio del asistente (assistantId) configurado en el bloque y vinculada al ARN del contacto activo. En segundo lugar, la acción interna UpdateContactData escribe el ARN resultante de la sesión en el atributo de sistema del contacto $.Wisdom.SessionArn y popula la estructura WisdomInfo (Contact.WisdomInfo.SessionArn), la cual queda expuesta al consultar la API DescribeContact (VERIFIED).

Una vez que $.Wisdom.SessionArn ha sido registrado en los datos del contacto por UpdateContactData, cuando el flujo avanza hacia el bloque Get customer input que invoca un bot de Amazon Lex V2 configurado con el intent integrado AMAZON.QInConnectIntent, la instancia de Amazon Connect transfiere el identificador de sesión hacia Lex poblando el atributo de sesión x-amz-lex:q-in-connect:session-arn (VERIFIED, https://docs.aws.amazon.com/lexv2/latest/dg/built-in-intent-qinconnect.html, nov. 2026). No obstante, en arquitecturas con agentes de IA personalizados, el repositorio oficial de AWS (https://github.com/aws-samples/sample-devops-agent-oncall-connect, 2026) y las guías de resolución de problemas en AWS re:Post (https://repost.aws/questions/QUYZ3taxJlRFuIN9uKDxChgQ/amazon-connect-native-ai-voice-agent-get-customer-input-throwing-bad-request-exception-without-flow-changes, 2026) documentan la práctica recomendada de declarar explícitamente el atributo de sesión x-amz-lex:q-in-connect:session-arn asignándole el valor dinámico del atributo de sistema $.Wisdom.SessionArn en la sección Session attributes del bloque Get customer input, además de asegurar que el bloque Connect assistant preceda estrictamente a Get customer input (VERIFIED, GeekFeed https://www.geekfeed.co.jp/geekblog/amazon-q-in-connect-chatbot/, 2025-12-14 [ANTERIOR A SEPTIEMBRE 2026]).

La tabla siguiente consolida todas las condiciones documentadas en las fuentes primarias para la creación de la sesión de Q in Connect y la ejecución del handoff A2A en llamadas de voz:

Condición / Componente	Requisito Técnico Documentado	Fuente Primaria, Fecha y Estado de Verificación
Nivel de Instancia (Instance Tier)	La instancia debe operar en el nivel Connect Customer. Las funcionalidades de agentes de IA y la colaboración Agent-to-Agent (A2A) no están disponibles en el nivel Customer Basic.	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-collaboration.html, nov. 2026)

Contact Lens Real-Time Analytics	Para utilizar agentes de IA en llamadas de voz, la documentación del bloque Connect assistant exige añadir un bloque Set recording and analytics behavior configurado con conversational analytics real-time habilitado (su posición relativa respecto al bloque Connect assistant no altera la asistencia en tiempo real, pero Connect assistant debe ejecutarse antes de Get customer input). En el canal de chat no se requiere Contact Lens.	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/connect-assistant-block.html, nov. 2026; GeekFeed 2025-12-14 [ANTERIOR A SEPTIEMBRE 2026])

Idioma y Locale del Bot / Flujo	Para transmisión de audio A2A (audioStreamingEnabled: true), el locale del bot de Amazon Lex V2 debe utilizar Amazon Nova Sonic speech-to-speech y contener únicamente un solo intent (AMAZON.QInConnectIntent). Asimismo, el idioma del contacto en el flujo (fijado mediante el bloque Set voice con Set language attribute) debe coincidir con el locale del bot (en_US) para evitar errores HTTP 400/404 en Lex. Las voces de lanzamiento soportadas por Nova Sonic son Matthew (en-US), Amy (en-GB), Olivia (en-AU) y Lupe (es-US).	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, nov. 2026; aws-samples/sample-devops-agent-oncall-connect, 2026; Eveonix 2026-11-10)

Atributos de Instancia e Integraciones	La instancia debe contar con: (1) el asistente asociado mediante CreateIntegrationAssociation con IntegrationType: WISDOM_ASSISTANT; (2) la aplicación A2A_SERVER asociada con IntegrationType: APPLICATION; y (3) las opciones Connect assistant y gestión de bots Lex habilitadas a nivel de instancia.	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html y connect-assistant-ui-builder.html, nov. 2026)

Security Profile del Agente de IA	El perfil de seguridad debe: (1) incluir los permisos QConnectAIAgents.View y Wisdom.View; (2) registrar la aplicación en AllowedAIAgents con "Type": "THIRD_PARTY"; (3) otorgar el permiso Access Contact Control Panel para compartir el contexto del contacto (dirección del llamante, dirección del sistema y canal) con el agente externo; y (4) asociarse mediante AssociateSecurityProfiles (entity-type AI_AGENT) tanto al ARN sin versión como al ARN versionado (:1) del agente de orquestación.	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html y a2a-collaboration.html, nov. 2026; ElevenLabs Docs nov. 2026)

Campo opcional de Agente IA en el bloque Connect assistant	El bloque Connect assistant define el ARN del dominio del asistente y opcionalmente el agente de IA de orquestación para Agent Assistance. En flujos de autoservicio con handoff A2A, el agente de orquestación se invoca pasando su ARN versionado en el atributo de sesión de Lex x-amz-lex:q-in-connect:ai-agent-arn dentro del bloque Get customer input, o mediante una función Lambda que invoque UpdateSession.	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/connect-assistant-block.html, nov. 2026; ElevenLabs Docs nov. 2026; GeekFeed 2025-12-14 [ANTERIOR A SEPTIEMBRE 2026])

Restricciones del Agente de Orquestación para Audio Streaming	Cuando audioStreamingEnabled es true: (1) immediateHandoff debe ser true; (2) el colaborador externo debe ser el único colaborador configurado en el agente; (3) el agente de orquestación no debe tener prompt de orquestación (orchestrationAIPromptId) ni guardrail; y (4) debe incluir la herramienta reservada Complete (RETURN_TO_CONTROL), opcionalmente la herramienta reservada Escalate, y ninguna otra herramienta adicional.	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html y a2a-collaboration.html, nov. 2026)

Regiones y Cuenta	Todos los recursos (instancia Connect, asistente Q in Connect, secreto en Secrets Manager, clave KMS, aplicación AppIntegrations y bot Lex V2) deben residir en la misma cuenta de AWS y misma Región (us-east-1), donde Connect Customer, qconnect y Amazon Nova Sonic estén soportados.	

VERIFIED (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect y a2a-setup-external.html, nov. 2026)

B. Por Qué el Bloque Connect assistant se Ejecuta sin Error pero Deja WisdomInfo Vacío (null)

El síntoma en el que el bloque Connect assistant se ejecuta en el flujo de contacto sin tomar la rama Error, pero aws connect describe-contact devuelve WisdomInfo = null (provocando que 1.5 a 2 segundos más tarde el bloque Get customer input falle con Amazon Lex needs active session for Q In Connect), responde al diseño de tolerancia a fallos del motor de flujos de Amazon Connect documentado por AWS. En el artículo técnico oficial del AWS Contact Center Blog (https://aws.amazon.com/blogs/contact-center/automate-email-support-with-amazon-connect-customer-email-ai-agents/, 2026), los autores explican que dentro de la secuencia compuesta del bloque Connect assistant (CreateWisdomSession seguida de UpdateContactData): "Failures here are usually silent, so these two sources are where to look: Connect assistant event logs. Enable delivery with EVENT_LOGS as the log type... Session traces. ListSpans returns the per-agent trace for a session, keyed on the session ID in the contact's WisdomInfo" (VERIFIED). Debido a que originalmente el bloque Connect assistant fue concebido para habilitar recomendaciones de asistencia al agente en segundo plano sin interrumpir el enrutamiento de llamadas críticas si el subsistema de IA experimenta un error de configuración, un rechazo en CreateWisdomSession no fuerza el contacto hacia la rama Error del bloque; en su lugar, la acción CreateWisdomSession aborta silenciosamente, UpdateContactData no tiene ningún $.Wisdom.SessionArn que escribir en el contacto, WisdomInfo permanece en null, y la llamada avanza normalmente hasta estrellarse en el bloque Get customer input (VERIFIED / INFERENCE).

Existen tres desencadenantes técnicos específicos que provocan que CreateWisdomSession falle silenciosamente en esta arquitectura. El primero ocurre cuando CreateWisdomSession intenta inicializar la sesión validando la configuración de agentes del asistente (assistant.aiAgentConfiguration, consultable con aws qconnect get-assistant --assistant-id <id> --query "assistant.aiAgentConfiguration") o el agente de orquestación seleccionado en la pestaña Config del bloque Connect assistant. Si el asistente o el bloque hacen referencia a un agente de orquestación que contiene un handoffAgentConfiguration hacia un A2A_SERVER de terceros mientras la cuenta de AWS aún no tiene activado el allowlist de Third-Party AI Agent support (o mientras el agente presenta un conflicto de validación como tener un prompt o un applicationId irresoluble), el servicio qconnect rechaza la apertura de la sesión de forma silenciosa (INFERENCE fundamentada en a2a-setup-external.html y el AWS Contact Center Blog 2026).

El segundo desencadenante es una denegación de permisos KMS si el propio asistente de Q in Connect (o su dominio) fue configurado con una clave KMS administrada por el cliente (CMK). Según la guía de Amazon Lex V2 (https://docs.aws.amazon.com/lexv2/latest/dg/built-in-intent-qinconnect.html, nov. 2026) y el análisis técnico de Classmethod (https://dev.classmethod.jp/articles/amazon-connect-ai-agent-lex-kms-policy-update/, 2026-05-11 [ANTERIOR A SEPTIEMBRE 2026]), la creación y operación de sesiones sobre un asistente cifrado con CMK exige permisos kms:Decrypt y kms:GenerateDataKey condicionados por kms:ViaService: "wisdom.<region>.amazonaws.com" y kms:EncryptionContext:aws:wisdom:assistant:arn (VERIFIED). Si la clave KMS fue configurada únicamente con la condición kms:ViaService: "secretsmanager.us-east-1.amazonaws.com" (la cual sirve para el secreto de la API key de ElevenLabs, pero no para el asistente de Q in Connect), CreateWisdomSession falla por AccessDeniedException en los EVENT_LOGS internos sin activar la rama de error del flujo (INFERENCE). Finalmente, el tercer desencadenante documentado en repositorios de validación de AWS (https://github.com/aws-samples/sample-aicc-builder-for-amazon-connect-ai-agent/blob/main/docs/acxd-live-validation.md, 2026) y en AWS re:Post (https://repost.aws/questions/QUYZ3taxJlRFuIN9uKDxChgQ/amazon-connect-native-ai-voice-agent-get-customer-input-throwing-bad-request-exception-without-flow-changes, 2026) es un enlace obsoleto (stale binding) en el bloque Connect assistant o Get customer input tras recrear recursos por CLI sin volver a seleccionar y publicar el enlace en el diseñador de flujos (VERIFIED).

C. Habilitación de Cuenta/Región para A2A Audio Passthrough (x-amz-lex:qic-audio-passthrough), Estado Actual y Regiones

La ruta de transmisión de audio hacia agentes externos de terceros controlada por el atributo x-amz-lex:qic-audio-passthrough requiere habilitación explícita tanto a nivel de cuenta y región en AWS como a nivel de espacio de trabajo (workspace) en ElevenLabs (VERIFIED). En la documentación oficial de ElevenLabs (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, noviembre de 2026), bajo las secciones Prerequisites & Requirements y Limited Availability Requirements, se estipula de forma inequívoca: "The Amazon Connect integration is in limited availability. Amazon Connect's third-party AI agent support must be enabled for your AWS account, and the ElevenLabs transport is enabled per workspace. Contact your ElevenLabs representative before routing customer traffic", precisando además que la instancia de Amazon Connect "Must be on the Connect Customer tier with third-party AI agent support enabled for the account and Region" (VERIFIED). Con respecto a la función específica del atributo de sesión x-amz-lex:qic-audio-passthrough, la misma fuente primaria detalla que "x-amz-lex:qic-audio-passthrough acts as a gate for the third-party voice path during AWS’s prelaunch period", añadiendo que AWS prevé retirar la obligatoriedad de este atributo cuando la función pase a disponibilidad pública general, momento en el cual conservar el atributo configurado en true resultará inocuo (VERIFIED).

En cuanto al procedimiento para solicitar dicha habilitación, no existe ningún formulario web público de autoservicio en la documentación de AWS ("not found"). En su lugar, la guía oficial del administrador de Amazon Connect (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, noviembre de 2026) instruye en su lista de prerrequisitos: "If using audio streaming (bidirectional audio), work with your AWS account team or Solutions Architect to validate that the agent meets latency and audio quality requirements prior to production deployment" (VERIFIED). Por consiguiente, la activación en AWS debe solicitarse directamente a través del AWS Account Team (Account Manager / Solutions Architect de Amazon Connect) o mediante la apertura de un caso de AWS Support dirigido al equipo de ingeniería de servicio de Amazon Connect / Q in Connect proporcionando el Account ID, la región (us-east-1) y el Instance ARN, mientras que la habilitación del transporte wss://api.elevenlabs.io/v1/convai/conversation/amazon-connect/<AGENT_ID> debe solicitarse al representante de cuenta de ElevenLabs indicando el Workspace ID (VERIFIED / INFERENCE).

Respecto a su estado actual y regiones soportadas a noviembre de 2026, tras el anuncio de la funcionalidad alrededor del 2026-09-23, el marco general de colaboración A2A forma parte de la guía oficial del administrador de Amazon Connect Customer (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-collaboration.html, nov. 2026) como una capacidad configurable exclusivamente por API (VERIFIED). Sin embargo, el sub-camino de transmisión de audio bidireccional hacia plataformas de terceros permanece en estado de Limited Availability / Prelaunch Period a noviembre de 2026 (VERIFIED, https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect y https://eveonix.com/resources/ai-voice-agent-amazon-connect-build-guide, actualizado el 2026-11-10). En lo relativo a disponibilidad regional, todos los recursos de AWS deben coexistir en la misma región donde el nivel Connect Customer, los agentes de IA de Connect (qconnect) y el modelo Amazon Nova Sonic speech-to-speech en Amazon Lex V2 estén activos (VERIFIED). La región us-east-1 es la región principal soportada, con voces de lanzamiento de Nova Sonic disponibles para los locales en-US (Matthew), en-GB (Amy), en-AU (Olivia) y es-US (Lupe) (VERIFIED, https://eveonix.com/resources/amazon-connect-custom-voice-options, 2026-11-10 y AWS re:Post 2026). En el extremo de ElevenLabs, se soportan el endpoint estándar global (wss://api.elevenlabs.io/...) y los endpoints regionales de residencia de datos (wss://api.<region>.residency.elevenlabs.io/... para EE. UU., Unión Europea e India) (VERIFIED).

D. Rol IAM Personalizado vs. Rol Vinculado a Servicios (AWSServiceRoleForLexV2Bots) en Amazon Lex V2

Un bot de Amazon Lex V2 que emplea un rol IAM personalizado se comporta de manera sustancialmente distinta a uno que utiliza el rol vinculado a servicios (AWSServiceRoleForLexV2Bots_AmazonConnect_<accountId>) cuando ejecuta el intent integrado AMAZON.QInConnectIntent. De acuerdo con la guía para desarrolladores de Amazon Lex V2 (https://docs.aws.amazon.com/lexv2/latest/dg/built-in-intent-qinconnect.html, vigente en noviembre de 2026), cuando un bot se configura con un Service-Linked Role (SLR), el servicio Amazon Lex V2 posee privilegios administrativos internos para inyectar y actualizar automáticamente las políticas de permisos en el rol cada vez que se añade o modifica el intent AMAZON.QInConnectIntent y se vincula un asistente de Q in Connect (VERIFIED). Por el contrario, cuando el administrador selecciona un rol IAM personalizado, Amazon Lex V2 no realiza ninguna modificación automática sobre el rol, recayendo en el usuario la responsabilidad de definir con exactitud los comodines de recursos de wisdom, los permisos de descifrado KMS con contexto de cifrado y la política de confianza interna (VERIFIED).

La afirmación publicada en el blog técnico japonés de Classmethod por Yuji Hirai (https://dev.classmethod.jp/articles/amazon-q-in-connect-lex-service-link-role-update/, fechada el 2025-03-12 [ANTERIOR A SEPTIEMBRE 2026]) es totalmente VERIFIED. Dicho artículo documenta que al invocar un bot con AMAZON.QInConnectIntent desde el bloque Get customer input, la llamada puede desviarse inmediatamente hacia la rama de error con BadRequestException ("The service cannot process the request") cuando el rol vinculado a servicios AWSServiceRoleForLexV2Bots_AmazonConnect_<accountId> no recibió la actualización automática de la política IAM con el assistantId correspondiente. La solución verificada en ese estudio consiste en eliminar el bot de Lex, desmarcar la casilla "Enable Lex bot management in Amazon Connect management website" en la consola de AWS, guardar los cambios, volver a marcar la casilla, esperar aproximadamente un minuto hasta verificar en IAM que el SLR contiene la política con el assistantId, y finalmente recrear el bot (VERIFIED). Además, un análisis de experto en AWS re:Post (https://repost.aws/questions/QU-2fZ6CL4T8q5Utsc-LwiwQ/lex-v2-bot-with-amazon-qinconnectintent-fails-with-too-many-queries-per-second-to-your-q-in-connect-assistant-on-connect-voice-calls, [ANTERIOR A SEPTIEMBRE 2026]) advierte que en integraciones de Connect se debe inspeccionar CloudTrail buscando llamadas originadas tanto desde el rol personalizado como desde el SLR de Lex (REPORTED BY A SINGLE SOURCE).

Aún más relevante para una implementación en noviembre de 2026 es una segunda publicación de Classmethod (https://dev.classmethod.jp/articles/amazon-connect-ai-agent-lex-kms-policy-update/, actualizada el 2026-05-11 [ANTERIOR A SEPTIEMBRE 2026]), la cual documenta un cambio de seguridad obligatorio de AWS que entró en vigor el 27 de octubre de 2026 (VERIFIED). A partir del 2026-10-27, AWS refuerza el cifrado de las comunicaciones entre Amazon Lex V2 y los agentes de IA de Amazon Connect cuando se emplea una clave KMS administrada por el cliente (CMK), exigiendo que el rol de ejecución de Lex posea permisos explícitos kms:Decrypt y kms:GenerateDataKey restringidos al servicio wisdom.<region>.amazonaws.com y al contexto de cifrado del ARN del asistente; de lo contrario, se producen errores de tiempo de ejecución en los flujos de autoservicio (VERIFIED). Mientras que para los bots con SLR la consola de Amazon Connect ofrece el botón [Update KMS Policy] en la sección [AI agents] (que añade automáticamente la política AmazonLexV2QinConnectKmsCMKPolicy<random> al rol AWSServiceRoleForLexV2Bots_AmazonConnect_<accountId>), en la ruta de rol IAM personalizado el administrador debe incorporar manualmente las declaraciones exactas que se detallan en la tabla siguiente (VERIFIED, https://docs.aws.amazon.com/lexv2/latest/dg/built-in-intent-qinconnect.html, nov. 2026):

Elemento del Rol IAM Personalizado de Lex V2	Especificación Técnica Requerida por AMAZON.QInConnectIntent	Diferencia Crítica frente a la Configuración del Solicitante
QInConnectAssistantPolicy (Permisos de Asistente)	

Acciones: wisdom:CreateSession, wisdom:GetAssistant.

Recursos obligatorios (ambos patrones):

arn:aws:wisdom:*:<accountId>:assistant/<assistantId> y

arn:aws:wisdom:*:<accountId>:assistant/<assistantId>/*

	

VERIFIED (built-in-intent-qinconnect.html, nov. 2026). Si el rol personalizado solo incluye el ARN base del asistente sin el comodín /* de sub-recursos (donde residen los agentes de IA y versiones), la invocación al agente de IA falla.

QInConnectSessionsPolicy (Permisos de Sesión)	

Acciones: wisdom:SendMessage, wisdom:GetNextMessage.

Recurso obligatorio:

arn:aws:wisdom:*:<accountId>:session/<assistantId>/*

	

VERIFIED (built-in-intent-qinconnect.html, nov. 2026). El ARN de sesión en wisdom lleva el assistantId como prefijo de ruta (session/<assistantId>/<sessionId>).

QInConnectKmsCMKPolicy (Obligatorio desde 2026-10-27 si el Asistente usa CMK)	

Acciones: kms:Decrypt, kms:GenerateDataKey sobre la CMK.

Condiciones StringEquals:

aws:ResourceAccount: <accountId>

kms:ViaService: wisdom.<region>.amazonaws.com

kms:EncryptionContext:aws:wisdom:assistant:arn: ["arn:aws:wisdom:<region>:<accountId>:assistant/<assistantId>"]

	

VERIFIED (built-in-intent-qinconnect.html, nov. 2026; Classmethod 2026-05-11 [ANTERIOR A SEPTIEMBRE 2026]). El solicitante no incluyó permisos KMS en el rol del bot de Lex; si el asistente usa CMK, la comunicación entre Lex y Q in Connect es bloqueada desde el 2026-10-27.

LexV2InternalTrustPolicy (Política de Confianza del Rol)	sts:AssumeRole permitido al principal "Service": "lexv2.aws.internal" (y "lexv2.amazonaws.com"), con condiciones StringEquals (aws:SourceAccount: <accountId>) y ArnLike (aws:SourceArn: arn:aws:lex:*:<accountId>:bot-alias/<botId>/*).	

VERIFIED (built-in-intent-qinconnect.html, nov. 2026 y Classmethod 2026-05-11). Muchos roles personalizados solo autorizan lexv2.amazonaws.com y omiten el principal interno lexv2.aws.internal requerido por el motor de QInConnectIntent.

E. Ejemplos Públicos Funcionales de Amazon Connect + ElevenLabs (o Agentes Externos A2A) con Streaming de Audio

Se han verificado cuatro fuentes públicas primarias que documentan la arquitectura funcional completa de extremo a extremo: la guía oficial de integración de ElevenLabs con Amazon Connect (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, noviembre de 2026) (VERIFIED), la guía oficial de configuración de colaboradores externos de AWS (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, noviembre de 2026) (VERIFIED), el repositorio de código de ejemplo de AWS para sub-agentes A2A en contenedores Python (https://github.com/aws-samples/sample-voice-agent-on-aws, 2026) (VERIFIED), y el repositorio de AWS para flujos de contacto con agentes de IA de Connect (https://github.com/aws-samples/sample-devops-agent-oncall-connect, 2026) (VERIFIED).

En la implementación pública funcional documentada por ElevenLabs y AWS, el flujo de llamadas y la configuración de sesión operan bajo una secuencia precisa. En primer lugar, en ElevenLabs se configura un agente en ElevenAgents con un first message (ya que Amazon Connect no reproduce ningún audio propio durante la sesión A2A), se habilita la herramienta de sistema end_call (que devuelve el resultado Complete a Connect) y opcionalmente se configura por API (PATCH https://api.elevenlabs.io/v1/convai/agents/<AGENT_ID>) la herramienta de sistema transfer_to_number con provider_configs de tipo amazon_connect y "type": "amazon_connect_escalate" (que devuelve el resultado Escalate a Connect) (VERIFIED). En segundo lugar, dentro del flujo de contacto de Amazon Connect, tras habilitar los registros (Set logging behavior), la analítica conversacional en tiempo real (Set recording and analytics behavior) y fijar el idioma del contacto para que coincida con el locale en_US del bot (Set voice / Set contact attributes), se ejecuta el bloque Connect assistant apuntando al asistente WISDOM_ASSISTANT e inmediatamente después se invoca el bloque Get customer input con el ARN del alias del bot de Lex V2 (Nova Sonic speech-to-speech) (VERIFIED). Dentro del bloque Get customer input, el prompt de Text-to-Speech se deja configurado como un único carácter de espacio (" ") para evitar que Connect sintetice audio previo al handoff, y se definen los atributos de sesión x-amz-lex:q-in-connect:ai-agent-arn (con el ARN versionado :1 del agente de orquestación), x-amz-lex:qic-audio-passthrough (con valor true) y, siguiendo la directriz de aws-samples/sample-devops-agent-oncall-connect, x-amz-lex:q-in-connect:session-arn apuntando dinámicamente a $.Wisdom.SessionArn (VERIFIED). A la salida de Get customer input, un bloque Check contact attributes evalúa el atributo de sesión de Lex Tool ($.Lex.SessionAttributes.Tool): si es Complete desconecta la llamada, y si es Escalate invoca opcionalmente un bloque Set whisper flow (que lee $.Attributes.handoff_summary escrito por un webhook de ElevenLabs vía connect:UpdateContactAttributes) y transfiere a la cola humana (VERIFIED).

La auditoría comparativa entre la arquitectura construida por el solicitante y las especificaciones exactas de las fuentes primarias revela seis diferencias críticas que explican el fallo en tiempo de ejecución:

Paso / Componente	Configuración Construida por el Solicitante	Especificación Exacta en los Ejemplos Públicos (Diferencia Detectada)	Fuente Primaria y Estado
1. Formato de agentTarget.applicationId en CreateAIAgent	Se configuró el agente ORCHESTRATION apuntando a la aplicación, sin distinguir entre el Id (UUID) y el Arn.	La guía oficial de AWS (a2a-setup-external.html, Modo C) exige pasar el Application ID ("applicationId": "YOUR_APPLICATION_ID"), mientras que ElevenLabs muestra $APPLICATION_ARN. Pasar el formato incorrecto impide que Q in Connect resuelva la asociación 3P en la instancia.	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html vs ElevenLabs Docs, nov. 2026)

2. Permiso Access Contact Control Panel en el Security Profile	Se asignaron únicamente QConnectAIAgents.View, Wisdom.View y AllowedAIAgents = THIRD_PARTY.	La documentación de AWS exige añadir el permiso Access Contact Control Panel al Security Profile asociado al agente de IA para que Connect pueda transmitir el contexto del contacto (customer address, system address, channel) al colaborador externo.	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html y a2a-collaboration.html, nov. 2026)

3. Prohibición de Prompt y Guardrail en el Agente de Orquestación	Agente ORCHESTRATION con audioStreamingEnabled=true, immediateHandoff=true y herramienta Complete.	Para audioStreamingEnabled: true, la guía de AWS establece que el agente de orquestación NO debe tener orchestrationAIPromptId ni guardrail, y el colaborador de audio debe ser el único colaborador configurado en multiAgentConfigurations.	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, Modo C, nov. 2026)

4. Condición kms:ViaService en la CMK y Resource Policy del Secreto	Secreto cifrado con una clave KMS administrada por el cliente (CMK).	La política de la clave KMS debe autorizar kms:Decrypt al principal connect.amazonaws.com con la condición kms:ViaService: "secretsmanager.us-east-1.amazonaws.com", y la política de recursos del secreto debe autorizar secretsmanager:GetSecretValue restringido por aws:SourceAccount y aws:SourceArn (ARN de la instancia de Connect).	

VERIFIED (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html#a2a-setup-external-step1, nov. 2026)

5. Configuración del Bloque Get customer input e Idioma del Flujo	Prompt silencioso opcional de 3 segundos previo al bloque; solo 2 atributos de sesión pasados a Lex.	ElevenLabs exige poner un único espacio (" ") en el prompt TTS de Get customer input; aws-samples exige fijar explícitamente el idioma del contacto al locale del bot (en_US) y pasar explícitamente x-amz-lex:q-in-connect:session-arn = $.Wisdom.SessionArn.	

VERIFIED (ElevenLabs Docs nov. 2026; https://github.com/aws-samples/sample-devops-agent-oncall-connect, 2026)

6. Allowlist Previo en AWS y en el Workspace de ElevenLabs	Ejecución directa de llamadas de prueba tras aprovisionar por CLI/API.	Requiere que AWS habilite previamente el soporte de agentes de IA de terceros para la cuenta y región, y que ElevenLabs habilite el transporte de Amazon Connect en el workspace.	

VERIFIED (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, nov. 2026)

F. Significado del Segundo Error ("Passthrough init failed: agent=<ai-agent-id>:1 has no Connect instance; cannot resolve 3P") y Vinculación en Tiempo de Ejecución

El mensaje de error literal "Passthrough init failed: agent=<ai-agent-id>:1 has no Connect instance; cannot resolve 3P (Status Code: 502)" no se encuentra documentado ("not found") en ninguna página pública de docs.aws.amazon.com, AWS re:Post, blogs oficiales ni repositorios de GitHub hasta noviembre de 2026. No obstante, su semántica técnica puede reconstruirse con exactitud mediante INFERENCE directa a partir de los contratos de API verificados de qconnect, connect y app-integrations. Cuando el bloque Get customer input invoca a Amazon Lex V2 con x-amz-lex:qic-audio-passthrough = true, un x-amz-lex:q-in-connect:session-arn activo y x-amz-lex:q-in-connect:ai-agent-arn = .../<ai-agent-id>:1, el subsistema de passthrough de voz intenta construir el puente WebSocket resolviendo de forma encadenada la sesión de Q in Connect y la versión :1 del agente hacia la instancia de Amazon Connect, y desde dicha instancia hacia la asociación de integración APPLICATION (A2A_SERVER) y el perfil de seguridad que autoriza el destino THIRD_PARTY (3P).

En tiempo de ejecución, existen cinco mecanismos precisos que vinculan una versión de agente de IA con la instancia de Amazon Connect y permiten resolver la aplicación 3P, cuya ausencia o ruptura explica ambas mitades del mensaje de error ("has no Connect instance" y "cannot resolve 3P"):

En primer lugar, a nivel de la definición del recurso en qconnect, el vínculo se establece mediante la propiedad "connectInstanceArn": "arn:aws:connect:us-east-1:<ACCOUNT_ID>:instance/<INSTANCE_ID>" dentro de configuration.orchestrationAIAgentConfiguration al invocar CreateAIAgent o UpdateAIAgent (VERIFIED, https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, nov. 2026). Dado que las versiones publicadas con CreateAIAgentVersion son instantáneas inmutables (VERIFIED, AWS Contact Center Blog 2026), si connectInstanceArn se añadió o corrigió en el borrador del agente ($LATEST) después de haber publicado la versión :1, la instantánea :1 carece literalmente de connectInstanceArn en tiempo de ejecución (INFERENCE). En segundo lugar, a nivel de la sesión de Q in Connect, la API qconnect:CreateSession (https://docs.aws.amazon.com/cli/latest/reference/qconnect/create-session.html, CLI v2.32.18, 2026) incluye el parámetro --contact-arn y documenta que "Connect Customer creates a new Amazon Q in Connect session for each contact on which Amazon Q in Connect is enabled" (VERIFIED). Cuando en el Síntoma 3 el solicitante creó una sesión manualmente con CreateSession fuera del flujo de Amazon Connect, dicha sesión nació huérfana (sin vínculo interno con un contacto activo ni con la instancia de Connect donde WisdomInfo seguía siendo null), provocando que al evaluar la sesión junto con el agente :1 el motor de passthrough dictaminara que la ejecución no posee contexto de instancia de Connect (INFERENCE).

En tercer lugar, a nivel de autorización de instancia, el vínculo en tiempo de ejecución se materializa ejecutando aws connect associate-security-profiles --instance-id <INSTANCE_ID> --entity-arn <VERSIONED_AGENT_ARN> --entity-type AI_AGENT --security-profiles Id=<SECURITY_PROFILE_ID> (VERIFIED, a2a-setup-external.html, Paso 5). Es esta asociación sobre el ARN versionado (:1) la que permite al runtime de Q in Connect consultar en la instancia de Connect la lista AllowedAIAgents ([{"Arn": "<APPLICATION_ARN>", "Type": "THIRD_PARTY"}]) del perfil de seguridad. En cuarto lugar, para resolver el colaborador 3P, el runtime cruza el valor de handoffAgentConfiguration.agentTarget.applicationId con las integraciones asociadas a la instancia mediante aws connect create-integration-association --instance-id <INSTANCE_ID> --integration-type APPLICATION --integration-arn <APPLICATION_ARN> (VERIFIED). Si agentTarget.applicationId contiene el ARN cuando el resolver interno espera el UUID Id (o viceversa, según la contradicción documentada entre AWS y ElevenLabs), la búsqueda en la tabla de integraciones de la instancia falla con "cannot resolve 3P" (INFERENCE). Finalmente, en quinto lugar, si la cuenta de AWS no tiene habilitado el feature flag de soporte para agentes de IA de terceros (3P) en us-east-1, el resolver de passthrough de voz ignora o bloquea las asociaciones APPLICATION de tipo A2A_SERVER y devuelve este mismo error 502 (INFERENCE fundamentada en ElevenLabs Docs, nov. 2026).

G. Alternativas Viables Hoy si la Ruta Nativa A2A Audio Streaming No Está Disponible

En caso de que la habilitación en lista blanca de x-amz-lex:qic-audio-passthrough por parte de AWS y ElevenLabs tome tiempo, existen cuatro rutas arquitectónicas alternativas evaluadas en las fuentes primarias y guías de construcción de noviembre de 2026, tres de las cuales son plenamente operativas hoy en disponibilidad general (GA) mientras que la cuarta (puente con Kinesis Video Streams) resulta inviable para voz conversacional bidireccional.

Alternativa 1: Agente de IA Nativo de Amazon Connect (Agentic Voice / Nova Sonic) con ElevenLabs como Proveedor TTS de Terceros en Connect

Cuando el objetivo principal de integrar ElevenLabs es utilizar sus voces hiperrealistas o voces de marca clonadas manteniendo toda la orquestación dentro de AWS, Amazon Connect soporta nativamente a ElevenLabs como proveedor de síntesis de voz de terceros (Third-Party TTS) dentro del flujo de contacto (VERIFIED, https://docs.aws.amazon.com/connect/latest/adminguide/configure-third-party-tts.html, nov. 2026; Eveonix https://eveonix.com/resources/amazon-connect-custom-voice-options, 2026-11-10; Cartesia https://www.cartesia.ai/vs/elevenlabs-vs-amazon-polly, 2026). En esta arquitectura se utiliza un Agente de IA nativo de Amazon Connect (configurado con herramientas MCP o funciones Lambda) y en el bloque Set voice del flujo se selecciona a ElevenLabs como proveedor de voz, especificando el ID del modelo, el ID de la voz, el idioma y el ARN del secreto en AWS Secrets Manager cifrado con una CMK (incluyendo opcionalmente el campo apiTokenRegion configurado en us, eu o in dentro del JSON del secreto para minimizar la latencia regional) (VERIFIED). Para el reconocimiento de voz (STT), se emplea el reconocedor avanzado en streaming de Agentic Voice de Connect o un proveedor STT de terceros como Deepgram configurado en el locale del bot (VERIFIED). Bajo este esquema, el llamante experimenta una conversación fluida con soporte nativo de interrupción (barge-in activado por defecto y tiempo de espera de silencio ajustable desde 640 ms) escuchando la voz de ElevenLabs. Toda la llamada queda registrada en Amazon Connect como un único contacto continuo (1 CTR), Contact Lens funciona en su totalidad (tanto en tiempo real como en post-llamada) y las trazas del agente se publican automáticamente sin riesgo de bloqueo por TRACING_SPAN. El ContactId nunca abandona AWS y está disponible de forma nativa en event.Details.ContactData.ContactId para cualquier función Lambda. Los límites conocidos de esta ruta son el tiempo máximo de ejecución de 30 segundos por llamada a herramienta MCP en el agente nativo de Connect y la cuota predeterminada de 10 llamadas concurrentes de agentes de IA por instancia (ajustable bajo petición) (VERIFIED, Dilr 2026, Eveonix 2026-11-10 y Dograh 2026).

Alternativa 2: Colaboración A2A en Modo Texto (audioStreamingEnabled: false) Combinada con ElevenLabs como Proveedor TTS de Terceros

Si es indispensable que un motor de agente externo tome las decisiones conversacionales pero la compuerta de passthrough de audio (x-amz-lex:qic-audio-passthrough) aún no está habilitada para la cuenta, la guía oficial de AWS (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, Modo B, nov. 2026) permite configurar handoffAgentConfiguration con "audioStreamingEnabled": false sobre HTTPS JSON-RPC o WebSocket (wss://) (VERIFIED). En esta modalidad no se requiere Amazon Nova Sonic ni el atributo de pre-lanzamiento x-amz-lex:qic-audio-passthrough: Amazon Connect convierte la voz del llamante a texto (STT), transmite el texto al colaborador A2A externo y sintetiza la respuesta de texto recibida utilizando la voz de ElevenLabs configurada en el bloque Set voice de Connect (VERIFIED / INFERENCE). El llamante escucha la voz de ElevenLabs y conversa con la lógica del agente externo, aunque con una latencia ligeramente superior al streaming de audio puro debido a las etapas separadas de STT y TTS en Connect. La llamada se conserva como un único contacto (1 CTR) en Amazon Connect y Contact Lens opera al 100% en tiempo real y post-llamada. Con el permiso Access Contact Control Panel activo en el Security Profile, Amazon Connect inyecta automáticamente el ARN del contacto (ContactId), las direcciones de origen/destino y el canal dentro del payload INIT_SESSION enviado al servidor A2A (VERIFIED, a2a-collaboration.html y a2a-external-server.html, nov. 2026). Como límite crítico, el servidor externo A2A debe aceptar mensajes de texto y devolver obligatoriamente eventos TRACING_SPAN con startTimeUnixNano, endTimeUnixNano, mensajes de entrada/salida y resultados de herramientas en cada turno, ya que Amazon Connect deshabilita automáticamente cualquier endpoint externo que omita datos de traza desde el primer contacto (VERIFIED, https://docs.aws.amazon.com/connect/latest/adminguide/a2a-trace-enforcement.html, nov. 2026). Asimismo, la cuota inicial predeterminada es de 5 conexiones salientes de terceros concurrentes por instancia (ajustable) (VERIFIED, Eveonix 2026-11-10).

Alternativa 3: Transferencia Externa de Voz (Conector SIP de External Voice Transfer o Transferencia PSTN / Twilio hacia ElevenLabs)

Para utilizar de inmediato el motor conversacional completo de audio extremo a extremo de ElevenAgents sin pasar por Amazon Lex V2 ni por Q in Connect, la arquitectura estándar de mercado consiste en emplear el bloque Transfer to phone number en el flujo de Amazon Connect hacia un número telefónico o troncal SIP vinculada directamente a ElevenLabs (vía Twilio, Chime SDK Voice Connector o el conector nativo External voice systems de Amazon Connect, correspondiente al Patrón 6) (VERIFIED, https://eveonix.com/resources/ai-voice-agent-integration-amazon-connect, 2026-11-10; AWS re:Post https://repost.aws/es/questions/QUhjj_qhY9S_29EUf6npqDpg/does-aws-connect-support-sip-transfers-natively; Simple AI 2026; Dograh 2026). Para el llamante, tras el saludo o enrutamiento inicial en Connect se percibe una transferencia telefónica breve (~1–2 segundos) seguida de la conversación directa en baja latencia con el agente de ElevenLabs. El impacto en grabaciones y Contact Lens depende del mecanismo de transferencia elegido: si se realiza una transferencia PSTN o SIP externa que entrega la llamada a ElevenLabs y, en caso de escalamiento a un humano, ElevenLabs transfiere de vuelta marcando un número DID de entrada de Amazon Connect, se generan dos contactos separados (2 CTRs) en Amazon Connect y Contact Lens no graba ni analiza el tramo conversado en ElevenLabs (salvo que Connect mantenga las dos patas en puente permanente durante toda la llamada, lo cual mantiene un único contacto pero incurre en cargos simultáneos de telefonía entrante y saliente en Connect) (VERIFIED / INFERENCE). Si en cambio se utiliza el conector nativo External Voice Transfer de Amazon Connect con la opción Resume flow after transfer habilitada, el flujo de Connect puede retomar el control al finalizar la sesión externa (VERIFIED).

Para transportar el ContactId de Amazon Connect hacia ElevenLabs en esta tercera alternativa existen dos métodos verificados: si se utiliza el conector SIP de External Voice Systems, el ContactId se envía de forma nativa dentro del encabezado SIP User-to-User (UUI) configurado dinámicamente en el conector (VERIFIED, Eveonix 2026-11-10); si se utiliza una transferencia telefónica PSTN estándar (donde los atributos de contacto de Connect no viajan por la red pública), se coloca un bloque AWS Lambda function justo antes del bloque Transfer to phone number que registra en una base de datos de baja latencia (como DynamoDB) o envía por API el ContactId indexado por el número del llamante ($.CustomerEndpoint.Address / caller_id), de modo que el webhook de inicio de conversación de ElevenLabs recupere el ContactId al recibir la llamada entrante, y antes de devolver la llamada a una cola humana de Connect, una herramienta webhook de ElevenLabs invoque la API connect:UpdateContactAttributes pasando el InitialContactId para adjuntar el atributo handoff_summary que será leído al agente humano mediante un bloque Set whisper flow (VERIFIED, https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect y https://www.usesimple.ai/integrations/amazon-connect, nov. 2026). Los límites conocidos de esta alternativa son la necesidad de solicitar un aumento de cuota de servicio en AWS para habilitar conectores de transferencia de voz externa SIP, el costo adicional por minuto de telefonía saliente/entrante, y el riesgo de colisión al correlacionar por caller_id en PSTN si dos usuarios llaman simultáneamente desde un mismo número de cabecera empresarial (VERIFIED / INFERENCE).

Alternativa 4: Streaming de Medios en Vivo a Amazon Kinesis Video Streams (KVS) + Puente AWS Lambda (Descartada por Unidireccionalidad)

Aunque con frecuencia se plantea utilizar el bloque Start media streaming en el flujo de contacto para extraer el audio del llamante hacia Amazon Kinesis Video Streams (KVS) y procesarlo con una función Lambda o contenedor conectado al WebSocket de ElevenLabs (Patrón 4), las fuentes de arquitectura verificadas advierten que esta ruta no soporta conversación bidireccional en Amazon Connect. Tal como documenta la guía de construcción de agentes de voz (https://eveonix.com/resources/ai-voice-agent-amazon-connect-build-guide, actualizada el 2026-11-10): "Connect streams call audio to Kinesis Video Streams so your service can listen in; it carries audio out of Connect but not a reply back. Best for: Real-time transcription, analytics and monitoring alongside another pattern" (VERIFIED). Debido a que KVS en Amazon Connect es estrictamente un flujo de salida de audio (unidireccional para escucha y monitoreo) y no permite inyectar una pista de audio PCM de retorno directamente al canal de voz del llamante en tiempo real, cualquier intento de responder al usuario obligaría a escribir fragmentos de audio en S3 y reproducirlos mediante un bucle de bloques Play prompt o Get customer input en el flujo de contacto, destruyendo por completo la baja latencia, el manejo de interrupciones (barge-in) y la naturalidad de ElevenAgents (INFERENCE derivada de la restricción verificada de KVS).

3. Lista Priorizada de Experimentos de Diagnóstico en AWS

Con el fin de aislar empíricamente y al menor costo posible cuál de los factores identificados está provocando los fallos en us-east-1, la siguiente tabla presenta seis experimentos secuenciales ordenados desde verificaciones gratuitas de solo lectura en el plano de control hasta pruebas de aislamiento en el plano de ejecución:

Prioridad y Costo	Experimento y Modificación Exacta a Ejecutar en AWS	Resultado que Confirma o Rechaza la Hipótesis	Campo de API o Registro Exacto a Inspeccionar
Experimento 1 (Costo: $0.00 — Solo lectura vía AWS CLI)	

Auditar la instantánea inmutable de la versión :1 del Agente de IA y la configuración del Asistente.

Ejecutar en terminal:

1. aws qconnect get-ai-agent --assistant-id <ASSISTANT_ID> --ai-agent-id <AI_AGENT_ID>:1 --region us-east-1

2. aws qconnect get-assistant --assistant-id <ASSISTANT_ID> --region us-east-1

3. aws kms get-key-policy --key-id <CMK_ID> --policy-name default --region us-east-1

	

Confirma la Causa Raíz 2 si en la salida de la versión :1 no aparece connectInstanceArn dentro de orchestrationAIAgentConfiguration, si existe un orchestrationAIPromptId o aiGuardrailId (prohibidos cuando audioStreamingEnabled es true), o si agentTarget.applicationId contiene el ARN completo en lugar del UUID Id (o viceversa).

	

En la respuesta JSON de get-ai-agent:

aiAgent.configuration.orchestrationAIAgentConfiguration.connectInstanceArn y multiAgentConfigurations[0].handoffAgentConfiguration.agentTarget.applicationId. En get-assistant: assistant.serverSideEncryptionConfiguration.kmsKeyId y assistant.aiAgentConfiguration.

Experimento 2 (Costo: ~$0.00 — Configuración de Logs y Permisos)	

Activar EVENT_LOGS en el Asistente de Q in Connect, añadir Access Contact Control Panel y mapear explícitamente $.Wisdom.SessionArn.

1. Configurar la entrega de logs del asistente a CloudWatch Logs (PutDeliverySource, PutDeliveryDestination, CreateDelivery) con logType: EVENT_LOGS.

2. En el Security Profile asociado al agente :1, activar el permiso Access Contact Control Panel.

3. En el flujo de contacto, agregar un bloque Set voice previo con Set language attribute en en-US, dejar el prompt de Get customer input como un espacio " ", y agregar en Session attributes de Get customer input la clave x-amz-lex:q-in-connect:session-arn asignada dinámicamente al atributo de sistema $.Wisdom.SessionArn.

	

Confirma la Causa Raíz 3 si al realizar una llamada los EVENT_LOGS del asistente muestran el error exacto por el que CreateWisdomSession fallaba silenciosamente (por ejemplo, AccessDeniedException en KMS o fallo de validación del agente por defecto), o si tras fijar el idioma y $.Wisdom.SessionArn desaparece el error HTTP 400.

	

1. Grupo de CloudWatch Logs correspondiente a EVENT_LOGS del asistente de Q in Connect.

2. Salida de aws connect describe-contact --instance-id <INSTANCE_ID> --contact-id <CONTACT_ID> --query "Contact.WisdomInfo.SessionArn".

Experimento 3 (Costo: ~$0.01 — 1 llamada de prueba)	

Aislar la creación de sesión en el bloque Connect assistant respecto al Agente A2A.

Verificar en el bloque Connect assistant del flujo (y en assistant.aiAgentConfiguration del asistente) que el agente de orquestación predeterminado para Agent Assistance sea el agente nativo por defecto del sistema y no el agente personalizado A2A :1. Invocar el agente personalizado A2A :1 exclusivamente a través del atributo de sesión x-amz-lex:q-in-connect:ai-agent-arn en el bloque Get customer input.

	

Confirma que el Agente A2A bloqueaba CreateWisdomSession si tras esta separación DescribeContact muestra WisdomInfo.SessionArn correctamente poblado (distinto de null) y la llamada supera el bloque Connect assistant y la validación 400 de Lex sin necesidad de crear sesiones manuales por CLI.

	

Contact.WisdomInfo.SessionArn en la respuesta de DescribeContact y la presencia de x-amz-lex:q-in-connect:session-arn en los Conversation Logs de Amazon Lex V2.

Experimento 4 (Costo: ~$0.01 — Publicación de versión :2)	

Probar el UUID APPLICATION_ID frente a APPLICATION_ARN en agentTarget.applicationId y publicar la versión :2.

1. Ejecutar aws qconnect update-ai-agent cambiando agentTarget.applicationId al formato alternativo respecto al usado en :1 (colocar el UUID corto Id devuelto por appintegrations create-application, tal como especifica a2a-setup-external.html, asegurándose de no incluir prompt ni guardrail).

2. Publicar la versión :2 con aws qconnect create-ai-agent-version.

3. Asociar el Security Profile al nuevo ARN versionado :2 con aws connect associate-security-profiles --entity-type AI_AGENT.

4. Actualizar x-amz-lex:q-in-connect:ai-agent-arn en el flujo para que apunte a :2.

	

Confirma la Causa Raíz 2 si el error HTTP 502 "has no Connect instance; cannot resolve 3P" desaparece y Amazon Connect procede a iniciar la conexión WebSocket hacia ElevenLabs (observándose la conversación en el workspace de ElevenLabs o un código de estado WebSocket distinto en los logs).

	

Registros del flujo de contacto en el bloque Get customer input, trazas de sesión mediante aws qconnect list-spans --assistant-id <ASSISTANT_ID> --session-id <SESSION_ID> y panel de conversaciones en ElevenLabs.

Experimento 5 (Costo: ~$0.01 — Prueba de Rol IAM en Lex V2)

Validar el Service-Linked Role (SLR) y la política KMS del 2026-10-27 en Amazon Lex V2.

Actualizar el rol IAM personalizado del bot añadiendo el comodín arn:aws:wisdom:*:<accountId>:assistant/<assistantId>/*, la declaración QInConnectKmsCMKPolicy y el principal lexv2.aws.internal en el Trust Policy (o crear un bot de prueba idéntico en en_US con Nova Sonic utilizando el rol vinculado a servicios AWSServiceRoleForLexV2Bots_AmazonConnect_<accountId> y pulsando [Update KMS Policy] en la sección AI agents de la consola de Connect).

Confirma la Causa Raíz 5 si al usar el SLR o las políticas corregidas desaparece cualquier rechazo de permisos entre Lex V2 y wisdom.us-east-1.amazonaws.com durante la apertura o envío de mensajes a la sesión.

Eventos de AWS CloudTrail filtrados por eventSource = wisdom.amazonaws.com y eventName (CreateSession, GetAssistant, SendMessage, GetNextMessage) verificando la ausencia de AccessDenied.

Experimento 6 (Costo: ~$0.01 — Prueba de Aislamiento de Feature Gate)

Probar el handoff A2A en Modo Texto (audioStreamingEnabled: false) sin x-amz-lex:qic-audio-passthrough.

Actualizar el agente de orquestación a "audioStreamingEnabled": false (Modo B de a2a-setup-external.html, añadiendo un orchestrationAIPromptId), publicar la versión :3, asociar el Security Profile a :3 y retirar temporalmente el atributo x-amz-lex:qic-audio-passthrough del bloque Get customer input.

Confirma al 100% la Causa Raíz 1 (Bloqueo por falta de Allowlist en la cuenta) si después de aplicar los Experimentos 1 a 5 tanto el modo audio como el modo texto continúan devolviendo cannot resolve 3P, demostrando que la tabla de resolución 3P requiere activación en backend por AWS Support.

Flow logs de Amazon Connect en el bloque Get customer input y respuesta de qconnect:ListSpans.

 
4. Solicitud de Habilitación para el AWS Account Team / AWS Support e Identificadores Requeridos

Dado que la documentación oficial de ElevenLabs (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, noviembre de 2026) especifica que el soporte para agentes de IA de terceros en Amazon Connect se encuentra en disponibilidad limitada y debe ser habilitado para la cuenta y región de AWS ("Amazon Connect's third-party AI agent support must be enabled for your AWS account", con x-amz-lex:qic-audio-passthrough actuando como compuerta durante el período de pre-lanzamiento) y que la guía de administración de AWS (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, noviembre de 2026) requiere coordinar con el AWS Account Team o Solutions Architect las implementaciones con streaming de audio bidireccional (VERIFIED), se debe remitir el siguiente texto técnico en inglés tanto al AWS Account Team como a través de un caso de AWS Support (Servicio: Amazon Connect, Categoría: AI Agents / Amazon Q in Connect):  

Subject: Enablement Request: Third-Party AI Agent (3P A2A) Audio Streaming / Passthrough Support in us-east-1

Hello AWS Account Team and Amazon Connect Service Engineering,

We are deploying an external third-party conversational AI voice agent (ElevenLabs) integrated with our Amazon Connect Customer instance in us-east-1 using the Agent-to-Agent (A2A) collaboration feature with bidirectional audio streaming, following the official Amazon Connect Administrator Guide ("Set up an external AI agent integration" / a2a-setup-external.html).

Control-Plane Configuration Completed in us-east-1:

Amazon Connect instance on the Connect Customer tier with Contact Lens real-time conversational analytics enabled.

Amazon Q in Connect Assistant (type AGENT) associated with the Connect instance via CreateIntegrationAssociation (WISDOM_ASSISTANT).

AWS AppIntegrations application configured with ApplicationType: A2A_SERVER, AuthType: API_KEY, and a wss:// endpoint, referencing a Secrets Manager secret encrypted with a customer-managed KMS key granting connect.amazonaws.com decrypt permissions, associated with the Connect instance via CreateIntegrationAssociation (IntegrationType: APPLICATION).

Amazon Connect Security Profile granting QConnectAIAgents.View, Wisdom.View, Access Contact Control Panel, and AllowedAIAgents configured with the A2A_SERVER application as Type: THIRD_PARTY.

Q in Connect ORCHESTRATION AI Agent configured with connectInstanceArn, handoffAgentConfiguration (audioStreamingEnabled: true, immediateHandoff: true), no orchestration prompt or guardrail, and the reserved Complete (RETURN_TO_CONTROL) tool, published as an immutable version and associated with the Security Profile on both the unversioned and versioned ARNs (entity-type AI_AGENT).

Amazon Lex V2 bot (en_US locale, Amazon Nova Sonic speech-to-speech) containing a single AMAZON.QInConnectIntent, invoked in the contact flow via Get customer input with session attributes x-amz-lex:q-in-connect:ai-agent-arn and x-amz-lex:qic-audio-passthrough = true.

Observed Runtime Behavior:

On inbound voice calls, the "Connect assistant" flow block (CreateWisdomSession) executes without taking the Error branch, but DescribeContact returns WisdomInfo = null, causing the subsequent "Get customer input" block to fail with HTTP 400 ValidationException ("Amazon Lex needs active session for Q In Connect. Please provide valid session attribute x-amz-lex:q-in-connect:session-arn").

When a valid Q in Connect session ARN is supplied in x-amz-lex:q-in-connect:session-arn with x-amz-lex:qic-audio-passthrough = true, the call fails at the passthrough initialization gate with HTTP 502 BadGatewayException:
"Passthrough init failed: agent=<AI_AGENT_ID>:1 has no Connect instance; cannot resolve 3P (Status Code: 502)"

Requested Actions:

Please enable / allowlist Third-Party AI Agent (3P A2A) support and the prelaunch audio passthrough gate (x-amz-lex:qic-audio-passthrough) for our AWS Account and Amazon Connect instance in us-east-1.

Please verify on the service backend why the runtime passthrough resolver reports "has no Connect instance; cannot resolve 3P" for our versioned orchestration AI agent despite connectInstanceArn, APPLICATION integration association, and AI_AGENT Security Profile associations being active.

Required Identifiers (us-east-1):

AWS Account ID: <INSERT_AWS_ACCOUNT_ID>

AWS Region: us-east-1

Amazon Connect Instance ID: <INSERT_CONNECT_INSTANCE_ID>

Amazon Connect Instance ARN: <INSERT_CONNECT_INSTANCE_ARN>

Q in Connect Assistant ID & ARN: <INSERT_ASSISTANT_ID_AND_ARN>

Q in Connect Orchestration AI Agent ID & Versioned ARN: <INSERT_AI_AGENT_VERSIONED_ARN>

AppIntegrations A2A_SERVER Application ID (UUID) & ARN: <INSERT_APPLICATION_ID_AND_ARN>

Connect Security Profile ID: <INSERT_SECURITY_PROFILE_ID>

Amazon Lex V2 Bot ID & Bot Alias ARN: <INSERT_LEX_BOT_ALIAS_ARN>

Sample Contact IDs & Timestamps (UTC) for HTTP 400 and HTTP 502 calls: <INSERT_SAMPLE_CONTACT_IDS>

Thank you.

De forma simultánea a esta solicitud en AWS, se debe contactar al representante de cuenta o soporte Enterprise de ElevenLabs proporcionando el Workspace ID y el Agent ID de ElevenAgents para verificar que el transporte amazon-connect se encuentre habilitado en dicho espacio de trabajo (VERIFIED, https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, nov. 2026).  

5. Tabla de Contradicciones entre Fuentes

El contraste riguroso de las fuentes primarias publicadas por AWS y por ElevenLabs pone al descubierto cinco contradicciones técnicas directas que inducen a error durante la construcción del plano de control y del flujo de contacto:

Aspecto Técnico Fuente Primaria A (Afirmación, URL y Fecha) Fuente Primaria B (Afirmación Contradictoria, URL y Fecha) Implicación Operativa y Resolución
Identificador esperado en agentTarget.applicationId al crear el Agente de IA

AWS Admin Guide (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html, nov. 2026): En los esquemas JSON de los Modos A, B y C especifica utilizar el ID corto de la aplicación: "applicationId": "YOUR_APPLICATION_ID" (VERIFIED).

ElevenLabs Docs (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, nov. 2026): En el Paso 2.6 indica asignar el ARN completo al campo: agentTarget.applicationId: $APPLICATION_ARN (VERIFIED).

Impacto Crítico: Causa directa potencial del error 502 "cannot resolve 3P". Debe probarse el UUID (Id) devuelto por appintegrations create-application en una nueva versión :2 del agente (Experimento 4).

Estado de Disponibilidad y Documentación de x-amz-lex:qic-audio-passthrough

ElevenLabs Docs (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, nov. 2026): Afirma que la integración está en Limited Availability, exige que AWS habilite el soporte 3P para la cuenta y región, y documenta que x-amz-lex:qic-audio-passthrough = true es obligatorio durante el prelaunch period de AWS (VERIFIED).

AWS Admin Guide (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-collaboration.html y a2a-setup-external.html, nov. 2026): Documenta el Modo C (Audio streaming) como parte de la guía estándar sin etiquetarlo como Preview ni mencionar el atributo x-amz-lex:qic-audio-passthrough en la página de configuración del agente (VERIFIED).

Impacto Crítico: Un ingeniero que siga únicamente la documentación de AWS desconoce tanto el requisito del atributo x-amz-lex:qic-audio-passthrough como la obligatoriedad del allowlist de cuenta en el backend de AWS.

Paso automático vs. explícito de x-amz-lex:q-in-connect:session-arn en el bloque Get customer input

ElevenLabs Docs (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, nov. 2026): Instruye configurar manualmente solo dos atributos de sesión en Get customer input: x-amz-lex:q-in-connect:ai-agent-arn y x-amz-lex:qic-audio-passthrough, dando por sentado que Connect inyecta session-arn implícitamente (VERIFIED).

Repositorio oficial aws-samples (https://github.com/aws-samples/sample-devops-agent-oncall-connect, 2026) y AWS re:Post (2026): Indican pasar x-amz-lex:q-in-connect:session-arn explícitamente en los atributos de sesión del bloque Get customer input apuntando a $.Wisdom.SessionArn (VERIFIED).

Impacto Alto: Declarar explícitamente x-amz-lex:q-in-connect:session-arn = $.Wisdom.SessionArn en el bloque Get customer input asegura que el ARN de sesión llegue a Lex en cuanto CreateWisdomSession tenga éxito.

Permisos requeridos en el Security Profile del Agente de IA

ElevenLabs Docs (https://elevenlabs.io/docs/eleven-agents/phone-numbers/c-caa-s-integrations/amazon-connect, nov. 2026): Crea el perfil de seguridad únicamente con --permissions QConnectAIAgents.View Wisdom.View y la lista AllowedAIAgents (VERIFIED).

AWS Admin Guide (https://docs.aws.amazon.com/connect/latest/adminguide/a2a-setup-external.html y a2a-collaboration.html, nov. 2026): Exige que el Security Profile otorgue también el permiso Access Contact Control Panel para compartir el contexto del contacto (direcciones y canal) con el colaborador externo (VERIFIED).

Impacto Medio-Alto: Debe añadirse Access Contact Control Panel al perfil de seguridad; sin él, Connect omite los metadatos de dirección y canal que ElevenLabs espera recibir en INIT_SESSION.

Principal del Servicio en el Trust Policy del Rol IAM de Amazon Lex V2

Amazon Lex V2 Developer Guide (https://docs.aws.amazon.com/lexv2/latest/dg/built-in-intent-qinconnect.html, nov. 2026): Especifica el principal "Service": "lexv2.aws.internal" en la política de confianza para roles personalizados con AMAZON.QInConnectIntent (VERIFIED).

Classmethod (https://dev.classmethod.jp/articles/amazon-connect-ai-agent-lex-kms-policy-update/, 2026-05-11 [ANTERIOR A SEPTIEMBRE 2026]): Muestra que el rol vinculado a servicios creado por AWS (AWSServiceRoleForLexV2Bots_AmazonConnect_<accountId>) confía en lexv2.amazonaws.com (VERIFIED).

Impacto Medio: En un rol IAM personalizado se deben incluir ambos principales (["lexv2.amazonaws.com", "lexv2.aws.internal"]) en el Trust Policy para evitar rechazos de sts:AssumeRole.

 
6. Conclusiones y Hoja de Ruta de Resolución

El diagnóstico integral basado en fuentes primarias demuestra que los cuatro síntomas observados en us-east-1 conforman una cadena causal coherente: primero, la acción interna CreateWisdomSession del bloque Connect assistant falla de manera silenciosa (comportamiento documentado por AWS que no activa la rama Error del bloque pero impide que UpdateContactData escriba $.Wisdom.SessionArn), lo cual deja WisdomInfo = null en DescribeContact y provoca que entre 1.5 y 2 segundos más tarde el bloque Get customer input sea rechazado por Amazon Lex V2 con HTTP 400 ValidationException al faltar x-amz-lex:q-in-connect:session-arn; segundo, cuando se inyecta manualmente una sesión creada con CreateSession fuera del flujo de contacto, dicha sesión carece de vinculación interna con un contacto activo de la instancia y colisiona en la compuerta de passthrough de voz con HTTP 502 BadGatewayException ("Passthrough init failed: agent=<ai-agent-id>:1 has no Connect instance; cannot resolve 3P"), resultado directo de la falta de habilitación en lista blanca (Limited Availability / Prelaunch Gate) en la cuenta de AWS y/o de la discrepancia entre APPLICATION_ID y APPLICATION_ARN en agentTarget.applicationId dentro de la versión inmutable :1 del agente de orquestación.  

Para resolver el bloqueo de forma definitiva, se recomienda ejecutar de inmediato los Experimentos 1 a 4 (habilitar EVENT_LOGS en el asistente de Q in Connect para exponer el fallo silencioso de CreateWisdomSession, añadir el permiso Access Contact Control Panel al perfil de seguridad, configurar explícitamente x-amz-lex:q-in-connect:session-arn = $.Wisdom.SessionArn junto con el idioma en-US en el flujo, y publicar una versión :2 del agente utilizando el UUID corto en agentTarget.applicationId sin prompt ni guardrail, asociando el perfil de seguridad a :2) y remitir en paralelo la solicitud de allowlist de Third-Party AI Agent Audio Streaming al equipo de cuenta de AWS y al representante de ElevenLabs. Mientras AWS y ElevenLabs completan la habilitación en el backend, la arquitectura puede entrar en operación inmediata en us-east-1 implementando ya sea el Agente de IA nativo de Connect con ElevenLabs configurado como proveedor TTS de terceros en el bloque Set voice (que conserva un único contacto y el 100% de Contact Lens) o una transferencia externa de voz (SIP/PSTN) hacia ElevenLabs sincronizando el ContactId y el handoff_summary mediante AWS Lambda y connect:UpdateContactAttributes.
