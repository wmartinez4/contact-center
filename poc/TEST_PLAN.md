# Plan de pruebas de la PoC (versión exploratoria, actualizada 2026-11-09)

Objetivo: **medir capacidades**, no construir algo definitivo. Datos inventados; destinos solo a teléfonos del equipo. Cada prueba termina en pasa, pasa con solución alterna (con esfuerzo estimado) o falla.

## Preguntas que debe responder

1. ¿Connect rutea como MEI necesita (idioma, estatus especial por encima de la mora)?
2. ¿Una llamada transferida conserva un solo ID y todas sus grabaciones, sin trabajo manual?
3. ¿Qué tal funciona la IA nativa en inglés y español de EE. UU.? ¿Reemplaza el diseñador agéntico el armado a mano?
4. ¿La voz de ElevenLabs (o Deepgram) mejora lo suficiente para justificar su costo y su complejidad?
5. ¿Puede un usuario de oficina vivir en Connect?
6. ¿Qué se pierde en el modelo de dos sistemas (Connect + Zultys), y se puede hacer QA con IA de llamadas que no pasan por Connect?

## Estructura: tres PoC

| PoC | Demos | Pregunta |
|---|---|---|
| **1 Contact center** | D1 ruteo, D2 ID y grabaciones, D3 saliente | 1, 2 |
| **2 Voz con IA** | D4 variantes A, B, C, D | 3, 4 |
| **3 Oficina e híbrido** | D5 oficina, D6 híbrido Zultys | 5, 6 |

Orden sugerido: D1 y D2 primero (núcleo); D5 en paralelo, y **pedir las cuotas el día 1**; D3 y D6 son rápidos; D4 al final.

## Día 1: solicitudes con espera

- Aumento de llamadas concurrentes y de números (defecto: 10 y 10).
- Cuota de campañas salientes (defecto 0), solo si se usará el módulo de campañas.
- Cuota de conexiones con agentes de terceros (defecto 5) si se prueba A2A.
- Habilitación de la integración de ElevenLabs en Connect (disponibilidad limitada).
- Cuota de conectores de analítica de voz externa (defecto 0), solo si se prueba SIPREC.

## D1: ruteo entrante (F1)

| Caso | Esperado | Resultado | Notas |
|---|---|---|---|
| 1 al corriente, EN | Q-Current | | |
| 2 mora 5 días, ES | Q-1-8 | | |
| 3 mora 22 días, EN | Q-16-30 | | |
| 4 mora 47 días, ES | Q-31Plus | | |
| 5 Redemptions con 12 días | **Q-Redemptions** (no Q-9-15) | | |
| 6 EPD, ES | Q-EPD | | |
| 7 desconocido | Q-Fallback | | |

## D2: ID único y grabaciones (F2)

1. Entrante, agente 1 transfiere al agente 2 (otra cola). Repetir con callback y con transferencia a un número externo (desde el flujo y desde el agente).
2. Para cada caso, del registro de contactos: `ContactId`, `InitialContactId`, `PreviousContactId`, `NextContactId`, método de inicio, ubicación de la grabación.
3. Escribir `master_call_id` una sola vez en el primer bloque. Verificar:
   - que llega al registro de **cada** tramo (la documentación dice que sí) y que **ninguna transferencia lo sobrescribe**;
   - que un dato de un solo tramo en *segment attributes* no se mezcla con los demás;
   - `InitialContactId` nulo en el primer tramo, y el valor de `$.InitialContactId` dentro del flujo (no documentado);
   - que la transferencia a número desde el flujo **sigue grabando**, y que la hecha por el agente deja de grabar cuando este cuelga;
   - que cada tramo tiene su grabación localizable por la ubicación del registro (el nombre del archivo puede no coincidir con el ID).
4. Exportar los registros a S3 y reconstruir la cadena completa de una llamada.

Éxito: dada una llamada transferida, se obtiene **sin trabajo manual** la lista ordenada de tramos con sus grabaciones.

## D3: saliente (F4)

- Recordatorio a un teléfono permitido, en inglés y español, con aviso de IA y de grabación.
- Pedir hablar con una persona: debe transferirse.
- Decir "no me llamen más" o la tecla designada: debe registrar la revocación.
- Intento a un número **no** permitido: debe rechazarse.
- Costo real por minuto a Colombia y EE. UU. en la facturación (no hay tarifa verificada a Colombia).

## D4: voz con IA (F3), mismas frases por variante

Variantes: A Nova Sonic (confirmar en consola si hay voz "carlos"), B diseñador agéntico, C Deepgram + ElevenLabs TTS, D A2A modo texto (condicional a habilitación). Medir:

- **Comprensión** del español de EE. UU. y del spanglish (frases preparadas, con montos, fechas y cifras).
- **Latencia percibida**, con la grabación estéreo.
- **Cambio de idioma** a mitad de llamada.
- **Escalada** correcta con resumen, motivo e idioma.
- **Esfuerzo de armado**: horas para B frente al armado manual de A.
- **Escucha a ciegas** de 3 personas.
- Si Nova Sonic se puede desplegar por código o solo por consola.

## D5: oficina

| # | Escenario | Pasa si |
|---|---|---|
| D5.1 | Llamada entre dos usuarios inactivos (aplicación de terceros en Agent Workspace) | Conecta en menos de 5 s, audio en ambos sentidos, aparece en el registro; anotar cómo se factura |
| D5.2 | Transferencia interna (consulta y asistida) entre tres usuarios | Funciona y se mantiene el contacto |
| D5.3 | Menú automático con horarios y un feriado | Rutea por tecla y horario; fuera de horario va al buzón |
| D5.4 | Buzón (Voicemail Express) por usuario y cola | Mensaje por correo con transcripción en menos de 2 min; anotar qué falta |
| D5.5 | Softphone y modo teléfono de escritorio | Softphone estable; en modo escritorio, medir fallas si no contesta |
| D5.6 | Grupo de timbrado (cola con 3 usuarios) | Timbra en la secuencia esperada; documentar si hay "timbrar a todos" |
| D5.7 | 911 **solo con el 933** | Se reproduce el número y la dirección correctos. Nunca llamar al 911 real |
| D5.8 | Cuotas y números | Ocupado al llegar a 10 llamadas; medir plazo del aumento |

Esfuerzo estimado (supuesto): 5 a 8 días de un desarrollador senior, más la espera de cuotas (hasta 3 semanas).

## D6: híbrido (H1)

1. **Transferencia a número externo** (ver D2): qué contexto, ID y grabación sobreviven.
2. **Importación de grabaciones externas:** subir 3 WAV estéreo de 8 kHz inventados a S3, crear el contacto, adjuntar la grabación, correr el análisis de Contact Lens y una evaluación. Medir tiempo, costo y calidad de la transcripción en español.
3. SIPREC desde un SBC: **no se prueba** sin BrevAll. Queda como pregunta (¿Zultys o un SBC emiten SIPREC?).

## Fuera de alcance de esta ronda

iDMS real, volúmenes reales, pruebas de carga, SMS de pago, campañas salientes masivas, captura de tarjeta, tableros de supervisor, llamadas a clientes reales, desvío de números reales.
