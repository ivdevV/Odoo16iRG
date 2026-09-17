# Fachada API: diploma, matrícula y asistencia

## Decisión

Hay dos productos de «diploma» en Odoo. Lisa debe usar el académico del formulario de alumno (`irg.diploma.wizard`), no el certificado de campus ligado a libreta (`irg.certificate.request` con `document_type=diploma`). Matrícula y asistencia sí usan plantillas Word de `irg.certificate.request`, pero el agente nunca envía ni recibe `gradebook_student_id`: la libreta se resuelve en servidor desde `admission_id`.

Comandos: `irg_generate_diploma`, `irg_generate_enrollment_certificate`, `irg_generate_attendance_certificate`. Fuera: diplomados de curso (`irg.diplomado.*`) y actas TFM.

## Diploma

Payload: `student_id`, `student_course_id`, `diploma_type` (`digital`|`physical`), `issue_date?`. Apply llama a `irg.diploma.wizard.action_print_diploma`. Gate de cierre: `op.student.course.state == finished`. No se exige libreta `done` ni el pago del portal de certificados (esa ruta es otro producto). El wizard oficial sí enlaza `irg.diploma.registry.attachment_id`. El preview no consume la secuencia; el número aparece en el resultado.

`diploma_type` del wizard no es el `certificate_type` Word (`custom`, `physical_apostilled`).

## Matrícula y asistencia

Opciones Word: `certificate_type`, `signer` obligatorio (`dpto_academico`|`raimon`), `shipping_type` si es físico. `origin=backend` y `state=done` para no disparar correo de portal ni factura. Si hay varias libretas y el lote no desambigua, `UserError` (no elegir por `id desc`).

Asistencia: campo `session_id` presente (dependencia blanda; no consultar `ir.module.module`). Validar HC con `new()` + `_validate_attendance_request()`. La sesión debe ser del `batch_id` de la admisión.

## Resultado

Misma forma que notas: `file_b64`, checksum SHA-256, `public: false`, parseo `/web/content/<id>`, `bin_size=False`. `state` en el dict es el de `irg.certificate.request` (Word) o el de `irg.diploma.registry` (diploma).
