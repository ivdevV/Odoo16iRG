# Execution — irg-enrollment-modification

- Spec approved 2026-09-03.
- Plan: `docs/superpowers/plans/2026-09-03-irg-enrollment-modification.md`
- Security Advisor: `[YES]` in `artifacts/security-advisor.txt`
- Branch: `feat/irg-enrollment-modification`

## Implementación

- Módulo nuevo `irg_enrollment_modification` (sin editar addons existentes).
- Wizard + `irg.enrollment.change` + relleno Word + vistos académico/finanzas + botón en `op.student`.
- Chatter del estudiante: `message_post` con `sudo()` y `author_id` del operador, porque el grupo académico no tiene write en `op.student` (el ACL de `mail.message` exige write en el documento). El adjunto vive en la solicitud (`irg.enrollment.change`), no en el alumno.
- Tests: curso con `lang` si el campo existe (ISEP).

## Comandos

Sintaxis:

```bash
python3 -m py_compile addons-extra/extrairg/irg_enrollment_modification/**/*.py
python3 -c "import xml.etree.ElementTree as ET; ..."
```

Resultado: compile+xml pass.

BD desechable clonada de `test_irg_db`:

```bash
docker compose -f docker-compose.local.yml exec -T pgodoo_local \
  createdb -U odoo -T test_irg_db test_irg_enroll_mod_20260903

docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_enroll_mod_20260903 \
  -u irg_enrollment_modification --test-enable \
  --test-tags=/irg_enrollment_modification \
  --stop-after-init --http-port=8099 --log-level=test
```

- E2E TestSprite: skipped — MCP no registrado. Evidencia `artifacts/e2e-testsprite.txt`.
- Documentación: `missions/irg-enrollment-modification/CHANGELOG.md` y knowledge `irg_enrollment_modification.md`.
