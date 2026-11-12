# Investigación técnica: Amazon Connect → Lex `AMAZON.QInConnectIntent` → Q in Connect ORCHESTRATION → ElevenLabs A2A audio

## Resumen ejecutivo

**[VERIFIED — alta confianza] La causa inmediata del primer error está antes de A2A y antes de ElevenLabs: el contacto no tiene una Q in Connect session asociada.** Amazon Lex documenta que, cuando `AMAZON.QInConnectIntent` se invoca desde Amazon Connect, el `session ARN` debe ser creado y pasado por Amazon Connect; el atributo esperado es `x-amz-lex:q-in-connect:session-arn`. `DescribeContact.WisdomInfo.SessionArn` es precisamente el campo de contacto donde Connect expone esa asociación. Tus llamadas muestran `WisdomInfo=null`, por lo que Lex está rechazando correctamente el turno con `"Amazon Lex needs active session for Q In Connect"`. AWS Lex Developer Guide, snapshot vigente 12-Nov-2026; Amazon Q Connect API Reference publicado 6-Nov-2026. citeturn125169view0turn429499search5turn126056search9

**[VERIFIED — alta confianza] El hallazgo más importante es que el bloque visual `Connect assistant` no equivale solamente a `CreateWisdomSession`.** Un blog técnico oficial de AWS publicado el **30-Sep-2026** explica explícitamente que el bloque está compuesto por **dos flow actions**: `CreateWisdomSession`, que abre la sesión, y `UpdateContactData`, que escribe el resultado como `WisdomSessionArn` sobre el contacto. AWS advierte además que, si se omite el segundo action, el flujo puede continuar sin error mientras el contacto queda sin sesión asociada. Eso coincide casi exactamente con tus síntomas: el bloque parece exitoso, pero `WisdomInfo=null`. citeturn111643view0turn714930view0

**[INFERENCE — alta confianza] Por tanto, la primera hipótesis que probaría es que el JSON publicado de tu flow contiene `CreateWisdomSession` pero no el `UpdateContactData` correspondiente, o que ese segundo action no está escribiendo `WisdomSessionArn` al `Current` contact.** No importa cuánto delay insertes después: un sleep no puede reparar una asociación que nunca fue escrita. La evidencia que lo confirmaría es el JSON exportado de `DescribeContactFlow`/`GetContactFlow` y `DescribeContact.WisdomInfo.SessionArn` inmediatamente después del bloque. La inferencia se apoya en el comportamiento documentado del par de actions y en el síntoma observado. citeturn111643view0turn714930view0

**[VERIFIED — alta confianza] Existe además una segunda barrera independiente para llegar a ElevenLabs.** La documentación actual de ElevenLabs declara literalmente que la integración Amazon Connect está en **“limited availability”**, que `"Amazon Connect’s third-party AI agent support must be enabled for your AWS account"` y que el transport de Amazon Connect debe habilitarse por workspace en ElevenLabs. También exige habilitación para la combinación account + Region. La página está vigente al **12-Nov-2026**; no expone una fecha pública de publicación. citeturn125169view2turn607722search3

**[VERIFIED — alta confianza] Esto no significa que A2A de AWS siga en preview.** AWS anunció públicamente **General Availability / launch** de agent-to-agent collaboration el **22-Sep-2026**, incluyendo agentes externos y bidirectional voice, y las release notes indican disponibilidad en las regiones donde se ofrece Connect Customer. `us-east-1` está en la lista de regiones de Connect Customer. Por tanto, hay una distinción crítica entre **A2A como capability pública de AWS** y **el runtime third-party/ElevenLabs todavía gated según ElevenLabs**. citeturn695346search6turn607722search0turn607722search2

**[INFERENCE — media-alta confianza] El segundo error, `"Passthrough init failed: agent=<id>:1 has no Connect instance; cannot resolve 3P"`, apunta a una falla en la resolución runtime del ORCHESTRATION agent hacia su Connect instance, no a WebSocket, API key o ElevenLabs.** El WebSocket todavía no se ha intentado abrir. Dos explicaciones son compatibles con la evidencia: el objeto **versionado** realmente no contiene `connectInstanceArn`, aunque el draft/unversioned sí; o el backend de third-party A2A no tiene habilitada/resuelta la instance para esa account/Region. No encontré documentación pública de AWS, re:Post ni GitHub que documente ese mensaje exacto. AWS sí documenta que `connectInstanceArn` pertenece a `OrchestrationAIAgentConfiguration` y lo incluye en todos sus ejemplos de external collaboration. citeturn529894search3turn529894search0

