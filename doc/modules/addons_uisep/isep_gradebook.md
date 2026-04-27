# isep_gradebook

**Categoría:** addons_uisep
**Versión:** 16.0.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `website_slides`, `isep_elearning_custom`, `openeducat_core`, `openeducat_admission`, `survey`, `isep_survey`

---

## ¿Qué hace este módulo?

Implementa el sistema de libretas de calificaciones académicas. Cada alumno tiene una libreta vinculada a su admisión que contiene sus asignaturas con notas por tipo de actividad (examen, asignación, interacción, foro). Permite a docentes y administradores gestionar notas académicas de forma centralizada.

## Funcionalidades principales

- Modelo de libreta de calificaciones por alumno y admisión.
- Modelo de asignatura dentro de la libreta con notas por categoría.
- Cálculo automático de nota final de asignatura.
- Cálculo del promedio global de la libreta.
- Vistas de gestión para docentes y administradores.
- Acceso desde el backend y desde la ficha del alumno.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `app.gradebook` (nuevo) | Nuevo | Alumno, admisión, año académico |
| `app.gradebook.student` (nuevo) | Nuevo | Libreta del alumno, lista de asignaturas |
| `app.gradebook.subject` (nuevo) | Nuevo | Asignatura, notas por categoría, nota final |

## Vistas y UI

- Formulario de libreta con lista de asignaturas y notas.
- Vista de libreta desde la ficha del alumno.
- Menú de libretas en el backend.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_gradebook \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_gradebook \
    --stop-after-init --db_host=pgodoo_latest
```
