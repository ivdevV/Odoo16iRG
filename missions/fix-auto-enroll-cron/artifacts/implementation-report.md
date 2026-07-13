# Informe de implementación — `fix-auto-enroll-cron`

Estado de fase: `DONE_WITH_CONCERNS`.

La implementación de Tareas 1–6 (T1.1–T3.2 y S1–S4) está aplicada en el worktree
aislado. No se creó `verification.json`: corresponde a la validación independiente.

## Archivos de producto

Modificados:

- `addons-extra/addons_uisep/isep_elearning_custom/data/cron_batch_slide_channel.xml`
- `addons-extra/addons_uisep/isep_elearning_custom/models/op_admission.py`
- `addons-extra/extrairg/irg_subject_fix/models/op_admission.py`
- `addons-extra/extrairg/irg_online_subject_opening/models/op_admission.py`
- `addons-extra/extrairg/irg_online_clone_access_fix/models/op_admission.py`
- `addons-extra/extrairg/irg_online_clone_access_fix/models/slide_channel_partner.py`
- `addons-extra/extrairg/irg_course_convocatorias_v2/models/slide_channel_partner.py`

Creado el micro-módulo `addons-extra/extrairg/irg_auto_enroll_cron_robust/` con manifest,
hooks, modelos y tests. No crea modelos nuevos, por lo que no necesita ACL propia.

## Resultado funcional

- Cron horario por defecto y XML `noupdate=1` conservando el XML ID.
- Hooks relevantes de `op.subject.to.batch` llaman directamente a `_trigger()`.
- Índice único parcial activo por alumno/canal/lote, preflight sin mutación y uninstall.
- La constraint Python heredada se alinea con la misma clave por lote; sin ello el módulo
  preexistente `isep_subject_precedence` bloqueaba lotes distintos antes del índice.
- Colisiones exactas del índice se aíslan por savepoint en auto-enroll y clonación.
- Todas las búsquedas que reutilizan archivadas usan `active_test=False`, lote actual y
  orden `active DESC, create_date ASC`.
- Precedencia: primero membership completada de la admisión; fallback histórico completado
  limitado por alumno, asignatura padre y lote.
- El cron procesa admisiones `done` con lote, incluidas manuales, delegando al botón por
  admisión con savepoint individual.
- Snapshot antes/después incluye memberships históricas de los pares alumno/lote; el ratio
  global revierte el savepoint exterior si supera estrictamente el 30%.
- Eliminado únicamente el override muerto del cron en `irg_online_clone_access_fix`; los
  otros overrides históricos conservan cuerpo y reciben comentario.

## Ciclos TDD y comandos

RED en DB aislada `fix_auto_enroll_cron_red_20260713` mediante
`docker-compose.local.yml`, montando este worktree en `/mnt/extra-addons`: 24 tests,
4 failed y 15 errors. Las causas esperadas fueron XML diario, hooks/índice/helpers ausentes.

Primer GREEN en DB nueva `fix_auto_enroll_cron_green_20260713`: 24 tests, 0 failed,
0 errors. Tras reforzar tests conductuales apareció la constraint Python sin lote;
se añadió la alineación mínima y el último rerun obtuvo de nuevo 24 tests, 0 failed,
0 errors (1514 queries).

Checks adicionales:

- `python3 -m compileall`: PASS antes de retirar los `__pycache__` generados.
- `xmllint --noout cron_batch_slide_channel.xml`: PASS.
- `git diff --check`: PASS.
- `membership-gaps-report.sql` con `psql -v ON_ERROR_STOP=1`: PASS.
- `backfill_memberships.sql` con `psql -v ON_ERROR_STOP=1`: PASS; `UPDATE 0`, `UPDATE 0`
  y `ROLLBACK` confirmado en la DB aislada.

## Artefactos SQL

- `membership-gaps-report.sql` es exclusivamente read-only.
- `backfill_memberships.sql` usa candidatos únicos (`HAVING count(*) = 1`), muestra
  conteos antes/después y termina en `ROLLBACK`.
- Ningún manifest, hook o XML carga estos scripts. No se ejecutaron en `Base16`.

## Riesgos y concerns para Validación

1. Una instalación aislada de solo `irg_online_subject_opening` confirmó que
   `irg_auto_enroll_cron_robust` está `uninstalled` y que `_irg_auto_enroll_domain()` pertenece
   a `irg_online_subject_opening`, con el domain esperado. Dos tests históricos de esa
   instalación mínima fallan por APIs/campos aportados por otros módulos no declarados como
   dependencias (`get_subjects_visible_for_batch` y `nbr_certification`); no están relacionados
   con el helper corregido. En el stack completo relevante, los 13 post-tests existentes pasan.
2. El log del stack contiene warnings históricos de manifests ajenos al cambio.

No se hizo commit, push, deploy, PR, merge ni escritura en `Base16`.

## Corrección de hallazgos de revisión (2026-07-13)

- `_irg_auto_enroll_domain()` se movió al módulo autónomo
  `irg_online_subject_opening`; el micro-módulo ya no lo aporta accidentalmente.
- `uninstall_hook` usa la firma Odoo 16 completa:
  `tools.drop_index(cr, index_name, 'slide_channel_partner')`.
- Se reemplazaron todos los placeholders señalados por pruebas conductuales reales:
  guardarraíl 30% y >30% con rollback, dos transacciones cron/botón concurrentes,
  Homeclass→Online, aislamiento de lote, preferencia de activa, equivalencia cron/botón,
  aislamiento de fallo, ciclo de fechas e idempotencia, online sin fechas y modalidad manual.
