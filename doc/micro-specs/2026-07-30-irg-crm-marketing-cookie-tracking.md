# Micro-especificación: identificadores de cookies de marketing en CRM

## Alcance

Extender `irg_crm_marketing_event_tracking` con cinco campos `Char` de texto libre: `fbc` y `fbp` en Marketing; `fbclid_reactivacion`, `fbc_reactivacion` y `fbp_reactivacion` en Reactivación. No se añaden automatismos, relaciones, migraciones ni permisos.

## Criterios de aceptación

1. Marketing muestra `fbc` y `fbp`.
2. Reactivación muestra `fbclid_reactivacion`, `fbc_reactivacion` y `fbp_reactivacion`.
3. Los cinco campos son `Char` editables.
4. El cambio parte de `main` y no incluye commits previos fuera del módulo ya integrado.

## Validación acordada

No se iniciará Docker ni se ejecutarán pruebas Odoo, por instrucción previa del usuario. Se harán comprobaciones estáticas de Python, XML y contrato de campos.
