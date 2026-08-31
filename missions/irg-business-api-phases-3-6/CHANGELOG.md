# irg-business-api-phases-3-6

## 16.0.1.1.0 — 2026-08-28

Extiende `irg_business_api` con las fases 3–6 del plan técnico, envolviendo métodos oficiales:

- Clonación HomeClass→Online: `irg_apply_online_clone` llama a `action_copy_homeclass_to_online` (contenido, no solo canal).
- Aperturas, acceso (guardarraíl 30 %), matrícula solo desde `confirm` vía `enroll_student`.
- Baja (`action_down`) **no** expuesta.
- Mapas Moodle explícitos, sync oficial de notas sin devolver tokens.
- Encuestas borrador, auto-score, recalificación de un intento, import TXT, adjuntos privados.

Pruebas: 53 tests, 0 fallos (`--test-tags /irg_business_api`).
