# irg_op_course_modality

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `openeducat_core`

---

## ¿Qué hace este módulo?

Añade al modelo `op.course` un catálogo multi-selección de modalidades académicas para indicar cómo puede impartirse un curso. El curso puede marcar una o varias modalidades simultáneamente, lo que permite representar escenarios mixtos como Presencial + Online o HomeClass + Online sin alterar la estructura base de OpenEduCat.

El módulo introduce un modelo auxiliar `irg.course.modality` para mantener el catálogo extensible y separa esta clasificación de la lógica operativa de `op.batch`. De este modo no rompe los flujos actuales de admisión, visibilidad de asignaturas, eLearning o generación de libretas, y deja preparado el dato maestro que futuros módulos podrán consumir para desbloqueos específicos de modalidad online.

## Funcionalidades principales

- Añade el campo `irg_modality_ids` en `op.course` como relación Many2many.
- Crea el modelo `irg.course.modality` para gestionar el catálogo de modalidades.
- Precarga tres modalidades base: `Presencial`, `HomeClass` y `Online`.
- Permite asignar varias modalidades al mismo curso desde backend.
- Muestra las modalidades en el formulario y en la vista árbol de cursos.
- Añade una pantalla de administración del catálogo bajo la configuración general de OpenEduCat.
- Incluye pruebas para datos semilla, asignación múltiple, persistencia y unicidad del código técnico.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.course.modality` | Nuevo | `name`, `code`, `sequence`, `active`, `course_ids` |
| `op.course` | Herencia | `irg_modality_ids` |

## Vistas y UI

- `views/op_course_views.xml` hereda `openeducat_core.view_op_course_form` y añade `irg_modality_ids` después de `code` con widget `many2many_tags`.
- `views/op_course_views.xml` hereda `openeducat_core.view_op_course_tree` y añade la columna de modalidades después de `evaluation_type`.
- `views/irg_course_modality_views.xml` define las vistas árbol y formulario de `irg.course.modality`.
- El catálogo de modalidades se publica con la acción `action_irg_course_modality` y el menú `menu_irg_course_modality` bajo `openeducat_core.menu_op_school_config_general`.

## Reglas de negocio

- Un curso puede tener cero, una o varias modalidades asignadas.
- Cada modalidad tiene un `code` técnico único para que otros módulos puedan apoyarse en reglas estables.
- El módulo no infiere automáticamente la modalidad desde el lote ni modifica `op.batch`.
- La modalidad `online` queda disponible para que otros módulos combinen este dato con la regla existente de lotes `ONL` excluyendo `MONL`.

## Compatibilidad con lógica activa

- No modifica modelos nativos ni sobrescribe métodos de negocio existentes de `op.course`.
- No altera la lógica ya desplegada en `irg_admission_auto_gradebook`, `irg_op_subject_visibility`, `irg_generacion_diplomas` ni `irg_online_subject_opening`.
- No interfiere con `op.modality` de `isep_student_migration`, ya que ese modelo sigue resolviendo la modalidad operativa del lote y no la del curso.
- El dato es aditivo: si ningún curso tiene modalidades configuradas, el sistema sigue funcionando como hasta ahora.

## Tests

El módulo incluye pruebas transaccionales en `tests/test_irg_op_course_modality.py`.

Casos cubiertos:

- Existencia de las tres modalidades semilla.
- Estado activo de los registros semilla.
- Creación de cursos sin modalidades.
- Asignación de una modalidad única.
- Asignación simultánea de varias modalidades.
- Persistencia del vínculo Many2many tras `write()`.
- Restricción de unicidad sobre `code`.

Para ejecutar las pruebas del módulo en una base local:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_op_course_modality \
    --test-tags /irg_op_course_modality \
    --stop-after-init --db_host=pgodoo_latest
```

## Seguridad

El módulo define `security/ir.model.access.csv` para `irg.course.modality`:

- `base.group_user`: lectura.
- `base.group_system`: lectura, escritura, creación y borrado.

No define record rules, controladores HTTP ni cron propio.

## Dependencias externas

- `openeducat_core`: aporta el modelo `op.course` y sus vistas base.

## Notas técnicas

- La relación Many2many usa la tabla intermedia `op_course_irg_modality_rel`.
- El campo en formulario usa tags para edición rápida desde la ficha del curso.
- El catálogo queda abierto a futuras ampliaciones sin necesidad de cambiar el esquema del curso.
- El módulo no usa `sudo()`, SQL directo, assets frontend ni automatismos programados.
- La lógica ONL/MONL no se duplica aquí; permanece en el módulo funcional que gestiona aperturas online de asignaturas.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_op_course_modality \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_op_course_modality \
    --stop-after-init --db_host=pgodoo_latest
```

## Operación

Una vez instalado, cada curso dispone del campo **Modalidades** para marcar una o varias opciones del catálogo. El uso operativo previsto es que los cursos con modalidad `Online` sirvan como bandera funcional para futuros módulos de eLearning, que además cruzarán esta información con la nomenclatura de lotes `ONL` y la excepción `MONL` ya existente en la lógica académica del proyecto.