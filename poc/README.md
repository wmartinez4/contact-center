# PoC de Amazon Connect para MEI

Prueba de concepto exploratoria. Mide capacidades con datos inventados antes de invertir en algo más complejo.

- Flujos: [../docs/proposal/flujos-poc.md](../docs/proposal/flujos-poc.md)
- Plan de pruebas: [TEST_PLAN.md](TEST_PLAN.md)
- Casos de prueba: [data/personas.json](data/personas.json)

## Alcance: tres PoC, seis demos (propuesta pendiente de aprobación)

- **PoC 1, contact center:** D1 ruteo, D2 ID único y grabaciones, D3 saliente.
- **PoC 2, voz con IA:** D4, variantes Nova Sonic, diseñador agéntico, Deepgram + ElevenLabs y A2A.
- **PoC 3, oficina e híbrido:** D5 oficina (extensiones, buzón, menú, softphone, 911 con el 933) y D6 modelo de dos sistemas (transferencia externa e importación de grabaciones).

La meta es reemplazar todo con Connect como núcleo, pero la oficina se decide con la PoC 3. Detalle en [TEST_PLAN.md](TEST_PLAN.md). Ver [AGENTS.md](../AGENTS.md). Idioma fijo: es-US, no es-MX.

## De dónde viene

Esta PoC **transforma** el demo de renovaciones de `~/olive.business.connect` (archivado el 2026-11-09). Reutiliza su cuenta de AWS de pruebas, su instancia de Connect y su número reclamado. Una copia de la infraestructura de ese demo queda en `infra/baseline-renewal-demo/` como punto de partida y referencia, sin secretos.

## Entorno de AWS

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

- Prefijo `mei-` en todo lo nuevo. No modificar los stacks `connect-demo-02/03/04` hasta decidir su borrado.
- No ejecutar `infra/baseline-renewal-demo/deploy-code.sh`: es del demo anterior y actualizaría el stack viejo.
- Destinos de llamadas salientes: solo teléfonos del equipo, en la lista permitida de la Lambda.
- Sin tarjetas ni datos reales. Los `.env` de los otros proyectos no se copian aquí.
- Lenguaje de las Lambdas nuevas: por definir (Python para el servicio simulado, o .NET para mantener el patrón anterior).

## Próximos pasos

1. Escribir las plantillas de los stacks `mei-` (rutas, backend, Lex, flujos).
2. Revisarlas contigo antes de desplegar nada.
3. Desplegar y ejecutar [TEST_PLAN.md](TEST_PLAN.md).
