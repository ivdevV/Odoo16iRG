# Changelog — 2026-03-20 — irg_phone_prefix_fix

## Objetivo
Corregir pérdida del dígito "1" en números mexicanos (+521...) y evitar reformateo visual inconsistente en formulario de contacto.

## Cambios realizados
1. Se añadió models/__init__.py en el módulo para asegurar carga de código Python.
2. Se reescribió el override de res.partner._phone_format para preservar +521 cuando el usuario lo introduce.
3. Se añadieron overrides de onchange para phone/mobile y mantener consistencia en UI.
4. Se añadió vista heredada de partner form para cambiar widget="phone" por widget="char" en phone/mobile.
5. Se actualizó __manifest__.py a versión 16.0.2.0.0 e inclusión de la vista XML en data.

## Impacto esperado
- El número +52 1 ... no pierde el dígito "1" al guardar/editar.
- El formulario muestra el valor tal cual fue guardado.
- Se reduce dependencia del formateo automático JS en campos de contacto.

## Nota de cumplimiento
Este changelog cubre el requisito de entrega "changelog sencillo y claro" indicado en SPECIFICATIONS.md.
