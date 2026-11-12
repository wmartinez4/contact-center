# Modelo de costos del contact center en Amazon Connect (borrador, 10-nov-2026)

Precios de lista leídos en las páginas oficiales de AWS el 2026-11-10 y **re-verificados el mismo día por la tarde** en `aws.amazon.com/products/connect/customer/pricing/` (la antigua `/connect/pricing/` redirige ahí) y su apéndice `/appendix/`. Sin cambios en las cifras. **Hecho** = leído en la página. **[S]** = sale de un resumen y no está verificado. Sin volúmenes de MEI, todo lo que sigue es ilustrativo, no una cotización.

## 1. Cómo factura Connect (reglas que cambian el cálculo)

- **No hay licencia por usuario.** La página principal dice "sin licencias por asiento". Se paga por uso.
- **El servicio de voz se factura por segundo, con un mínimo de 10 segundos, sobre toda la llamada activa**: el flujo (IVR), la espera en cola y el tiempo con el agente. No es solo el tiempo de conversación. Un ejemplo oficial factura 10 minutos = 3 de cola + 2 con el agente + 5 de una transferencia saliente.
- **La telefonía se factura aparte**, por segundo y con **mínimo de 60 segundos**. En llamadas salientes de cobranza con muchos intentos cortos, ese mínimo pesa.
- **Sin mínimos ni contratos de plazo**: "no minimums, no long-term contracts". Un descuento por volumen tendría que negociarse con AWS.

## 2. Precios de lista

| Concepto | Precio | Estado |
|---|---|---|
| Voz, Connect Customer (incluye Nova Sonic, voces generativas, Lex, analítica y evaluaciones) | **$0.038/min** | Hecho |
| Voz, Connect Customer Basic | **$0.018/min** | Hecho |
| Basic: analítica conversacional y resúmenes | $0.015/min (hasta 5 M min), $0.0125 después | Hecho |
| Basic: evaluaciones de desempeño | $12 por agente al mes | Hecho |
| Basic: pronóstico y planificación | $27 por agente al mes | Hecho |
| Basic: grabación de pantalla | $0.006/min | Hecho |
| Basic **no incluye** | Nova Sonic, voces de terceros, estimación de espera, devolución de llamada al cliente, métricas personalizadas | Hecho |
| Número local (DID) | $0.03/día | Hecho (ejemplos del apéndice) |
| Telefonía entrante / saliente a EE. UU. | $0.0022 / $0.0048 por min | Hecho (ejemplos del apéndice; mínimo de 60 s) |
| Llamada desde la web o la app del cliente (no aplica a teléfonos) | $0.010/min | Hecho |
| Número gratuito (800) | $0.06/día | **[S]** |
| Telefonía de números gratuitos, por minuto | **no encontrado** (la tabla por país del apéndice no se pudo leer) | Verificar en el calculador de AWS |
| Campañas salientes de voz, Connect Customer | $0.045/min (reemplaza a $0.038) | Hecho |
| SMS, Connect Customer / Basic | $0.014 / $0.010 por mensaje | Hecho |
| Tarifa del operador para SMS en EE. UU. (10DLC) | ~$0.0088 por mensaje saliente | **[S]** |
| Agentes de IA de terceros (A2A): voz / texto | $0.01/min / $0.001 por mensaje | Hecho |
| Conector de voz externa | $0.032/min + $100 por conector al día | Hecho (el resumen dice $0.012, discrepa) |
| Almacenamiento de grabaciones | **no tiene precio en esas páginas**: se paga como S3 estándar | Ver nota |
| Plan de soporte de AWS | **no encontrado** | Preguntar |

Medición propia: una grabación de prueba de 187 segundos pesó 1.6 MB, es decir **~0.5 MB por minuto**. Con 300,000 minutos al mes serían unos 150 GB y, a tarifa estándar de S3, **menos de $5 al mes**. No es un costo relevante.

## 3. Fórmula y escenarios

```
Costo mensual ≈ minutos facturados × (tarifa de voz + tarifa de telefonía) + números + mensajes
```

Por cada **100,000 minutos facturados** (voz Connect Customer + telefonía entrante o saliente): **$4,020 a $4,280**. Con Basic y analítica, entre $3,520 y $3,780; con Basic sin analítica, entre $2,020 y $2,280, pero sin Nova Sonic ni las funciones incluidas.

