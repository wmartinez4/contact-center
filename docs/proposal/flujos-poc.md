# Flujos de la PoC (versión exploratoria, actualizada 2026-11-09)

Cuatro flujos de contact center más dos escenarios híbridos, con datos inventados (ver `poc/data/personas.json`). Todo lo marcado **(por confirmar)** es una regla de negocio de MEI que se aclara en el descubrimiento. Idioma fijo: **es-US** (no es-MX) para bot, voz, analítica y evaluaciones.

## F1: Entrante, ruteo por idioma, estatus y mora

```mermaid
flowchart TD
    A[Llamada entrante] --> B[Marcar master_call_id]
    B --> C{Idioma: 1 inglés, 2 español}
    C --> D[Elegir caso de prueba 1 a 7 con el teclado]
    D --> E[Consulta de cuenta - servicio simulado]
    E -->|No existe| Z[Q-Fallback]
    E -->|Existe| F{¿Estatus especial?}
    F -->|Redemptions| R[Q-Redemptions]
    F -->|EPD| P[Q-EPD]
    F -->|OFR/Skip por confirmar| S[Q-OFR-Skip]
    F -->|Ninguno| G{Días de mora}
    G -->|0| Q0[Q-Current]
    G -->|1 a 8| Q1[Q-1-8]
    G -->|9 a 15| Q2[Q-9-15]
    G -->|16 a 30| Q3[Q-16-30]
    G -->|31 o más| Q4[Q-31Plus]
```

Regla clave: **el estatus especial se evalúa antes que la mora**. La consulta devuelve una sola respuesta con cola, prioridad e idioma, para que el flujo no tenga lógica de negocio.

## F2: Transferencia, callback y cadena de ID

```mermaid
flowchart TD
    A[Agente 1 atiende] --> B{¿Qué necesita el cliente?}
    B -->|Pasar a otro equipo| C[Transferir a otra cola con contexto]
    B -->|Nadie disponible| D[Callback en cola]
    B -->|Transferir a número externo| X[Transferir a teléfono externo]
    C --> E[Agente 2 recibe llamada con resumen]
    D --> F[Connect devuelve la llamada al cliente]
    E --> G[Prueba: master_call_id, tramos, grabaciones]
    F --> G
    X --> G
```

Lo que ya dice la documentación (hay que **confirmarlo**, no asumirlo):

- Los atributos de usuario se comparten entre todos los contactos con el mismo `InitialContactId`, y **una transferencia puede sobrescribirlos**. `master_call_id` se escribe una sola vez; los datos de un tramo van en *segment attributes*.
- En el registro de contacto, `InitialContactId` es nulo en el primer tramo: el ID maestro es `InitialContactId` si existe, si no `ContactId`.
- "Transferir a número" desde un flujo **sigue grabando**. La transferencia externa hecha por el agente deja de grabar cuando el agente cuelga.
- Máximo 2 grabaciones por contacto.

## F3: Entrante con IA (consulta y escalada)

```mermaid
flowchart TD
    A[Llamada entrante] --> B[Saludo bilingüe]
    B --> C[IA identifica al cliente - servicio simulado]
    C --> D[IA informa saldo y fecha de pago]
    D --> E{¿Resuelto?}
    E -->|Sí| F[Fin y registro del resultado]
    E -->|Quiere persona o IA no entiende| G[Escalar con resumen, motivo e idioma]
    G --> H[Cola según F1]
```

Variantes de la misma conversación, mismo guion y mismos casos:

| Variante | Oído | Cerebro | Voz | Estado |
|---|---|---|---|---|
| A | Nova Sonic | Nova Sonic | Nova Sonic (confirmar en consola si es Nova 2 y si aparece la voz "carlos") | Base |
| B | Agentic CX designer | Pasos fijos + IA | Voces de Connect | Opcional: mide si reemplaza el armado a mano |
| C | Deepgram | Connect | ElevenLabs (TTS dentro de Connect) | Requiere token de ElevenLabs (`us`) |
| D | Connect (STT) | Agente externo por A2A, modo texto | Connect o ElevenLabs | Solo si AWS y ElevenLabs lo habilitan; tope de 5 conexiones |

La IA solo informa y escala. **No captura tarjeta ni cierra pagos.** El aviso de que habla una IA y de que la llamada se graba va al inicio, en ambos idiomas.

## F4: Saliente, recordatorio a un teléfono propio

```mermaid
flowchart TD
    A[Disparo manual por Lambda] --> B{¿Destino en la lista permitida?}
    B -->|No| X[Rechazar]
    B -->|Sí| C[Controles: consentimiento, no llamar, intentos, horario]
    C --> D[Llamada saliente]
    D --> E{¿Contesta una persona?}
    E -->|Sí| F[Recordatorio de pago bilingüe con aviso de IA]
    E -->|Contestadora| G[Registrar resultado]
    F -->|Pide hablar con persona| H[Transferir a agente]
    F -->|Dice dejar de recibir llamadas| R[Registrar revocación]
    F -->|Resuelto| I[Registrar resultado]
```

Solo a teléfonos del equipo, con lista de destinos permitidos. Nunca a clientes reales. Se agrega la **revocación de consentimiento** por voz o tecla, por la orden de la FCC vigente desde el 2026-11-25 (revisión legal pendiente). El SMS de pago queda fuera de esta ronda.

## H1: Híbrido, llamada que sigue en Zultys

Simula el modelo de dos sistemas, con un teléfono normal en el papel de Zultys. Dos pruebas:

1. **Transferencia a un número externo**, desde el flujo y desde el agente: qué se conserva (ID, contexto, grabación) y qué se pierde.
2. **Importación de grabaciones externas** (WAV estéreo de 8 kHz en S3 → contacto → análisis de Contact Lens): ¿se puede calificar con IA una llamada que nunca pasó por Connect? Si funciona, el QA de MEI no depende de migrar todo. SIPREC desde un SBC queda como pregunta para BrevAll.

## Reglas de negocio por confirmar

- Qué significa **OFR** y si hay más estatus especiales.
- Si Redemptions, OFR/Skip y EPD tienen colas y agentes distintos.
- Qué se le dice al cliente en cada tramo, y qué se puede informar tras verificar su identidad.
- Horarios de atención y de llamadas salientes.
