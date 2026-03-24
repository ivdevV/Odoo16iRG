# GitHub Copilot Instructions — Odoo 16 IRG Workspace

## Project Overview

This is an **Odoo 16** deployment for an educational institution (ISEP/IRG). The stack runs in Docker (services: `odoo_latest`, `pgodoo_latest`, `nginx`, `redisodoo`) with all custom code living under `addons-extra/`.

## Non-Negotiable Rules

1. **Never modify native Odoo modules.** All changes must be implemented as extra modules using `_inherit`.
2. **New modules always go in `addons-extra/extrairg/`** with the prefix `irg_` (e.g. `irg_sale_order_override`).
3. **Target version is Odoo 16.** Follow the official Odoo 16 documentation and API.
4. **A micro-spec must be written first** (in `doc/micro-specs/`) before implementing any new module. Use the template in `SPECIFICATIONS.md`.
5. **Emit a clear, concise changelog** at the end of every task.

## Module Scaffolding Requirements

Every `irg_*` module must have:
- `__manifest__.py` — `version: '16.0.x.x.x'`, explicit `depends`, `installable: True`, `license`
- `__init__.py`
- `models/` — Python logic using `_inherit`
- `views/` — XML using `inherit_id` + `xpath` (no editing native XML)
- `security/ir.model.access.csv` — required whenever new models are added
- `tests/` — at minimum for critical business logic

## Coding Standards

### Python
- Use `_inherit` (never modify source). Override with `super()`.
- Justify every `sudo()` call with a comment.
- All user-facing strings must be wrapped in `_()` for translation.
- Avoid raw SQL unless clearly justified; document it when used.
- Validate JSON stored in `fields.Text` in `create`/`write` or via `@api.constrains`.
- Do not expose endpoints without CSRF protection, authentication, and permission checks.

### XML / QWeb
- Do **not** use unsupported XML namespaces (`x-on:click`, `x-bind:class`, etc.) — they break Odoo's XML parser.
- Use stable XPath anchors (`//field[@name='...']`, `//button[@name='...']`) — avoid positional XPaths.
- Sanitize all content rendered with `t-raw`.
- Maintain correct XML tag structure; no unclosed or duplicate tags.

### JavaScript / Assets
- Register all external libraries in `web.assets_frontend` (or the appropriate bundle).
- Guard CDN-loaded libraries defensively: `if (window.LibName) { ... }`.
- Do not mix JS templating syntax that conflicts with QWeb/XML parsing.

## Key Architectural Areas

### Subscription / Payment Flow
- **Schedule choreographer:** `isep_sale_subscription_extension` (`addons-extra/addons_uisep/`)
- **Recurring cron:** `isep_sale_order_cron_payment`
- **Tokenized payments:** `isep_payment_cron`
- **E-commerce entry:** `isep_website_sale_custom` (controllers) + `irg_sale_subscription_esp` (Spanish override)
- See repo memory `odoo16_subscription_architecture.md` for method-level hotspot map.

### Forum / Karma
- Base: `website_forum` (native Odoo)
- Custom addons: `irg_forum_batch_visibility`, `irg_forum_email_notify`, `irg_forum_followers_post_notify`, `irg_forum_post_comments_limit`, `irg_forum_notice_popup`, `irg_forum_disable_karma`, `irg_forum_web_editor_save_guard`
- See repo memory `odoo16_forum_karma_validation.md` for karma field reference.

### E-learning / Education
- OpenEduCat-based academic modules under `addons-extra/addons_uisep/`
- Custom overrides: `irg_academic_adaptations`, `irg_campus_course_forum`, `irg_op_*`, `irg_quiz_auto_scoring`, `irg_survey_*`, `irg_timetable_*`

## Docker / Testing Commands

```bash
# Run Odoo command inside the container
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf <args> --db_host=pgodoo_latest

# Install a module
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> -i irg_module_name --stop-after-init --db_host=pgodoo_latest

# Update a module
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> -u irg_module_name --stop-after-init --db_host=pgodoo_latest
```

- Container name: `odoo_latest`; DB container: `pgodoo_latest`
- The `odoo.conf` sets `db_host = nat16_pgodoo_latest` (for production); use `--db_host=pgodoo_latest` override for local testing.
- See repo memory `odoo16_local_docker_testing.md` for known testing gotchas.

## Pre-merge Checklist

Before finishing any implementation, verify:
- [ ] Module is in `addons-extra/extrairg/` with `irg_` prefix.
- [ ] `__manifest__` has correct `version` (`16.0.x.x.x`), `depends`, and `installable: True`.
- [ ] `data` list order in manifest is correct (security CSV before views).
- [ ] No native Odoo files were modified.
- [ ] `ir.model.access.csv` present if new models added.
- [ ] XML has no unsupported namespaces and valid structure.
- [ ] XPaths are stable semantic anchors.
- [ ] Tests added for critical logic.
- [ ] All strings translatable with `_()`.
- [ ] No unsecured endpoints or unjustified `sudo()`.
- [ ] Changelog written.

## Micro-spec Template Location

`doc/micro-specs/YYYY-MM-DD-irg_module_name.md` — follow the 10-section template in `SPECIFICATIONS.md`.
