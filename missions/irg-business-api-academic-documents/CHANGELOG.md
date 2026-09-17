# Changelog — irg-business-api-academic-documents

## 16.0.1.4.0 — 2026-09-08

- Nuevos comandos `irg_generate_diploma`, `irg_generate_enrollment_certificate` y `irg_generate_attendance_certificate`.
- El diploma académico usa `irg.diploma.wizard` (`student_id` + `student_course_id`). El curso debe estar `finished`. No usa libreta ni el pago del portal de certificados.
- Matrícula y asistencia se piden con `admission_id` (asistencia también `session_id`). La libreta se resuelve internamente y no aparece en payload ni resultado.
- `irg_generate_gradebook_certificate` vuelve a ser solo notas (`gradebook` / `gradebook_partial`). Los tipos movidos se rechazan con el nombre del comando nuevo.
- Resultado: preview → approve, `file_b64` + SHA-256, adjunto privado, sin mail al alumno.
- Fuera de alcance: diplomados de curso y actas TFM/TFG.
