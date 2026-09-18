# Spec — irg-batch-homeclass-subject-lead-days

Fuente canónica:
`docs/superpowers/specs/2026-09-18-irg-batch-homeclass-subject-lead-days-design.md`

Módulo nuevo `irg_batch_homeclass_subject_lead_days` que, tras un
`_sync_homeclass_calendar` exitoso del scheduler original, resta 3 días a cada
`op.subject.to.batch.date_from`. No toca `date_to` ni `date_start_class`.
