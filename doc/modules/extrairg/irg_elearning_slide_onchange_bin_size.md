# irg_elearning_slide_onchange_bin_size

## Descripcion

`irg_elearning_slide_onchange_bin_size` fuerza `bin_size: True` durante los `onchange` de `slide.slide` para evitar que Odoo lea adjuntos binarios completos al recalcular formularios de eLearning.

Este modulo complementa las correcciones de vista aplicadas en `irg_elearning_editable_sections`, `irg_course_convocatorias_v2` e `irg_elearning_child_bin_size_fix`.

## Problema Corregido

Al editar batches en secciones iRG, Odoo puede crear registros virtuales de formulario como `slide.slide(<NewId origin=3742>)`. Durante el snapshot interno del `onchange`, el cliente puede incluir campos binarios en el arbol de campos (`nametree`), como `image_binary_content` o `binary_content`.

Si el contexto efectivo del `onchange` no contiene `bin_size: True`, Odoo intenta leer el binario real desde `ir.attachment.datas`. En adjuntos grandes, esa lectura puede agotar la memoria del worker y provocar `MemoryError`.

Aunque `bin_size: True` este configurado en campos `x2many`, ese contexto puede no llegar a todas las llamadas de `onchange` del propio `slide.slide`. Por eso esta correccion actua a nivel de modelo.

## Cambios Tecnicos

- Nuevo modulo en `addons-extra/extrairg/irg_elearning_slide_onchange_bin_size`.
- Dependencias:
  - `website_slides`
  - `irg_elearning_child_bin_size_fix`
- Hereda `slide.slide`.
- Sobrescribe `onchange(self, values, field_name, field_onchange)`.
- Si el contexto ya trae `bin_size`, no lo modifica.
- Si no lo trae, llama al `super` con `self.with_context(bin_size=True)`.

## Uso

Instalar el modulo en la base afectada:

```bash
odoo -c /etc/odoo/odoo.conf -d <base_datos> -i irg_elearning_slide_onchange_bin_size --stop-after-init
```

Actualizarlo si ya esta instalado:

```bash
odoo -c /etc/odoo/odoo.conf -d <base_datos> -u irg_elearning_slide_onchange_bin_size --stop-after-init
```

## Validacion

Pruebas ejecutadas en local:

```bash
python3 addons-extra/extrairg/irg_elearning_slide_onchange_bin_size/tests/test_slide_onchange_bin_size.py
python3 -m compileall -q addons-extra/extrairg/irg_elearning_slide_onchange_bin_size
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d validation_slide_onchange_bin_size_20260605 \
  --stop-after-init \
  --init irg_elearning_slide_onchange_bin_size \
  --test-enable \
  --test-tags /irg_elearning_slide_onchange_bin_size \
  --log-level=test
```

Resultados:

- Test estatico: 1 test ejecutado, 0 fallos, 0 errores.
- Compilacion Python: sin errores.
- Odoo local: modulo cargado correctamente, 0 fallos, 0 errores.

## Limitaciones

Esta correccion evita que el `onchange` de `slide.slide` lea binarios completos cuando Odoo recalcula formularios. No reduce el tamano de los adjuntos ni reemplaza una politica de almacenamiento/limpieza de ficheros pesados.

Si tras instalar este modulo el error persistiera con otro modelo o campo, habria que revisar el nuevo traceback para identificar otra ruta de lectura binaria fuera de `slide.slide.onchange`.

## Changelog

- **2026-06-05:** creado modulo heredado para forzar `bin_size: True` en `slide.slide.onchange` y evitar `MemoryError` con registros virtuales `NewId origin` al editar batches en secciones iRG.