Escenarios con Connect Customer, telefonía mixta (tarifa total ≈ $0.0415/min) y **horas de contacto por agente y día como supuesto** (20 días al mes). Recuerda que los minutos facturados incluyen IVR, cola y transferencias, así que superan el tiempo de conversación:

| Agentes | 2 h/día | 3 h/día | 4 h/día |
|---|---|---|---|
| 85 | $8,466 al mes | $12,699 | $16,932 |
| 210 | $20,916 al mes | $31,374 | $41,832 |
| **Por agente** | **~$100 al mes** | **~$149** | **~$199** |

Para comparar con lo que MEI paga hoy, la cifra útil es **el costo por agente al mes**, que no depende de cuántos agentes sean: sale de las horas de contacto que se asuman.

## 3b. Precio por nivel: flujo normal, complementos de análisis y flujo con IA (2026-11-10)

Releído en el apéndice de precios el 2026-11-10. **Regla clave (hecho):** "Connect Customer charges apply to all channel usage in your account". El nivel se elige **por cuenta**, no por flujo: no se puede pagar Basic en unas llamadas y Customer en otras dentro de la misma cuenta.

| Nivel | Qué incluye | Voz | + telefonía mixta | Por agente al mes (2 / 3 / 4 h de contacto al día) |
|---|---|---|---|---|
| **1. Flujo normal** (Basic) | IVR, ruteo por mora y estatus, colas, transferencias, devolución de llamada en cola*, grabación, reportes | $0.018/min | $0.0215/min | ~$52 / ~$77 / ~$103 |
| **2. Flujo normal + complementos de análisis** (Basic + analítica conversacional) | Lo anterior + transcripción, **análisis de sentimiento**, **resumen de la llamada con IA**, **categorías automáticas**, búsqueda por palabras | $0.018 + $0.015 = $0.033/min | $0.0365/min | ~$88 / ~$131 / ~$175 |
| **3. Todo incluido** (Connect Customer) | Lo anterior + **agente de IA por voz (Nova Sonic)**, voces generativas, evaluaciones automáticas, estimación de espera | $0.038/min | $0.0415/min | ~$100 / ~$149 / ~$199 |

Supuestos: 20 días al mes; telefonía mixta entrante/saliente de EE. UU. ≈ $0.0035/min; los minutos facturados incluyen IVR, cola y transferencias. Precios de lista, sin volúmenes de MEI.

\* El apéndice lista "devolución de llamada al cliente" como no incluida en Basic: confirmar si se refiere a la devolución desde la cola que usa la demo.

**Lecturas para la reunión:**
- **El flujo con IA no es un cargo aparte en el nivel 3**: cada minuto atendido por el agente de IA cuesta lo mismo que cualquier minuto de voz ($0.038 + telefonía). Su beneficio está en el tiempo de agente que ahorra, no en un precio menor de Connect.
- **Pasar del nivel 2 al 3 cuesta ~$0.005/min** más (≈ $18 por agente al mes con 3 h diarias) y suma la IA conversacional y las evaluaciones.
- **El análisis de sentimiento** viene dentro de la analítica conversacional (Contact Lens): se activa en el mismo bloque del flujo que la transcripción. La página de precios no le pone un precio propio (no encontrado como línea separada).
- **El resumen con IA** está en la misma línea de precio que la analítica ("Conversational analytics & post-contact summaries"). Soporta español de EE. UU. (es-US), según la tabla de idiomas de AWS leída el 2026-11-10; en la demo está activo en los dos idiomas. Si la llamada tiene muy poca conversación, AWS no genera el resumen.
- **Las categorías automáticas** (reglas de Contact Lens con frases en inglés y español: promesa de pago, arreglo de pago, dificultad financiera, disputa, devolución de llamada y aviso de cobranza dado) forman parte de la analítica conversacional: no encontré una línea de precio aparte.
- Evaluaciones de desempeño en Basic: $12 por agente al mes (incluidas en Customer).

## 3c. Costo de la plataforma frente a precio sugerido para MEI (BORRADOR para revisión interna, 2026-11-10)

Son dos diapositivas seguidas del deck (10 y 11). La primera es nuestro costo en AWS (sección 3b, sin cambios). La segunda es lo que cobraríamos. **Es una propuesta para ajustar, no un precio final.** Todo supuesto de abajo es nuestro, no un dato de MEI.

**Precio recurrente por agente al mes** = costo de AWS ÷ 0,70 (margen bruto de 30 % sobre el precio), redondeado a $5:

