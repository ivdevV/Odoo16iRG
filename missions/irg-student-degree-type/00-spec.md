# Spec — irg-student-degree-type

## Problema

En la ficha de alumno (`op.student`), pestaña Información personal, hace falta
clasificar el **tipo de titulación** del estudiante con el mismo aspecto de
etiqueta de colores que las etiquetas de CRM (widget `many2many_tags`).

El campo debe verse en la columna izquierda, debajo de **Estado de pago**
(y por tanto debajo de **Contacto de emergencia**, último campo de esa
columna en la vista base).

## Solución

Módulo nuevo `addons-extra/extrairg/irg_student_degree_type` (sin modificar
módulos existentes):

1. Catálogo `irg.student.degree.type` con `name` y `color`.
2. Campo `irg_degree_type_ids` Many2many en `op.student`, etiqueta
   «Tipo de titulación».
3. Vista de formulario: xpath tras `emergency_contact` en
   `openeducat_core.view_op_student_form`, widget `many2many_tags` y
   `color_field: color`.
4. Menú de catálogo bajo Configuración de OpenEduCat.
5. ACL de lectura para usuarios internos; escritura para back-office.

No se siembra un catálogo cerrado: las etiquetas se crean desde el propio
campo, como en CRM. No se toca `x_studio_titulacion` ni `study_type_id`
(titulación concreta, no el tipo).

## Criterios de aceptación

1. El modelo `op.student` expone `irg_degree_type_ids` Many2many hacia
   `irg.student.degree.type`.
2. Se puede asignar y persistir una o varias etiquetas con color.
3. El formulario combinado de alumno muestra el campo después de
   `emergency_contact`, con widget `many2many_tags`.
4. Existe menú para gestionar el catálogo.
5. Suite de tests del módulo en verde.

## Fuera de alcance

- Portal, informes, pedidos de matrícula, Studio.
- Migración de valores históricos.
- Semilla fija de tipos.
