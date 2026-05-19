# irg_elearning_editable_sections

**Categoría:** addons_uisep
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `website_slides`, `irg_batch_slide_restrictions`, `irg_elearning_scheduled`

---

## ¿Qué hace este módulo?

Añade al backoffice de eLearning de Odoo una capa de organización editable para los contenidos de un curso (`slide.channel`). Aporta tres piezas complementarias:

- un modelo nuevo `irg.slide.section` para definir secciones iRG por curso, independientes de las "categorías" nativas de `website_slides`,
- una relación `parent_slide_id`/`child_slide_ids` en `slide.slide` para construir jerarquías padre/hijo dentro del mismo canal,
- un mecanismo de **herencia de límites** desde el padre (lotes permitidos y fecha programada), pensado para que un contenido hijo respete por defecto las restricciones de su padre sin tener que reescribirlas a mano.

El módulo es base estructural de la organización académica del workspace y lo consumen, entre otros, `irg_course_convocatorias` (pestañas HomeClass/Online y bootstrap Online), las vistas modernas del aula y los flujos de visibilidad por lote (`irg_batch_slide_restrictions`).

## Funcionalidades principales

- Modelo `irg.slide.section` con `name`, `sequence`, `active`, `channel_id`, `slide_ids` y `slide_count`.
- Acción `action_open_slides` en la sección iRG para abrir la lista filtrada de contenidos del curso con el contexto preconfigurado.
- Herencia de `slide.slide`:
  - campo `irg_section_id` (`ondelete='set null'`) que vincula contenido a sección iRG;
  - campo `parent_slide_id` con dominio al mismo canal y excluyendo el propio registro;
  - relación inversa `child_slide_ids`;
  - flag `inherit_limitations_from_parent` (activo por defecto).
- Onchange `_onchange_parent_slide_apply_limitations`: cuando el padre es categoría, asigna `category_id`; si no, hereda la categoría del padre; si `inherit_limitations_from_parent` está activo, copia `allowed_batch_ids` y `scheduled_date` cuando el hijo los tiene vacíos.
- Onchange `_onchange_category_id_set_parent`: cuando se asigna una categoría, alinea `parent_slide_id` con ella.
- Hooks `_apply_parent_hierarchy` y `_apply_parent_limitations` ejecutados desde `create()` y `write()` para mantener la jerarquía y los límites coherentes incluso cuando los registros se crean por código.
- Constraint `_check_irg_section_channel`: una sección iRG sólo puede asociarse a contenidos del mismo `channel_id`.
- Herencia de `slide.channel`:
  - `irg_section_ids` (one2many a `irg.slide.section` por canal);
  - `irg_native_section_ids` (one2many técnico a `slide.slide` filtrado por `is_category=True`, usado como ancla por otras vistas).

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.slide.section` | Nuevo | `name`, `sequence`, `active`, `channel_id`, `slide_ids`, `slide_count` |
| `slide.slide` | Herencia | `irg_section_id`, `parent_slide_id`, `child_slide_ids`, `inherit_limitations_from_parent` |
| `slide.channel` | Herencia | `irg_section_ids`, `irg_native_section_ids` |

## Soporte del context flag `irg_skip_parent_propagation`

Para permitir que módulos consumidores ejecuten operaciones de clonación o migración sin que los hooks reescriban automáticamente la jerarquía, los siguientes puntos respetan el flag de contexto `irg_skip_parent_propagation`:

- `_onchange_parent_slide_apply_limitations` y `_onchange_category_id_set_parent` regresan sin hacer nada cuando el flag está activo.
- `create()` no ejecuta `_apply_parent_hierarchy` ni `_apply_parent_limitations` cuando el flag está activo.
- `write()` omite la reaplicación de jerarquía y límites cuando el flag está activo, aunque se modifiquen `parent_slide_id`, `category_id` o `inherit_limitations_from_parent`.

El comportamiento por defecto, sin flag, es idéntico al anterior: los onchange y hooks siguen aplicándose y propagando categoría, lotes permitidos y fecha programada.

El consumidor principal de este flag es `irg_course_convocatorias`, que lo activa durante el bootstrap HomeClass -> Online (`action_copy_homeclass_to_online`) para que la clonación pueda crear contenidos con `parent_slide_id`, `category_id` e `irg_section_id` controlados manualmente, sin que los hooks de este módulo los sobrescriban.

## Vistas y UI

- `views/slide_channel_view.xml`: integra la pestaña `Secciones iRG` (`name="irg_sections"`) sobre el formulario del canal, ancla XPath usada por `irg_course_convocatorias`.
- `views/slide_slide_view.xml`: añade los campos `irg_section_id`, `parent_slide_id`, `inherit_limitations_from_parent` y la lista de hijos al formulario y árbol de `slide.slide`.
- `views/slide_slide_search_view.xml`: añade filtros y agrupaciones por sección iRG y padre.
- `views/website_slides_section_visibility.xml`: ajustes de visibilidad para que las secciones iRG se integren correctamente con la presentación frontend.

## Seguridad

- `security/ir.model.access.csv` define accesos al nuevo modelo `irg.slide.section` para `base.group_user`.
- No se introducen `sudo()` adicionales fuera de los hooks de jerarquía, donde se usa `parent_slide_id.sudo()` para leer atributos del padre con independencia de las reglas de acceso del hijo.

## Dependencias externas

- `website_slides`: aporta `slide.channel` y `slide.slide`, sobre los que se construye toda la jerarquía editable.
- `irg_batch_slide_restrictions`: aporta `allowed_batch_ids` en `slide.slide`, que este módulo propaga desde el padre.
- `irg_elearning_scheduled`: aporta `scheduled_date` en `slide.slide`, también propagado desde el padre.

## Riesgos y notas técnicas

- Los hooks `_apply_parent_hierarchy` y `_apply_parent_limitations` se ejecutan en `create()`/`write()`; cualquier flujo que cree o actualice slides en masa y necesite control fino debe activar `irg_skip_parent_propagation=True` en el contexto.
- La constraint `_check_irg_section_channel` garantiza coherencia de canal, pero requiere que el `channel_id` esté presente antes de asignar `irg_section_id`.
- La página `name="irg_sections"` es un ancla XPath estable consumida por otros módulos (`irg_course_convocatorias`); cambiarla rompería esos consumidores.
- Sin endpoints HTTP, crons ni SQL raw.

## Historial reciente

- **16.0.1.0.0:** versión base con `irg.slide.section`, `parent_slide_id`, herencia de límites y pestaña `Secciones iRG`.
- **Cambio menor compatible:** se añade soporte para el context flag `irg_skip_parent_propagation` en los hooks `_apply_parent_hierarchy`, `_apply_parent_limitations` y en los onchange `_onchange_parent_slide_apply_limitations` y `_onchange_category_id_set_parent`. Cuando el flag está activo, los hooks se omiten; cuando no, el comportamiento es idéntico al anterior. El módulo `irg_course_convocatorias` (16.0.2.0.0) utiliza este flag durante el bootstrap HomeClass -> Online para evitar reescrituras automáticas sobre las copias Online. El manifest del módulo `irg_elearning_editable_sections` no cambia.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_elearning_editable_sections \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_elearning_editable_sections \
    --stop-after-init --db_host=pgodoo_latest
```
