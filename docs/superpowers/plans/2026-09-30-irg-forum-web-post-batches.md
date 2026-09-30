# Selector web de lotes al crear una publicación de foro — Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un usuario interno elige, al crear un tema en la web del foro, los lotes que pueden ver esa publicación, y esa selección queda en `forum.post.visibility_batch_ids`.

**Architecture:** Módulo nuevo `irg_forum_web_post_batches`. Hereda la plantilla `website_forum.new_question` y el `post_create` de `website_forum`. El controlador pone los ids válidos en el contexto `irg_visibility_batch_ids`. `forum.post.create` los escribe en el mismo `create`, solo si el usuario es interno y el registro no es una respuesta.

**Tech Stack:** Odoo 16, QWeb, `website_forum`, `irg_forum_batch_visibility`, `openeducat_core`.

## Global Constraints

- Módulo nuevo. No se modifican módulos existentes.
- El selector solo se renderiza para `base.group_user`, con `irg_course_id` y al menos un lote activo.
- La lista son `op.batch` activos de ese curso (`active` = True).
- Sin selección, `visibility_batch_ids` queda vacío.
- Ids de otro curso, inactivos o inválidos se descartan.
- Un portal no aplica ids aunque los envíe.
- Una respuesta no copia el contexto.
- No se usa `sudo()` para ampliar los lotes asignables. El catálogo se lee con `sudo()` porque `op.batch` solo es legible por grupos de OpenEduCat; la asignación sigue limitada a ese catálogo.
- El gate E2E aplica porque hay plantilla web y controlador HTTP.

## jev_intake

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 0.99, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.86, "needs_security_advisor": false, "security_noul": 0.09, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```

**Tier:** `standard`. La función es un alta acotada sobre un campo existente. El esqueleto del módulo supera cinco archivos, pero no hay arquitectura nueva, concurrencia ni migración.

---

### Task 1: Catálogo y alta

**Files:**
- Create: `addons-extra/extrairg/irg_forum_web_post_batches/`
- Test: `addons-extra/extrairg/irg_forum_web_post_batches/tests/test_web_post_batches.py`

- [ ] Implementar `_irg_web_post_batches` y `_irg_sanitize_web_post_batch_ids` en `forum.forum`.
- [ ] En `forum.post.create`, copiar el contexto al campo antes de `super()` cuando el usuario es interno y no hay `parent_id`.
- [ ] Heredar `post_create` para leer `irg_visibility_batch_ids` del POST solo si el usuario es interno y no es una respuesta.
- [ ] Heredar `website_forum.new_question` con casillas para esos lotes.
- [ ] Ejecutar las pruebas del módulo con `docker-compose.local.yml`.

### Task 2: Cierre

- [ ] Review de código independiente.
- [ ] Validación con `verification.json`.
- [ ] Documentar uso y limitaciones.
- [ ] Subir el cambio a `Dev_iRG`.
