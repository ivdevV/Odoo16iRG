# irg_hide_certifies_button — Design

**Date:** 2026-06-12
**Status:** Approved

## Problem

The op.student form header shows two buttons: "Generar Diploma"
(`irg_generacion_diplomas`, the current flow) and "Certifies / Diplomas"
(legacy wizard from `isep_openeducat_reports`,
`addons-extra/addons_uisep/isep_openeducat_reports/views/op_student_view.xml`).
Only "Generar Diploma" should remain.

## Solution

New module `addons-extra/extrairg/irg_hide_certifies_button` (project rule: do
not modify `addons_uisep` modules; ship fixes as new `extrairg` modules).

- View inheriting the `isep_openeducat_reports` student form extension,
  removing the button via xpath match on its `string`:
  `//button[@string='Certifies / Diplomas']` → `position="replace"`.
- Depends: `isep_openeducat_reports`.
- Reversible: uninstalling the module brings the button back.

## Tests

`get_view()` on the op.student form: rendered arch must not contain
"Certifies / Diplomas" and must still contain "Generar Diploma" (when
`irg_generacion_diplomas` is installed).
