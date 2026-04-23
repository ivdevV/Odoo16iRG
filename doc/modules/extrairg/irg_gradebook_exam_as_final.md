# irg_gradebook_exam_as_final

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_gradebook`

---

## ¿Qué hace este módulo?

Sobrescribe el cálculo de la nota final de asignatura en la libreta para que la nota final sea únicamente la nota del examen registrado (o el promedio de exámenes si hay varios). Las categorías de asignación, interacción y foro no influyen en la nota final con este módulo instalado.

## Funcionalidades principales

- Override del campo computado `final_subject_note` en `app.gradebook.subject`.
- La nota final = nota del examen (o promedio de exámenes).
- Las actividades de asignación, interacción y foro no puntúan.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `app.gradebook.subject` | Herencia | Override de `final_subject_note` |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_gradebook_exam_as_final \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_gradebook_exam_as_final \
    --stop-after-init --db_host=pgodoo_latest
```
