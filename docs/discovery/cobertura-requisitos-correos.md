# Cobertura de los correos de MEI (revisión del 10-nov-2026)

Cada requisito o pedido de los correos de Jacob Long (6 y 9 de nov.) y de Mauricio Cuevas, cruzado con lo que tenemos: deck de opciones, guía de demos, preparación de la reunión y pruebas en AWS.

Alcance acordado internamente: **solo el contact center** (telefonía interna de la oficina fuera de alcance, y declarada como exclusión explícita).

**Resultado:** 35 puntos. **5 cubiertos, 20 parciales, 10 sin cubrir.**

Estados: **Cubierto** = está en el deck o la demo. **Parcial** = existe pero incompleto, sin probar o solo como pregunta. **Falta** = no aparece.

## Entregables y reunión

| # | Pedido | Estado | Dónde / qué falta |
|---|---|---|---|
| 1 | Qué reemplazaría Connect y qué componentes adicionales harían falta | Cubierto | Deck, diapositivas 3 a 7. Hay que reescribirlas con alcance solo contact center |
| 2 | **Cómo entregaríamos y daríamos soporte** | **Falta** | Diapositiva nueva: fases, responsabilidades, soporte, capacitación |
| 3 | Costos itemizados de implementación y recurrentes, supuestos de uso | Parcial | Hay precios unitarios (diap. 8); faltan supuestos de uso y el desglose de implementación |
| 4 | SOW: integraciones, migración, pruebas, capacitación, soporte, responsabilidades, tiempos | Parcial | Solo se menciona en "next steps"; falta el esquema del SOW |
| 5 | **Limitaciones, exclusiones y cargos adicionales** | Parcial | Diapositiva nueva de supuestos y exclusiones (incluye la oficina) |
| 6 | Tiempos de la demo a medida, el estimado y el SOW | Cubierto | Diap. 10, "next steps" |
| 7 | Demo basada en los requisitos (correo de Mauricio) | Parcial | Demos 1 a 3 en la cuenta del sandbox; la 2 sin verificar; 4 y 5 sin construir |
| 8 | Es solo una evaluación; proyecto separado del avance del AI QA | Parcial | No está dicho en el deck; añadir una frase |

## Manejo de llamadas

| # | Pedido | Estado | Dónde / qué falta |
|---|---|---|---|
| 9 | Ruteo en inglés y español | Cubierto | Demo 1, funciona con llamada real |
| 10 | Cobranza por mora (0, 1-8, 9-15, 16-30, 31+) y estatus especial con prioridad | Cubierto | Demo 1. OFR/Skip sigue sin definirse |
| 11 | **Ruteo de Ventas y Servicio** (servicio del vehículo, seguros, títulos/payoffs, ventas en concesionarios) | **Falta** | Solo hay una pregunta. Añadir al cuadro de cobertura y, si hay tiempo, un menú de departamentos en el flujo |
| 12 | Transferencias que conserven el contexto | Parcial | Demo 2: no se ha logrado probar la transferencia entre agentes |
| 13 | **Callbacks** que conserven el contexto | **Falta** | No está en ninguna demo. Añadir un callback a la demo 2 |
| 14 | **Reportes de supervisor** (pedido explícito en el correo de Jacob) | **Falta** | Mostrar métricas en tiempo real e históricas, y escucha e intervención |

## Integraciones y AI QA

| # | Pedido | Estado | Dónde / qué falta |
|---|---|---|---|
| 15 | Conectividad con iDMS/DealerSocket | Parcial | Simulada; pregunta abierta sobre su API |
| 16 | Acceso fiable a las grabaciones | Parcial | Entrantes comprobadas (4 llamadas, grabación en S3 localizable) |
| 17 | Metadata completa: agente, cola, **número**, **fecha y hora**, duración, ID, tramos, archivo | Parcial | `chain.py` ya muestra casi todo; falta el número y la hora completa |
| 18 | **Identificación precisa de las llamadas de Cobranza** | **Falta** | Añadir un atributo de departamento (Collections) en el flujo |
| 19 | Soporte a la integración de AI QA existente | Parcial | No sabemos qué proveedor es ni qué campos exige: pregunta 4 |
| 20 | Grabar **todas** las llamadas de Cobranza: entrantes, salientes y transferidas, de cualquier duración | Parcial | Entrantes sí; salientes, transferidas y duraciones muy cortas sin probar |

