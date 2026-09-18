# Plan — irg-batch-homeclass-subject-lead-days

## Fuente

- Spec: `docs/superpowers/specs/2026-09-18-irg-batch-homeclass-subject-lead-days-design.md`
- Plan TDD: `docs/superpowers/plans/2026-09-18-irg-batch-homeclass-subject-lead-days.md`
- Rama prevista: `feat/irg-batch-homeclass-subject-lead-days` (desde `Dev_iRG`)

## Knowledge

- `modding_rules_and_email_analysis.md` — módulo nuevo `irg_` en
  `addons-extra/extrairg/`, herencia, no editar existentes, `auto_install` False.
- `irg_diplomado_class_start_date.md` — `date_start_class` es la fecha oficial
  de inicio de clases; esta misión no la muta.
- `irg_auto_enroll_cron_robust.md` — un `write` de `date_from` dispara el cron
  de auto-enroll; el segundo write (offset) es aceptable y esperado.

## Clasificación

- Misión: `full` (cambio de comportamiento de producto: apertura de asignaturas)
- Tier: `standard` (addon nuevo, un inherit, offset de 3 días, tests con mock)
- Capacidad: implementación y pruebas sólidas; no hay selección de modelo en
  este runtime
- E2E: **skipped** — el diff no toca vistas, QWeb, `static/`, portal, website,
  controladores HTTP ni plantillas de diploma
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

1. Tras un sync HomeClass exitoso, cada `date_from` informado es 3 días anterior
   al valor que habría dejado `irg_batch_homeclass_api_scheduler`.
2. `date_to` y `date_start_class` no cambian respecto al original.
3. El fallback a `start_date` también se adelanta 3 días; no se recorta contra
   el inicio del lote.
4. Si el sync original falla, no se reescriben fechas.
5. Re-sync no acumula el offset (idempotente respecto a la fecha de la API).
6. No se modifica `irg_batch_homeclass_api_scheduler`.
7. Tests de módulo GREEN en `docker-compose.local.yml` sin HTTP a la API real.

## Comando canónico

BD desechable: `test_irg_hc_lead`. Compose: `docker-compose.local.yml`.

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_hc_lead \
  -i irg_batch_homeclass_subject_lead_days --test-enable \
  --test-tags=/irg_batch_homeclass_subject_lead_days \
  --stop-after-init --http-port=8099 --log-level=test
```

## Riesgos

- Llamar a `_sync_homeclass_calendar` en tests sin mock pega a producción
  (`calendario.institutoraimongaja.com`). Los tests deben parchear
  `requests.get` del scheduler y crear lotes con `skip_homeclass_sync`.
- Un `date_from` anterior a `start_date` del lote es válido aquí; el onchange
  del scheduler original no aplica a writes programáticos.

## Artefactos

- `missions/irg-batch-homeclass-subject-lead-days/execution.md`
- `missions/irg-batch-homeclass-subject-lead-days/artifacts/`
- `missions/irg-batch-homeclass-subject-lead-days/verification.json`
- `missions/irg-batch-homeclass-subject-lead-days/CHANGELOG.md` (fase Documentación)
- `doc/modules/extrairg/irg_batch_homeclass_subject_lead_days.md` (fase Documentación)
