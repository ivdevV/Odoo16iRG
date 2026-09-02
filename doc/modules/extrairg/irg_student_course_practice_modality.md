# irg_student_course_practice_modality

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Depende de:** `openeducat_core`, `isep_practices_2`, `irg_practice_center_type_modalities`, `isep_website_custom`, `openeducat_core_enterprise`

---

## Qué hace

Guarda la **modalidad de prácticas** (no la académica HomeClass/Online) en cada matrícula (`op.student.course.irg_practice_center_type_id`) y la muestra en backend y campus.

No es `irg_content_modality`. El Many2one apunta a `practice.center.type`.

## Comportamiento

- Al crear o escribir `practice.request`, si hay alguna solicitud de esa matrícula en `approved`, `progress` o `end`, se copia el `practice_center_type_id` de la más reciente (`request_date desc, id desc`).
- Borrador, asignado o rechazado no copian ni borran el valor.
- Secretaría puede editar el campo en el formulario/árbol de `op.student.course`. Ese valor rige hasta que una solicitud posterior en estado de sync vuelva a copiar.
- Campus: línea «Prácticas: … / Pendiente de seleccionar» bajo el nombre del curso.
- Portal educativo OpenEduCat: columna en la tabla de matrículas.

`practice.request.course_id` es `op.student.course`, no `op.course`.

## Instalación

Instalar este módulo **antes** de `irg_practice_slide_restrictions`.

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
    odoo -c /etc/odoo/odoo.conf -d <db> \
    -i irg_student_course_practice_modality \
    --stop-after-init
```

## Pruebas

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
    odoo -c /etc/odoo/odoo.conf -d <db_test> \
    -u irg_student_course_practice_modality \
    --test-enable --test-tags /irg_student_course_practice_modality \
    --stop-after-init --workers=0 --http-port=18069 --log-level=test
```

## Limitaciones

- Un alumno con dos matrículas tiene una modalidad por curso; no hay valor global.
- El portal no ofrece selector; solo lectura.
