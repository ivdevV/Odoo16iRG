# Changelog — irg-business-api-certificate-types

## 16.0.1.3.0 — 2026-09-07

- `irg_generate_gradebook_certificate` admite `diploma`, `attendance` y `enrollment` además de las notas.
- Notas siguen el wizard; diploma/matrícula/asistencia usan `irg.certificate.request._generate_and_attach_pdf`.
- Diploma y notas completas exigen libreta `done`. Asistencia exige `session_id`.
- Fuera de alcance: diplomados de curso y actas TFM/TFG.
