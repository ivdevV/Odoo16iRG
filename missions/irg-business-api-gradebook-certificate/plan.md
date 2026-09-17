# Plan de misión: irg-business-api-gradebook-certificate

## Fuente y alcance

- Fuente: diseño aprobado (comando de escritura, preview → approve, `file_b64` en el resultado para el agente).
- Spec: `missions/irg-business-api-gradebook-certificate/00-spec.md`
- Diseño: `docs/superpowers/specs/2026-09-07-irg-generate-gradebook-certificate-design.md`
- Plan detallado TDD: `missions/irg-business-api-gradebook-certificate/01-plan.md`
- Knowledge consultada:
  - `.agents/knowledge/odoo_development_modding/artifacts/irg_business_api_command_facade.md`
  - `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
  - `.agents/workflows/odoo16_codebase_knowledge.md`
- Patrón: extender `irg_business_api` (registro cerrado `OPERATION_SPECS`). No se edita `irg_gradebook_certificates`. Apply llama a `irg.certificate.wizard.action_generate`.
- Rama base: checkout actual. Sin worktree: el compose monta este árbol.

## Decisiones cerradas

- Un comando `irg_generate_gradebook_certificate`, `kind=write`. No hay HTTP.
- `file_b64` va en `result_snapshot` tras approve (no en preview). El agente verifica checksum y reenvía el PDF.
- `idempotency_key` es campo de `irg.api.operation`.
- `signer` obligatorio; sin default a `raimon`.
- Dependencia blanda de certificados. `production` sigue rechazado.
- No mail, no `public=True`, no factura portal.
- Stub de `_convert_to_pdf` en tests (LibreOffice no es el contrato de la fachada). `_fill_template` + wizard sí se invocan.

## Tier y capacidad

- Misión completa, tier `complex`: más de cinco archivos, fachada API + flujo de certificados, binario en snapshot.
- Security Advisor: no aplica (no cambia autenticación, migraciones históricas, secretos de despliegue ni borrado). Reutiliza grupo + allowlist + `sudo()` ya existentes. El binario solo se devuelve al actor de la fachada tras approve.
- Capacidad: máxima de razonamiento disponible. El runtime no selecciona modelo.

## Fases y propietarios

1. **Plan — orquestador**: este documento.
2. **Implementación/TDD — codificador**: RED antes de producción, GREEN, refactor.
3. **Review — revisor independiente** (no el codificador).
4. **Validación — validador independiente** con `docker-compose.local.yml`.
5. **E2E — skipped** justificado (sin superficie web en el diff).
6. **Documentación**.
7. **Publicación**: no commit, push ni PR sin autorización explícita.

## Disparo E2E

Skipped. El cambio es Python, tests y docs de `irg_business_api`. No toca `views/`, `templates/`, `report/`, `static/`, portal, `website` ni controladores HTTP. El validador no puede activar E2E por su cuenta.

## Comandos previstos

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d test_irg_api_gradebook_cert \
  -i irg_business_api --test-enable --test-tags /irg_business_api \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test
```

Si el test-db no tiene certificados:

```bash
-i irg_gradebook_certificates,irg_certificate_partial,irg_business_api
```

Cleanup: no dejar el servicio apuntando a un worktree; la base `test_irg_api_gradebook_cert` es desechable.

## Riesgos

- `ir.attachment.datas` con `bin_size` en contexto: leer con `bin_size=False`.
- Snapshots grandes por `file_b64`: aceptado para el agente.
- Wizard default `signer=raimon`: la fachada rechaza firmante vacío **antes** de crear el wizard.
- `_fill_template` en tests puede fallar si faltan plantillas; fallback documentado en `01-plan.md` (stub de `_generate_and_attach_pdf` solo si fill falla, registrado en `execution.md`).