## Sistemas y pagos

| # | Pedido | Estado | Dónde / qué falta |
|---|---|---|---|
| 21 | Conservar el Text-to-Pay existente | Parcial | Solo pregunta. Aviso: el registro de SMS puede tardar hasta 15 días hábiles |
| 22 | Acceso a un representante para ayuda con pagos | Cubierto | Es una transferencia a un agente |
| 23 | Qué datos de cuenta y cliente se pueden consultar | Parcial | Pregunta 5 (iDMS) |

## Experiencia del cliente

| # | Pedido | Estado | Dónde / qué falta |
|---|---|---|---|
| 24 | Reconocimiento de quien llama | Parcial | La demo usa un caso tecleado, no reconoce al cliente por su número |
| 25 | **Verificación adecuada** | **Falta** | No está en la demo ni en el deck |
| 26 | Conversación bilingüe natural | Parcial | Demos 4 y 5 planeadas, sin construir |
| 27 | Información de cuenta y de pagos | Parcial | Demo 4, planeada |
| 28 | **Acuerdos de pago: reglas de negocio, aprobaciones, actualización de sistemas, confirmación** | **Falta** | Explícitamente fuera de la demo. Debe aparecer en el deck como alcance por definir y como preguntas |

## Línea base de desempeño

| # | Pedido | Estado | Dónde / qué falta |
|---|---|---|---|
| 29 | ~27% de transferencias; reducir las innecesarias | Parcial | Se menciona; falta explicar cómo se medirá en Connect |
| 30 | **Tiempos de espera, abandono, llamadas repetidas, autoservicio y callbacks completados** | **Falta** | Va junto con el reporte de supervisor (14) |
| 31 | Volúmenes, minutos y picos sin validar | Parcial | Pregunta 1 |

## Plataforma y alcance

| # | Pedido | Estado | Dónde / qué falta |
|---|---|---|---|
| 32 | 210 usuarios, revisión de usuarios activos | Parcial | Con el alcance nuevo, importan los ~85 del contact center |
| 33 | **Áreas "Corporate" y 123 usuarios estándar** | **Falta** | Nueva: declarar la exclusión de la oficina y **preguntarle a MEI** si esperan moverlos |
| 34 | Zultys 19 / AI Receptionist como alternativa en evaluación | Parcial | Existía como "ruta D" en el deck viejo; mantener una comparación breve |
| 35 | **Migración**: portabilidad de números, corte, convivencia con Zultys, capacitación | **Falta** | Va dentro de la diapositiva de entrega |

## Acciones, de más a menos importantes

1. **Diapositiva de entrega, soporte y migración** (puntos 2, 4, 35). Es lo que Jacob pidió expresamente y hoy no existe.
2. **Diapositiva de supuestos, exclusiones y cargos** (puntos 3, 5, 33), con la exclusión de la oficina y la pregunta a MEI.
3. **Reporte de supervisor y métricas de desempeño** (14, 29, 30). Lo trae Connect de fábrica: una diapositiva y una demostración corta de las métricas.
4. **Ventas y Servicio** (11). Filas nuevas en el cuadro de cobertura y, si hay tiempo, un menú de departamentos en el flujo.
5. **Callback en la demo 2** (13) y **atributo de departamento** (18).
6. **Ampliar `chain.py`** con número y hora (17).
7. **Verificación y acuerdos de pago** (25, 28): alcance por definir y preguntas, sin demo.
8. Frase sobre "evaluación solamente, separado del AI QA" (8).
