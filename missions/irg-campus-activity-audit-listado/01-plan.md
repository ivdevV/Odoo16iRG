# Plan — irg-campus-activity-audit-listado

> **For agentic workers:** Execute task-by-task with TDD. Commits only if the user authorizes them. Do not push to `Dev_iRG`.

**Goal:** El personal interno sube el Excel de listado (como `listado diplomados.xlsx`) y descarga el informe de actividad. El lote deja de ser el origen.

**Architecture:** Mismo addon `irg_campus_activity_audit`. El wizard exige el XLSX. Cruce por correo y código de curso extraído de `Curso` (`Nombre del diplomado (CODIGO)`). Menú en OpenEduCat → Reporting. Se elimina el botón y el binding del lote.

**Tech Stack:** Odoo 16, `xlsxwriter`, `TransactionCase`, `docker-compose.local.yml`.

## Global Constraints

- Solo se edita `addons-extra/extrairg/irg_campus_activity_audit/`.
- Knowledge: `modding_rules_and_email_analysis.md`, `irg_course_completion_progress.md`.
- `completion_porc` no va a dominios SQL.
- Tres flags separados de finalización.
- ACL Facultad + `AccessError` server-side.
- Adjunto no público. Sin portal.
- Rama: `Dev_iRG`. Sin push.
- Runtime: `docker-compose.local.yml`. BD: `test_irg_campus_audit`.
- E2E TestSprite: `skipped`. El diff no toca QWeb, `static/`, portal, website ni controladores HTTP. El XML del wizard es un TransientModel de backend; la descarga se cubre con TransactionCase.

## Tier

`standard`. Cambio de origen del informe (listado vs lote), parser y matching. Sin auth, migraciones ni secretos.

## Files

- Modify: wizard, parser, export, tests, manifest, views del wizard
- Delete: `models/op_batch.py`, `views/op_batch_views.xml`

## Command

```
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_campus_audit \
  -u irg_campus_activity_audit --test-enable --test-tags /irg_campus_activity_audit \
  --without-demo=all --max-cron-threads=0 --stop-after-init --log-level=test
```

Pasa si `odoo.tests.result` reporta `0 failed, 0 error(s)` y exit 0.

---

### Task 1: Parser del listado real

**Produces:** filas con email, curso, código entre paréntesis, nombre, país, modalidad.

### Task 2: Wizard sin lote

**Produces:** listado obligatorio; matching global por correo+curso; menú interno; sin botón de lote.

## Criterios de aceptación

1. OpenEduCat → Reporting → Informe de actividad abre el wizard.
2. Sin Excel no se genera.
3. El Excel de diplomados (correo, curso con código, nombre, país, modalidad) cruza matrículas aunque no se elija lote.
4. Un correo del listado sin matrícula va a «No encontrados».
5. Un alumno del mismo lote que no está en el Excel no sale en el resumen.
6. Siguen las tres columnas de finalización. No se escriben matrículas ni libretas.