**[VERIFIED — media confianza] Tu custom Lex IAM role no es, por sí sola, incorrecta, pero debe reproducir exactamente el acceso que Lex agrega automáticamente al Service-Linked Role.** AWS requiere `wisdom:CreateSession`, `wisdom:GetAssistant`, `wisdom:SendMessage` y `wisdom:GetNextMessage`; si el **assistant** usa una customer-managed KMS key, también `kms:Decrypt` y `kms:GenerateDataKey` con las condiciones documentadas. El CMK usado solamente para el **ElevenLabs Secrets Manager secret** no genera ese requisito para el Lex role: ese secret lo lee `connect.amazonaws.com`. AWS también documenta una trust statement específica para `lexv2.aws.internal`. citeturn125169view0turn125169view1

Mi ranking final de causas es: **(1) session creada pero no attached al contact por ausencia/fallo de `UpdateContactData`: alta; (2) third-party A2A runtime/ElevenLabs transport no habilitado para account+Region/workspace: alta para el segundo fallo; (3) `connectInstanceArn` ausente del snapshot de AI agent version `:1`: media-alta; (4) custom Lex role incompleto —especialmente trust o KMS si el assistant usa CMK—: media-baja, porque el primer error es session-state, no `AccessDenied`; (5) problemas de AppIntegration secret/WebSocket: baja en esta fase, porque todavía no se llega a ElevenLabs.**

## Respuestas a A–G

**A. ¿Quién crea la Q session y quién inyecta `x-amz-lex:q-in-connect:session-arn`?**

**[VERIFIED]** `CreateSession` es la API de Amazon Q in Connect para crear el container contextual; su referencia afirma que Connect crea una nueva Q session para cada contacto donde Q in Connect está habilitado. La flow action `CreateWisdomSession` asocia el assistant/domain al contacto. citeturn725270search4turn725270search0

**[VERIFIED]** Sin embargo, para que esa sesión quede materializada como contact state, `UpdateContactData` dispone del parámetro `WisdomSessionArn`. El walkthrough oficial AWS del 30-Sep-2026 afirma que el bloque UI `Connect assistant` genera ambos actions y que `UpdateContactData` es el que escribe `$.Wisdom.SessionArn`. citeturn111643view0turn714930view0

**[INFERENCE]** Connect usa luego esa sesión attached al contacto para suministrar `x-amz-lex:q-in-connect:session-arn` a Lex. AWS Lex no documenta el código interno exacto de esa inyección, pero sí exige que el ARN sea creado y pasado por Amazon Connect; y el ejemplo oficial de ElevenLabs configura manualmente únicamente `x-amz-lex:q-in-connect:ai-agent-arn` y `x-amz-lex:qic-audio-passthrough`, no el session ARN. Es decir, en el path normal el usuario **no debe inventar ni crear manualmente ese atributo**. citeturn125169view0turn375441view0

**[VERIFIED] Condiciones documentadas para voice:** Connect Customer tier, no Customer Basic; assistant asociado a la instance; Lex V2 asociado a la instance; para audio streaming, locale Nova Sonic speech-to-speech y un único `AMAZON.QInConnectIntent`; external audio requiere `wss://`, `audioStreamingEnabled=true`, `immediateHandoff=true`, un único collaborator, ORCHESTRATION sin orchestration prompt ni guardrail y solamente reserved `Complete` —y opcional `Escalate`— tools. citeturn125169view1turn529894search0turn529894search1

**[VERIFIED]** Para usar AI agents en voice, la documentación del `Connect assistant` exige **real-time conversational analytics** en el flow. La instance debe tener conversational analytics habilitado y, para voice, recording/speech analytics correctamente configurado. La ubicación del analytics block dentro del flow no importa para ese requisito. citeturn125169view3turn126056search3

**[VERIFIED]** Tu `en_US` es compatible con el path mostrado por ElevenLabs. AWS Lex indica además que assistant/domain y Lex deben estar en la misma Region. Para audio A2A, AWS exige Nova Sonic; no encontré un requisito adicional que diga que el `Connect assistant` deba usar otro language field diferente al bot locale para este caso. citeturn125169view0turn529894search1

