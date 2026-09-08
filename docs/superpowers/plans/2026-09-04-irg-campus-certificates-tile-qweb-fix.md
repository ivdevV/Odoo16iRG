# QWeb certificates tile fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evitar el 500 de `/campus/course/<id>` causado por `hasattr` en QWeb, sin editar módulos existentes.

**Architecture:** Módulo nuevo que hereda la plantilla del tile `certificates_and_diplomas` y reemplaza el `t-if` por `not course_id.is_diplomado()`. Un test extrae ese `t-if` del arch combinado y lo renderiza con `ir.qweb` para reproducir el TypeError.

**Tech Stack:** Odoo 16, QWeb inherit, TransactionCase, docker-compose.local.yml

---

### Task 1: Tests RED

**Files:**
- Create: `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/__init__.py`
- Create: `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/__manifest__.py`
- Create: `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/tests/test_qweb_guard.py`

- [ ] **Step 1: Write the failing tests** (esqueleto sin vista)

- [ ] **Step 2: Run tests and confirm RED** (`hasattr` sigue en el `t-if`; render lanza TypeError)

### Task 2: Inherit QWeb GREEN

**Files:**
- Create: `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/views/campus_dashboard_override.xml`
- Modify: `__manifest__.py` para cargar la vista

- [ ] **Step 1: Add xpath that sets `t-if="not course_id.is_diplomado()"`**
- [ ] **Step 2: Run tests and confirm GREEN**

### Task 3: Review, validation, docs, publish

- [ ] Review independiente del código
- [ ] Validación en `docker-compose.local.yml`
- [ ] E2E TestSprite (scope QWeb/portal)
- [ ] Documentación y knowledge
- [ ] Commit y push a `Dev_iRG` (autorizado)
