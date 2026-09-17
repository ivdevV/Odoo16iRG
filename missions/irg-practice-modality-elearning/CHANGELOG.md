# Changelog — irg-practice-modality-elearning

## 16.0.1.0.0 — 2026-09-02

- Nuevo módulo `irg_student_course_practice_modality`: modalidad de prácticas por matrícula, sync desde la última solicitud en `approved`/`progress`/`end`, visible en backend, campus y portal educativo.
- Nuevo módulo `irg_practice_slide_restrictions`: requisito por sección de eLearning, bloqueo en el GET `/slides/slide/<id>` y ocultación en índice/sidebar sin romper las restricciones de lote.
