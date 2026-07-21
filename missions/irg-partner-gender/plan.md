# Plan — irg-partner-gender

## Objetivo

Hacer visible y editable el género en `res.partner` y en la pestaña de admisión del pedido, y resolver el género en matrícula automática con cascada pedido → partner → heurística → `'o'`, persistiendo en el partner cuando se infiere.

## Clasificación

- Tier misión: `full`
- Capacidad: `standard`
- Módulo nuevo: `irg_partner_gender` (no editar módulos legacy)
- Depende de: `irg_admission_gender_fix`, `isep_sale_order_admissions`

## Criterios de aceptación

1. Campo `gender` visible en ficha de contacto (fuera de la pestaña Moodle).
2. Campo `gender` visible en pestaña Admisión del pedido de venta.
3. `_irg_resolve_gender` / `_irg_resolve_admission_gender` aplican cascada SO → partner → heurística → `'o'`.
4. Si el valor sale de heurística y el partner no tenía `m`/`f`, se escribe `partner.gender` (`m`/`f`/`o`).
5. `_create_or_get_admission` y `create_admission_manual` usan el género resuelto (vía write-back a partner antes de `super()`).
6. Tests unitarios GREEN en `docker-compose.local.yml`.

## Knowledge consultado

- `.agents/knowledge/odoo_development_modding/artifacts/irg_admission_gender_fix.md`

## Fuera de alcance

- Checkout/web pidiendo género
- Backfill masivo histórico
- Unificación total de selection Moodle vs OpenEduCat
