# Validation — irg-business-api

Independent validator. Production/addon code not edited. Checks re-executed; prior GREEN logs not trusted.

Environment: `docker-compose.local.yml` + worktree overlay. DB: `test_irg_business_api` (reused then dropped). base_commit: `41628848dbda4e0537eada3a5e67beed68e98a9c`.

## Checks

### python_compile — PASS

Command: `python3 -m compileall -q -f addons-extra/extrairg/irg_business_api`

Evidence: `COMPILE_OK exit=0` in `artifacts/validation-compile.txt`.

### xml_wellformed — PASS

Command: `xmllint --noout` on `views/api_operation_views.xml`, `security/groups.xml`, `security/ir_rule.xml`.

Evidence: all three `OK`; `XML_OK` in `artifacts/validation-xml.txt`.

### module_install — PASS

Command: `docker compose -f COMPOSE_BASE -f OVERLAY run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_business_api -i irg_business_api -u irg_business_api --without-demo=all --max-cron-threads=0 --stop-after-init --log-level=info`

Evidence (`artifacts/validation-install.txt`): module loaded (groups, ACL, rules, views); `Modules loaded.`; `exit_code=0`.

### odoo_tests — PASS

Command: `odoo -c /etc/odoo/odoo.conf -d test_irg_business_api -u irg_business_api --test-enable --test-tags /irg_business_api --without-demo=all --max-cron-threads=0 --stop-after-init --log-level=test`

Evidence (`artifacts/validation-tests.txt`):

```
38 post-tests in 1.56s, 2105 queries
irg_business_api: 46 tests 1.55s 2105 queries
0 failed, 0 error(s) of 38 tests when loading database 'test_irg_business_api'
exit_code=0
```

Suites executed: `test_access_permissions`, `test_api_read_contract`, `test_idempotency_and_concurrency`, `test_slide_draft_operations`.

### e2e_testsprite — SKIPPED (justified)

Plan declared E2E mandatory because `views/api_operation_views.xml` exists. TestSprite MCP is not available in this Cursor runtime (namespaces: cursor, cursor-app-control, cursor-ide-browser, plugin-claude-mem-mcp-search). Check recorded as skipped, not pass.

Evidence: `artifacts/validation-e2e-skip.txt`.

### cleanup — PASS

`DROP DATABASE test_irg_business_api` succeeded. Persistent `odoo16irg_local` still mounts main checkout `/Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/addons-extra`, not the worktree. No leftover `odoo_local-run` containers. Service was already exited; it was not started against the worktree.

Evidence: `artifacts/validation-cleanup.txt`.

## Acceptance criteria (from plan.md)

Covered by odoo_tests (PASS): install on test DB without native edits; paginated reads; unpublished slide draft; idempotency; no default publish/clone/enroll; preview+audit on writes; ACL (no group cannot create/approve; write cannot forge state).

PASS global
