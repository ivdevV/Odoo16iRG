# micro-spec: irg_web_editor_fix

## 1. Título corto
Fix TypeError in OdooEditor _applyRawCommand method

## 2. Resumen objetivo
Crear un módulo extra que parchea el método `_applyRawCommand` de OdooEditor para prevenir el error `TypeError: sel.anchorNode[method] is not a function` que ocurre al editar contenido en el editor WYSIWYG.

## 3. Motivo / justificación
El error se produce en `web_editor` core cuando el DOM selection está en un estado inesperado y `anchorNode` no tiene el método esperado. No se puede modificar el core de Odoo, por lo que se requiere un override mediante assets.

## 4. Alcance exacto
- **Módulo**: `irg_web_editor_fix`
- **Asset**: Extender `web_editor.assets_wysiwyg`
- **JavaScript**: Patchear `OdooEditor._applyRawCommand` para añadir validación antes de ejecutar el método
- **Ubicación**: `addons-extra/extrairg/irg_web_editor_fix/`

## 5. Diseño técnico
- Crear módulo `irg_web_editor_fix`
- Usar sistema de assets para extender OdooEditor
- Añadir validación `if (sel.anchorNode && typeof sel.anchorNode[method] === 'function')` antes de llamar al método
- En caso de falla, permitir que el flujo continúe sin interrumpir la edición

## 6. Dependencias
- `depends`: `['web_editor']`

## 7. Backwards-compatibility / migración
- No afecta a datos existentes
- Compatible con cualquier versión de Odoo 16
- No requiere migración de datos

## 8. Casos de prueba / criterios de aceptación
- [ ] El editor WYSIWYG no lanza error al editar contenido
- [ ] El módulo se instala sin errores
- [ ] Las funciones del editor siguen funcionando correctamente

## 9. Rollback plan
```bash
# Desinstalar módulo
odoo-bin -d <db> -i irg_web_editor_fix --uninstall

# O eliminar directorio
rm -rf addons-extra/extrairg/irg_web_editor_fix
```

## 10. Estimación y responsable
- **Estimación**: 1 hora
- **Responsable**: Claude
