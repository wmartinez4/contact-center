# Preparación: reunión de descubrimiento con MEI (miércoles 11 de noviembre de 2026)

**Hora:** 10:30 a 11:30 CT (el correo de Jacob del 6 de nov. decía "hasta el mediodía"; el del 9 de nov. dice 11:30). **Formato:** presencial en Dallas; Willian participa en remoto.
**Por parte nuestra:** Mauricio Cuevas, Mauricio Ordóñez (CTO, presencial), Willian (Sr. Engineer lead, remoto).
**Por parte de MEI:** Jacob Long (VP Finance), Jose (autorizó explorar la solución).

## Lo que esperan (del correo)

- Nuestra evaluación de **qué reemplazaría Amazon Connect**, **qué componentes adicionales harían falta** y **cómo entregaríamos y daríamos soporte**.
- Después de la reunión: demostración a medida, estimado con costos itemizados y SOW propuesto (integraciones, migración, pruebas, capacitación, soporte, responsabilidades, tiempos), con limitaciones, exclusiones y cargos adicionales identificados.
- Es una evaluación. Cualquier implementación requiere aprobación aparte. Se maneja como proyecto separado del avance del QA con IA.
- Expectativa de Mauricio Cuevas: salir de la reunión con **todo lo necesario para armar propuesta y SOW**.

## Tres cosas por aclarar al inicio

1. **¿La demostración es en esta reunión o después?** Jacob la describe como un paso posterior a la reunión ("tailored demonstration"). Mauricio Cuevas escribió "we'll present a demonstration". Hoy no hay nada desplegado en AWS que mostrar, salvo una llamada saliente probada. Si esperan demo mañana, hay que saberlo hoy.
2. **¿Qué es el "AI QA existente"?** Jacob dice "como saben por nuestro trabajo juntos" y "soporte para nuestra integración de QA con IA existente". Hay que saber qué proveedor es, cómo recibe hoy las grabaciones y qué campos de metadata exige. Es el requisito que más les duele y el que mejor podemos resolver.
3. **¿Qué significa "reemplazar"?** Solo el contact center (~85 agentes) o también la oficina (~125 usuarios). La respuesta cambia todo el SOW.

## Nuestra postura (versión corta)

- Connect puede reemplazar el contact center de cobranza, con ruteo por idioma, estatus especial y mora, transferencias, callbacks, grabación de todos los tramos y QA con IA.
- Connect **no reemplaza por sí solo** la telefonía de oficina (extensiones, buzón por persona, teléfonos de escritorio, paging, fax, estacionar llamadas). Hay tres caminos: dejarla en Zultys, pasarla a un UCaaS, o construir una capa a medida.
- Recomendación: **por fases**. Fase 1 contact center y QA; fase 2 decisión de oficina tras una prueba corta.
- Sin volúmenes, números, contratos ni interfaz de iDMS **no se puede dar un precio cerrado**. Podemos dar rangos con supuestos explícitos.

## Preguntas, por prioridad

### A. Para poder cotizar (las indispensables)

1. Volúmenes: llamadas por día y por hora pico, minutos, agentes simultáneos, % entrantes y salientes, % en español, tiempo de espera y abandono actuales.
2. Cómo se midió el ~27% de transferencias, y qué cuenta como transferencia.
3. Usuarios activos reales (la revisión sigue abierta) y cuántos usan funciones de oficina avanzadas (teléfono de escritorio, fax, paging, park, buzón).
4. Inventario de números (DID, gratuitos), operadores y fechas de vencimiento de contratos con Zultys, BrevAll y operadores. Cantidad de oficinas y direcciones (para el 911).
5. **iDMS/DealerSocket:** ¿tiene API o base de datos de consulta? ¿Quién la administra? ¿Qué datos podemos leer (identificación del cliente, días de mora, estatus) y escribir?
6. Qué significa **OFR**, qué otros estatus hay, quién los asigna y con qué frecuencia cambian.

### B. Grabación y QA con IA

7. Cómo graba hoy Zultys, dónde guarda los archivos, formato, retención y cómo los obtiene el proveedor de QA.
8. Qué campos de metadata exige el proveedor de QA, con su nombre exacto, y cómo define "tramo" de una llamada.
9. Política de retención y de consentimiento (aviso de grabación): estados donde operan.
10. ¿Se deben conservar las grabaciones históricas? ¿Se migran o se mantienen en Zultys?

### C. Operación de cobranza

11. Colas, habilidades y agentes bilingües por bucket de mora y por estatus especial. ¿Redemptions, OFR/Skip y EPD tienen equipos distintos?
12. Horarios de atención y de llamadas salientes. ¿Hacen llamadas salientes automáticas hoy?
13. Ruteo de servicio del vehículo, seguros, títulos/payoffs y ventas en concesionarios: ¿colas fijas o por reglas?
14. Qué hace hoy el Text-to-Pay (sistema, proveedor, interfaz) y la asistencia de pago con representante.

### D. IA y experiencia del cliente

15. Qué quieren que haga la IA: informar saldo y fecha, verificar identidad, tomar acuerdos de pago. Qué reglas de aprobación existen y qué sistemas se actualizan.
16. ¿Qué nivel de riesgo aceptan con una voz de IA hablando con deudores? (Implica avisos, consentimiento y revisión legal.)

### E. Cumplimiento

17. ¿MEI cobra cuentas propias o de terceros? Estados donde llama. Quién es el responsable de cumplimiento (TCPA, Reg F, PCI para pagos) y si tienen asesoría legal.

### F. Proyecto

18. Fecha objetivo y ventana de corte. ¿Qué pasa en la fecha de vencimiento del contrato de Zultys?
19. Rango de presupuesto. Criterios de éxito (qué número de transferencias, espera y abandono considerarían un éxito).
20. Modelo de soporte esperado: horario, tiempos de respuesta, quién da soporte de primer nivel, y el papel de BrevAll.
21. Quién decide, y cuál es el proceso de aprobación del SOW.

## Qué no prometer

- Un precio cerrado o un plazo de migración sin los datos de arriba.
- Que Connect reemplaza la oficina por sí solo.
- Que el español de la IA suena natural: nadie lo midió con acentos reales.
- Que iDMS se integra: no sabemos si tiene interfaz.
- Cumplimiento legal: hay que decir que requiere revisión de abogado.

## Qué llevar

- Una página en inglés con la conclusión y las fases (hoy `docs/proposal/resumen-ejecutivo.md` está en español y tiene lenguaje interno, como la tabla "se esperaba"; no es para entregar tal cual).
- El diagrama del ecosistema y la lista de preguntas A a F impresa.
- Mostrar solo lo verificado: una llamada saliente real desde Connect. Nada más está probado todavía.

## Después de la reunión

1. Resumen de la reunión en 24 horas, con las respuestas y los vacíos.
2. Lista de datos que MEI y BrevAll deben enviar, con responsable y fecha.
3. Fecha de la demostración y qué flujos se mostrarán.
4. Borrador del estimado con rangos y supuestos, y del SOW con exclusiones.
