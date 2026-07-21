# irg_admission_auto_gradebook_templates

## Qué hace

Tras crear la libreta automática en `enroll_student`, asigna `gradebook_id` en la cabecera si está vacío:

1. Conserva el de `course.gradebook_id` (ya rellenado por compute editable).
2. Si falta y es diplomado → `gradebook_diploma_exam_50_50`.
3. Si falta y es máster → `Solo Examen` (xml_id del módulo o búsqueda por nombre).
4. Otros cursos: sin plantilla.

No fuerza plantilla en líneas de asignatura.

## Instalación

Instalar `irg_admission_auto_gradebook_templates` (trae auto-gradebook, editable template y plantillas de diplomado).

## Pruebas

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d <db_test> \
  -i irg_admission_auto_gradebook_templates --test-enable \
  --test-tags=/irg_admission_auto_gradebook_templates --stop-after-init \
  --http-port=8099 --log-level=test
```
