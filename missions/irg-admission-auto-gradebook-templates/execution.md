# Execution — irg-admission-auto-gradebook-templates

## Decisiones

- Enfoque puente nuevo (no editar `irg_admission_auto_gradebook`).
- Precedencia: `course.gradebook_id` → canónica diplomado → canónica máster → vacío.
- Tests unitarios del helper `_irg_assign_auto_gradebook_templates` (evitan stack OpenEduCat/`res.users` login).

## Comandos

### RED (tests antes del override; errores de setup por enroll completo)

Base `test_irg_agtpl_20260721_c` — 6 errors por `NotNullViolation` en `res_users.login` al invocar enroll real. Evidencia: `artifacts/red-install.txt`.

### GREEN

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_agtpl_20260721_green \
  -i irg_admission_auto_gradebook_templates --test-enable \
  --test-tags=/irg_admission_auto_gradebook_templates --stop-after-init \
  --http-port=8099 --log-level=test
```

Resultado: `0 failed, 0 error(s) of 6 tests`. Evidencia: `artifacts/green-install.txt`.

## Syntax

```bash
python3 -m py_compile addons-extra/extrairg/irg_admission_auto_gradebook_templates/models/op_admission.py \
  addons-extra/extrairg/irg_admission_auto_gradebook_templates/tests/test_auto_gradebook_templates.py
```

OK.
