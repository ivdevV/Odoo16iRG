# Diseño: adelanto de 3 días en date_from HomeClass

Fecha: 2026-09-18

Módulo: `irg_batch_homeclass_subject_lead_days`

## Objetivo

Abrir cada asignatura de un lote HomeClass **3 días antes** de la fecha que calcula
`irg_batch_homeclass_api_scheduler`, sin cambiar la fecha oficial de inicio de
clases del lote ni el resto de la sincronización con la API de calendarios.

## Contexto

`irg_batch_homeclass_api_scheduler` consulta
`/api/lotes/{code}/calendario`, asigna `op.subject.to.batch.date_from` (primera
clase o fallback a `op.batch.start_date`) y `date_to` (`end_date` del lote), y
escribe `op.batch.date_start_class` con la primera clase matcheada.

Ese `date_from` abre campus y dispara auto-enroll. `date_start_class` alimenta
correos y diplomas. El negocio quiere acceso anticipado a la asignatura, no
adelantar la fecha comunicada de inicio de clases.

No se corrigen en esta misión el matching por bloque, el fallback a
`start_date` ni la falta de cron del scheduler original.

## Diseño

Addon nuevo en `addons-extra/extrairg/`, prefijo `irg_`, `auto_install` en
False. Depende de `irg_batch_homeclass_api_scheduler`. No se edita el
scheduler.

Hereda `op.batch` y redefine `_sync_homeclass_calendar`:

1. Ejecuta `super()` (API, matching, fallback, `date_to`, `date_start_class`).
2. Si `super()` no es verdadero, termina.
3. Si es verdadero, resta 3 días a cada `date_from` informado en
   `subject_to_batch_ids`.
4. No escribe `date_to` ni `date_start_class`.

El offset es una constante de módulo `IRG_HOMECLASS_SUBJECT_LEAD_DAYS = 3`.
Aplica a fechas de API y al fallback `start_date`. No se recorta contra
`start_date` del lote.

La operación es idempotente: cada sync vuelve a escribir la fecha absoluta del
scheduler y después resta 3 días. Un segundo clic no resta 6.

## Errores y límites

- Lote no HomeClass, sin código, 404 o calendario vacío: el original no
  persiste fechas; este módulo no las inventa.
- `date_from` vacío no se toca.
- No hay cron nuevo, vistas, controladores ni parámetros de sistema.
- No se cambia el botón «Sincronizar Calendario HomeClass».

## Pruebas de aceptación

- Tras un sync exitoso simulado con `date_from` 16/01/2026, la línea queda en
  13/01/2026.
- `date_to` y `date_start_class` conservan el valor que dejó el original.
- El fallback `start_date` 01/01/2026 queda en 29/12/2025.
- Sync fallida deja las fechas como estaban.
- Dos syncs seguidas no restan 6 días.
- Los tests no llaman a la API real.
