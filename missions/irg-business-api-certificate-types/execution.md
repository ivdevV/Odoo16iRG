# Execution — irg-business-api-certificate-types

## Base

- Branch: `Dev_iRG`
- HEAD: `70cd1fe3a2d111dd90039e030ae7515b6524f991`
- Pre-existing dirty/untracked (do not touch): `.gitignore`, `.obsidian/`, other missions, `graphify-out/`, `scratch/`, `test_mnc_out.docx`, forum-notice superpowers docs.

## Approach

Inline TDD in this session. Review and Validation use distinct subagents after GREEN.

## RED

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_api_gradebook_cert \
  -u irg_business_api --test-enable --test-tags /irg_business_api \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test --workers=0
```

Result: `2 failed, 3 error(s) of 69 tests`. Cause: `document_type must be gradebook or gradebook_partial` on enrollment/diploma; `session_id` still unpublished. Attendance HC tests skipped (`irg_certificate_attendance` not on this DB). Evidence: `artifacts/red-tests.txt`.

## GREEN

```bash
python3 -m py_compile \
  addons-extra/extrairg/irg_business_api/models/api_constants.py \
  addons-extra/extrairg/irg_business_api/models/gradebook_service.py \
  addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py

docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_api_gradebook_cert \
  -u irg_business_api --test-enable --test-tags /irg_business_api \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test --workers=0
```

Result: `0 failed, 0 error(s) of 70 tests`. Attendance HC tests still skipped (installing `irg_certificate_attendance` would pull website/portal/Stripe). Soft reject `test_attendance_without_module_is_rejected` covers that DB. Evidence: `artifacts/green-tests.txt`, `artifacts/syntax-py-compile.txt`.

## Fallback

Not used. Notes still go through the wizard. Diploma/enrollment/attendance go through `irg.certificate.request._generate_and_attach_pdf`. Diploma tests patch `_generate_diploma_pdf_content`.

## Review

Independent reviewer: APPROVE, no blocking findings. File: `02b-review.md`.
MENOR (not implemented this round; would reopen Review/Validation): session-to-batch server check, diploma soft-dependency in preview, diploma registry `attachment_id` (preexisting, module out of scope).

## Validation

Independent validator: `verification.json` status `passed`. `0 failed, 0 error(s) of 70 tests`. Attendance HC tests skipped (module not on test DB). E2E skipped (no web surface in the diff).

## Documentation

- Contract/README/module doc: tipos diploma/asistencia/matrícula.
- Knowledge: split wizard vs request, diploma ReportLab, fuera diplomados/actas.
- `CHANGELOG.md` 16.0.1.3.0

No production code changed in this phase.
