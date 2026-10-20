# Cinta de dotación por morosidad Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar la cinta «Dotado por morosidad» en la factura de cliente conciliada con un asiento publicado de dotación, y anotar el cambio en su historial.

**Architecture:** Un booleano guardado en `account.move` lo decide `_irg_move_is_dotado_morosidad` y lo escribe `_irg_recompute_dotacion`. Los ganchos están en la conciliación parcial, en `state`/`ref` del asiento y en `name` del apunte. La cinta lee ese booleano. La instalación repite el recálculo sin nota.

**Tech Stack:** Odoo 16, `account`, `web_ribbon`, `account.partial.reconcile`.

## Global Constraints

- Módulo nuevo `addons-extra/extrairg/irg_invoice_dotacion_banner`, versión `16.0.1.0.0`. No editar módulos existentes. Depende solo de `account`.
- Frase `_IRG_DOTACION_PHRASE = 'dotación por morosidad'`.
- Campo `account.move.irg_dotado_morosidad`: booleano almacenado, default falso, `copy=False`, índice, sin `tracking`.
- Notas exactas: `Pasa a dotado por morosidad.` y `Deja de estar dotado por morosidad.` Subtipo `mail.mt_note`.
- Cinta: título `Dotado por morosidad`, `bg_color="irg_bg_dotado"`, fondo `#4F6D7A`, texto `#FFFFFF`.
- Sin filtro de compañía. Sin cron. Sin `ir.model.access.csv`. Sin commit salvo autorización explícita.

---

### Task 1: Regla, nota y ganchos

**Files:**
- Create: `addons-extra/extrairg/irg_invoice_dotacion_banner/models/account_move.py`
- Test: `addons-extra/extrairg/irg_invoice_dotacion_banner/tests/test_invoice_dotacion_banner.py`

**Interfaces:**
- Consumes: `account.partial.reconcile.debit_move_id` y `credit_move_id`; `account.move.ref`, `state`, `move_type`; `account.move.line.name`.
- Produces: `irg_dotado_morosidad`, `_irg_move_is_dotado_morosidad()`, `_irg_recompute_dotacion(notify=True)`, `_irg_install_recompute_dotacion()`.

- [x] Escribir la suite y verla fallar porque faltan el campo y los métodos.
- [x] Implementar la regla, la nota y los ganchos de conciliación, asiento y apunte.
- [x] Volver a ejecutar la suite hasta que pasen las pruebas de comportamiento.

### Task 2: Instalación, cinta y estilo

**Files:**
- Create: `addons-extra/extrairg/irg_invoice_dotacion_banner/views/account_move_views.xml`
- Create: `addons-extra/extrairg/irg_invoice_dotacion_banner/static/src/scss/dotacion_ribbon.scss`
- Modify: `addons-extra/extrairg/irg_invoice_dotacion_banner/__manifest__.py`
- Modify: `addons-extra/extrairg/irg_invoice_dotacion_banner/__init__.py`

**Interfaces:**
- Consumes: `_irg_install_recompute_dotacion` e `irg_dotado_morosidad`.
- Produces: `post_init_hook` y la cinta en `account.view_move_form`.

- [x] Añadir el XML, el SCSS y el hook.
- [x] Comprobar que la vista combinada contiene `irg_bg_dotado` y `#4F6D7A`.
- [x] Actualizar el módulo con la suite en verde.

### Task 3: Validación

- [x] `python3 -m compileall` del módulo.
- [x] Suite Odoo en `test_irg_invoice_dotacion`.
- [ ] `e2e_testsprite` con `projectPath` en el directorio del módulo, contra el runtime local, solo si la suite no tiene fallos.
