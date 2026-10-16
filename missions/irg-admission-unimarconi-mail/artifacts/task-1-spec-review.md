SPEC OK

## Requirements met

Task 1 is visibility only. The mail action, template, and header button stay out of this cut, as the brief defers them.

The module skeleton matches the brief and the spec module contract for this cut:

- Technical name `irg_admission_unimarconi_mail`, version `16.0.1.0.0`.
- Depends on `openeducat_admission` and `mail`.
- No new model and no `ir.model.access.csv`.
- `data` is empty. Views and the mail template are later tasks.
- Package imports load `models/op_admission.py` and `tests/test_unimarconi_mail.py`.

`irg_batch_code_is_official_master` is `(code or '').strip().upper().startswith('MO')`. That is the brief's helper and the spec rule: ignore a missing code, drop surrounding whitespace, compare in uppercase, and require the `MO` prefix. `False` and `''` are hidden. `MIAMONL…` stays hidden because `MO` is not the prefix.

`op.admission.irg_show_unimarconi_mail` is a non-stored Boolean. The compute depends on `batch_id` and `batch_id.code`, reads the batch code only when a batch is set, and otherwise passes `''`. It does not read `state`, so the flag stays on for every admission state when the prefix matches. No `sudo()`.

The two tests keep every assertion from the brief:

- Helper: `MOPCONL2606`, `  moabc`, and `MONLHC2601` are true; `MPTEST01`, `MBTEST01`, `MIAMONL2601`, `''`, and `False` are false.
- Flag: `MOPCONL2606`, `moabc2601`, and `MONLHC2601` are true; `MPTEST01`, `MBTEST01`, `MIAMONL2601`, and no batch are false. The official admission is `draft`, then `done`, and the flag stays true.

That covers the spec visibility table and the testing line for `MO`, `mo`, `MONL`, `MP`, `MB`, `MIA`, and an empty batch. Representative codes stand in for the other `MO…` examples (`MOPCIN…`, `MONLPRS…`, `MONLONL…`); the same prefix rule covers them.

## Missing or extra behavior

No missing visibility behavior. No extra product behavior: the field is not stored, the helper is not duplicated elsewhere, and this cut does not open the composer or send mail.

The only additions beyond the brief are the authorized course `lang` value and the class tag below. `lang` is fixture data so `op.course` can be created; the production helper and compute do not use it.

## post_install tag

Acceptable. `@tagged('post_install', '-at_install')` does not change the required assertions, skip a case, or alter product behavior. It only moves these tests out of the at-install phase, so `-u` runs them after `op.course.lang` exists and the authorized `lang` value is valid. Both visibility tests still execute with the assertions the brief requires.
