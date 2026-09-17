# Informe de actividad de campus (backend)

## Problema

El equipo académico necesita un informe de lo que los alumnos han hecho en el campus (e-learning, evaluaciones y libreta), más tres lecturas distintas de “curso finalizado”. Hasta ahora eso se sacaba con SQL de solo lectura a producción y un Excel ad hoc. No hay pantalla interna en Odoo.

El módulo OCA `auditlog` no aplica: registra create/write/delete, no el progreso de campus ni esas tres lecturas.

## Alcance (v1)

Módulo nuevo `irg_campus_activity_audit` en `addons-extra/extrairg/`. No se modifica ningún addon existente; el lote se extiende por herencia.

**Camino interno (principal):** desde la ficha (y Acción) de `op.batch` un usuario interno genera un XLSX con los alumnos matriculados en ese lote (`op.student.course`).

**Camino listado (opcional):** el mismo asistente admite un Excel de correos. Cruza contra el lote abierto; las filas del listado sin matrícula en ese lote van a la hoja “No encontrados”.

Fuera de alcance en v1: portal del alumno, OCA auditlog, foros, asistencia, tareas `op.assignment`, menú independiente sin lote, escritura en fichas de alumno.

## Flujo

1. Usuario interno con grupo Facultad (`openeducat_core.group_op_faculty`) abre un lote.
2. Pulsa **Informe de actividad** (cabecera o menú Acción).
3. El asistente trae el lote; opcionalmente sube un listado XLSX (columna `email` / `correo`; opcional `curso` / `codigo`).
4. Genera un adjunto temporal en el wizard (no público) y ofrece la descarga.
5. No crea ni escribe matrículas, canales, libretas ni logs de auditoría.

La autorización se comprueba en el servidor (`has_group`); la UI no basta. Tras ese control, la recopilación puede usar `sudo()` de solo lectura porque Facultad no siempre tiene ACL de e-learning/libreta y el informe debe ver los mismos hechos que el SQL anterior.

## Fuentes de datos

| Hoja / dato | Origen |
| --- | --- |
| Alumnos del lote | `op.student.course` del `batch_id` |
| Campus | `slide.channel.partner` (`batch_id`, `active`) y `slide.slide.partner` |
| Evaluaciones | `survey.user_input` ligado a `slide_id` del canal del lote |
| Libreta | `app.gradebook.student` / `subject` / `result` (partner + lote o curso) |
| Matrícula finalizada | `op.student.course.state == 'finished'` |
| Libreta 100 % | `op.student.course.completion_porc >= 100` (`isep_student_filter`: obligatorias con `final_subject_note >= 8`) |
| Campus completado | Hay ≥1 contenido publicado (no sección) en canales del lote del alumno y todos esos contenidos tienen `slide.slide.partner.completed` |

`completion_porc` es calculado, no almacenado y no admite `search`; se lee por ORM sobre las matrículas.

## Excel de salida

Hojas: Resumen alumnos, Progreso por asignatura, Actividades, Evaluaciones, Libreta alumnos, Libreta asignaturas, Libreta examenes, No encontrados (si hay listado), Metodologia.

El resumen incluye las tres columnas de finalización **separadas** (no se mezclan en un único sí/no).

Cruce de listado: email normalizado contra `res.partner.email` o `res.users.login`.

## Seguridad

- ACL del wizard: `openeducat_core.group_op_faculty`.
- `action_generate` lanza `AccessError` si el usuario no tiene ese grupo.
- El binario no es `public`.
- Sin cambios de autenticación, migraciones ni borrado histórico.

## Pruebas

`TransactionCase` post-install: acceso denegado, alumnos del lote, tres flags, actividades de campus, listado opcional, XLSX con hojas esperadas.

E2E TestSprite: obligatorio (vistas XML del wizard y botón en lote).
