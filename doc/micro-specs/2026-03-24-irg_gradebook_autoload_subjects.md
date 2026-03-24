# Micro-spec: irg_gradebook_autoload_subjects

**Fecha:** 2026-03-24  
**Módulo:** `irg_gradebook_autoload_subjects`  
**Versión:** 16.0.1.0.0  
**Estado:** En implementación

---

## 1. Problema

Al crear un `app.gradebook.student` (libreta de calificaciones), las asignaturas (`app.gradebook.subject`) se dejan vacías. El docente o administrador tiene que añadirlas manualmente una a una, aunque el curso ya tiene asignadas sus asignaturas en `op.course.subject_ids`.

## 2. Objetivo

Auto-poblar `gradebook_subject_ids` con las asignaturas de tipo `compulsory` definidas en `op.course.subject_ids` en el momento en que se crea la libreta, o cuando se cambia la admisión.

## 3. Módulos afectados

- `isep_gradebook` (base — no se modifica)
- **Nuevo:** `irg_gradebook_autoload_subjects` (herencia vía `_inherit`)

## 4. Modelos involucrados

| Modelo | Rol |
|---|---|
| `app.gradebook.student` | Modelo a extender con `_inherit` |
| `app.gradebook.subject` | Registros a crear automáticamente |
| `op.course` | Fuente de verdad de asignaturas (campo `subject_ids`) |
| `op.subject` | Asignaturas individuales (`subject_type = compulsory`) |

## 5. Lógica de negocio

1. Al hacer `create()` de `app.gradebook.student`, tras llamar `super()`, se invoca `_autoload_subjects()`.
2. Al hacer `write()` con cambio en `admission_id` (que implica posible cambio de `course_id`), idem.
3. `_autoload_subjects()` calcula las asignaturas del curso que son `compulsory` y que **no** están ya en `gradebook_subject_ids`, y las crea.
4. Nunca elimina asignaturas existentes (política conservadora: preserva notas ya registradas).

## 6. Restricciones y decisiones

- Solo asignaturas `compulsory`. Las electivas se añaden manualmente.
- No se gestiona el caso de "añadir asignatura al curso después de crear las libretas" (requeriría un wizard batch separado).
- No se necesita `ir.model.access.csv` (sin modelos nuevos).
- No hay SQL directo ni `sudo()` (opera en el contexto del usuario que crea la libreta).

## 7. Criterios de aceptación

- [ ] Crear un `app.gradebook.student` nuevo → `gradebook_subject_ids` se llena con asignaturas compulsory del curso.
- [ ] Crear una libreta cuyo curso no tiene asignaturas → no falla, lista vacía.
- [ ] Cambiar `admission_id` a otra admisión de curso diferente → se añaden las asignaturas del nuevo curso.
- [ ] No duplica asignaturas si ya existen.
- [ ] Asignaturas electivas no aparecen automaticamente.

## 8. Archivos del módulo

```
addons-extra/extrairg/irg_gradebook_autoload_subjects/
├── __manifest__.py
├── __init__.py
└── models/
    ├── __init__.py
    └── app_gradebook_student.py
```
