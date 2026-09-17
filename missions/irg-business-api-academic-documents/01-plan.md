# IRG Business API Academic Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tres comandos propios para diploma, matrícula y asistencia, sin `gradebook_student_id` en el payload. El comando de notas vuelve a ser solo notas.

**Architecture:** `AcademicDocumentService` en `irg_business_api`. Diploma llama al wizard del alumno. Matrícula/asistencia resuelven la libreta internamente desde `admission_id` porque las plantillas Word viven en `irg.certificate.request`. Lisa nunca ve esa libreta.

**Tech Stack:** Odoo 16, `irg_business_api`, `TransactionCase`, `docker-compose.local.yml`.

---

## Clasificación

- Misión: **full**
- Tier: **standard**
- E2E: **skipped** (sin vistas/QWeb/static/portal/HTTP)
- Security Advisor: no aplica

## Knowledge

- `irg_business_api_command_facade.md`
- `irg_business_api_gradebook_certificate.md` (`file_b64`, `bin_size=False`, parseo `/web/content/<id>`)
- Diploma oficial: `irg.diploma.wizard` (`student_id` + `student_course_id`)
- Word matrícula/asistencia: `irg.certificate.request` (interno)

## File map

- Create: `addons-extra/extrairg/irg_business_api/models/document_service.py`
- Modify: `models/api_constants.py`, `models/api_operation.py`, `models/gradebook_service.py`, `models/__init__.py` if needed, `__manifest__.py` → `16.0.1.4.0`
- Modify: `tests/test_gradebook_certificate.py` (solo notas; rechazar diploma/enrollment/attendance)
- Create: `tests/test_academic_documents.py`
- Modify: `tests/__init__.py`

No editar `irg_generacion_diplomas` ni `irg_gradebook_certificates`.

## Runtime

DB: `test_irg_api_gradebook_cert`. `--test-tags /irg_business_api`.

## Tasks

- [x] RED: tests de los tres comandos + rechazo en el de notas
- [x] GREEN: servicio + dispatch + restringir `DOCUMENT_TYPES`
- [x] Review independiente
- [x] Validación independiente + `verification.json`
- [x] Documentación (contrato, README, knowledge)