| Nivel | Costo AWS a 3 h | Precio sugerido a 3 h | Rango sugerido a 2 y 4 h |
|---|---|---|---|
| 1. Flujo normal | ~$77 | ~$110 | ~$75 a ~$145 |
| 2. Flujo normal + análisis | ~$131 | ~$185 | ~$125 a ~$250 |
| 3. Todo incluido | ~$149 | ~$215 | ~$145 a ~$285 |

- **Por qué 30 %:** los márgenes típicos de un servicio administrado sobre consumo de nube se mueven más o menos entre 25 % y 40 % (regla general, no una fuente). El consumo es casi un traspaso con poca diferenciación y el valor del servicio va en la cuota administrada y la implementación, así que elegí un punto medio-bajo. Con 25 % saldría ~$105 / ~$175 / ~$200 a 3 h; con 35 %, ~$120 / ~$200 / ~$230.
- **Cuota administrada:** propongo una cuota mensual fija y separada (monitoreo, cambios a flujos, colas y mensajes, administración de usuarios, reportes, horas de soporte con tiempos de respuesta). **No hay base para el monto ni las horas**: se fija después del descubrimiento. Si MEI prefiere un solo precio, se integra al precio por agente con un mínimo de agentes.
- **Implementación (SOW, pago único):** descubrimiento, iDMS, flujos y ruteo, agente de IA, portabilidad de números, pruebas, capacitación y operación en paralelo con Zultys. Duración de planificación: 3 a 5 meses. **Sin horas ni precio hasta tener acceso a iDMS, número de agentes y reglas.**
- **No incluido o traspasado:** minutos de números gratuitos (tarifa sin confirmar) y telefonía fuera de la mezcla supuesta; SMS para enlaces de pago ($0.014 + tarifa del operador); voz de terceros (ElevenLabs); procesador de pagos, trabajo de PCI y cargos de iDMS/DealerSocket; plan de soporte de AWS.
- **Condiciones comerciales (propuestas):** plazo mínimo de 12 meses para el servicio administrado; revisión de precios con volúmenes reales (unos 90 días tras el arranque); sin mínimo de agentes para el consumo (AWS no lo exige) y un piso solo para la cuota; precio por agente que incluye el consumo en nuestra cuenta de AWS, o como alternativa la cuenta de AWS de MEI con el consumo facturado por AWS al costo más nuestra cuota; un descuento por volumen de AWS se comparte por acuerdo (p. ej., se traspasa íntegro si la cuenta es de MEI).
- **Gancho de comparación:** el número que MEI puede comparar es el precio por agente al mes frente a lo que paga hoy por Zultys + BrevAll + operadores (datos por pedir: sección 6).

## 3d. Costo de operación y cuota de soporte sugerida (BORRADOR interno, 2026-11-10)

Diapositiva 12 del deck (solo interna). **Sugerencia preparada con investigación asistida por IA sobre datos públicos; tarifas, horas y cuota son estimaciones por validar, no una cotización.** Soporte estándar en horario de oficina; la cuota es **fija y no depende de la cantidad de agentes**; las horas se estimaron para el alcance de la demo (unas 10 colas, dos idiomas, un flujo de IA y una integración con iDMS).

| Línea | Base | Horas al mes | Costo por hora | Costo mensual |
|---|---|---|---|---|
| Soporte y administración | Tickets, usuarios, colas, mensajes, reportes | 40 | $70 | $2,800 |
| Ingeniería y DevOps | Cambios a flujos y Lambdas, despliegues, alarmas | 24 | $90 | $2,160 |
| Gestión del servicio y cumplimiento | Revisión mensual, aporte a PCI y TCPA | 8 | $90 | $720 |
| Herramientas | Tickets, monitoreo, alertas | - | - | $1,000 |
| **Costo de operación** | | **72** | | **$6,680** |
| **Cuota mensual sugerida** | Costo ÷ 0,70 (30 % de margen), a $500 | | | **~$9,500** al mes, fija |

