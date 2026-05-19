# Changelog 2026-05-19 — Bootstrap HomeClass → Online (`irg_course_convocatorias`)

## Resumen
Se reescribe la acción "Copiar contenido de HomeClass" como bootstrap 1:1 desvinculado. Las copias HomeClass→Online ya no se basan en `slide.slide.copy()` y por tanto no afectan a la pestaña HomeClass ni pierden contenido por remapeos silenciosos.

## Cambios por módulo

### `addons-extra/extrairg/irg_course_convocatorias` (16.0.1.4.0 → 16.0.2.0.0)
- Reescritura completa de `action_copy_homeclass_to_online` en `models/slide_channel.py`.
- Nuevos helpers `_irg_bootstrap_notification`, `_irg_bootstrap_base_sequence`, `_irg_bootstrap_clone_irg_sections`, `_irg_bootstrap_slide_clone_fields`, `_irg_bootstrap_prepare_slide_values`, `_irg_bootstrap_remap_values`, `_irg_bootstrap_clone_quizzes`.
- Eliminados helpers obsoletos `_irg_get_online_copy_sequence_map`, `_irg_copy_irg_sections_for_online`, `_irg_prepare_online_slide_copy_values`.
- Clonación manual con `create()` en tres pases (categorías y contenidos, remapeo de jerarquía, replicación de quizzes).
- Se clonan TODAS las `irg.slide.section` del canal, no sólo las referenciadas.
- Las copias se añaden al final del listado Online; `allowed_batch_ids` se vacía deliberadamente.
- Activa `irg_skip_parent_propagation=True` durante la operación para suspender los hooks de `irg_elearning_editable_sections`.
- Texto del `confirm` del botón actualizado en `views/slide_channel_views.xml`.
- Manifest bump a `16.0.2.0.0`.
- Nueva carpeta `tests/` con `test_bootstrap_online.py` (5 escenarios).

### `addons-extra/addons_uisep/irg_elearning_editable_sections`
- `models/slide_slide.py`: `create`, `write`, `_onchange_parent_slide_apply_limitations` y `_onchange_category_id_set_parent` honran el context flag `irg_skip_parent_propagation`. Comportamiento por defecto sin cambios.
- Sin cambios de manifest.

## Documentación
- Actualizada: `doc/modules/extrairg/irg_course_convocatorias.md`.
- Creada/actualizada: `doc/modules/addons_uisep/irg_elearning_editable_sections.md`.
- Micro-spec: `doc/micro-specs/2026-05-19-irg_course_convocatorias_bootstrap.md`.

## Despliegue
```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <db> -u irg_course_convocatorias,irg_elearning_editable_sections \
    --stop-after-init --db_host=pgodoo_latest
```

## Notas
- Compatible con datos existentes. Sin migración.
- Si otro módulo añade un campo obligatorio nuevo en `slide.slide`, extender `_irg_bootstrap_slide_clone_fields()` por herencia.
