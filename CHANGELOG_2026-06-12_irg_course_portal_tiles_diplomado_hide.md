# Registro de Cambios - irg_course_portal_tiles_diplomado_hide (2026-06-12)

Este documento contiene el resumen de cambios, pruebas superadas y archivos añadidos durante el desarrollo del módulo `irg_course_portal_tiles_diplomado_hide` para Odoo 16.

---

## Archivos Añadidos

### Código y Vistas del Módulo:
* `addons-extra/extrairg/irg_course_portal_tiles_diplomado_hide/__init__.py`
* `addons-extra/extrairg/irg_course_portal_tiles_diplomado_hide/__manifest__.py`
* `addons-extra/extrairg/irg_course_portal_tiles_diplomado_hide/controllers/__init__.py`
* `addons-extra/extrairg/irg_course_portal_tiles_diplomado_hide/controllers/main.py`
* `addons-extra/extrairg/irg_course_portal_tiles_diplomado_hide/models/__init__.py`
* `addons-extra/extrairg/irg_course_portal_tiles_diplomado_hide/models/op_course.py`
* `addons-extra/extrairg/irg_course_portal_tiles_diplomado_hide/tests/__init__.py`
* `addons-extra/extrairg/irg_course_portal_tiles_diplomado_hide/tests/test_course_diplomado.py`
* `addons-extra/extrairg/irg_course_portal_tiles_diplomado_hide/views/irg_course_portal_tiles_views.xml`

### Documentación del Proyecto:
* `doc/modules/extrairg/irg_course_portal_tiles_diplomado_hide.md` (Ficha técnica y manual del módulo)
* `CHANGELOG_2026-06-12_irg_course_portal_tiles_diplomado_hide.md` (Este archivo)

---

## Resumen de Cambios

1. **Estructura base del módulo**:
   * Creación del manifiesto y la configuración inicial con dependencias a `irg_course_portal_tiles`, `openeducat_core` y `product`.

2. **Cálculo e identificación de Diplomados**:
   * Adición del método `is_diplomado()` en `op.course` para comprobar si el curso, su tipo, su producto asociado o la categoría de su producto corresponden a un Diplomado (buscando códigos que inician por 'DI' o 'D', o textos que contienen 'DIPLOMADO' de forma case-insensitive).

3. **Ocultación de Tiles en Portal**:
   * Modificación de la UI del portal por medio de XPath para ocultar las tarjetas de TFM y Prácticas si `course_id.is_diplomado()` es verdadero.

4. **Bloqueo de seguridad de rutas**:
   * Sobrescritura del controlador `IrgTFMController` en `IrgTFMControllerDiplomado` para denegar peticiones HTTP a `/campus/course/<id>/tfm` retornando error 403 en caso de que el estudiante pertenezca a un Diplomado.

---

## Pruebas Superadas

Se han ejecutado y superado las pruebas automáticas contenidas en `tests/test_course_diplomado.py`. Los siguientes casos han sido validados con éxito:
* **Detección por código de curso**: Verificación de códigos que inician con `DI`/`di` (`test_01_course_code_starts_with_di`).
* **Detección por tipo de curso**: Validación basada en el código (empieza por `DI` o `D`) o nombre del tipo de curso (`test_02_course_type_conditions`).
* **Detección por nombre de producto**: Validación de presencia del término "DIPLOMADO" en la plantilla del producto del curso (`test_03_product_template_name_contains_diplomado`).
* **Detección por categoría del producto**: Validación basada en el código o nombre de la categoría del producto (`test_04_product_template_category_conditions`).
* **Cursos estándar**: Validación de que cursos no correspondientes a Diplomados (ej: programas de Máster estándar) no sufran ocultación ni restricciones de acceso (`test_05_normal_course`).

### Comando de ejecución de pruebas:
```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_course_portal_tiles_diplomado_hide --test-enable --stop-after-init --log-level=test
```
* **Resultado del test**: `0 failed, 0 error(s)` (Pruebas pasadas correctamente).
