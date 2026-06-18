# Mision: irg_qr_verification_fix (Actualizado)

## Alcance

Corregir las URLs QR generadas en los diplomas y diplomados de Odoo para que apunten dinámicamente al dominio del entorno correspondiente (usando `web.base.url`). Adicionalmente, actualizar el controlador del módulo `irg_diploma_sheet_verification` para que sea compatible y busque dinámicamente registros de diplomados en `irg.diplomado.registry` cuando se valide desde la web.

## Clasificación de complejidad

Tier: `standard`.

Justificación: Afecta a un archivo adicional de control (`main.py` de `irg_diploma_sheet_verification`), sumando un total de 6 archivos. No introduce cambios de arquitectura, flujos de autenticación, migraciones de datos, ni eliminación de datos históricos.

## Knowledge base consultada

- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_website_verify_qr.md`

## Referencia analizada

- `irg_diploma_sheet_verification.controllers.main`: Intercepta la ruta `/verificar` omitiendo diplomados y rompiendo su validación.

## Plan

1. **Investigar y Planificar**: (Completado) Identificar la interferencia del controlador de `irg_diploma_sheet_verification`.
2. **Implementación**:
   - Modificar `irg_generacion_diplomas` e `irg_generacion_diplomados` (ya completado en la iteración anterior).
   - Modificar `irg_diploma_sheet_verification/controllers/main.py` para admitir búsqueda condicional en `irg.diplomado.registry` y formatear el diccionario de salida de forma compatible y segura.
3. **Validación**:
   - Compilación estática de todos los archivos modificados.
   - Ejecución de los tests existentes de verificación web para validar que el sistema no presente regresiones.
4. **Documentación**:
   - Registrar los cambios en `execution.log` y crear `verification.json` con los resultados.
   - Actualizar el changelog y la base de conocimientos si corresponde.
