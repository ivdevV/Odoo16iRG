# Validation — irg-business-api-gradebook-certificate

**Validator:** independent agent (not the coder)  
**Date:** 2026-09-07  
**Base commit:** `8548223716c621944590dd250324c599b28fbbaa`  
**Runtime:** `docker-compose.local.yml`, container `odoo16irg_local`, DB `test_irg_api_gradebook_cert`

---

## Check 1 — syntax_py_compile

**Command:**
```bash
python3 -m py_compile \
  addons-extra/extrairg/irg_business_api/models/api_constants.py \
  addons-extra/extrairg/irg_business_api/models/api_operation.py \
  addons-extra/extrairg/irg_business_api/models/gradebook_service.py \
  addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py \
  addons-extra/extrairg/irg_business_api/tests/common.py \
  addons-extra/extrairg/irg_business_api/tests/__init__.py
```

**Result:** PASS  
**Evidence:** Exit code 0, no output — all 6 files compile without error.

---

## Check 2 — odoo_module_tests

**Command:**
```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_api_gradebook_cert \
  -u irg_business_api --test-enable --test-tags /irg_business_api \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test --workers=0
```

**Result:** PASS  
**Exact result line:**
```
odoo.tests.result: 0 failed, 0 error(s) of 62 tests when loading database 'test_irg_api_gradebook_cert'
```
**Stats line:**
```
odoo.tests.stats: irg_business_api: 76 tests 1.65s 4163 queries
```

**New test class — TestGradebookCertificateOperation (10 tests, all passing):**
- `test_approve_does_not_queue_certificate_mail`
- `test_approve_returns_private_pdf_and_checksum`
- `test_final_certificate_requires_done_gradebook`
- `test_invalid_signer_rejected`
- `test_missing_signer_rejected`
- `test_partial_allows_open_gradebook`
- `test_physical_requires_shipping`
- `test_same_idempotency_key_does_not_duplicate`
- `test_unknown_payload_key_rejected`

**Evidence:** `missions/irg-business-api-gradebook-certificate/artifacts/validation-tests.txt`

---

## Check 3 — e2e_testsprite

**Result:** SKIPPED  
**Justification:** The mission diff is confined to Python production code (`models/api_constants.py`, `models/api_operation.py`, `models/gradebook_service.py`), tests and documentation of `irg_business_api`. It does not touch `views/`, `templates/`, `report/`, `static/`, portal, `website`, or HTTP controllers. Per AGENTS.md E2E policy, the check is recorded as skipped with this scope detail.

---

## Check 4 — git_scope

**Command:**
```bash
git diff --name-only HEAD -- addons-extra/extrairg/irg_business_api/ doc/modules/extrairg/irg_business_api.md
git ls-files --others --exclude-standard addons-extra/extrairg/irg_business_api/ doc/modules/extrairg/irg_business_api.md
```

**Result:** PASS  
**All production edits confirmed under:**
- `addons-extra/extrairg/irg_business_api/README.md`
- `addons-extra/extrairg/irg_business_api/__manifest__.py`
- `addons-extra/extrairg/irg_business_api/doc/api-contract.md`
- `addons-extra/extrairg/irg_business_api/models/api_constants.py`
- `addons-extra/extrairg/irg_business_api/models/api_operation.py`
- `addons-extra/extrairg/irg_business_api/models/gradebook_service.py`
- `addons-extra/extrairg/irg_business_api/tests/__init__.py`
- `addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py` (new)
- `doc/modules/extrairg/irg_business_api.md`

No production edits outside `irg_business_api/` or the permitted docs path. Pre-existing dirty files (`.obsidian/`, other missions, `graphify-out/`) are pre-existing and not counted.

---

## Global verdict

**PASS global**

All checks passed or are skipped with justified reasons. No failures.
