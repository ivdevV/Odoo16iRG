# Plan — irg-gradebook-elearning-exam-qty

## Fuente

- Spec: `docs/superpowers/specs/2026-09-18-irg-gradebook-elearning-exam-qty-design.md`
- Plan TDD: `docs/superpowers/plans/2026-09-18-irg-gradebook-elearning-exam-qty.md`
- Rama prevista: `feat/irg-gradebook-elearning-exam-qty` (desde `Dev_iRG`)

## Knowledge

- `modding_rules_and_email_analysis.md` — módulo nuevo `irg_` en
  `addons-extra/extrairg/`, herencia, no editar existentes, `auto_install` False.
- `irg_gradebook_auto_close.md` — el cierre y los promedios leen
  `_get_gradebook_info`; no cerrar con un lote parcial de requisitos. Esta
  misión no toca los hooks de `app.gradebook.result`.
- `irg_admission_auto_gradebook_templates.md` — el template de cabecera sigue
  existiendo; este addon solo sustituye `exam.qty` cuando el recuento e-learning
  es > 0.

## Clasificación

- Misión: `full` (cambia cuántos exámenes exige cada línea de libreta)
- Tier: `standard` (addon nuevo, un inherit, recuento por canal/lote, tests)
- Capacidad: implementación y pruebas sólidas; no hay selección de modelo en
  este runtime
- E2E: **skipped** — el diff no toca vistas, QWeb, `static/`, portal, website,
  controladores HTTP ni plantillas de diploma (`info_exam` ya se pinta)
- Security Advisor: no aplica (sin auth, migraciones, secretos, despliegue ni
  borrado histórico)

## Roles

- Plan / orquestación: esta sesión
- Implementación/TDD: coder de la misión
- Review: agente distinto tras GREEN
- Validación: agente distinto; `verification.json`
- Documentación: tras Review y Validación (`doc/modules/extrairg/`, changelog)
- Commit / push / PR: solo con autorización explícita

## Criterios de aceptación

1. N se calcula **por línea** (`app.gradebook.subject`), no como entero de
   `op.batch` ni de la cabecera.
2. N = surveys únicos tipo `exam` publicados en `op_subject.slide_channel_id`
   cuyo `allowed_batch_ids` está vacío o contiene `gradebook.batch_id`.
3. En una misma libreta, una asignatura puede exigir 3 y otra 2.
4. Un examen restringido a un lote nuevo no incrementa N en el lote antiguo.
5. `scheduled_date` futura no excluye el examen del recuento.
6. N = 0 deja el `qty` de la plantilla.
7. Libreta `done`: no se sustituye qty.
8. No se modifica `isep_gradebook` ni `irg_batch_slide_restrictions`.
9. Tests GREEN en `docker-compose.local.yml`.

## Comando canónico

BD desechable: `test_irg_gb_exam_qty`. Compose: `docker-compose.local.yml`.

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_gb_exam_qty \
  -i irg_gradebook_elearning_exam_qty --test-enable \
  --test-tags=/irg_gradebook_elearning_exam_qty \
  --stop-after-init --http-port=8099 --log-level=test
```

## Riesgos

- Usar `is_user_allowed_by_batch` en tests/backend contaría según el usuario
  admin, no según el lote de la admisión. El recuento usa
  `app.gradebook.student.batch_id`.
- `info_exam` es stored: el cierre lee `_get_gradebook_info` en vivo; el texto
  `[n de N]` se refresca al recomputar promedios.
- Crear `slide.slide` con `survey_id` exige `website_slides_survey` (ya viene
  por `isep_gradebook` → `isep_survey`).

## Artefactos

- `missions/irg-gradebook-elearning-exam-qty/execution.md`
- `missions/irg-gradebook-elearning-exam-qty/artifacts/`
- `missions/irg-gradebook-elearning-exam-qty/verification.json`
- `missions/irg-gradebook-elearning-exam-qty/CHANGELOG.md` (fase Documentación)
- `doc/modules/extrairg/irg_gradebook_elearning_exam_qty.md` (fase Documentación)
