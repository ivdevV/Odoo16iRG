# Changelog — irg-tfm-outline-survey

## 2026-09-10

- Sustituido el nuevo envío del Esquema como archivo por un cuestionario de tres
  bloques y varias preguntas por pantalla.
- Añadida una plantilla editable basada en Encuestas con diez preguntas iniciales.
- Precargados nombre, correo y máster como valores editables.
- Añadidos borrador persistente, revisión optimista, snapshot de plantilla y
  versiones inmutables.
- Añadida consulta de respuestas enviadas para el grupo Revisor TFM.
- Cerrado el cuestionario al asignar convocatoria y reabierto al retirarla.
- Conservados los Esquemas antiguos en archivo exclusivamente en lectura.
- Bloqueadas las rutas e intentos nativos de Survey para la plantilla TFM.
- Añadidos límites de tamaño, aislamiento por matrícula, protección CSRF y
  registro de chatter sin notificaciones.
- Incorporadas pruebas de modelo, HTTP, concurrencia, seguridad, límites,
  versionado y regresión del flujo de archivos.
- Corregida la compilación QWeb del cuestionario en Odoo 16: los campos de
  título y descripción ahora se renderizan sobre nodos HTML compatibles.
- Evitada la colisión con la variable `editable` reservada por Website, que
  mostraba como solo lectura un borrador válido de un alumno Portal.
