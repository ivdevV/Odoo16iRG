# Mision: irg_diplomado_website_verify_qr

## Alcance

Hacer que el QR de los diplomas de diplomados valide en el sitio web del mismo Odoo, de forma equivalente al modulo `irg_generacion_diplomas`.

## Clasificacion de complejidad

Tier: `standard`.

Justificacion: se crea un modulo puente por herencia con controlador web publico, extension de modelo/wizard y tests. No toca autenticacion, secretos, migraciones ni borrado de datos.

## Knowledge base consultada

- `.agents/knowledge/odoo_development_modding/artifacts/diplomado_report_layout.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_course_duration.md`

## Referencia analizada

- `irg_generacion_diplomas.controllers.main`: rutas publicas `/verificar` y `/verificar_api`.
- `irg_generacion_diplomas.views.diploma_verify_templates`: plantilla web de validacion.
- `irg_generacion_diplomas.wizard.diploma_wizard`: QR con parametros `id`, `stamp`, `data_str`, `certificate_id`.

## Plan

1. Crear modulo nuevo `irg_generacion_diplomados_website_verify`.
2. Extender `/verificar` y `/verificar_api` para que validen tambien `irg.diplomado.registry` por `name`.
3. Anadir plantilla web especifica que muestre diplomas normales y diplomados sin romper el flujo existente.
4. Extender `irg.diplomado.registry.action_reprint()` para construir `qr_url` con `web.base.url + /verificar/?...`.
5. Extender `irg.diplomado.wizard.action_print_diplomado()` para usar la misma URL al generar desde backend.
6. Validar con tests HTTP y unitarios.
