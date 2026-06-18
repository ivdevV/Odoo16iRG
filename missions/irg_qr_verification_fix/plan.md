# Mision: irg_qr_verification_fix (Actualizado v2)

## Alcance

Corregir las URLs QR generadas en los diplomas y diplomados de Odoo para que apunten dinámicamente al dominio del entorno correspondiente (usando `web.base.url`). Resolver los conflictos de ruteo HTTP entre controladores y posibilitar la validación e interpretación del sello de firma digital cuando los registros no existan físicamente en la base de datos (por ejemplo, en el entorno de desarrollo).

## Clasificación de complejidad

Tier: `standard`.

Justificación: Afecta a 3 archivos controladores existentes para unificar y reestructurar la lógica de verificación web de forma cooperativa. No introduce cambios de arquitectura, flujos de autenticación, migraciones ni borrado de datos.

## Knowledge base consultada

- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_website_verify_qr.md`

## Referencia analizada

- `irg_generacion_diplomas.controllers.main`: Controlador base de verificación.
- `irg_generacion_diplomados_website_verify.controllers.main`: Registra rutas HTTP duplicadas que entran en conflicto.
- `irg_diploma_sheet_verification.controllers.main`: Registra rutas HTTP duplicadas que entran en conflicto e ignora la validación por sello.

## Plan

1. **Investigar y Planificar**: (Completado) Identificar conflictos de rutas y la falta de decodificación de sellos en el histórico.
2. **Implementación**:
   - Modificar `irg_generacion_diplomas/controllers/main.py` para integrar la búsqueda de diplomados y retornar `record_model`.
   - Modificar `irg_generacion_diplomados_website_verify/controllers/main.py` vaciando el controlador para eliminar registros de rutas duplicadas.
   - Modificar `irg_diploma_sheet_verification/controllers/main.py` para delegar en `super()`, admitir diplomados de forma segura y decodificar los datos firmados en el sello si no existe registro físico.
3. **Validación**:
   - Compilación estática de todos los archivos.
   - Pruebas HTTP simulando llamadas en Docker local.
4. **Documentación**:
   - Registrar los cambios en `execution.log` y crear `verification.json` con los resultados.
   - Actualizar el changelog y la base de conocimientos si corresponde.
