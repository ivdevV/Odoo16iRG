# Review de código — irg-batch-homeclass-subject-lead-days

Revisor independiente. No se ha editado código de producción ni se han
ejecutado tests.

Alcance revisado (solo código y tests del addon nuevo):

- `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/__init__.py`
- `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/__manifest__.py`
- `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/models/__init__.py`
- `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/models/op_batch.py`
- `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/tests/__init__.py`
- `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/tests/test_subject_lead_days.py`

Contrato usado (no revisado como entregable): spec
`docs/superpowers/specs/2026-09-18-irg-batch-homeclass-subject-lead-days-design.md`
y criterios de `01-plan.md` / `02-progress.md`.

`git status` sobre `addons-extra/extrairg/irg_batch_homeclass_api_scheduler`
está limpio. El scheduler no forma parte del diff.

## Contrato que se cumple

- Addon nuevo `irg_*` en `addons-extra/extrairg/`, `version` `16.0.1.0.0`,
  `auto_install` False, depende de `irg_batch_homeclass_api_scheduler`.
- Hereda `op.batch`, redefine `_sync_homeclass_calendar`, llama
  `super()._sync_homeclass_calendar()` y solo si el resultado es verdadero
  aplica `_irg_apply_homeclass_subject_lead_days()`.
- Offset fijo `IRG_HOMECLASS_SUBJECT_LEAD_DAYS = 3` sobre cada `date_from`
  informado; `date_from` vacío se deja; no hay recorte contra `start_date`.
- Los `write` del offset van solo a `date_from`, con
  `skip_homeclass_sync=True` para no reentrar en el sync del padre.
- No hay `sudo`, secretos ni llamadas HTTP propias.
- `__init__.py` raíz importa solo `models`, no `tests`.
- Tests `post_install` / `-at_install`: match 16/01→13/01, fallback
  01/01/2026→29/12/2025, skip vacío, sync fallida, idempotencia vía padre
  que reescribe fechas absolutas. `requests.get` del scheduler está parcheado
  con `AssertionError`; el lote se crea con `skip_homeclass_sync`.

## Hallazgos

### BLOQUEANTE

Ninguno.

### MENOR

Ninguno.

### NIT

- **`tests/test_subject_lead_days.py` (`test_sync_is_idempotent_against_parent_absolute_dates`)**
  — Tras dos syncs solo se aserta el `date_from` de la línea matcheada. El
  fallback (29/12/2025) y `date_start_class` ya están cubiertos en el sync
  de una pasada. Si se quiere simetría, repetir esas aserciones en el test
  de idempotencia. No es un agujero del plan.

- **`models/op_batch.py` (`_irg_apply_homeclass_subject_lead_days`)**
  — El helper no es idempotente si se invoca dos veces sin que el padre
  reescriba la fecha absoluta; restaría 6 días. El contrato de producto es
  el re-sync (padre escribe la fecha de API y después se resta 3), y ese
  camino sí está cubierto. No hace falta guardia extra salvo que se quiera
  endurecer el método privado.

## Veredicto

Ningún hallazgo rompe seguridad, arquitectura ni el plan. El addon es el
inherit mínimo acordado y los tests cubren los cinco casos exigidos sin
pegar a la API real.

REVIEW OK