**[VERIFIED]** El bloque actual tiene un campo para seleccionar un Orchestration AI agent “for Agent Assistance”. Sin embargo, el procedimiento público de ElevenLabs solamente pide seleccionar el assistant en ese bloque y pasa el versioned ORCHESTRATION ARN mediante `x-amz-lex:q-in-connect:ai-agent-arn`. **No encontré documentación primaria que diga que ese campo opcional del bloque sea obligatorio para el A2A self-service path.** citeturn125169view3turn375441view0

**[VERIFIED]** `us-east-1` está soportado por Connect Customer y AWS declara A2A disponible donde se ofrece Connect Customer. No encontré una sublista pública de regiones exclusivamente para external A2A audio distinta de esa lista. citeturn607722search0turn607722search2

**B. ¿Cómo puede el `Connect assistant` “pasar” y dejar `WisdomInfo` vacío?**

**[VERIFIED]** Hay una explicación oficial y muy concreta: el visual block está compuesto por más de un flow action. AWS documentó el 30-Sep-2026 que omitir su `UpdateContactData` permite que el flow siga sin error pero deja al contacto sin la Q session attached. Eso es el match más fuerte con tu caso. citeturn111643view0

**[INFERENCE]** Esto es especialmente relevante si el flow fue importado, generado vía API/CDK, editado como JSON o creado originalmente antes de cambios recientes del diseñador. Debes inspeccionar el **contenido publicado**, no confiar en lo que muestra visualmente el canvas. AWS también advierte en troubleshooting que imports/API updates pueden dejar diferencias entre display y resource content. citeturn942342search30

**[REPORTED BY A SINGLE SOURCE — fuente comunitaria, anterior a Sep-2026]** Un artículo de Classmethod de **11-Mar-2025 [OLD]** reproduce otra clase de fallo de Q in Connect: el Lex SLR no había recibido sus permissions para el assistant. El autor eliminó el bot, deshabilitó/re-habilitó `"Enable Lex Bot Management in Amazon Connect"`, esperó a que AWS actualizara el SLR y recreó el bot; después funcionó. citeturn440350search1

**[REPORTED BY A SINGLE SOURCE — re:Post, anterior a Sep-2026]** Una pregunta de AWS re:Post documenta el mismo problema con `AWSServiceRoleForLexV2Bots_AmazonConnect_*` y `wisdom:CreateSession`; usuarios reportan que toggling Lex Bot Management reparó el SLR. La respuesta no fue revisada por un expert, así que no la trataría como comportamiento contractual. citeturn440350search3

**[VERIFIED]** Ese bug histórico del SLR **no explica directamente `WisdomInfo=null` si tu `Connect assistant` falla antes de Lex**, y tampoco aplica automáticamente a un custom IAM role. Sí justifica revisar CloudTrail para distinguir `AccessDenied` de session-attachment failure. AWS recomienda flow logs y Lex conversation logs para aislar integrations. citeturn440350search6

**C. Allowlist/prelaunch/estado actual.**

**[VERIFIED]** AWS lanzó agent-to-agent collaboration el **22-Sep-2026** para Connect Customer con external agents y bidirectional voice. Las release notes no lo etiquetan como preview. Desde el punto de vista de AWS, A2A como feature es público. citeturn695346search6turn607722search0

**[REPORTED BY A SINGLE SOURCE — ElevenLabs, vigente 12-Nov-2026]** ElevenLabs todavía llama su Amazon Connect transport **“limited availability”** y afirma que `"Amazon Connect’s third-party AI agent support must be enabled for your AWS account"` y que el transport debe habilitarse por workspace. Su requirement más detallado dice account **and Region**. citeturn125169view2

**[REPORTED BY A SINGLE SOURCE — ElevenLabs]** La misma guía dice que `x-amz-lex:qic-audio-passthrough` `"gates the third-party voice path during AWS’s prelaunch period"` y que dejará de ser necesario cuando la feature sea pública. Esta frase parece desactualizada frente al launch de AWS del 22-Sep-2026, pero ElevenLabs todavía indica que dejar el atributo es harmless. citeturn834652view0

