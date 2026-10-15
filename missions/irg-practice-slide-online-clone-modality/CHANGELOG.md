# Changelog — irg-practice-slide-online-clone-modality

## 16.0.1.2.0 — 2026-10-15

### Fixed

- En canales clon online (`irg_homeclass_channel_id`), el filtro por
  `irg_required_practice_type` resuelve cursos/asignaturas del canal maestro.
  Antes, al no haber `op_subject_ids` en el clon, las secciones con modalidad
  requerida quedaban ocultas para alumnos online con modalidad en matrícula.
