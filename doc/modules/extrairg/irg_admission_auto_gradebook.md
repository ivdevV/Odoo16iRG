# irg_admission_auto_gradebook

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `openeducat_admission`, `isep_gradebook`

---

## ¿Qué hace este módulo?

Crea automáticamente la libreta de calificaciones del alumno cuando se confirma su matrícula (acción "Enroll Student" en la admisión, cuando el estado pasa a `done`). Sin este módulo, las libretas debían crearse manualmente.

El proceso es idempotente: si ya existe una libreta para la admisión, no crea duplicados.

## Funcionalidades principales

- Override del método `enroll_student` en `op.admission`.
- Verifica si el curso tiene habilitada la creación automática de libreta.
- Comprueba que no exista ya una libreta para la admisión (idempotente).
- Crea `app.gradebook.student` vinculado a la admisión.
- Puebla asignaturas según filtro del curso (solo obligatorias o todas).

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.admission` | Herencia | Lógica auto-creación de libreta |
| `op.course` | Herencia | Configuración de creación automática |

## Vistas y UI

- `views/op_course_views.xml` — checkbox de creación automática en el formulario de curso.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_admission_auto_gradebook \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_admission_auto_gradebook \
    --stop-after-init --db_host=pgodoo_latest
```
