# Plan de misión: irg-practice-agreement-specific-homeclass

## Fuente y alcance

### Excepción de módulo

Ampliar `irg_practice_agreement_specific` (no un módulo hermano).
Knowledge: `irg_practice_agreement_specific_same_module.md`,
`irg_qweb_hasattr_unsafe.md`, `irg_report_print_name_foreign_xmlid.md`,
`irg_selection_qweb_predicate_alignment.md`.
No editar `irg_practice_agreement_sign` ni `irg_practice_agreement_types`.

## Decisiones (aprobadas)

- Tipo `especifico_homeclass_sincronas` en `ESPECIFICO_TYPES`,
  `selection_add`, wizard, report, portal y `attrs` el mismo día.
- Sin QUINTA. SÉPTIMA económica del ejemplo, genérica.
- CUARTA con difusión del centro, talleres y guías psicoeducativas
  genéricas. Sin PII del PDF.
- `_especifico_pdf_filename` y `print_report_name`: slug
  `Homeclass_Sincronas`. `print_report_name` defensivo con `_fields`.
- E2E TestSprite obligatorio (views/portal/report).

## Tier

Completa, `standard`. Un módulo, mismo patrón que el nacional.
Security Advisor: no aplica.

## Comando de tests

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d test_irg_practice_agreement_specific \
  -u irg_practice_agreement_specific \
  --test-enable --test-tags /irg_practice_agreement_specific \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test
```
