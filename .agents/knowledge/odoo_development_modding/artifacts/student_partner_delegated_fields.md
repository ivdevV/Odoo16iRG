# Campos compartidos entre `op.student` y `res.partner`

En OpenEducat 16, `op.student` declara `_inherits = {"res.partner": "partner_id"}`. Para un dato que debe ser idéntico en la ficha del estudiante y en la del contacto, el patrón más simple y seguro es definir el campo físico únicamente en `res.partner`.

Durante la carga del registro, Odoo expone esos campos también en `op.student` como campos delegados. Las escrituras realizadas mediante el estudiante se almacenan en su `partner_id`, y los cambios realizados en el contacto se leen directamente desde el estudiante. No hace falta declarar campos `related`, métodos `compute` ni lógica de sincronización.

Las dos vistas sí deben heredarse por separado para mostrar los campos en ambas interfaces. Este patrón quedó cubierto por pruebas de escritura en ambos sentidos en `irg_student_birth_citizenship`.
