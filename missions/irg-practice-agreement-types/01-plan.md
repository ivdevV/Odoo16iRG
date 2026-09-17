# Plan de misión: irg-practice-agreement-types

## Fuente y alcance

- Fuente: diseño acordado (wizard radio, marcos en practice center,
  plantilla internacional genérica, específicos más adelante).
- Knowledge consultada:
  - `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
  - `.agents/knowledge/odoo_development_modding/artifacts/irg_qweb_hasattr_unsafe.md`
  - `.agents/workflows/odoo16_codebase_knowledge.md`
- Patrón: módulo nuevo en `addons-extra/extrairg/` que hereda
  `irg_practice_agreement_sign` (xpath + `_inherit`). No se edita el módulo
  base: la QWeb nacional permanece y se reutiliza para `marco_nacional`.
- Rama base: `Dev_iRG`. Sin worktree: el compose monta este checkout.

## Decisiones cerradas

- Wizard TransientModel `irg.practice.agreement.create.wizard`, widget radio.
- `agreement_type`: `marco_nacional` | `marco_internacional`. Ausencia o
  vacío = nacional (convenios ya creados).
- `action_create_agreement` del módulo base no se anula: el botón nuevo
  llama a `action_open_create_agreement_wizard`.
- Cláusulas internacionales en un `t-call` compartido (PDF + portal).
  XPath: `t-if` sobre el bloque CLÁUSULAS existente + bloque internacional
  a continuación. En QWeb no usar `hasattr`.
- INMIRA omitido. Específicos fuera de esta entrega.
- E2E TestSprite obligatorio: el diff toca `views/`, portal y report.

## Tier y capacidad

- Misión completa, tier `standard`: módulo nuevo acotado, un wizard, un
  campo, herencias de vista/QWeb y tests. No es cross-module de negocio
  más allá del inherit del convenio ya existente.
- Security Advisor: no aplica (no cambia autenticación, concurrencia,
  migraciones históricas, secretos ni despliegue). El campo nuevo no borra
  datos; los convenios existentes se interpretan como nacional.

## Fases y propietarios

1. **Plan — orquestador**: este documento.
2. **Implementación/TDD — codificador**: tests RED, implementación mínima,
   GREEN.
3. **Review — revisor independiente**.
4. **Validación — validador independiente** con `docker-compose.local.yml`.
5. **E2E — e2e-tester** tras el resto de checks en verde.
6. **Documentación**.
7. **Publicación**: no commit, push ni PR sin autorización explícita.

## Criterios de aceptación

Ver `00-spec.md`.

## Riesgos y pruebas

- **XPath del botón**: heredar
  `irg_practice_agreement_sign.view_practice_center_form_agreement_sign`
  y cambiar `name` + `string` del botón `action_create_agreement`.
- **XPath CLÁUSULAS**: `//h4[contains(., 'CLÁUSULAS')]/parent::div` en
  report y `//h6[contains(., 'CLÁUSULAS')]/parent::div` en portal.
- **Regresión nacional**: render HTML sin `LATAM` / `4.3`.
- **Permisos wizard**: mismos grupos `group_practice_agreement_user`.

## Disparo E2E

Obligatorio: vistas XML, plantilla portal y report QWeb.

## Comandos previstos

```bash
docker compose -f docker-compose.local.yml \
  run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf \
  -d test_irg_practice_agreement_types -i irg_practice_agreement_types \
  --test-enable --test-tags /irg_practice_agreement_types \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --log-level=test --no-http
```
