# IRG Business API Certificate Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extender `irg_generate_gradebook_certificate` a diploma, asistencia y matrícula con el mismo `file_b64` privado.

**Architecture:** El código de operación no cambia. Preview valida tipo, firmante y estado de libreta. Apply usa el wizard solo para notas; el resto crea `irg.certificate.request` y llama `_generate_and_attach_pdf`. Asistencia añade `session_id`.

**Tech Stack:** Odoo 16, `irg_business_api`, dependencias blandas de certificados, `TransactionCase`, `docker-compose.local.yml`.

---

## Clasificación

- Misión: **full** (cambio de comportamiento de producto).
- Tier: **standard** (lógica acotada en 2–5 archivos de producción, contexto claro).
- E2E TestSprite: **skipped** (el diff no toca vistas, QWeb, static, portal ni controladores HTTP).
- Security Advisor: no aplica (no hay auth, migraciones, secretos, despliegue ni borrado histórico).

## Knowledge

- `.agents/knowledge/odoo_development_modding/artifacts/irg_business_api_gradebook_certificate.md` — `file_b64`, `bin_size=False`, firmante explícito, parseo `/web/content/<id>`.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_business_api_command_facade.md` — write cerrado, no flags de contexto RPC.
- Wizard notas: `irg.certificate.wizard` Selection solo `gradebook` | `gradebook_partial`.
- Tipos oficiales: `irg.certificate.request.document_type`.
- Portal: diploma/notas completas exigen libreta `done`.

## File map

- Modify: `addons-extra/extrairg/irg_business_api/models/gradebook_service.py`
- Modify: `addons-extra/extrairg/irg_business_api/models/api_constants.py`
- Modify: `addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py`
- Modify: `addons-extra/extrairg/irg_business_api/__manifest__.py` → `16.0.1.3.0`
- Docs (tras gates): contract, README, `doc/modules/extrairg/irg_business_api.md`, knowledge, CHANGELOG.

No editar `irg_gradebook_certificates` ni `irg_certificate_attendance`.

## Runtime

DB desechable: `test_irg_api_gradebook_cert`. Compose: `docker-compose.local.yml`. Tests: `--test-tags /irg_business_api`. Si asistencia no está instalada, instalar `irg_certificate_attendance` en esa DB para los tests de `session_id`.

No commit/push/PR sin autorización explícita.

---

### Task 1: RED

- [ ] Escribir tests de enrollment/diploma/attendance en `test_gradebook_certificate.py`.
- [ ] Ejecutar en Docker y confirmar fallo por `document_type` / mensaje incorrecto. Evidencia: `artifacts/red-tests.txt`.

### Task 2: GREEN

- [ ] Ampliar `DOCUMENT_TYPES`, `session_id` en OPERATION_SPECS, preview/apply split wizard vs request.
- [ ] Diploma: mismo check `done` que notas completas.
- [ ] Asistencia: exigir `session_id` si el campo existe; validar HC vía `_validate_attendance_request` en preview (`new()`).
- [ ] Diploma PDF tests: patch `_generate_diploma_pdf_content`. Asistencia: patch `_fill_template` + `_convert_to_pdf` (el módulo de asistencia no trae las plantillas Word).
- [ ] GREEN en Docker. Evidencia: `artifacts/green-tests.txt`.
- [ ] `python3 -m py_compile` de los `.py` tocados.

### Task 3: Review + Validación

- [ ] Reviewer independiente (solo código/tests).
- [ ] Validator independiente: tests + py_compile + E2E skipped justificado → `verification.json`.

### Task 4: Documentación

- [ ] Contrato, README, ficha del módulo, knowledge, CHANGELOG. Sin código de producción.
