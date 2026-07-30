# Diseño: trazabilidad de eventos de marketing en CRM

## Objetivo

Guardar identificadores libres de eventos y anuncios que permitan atribuir leads y reactivaciones a conversiones de Meta y Google.

## Alcance aprobado

Se creará el módulo `irg_crm_marketing_event_tracking` bajo `addons-extra/extrairg/`. Extenderá `crm.lead` con tres campos `Char`, sin automatismos, integraciones externas, modelos nuevos ni cambios de permisos:

- `event_id`, etiquetado como **ID de evento**, en la pestaña Marketing.
- `event_id_reactivacion`, etiquetado como **ID de evento de reactivación**, en el bloque Reactivación.
- `irg_ad_reactivacion`, etiquetado como **Anuncio de reactivación**, en el bloque Reactivación.

El módulo dependerá de `crm` e `irg_crm_reactivacion`. La vista heredará `crm.crm_lead_view_form`; insertará el primer campo junto a la categorización de Marketing y localizará el bloque de Reactivación mediante su campo existente `irg_fecha_reactivacion`, evitando depender del texto traducible del título del grupo.

## Alternativas evaluadas

1. Modificar `irg_crm_reactivacion` y los módulos existentes: descartada, porque las convenciones del repositorio requieren extensiones mediante un módulo nuevo.
2. Crear relaciones a eventos o anuncios: descartada, porque los tres valores deben ser texto libre recibido con el lead.
3. Módulo de extensión pequeño y aislado: seleccionado; aporta los campos sin alterar lógica existente ni introducir dependencias de datos.

## Validación

Se comprobará sintaxis Python, formato XML y coherencia de manifiesto/archivos. Por instrucción expresa del usuario no se iniciará Docker ni se ejecutarán pruebas de Odoo; esta limitación quedará registrada en la evidencia.
