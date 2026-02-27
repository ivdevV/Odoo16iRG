# Odoo 16 Development Guidelines & Codebase Analysis

## Core Conventions from SPECIFICATIONS.md
- **Addons Directory:** All custom modules MUST be placed in `addons-extra/extrairg/`.
- **Naming Rule:** Prefix module names with `irg_` (e.g., `irg_sale_order_override`).
- **No Core Modifications:** Never modify native Odoo modules directly. Always use standard `_inherit` techniques.
- **Micro-Specs:** A micro-spec document must be approved before implementing changes, focusing on the justification and exact scope, following the template in `doc/micro-specs/`.
- **Overrides:** Use `_inherit` for Python models and `xpath` with `inherit_id` for views.
- **Good Practices:**
  - Avoid monkey-patching native libraries.
  - Test critical logic and migrations using pytest.
  - Apply `env.ref()` and `ref()` instead of using hardcoded external IDs.
  - Add translation wrappers `_()` to strings.
  - Review ACLs and record rules, and justify any use of `sudo()`.

## Email Templates Analysis (Analysis Date: 2026-02-23)
A full codebase analysis of custom modules (`addons-extra/extrairg`, `addons_uisep`, `addons-extend`, and `addons_irg`) was performed to identify any overrides or conflicts related to **Email Templates**.

- **XML / Views:** No code extends or overrides `mail.template`, and no hardcoded references to custom email templates (`email_template_id`) were found in custom module XML files.
- **Python Models:** No custom overrides were found for core mail models (`mail.mail`, `mail.message`) or native mailing methods (like `send_mail`, `action_quotation_send`). The only template references found were strictly for `product_template_id` handling.

**Conclusion:**
There are no conflicts introduced by the custom modules regarding Odoo's native email template functionality. The codebase properly relies on Odoo's core mailing logic.
