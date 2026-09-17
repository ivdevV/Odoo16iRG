# Execution — irg-admission-register-export-nationality

## Decisiones

- Campo fuente: `op.student.nationality` (confirmado por el usuario).
- No se exporta `citizenship_country_id` ni el país de dirección del partner.
- Columna al final de `_COLUMNS` para no romper el orden existente.
- CSV incluido porque comparte `_get_rows`; no hay rama distinta de columnas.

## Knowledge

- `student_partner_delegated_fields.md`: `nationality` no es campo de `res.partner`.
- `citizenship_country_id` queda fuera de alcance.

## Comandos

### Fixtures

El registro de admisión exige `min_count > 0`. Los tests usan `min_count=1`, `max_count=100`.

### RED

```bash
docker compose -f docker-compose.local.yml exec -T pgodoo_local \
  psql -U odoo -d postgres -c \
  "CREATE DATABASE test_irg_arex_nat_red_20260908 TEMPLATE odoo16irg_local;"

docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_arex_nat_red_20260908 \
  -u irg_admission_register_export --test-enable \
  --test-tags=/irg_admission_register_export --stop-after-init \
  --http-port=8099 --log-level=test --workers=0
```

Resultado: `2 failed, 0 error(s) of 2 tests`.
`AssertionError: 'Nacionalidad' not found in [...]`
Evidencia: `artifacts/red-summary.txt`, `artifacts/red-install.txt`.

### GREEN

Columna añadida a `_COLUMNS`. Misma suite:

Resultado: `0 failed, 0 error(s) of 2 tests`.
`python3 -m py_compile`: OK.
Evidencia: `artifacts/green-summary.txt`, `artifacts/green-install.txt`.

## Review

Agente distinto del coder: `[YES] Review approved` (sin hallazgos bloqueantes).

## Validación

Validador independiente: `[PASS] validation`.
`verification.json` con `status: passed`.
Bases `test_irg_arex_nat_red_20260908` y `test_irg_arex_nat_val_20260908` eliminadas. `odoo_local` sigue Up.

## Documentación

Actualizados `doc/modules/extrairg/irg_admission_register_export.md` y `doc/modules/INDEX.md`. Sin entrada nueva de knowledge: el cambio no introduce un patrón reutilizable distinto de `_COLUMNS`.

