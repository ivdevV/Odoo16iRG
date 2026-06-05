# irg_elearning_child_bin_size_fix

## Descripcion

`irg_elearning_child_bin_size_fix` evita que el formulario de `slide.slide` cargue adjuntos binarios completos al editar los batches de elementos hijos dentro de secciones iRG.

El modulo aplica una herencia de vista sobre `irg_elearning_editable_sections.view_slide_slide_form_child_elements` y añade `bin_size: True` al contexto del campo `child_slide_ids`, conservando los defaults existentes.

## Problema Corregido

Tras proteger `slide_ids`, `irg_native_section_ids`, `irg_online_slide_ids` e `irg_online_section_ids`, el error podia seguir apareciendo si la seccion se abria como ficha completa de `slide.slide`.

En esa ficha, la pestaña **Elementos Hijos** contenia `child_slide_ids` sin `bin_size`. Durante un `onchange`, Odoo podia calcular snapshots de esas lineas hijas y terminar leyendo campos binarios como `image_binary_content` o `binary_content`. En cursos con adjuntos grandes, esa lectura llega a `ir.attachment.datas` y puede agotar la memoria del worker con `MemoryError`.

## Cambios Tecnicos

- Nuevo modulo en `addons-extra/extrairg/irg_elearning_child_bin_size_fix`.
- Dependencia directa: `irg_elearning_editable_sections`.
- Herencia XML de la vista `irg_elearning_editable_sections.view_slide_slide_form_child_elements`.
- Contexto final de `child_slide_ids`:

```python
{
    'default_channel_id': channel_id,
    'default_parent_slide_id': id,
    'default_inherit_limitations_from_parent': True,
    'bin_size': True,
}
```

No se crean modelos, reglas de seguridad ni cambios de datos.

## Uso

Instalar o actualizar el modulo en la base afectada:

```bash
odoo -c /etc/odoo/odoo.conf -d <base_datos> -u irg_elearning_child_bin_size_fix --stop-after-init
```

Si el modulo aun no esta instalado:

```bash
odoo -c /etc/odoo/odoo.conf -d <base_datos> -i irg_elearning_child_bin_size_fix --stop-after-init
```

## Validacion

Pruebas ejecutadas en local:

```bash
python3 addons-extra/extrairg/irg_elearning_child_bin_size_fix/tests/test_slide_slide_child_bin_size.py
python3 -m compileall -q addons-extra/extrairg/irg_elearning_child_bin_size_fix
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d validation_child_bin_size_20260605 \
  --stop-after-init \
  --init irg_elearning_child_bin_size_fix \
  --test-enable \
  --test-tags /irg_elearning_child_bin_size_fix \
  --log-level=test
```

Resultados:

- Test estatico: 1 test ejecutado, 0 fallos, 0 errores.
- Compilacion Python: sin errores.
- Odoo local: modulo cargado correctamente, 0 fallos, 0 errores.

## Limitaciones

Esta correccion evita la carga de binarios en `child_slide_ids`. Si aparece un traceback similar en otra vista o relacion `x2many` de `slide.slide`, habra que revisar esa vista concreta y aplicar el mismo criterio de `bin_size: True`.

## Changelog

- **2026-06-05:** creado modulo heredado para añadir `bin_size: True` a `child_slide_ids` y evitar `MemoryError` al editar batches desde secciones iRG abiertas como ficha completa de `slide.slide`.
