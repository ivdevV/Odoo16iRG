# Filtro modalidades prácticas online — Implementation Plan

> **For agentic workers:** TDD en el módulo nuevo. No editar addons existentes.

**Goal:** Limitar el combo de tipo de práctica en el campus a convalidaciones y asíncronas cuando el lote de la matrícula es máster online.

**Architecture:** Addon `irg_practice_request_online_types`. Helper de código de lote, Boolean computado en `op.student.course`, constraint en `practice.request` para portal, inherit QWeb del formulario. Depende de `irg_practice_preferred_quarter` para ir al final de la cadena HTTP.

**Tech Stack:** Odoo 16, herencia, tests `TransactionCase`.

---

### Task 1: Helper de lote + campo en matrícula

- Create: `addons-extra/extrairg/irg_practice_request_online_types/`
- Test: `tests/test_practice_request_online_types.py`

### Task 2: Constraint portal en `practice.request`

Create/write rechazan tipo no permitido si `env.user` es portal.

### Task 3: QWeb + JS

Inherit `isep_practices_2.practice_request_form_template`. `setTimeout(0)` tras el change legacy.

### Task 4: Controller

Inherit `IrgPracticePreferredQuarter._irg_create_portal_request`, validar antes de `super()` y re-renderizar con `error_message`.
