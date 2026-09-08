# Modificación de matrícula (`irg_enrollment_modification`)

## Contexto

El cambio de curso, lote, modalidad, año académico y forma de pago se pedía con un Word fuera de Odoo. El módulo nuevo inyecta un botón en `op.student`, crea una solicitud persistente y aplica los datos solo tras los vistos. No se editan addons existentes.

## Decisiones de diseño

1. La matrícula de origen (`op.student.course`) se elige siempre, aunque el alumno tenga una sola.
2. Cinco booleanos independientes. Solo las secciones marcadas se rellenan en el Word y se escriben al aprobar.
3. Crear la solicitud no escribe curso ni pago. El Word de solicitud deja vacías firma del alumno, Área Financiera y resolución.
4. Modalidad no vive en `op.student.course`. Se lee y escribe `sale.order.line.x_studio_modalidad` si el campo existe. El wizard exige `sale_order_id` tanto para modalidad como para pago.
5. Si hay cambio de pago, el visto académico deja `academic_approved` sin PDF. Contabilidad escribe `payment_mode_id` y entonces se genera el PDF.
6. LibreOffice convierte a PDF. Si falla tras un visto correcto, los datos se quedan y `pdf_pending` permite reintentar.
7. La plantilla oficial no tiene merge fields. «Grupo de origen/destino» se repite en varias filas: hay que rellenar **por fila de tabla**, no con un replace global.

## Seguridad

- Grupo nuevo `irg_enrollment_modification.group_academic` para crear, visto académico y denegar en `submitted`.
- Finanzas: `account.group_account_invoice` para visto y denegar en `academic_approved`.
- `groups=` en la vista no basta. Cada método mutante hace `has_group()` antes de `sudo()`.
- `sudo()` estrecho: write de `op.student.course`, líneas del pedido y `sale.order.payment_mode_id`.
- Métodos que publican adjuntos en chatter no pueden ser RPC-públicos si internamente usan `sudo()`. Prefijo `_` (`_generate_request_docx`).
- El grupo académico tiene **read** en `op.student`. `mail.message` exige write en el documento para `message_post`. Por eso el chatter del alumno usa `sudo()` con `author_id` del operador. El chatter de la solicitud corre sin `sudo()`.

## Gotchas

- `op.course.lang` es required en esta instancia (ISEP). Los tests deben setearlo si el campo existe.
- Crear `ir.attachment` con `res_model=op.student` también exige write en el alumno. El adjunto se guarda en `irg.enrollment.change` y se enlaza al mensaje del estudiante.
- Un lote de destino debe pertenecer al curso de destino (o al de origen si el curso no cambia). Cambiar solo el curso sin lote incompatible con el lote actual se rechaza.
- Unique OpenEduCat `(student, course, batch)` no se traga: si choca, falla la transacción del visto académico.
