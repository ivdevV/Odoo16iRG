# irg-campus-activity-audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Commits only if the user authorizes them. Do not push.

**Goal:** Wizard interno en el lote que genera el Excel de actividad de campus con tres flags de finalización.

**Architecture:** Addon nuevo; wizard transitorio; herencia de `op.batch` para el botón. Lectura + `sudo()` tras chequeo de Facultad.

**Tech Stack:** Odoo 16, xlsxwriter, TransactionCase, docker-compose.local.yml.

## Global Constraints

- New module only under `addons-extra/extrairg/irg_campus_activity_audit`.
- Version `16.0.1.0.0`. Depends: `openeducat_core`, `isep_elearning_custom`, `isep_student_filter`, `isep_gradebook`.
- `completion_porc` is computed; never use it in SQL domains.
- Three separate completion columns; never collapse them.
- Server-side `AccessError` unless `openeducat_core.group_op_faculty`.
- Work on `Dev_iRG`. No push. No commit unless the user asks.
- Tests on disposable DB `test_irg_campus_audit` via `docker-compose.local.yml`.
- E2E TestSprite is in scope (wizard XML + batch button).

See `missions/irg-campus-activity-audit/01-plan.md` and `docs/superpowers/specs/2026-09-17-irg-campus-activity-audit-design.md` for tasks and acceptance.
