# Micro-Spec: IRG Practice Center Documents Consistency (2026-06-02)

## 1. Titulo corto
Consistencia de adjuntos en centros de practicas

## 2. Resumen objetivo
Crear un modulo correctivo `irg_practice_center_documents_consistency` para estabilizar el guardado de documentos asociados a `practice.center` desde backend.

## 3. Motivo / justificacion
- El modulo `irg_practice_center_documents` muestra el mismo campo `document_ids` dos veces en la misma vista: una como `many2many_binary` editable y otra como lista readonly.
- Esa duplicidad puede provocar estados inconsistentes del formulario al guardar campos x2many.
- Los adjuntos nuevos o sin vinculacion previa deben quedar normalizados con `res_model='practice.center'` y `res_id` del centro para mantener permisos, busquedas y trazabilidad coherentes.

## 4. Alcance exacto
- Nuevo modulo `irg_practice_center_documents_consistency` en `addons-extra/extrairg/`.
- Herencia de `practice.center` para anadir un campo readonly separado `document_display_ids` sobre la misma tabla relacional que `document_ids`.
- Normalizacion de metadatos de `ir.attachment` nuevos o sin vinculacion previa despues de crear o actualizar centros con documentos.
- Herencia de la vista de `irg_practice_center_documents` para reemplazar la segunda aparicion readonly de `document_ids` por `document_display_ids`.
- Tests automatizados para validar campo, vista y persistencia real de adjuntos.
- Documentacion del modulo en `doc/modules/extrairg/irg_practice_center_documents_consistency.md`.

## 5. Fuera de alcance
- No se crea un modelo documental propio con estados o vencimientos.
- No se exponen documentos en portal.
- No se modifica directamente `isep_practices_2` ni `irg_practice_center_documents`.
- No se cambian permisos globales de `ir.attachment`.

## 6. Dependencias
- `irg_practice_center_documents`

## 7. Criterios de aceptacion
1. La vista mantiene un unico `document_ids` editable con `many2many_binary`.
2. La lista readonly usa `document_display_ids`, no una segunda instancia de `document_ids`.
3. Al guardar documentos en un centro existente, la relacion se conserva despues de recargar el registro.
4. Los adjuntos nuevos o sin vinculacion previa quedan con `res_model='practice.center'` y `res_id` del centro.
5. Los adjuntos ya vinculados a otro recurso no se reasignan automaticamente.
6. La correccion se implementa por herencia, sin editar modulos existentes.
7. Los tests del modulo pasan en Odoo local cuando el entorno este disponible.

## 8. Rollback plan
Desinstalar `irg_practice_center_documents_consistency` o revertir el commit del modulo y actualizar la base de datos.
