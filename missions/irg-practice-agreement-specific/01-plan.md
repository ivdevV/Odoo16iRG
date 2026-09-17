# Plan de misión: irg-practice-agreement-specific

## Fuente y alcance

- Diseño acordado: wizard en `practice.request`, específico internacional
  genérico, dos enlaces de firma, lugar = centro asignado, sin INMIRA.
- Knowledge: `modding_rules_and_email_analysis.md`,
  `irg_qweb_hasattr_unsafe.md`, `irg_report_print_name_foreign_xmlid.md`.
- Módulo nuevo; no editar `irg_practice_agreement_sign` ni
  `irg_practice_agreement_types`.
- Rama: `Dev_iRG`. Runtime: `docker-compose.local.yml`.

## Decisiones

- `selection_add` de `especifico_internacional` (y `especifico_nacional`
  reservado) en `practice.agreement`.
- Tokens: `access_token` (centro, ya existe) y `student_access_token`.
- `action_complete_signature` del específico no llama a `super` hasta que
  falte generar PDF: intercepta la firma del centro; firma alumno en
  `action_complete_student_signature`; PDF al tener las dos.
- QWeb: ocultar el `div.page` marco si el tipo es específico; `t-call`
  del documento específico (sin `hasattr`).
- `print_report_name` defensivo incluyendo marco e específico.
- E2E TestSprite obligatorio (views + portal + report).

## Tier

Completa, `standard`. Security Advisor: no aplica.

## Comando de tests

```bash
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d test_irg_practice_agreement_specific \
  -i irg_practice_agreement_specific \
  --test-enable --test-tags /irg_practice_agreement_specific \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test
```
