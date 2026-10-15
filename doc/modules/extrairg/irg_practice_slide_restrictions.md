# irg_practice_slide_restrictions

**Categoría:** extrairg
**Versión:** 16.0.1.2.0
**Licencia:** LGPL-3
**Depende de:** `irg_student_course_practice_modality`, `irg_elearning_editable_sections`, `isep_elearning_custom`, `irg_batch_slide_restrictions`

---

## Qué hace

Restringe secciones nativas de eLearning (`slide.slide` categoría e hijos) según la modalidad de prácticas de la matrícula del alumno.

Vacío = visible para todos. Con valor = solo si `enrollment.irg_practice_center_type_id.type_of_practice` coincide.

## Cómo etiquetar

Staff lo pone en las secciones del canal de prácticas de cada curso, campo **Modalidad de prácticas requerida**, junto a los lotes. Aparece en la pestaña **Secciones iRG** (lista y formulario) y en el formulario de contenido. No hace falta un flag «es asignatura de prácticas».

## Autorización

- El GET `/slides/slide/<id>` bloquea en servidor. Público con requisito → login. Alumno no autorizado → página «Contenido Bloqueado».
- La comprobación va **antes** de `super().slide_view()` para no entregar el documento ni registrar `action_set_viewed()`.
- QWeb oculta secciones y filas del sidebar; no sustituye el GET. Las condiciones de lote se conservan (`and`).
- Un hijo dentro de una sección etiquetada queda restringido aunque su propio campo esté vacío. El flag `inherit_limitations_from_parent` solo **copia** el valor al hijo.

## Resolución curso ↔ canal

Si el canal visto tiene `irg_homeclass_channel_id` (clon online), la resolución
usa el **canal maestro**; si no, el propio canal. Soft-check: sin ese campo, sin cambio.

1. `slide.channel.op_subject_ids` → `op.subject.course_id`
2. `op.course.subject_ids` que contienen esas asignaturas
3. `op.course.slide_channel_ids` que contienen el canal de resolución

Si un canal resuelve varios cursos, basta que **alguna** matrícula coincida.

Los clones online no enlazan asignaturas propias (`op_subject_ids` vacío); sin el
salto al maestro, las secciones con modalidad requerida quedarían siempre ocultas.

## Instalación

Después del módulo A:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
    odoo -c /etc/odoo/odoo.conf -d <db> \
    -i irg_practice_slide_restrictions \
    --stop-after-init
```

## Pruebas

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
    odoo -c /etc/odoo/odoo.conf -d <db_test> \
    -u irg_practice_slide_restrictions \
    --test-enable --test-tags /irg_practice_slide_restrictions \
    --stop-after-init --workers=0 --http-port=18069 --log-level=test
```

Al crear canales en tests, `category_id` de Moodle solo se rellena si el modelo existe; el parche de credenciales Moodle es opcional.

## Limitaciones

- Canal compartido entre cursos: se admite si alguna matrícula coincide.
- Alumnos sin modalidad no ven secciones etiquetadas.
- No clona canales ni mezcla con `irg_content_modality`.
- En clon, solo se consultan cursos del maestro (no se unen enlaces directos del clon vía `slide_channel_ids`); en producción los clones no llevan esos enlaces.