**[VERIFIED]** AWS no publica, en las páginas que encontré, un formulario de self-service para habilitar “third-party A2A”. La documentación AWS actual para external audio dice que se debe trabajar con el **AWS account team o Solutions Architect** para revisar voice streaming antes de producción. citeturn125169view1

**[NOT FOUND]** No encontré un AWS Support form público, Service Quota, entitlement API, instance attribute visible ni CLI command que permita comprobar directamente `"third-party AI agent support enabled"`. Por eso un control-plane `CreateApplication(A2A_SERVER)` exitoso **no prueba** que el media runtime esté enabled.

**D. Custom IAM role versus `AWSServiceRoleForLexV2Bots`.**

**[VERIFIED]** Sí hay una diferencia contractual. Si el bot usa el SLR, Lex puede actualizar automáticamente la policy cuando se agrega `AMAZON.QInConnectIntent`. Con custom IAM role, tú debes agregar manualmente las permissions. citeturn125169view0

La policy documentada incluye:

```text
wisdom:CreateSession
wisdom:GetAssistant
wisdom:SendMessage
wisdom:GetNextMessage
```

y, **solamente si el Q in Connect assistant usa una customer-managed KMS key**:

```text
kms:Decrypt
kms:GenerateDataKey
```

con `kms:ViaService = wisdom.<region>.amazonaws.com` y el encryption context del assistant. AWS Lex Developer Guide vigente 12-Nov-2026. citeturn125169view0

**[VERIFIED]** La documentación también muestra una trust policy para `lexv2.aws.internal` restringida por `aws:SourceAccount` y el bot-alias ARN. Un custom role merece comparación literal contra esa trust policy, no sólo contra las action permissions. citeturn125169view0

**[VERIFIED]** El CMK que protege el **ElevenLabs API key secret** es otro trust boundary: ahí quien necesita `kms:Decrypt` y `secretsmanager:GetSecretValue` es `connect.amazonaws.com`, no el Lex role. citeturn125169view1

**[INFERENCE]** Dado que tu role ya tiene las cuatro `wisdom:*` indicadas, revisaría antes el trust relationship y si **el assistant**, no el secret, usa CMK. Si CloudTrail no muestra `AccessDenied`, no invertiría tiempo recreando el bot únicamente para imitar el workaround del SLR.

**E. Ejemplo público funcional.**

**[VERIFIED]** Sí existe uno muy cercano a un end-to-end reference implementation: la guía oficial de ElevenLabs “Amazon Connect”, vigente al 12-Nov-2026. Incluye CLI/`awscurl`, KMS, Secrets Manager, `A2A_SERVER`, integration association, security profile, ORCHESTRATION agent, versioning, Lex, flow, pruebas, dynamic variables, transfers y troubleshooting. No encontré un repo público oficial que incluya un exported flow JSON/CDK específico para **ElevenLabs A2A audio**, pero la guía contiene los payloads suficientes para reproducirlo. citeturn375441view0turn834652view0

Su flow público es:

```text
Set logging behavior
→ Connect assistant
→ Get customer input (Lex alias)
→ Check $.Lex.SessionAttributes.Tool
```

y manualmente define sólo:

```text
x-amz-lex:q-in-connect:ai-agent-arn = <versioned ORCHESTRATION ARN>
x-amz-lex:qic-audio-passthrough    = true
```

No configura manualmente `x-amz-lex:q-in-connect:session-arn`. citeturn375441view0

**[VERIFIED]** El ORCHESTRATION agent del ejemplo tiene `connectInstanceArn`, `locale=en_US`, un solo `handoffAgentConfiguration`, `audioStreamingEnabled=true`, `immediateHandoff=true`, y reserved `Complete`. La guía también asocia el security profile tanto al ARN unversioned como al versioned `:1`, exactamente como hiciste. citeturn375441view0

**[VERIFIED]** Una diferencia visible respecto de tu flow es que la receta ElevenLabs no muestra el `Set recording and analytics behavior`, aunque AWS exige real-time conversational analytics para AI agents en voice. Como tú sí lo tienes, esa omisión no explica tu fallo. citeturn375441view0turn125169view3