- **Soporte estándar (propuesta):** lunes a viernes, 8:00 a 17:00 CT. Respuesta: servicio caído 1 hora; problema mayor 4 horas hábiles; resto, siguiente día hábil. Incluye monitoreo, cambios a flujos, colas y mensajes, administración de usuarios, reportes y revisión mensual. Fuera de horario y 24/7: aparte, por hora (la única fuente encontrada pone el trabajo fuera de horario de un MSP en $250 a $500 por hora).
- **Tarifas (costo cargado):** soporte, ~$48 por hora de salario medio de administradores de sistemas según BLS (dato de mayo de 2023 en un resultado de búsqueda; no pude abrir la página) ÷ 0,70, porque los salarios son ~70 % del costo laboral del empleador (BLS 2025) = ~$69, redondeado a $70. Ingeniería: mediana nacional de ~$65 por hora para desarrolladores (O*NET; año sin confirmar), cargada ~$93, y ofertas de contratistas de Amazon Connect de $70 a $85 por hora; uso $90. Facturadas a costo ÷ 0,70 salen ~$100 y ~$130 por hora, por debajo de los $125 a $250 de un socio de AWS y de los MSP.
- **Horas: no hay referencia publicada.** Busqué una razón de agentes por administrador de plataforma y no existe (las publicadas son 8 a 15 agentes por supervisor y ~1 evaluador de calidad por 33 agentes). Los socios de Connect describen el mismo alcance (altas, bajas y cambios, soporte, revisiones, monitoreo) pero cotizan caso por caso. **72 horas al mes (~0,45 de una persona) es estimación nuestra**: validar con los tickets de los primeros 90 días.
- **Se traspasa al costo:** plan de soporte de AWS (opcional, recomendable en producción). Business Support+ cuesta lo mayor entre $29 al mes o 9 % de los cargos mensuales de AWS hasta $10K, 7 % de $10K a $80K, 5 % de $80K a $250K y 3 % por encima. Con 85 agentes y 3 h al día (supuesto solo para este cálculo): ~$590 (nivel 1), ~$980 (nivel 2) o ~$1,090 (nivel 3) al mes. Otros servicios de AWS fuera del precio por minuto (Lex, Lambda, Customer Profiles, almacenamiento, claves, monitoreo) **no están medidos** salvo las grabaciones (menos de $5 al mes): medirlos en Cost Explorer de la cuenta de la demo antes de cotizar.
- **Por qué cuota fija y no por agente:** no se sabe cuántos agentes atienden llamadas (85 o hasta 210) y la mayor parte del trabajo no crece con la plantilla: monitoreo, despliegues, cambios y revisiones siguen el alcance. Con uso por agente y servicio como cuota fija, MEI compara cada parte con lo que paga hoy (Zultys y operadores por el uso, BrevAll por el servicio).
- **Comprobación:** $100 y $130 por hora facturadas están por debajo de los $125 a $250 de socios y MSP. (Los planes de TI administrada por usuario, de $110 a $185 al mes, son de TI de escritorio y no son comparables con una cuota fija.)
- **Escalamiento:** con volúmenes conocidos, fijar la cuota por bandas de agentes (por ejemplo hasta 100 y de 101 a 250), con un piso, y revisarla tras 90 días de tickets reales. Reestimar las horas si crece el alcance (más colas, un segundo flujo de IA, más integraciones).

**Referencias** (leídas por búsqueda el 2026-11-10; las guías de proveedores son marketing, tomarlas como orden de magnitud):
- Precios del plan de soporte de AWS: <https://aws.amazon.com/premiumsupport/pricing>
- BLS, administradores de redes y sistemas (15-1244): <https://www.bls.gov/OES/current/oes151244.htm>
- O*NET, salarios nacionales de desarrolladores (15-1252): <https://www.onetonline.org/link/localwages/15-1252.00>
- BLS, costos laborales del empleador (salarios ~70 %): <https://www.bls.gov/news.release/ecec.htm>
- Ofertas de contratistas de Amazon Connect: <https://jobs.insightglobal.com/find_a_job/maryland/job-427098>, <https://www.careerbuilder.com/job-details/aws-connect-specialist-dmv-area-consultants-reqd-washington-dc--e152fd75-5f7e-4904-b6a4-b7f0b45c8278>
- Tarifa de socio, $125 a $250 por hora (AWS IQ): <https://iq.aws.amazon.com/e/aspentgi>
- Guías de precios de MSP: <https://www.n-able.com/blog/msp-pricing-guide>, <https://arphost.com/managed-it-support-pricing/>, <https://serenit.pages.dev/it-support-cost>, <https://www.flamingo.run/blog/msp-pricing-models>, <https://www.kaseya.com/resource/msp-pricing-managed-it-services-pricing/>
- Alcance de servicios administrados de Connect (sin precios publicados): <https://usan.com/managed-services-amazon-connect>, <https://www.ventrica.co.uk/what-is-an-amazon-connect-msp/>
- Razones de personal (supervisores, calidad): <https://www.icmi.com/resources/2012/Staff-to-Supervisor-Ratio>

