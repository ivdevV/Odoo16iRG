# Changelog: 2026-06-01 - Auto-populate Class Start Date in op.admission

## [16.0.1.1.0] - 2026-06-01

### Added
*   Added auto-population logic for `irg_class_start_date` on `op.admission` records created/retrieved from sales orders.
*   Inherited `_create_or_get_admission` on `sale.order` in `irg_sale_manual_confirmation_wizard` to set the `irg_class_start_date` field to the value of `start_date_enroller` from the corresponding sales order line if it is present.
*   Added `irg_admission_class_start_date` module as a dependency in the manifest file of `irg_sale_manual_confirmation_wizard` to guarantee the field's existence.

### Verification
*   Successfully ran the unit tests for `irg_sale_manual_confirmation_wizard` with 100% success rate.
*   Validated the automatic synchronization using `scratch/test_class_start_date.py` via `odoo shell`. Confirming the sales order correctly propagates `line.start_date_enroller` ("2026-06-15") to the admission's `irg_class_start_date` field.