**[VERIFIED — posible inconsistencia documental]** AWS generic setup llama al target `applicationId` y sus ejemplos usan `YOUR_APPLICATION_ID`; ElevenLabs muestra en ese mismo campo un placeholder denominado `<APPLICATION_ARN>`. Ambos payloads son públicos. Si tú usaste el ARN porque seguiste ElevenLabs, vale la pena comprobar el valor persisted en `GetAIAgent`, aunque el hecho de que la API lo haya aceptado reduce la probabilidad de que sea tu problema principal. citeturn529894search0turn375441view0

**[VERIFIED]** Una sesión A2A exitosa entrega a ElevenLabs, entre otros, `amazon_connect_contact_id`, `amazon_connect_contact_arn`, instance IDs y `system__call_id`, por lo que en el native path no necesitas inventar un mecanismo para propagar `ContactId`. citeturn834652view0

**F. `"agent ... has no Connect instance; cannot resolve 3P"`.**

**[NOT FOUND]** No encontré esa cadena exacta en docs.aws.amazon.com, AWS re:Post, AWS GitHub ni documentación ElevenLabs indexada al 12-Nov-2026.

**[VERIFIED]** Lo documentado es que el ORCHESTRATION configuration tiene un `connectInstanceArn`, y AWS lo incluye explícitamente en el setup de external collaborators. El published AI agent version es el resource que el flow referencia mediante `x-amz-lex:q-in-connect:ai-agent-arn`. citeturn529894search3turn529894search0turn375441view0

**[INFERENCE — media-alta confianza]** `"has no Connect instance"` debería leerse literalmente como un fallo anterior a application resolution: el passthrough backend tomó `<ai-agent-id>:1` pero no obtuvo una usable Connect instance association de ese snapshot/runtime context, y por ello no pudo `"resolve 3P"`. Eso explica que ElevenLabs no vea WebSocket alguno.

**[INFERENCE]** Hay que comprobar **la versión `:1`**, no sólo el draft:

```bash
aws qconnect get-ai-agent \
  --assistant-id <ASSISTANT_ID> \
  --ai-agent-id <AI_AGENT_ID>:1 \
  --region us-east-1
```

y verificar que la respuesta versionada contiene exactamente:

```text
configuration.orchestrationAIAgentConfiguration.connectInstanceArn
configuration.orchestrationAIAgentConfiguration.multiAgentConfigurations[]
```

con el expected instance y third-party application target.

**[INFERENCE]** Si el versioned object contiene correctamente `connectInstanceArn` pero el error persiste, la hipótesis de backend entitlement/account-region enablement sube mucho de probabilidad, especialmente dada la declaración explícita de ElevenLabs sobre limited availability. citeturn125169view2

**G. Alternativas si native A2A no está habilitado.**

| Alternativa | Caller UX | Connect recording / Contact Lens | `ContactId` hacia ElevenLabs | Límites |
|---|---|---|---|---|
| **Transfer to phone number → Twilio number managed by ElevenLabs** | **[VERIFIED]** Connect hace un external PSTN transfer; ElevenLabs puede atender inbound sobre un Twilio number. citeturn691741search4turn942342search0 | **[VERIFIED]** Si el transfer ocurre durante IVR/flow interaction, AWS afirma que recording continúa y captura lo que el cliente dice y oye después del transfer. **[NOT FOUND]** No encontré garantía equivalente de que toda la conversación externa mantenga el mismo nivel de Contact Lens semantics del native A2A path. citeturn691741search0 | **[INFERENCE]** `Transfer to phone number` no ofrece headers personalizados. Por defecto pasa el caller ID, no `ContactId`. Puedes registrar previamente un mapping en Lambda `{ANI, timestamp/correlation-id → ContactId}` y resolverlo desde un ElevenLabs initiation webhook. | PSTN leg adicional, costo, caller-ID matching imperfecto, no A2A traces/outcomes. |
| **Connect → número PSTN que termina en SBC/SIP → ElevenLabs SIP** | **[VERIFIED]** ElevenLabs soporta SIP trunking; Enterprise/trial enablement. citeturn691741search7 | Igual que external transfer desde la perspectiva de Connect. | Se puede enriquecer en tu SBC si controlas el SIP leg; Connect flow por sí mismo no expone SIP headers arbitrarios. | Más infraestructura y telecom complexity. |
| **Direct SIP trunking de Connect a ElevenLabs** | — | — | — | **[VERIFIED] No hay un estándar native Connect flow → arbitrary SIP URI equivalente al A2A path.** AWS advierte que arquitecturas Connect + Chime Voice Connector/SIP bridges son tightly controlled y requieren architecture review; no deben asumirse como un simple BYOC bridge. citeturn691741search8 |
| **ElevenLabs sólo como TTS/pre-generated prompts** | Connect sigue controlando turn-taking; voces ElevenLabs pueden usarse como archivos/prompt content generados fuera del realtime path. | Connect conserva su contacto/recording normal. | Lambda ya conoce `ContactId`. | **[INFERENCE]** No sustituye ElevenAgents; latencia y barge-in hacen poco atractivo generar TTS por turno. |
| **Kinesis Video Streams + Lambda/custom bridge** | **[VERIFIED]** Connect puede stream audio “from the customer” y “to the customer” hacia KVS para captura/análisis. citeturn691741search2turn691741search3 | Contact remains in Connect y puedes conservar recording/analytics. | Stream/contact metadata permite correlación. | **[VERIFIED/INFERENCE]** KVS es un capture stream, no una API para inyectar arbitrary generated audio de vuelta al caller. Por sí solo **no es un full-duplex ElevenLabs bridge**; necesitarías otro media/telephony path. |
| **External PSTN transfer con `Resume flow after disconnect`** | **[VERIFIED]** ElevenLabs atiende; si el external party disconnects primero, Connect puede retomar el flow. citeturn691741search4 | Recording puede continuar en flow transfer. | Igual que PSTN mapping anterior. | No tienes native `Complete`/`Escalate`; debes modelar el outcome indirectamente. |

