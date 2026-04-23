# Módulos: community-16

Carpeta con los módulos base de **OpenEduCat Community v16** — el paquete de gestión académica open-source sobre el que está construida la plataforma ISEP/IRG.

Estos módulos son de terceros (OpenEduCat) y no deben modificarse directamente. Todas las personalizaciones se hacen mediante `_inherit` en los módulos `isep_openeducat_*` e `irg_*`.

---

## Módulos OpenEduCat Community

| Módulo | Descripción | Modelos principales | Estado |
|--------|-------------|---------------------|--------|
| openeducat_core | Núcleo de OpenEduCat: estudiantes, cursos, asignaturas, lotes | `op.student`, `op.course`, `op.subject`, `op.batch` | Instalable |
| openeducat_admission | Gestión de admisiones y matrículas | `op.admission`, `op.admission.register` | Instalable |
| openeducat_assignment | Tareas y entregas de alumnos | `op.assignment`, `op.assignment.submission` | Instalable |
| openeducat_attendance | Control de asistencia | `op.attendance`, `op.attendance.line` | Instalable |
| openeducat_classroom | Gestión de aulas | `op.classroom` | Instalable |
| openeducat_activity | Actividades académicas | `op.activity` | Instalable |
| openeducat_erp | Integración ERP de OpenEduCat | Varios | Instalable |
| openeducat_exam | Gestión de exámenes | `op.exam`, `op.exam.attendees` | Instalable |
| openeducat_facility | Gestión de instalaciones | `op.facility` | Instalable |
| openeducat_fees | Gestión de tasas y pagos académicos | `op.fees.terms`, `op.fees.terms.line` | Instalable |
| openeducat_library | Gestión de biblioteca | `op.library` | Instalable |
| openeducat_parent | Gestión de tutores/padres | `op.parent` | Instalable |
| openeducat_timetable | Horarios y sesiones académicas | `op.timetable`, `op.session` | Instalable |
| web_openeducat | Componentes web de OpenEduCat | — | Instalable |

---

## Notas de instalación

Los módulos de OpenEduCat Community deben instalarse **antes** que los módulos `isep_*` e `irg_*` que los heredan. El orden de instalación recomendado es:

1. `openeducat_core`
2. `openeducat_admission`
3. `openeducat_timetable`
4. Resto de módulos OpenEduCat
5. Módulos `isep_openeducat_*`
6. Módulos `isep_*` e `irg_*`
