# Changelog: 2026-05-28 - Implement Quarterly Admission Registers Module

## [16.0.1.0.0] - 2026-05-28

### Added
*   New custom module `irg_quarterly_admission_registers`.
*   Overridden `_compute_period` on `sale.order` to compute periods in a natural quarterly format (`YYYY-01` for Q1, `YYYY-02` for Q2, `YYYY-03` for Q3, `YYYY-04` for Q4) when academic programs are present in the order lines.
*   Overridden `_find_or_create_register` on `sale.order` to determine the correct quarterly period based on the line's start date (falling back to order admission date or today) and applying modal offset shifts (HomeClass and Presencial).
*   Context flag cleaning: Clears the `irg_get_lot_line_id` key from context inside `_find_or_create_register` before calling the super method to prevent subsequent wizards or overrides from altering the calculated quarterly period.
*   Overridden `gat_date_max_register` on `sale.order` to set the registration boundary limits to the last calendar day of the corresponding natural quarter.
*   Overridden `create` and `write` on `op.admission.register` to automatically align `start_date` and `end_date` of academic courses' registers to the boundaries of the natural calendar quarter corresponding to their period (e.g. period `2029-03` forces `start_date='2029-07-01'` and `end_date='2029-09-30'`).
*   Added Diplomados Exclusion logic: any course/product with a category code starting with `'DI'` (case-insensitive) is excluded from the quarterly period computation, quarterly boundaries, and register date alignment (falling back to standard monthly logic).
*   Updated `irg_sale_manual_confirmation_wizard` to detect Diplomados (category `'DI'`) automatically under HomeClass (`'HC'`) modality, routing them to the default HomeClass welcome email template and generating monthly batch codes (e.g., `'DIIAHC2606'`).

### Verification
*   Successfully installed the module in the local Odoo 16 development database.
*   Passed all 9 automated test cases defined in the validation script `scratch/test_quarterly_registers.py` in the Odoo shell.
    *   4 test cases verifying date boundary conversions to periods `YYYY-01` to `YYYY-04`.
    *   4 test cases verifying quarterly period end dates mapped by `gat_date_max_register`.
    *   1 test case verifying start_date and end_date auto-alignment on register creation for period `2029-03`.
*   Passed the Diplomados integration validation using `scratch/test_diplomados_wizard.py` in the Odoo shell:
    *   Verified category `'DI'` maps course `'IA'` (June 2026) to modality `'HC'`.
    *   Verified it generates the correct monthly batch code preview `'DIIAHC2606'`.


