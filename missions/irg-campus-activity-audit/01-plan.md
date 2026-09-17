# Plan — irg-campus-activity-audit

> **For agentic workers:** Execute task-by-task with TDD. Commits only if the user authorizes them. Do not push to `Dev_iRG`.

**Goal:** Desde la ficha interna de un lote, generar un Excel de actividad de campus (e-learning, evaluaciones, libreta) con tres columnas separadas de “curso finalizado”, y un listado XLSX opcional.

**Architecture:** Addon nuevo `irg_campus_activity_audit`. Wizard transitorio `irg.campus.activity.audit.wizard`. Herencia de `op.batch` solo para el botón. Lectura de modelos existentes; sin escritura académica. Tras `has_group(Facultad)`, recopilación con `sudo()` de solo lectura.

**Tech Stack:** Odoo 16, `xlsxwriter`, `TransactionCase`, `docker-compose.local.yml`.

## Global Constraints

- Módulo nuevo en `addons-extra/extrairg/`; no editar addons existentes.
- Prefijo `irg_`; versión `16.0.1.0.0`.
- Depende de `openeducat_core`, `isep_elearning_custom`, `isep_student_filter`, `isep_gradebook`.
- Knowledge: `modding_rules_and_email_analysis.md`, `irg_course_completion_progress.md`.
- `completion_porc` no se usa en dominios SQL.
- Tres flags separados; no un único “finalizado”.
- ACL y chequeo server-side: `openeducat_core.group_op_faculty`.
- Adjunto no público. Sin portal.
- Rama de trabajo: `Dev_iRG`. Sin push.
- Runtime: `docker-compose.local.yml`. BD desechable: `test_irg_campus_audit`.
- E2E TestSprite obligatorio (wizard + botón en lote); corre tras el resto de checks.

## Tier

`standard`. Un módulo nuevo, lógica acotada de informe, sin autenticación/migraciones/secretos. Security Advisor no se dispara (no hay cambio de auth, ni migración, ni borrado). El export contiene PII: grupo Facultad + `AccessError` en servidor.

## Files

- Create: `addons-extra/extrairg/irg_campus_activity_audit/__init__.py`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/__manifest__.py`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/models/__init__.py`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/models/op_batch.py`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/wizard/__init__.py`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/wizard/listado_parser.py`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/wizard/xlsx_export.py`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/wizard/campus_activity_audit_wizard.py`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/wizard/campus_activity_audit_wizard_views.xml`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/views/op_batch_views.xml`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/security/ir.model.access.csv`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_campus_activity_audit/tests/test_campus_activity_audit.py`

## Command

```
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_campus_audit \
  -i irg_campus_activity_audit --test-enable --test-tags /irg_campus_activity_audit \
  --without-demo=all --max-cron-threads=0 --stop-after-init --log-level=test
```

Pasa si `odoo.tests.result` reporta `0 failed, 0 error(s)` y exit 0.

---

### Task 1: Scaffold + parser de listado + wizard de lote

**Produces:** módulo instalable; `parse_listado_xlsx`; wizard con `batch_id`; `_assert_can_export`; `_enrollments`; tres flags; XLSX de resumen; acción en lote.

- [ ] Tests RED en `tests/test_campus_activity_audit.py`
- [ ] Implementación mínima GREEN
- [ ] No commit salvo autorización

### Task 2: Hojas de campus, evaluaciones y libreta

**Produces:** hojas Actividades, Progreso por asignatura, Evaluaciones, Libreta *; listado opcional → No encontrados.

- [ ] Tests RED de actividades completadas, campus_completado, cruce de listado, hojas de libreta
- [ ] GREEN
- [ ] No commit salvo autorización

### Task 3: Vistas internas

**Produces:** formulario del wizard, binding Acción en `op.batch`, botón en cabecera del lote (`groups="openeducat_core.group_op_faculty"`).

## Criterios de aceptación

1. Desde un lote interno se descarga un XLSX.
2. El resumen trae `matricula_finalizada`, `libreta_100` y `campus_completado` por separado.
3. Un interno sin Facultad recibe `AccessError`.
4. Un listado con un correo ajeno al lote aparece en “No encontrados”.
5. No se escriben `op.student.course`, canales ni libretas.
