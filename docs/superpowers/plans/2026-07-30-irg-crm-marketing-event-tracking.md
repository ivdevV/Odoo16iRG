# CRM Marketing Event Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir campos de texto libre para identificar eventos y anuncios de marketing en leads y reactivaciones de CRM.

**Architecture:** Un módulo `irg_` aislado hereda `crm.lead` y la vista estándar de formulario. Sus dependencias garantizan la pestaña Marketing de CRM y el grupo Reactivación; no crea modelos ni lógica de negocio.

**Tech Stack:** Odoo 16, Python, XML de vistas heredadas.

## Global Constraints

- Crear el módulo en `addons-extra/extrairg/` y no modificar módulos existentes.
- Usar API de Odoo 16, `_inherit = 'crm.lead'` y `xpath` sobre la vista estándar.
- Los tres campos son `fields.Char` de texto libre, sin relación ni automatismo.
- No levantar Docker ni ejecutar pruebas Odoo, por instrucción expresa del usuario.
- No realizar commit, push ni PR sin autorización independiente.

---

### Task 1: Módulo de trazabilidad de eventos

**Files:**
- Create: `addons-extra/extrairg/irg_crm_marketing_event_tracking/__init__.py`
- Create: `addons-extra/extrairg/irg_crm_marketing_event_tracking/__manifest__.py`
- Create: `addons-extra/extrairg/irg_crm_marketing_event_tracking/models/__init__.py`
- Create: `addons-extra/extrairg/irg_crm_marketing_event_tracking/models/crm_lead.py`
- Create: `addons-extra/extrairg/irg_crm_marketing_event_tracking/views/crm_lead_views.xml`

**Interfaces:**
- Consumes: modelo `crm.lead`, vista `crm.crm_lead_view_form` y campo `irg_fecha_reactivacion` de `irg_crm_reactivacion`.
- Produces: campos `event_id`, `event_id_reactivacion` e `irg_ad_reactivacion` editables en el formulario de CRM.

- [x] **Step 1: Registrar la excepción de TDD antes de implementar**

Documentar en `missions/irg-crm-marketing-event-tracking/execution.md` que una prueba Odoo requeriría el runtime Docker, que el usuario prohibió ejecutar, y que se aplicarán comprobaciones estáticas alternativas.

- [x] **Step 2: Crear el esqueleto e implementación mínima**

```python
class CrmLead(models.Model):
    _inherit = "crm.lead"

    event_id = fields.Char(string="ID de evento")
    event_id_reactivacion = fields.Char(string="ID de evento de reactivación")
    irg_ad_reactivacion = fields.Char(string="Anuncio de reactivación")
```

Declarar dependencias `crm` e `irg_crm_reactivacion`; cargar la vista. Con `xpath`, insertar `event_id` tras `x_studio_ga` y los dos campos de reactivación dentro del grupo que contiene `irg_fecha_reactivacion`.

- [x] **Step 3: Comprobar sintaxis y XML sin runtime Odoo**

Run: `python -m py_compile addons-extra/extrairg/irg_crm_marketing_event_tracking/models/crm_lead.py`
Expected: exit code 0.

Run: script de `xml.etree.ElementTree.parse` sobre manifiesto XML.
Expected: parse correcto y los tres nombres de campos presentes.

- [x] **Step 4: Revisar alcance y documentación**

Comprobar que solo se crean los cinco archivos del módulo y los artefactos de la misión; actualizar micro-especificación, changelog y `verification.json` con la exclusión justificada de Docker/Odoo.
