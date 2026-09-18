# Progress — irg-batch-homeclass-subject-lead-days

## Código tocado

Addon nuevo `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/`:

- `__manifest__.py` — depende de `irg_batch_homeclass_api_scheduler`
- `models/op_batch.py` — `IRG_HOMECLASS_SUBJECT_LEAD_DAYS = 3`,
  `_irg_apply_homeclass_subject_lead_days()`, override de
  `_sync_homeclass_calendar()`
- `tests/test_subject_lead_days.py` — 5 tests `post_install`

No se modificó `irg_batch_homeclass_api_scheduler`.

## TDD

- RED: 3 failed, 0 errors — `date_from` 16/01/2026 != 13/01/2026
- GREEN: 0 failed, 0 error(s) of 5 tests en `test_irg_hc_lead`

## Fuera de alcance de Review

`plan.md`, `execution.md`, `verification.json`, changelog, docs, knowledge.