**[VERIFIED]** Para un fallback productivo hoy, el patrón menos riesgoso es **Connect `Transfer to phone number` → Twilio number imported into ElevenLabs**. Es soportado por ambos productos sin inventar un bidirectional media bridge. Pierdes, eso sí, las ventajas del native A2A: un único logical agent session, A2A traces, `Complete`/`Escalate`, contact context automático y native `amazon_connect_contact_id`. citeturn691741search4turn942342search0turn834652view0

## Experimentos priorizados en AWS

**[VERIFIED/INFERENCE]** Los siguientes tests están ordenados por costo y capacidad discriminatoria:

1. **Exporta el flow publicado y busca el segundo action del `Connect assistant`.** No cambies nada todavía. Debes encontrar tanto `CreateWisdomSession` como un `UpdateContactData` que escriba `WisdomSessionArn` para `TargetContact=Current`. Si sólo aparece `CreateWisdomSession`, confirma la causa raíz del error 400. Fuente de referencia: AWS blog 30-Sep-2026 y flow-language API. citeturn111643view0turn714930view0

2. **Recrea únicamente el `Connect assistant` block desde el diseñador actual**, publícalo y compara el JSON before/after. Confirmación: la nueva versión introduce el action que actualiza contact data y, en la siguiente llamada, `describe-contact` devuelve `WisdomInfo.SessionArn`. Rechazo: el JSON ya tenía ambos y `WisdomInfo` sigue null.

3. **Después del `Connect assistant`, ejecuta una Lambda diagnóstica que haga `DescribeContact`.** Loguea solamente `ContactId` y `WisdomInfo.SessionArn`. Confirmación de session plumbing: el ARN está presente antes de entrar a Lex. Si está null, todavía no pruebes A2A.

4. **Elimina el `x-amz-lex:q-in-connect:session-arn` manual.** Una vez que `WisdomInfo.SessionArn` exista, deja que Connect siga el path normal. Confirmación: el Lex conversation log muestra automáticamente `x-amz-lex:q-in-connect:session-arn=<same ARN>`. AWS Lex requiere que Connect cree/pase esa sesión. citeturn125169view0

5. **Prueba el mismo bot sin A2A**, temporalmente sin `x-amz-lex:qic-audio-passthrough` y con un normal Q interaction si tu agent config lo permite. Objetivo: separar session plumbing de passthrough. Si Q/Lex funciona pero audio A2A produce el 502, el problema está en A2A runtime, no en Q session creation.

6. **Obtén el ORCHESTRATION agent versionado `:1`.** Comprueba `connectInstanceArn`, `multiAgentConfigurations`, `audioStreamingEnabled`, `immediateHandoff`, target application y tools. Si `connectInstanceArn` falta en `:1` aunque exista en unversioned, crea una nueva version después del update y usa `:2`. Esto confirmaría directamente el significado práctico de `"has no Connect instance"`. citeturn529894search3

