# Cinta de moroso Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar una cinta lila «Moroso» en el contacto y en el alumno cuando acumulan 2 o más facturas de cliente publicadas sin pagar del todo, y anotar el cambio en el historial.

**Architecture:** Un booleano guardado en `res.partner` lo recalcula `_irg_recompute_moroso` al cambiar la factura o el alumno. La decisión está en `_irg_partner_should_be_moroso` para que otro módulo pueda añadir causas. La cinta lee ese booleano en las dos vistas. Un cron diario y el `post_init_hook` repiten el mismo método.

**Tech Stack:** Odoo 16, `account`, `openeducat_core`, `irg_student_invoice_payment_link`, `web_ribbon`.

## Global Constraints

- Módulo nuevo `addons-extra/extrairg/irg_moroso_banner`, versión `16.0.1.0.0`. No editar módulos existentes.
- Umbral `_IRG_MOROSO_INVOICE_THRESHOLD = 2`.
- Campo `res.partner.irg_is_moroso`: booleano almacenado, default falso, `copy=False`, índice, sin `tracking`.
- Nota exacta: `Pasa a moroso. Facturas sin pagar: N.` y `Deja de ser moroso. Facturas sin pagar: N.` Subtipo `mail.mt_note`.
- Cinta: título `Moroso`, `bg_color="irg_bg_moroso"`, fondo `#7C5CBF`, texto `#FFFFFF`.
- La cuenta no filtra por compañía.
- Sin `ir.model.access.csv`. Sin commit salvo autorización explícita.

---

### Task 1: Regla, nota y ganchos

**Files:**
- Create: `addons-extra/extrairg/irg_moroso_banner/models/res_partner.py`
- Create: `addons-extra/extrairg/irg_moroso_banner/models/account_move.py`
- Create: `addons-extra/extrairg/irg_moroso_banner/models/op_student.py`
- Test: `addons-extra/extrairg/irg_moroso_banner/tests/test_moroso_banner.py`

**Interfaces:**
- Consumes: `account.move` (`state`, `move_type`, `payment_state`, `partner_id`, `irg_student_partner_id`) y `op.student.partner_id`.
- Produces: `res.partner.irg_is_moroso`, `_irg_unpaid_invoice_count()`, `_irg_partner_should_be_moroso()`, `_irg_recompute_moroso()`, `_cron_recompute_moroso()`.

- [ ] Escribir la suite y verla fallar porque faltan el campo y los métodos.
- [ ] Implementar la regla, la nota y los ganchos de factura y alumno.
- [ ] Volver a ejecutar la suite hasta que pase.

### Task 2: Cron, instalación, cinta y estilo

**Files:**
- Create: `addons-extra/extrairg/irg_moroso_banner/data/ir_cron.xml`
- Create: `addons-extra/extrairg/irg_moroso_banner/views/res_partner_views.xml`
- Create: `addons-extra/extrairg/irg_moroso_banner/views/op_student_views.xml`
- Create: `addons-extra/extrairg/irg_moroso_banner/static/src/scss/moroso_ribbon.scss`
- Modify: `addons-extra/extrairg/irg_moroso_banner/__manifest__.py`
- Modify: `addons-extra/extrairg/irg_moroso_banner/__init__.py`

**Interfaces:**
- Consumes: `_cron_recompute_moroso` y `irg_is_moroso`.
- Produces: cron `Recalcular morosos`, `post_init_hook`, cintas en `base.view_partner_form` y `openeducat_core.view_op_student_form`.

- [ ] Añadir el XML, el SCSS y el hook.
- [ ] Comprobar que la vista combinada contiene `irg_bg_moroso` y que el cron existe.
- [ ] Instalar de nuevo con la suite en verde.

### Task 3: Validación

- [ ] `python3 -m compileall` del módulo.
- [ ] Suite Odoo en `test_irg_moroso_banner`.
- [ ] `e2e_testsprite` con `projectPath` en el directorio del módulo, contra el runtime local. Solo si la suite no tiene fallos.
