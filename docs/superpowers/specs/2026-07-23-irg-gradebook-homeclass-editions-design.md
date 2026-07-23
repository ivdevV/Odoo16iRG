# Diseño: ediciones HomeClass con búsqueda de respaldo

## Objetivo

Permitir varios cursos Moodle HomeClass activos para un mismo curso Odoo sin
bloquear la sincronización. El asistente debe priorizar la edición académica
del lote y consultar las demás ediciones HomeClass únicamente como respaldo,
sin mezclar notas entre ediciones.

## Contexto confirmado

- El curso Moodle `36` corresponde a HomeClass `2024-2025`.
- El curso Moodle `35` corresponde a HomeClass `2025-2026`.
- Los Activity IDs pertenecen al curso Moodle que contiene cada actividad y
  no son intercambiables entre ediciones.
- El CSV consolidado actual puede omitir el año en el nombre del curso, por lo
  que la edición debe poder corregirse manualmente.

## Diseño

Se creará un addon puente nuevo, dependiente de
`irg_gradebook_moodle_mapping_admin`, que heredará los modelos y el asistente
existentes sin modificar directamente los addons publicados.

Cada mapa de curso tendrá un año de edición HomeClass editable. Al cambiar el
nombre del curso, el sistema propondrá el año inicial cuando encuentre un
periodo académico con cualquiera de estos formatos:

- `2025-2026`
- `2025/2026`
- `2025_2026`

El importador aplicará la misma detección cuando el CSV conserve el nombre
completo. Si el CSV no contiene el periodo, el administrador podrá informar el
año desde la tabla o el formulario de mapas de curso.

Para un lote `HC`, el asistente ordenará los mapas activos así:

1. mapa cuya edición coincide con el año de inicio del lote;
2. mapa HomeClass genérico, sin edición;
3. restantes mapas HomeClass activos, como respaldo.

La sincronización evaluará cada asignatura mapa por mapa en ese orden. Se
detendrá en el primer mapa que resuelva de forma válida al alumno, los Activity
IDs y una nota utilizable. No combinará ni promediará resultados de dos
ediciones. Un Activity ID ausente en un curso no será ambiguo: permitirá probar
el siguiente mapa. Una resolución realmente múltiple dentro del mismo curso
seguirá siendo incompatible.

Los lotes `ONL` conservarán exactamente el comportamiento actual.

## Errores y límites

- Cero mapas HomeClass activos seguirá siendo un error de configuración.
- Varios mapas HomeClass activos dejarán de ser un error.
- Dos mapas con la misma edición son válidos como inventario, pero se probarán
  de forma determinista por ID; no se mezclarán sus notas.
- Si ningún mapa produce una nota válida, el asistente mostrará el diagnóstico
  más útil acumulando qué cursos se probaron, sin exponer credenciales.
- No se borrarán ni desactivarán mapas, asignaturas o actividades existentes.

## Pruebas de aceptación

- Un lote 2025 prioriza el curso `35` frente al `36`.
- Si la actividad o el alumno no aparece en el curso priorizado, se consulta el
  otro HomeClass y se usa su resultado válido.
- Si ambos cursos producen resultado, solo se usa el primero según prioridad.
- Varios HomeClass no lanzan el antiguo error de “exactamente un mapa”.
- Los Activity IDs se resuelven únicamente dentro de su curso padre.
- Online mantiene selección por edición y fallback genérico actuales.
- El año se detecta en los tres separadores admitidos y puede editarse.