## 4. Lo que este modelo no incluye

- **Implementación** (nuestro trabajo): integraciones, pruebas, migración, capacitación. Falta nuestra tarifa y el esfuerzo.
- **Portabilidad de números** y su costo.
- **Operación en paralelo** con Zultys durante la transición.
- **Costos de terceros**: voz de ElevenLabs o Deepgram, soporte de AWS.
- **Pagos**: comisiones del procesador de pagos de MEI, servicio de Text-to-Pay actual y, si se toman pagos por teléfono, el trabajo de PCI. Nada de esto lo cobra Connect; el SMS para enviar enlaces de pago sí ($0.014 por mensaje más la tarifa del operador).
- **iDMS**: cualquier cargo de DealerSocket por usar su interfaz.
- **Equipos**: diademas; Connect no requiere teléfonos de escritorio.

## 5. Dudas y contradicciones en las páginas de AWS

1. Conector de voz externa: $0.032/min según el texto leído, $0.012 según un resumen. Solo importa si hubiera que conectarlo a la PBX.
2. ~~Los ejemplos de Basic usaban $0.038.~~ Resuelto el 2026-11-10: los ejemplos de telefonía del apéndice usan $0.018 para Basic y los de Connect Customer usan $0.038.
3. "Sin licencias por asiento" frente a $12 y $27 por agente al mes en Basic. Probablemente son de uso, pero la página no lo aclara.
4. Telefonía de números gratuitos por minuto: no la encontré. Los números 800 son habituales en cobranza, así que hay que obtenerla antes de cotizar.
5. Tareas, guías y correo muestran cifras distintas entre lo leído y el resumen. No afectan a este proyecto.

## 6. Datos que hay que conseguir de MEI para comparar costos

Para saber si Connect ahorra, hay que conocer lo que se paga hoy, **solo de lo que se movería**:

- **Zultys**: costo por licencia (estándar, contact center y premium), cuántas de cada una y el costo de mantenimiento o soporte anual. La cotización del upgrade a la versión 19.
- **BrevAll**: tarifa de soporte o servicios administrados, y qué cubre.
- **Operadores de telefonía**: costo mensual, minutos, canales y números (incluidos los gratuitos).
- **Fechas de vencimiento** de todos los contratos.
- **Volúmenes**: minutos al mes entrantes y salientes, picos, agentes por turno y duración media de llamada.

## 7. Estado de la diapositiva de costos del deck (2026-11-10)

Aplicado en `MEI_Amazon_Connect_Options_DRAFT.pptx`. Desde la tarde del 2026-11-10 hay **dos diapositivas de precios**: la 10 (costo de la plataforma en AWS, los tres niveles de la sección 3b) y la 11 (precio sugerido, sección 3c, borrador). La 12 (sección 3d) es el costo de operación y la cuota de soporte sugerida. Las tres son solo internas. La 10 conserva lo siguiente:

- Voz y telefonía por segundo y sobre toda la llamada (IVR, cola y agente), con mínimos de 10 y 60 segundos.
- Basic etiquetado "sin IA" y, en las notas, lo que no incluye (Nova Sonic, voces generativas y de terceros, estimación de espera, devolución de llamada).
- Sin el conector de PBX.
- Telefonía de números gratuitos marcada como por confirmar.
- Costo por agente al mes: ~$100, ~$149 y ~$199 (2, 3 y 4 h de contacto al día; 20 días; $0.0415/min).
- SMS reetiquetado como envío de enlaces de pago. La analítica (transcripción, sentimiento, resumen, categorías) aparece solo como complemento del nivel 2, sin sección de QA con IA.

## 8. Sobre los 210 usuarios

Si todos los 210 usuarios son del contact center, el número de agentes a considerar pasa de ~85 a hasta 210. En precio, eso **no cambia la tarifa por minuto**, pero sí:
- los **escenarios de arriba** (el costo total se multiplica);
- las **cuotas**: por defecto 10 llamadas simultáneas, y con cientos de agentes hay que pedir un aumento grande con tiempo;
- los **complementos por agente**, si se usan (evaluaciones, pronóstico);
- el esfuerzo de **migración y capacitación**.

Pregunta propuesta para MEI, en inglés:

> "Of the 210 planned users (123 standard, 85 contact-center, 2 premium), how many handle customer calls in queues or make collection calls, and what do the 123 standard users do? We want to size Amazon Connect for everyone who takes or makes customer calls, and leave out anyone who only uses internal office phone features."
