# irg_elearning_slide_onchange_bin_size

## Descripcion

`irg_elearning_slide_onchange_bin_size` fuerza `bin_size: True` durante los `onchange` de `slide.slide` y `slide.channel` para evitar que Odoo lea adjuntos binarios completos al recalcular formularios de eLearning.

Este modulo complementa las correcciones de vista aplicadas en `irg_elearning_editable_sections`, `irg_course_convocatorias_v2` e `irg_elearning_child_bin_size_fix`.

## Problema Corregido

Al editar batches en secciones iRG, Odoo puede crear registros virtuales de formulario como `slide.slide(<NewId origin=3742>)`. Durante la ejecución del método `onchange`, Odoo construye un snapshot de la base de datos para simular los cambios. Este proceso lee todos los campos del modelo, incluidos los campos binarios relacionados (incluso si no son visibles en el formulario) como `binary_content`, `image_binary_content`, `document_binary_content`, `datas` e `image_1920`.

El acceso a estos campos relacionados evalúa la propiedad `datas` de `ir.attachment`, cargando el archivo adjunto completo en memoria. En producción con adjuntos grandes, esta lectura consume toda la memoria disponible del worker de Odoo, desencadenando un error de tipo `MemoryError`.

Aunque `bin_size: True` esté configurado en campos `x2many`, ese contexto puede no llegar a todas las llamadas de `onchange` del propio `slide.slide`. Por tanto, esta corrección actúa a nivel de modelo interceptando la carga del campo.

## Cambios Tecnicos

- **Nuevo módulo** en `addons-extra/extrairg/irg_elearning_slide_onchange_bin_size`.
- **Dependencias**:
  - `website_slides`
  - `irg_elearning_child_bin_size_fix`
- **Hereda `slide.slide`**:
  - Sobrescribe `onchange(self, values, field_name, field_onchange)`.
  - Introduce el flag de contexto `irg_in_onchange=True` y llama al `super` inyectando `bin_size=True` si no está presente.
  - Sobrescribe el método `_compute_field_value(self, field)` para interceptar la computación de campos binarios durante el `onchange`. Si el contexto contiene `irg_in_onchange=True` y el campo pertenece a `BINARY_FIELD_ONCHANGE_NAMES` (`binary_content`, `image_binary_content`, `document_binary_content`, `datas`, `image_1920`), Odoo guarda `False` en la caché (`self.env.cache.set(record, field, False)`) y retorna de inmediato sin acceder a `ir.attachment` ni evaluar la relación.
  - Filtra una copia de `field_onchange` antes del `super` para retirar campos binarios de `slide.slide` cuando lleguen como claves directas o rutas con punto, por ejemplo `child_slide_ids.binary_content`.
- **Hereda `slide.channel`** y aplica el mismo contexto `bin_size=True` e `irg_in_onchange=True` durante su `onchange`.
  - En `slide.channel`, filtra una copia de `field_onchange` solo para rutas hijas bajo relaciones de slides/secciones (`slide_ids`, `irg_native_section_ids`, `irg_online_slide_ids`, `irg_online_section_ids`) cuyo último segmento sea binario. No elimina `image_1920` propio de `slide.channel`.
- **Autodescubrimiento y ejecución de pruebas (Test Discovery & Integration Tests)**:
  - Añadido `from . import tests` en el archivo raíz `__init__.py` del módulo y `from . import test_slide_onchange_bin_size` en `tests/__init__.py` para habilitar el autodescubrimiento nativo de Odoo.
  - Refactorizado `tests/test_slide_onchange_bin_size.py` utilizando importaciones condicionales (`odoo.tests.common` protegida bajo `try/except`). Esto permite ejecutar las pruebas tanto de forma estática en el host (sin entorno Odoo local) como pruebas de integración integrales en la base de datos de Odoo usando el contenedor Docker.

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

- Test estatico 2026-06-08: 5 tests ejecutados, 0 fallos, 0 errores.
- Compilacion Python 2026-06-08: sin errores.
- Odoo local 2026-06-08: no ejecutado porque el daemon Docker local no estaba disponible (`Cannot connect to the Docker daemon`).

## Limitaciones

Esta correccion evita que los `onchange` de `slide.slide` y `slide.channel` lean binarios completos cuando Odoo recalcula formularios. No reduce el tamano de los adjuntos ni reemplaza una politica de almacenamiento/limpieza de ficheros pesados.

Si tras instalar este modulo el error persistiera con otro modelo o campo, habria que revisar el nuevo traceback para identificar otra ruta de lectura binaria fuera de `slide.slide.onchange`.

## Changelog

- **2026-06-08 (bugfix):**
  - Implementada intercepción en `_compute_field_value` de `slide.slide` usando el flag de contexto `irg_in_onchange=True` para cachear `False` y evitar la evaluación de campos binarios en `onchange`, previniendo errores de `MemoryError` por carga de adjuntos completos.
  - Habilitado el autodescubrimiento de pruebas de Odoo importando el submódulo `tests` en los paquetes `__init__.py`.
  - Refactorizado `test_slide_onchange_bin_size.py` con imports condicionales para dar soporte a ejecuciones estáticas en local y pruebas de integración en el entorno de pruebas de Odoo.
- **2026-06-08:** anadida cobertura acotada de `slide.channel.onchange` para evitar lecturas binarias al recalcular relaciones de slides/secciones (`slide_ids`, `irg_native_section_ids`, `irg_online_slide_ids`, `irg_online_section_ids`).
- **2026-06-08:** filtrado preventivo de `field_onchange` para excluir campos binarios (`binary_content`, `image_binary_content`, `document_binary_content`, `datas`, `image_1920`) antes de que Odoo cree el snapshot del `onchange`.
- **2026-06-05:** creado modulo heredado para forzar `bin_size: True` en `slide.slide.onchange` y evitar `MemoryError` con registros virtuales `NewId origin` al editar batches en secciones iRG.
