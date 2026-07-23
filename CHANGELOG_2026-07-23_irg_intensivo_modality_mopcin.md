# CHANGELOG: Modalidad Intensivo (IN), Formato MOPCIN2701 y Campo 'Es Intensivo' en Presupuestos, Lotes y Admisiones

**Fecha**: 2026-07-23  
**Módulo(s)**: `irg_openeducat_sale_lote_custom`, `irg_sale_manual_confirmation_wizard`  

---

### Resumen de Cambios

1. **Campos 'Es Intensivo' (`irg_is_intensive`)**:
   - **`sale.order` & `sale.order.line`**: Añadido campo booleano `irg_is_intensive` ("Es Intensivo") con toggle en la vista formulario de presupuestos de ventas.
   - **`op.batch`**: Campo booleano computado y almacenado `irg_is_intensive` que detecta la modalidad `IN`.
   - **`op.admission`**: Campo booleano relacionado `irg_is_intensive` desde `batch_id.irg_is_intensive`.

2. **Generación de Código de Lote (`MOPCIN2701`)**:
   - Soporte genérico para modalidad `IN` cuando la orden tiene activo `irg_is_intensive` o el producto variante es `Intensivo`.
   - Formato resultante: `MO` (Categoría Máster Oficial) + `PC` (Código de Curso) + `IN` (Intensivo) + `27` (Año 2027) + `01` (Enero) = **`MOPCIN2701`**.

3. **Wizard Manual de Confirmación**:
   - `_detect_line_modalidad`: Reconoce la modalidad `IN` cuando `irg_is_intensive` está activo en el presupuesto/línea.
   - Previsualización correcta de `MOPCIN2701` y asignación del lote/admisión al confirmar.

4. **Vistas XML**:
   - [sale_order_views.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_openeducat_sale_lote_custom/views/sale_order_views.xml): Toggle "Es Intensivo" en presupuestos.
   - [op_batch_views.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_openeducat_sale_lote_custom/views/op_batch_views.xml): Toggle y filtro "Es Intensivo" en lotes.
   - [op_admission_views.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/views/op_admission_views.xml): Toggle y filtro "Es Intensivo" en admisiones.
