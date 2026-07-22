# Mission Plan: Fix Oficialidad Line MO Prefix

## Objective
Enhance the master course detection logic (`MO` vs `MP` prefix generation) in:
1. `irg_sale_manual_confirmation_wizard` (`manual_confirmation_wizard.py`)
2. `irg_openeducat_sale_lote_custom` (`sale_order.py`)
3. `irg_openeducat_sale_online_quarterly` (`sale_order.py`)

So that when a sale order has a Master course line whose product name does not explicitly state "Oficial", but the sale order has a secondary line for "Oficialidad" (or any line with "oficial" / "oficialidad" in product name, template name, description, or category name), the lot code prefix is set to `MO` (Máster Oficial) instead of `MP` (Máster Propio).

## Scope & Tier
- Tier: `standard`
- Files to modify:
  - `addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/wizards/manual_confirmation_wizard.py`
  - `addons-extra/addons_uisep/irg_openeducat_sale_lote_custom/models/sale_order.py`
  - `addons-extra/addons_uisep/irg_openeducat_sale_online_quarterly/models/sale_order.py`
  - `addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/tests/test_register_date_validation.py`

## Criteria of Acceptance
1. When a Sale Order has a Master course line without "Oficial" in its name, but includes another line with "Oficialidad" in product/template/name/description/category:
   - `wizard._build_line_batch_code_preview` returns code starting with `MO`.
   - `sale_order.get_lot_id(course)` returns batch with code starting with `MO`.
2. When a Sale Order has a Master course line without "Oficial" in its name and NO "Oficialidad" line:
   - `wizard._build_line_batch_code_preview` returns code starting with `MP`.
   - `sale_order.get_lot_id(course)` returns batch with code starting with `MP`.
3. Existing unit tests in `irg_sale_manual_confirmation_wizard` pass without regression.

## Roles
- Orchestrator: Plan definition & tracking
- Encoder: TDD implementation & refactoring
- Reviewer: Code review
- Validator: Verification checks & `verification.json`
- Documenter: Documentation & changelog update