7. **Verifica el target exactamente como está persisted.** Compara `agentTarget.applicationId` con el `Id` devuelto por AppIntegrations y con el ARN. AWS generic docs usan application **ID**; ElevenLabs muestra ARN en su sample. Si hoy tienes ARN, prueba una nueva agent version utilizando el literal `Id` devuelto por `CreateApplication`; si el 502 cambia o desaparece, habrás encontrado una incompatibilidad/documentation bug. citeturn695346search0turn375441view0

8. **Comprueba security-profile association sobre el ARN versionado.** Usa `ListSecurityProfileAIAgents`/equivalente actual para confirmar que `:1` está realmente asociado, además del draft. El profile debe incluir la third-party application en `AllowedAIAgents`. citeturn529894search5turn529894search7

9. **Audita el Lex custom IAM role contra la policy oficial.** Primero trust policy para `lexv2.aws.internal`; después las cuatro `wisdom:*`; finalmente KMS sólo si el **assistant** usa CMK. Revisa CloudTrail para `AccessDenied`. Si no existe, no cambies de role todavía. citeturn125169view0

10. **A/B con el Lex SLR.** Crea un bot mínimo nuevo mediante el Connect admin website para que AWS gestione `AWSServiceRoleForLexV2Bots_AmazonConnect_*`. Usa el mismo assistant. Si ese bot crea/pasa la session y el custom-role bot no, la diferencia está en IAM/trust. Si ambos fallan idéntico, IAM deja de ser una hipótesis fuerte. El workaround Classmethod sirve sólo como indicio histórico. citeturn440350search1turn440350search3

11. **Confirma entitlement con AWS antes de seguir modificando recursos.** Si `WisdomInfo` ya funciona y el versioned agent contiene el `connectInstanceArn`, pero el 502 `"cannot resolve 3P"` persiste y nunca aparece un WebSocket en ElevenLabs, pide confirmación explícita de third-party A2A audio enablement para account + `us-east-1`. La documentación de ElevenLabs hace esta comprobación obligatoria. citeturn125169view2

12. **Confirma por separado el workspace transport de ElevenLabs.** Sólo después de superar el 502. Si AWS ya abre WebSocket pero ElevenLabs no registra conversation, verifica `"Amazon Connect transport enabled"`, API key/workspace, `AccessUrl` y region/residency endpoint. citeturn834652view1

## Texto para AWS Support / account team

**[INFERENCE — recomendado]** Enviaría el caso en inglés para evitar ambigüedad entre el GA público de A2A y el posible runtime entitlement:

> **Subject: Confirm/enable Amazon Connect third-party A2A bidirectional audio support for account and us-east-1**
>
> We are implementing the Amazon Connect Customer external AI agent integration documented under “Agent-to-agent collaboration” / “Set up an external AI agent integration”, using an `A2A_SERVER` AppIntegrations application and an ORCHESTRATION Q in Connect AI agent with `audioStreamingEnabled=true` and `immediateHandoff=true`.
>
> The Connect Customer instance is in `us-east-1` and is on the Connect Customer tier.
>
> All control-plane operations succeed, including:
>
> `CreateApplication(ApplicationType=A2A_SERVER)`, application/instance association, AI agent creation and versioning, `connectInstanceArn`, `AllowedAIAgents` with type `THIRD_PARTY`, and security-profile association to the published AI agent version.
>
> We need AWS to confirm whether **third-party AI agent / external A2A bidirectional audio runtime support is enabled for this AWS account and Region (`us-east-1`)**, and enable it if an account/Region entitlement is still required.
>
> After supplying a valid Q in Connect session, the runtime currently returns:
>
> `BadGatewayException: Passthrough init failed: agent=<AI_AGENT_ID>:<VERSION> has no Connect instance; cannot resolve 3P (Status Code: 502)`
>
> No WebSocket connection is attempted to the external provider.
>
> Please confirm:
>
> 1. whether this account and `us-east-1` are enabled for external/third-party A2A voice passthrough;
> 2. whether any prelaunch/allowlist entitlement is still required despite the September 22, 2026 GA announcement;
> 3. whether `x-amz-lex:qic-audio-passthrough=true` is still required;
> 4. why the published AI agent version is reported as having “no Connect instance” when `configuration.orchestrationAIAgentConfiguration.connectInstanceArn` is populated;
> 5. whether any backend association or entitlement must be created by AWS for the Connect instance before a third-party application can be resolved at runtime.
>
> We can provide the following non-secret identifiers privately in the support case:
>
> - AWS account ID
> - Region
> - Amazon Connect instance ID and ARN
> - Q in Connect assistant ID/ARN
> - ORCHESTRATION AI agent ID, unversioned ARN and published version ARN
> - AppIntegrations application ID and ARN
> - integration-association ID
> - security-profile ID
> - Lex bot ID and alias ARN
> - affected ContactIds
> - UTC timestamps for failed calls
> - AWS request IDs from the `ValidationException` and `BadGatewayException`
>
> No API keys or secret values need to be shared.

