# Spec — comandos de diploma, matrícula y asistencia

## Problema

Lisa no debe generar diplomas ni certificados de matrícula/asistencia a través de la libreta. El diploma académico oficial es `irg.diploma.wizard` (alumno + curso). Matrícula y asistencia son de admisión/sesión. `irg_generate_gradebook_certificate` queda solo para notas.

## Comandos

| Código | Payload | Flujo oficial |
| --- | --- | --- |
| `irg_generate_diploma` | `student_id`, `student_course_id`, `diploma_type` (`digital`\|`physical`), `issue_date?` | `irg.diploma.wizard.action_print_diploma`. El curso debe estar `finished`. No usa libreta ni el pago del portal de certificados. |
| `irg_generate_enrollment_certificate` | `admission_id`, `certificate_type`, `signer`, `shipping_type?` | solicitud Word `document_type=enrollment` (libreta resuelta internamente) |
| `irg_generate_attendance_certificate` | `admission_id`, `session_id`, `certificate_type`, `signer`, `shipping_type?` | solicitud Word `attendance` + validación HC |
| `irg_generate_gradebook_certificate` | solo `gradebook` / `gradebook_partial` | wizard de notas |

Resultado: preview → approve, `file_b64` + checksum, adjunto privado, sin mail.

## Fuera de alcance

Diplomados (`irg.diplomado.*`) y actas TFM.
