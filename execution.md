# Registro de Ejecución: Soporte Modalidad Intensivo (IN), Código MOPCIN2701 y Campo 'Es Intensivo' en Sale Order

## Misión: `irg_intensivo_modality_mopcin`
- **Fecha**: 2026-07-23
- **Nivel de Misión**: `standard`
- **Estado**: COMPLETADO

## Log de Acciones
1. **Planificación**:
   - `implementation_plan.md` actualizado y aprobado por el usuario con el desglose exacto: `MO` (Máster Oficial), `PC` (Código de curso), `IN` (Intensivo), `27` (Año), `01` (Mes) -> `MOPCIN2701`.
   - Incorporado el campo booleano `irg_is_intensive` ("Es Intensivo") en `sale.order`, `sale.order.line`, `op.batch` y `op.admission`.
   - `plan.md` actualizado.

2. **Implementación Backend y Vistas XML**:
   - Campos `irg_is_intensive` agregados en `sale.order` y `sale.order.line`.
   - `get_lot_id` en `sale.order` extendido para usar `self.irg_is_intensive` o `line.irg_is_intensive` si está activo, forzando `prefix_02 = 'IN'`.
   - `_detect_line_modalidad` en el wizard manual actualizado para retornar `'IN'` cuando `irg_is_intensive` está activo en la línea/orden.
   - Vista formulario `sale_order_views.xml` en `irg_openeducat_sale_lote_custom` extendida con el toggle boolean "Es Intensivo".
   - Vistas XML agregadas en `op_batch_views.xml` y `op_admission_views.xml` para toggles y filtros de búsqueda.

3. **TDD y Validación**:
   - Actualizados unit tests `test_intensivo_modality.py` y `test_intensivo_wizard_preview.py` incluyendo los casos de uso con el tick `irg_is_intensive` en `sale.order`.
   - Verificación de sintaxis limpia (`py_compile`) de los archivos Python.
   - Verificación de ejecución completa de los 27 tests unitarios en `test_irg_db` con resultado exitoso (0 fallos).
   - Generado `verification.json` con `status: passed`.
