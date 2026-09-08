# Execution — irg-business-api-gradebook-certificate

## Base

- Branch: `Dev_iRG`
- HEAD: `8548223716c621944590dd250324c599b28fbbaa`
- Pre-existing dirty/untracked files (do not touch): `.gitignore`, `.obsidian/`, other missions, `graphify-out/`, `scratch/`, `test_mnc_out.docx`, forum-notice superpowers docs.

## Approach

Inline TDD in this session. Review and Validation use distinct subagents after GREEN.

## RED

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_api_gradebook_cert \
  -i irg_gradebook_certificates,irg_certificate_partial,irg_business_api \
  --test-enable --test-tags /irg_business_api --without-demo=all \
  --max-cron-threads=0 --stop-after-init --http-port=8099 --log-level=test --workers=0
```

Result: `0 failed, 4 error(s) of 62 tests`. Cause: `Unknown or unpublished operation.` on the generate success/idempotency tests. Evidence: `artifacts/red-tests.txt`.

## GREEN

```bash
python3 -m py_compile \
  addons-extra/extrairg/irg_business_api/models/api_constants.py \
  addons-extra/extrairg/irg_business_api/models/api_operation.py \
  addons-extra/extrairg/irg_business_api/models/gradebook_service.py \
  addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py

docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_api_gradebook_cert \
  -u irg_business_api --test-enable --test-tags /irg_business_api \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test --workers=0
```

Result: `0 failed, 0 error(s) of 62 tests`. `_fill_template` ran; `_convert_to_pdf` stubbed in tests. Evidence: `artifacts/green-tests.txt`.

## Fallback

Not used. Official wizard `action_generate` + `_convert_to_pdf` patch was enough.

## Review

Independent reviewer: APPROVE, no blocking findings. File: `02b-review.md`.
MENOR (not implemented this round; would reopen Review/Validation): snapshot PDF retention cron, read `attachment.public` instead of literal, comment on preview wizard create, distinct error messages, extra tests.

Retention decision documented in contract, README and knowledge: snapshots keep `file_b64`; `unlink` remains denied; no purge cron in 16.0.1.2.0.

## Validation

Independent validator: `verification.json` status `passed`. `0 failed, 0 error(s) of 62 tests`. E2E skipped (no web surface in the diff).

## Documentation

- `missions/irg-business-api-gradebook-certificate/CHANGELOG.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_business_api_gradebook_certificate.md`
- Contract/README/module doc: retention of `file_b64` in `result_snapshot`

No production code changed in this phase.
