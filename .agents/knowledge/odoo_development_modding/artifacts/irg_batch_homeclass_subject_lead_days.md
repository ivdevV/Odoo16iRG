# Patron: offset de date_from tras sync HomeClass

Fecha: 2026-09-18

Modulo: `irg_batch_homeclass_subject_lead_days`

## Decision reutilizable

Para ajustar fechas de asignatura **sin** tocar
`irg_batch_homeclass_api_scheduler`, heredar `op.batch`, llamar
`super()._sync_homeclass_calendar()` y aplicar el delta solo si el padre
devuelve verdadero. Mutar unicamente `op.subject.to.batch.date_from`. Dejar
`date_to` y `op.batch.date_start_class` al valor del scheduler (fecha real de
clase / comunicaciones).

El offset es idempotente respecto a la API porque cada sync reescribe la fecha
absoluta y despues resta. El helper privado no es idempotente por si solo.

## Motivos

- Abrir campus y auto-enroll antes de la primera clase.
- No adelantar correos ni diplomas que leen `date_start_class`.

## Gotchas

- Tests: crear el lote con `skip_homeclass_sync` y parchear
  `odoo.addons.irg_batch_homeclass_api_scheduler.models.op_batch.requests.get`.
  Sin eso, `create` de un lote HC pega a la API real.
- En esta instancia, `op.course.create` exige `lang`.
- El `__init__.py` raiz del addon no debe importar `tests`.
- `auto_install` False: instalar el modulo de forma explicita por entorno.
