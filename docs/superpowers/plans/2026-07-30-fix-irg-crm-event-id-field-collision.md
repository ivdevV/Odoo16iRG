# CRM Event ID Field Collision Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evitar la colisión de esquema con la columna relacional existente `crm_lead.event_id`.

**Architecture:** Cambiar únicamente el campo nuevo a `irg_event_id`, conservando su etiqueta de usuario y el resto de campos de reactivación. No se ejecutan migraciones ni operaciones SQL.

**Tech Stack:** Odoo 16, Python y XML de vistas heredadas.

## Global Constraints

- No modificar la columna preexistente `event_id` ni sus datos.
- Mantener `irg_event_id` como `fields.Char(string="ID de evento")`.
- Mantener `event_id_reactivacion` e `irg_ad_reactivacion` sin cambios.
- No levantar Docker ni ejecutar pruebas Odoo, por instrucción del usuario.
- No realizar commit ni push sin autorización independiente.

---

### Task 1: Renombrar el campo de tracking sin alterar el esquema existente

**Files:**
- Modify: `addons-extra/extrairg/irg_crm_marketing_event_tracking/models/crm_lead.py`
- Modify: `addons-extra/extrairg/irg_crm_marketing_event_tracking/views/crm_lead_views.xml`

**Interfaces:**
- Consumes: `crm.lead` y la pestaña `extra` del formulario CRM.
- Produces: `irg_event_id` de tipo `Char`, visible como **ID de evento**.

- [x] **Step 1: Registrar la excepción de TDD**

Registrar que una prueba de instalación requiere Docker/Odoo y está excluida por instrucción del usuario; sustituirla por verificaciones estáticas del nombre de campo y el XML.

- [x] **Step 2: Aplicar la corrección mínima**

```python
irg_event_id = fields.Char(
    string="ID de evento",
    help="Identificador del evento de marketing asociado al lead.",
)
```

Sustituir `<field name="event_id"/>` por `<field name="irg_event_id"/>` en la vista. No cambiar los campos de reactivación.

- [x] **Step 3: Validar estáticamente**

Run: `python -m py_compile addons-extra/extrairg/irg_crm_marketing_event_tracking/models/crm_lead.py`
Expected: exit code 0.

Run: parse XML y búsqueda de `event_id = fields.`.
Expected: XML válido y ausencia de la declaración conflictiva.
