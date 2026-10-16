QUALITY OK

## Blocking checklist

| Criterion | Result |
| --- | --- |
| Helper `irg_batch_code_is_official_master` present and used | Pass — defined in `models/op_admission.py`, imported in tests, covered by `test_prefix_helper`. |
| `sudo()` in action or tests | Pass — none found. |
| Action sends mail immediately | Pass — `action_send_unimarconi_mail` returns `ir.actions.act_window` on `mail.compose.message` only. |
| View hides button by admission `state` | Pass — visibility is `irg_show_unimarconi_mail` only; no state in attrs. |
| Tests assert required `UserError` cases | Pass — non-MO (`MO` in message), empty email (`correo`), missing template (`plantilla`); composer action asserted separately. |
| Manifest includes admission form view | Pass — `views/op_admission_views.xml` in `data`. |

## Notes (non-blocking)

- Empty-email test clears DB `op_admission.email` and partner email, then invalidates caches; action validates `(self.email or '').strip()`, which matches the related-field behavior described for `isep_openeducat_sale`.
- `test_button_flag_follows_batch_code` confirms flag stays true when `state` is set to `done`, aligned with acceptance criterion 1.
