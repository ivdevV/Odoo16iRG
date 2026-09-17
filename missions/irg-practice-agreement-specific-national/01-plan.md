# Plan de misión: irg-practice-agreement-specific-national

## Fuente y alcance

### Excepción de módulo (obligatorio dejarla explícita)

La regla de oro es no editar addons existentes. El usuario autoriza
**esta excepción**: ampliar `irg_practice_agreement_specific` en lugar
de crear `irg_practice_agreement_specific_national` u otro módulo
hermano. Un módulo nuevo no aporta arquitectura: comparte wizard, doble
firma, controlador y `print_report_name`. La excepción queda registrada
aquí y en la spec; **no** se tocan `irg_practice_agreement_sign` ni
`irg_practice_agreement_types`.

- Ejemplo nacional genérico (autorizado; sin PII del DOCX de muestra).
- Knowledge: `irg_qweb_hasattr_unsafe.md`,
  `irg_report_print_name_foreign_xmlid.md`,
  `irg_selection_qweb_predicate_alignment.md`.

## Decisiones

- `selection_add` de `especifico_nacional`; `ESPECIFICO_TYPES` incluye
  ambos. `_is_especifico()` cubre la doble firma.
- QWeb: ocultar el `div.page` marco si el tipo es cualquiera de los dos
  específicos; `t-call` nacional vs internacional. Sin `hasattr`.
- `print_report_name` defensivo con las cuatro ramas (dos marcos + dos
  específicos).
- Primera nacional: fechas, días y horario de la solicitud, horas, dirección
  del centro y párrafo de flexibilidad de horario.
- E2E TestSprite obligatorio (views/portal/report).

## Tier

Completa, `standard`. Security Advisor: no aplica.

## Comando de tests

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d test_irg_practice_agreement_specific \
  -u irg_practice_agreement_specific \
  --test-enable --test-tags /irg_practice_agreement_specific \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test
```
