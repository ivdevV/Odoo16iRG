# Ejecución: trazabilidad de eventos CRM

## Decisiones

- Se usa un módulo nuevo para no modificar extensiones existentes.
- Los campos son `Char` porque el usuario confirmó que recibirán identificadores libres de Meta y Google.
- TDD con pruebas Odoo no es viable en esta misión: requiere levantar Docker/runtime Odoo y el usuario instruyó expresamente no levantar Docker ni ejecutar esas pruebas. Antes de implementar se usará como alternativa comprobación estática de sintaxis Python y de XML.

## Comandos y resultados

- Se creó `irg_crm_marketing_event_tracking` con dependencias `crm` e `irg_crm_reactivacion`.
- Se añadieron los tres campos `Char` y una vista heredada que los ubica en Marketing y Reactivación.
- Revisión independiente: aprobada sin hallazgos; evidencia en `artifacts/code-review.txt`.
- Validación independiente: sintaxis Python, XML, campos/dependencias y whitespace aprobados; evidencia en `artifacts/static-validation.txt`.
- Docker y las pruebas Odoo no se ejecutaron por instrucción expresa del usuario.
