# Plan de misión: Moodle `iteminstance`

- Tipo: misión completa.
- Tier: `standard`.
- Motivo: bugfix de comportamiento en integración Moodle, con servicio,
  resolución de datos y fallback entre cursos.
- Objetivo: admitir IDs de actividad procedentes de `iteminstance` sin romper
  los mapeos existentes por `id` o `cmid`.
- Diseño:
  `docs/superpowers/specs/2026-07-24-irg-gradebook-moodle-iteminstance-matching-design.md`.
- Plan detallado:
  `docs/superpowers/plans/2026-07-24-irg-gradebook-moodle-iteminstance-matching.md`.
- Seguridad: no cambia autenticación, secretos, permisos, escritura externa ni
  borrado histórico. Las llamadas Moodle siguen siendo de lectura.
- Gates: TDD RED/GREEN, review de código independiente, validación independiente,
  documentación y comprobación final.
- Publicación: fuera de alcance hasta una autorización explícita separada.