**[VERIFIED]** Además, AWS recomienda involucrar al account team o Solutions Architect para external bidirectional voice validation antes de producción, por lo que este request sigue el canal descrito en su documentación. citeturn125169view1

## Contradicciones y calidad de las fuentes

| Tema | Fuente A | Fuente B | Evaluación |
|---|---|---|---|
| Estado de A2A | **[VERIFIED] AWS, 22-Sep-2026:** A2A con external agents y bidirectional voice fue lanzado públicamente. citeturn695346search6 | **[REPORTED BY A SINGLE SOURCE] ElevenLabs, vigente 12-Nov-2026:** integración Amazon Connect en “limited availability”, AWS debe enable third-party support por account/Region. citeturn125169view2 | No necesariamente incompatibles: feature AWS GA, provider/runtime path aún gated. |
| `x-amz-lex:qic-audio-passthrough` | **[REPORTED BY A SINGLE SOURCE] ElevenLabs:** requerido durante AWS `"prelaunch period"` y innecesario cuando sea public. citeturn834652view0 | **[VERIFIED] AWS:** feature pública desde 22-Sep-2026; AWS docs actuales no documentan ese attribute en las páginas A2A revisadas. citeturn695346search6 | Probable wording stale de ElevenLabs. Mantenerlo es razonable porque ElevenLabs dice que es harmless. |
| `applicationId` | **[VERIFIED] AWS setup:** examples usan `YOUR_APPLICATION_ID`. citeturn529894search0 | **[REPORTED BY A SINGLE SOURCE] ElevenLabs sample:** pone `<APPLICATION_ARN>` dentro de `applicationId`. citeturn375441view0 | Debe probarse con el literal `Id` de AppIntegrations si actualmente se usa ARN. |
| Flow mínimo ElevenLabs | **[REPORTED BY A SINGLE SOURCE] ElevenLabs:** logging → Connect assistant → Lex, sin mostrar analytics block. citeturn375441view0 | **[VERIFIED] AWS Connect assistant docs:** voice AI agents requieren real-time conversational analytics. citeturn125169view3 | Seguir el requisito AWS; tu configuración ya lo cumple. |
| SLR repair | **[VERIFIED] AWS Lex:** SLR recibe automáticamente Q permissions; custom role debe administrarlas manualmente. citeturn125169view0 | **[REPORTED BY SINGLE/COMMUNITY SOURCES — OLD, Mar-2025 y re:Post previo a Sep-2026]:** toggle Lex Bot Management reparó un SLR stale. citeturn440350search1turn440350search3 | Útil sólo para diagnóstico histórico; no prueba que tu custom role necesite recreación. |

**[VERIFIED — conclusión causal]** Hay **dos fallos secuenciales distintos** en tus pruebas. El primero es Q-session attachment: hasta que `DescribeContact.WisdomInfo.SessionArn` exista, A2A ni siquiera entra en juego. El segundo aparece únicamente cuando fuerzas una session manual y está en el passthrough runtime: el versioned ORCHESTRATION agent no está siendo resuelto hacia una Connect instance/third-party runtime. El orden de trabajo correcto es, por tanto, **reparar/validar `CreateWisdomSession → UpdateContactData → WisdomInfo` primero; después verificar `connectInstanceArn` sobre el resource versionado; y, si el 502 persiste, tratar account/Region third-party enablement como la hipótesis principal y escalarla a AWS.** citeturn111643view0turn125169view2turn529894search3