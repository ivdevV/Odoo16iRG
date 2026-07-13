# Revisión final — `fix-auto-enroll-cron`

Fecha: 2026-07-13.

Resultado: **APROBADA** para revisión del usuario. La validación independiente posterior
está en `passed`; no se autoriza por ello ningún commit, push o despliegue.

## Alcance revisado

- Correspondencia con T1.1–T4.2 y S1–S4 del plan/especificación aprobados.
- MRO de `op.admission`, unificación cron/botón y procesamiento de modalidad `manual`.
- Savepoints por admisión y savepoint exterior del guardarraíl.
- Concurrencia cron/botón, índice único parcial, preflight y uninstall.
- Reutilización de memberships archivadas, aislamiento por lote y transición
  Homeclass→Online.
- Triggers nativos de `ir.cron` creados por `create/write/unlink`.
- Fallback de precedencia histórica limitado al lote actual.
- Scripts SQL de informe/backfill y su ausencia de referencias desde manifests o hooks.
- Pruebas nuevas y regresiones existentes de online opening/clone access.

## Hallazgos cerrados

1. `_irg_auto_enroll_domain()` quedó en `irg_online_subject_opening`, por lo que ese módulo
   no depende accidentalmente del micro-módulo robusto.
2. El uninstall usa la firma Odoo 16 correcta de `tools.drop_index`.
3. Los placeholders se sustituyeron por escenarios conductuales reales, incluidos dos
   cursores para concurrencia y limpieza selectiva de triggers por ID.
4. Las búsquedas de memberships archivadas usan `active_test=False`, `batch_id` y orden
   `active DESC, create_date ASC`.
5. La constraint Python y el índice parcial usan la misma clave
   `(partner_id, channel_id, batch_id)` para registros activos con lote.
6. El guardarraíl se corrigió, tras el fallo real de T4.2 y aprobación del usuario, para
   calcular `archived_count / initial_active_count`. Exactamente 30% se permite y más de
   30% revierte el run completo.
7. El cambio de fechas concurrente crea el trigger mediante el hook real; los tests no
   borran triggers preexistentes ni dejan triggers residuales.

## Evidencia de cierre

- Suite `irg_auto_enroll_cron_robust`: 27/27, 0 fallos, 0 errores, 5963 queries.
- Regresiones `irg_online_subject_opening` + `irg_online_clone_access_fix`: 13/13,
  0 fallos, 0 errores, 2181 queries.
- T4.2 manual: archivado 1/10, reactivación del mismo ID e idempotencia sin duplicados.
- Guardarraíl manual: 4/10 = 40%, excepción esperada y estados restaurados.
- Persistencia `noupdate`, índice/preflight/uninstall, SQL con `ROLLBACK`, sintaxis,
  registry y `git diff --check`: PASS.

La evidencia detallada está en `validation.md`, `verification.json` y `artifacts/`.

## Riesgos y límites conocidos

- `noupdate="1"` conserva modificaciones administrativas posteriores; cambios futuros del
  XML del cron requerirán migración o edición explícita.
- Se aceptan triggers nativos redundantes durante cambios masivos, según S3; no se añadió
  cola, lock ni modelo técnico auxiliar.
- El índice no corrige históricos automáticamente. El preflight aborta ante duplicados
  activos y el backfill entregado termina siempre en `ROLLBACK` hasta que Operaciones decida
  revisarlo y ejecutarlo fuera de esta misión.
- T4.3 en beta no se ejecutó: requiere despliegue y autorización explícita nueva.

No quedan hallazgos bloqueantes dentro del alcance aprobado.
