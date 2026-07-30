# Micro-especificación: IDs de evento de Marketing y Reactivación

## Justificación

El equipo necesita conservar identificadores libres de eventos y anuncios asociados a los leads para mejorar la atribución de conversiones de Meta y Google.

## Alcance

El módulo nuevo `irg_crm_marketing_event_tracking` añadirá a `crm.lead` tres campos `Char`: `event_id` en Marketing, y `event_id_reactivacion` e `irg_ad_reactivacion` en Reactivación. No se modifican módulos existentes ni se añaden automatizaciones, datos, permisos o integraciones.

## Criterios de aceptación

1. El formulario de `crm.lead` muestra **ID de evento** en la pestaña Marketing.
2. El bloque Reactivación muestra **ID de evento de reactivación** y **Anuncio de reactivación**.
3. Los tres campos aceptan texto libre.
4. El manifiesto declara `crm` e `irg_crm_reactivacion` como dependencias.

## Validación acordada

No se levantará Docker ni se ejecutarán pruebas Odoo, por petición explícita del usuario. Se validarán sintaxis y estructura XML de forma estática.
