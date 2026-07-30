# CRM Marketing Cookie Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Registrar identificadores de clic y cookies de Meta para leads y reactivaciones de CRM.

**Architecture:** Ampliar el módulo de tracking ya integrado en `main`; el modelo añade campos `Char` y la vista los coloca en los bloques Marketing y Reactivación existentes.

**Tech Stack:** Odoo 16, Python y XML.

## Global Constraints

- Cinco campos de texto libre `Char`, sin relaciones ni automatismos.
- Marketing: `fbc`, `fbp`; Reactivación: `fbclid_reactivacion`, `fbc_reactivacion`, `fbp_reactivacion`.
- No levantar Docker ni ejecutar pruebas Odoo, por instrucción del usuario.
- Rama creada desde `origin/main`; no incluir cambios ajenos.

---

### Task 1: Campos adicionales de atribución de Meta

**Files:**
- Modify: `addons-extra/extrairg/irg_crm_marketing_event_tracking/models/crm_lead.py`
- Modify: `addons-extra/extrairg/irg_crm_marketing_event_tracking/views/crm_lead_views.xml`

**Interfaces:**
- Consumes: `crm.lead`, la página `extra` y el bloque con `irg_fecha_reactivacion`.
- Produces: cinco campos `Char` editables en Marketing y Reactivación.

- [x] **Step 1: Registrar excepción de TDD**

Documentar que la instalación Odoo requiere Docker, excluido por el usuario; validar estáticamente en su lugar.

- [x] **Step 2: Añadir campos y referencias de vista**

```python
fbc = fields.Char(string="FBC")
fbp = fields.Char(string="FBP")
fbclid_reactivacion = fields.Char(string="FBCLID de reactivación")
fbc_reactivacion = fields.Char(string="FBC de reactivación")
fbp_reactivacion = fields.Char(string="FBP de reactivación")
```

Insertar `fbc` y `fbp` junto a `irg_event_id`; añadir los tres campos de reactivación al grupo existente.

- [x] **Step 3: Ejecutar validación estática**

Run: `python -m py_compile addons-extra/extrairg/irg_crm_marketing_event_tracking/models/crm_lead.py`
Expected: exit code 0.

Run: parse XML, chequeo de los cinco campos y `git diff --check`.
Expected: todos aprobados.