- El test concurrente de triggers registra baseline, confirma la limpieza desde el snapshot,
  elimina solo sus IDs en `finally` y preserva triggers preexistentes.
- Índice real comprobado en PostgreSQL. El preflight se prueba con un duplicado SQL temporal y
  confirma que aborta sin borrarlo. El uninstall hook se ejecuta transaccionalmente y se verifica
  que retira exactamente el índice antes de restaurarlo para el resto de la suite.
- Se añadió `lang='en_US'` solo a los fixtures preexistentes de los dos módulos relevantes para
  que sus tests alcancen el comportamiento.

Resultados finales en `docker-compose.local.yml`, DB aislada
`fix_auto_enroll_review_red_20260713`:

- `irg_auto_enroll_cron_robust`: 26 post-tests, 0 failed, 0 errors, 4653 queries.
- `irg_online_subject_opening` + `irg_online_clone_access_fix`: 13 post-tests,
  0 failed, 0 errors, 2181 queries.
- Preflight dirigido: 1 post-test, 0 failed, 0 errors, 175 queries.
- `compileall`, `git diff --check` y ausencia de `__pycache__`/`.pyc` nuevos o no
  versionados: PASS. Los binarios ya versionados por el repositorio se preservaron sin cambios.
- Índice observado:
  `UNIQUE (partner_id, channel_id, batch_id) WHERE active IS TRUE AND batch_id IS NOT NULL`.

Recuento de tests de la suite robusta: 26 métodos conductuales. Escalados: 0.

## Corrección final de triggers concurrentes (2026-07-13)

- `test_change_committed_during_running_cron_keeps_trigger_for_next_run` ya no llama
  directamente a `ir.cron._trigger()`: crea un fixture confirmado, abre el snapshot del run y
  en una segunda transacción ejecuta `write({'date_to': ...})` y `commit()` reales sobre
  `op.subject.to.batch`. El trigger posterior se origina exclusivamente en el hook del modelo.
- El test registra por ID los triggers del fixture, del `write` y del `unlink`; su limpieza usa
  únicamente esos IDs en `finally`. También verifica que todos desaparecen y que cada ID del
  baseline sigue existiendo.
- Se eliminó `_clear_triggers()` de la suite. Los cuatro tests create/write irrelevante/write
  relevante/unlink comparan sets de IDs contra su baseline y nunca borran triggers ajenos.
- El fixture confirmado del test concurrente cron/botón también rastrea y elimina selectivamente
  los triggers generados al crear y desmontar su `op.subject.to.batch`.

Evidencia final en base fresca `fix_auto_enroll_trigger_fresh2_20260713`:

- Suite robusta completa: 26 post-tests, 0 failed, 0 errors, 4746 queries.
- Consulta posterior del cron `isep_elearning_custom.ir_cron_auto_enroll_students`:
  `ir_cron_trigger count = 0`.
- Cambios de producto para esta corrección: 0; solo tests y artefactos de misión.

## Reimplementación S1 aprobada tras T4.2 (2026-07-13)

El único cambio funcional de esta reapertura es el denominador del guardarraíl:

- Antes: `archived_count / (activated_count + archived_count)`.
- Ahora: `archived_count / initial_active_count`, donde `initial_active_count` es el número
  de memberships activas del snapshot anterior al run.
- Si `initial_active_count == 0`, el ratio es `0.0`.

Se conservan sin cambios el snapshot por pares alumno/lote, los contadores de activadas y
archivadas, el umbral estrictamente mayor que 30%, el savepoint exterior, el rollback global y
el aislamiento por admisión. El `WARNING` incluye ahora `activated`, `archived`,
`initial_active` y `ratio`.

TDD:

- RED en `fix_auto_enroll_review_red_20260713`: 27 post-tests, 0 failed, 3 errors,
  5739 queries. Fallaron exactamente el archivado único, el 30% exacto y el ciclo por cron
  pasado/futuro porque el denominador anterior devolvía 100%.
- GREEN tras el cambio mínimo: 27 post-tests, 0 failed, 0 errors, 5963 queries.

Pruebas conductuales S1:

- 1 archivada de 10 activas iniciales se aplica con 0 activaciones compensatorias.
- 3 archivadas de 10 activas iniciales (30% exacto) se aplican.
- 4 archivadas de 10 activas iniciales (40%) lanzan `ValidationError` y restauran todos los
  estados iniciales.
- 0 activas iniciales con 1 activación no divide por cero y finaliza correctamente.
- El escenario `date_to` pasado/futuro usa el cron en sus tres ejecuciones: archiva 1 de 10,
  reactiva la misma membership y conserva los 10 IDs tras una segunda ejecución idempotente.

Evidencia final en DB nueva `fix_auto_enroll_s1_green_20260713`:

- Suite robusta: 27 post-tests, 0 failed, 0 errors, 5963 queries.
- Regresión `irg_online_subject_opening` + `irg_online_clone_access_fix`: 13 post-tests,
  0 failed, 0 errors, 2181 queries.
- Triggers persistentes del cron tras ambas suites: 0.
- `compileall` y `git diff --check`: PASS; pycache generado retirado.

No se modificó ningún otro comportamiento y no hubo commit, push, deploy ni acceso a Base16.
