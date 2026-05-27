# Micro-spec — Bootstrap HomeClass → Online en `irg_course_convocatorias`

**Fecha:** 2026-05-19
**Módulo principal:** `addons-extra/extrairg/irg_course_convocatorias`
**Módulo afectado (cambio menor):** `addons-extra/addons_uisep/irg_elearning_editable_sections`
**Versión objetivo:** `16.0.2.0.0`
**Responsable:** equipo iRG

## 1. Título
Rediseño de la acción "Copiar contenido de HomeClass" como bootstrap 1:1 desvinculado.

## 2. Resumen objetivo
Reescribir `action_copy_homeclass_to_online` para que genere copias HomeClass→Online estructuralmente independientes, sin modificar la pestaña HomeClass, respetando jerarquía y secciones iRG, y replicando quizzes asociados.

## 3. Motivo / justificación
La implementación anterior usaba `slide.slide.copy()` y disparaba recomputaciones de `website_slides` y los hooks `_apply_parent_hierarchy` / `_apply_parent_limitations` de `irg_elearning_editable_sections`. Resultado: la pestaña HomeClass parecía alterarse, parte del contenido se perdía por remapeo silencioso de FKs cuando el padre no entraba en el lote, y las secciones iRG vacías no se duplicaban. La operación es un bootstrap único (luego se edita libre), no una sincronización, así que el coste/beneficio de una rutina manual controlada es positivo.

## 4. Alcance exacto
- Modelo `slide.channel` (`irg_course_convocatorias/models/slide_channel.py`):
  - Reescritura completa de `action_copy_homeclass_to_online`.
  - Helpers nuevos: `_irg_bootstrap_notification`, `_irg_bootstrap_base_sequence`, `_irg_bootstrap_clone_irg_sections`, `_irg_bootstrap_slide_clone_fields`, `_irg_bootstrap_prepare_slide_values`, `_irg_bootstrap_remap_values`, `_irg_bootstrap_clone_quizzes`.
  - Eliminación de helpers obsoletos: `_irg_get_online_copy_sequence_map`, `_irg_copy_irg_sections_for_online`, `_irg_prepare_online_slide_copy_values`.
- Vista `irg_course_convocatorias/views/slide_channel_views.xml`: texto del `confirm` del botón.
- Manifest: subida de versión `16.0.1.4.0` → `16.0.2.0.0`.
- Tests: nueva carpeta `tests/` con `test_bootstrap_online.py` y `__init__.py`.
- Modelo `slide.slide` en `irg_elearning_editable_sections/models/slide_slide.py`: guardas para honrar el context flag `irg_skip_parent_propagation` en `create`, `write`, `_onchange_parent_slide_apply_limitations` y `_onchange_category_id_set_parent`. Sin cambios de manifest.

No se tocan controladores, modelos de matrícula, e-commerce, ni vistas portal.

## 5. Diseño técnico
- `action_copy_homeclass_to_online`:
  1. Selecciona slides HomeClass elegibles (`_irg_is_homeclass_content`).
  2. Activa contexto `irg_skip_parent_propagation=True`.
  3. Clona TODAS las `irg.slide.section` del canal mediante `_irg_bootstrap_clone_irg_sections`.
  4. Pase 1: `create()` en orden categorías → contenidos. La whitelist `_irg_bootstrap_slide_clone_fields` cubre los campos textuales/binarios estables de `slide.slide` (`name`, `description`, `slide_category`, `is_category`, `is_published`, `url`, `document_google_url`, `mime_type`, `datas`, `image_1920`, `html_content`, `video_url`, `embed_code`, `completion_time`, `quiz_*_reward`, `inherit_limitations_from_parent`, `scheduled_date`). Cada campo se verifica con `_fields` antes de leer. `access_token` se omite (se regenera). `tag_ids` se replica como `(6, 0, ids)`. `allowed_batch_ids` se vacía con `(5,)`. La secuencia se calcula como `base + (idx+1)*10` siendo `base` el máximo `sequence` actual de slides Online en el canal.
  5. Pase 2: `_irg_bootstrap_remap_values` calcula `category_id`, `parent_slide_id`, `irg_section_id` apuntando al mapa de copias. Si la referencia original no tiene copia, se deja vacía explícitamente.
  6. Pase 3: `_irg_bootstrap_clone_quizzes` replica `slide.question` (y sus `slide.answer`) por cada slide copiado, con whitelist defensiva.
  7. Notificación final con `_irg_bootstrap_notification`: `success` con conteo si hubo copias, `warning` si no había HomeClass elegible.
- `irg_elearning_editable_sections`:
  - `_onchange_parent_slide_apply_limitations` y `_onchange_category_id_set_parent`: `return` temprano si el context flag está activo.
  - `create` y `write`: si el flag está activo, se omite la llamada a `_apply_parent_hierarchy` y `_apply_parent_limitations`.

## 6. Dependencias
Sin cambios de `depends`. Se mantienen `website_slides`, `openeducat_core`, `irg_op_course_modality`, `isep_elearning_custom`, `irg_elearning_editable_sections`.

## 7. Backwards-compatibility / migración
- Compatible. No se altera ningún esquema de datos ni se rompen FKs.
- El contenido Online creado por la versión anterior permanece tal cual; las nuevas ejecuciones añaden bloques al final.
- El flag `irg_skip_parent_propagation` es opt-in vía contexto; cualquier flujo existente sin el flag conserva el comportamiento previo.

## 8. Casos de prueba / criterios de aceptación
Tests Odoo automatizados en `tests/test_bootstrap_online.py`:
- Las copias Online no comparten id con HomeClass y los slides HomeClass conservan su `sequence`.
- `category_id` y `parent_slide_id` en las copias apuntan a copias Online, no a originales.
- Todas las `irg.slide.section` del canal (también las vacías) se duplican.
- Canal sin contenido HomeClass: la acción devuelve notificación `warning` y no crea nada.
- Doble ejecución: el segundo lote duplica el conteo Online sin tocar el primero.

Validación manual recomendada en servidor:
- Curso real con jerarquía y quizzes: verificar quiz duplicado y contenido idéntico texto a texto.
- Comprobar que `allowed_batch_ids` queda vacío en las copias Online.

## 9. Rollback plan
1. `git revert` del commit asociado.
2. `docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <db> -u irg_course_convocatorias,irg_elearning_editable_sections --stop-after-init --db_host=pgodoo_latest`.
3. No hay migración de datos a deshacer.

## 10. Estimación y responsable
- Implementación: completada (sesión 2026-05-19).
- Responsable: equipo iRG.
