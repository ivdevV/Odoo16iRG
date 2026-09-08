# Validación — irg-admission-register-export-nationality

Validador independiente. Sin edición de código de producción ni de tests del módulo.
Runtime: `docker-compose.local.yml`. Base desechable: `test_irg_arex_nat_val_20260908`.
HEAD: `0fc4765def6f0f082eec28f4d303f589b98718c1`. Capacidad: `standard`.

## Tareas / checks

### syntax_py_compile — PASS

Comando:

```
python3 -m py_compile \
  addons-extra/extrairg/irg_admission_register_export/wizard/admission_export_wizard.py \
  addons-extra/extrairg/irg_admission_register_export/tests/test_admission_export.py \
  addons-extra/extrairg/irg_admission_register_export/tests/__init__.py
```

Evidencia: exit 0. Sin salida de error. Registrado en `artifacts/validation-summary.txt` (`PY_COMPILE_OK`).

### odoo_test_suite — PASS

Base nueva creada con `CREATE DATABASE test_irg_arex_nat_val_20260908 TEMPLATE odoo16irg_local;` (no se reutilizó `test_irg_arex_nat_red_20260908`).

Comando:

```
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_arex_nat_val_20260908 \
  -i irg_admission_register_export --test-enable \
  --test-tags=/irg_admission_register_export --stop-after-init \
  --http-port=8098 --log-level=test --workers=0
```

Evidencia real (`artifacts/validation-tests.txt`):

```
Starting TestAdmissionRegisterExportNationality.test_export_includes_student_nationality ...
Starting TestAdmissionRegisterExportNationality.test_export_nationality_empty_without_student_or_value ...
odoo.tests.stats: irg_admission_register_export: 4 tests 0.10s 221 queries
odoo.tests.result: 0 failed, 0 error(s) of 2 tests when loading database 'test_irg_arex_nat_val_20260908'
```

Resumen: `artifacts/validation-summary.txt`.

### e2e_testsprite — PASS (skipped justificado)

No ejecutado. Justificación: el diff no toca vistas/QWeb, `static/`, portal, `website`, controladores HTTP ni plantillas de diploma/certificado; solo Python del wizard y tests. Declarado en `plan.md`.

## Limpieza

`DROP DATABASE` de `test_irg_arex_nat_val_20260908` y `test_irg_arex_nat_red_20260908`. Confirmado 0 filas restantes en `pg_database` para esos nombres. Servicio `odoo_local` sigue `Up`; comando `["odoo","-c","/etc/odoo/odoo.conf"]` (sin `-d` a las bases de prueba). Evidencia: `artifacts/cleanup.txt`.

## Gate

`verification.json`: `status: passed`.

PASS global
