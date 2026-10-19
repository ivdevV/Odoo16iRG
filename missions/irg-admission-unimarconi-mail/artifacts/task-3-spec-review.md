SPEC OK

## Scope

Task 3 only: composer action, form button, manifest data order, and `TestUnimarconiMailAction` (plus inherited visibility used by those tests). Design spec sections on template body, dependencies beyond Task 3, and E2E are out of scope for this pass except where they constrain the action/view.

## Checklist

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| Button label **Enviar matrícula Unimarconi** | Pass | `op_admission_views.xml`: `string="Enviar matrícula Unimarconi"`; action window `name` uses the same translated string. |
| Visible only for MO batch prefix | Pass | Hidden via `attrs` on `irg_show_unimarconi_mail`; compute uses `irg_batch_code_is_official_master` (strip + upper + `startswith('MO')`). Server action repeats the same rule before opening the composer. |
| All admission states (no `state` on button) | Pass | Button has no `states` / state-based `attrs`; visibility depends only on `irg_show_unimarconi_mail`. Parent visibility test sets `state = 'done'` and flag stays true. |
| Composer opens in dialog; no immediate send from action | Pass | `action_send_unimarconi_mail` returns `ir.actions.act_window` with `res_model` `mail.compose.message`, `target` `new`, and compose form view. It does not call `send_mail` or equivalent. |
| Composition mode `comment` | Pass | Context includes `default_composition_mode`: `'comment'`. `test_official_admission_opens_composer` asserts this. |
| UserError: non-MO batch | Pass | Message: «El envío solo corresponde a lotes cuyo código empieza por MO.» Matches spec flow step 2. Test asserts `'MO'` in exception text. |
| UserError: empty email | Pass | Message: «Indica el correo de la admisión antes de enviar la matrícula Unimarconi.» Matches spec step 3 intent. Test asserts `'correo'` in message. |
| UserError: missing template | Pass | Message: «No está instalada la plantilla de matrícula Unimarconi.» Uses `env.ref(..., raise_if_not_found=False)`. Test unlinks template and asserts `'plantilla'`. |
| No `sudo()` | Pass | No `sudo` in module code (models/views/tests for this feature). |
| Resend allowed | Pass | Action has no “already sent” guard. `test_send_posts_on_chatter_and_can_be_repeated` sends once via composer, then calls action again and expects `mail.compose.message`. |
| Manifest loads view after template data | Pass | `__manifest__.py` `data`: `mail_template_data.xml`, then `op_admission_views.xml`. |
| Form view inheritance and wiring | Pass | View id `view_op_admission_form_unimarconi_mail`, inherits `openeducat_admission.view_op_admission_form`, header button + invisible helper field; tests assert arch strings and inherit target. |

## Local stack: `op.admission.email` as related field

In `isep_openeducat_sale`, `email` on `op.admission` is redefined as `related='partner_id.email'` (not stored). The action validates `(self.email or '').strip()`, which resolves the same value shown on the admission form (partner email when isep is installed).

The empty-email test nulls both `op_admission.email` (legacy column, ineffective for a non-stored related field) **and** `res_partner.email`, then invalidates caches. That correctly exercises the path users see in production: empty partner email ⇒ empty admission email ⇒ UserError, composer not opened.

`TestUnimarconiMailAction._admission` creates/links a partner when create-time email would otherwise be discarded—appropriate for related-field semantics and does not weaken the empty-email case.

## Tests vs spec (Task 3)

`TestUnimarconiMailAction` covers: non-MO blocks composer, empty email blocks composer, MO + email opens composer with template and context, missing template, chatter + repeat open, form view button/label/flag. Aligns with design spec testing bullets for action/composer (not re-validating template render or full visibility matrix here—covered by sibling test classes).

## Minor notes (non-blocking)

- Context includes `force_email`: True (from task brief); still opens wizard only—does not auto-send.
- Button uses Odoo 16 `attrs` for invisibility; matches brief; no state coupling.

## Conclusion

Implementation and `TestUnimarconiMailAction` match the design spec and Task 3 brief for the composer action and form button. No spec gaps identified for this task slice.
