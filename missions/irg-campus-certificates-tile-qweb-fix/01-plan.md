# Mission Plan: irg-campus-certificates-tile-qweb-fix

## Fuente

- Spec: `docs/superpowers/specs/2026-09-04-irg-campus-certificates-tile-qweb-fix-design.md`
- Plan TDD: `docs/superpowers/plans/2026-09-04-irg-campus-certificates-tile-qweb-fix.md`

## Knowledge

- `modding_rules_and_email_analysis.md` — módulo nuevo `irg_`, herencia, no editar existentes.
- `irg_diplomado_portal_request.md` — para tiles QWeb conviene validar la vista heredada; `hasattr` no es seguro en QWeb.
- `doc/modules/extrairg/irg_course_portal_tiles_diplomado_hide.md` — `is_diplomado()` ya se usa en las tiles hermanas.

## Clasificación

- Misión: `full` (bugfix de portal / QWeb)
- Tier: `standard` (módulo nuevo, un xpath, tests acotados)
- E2E: **obligatorio** (toca vista QWeb de portal)
- Security Advisor: no aplica (sin autenticación, migraciones, secretos ni borrado)

## Roles

- Plan / orquestación: esta sesión
- Implementación/TDD: esta sesión
- Review: agente distinto tras GREEN
- Validación: agente distinto
- Commit / push: autorizado a `Dev_iRG`

## Comando canónico

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_campus_certificates_tile_qweb_fix --test-enable \
  --test-tags=/irg_campus_certificates_tile_qweb_fix \
  --stop-after-init --http-port=8099 --log-level=test
```
