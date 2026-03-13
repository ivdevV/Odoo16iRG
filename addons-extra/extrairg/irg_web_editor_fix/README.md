# IRG Web Editor Fix

## Descripción
Este módulo parchea el método `_applyRawCommand` de OdooEditor para prevenir el error `TypeError: sel.anchorNode[method] is not a function` que ocurre al editar contenido en el editor WYSIWYG.

## Motivo
El error se produce en `web_editor` core cuando el DOM selection está en un estado inesperado y `anchorNode` no tiene el método esperado. Este módulo añade validación y manejo de errores para prevenir que el editor falle.

## Instalación

### Instalación vía CLI
```bash
odoo-bin -d <tu_base_de_datos> -i irg_web_editor_fix --stop-after-init
```

### Instalación desde interfaz
1. Ir a Ajustes > Aplicaciones > Actualizar lista de aplicaciones
2. Buscar "IRG Web Editor Fix"
3. Hacer clic en Instalar

## Funcionalidad
- Parchea el método `_applyRawCommand` de OdooEditor
- Añade manejo de errores para capturar `TypeError` con mensajes "is not a function"
- Registra warnings en la consola del navegador para debugging
- Permite que el editor continue funcionando sin interrupciones

## Dependencias
- `web_editor` (nativo de Odoo)

## Changelog

### 16.0.1.0 (2026-03-12)
- Versión inicial
- Parche para `_applyRawCommand` y `_protect`
- Añadido manejo de errores para TypeError
- Micro-spec: `doc/micro-specs/2026-03-12-irg_web_editor_fix.md`

## Soporte
Instituto Raimon Gaja - https://www.institutoraimongaja.com
