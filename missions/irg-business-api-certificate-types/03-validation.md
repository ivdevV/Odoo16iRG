# Validation — irg-business-api-certificate-types

**Validador independiente · 2026-09-07**

---

## Check 1 — py_compile

```bash
python3 -m py_compile \
  addons-extra/extrairg/irg_business_api/models/api_constants.py \
  addons-extra/extrairg/irg_business_api/models/gradebook_service.py \
  addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py
```

**Resultado:** exit 0, sin errores de sintaxis.
**Veredicto:** PASS

---

## Check 2 — unit_tests (módulo irg_business_api)

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_api_gradebook_cert \
  -u irg_business_api --test-enable --test-tags /irg_business_api \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test --workers=0
```

**Resultado (línea de cierre de Odoo):**
```
0 failed, 0 error(s) of 70 tests when loading database 'test_irg_api_gradebook_cert'
irg_business_api: 84 tests 1.64s 4413 queries
```

Dos tests marcados `skipped` por el propio runner de Odoo:
- `test_attendance_approve_on_hc_batch` — `Attendance certificates are not installed.`
- `test_attendance_requires_session_id` — `Attendance certificates are not installed.`

Justificación del skip: `irg_certificate_attendance` no está instalado en esta DB porque
instalar ese módulo arrastra `website`, `portal` y Stripe. El plan lo declara explícitamente;
el test `test_attendance_without_module_is_rejected` cubre el rechazo soft en producción.

Evidencia completa: `artifacts/validation-tests.txt`
**Veredicto:** PASS

---

## Check 3 — attendance_hc_tests (skipped)

`test_attendance_approve_on_hc_batch` y `test_attendance_requires_session_id` se omiten porque
`irg_certificate_attendance` no está instalado. Skip justificado y documentado (ver arriba).
**Veredicto:** SKIPPED (justificado)

---

## Check 4 — e2e_testsprite

El diff toca únicamente:
- `models/api_constants.py`
- `models/gradebook_service.py`
- `tests/test_gradebook_certificate.py`
- `__manifest__.py`

Ningún archivo bajo `views/`, `templates/`, `report/`, `static/`, portal, website ni
controladores HTTP. El plan declara este check skipped. El validador lo confirma.
**Veredicto:** SKIPPED (scope no alcanza superficie web)

---

## Veredicto global

**PASS global** — 0 fallos, 0 errores en 70 tests ejecutados. 2 skips de asistencia justificados. E2E skipped por scope.
