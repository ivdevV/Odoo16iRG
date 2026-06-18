# Mision: irg_qr_verification_fix

## Alcance

Corregir las URLs QR generadas en los diplomas y diplomados de Odoo para que apunten dinámicamente al dominio del entorno correspondiente (usando `web.base.url`) en lugar del dominio corporativo hardcodeado `https://institutoraimongaja.com`.

## Clasificación de complejidad

Tier: `standard`.

Justificación: Afecta a 5 archivos de lógica y reportes en dos módulos existentes. No introduce cambios de arquitectura, flujos de autenticación, migraciones de datos, ni eliminación de datos históricos.

## Knowledge base consultada

- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_website_verify_qr.md`

## Referencia analizada

- `irg_generacion_diplomas.wizard.diploma_wizard`: QR URL hardcodeada en la línea 72.
- `irg_generacion_diplomados.models.diplomado_registry`: QR URL hardcodeada en la línea 117.
- `irg_generacion_diplomados.wizard.diplomado_wizard`: QR URL hardcodeada en la línea 147.
- `irg_generacion_diplomas.reports.diploma_pdf_report`: Fallback hardcodeado en la línea 423.
- `irg_generacion_diplomados.reports.diplomado_pdf_report`: Fallback hardcodeado en la línea 96.

## Plan

1. **Investigar y Planificar**: (Completado) Identificar todos los puntos donde se genera el QR.
2. **Implementación**:
   - Modificar `irg_generacion_diplomas/wizard/diploma_wizard.py` para obtener `web.base.url` dinámicamente.
   - Modificar `irg_generacion_diplomas/reports/diploma_pdf_report.py` para usar `web.base.url` en el fallback.
   - Modificar `irg_generacion_diplomados/models/diplomado_registry.py` para obtener `web.base.url` dinámicamente.
   - Modificar `irg_generacion_diplomados/wizard/diplomado_wizard.py` para obtener `web.base.url` dinámicamente.
   - Modificar `irg_generacion_diplomados/reports/diplomado_pdf_report.py` para usar `web.base.url` en el fallback.
3. **Validación**:
   - Compilación estática de todos los archivos modificados.
   - Ejecución de los tests existentes de verificación web para validar el correcto funcionamiento.
4. **Documentación**:
   - Registrar los cambios en `execution.log` y crear `verification.json` con los resultados.
   - Actualizar el changelog y la base de conocimientos si corresponde.
