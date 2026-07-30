# Ejecución: colisión de `event_id`

## Diagnóstico

El traceback de instalación registra `crm_lead_event_id_fkey` y tipos incompatibles `character varying` e `integer`. Esto demuestra que `event_id` ya pertenece al esquema de CRM como campo relacional.

## Decisión

Se renombrará solamente el campo introducido por `irg_crm_marketing_event_tracking` a `irg_event_id`. La etiqueta seguirá siendo **ID de evento**, y no se tocarán la columna, los datos ni la clave foránea preexistentes.

## Excepción de TDD

La reproducción y la prueba de instalación requieren runtime Odoo/Docker. El usuario indicó previamente no levantar Docker ni ejecutar pruebas Odoo; se utilizarán comprobaciones estáticas de Python, XML y contrato de campos como alternativa.

## Implementación

- Sustituida la declaración `event_id` por `irg_event_id` en el modelo.
- Sustituida la referencia de vista por `irg_event_id`; la etiqueta visible continúa siendo **ID de evento**.
- Sin cambios en `event_id_reactivacion` ni `irg_ad_reactivacion`.

## Gates

- Revisión independiente aprobada; evidencia en `artifacts/code-review.txt`.
- Validación independiente estática aprobada; evidencia en `artifacts/static-validation.txt`.
- Docker y pruebas Odoo no ejecutados por instrucción explícita del usuario.
