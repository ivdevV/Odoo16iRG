# irg_web_editor_fix

## 1. Titulo corto
Fix TypeError in OdooEditor _applyRawCommand method.

## 2. Resumen objetivo
Crear un modulo extra que parchea el metodo _applyRawCommand de OdooEditor para prevenir el error TypeError: sel.anchorNode[method] is not a function al editar contenido en el editor WYSIWYG.

## 3. Motivo / justificacion
El error se produce en web_editor core cuando el selection del DOM queda en un estado inesperado y anchorNode no expone el metodo requerido. No se toca core Odoo; se implementa override por assets.

## 4. Alcance exacto
- Modulo: irg_web_editor_fix.
- Asset: web_editor.assets_wysiwyg.
- JavaScript: patch defensivo de OdooEditor._applyRawCommand.
- Ubicacion: addons-extra/extrairg/irg_web_editor_fix/.

## 5. Diseno tecnico
- Importar OdooEditor desde @web_editor/js/editor/odoo-editor/src/OdooEditor.
- Aplicar patch al prototype.
- Antes de ejecutar el comando:
  - Validar que anchorNode exista.
  - Validar que anchorNode[method] sea funcion.
  - Si no lo es, intentar fallback en parentNode para text nodes.
  - Si no hay fallback valido, retornar false para evitar crash de UI.
- En caso de excepcion con mensaje de is not a function vinculado a anchorNode, retornar false y no propagar.

## 6. Dependencias
- web_editor
- website_forum

## 7. Backwards-compatibility / migracion
No hay cambios de modelo ni de schema. Cambio acotado a cliente web en bundle de editor.

## 8. Casos de prueba / criterios de aceptacion
- Editar aviso en foro campus y guardar sin TypeError en consola.
- Validar que comandos basicos de edicion sigan funcionando.
- Validar que no se rompa el editor para posts nuevos y existentes.

## 9. Rollback plan
- Desinstalar modulo irg_web_editor_fix o revertir commit.
- Actualizar modulo web_editor si fuese necesario.

## 10. Estimacion y responsable
- Estimacion: 1 hora.
- Responsable: equipo IRG.
