# Changelog - 2026-06-23

## Corrección de Campo Inexistente 'state' en Lotes de Foro

Se ha corregido el error `ValueError: Invalid field op.batch.state` que ocurría al intentar configurar el curso académico en la configuración de un foro, impidiendo el correcto funcionamiento de los filtros y la vinculación de lotes.

### Archivos Modificados:
- **`addons-extra/extrairg/irg_forum_batch_visibility/models/forum_forum.py`**:
  * Se modificó el método `_onchange_irg_course_id` para reemplazar la condición de búsqueda incorrecta `('state', '=', 'active')` por `('active', '=', True)` en el modelo `op.batch`.

### Estado de Validación:
- **Validado**:
  * Verificación de sintaxis AST superada correctamente en el contenedor de Odoo local.
  * Ejecución de consultas en la shell de Odoo exitosa contra las bases de datos `odoo_db` y `local_db`.
