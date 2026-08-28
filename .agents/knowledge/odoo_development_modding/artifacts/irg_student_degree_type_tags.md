# Etiquetas Many2many en la ficha de alumno

Para un campo de etiquetas de color en `op.student`, el patrón estable es un
catálogo propio (`_name` nuevo) con `name` + `color` Integer, un Many2many
en el alumno y `widget="many2many_tags"` con `options="{'color_field': 'color'}"`.

El ancla de la columna izquierda de Información personal es
`emergency_contact` en `openeducat_core.view_op_student_form`. Un
`position="after"` sobre ese campo deja la etiqueta al final de esa
columna, debajo de los campos que otras herencias o Studio inserten
después del contacto de emergencia (p. ej. Estado de pago).

No reutilizar `op.study.type` / `study_type_id` ni
`x_studio_titulacion`: esos guardan la titulación concreta, no el tipo.

Referencia: módulo `irg_student_degree_type`.
