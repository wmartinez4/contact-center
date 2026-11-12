# Resumen ejecutivo: ¿se puede migrar todo MEI a Amazon Connect?

**Actualizado el 9 de noviembre de 2026, tras verificar los supuestos contra fuentes actuales de AWS, ElevenLabs, Zultys y la FCC. Basado en documentación pública; todavía no hay pruebas completas ni datos reales de MEI.**

## Conclusión

**Amazon Connect puede reemplazar el contact center de MEI (unos 85 agentes). No reemplaza por sí solo el teléfono de oficina (unos 125 usuarios).** En 2026 AWS no agregó extensiones, buzón por persona, teléfonos de escritorio SIP, paging, park ni fax, y no tiene un producto de telefonía de oficina (Chime Business Calling terminó el 20 de febrero de 2026). No encontré ningún caso independiente de una oficina de este tamaño operando solo en Connect.

## Expectativa frente a la realidad

| Se esperaba | Lo que encontré |
|---|---|
| Connect reemplaza todo el sistema telefónico | Reemplaza bien el contact center. La oficina necesita otra plataforma o una capa a medida |
| Un solo sistema | Lo más realista hoy son dos: Connect para cobranza y ventas, y Zultys o un UCaaS para la oficina |
| Migrar rápido | Portar números toma de 2 a 4 semanas; la migración completa se estima en 3 a 5 meses |

## Lo que sí se puede

- Ruteo por idioma, estatus especial y días de mora; transferencias, callbacks y supervisor.
- Grabar todas las llamadas con un registro por tramo. El identificador único **sí se puede resolver con la documentación actual**: los atributos propios se comparten entre los tramos de una misma llamada. Hay que protegerlos de sobrescrituras.
- IA de voz en inglés y español dentro de Connect (usar español de EE. UU., no el de México). ElevenLabs y Deepgram se integran, aunque la integración de ElevenLabs sigue en "disponibilidad limitada".
- QA con IA nativo (Contact Lens), incluso **sobre llamadas que sigan en Zultys** mediante importación de grabaciones (julio de 2026).
- Llamadas salientes. Ya se probó una real a Colombia y funcionó.

## Lo que Connect no trae (oficina)

Marcar por extensión, buzón de voz por persona, teléfonos SIP, paging, park/pickup, fax y analógicos. Se construye, se compra a un socio o se deja en otro sistema. El 911 con ubicación por oficina requiere solución propia.

## Costos y riesgos

- Conectar Connect con una PBX externa: **$100 por conector al día (~$3,000 al mes) más $0.032 por minuto**. Cifra oficial vigente.
- Por defecto: 10 llamadas simultáneas, 10 números y campañas salientes en 0. Subirlos puede tomar semanas.
- La integración de agentes externos (A2A) admite 5 conexiones simultáneas por instancia.
- Nueva regla de la FCC sobre revocación de consentimiento, vigente desde el **25 de noviembre de 2026**; requiere revisión legal.
- Los costos totales siguen siendo ilustrativos: no hay volúmenes de MEI.

## Lo que no sabemos

- Si iDMS/DealerSocket tiene interfaz. Sin ella, el ruteo por mora no es posible en ninguna plataforma.
- Qué significa OFR y si hay más estatus especiales.
- Volúmenes, números, equipos y vencimiento de contratos.
- Calidad real del español en cada opción de IA. No hay comparaciones independientes.
- Qué incluye Zultys 19.0.20 (salió el 13 de octubre) y si BrevAll sigue siendo su socio: su sitio ya no lo menciona.

## Recomendación

**Por fases, sin prometer el reemplazo total antes de probarlo.**

1. **Fase 1:** contact center en Connect, con IA de voz opcional. Es donde la evidencia es fuerte y está el dolor del cliente.
2. **Fase 2:** prueba corta de oficina para decidir si esos usuarios se quedan en Zultys, pasan a un UCaaS o van a Connect.
3. "Todo en Connect" solo es creíble si la oficina usa muy poco lo que Connect no trae, MEI acepta mantener una capa a medida, AWS aprueba los límites y el costo a tres años es menor que las licencias por usuario.

## Qué se necesita de MEI y BrevAll

Contratos y vencimientos; inventario de números y equipos; acceso a la interfaz de iDMS; qué se puede exportar de Zultys; si Zultys o un SBC pueden emitir SIPREC.

*Fuentes y detalle: `docs/research/verificacion-supuestos-2026-11-09.md`. Nada de esto es asesoría legal.*
