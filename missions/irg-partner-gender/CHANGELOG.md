# Changelog — irg-partner-gender

## 16.0.1.1.0 — 2026-07-22

### Fixed

- `username` deja de ser `required` a nivel de modelo y en la pestaña Moodle, para poder editar `gender` (y el contacto) sin usuario Moodle.

## 16.0.1.0.0 — 2026-07-21

### Added

- Módulo `irg_partner_gender`: campo `gender` visible en ficha de contacto (junto a etiquetas) y en pestaña Admisión del pedido.
- Cascada de resolución SO → partner → heurística (título/nombre) → `'o'`, con write-back al partner cuando el género se infiere.
- Overrides de `_create_or_get_admission`, `create_admission_manual` y `get_admision_id` para resolver género antes de crear la admisión.
- Tests unitarios de cascada, write-back y create de admisión tras resolve.
