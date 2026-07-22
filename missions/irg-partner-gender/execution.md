# Execution — irg-partner-gender

## Decisiones

- Módulo puente nuevo `irg_partner_gender` (no editar `isep_*` ni `irg_admission_gender_fix`).
- Heurística en `res.partner` (misma lógica que gender_fix) para write-back y cascada centralizada.
- Antes de crear admisión: resolver género y persistir en partner; el create legacy sigue leyendo `self.gender or partner.gender or 'o'`.
- `test_05` valida resolve + create `op.admission` (no `create_admission_manual` completo: en DB de test falta `op.admission.order_id` del grafo completo).

## Comandos

### RED

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_partner_gender_red_20260721 \
  -i irg_partner_gender --test-enable --test-tags=/irg_partner_gender \
  --stop-after-init --http-port=8098 --log-level=test
```

Resultado: `0 failed, 5 error(s) of 5 tests`. Evidencia: `artifacts/red-install.txt`.

### GREEN

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_partner_gender_green5_20260721 \
  -i irg_partner_gender --test-enable --test-tags=/irg_partner_gender \
  --stop-after-init --http-port=8093 --log-level=test
```

Resultado: `0 failed, 0 error(s) of 5 tests`. Evidencia: `artifacts/green-install.txt`.

### Syntax

```bash
python3 -m py_compile addons-extra/extrairg/irg_partner_gender/models/*.py \
  addons-extra/extrairg/irg_partner_gender/tests/test_partner_gender.py
```

OK. Evidencia: `artifacts/syntax-check.txt`.

## Estado

- 2026-07-21: plan de misión creado; TDD RED → implementación → GREEN.
- 2026-07-21: `verification.json` status `passed`.
- 2026-07-22: `username` required=False (modelo + vista Moodle). GREEN `0 failed, 0 error(s) of 6 tests` en `test_irg_partner_gender_username_20260722`. Evidencia: `artifacts/green-username-optional.txt`.
- Pendiente `-u irg_partner_gender` en BD operativa tras pull.
