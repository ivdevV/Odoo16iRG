# irg_course_portal_tiles_diplomado_hide

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `irg_course_portal_tiles`, `openeducat_core`, `product`

---

## ¿Qué hace este módulo?

Este módulo oculta las tarjetas (tiles) de acceso a **TFM** (Trabajo Fin de Máster) y **Prácticas** en el portal de cursos para aquellos estudiantes que estén matriculados en cursos de tipo **Diplomado**. Esto evita que los estudiantes de Diplomados visualicen accesos a secciones académicas que no aplican a su plan de estudios.

## Funcionalidades principales

El módulo implementa las siguientes adaptaciones en Odoo 16:

1. **Método Helper `is_diplomado()` en `op.course`**:
   Añade una función en el modelo de cursos para determinar si un curso es un Diplomado basándose en los siguientes criterios de búsqueda e inspección:
   - Si el código del curso (`code`) comienza por "DI" (sin distinguir mayúsculas/minúsculas).
   - Si el tipo de curso (`course_type_id`) tiene un código que comienza con "DI" o "D", o si su nombre contiene la palabra "DIPLOMADO".
   - Si la plantilla de producto vinculada (`product_template_id` o `product_template_ids`) contiene "DIPLOMADO" en su nombre.
   - Si la categoría del producto (`categ_id`) de las plantillas vinculadas tiene un código que empieza por "DI" o "D", o su nombre contiene "DIPLOMADO".

2. **Ocultación de Tiles en QWeb (Frontend)**:
   Hereda la plantilla `irg_course_portal_tiles.irg_user_profile_content_details_inherit` y mediante expresiones XPath añade el atributo condicional `t-if="not course_id.is_diplomado()"` a los contenedores HTML de los botones de Prácticas y TFM.

3. **Restricción de Acceso Directo por Controlador (Seguridad)**:
   Invalida el acceso directo por URL a la página del TFM (`/campus/course/<int:course_id>/tfm`). Si un usuario intenta forzar la navegación web hacia esa dirección y el curso evaluado es de tipo Diplomado, el sistema interrumpe la petición devolviendo una pantalla de acceso denegado (HTTP 403 Forbidden - `website.403`).

## Vistas y UI

- `views/irg_course_portal_tiles_views.xml`: Contiene la plantilla QWeb `irg_user_profile_content_details_diplomado_hide` que aplica los cambios visuales sobre el portal de curso del estudiante.

## Pruebas y Validación

El módulo cuenta con un conjunto completo de pruebas unitarias integradas en `tests/test_course_diplomado.py`. La clase `TestCourseDiplomado` valida el comportamiento del método `is_diplomado()` bajo múltiples escenarios:

* `test_01_course_code_starts_with_di`: Verifica la detección basada en el código del curso (case-insensitive).
* `test_02_course_type_conditions`: Valida la detección basada en la configuración del modelo de tipo de curso (`op.course.type`).
* `test_03_product_template_name_contains_diplomado`: Asegura que se clasifiquen correctamente los cursos cuyos productos de venta asociados contienen "DIPLOMADO" en el nombre.
* `test_04_product_template_category_conditions`: Evalúa la detección basada en el código o nombre de la categoría del producto.
* `test_05_normal_course`: Confirma que un curso convencional (ej. Máster) no se clasifica erróneamente como un Diplomado.

### Comando de ejecución de pruebas

Para ejecutar las pruebas del módulo en el entorno de validación dockerizado, utilice el siguiente comando:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_course_portal_tiles_diplomado_hide --test-enable --stop-after-init --log-level=test
```

## Instalación / Actualización

### Instalación desde cero

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d <dbname> \
  -i irg_course_portal_tiles_diplomado_hide --stop-after-init
```

### Actualización

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d <dbname> \
  -u irg_course_portal_tiles_diplomado_hide --stop-after-init
```

---

## Flujo de Trabajo y Cumplimiento (AGENTS.md)

De acuerdo con la política establecida en `AGENTS.md`, este módulo ha sido desarrollado siguiendo estrictamente las cuatro fases requeridas:
1. **Plan**: Se analizó la estructura del portal y las necesidades de filtrado para alumnos de Diplomado.
2. **Implementación**: Se extendió el modelo `op.course`, el controlador de portal y se aplicaron las expresiones XPath sobre la plantilla QWeb.
3. **Validación**: Se crearon casos de prueba unitaria en `tests/test_course_diplomado.py` y se ejecutaron con éxito a través del framework de pruebas de Odoo.
4. **Documentación**: Generación de esta ficha técnica y creación del archivo de registro de cambios (Changelog) en la raíz del proyecto.
