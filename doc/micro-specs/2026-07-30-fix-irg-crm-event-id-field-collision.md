# Micro-especificación: corrección de colisión de `event_id` en CRM

## Problema

Al instalar `irg_crm_marketing_event_tracking`, Odoo intenta definir `crm.lead.event_id` como texto. La base de datos ya contiene esa columna como clave foránea entera, y PostgreSQL no permite convertirla a `varchar`.

## Alcance aprobado

Sustituir exclusivamente el nombre técnico del nuevo campo por `irg_event_id`; conservar la etiqueta **ID de evento** y su ubicación en Marketing. No se modifica ni elimina la columna preexistente `event_id`, sus datos ni su clave foránea.

## Criterios de aceptación

1. El módulo no declara ningún campo `event_id` sobre `crm.lead`.
2. Declara `irg_event_id` como `fields.Char`.
3. La vista muestra `irg_event_id` con etiqueta **ID de evento** en Marketing.
4. `event_id_reactivacion` e `irg_ad_reactivacion` permanecen sin cambios.

## Validación acordada

No se levantará Docker ni se ejecutarán pruebas Odoo, por instrucción explícita del usuario. Se harán comprobaciones estáticas de Python, XML y ausencia del campo técnico conflictivo.
