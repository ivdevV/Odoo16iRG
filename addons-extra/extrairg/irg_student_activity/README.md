# irg_student_activity

Pestaña **Actividad** en la ficha de alumno (`op.student`) para Facultad:
historial cronológico de contenidos de campus y evaluaciones, con export CSV.

## Uso

1. Abrir un alumno.
2. Pestaña **Actividad** (tras **Acceso**); en edición puede verse vacía hasta
   guardar el contacto (partner) del alumno.
3. Revisar la tabla (máx. 500 eventos recientes).
4. **Exportar CSV** si hace falta.

## Permisos

Grupo `Facultad` (`openeducat_core.group_op_faculty`). La UI no basta: el
servidor comprueba el grupo en lectura y export.

## Fuera de alcance

Libreta, logins, Moodle, foros, import de listados. El Excel por lote sigue
en `irg_campus_activity_audit`.
