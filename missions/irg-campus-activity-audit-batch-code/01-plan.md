# Plan — irg-campus-activity-audit-batch-code

> **For agentic workers:** Execute with TDD. No commit/push unless the user authorizes it.

**Goal:** El código entre paréntesis del listado (`DITGHC2606`) debe cruzar `op.batch.code` además de `op.course.code`. En producción el curso es `TG` y el lote es `DITGHC2606`.

**Evidence:** logs prod `call_button` 11:30:40 UTC, 41 queries / 3.7s (informe vacío de matches). SELECT: emails existen; matrícula `course=TG`, `batch=DITGHC2606`.

**Tier:** `standard`. Bug de matching. Sin auth/migraciones. E2E `skipped` (wizard backend).

## Command

```
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_campus_activity_audit --test-enable --test-tags /irg_campus_activity_audit \
  --without-demo=all --max-cron-threads=0 --stop-after-init --log-level=test
```
