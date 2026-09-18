# Changelog — irg-batch-homeclass-subject-lead-days

## 16.0.1.0.0

- Nuevo módulo `irg_batch_homeclass_subject_lead_days`.
- Tras un sync HomeClass exitoso, cada `date_from` de asignatura queda 3 días
  antes de la fecha del scheduler original.
- No se mutan `date_to` ni `op.batch.date_start_class`.
- No se edita `irg_batch_homeclass_api_scheduler`.
