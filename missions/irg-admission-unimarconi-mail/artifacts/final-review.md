APPROVED

Cross-task review of `irg_admission_unimarconi_mail` against the design spec and the implementation plan. Per-task reviews were not re-litigated. Logo file exists: `static/src/img/logo-irg.jpg` (JPEG, 587×282). No production files were edited and no tests were run.

## Cross-task checklist

| Gap | Result | Where |
| --- | --- | --- |
| Helper dropped | Present and used by the compute and the action | `models/op_admission.py` 9–10, 26, 32; imported in `tests/test_unimarconi_mail.py` 4–6 |
| Button hidden by state | Visibility is only `irg_show_unimarconi_mail`; no `states` and no state in `attrs` | `views/op_admission_views.xml` 10–13 |
| Immediate send | Action returns `ir.actions.act_window` on `mail.compose.message` with `target` `new` | `models/op_admission.py` 46–62 |
| `sudo()` | None in the module | models, views, data, tests |
| Wrong URL | Button href is `https://oficialidad.institutoraimongaja.com` | `data/mail_template_data.xml` 29 |
| Wrong colors | Callout `#0191c0`; button background `#4db4e7` and text `#ffffff` | `data/mail_template_data.xml` 22, 30 |
| Missing manifest data | Template then form view, in that order | `__manifest__.py` 9–12 |
| Tests no longer match the action | Assertions match the returned window, model, target, and context (`comment`, template, this admission) | `tests/test_unimarconi_mail.py` 170–177 vs `models/op_admission.py` 46–61 |

The server method repeats the same prefix rule as the computed flag (`strip`, `upper`, `startswith('MO')`) before it opens the composer. Empty email and a missing template raise `UserError` and do not return an action. The template is `noupdate="1"`, subject and sender match the spec, and the rendered greeting uses `first_name` or `name`.
