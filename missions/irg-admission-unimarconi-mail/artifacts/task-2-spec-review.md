SPEC OK

## Scope

Review covers Task 2 only: `mail.template` data, logo asset, manifest registration, and render tests from line 87 of `test_unimarconi_mail.py`. Send action, form button, and composer flow are out of scope (Task 3).

## Design spec — mail template

| Requirement | Status | Evidence |
| --- | --- | --- |
| XML record `email_template_admission_unimarconi` on `mail.template`, `noupdate="1"` | OK | `data/mail_template_data.xml` |
| Model `op.admission` | OK | `model_id` → `openeducat_admission.model_op_admission` |
| Subject `¡Tu formulario de matrícula en Unimarconi!` | OK | `subject` field; asserted in test |
| Salute `¡Hola, {nombre}!` with `first_name`, else `name` | OK | `t-out="object.first_name or object.name"`; test uses `María` |
| `{curso}` from `course_id.name`; empty/whitespace → «Para tu máster te facilitamos…» | OK | `t-if` / `t-else` on `(object.course_id.name or '').strip()`; dedicated test |
| Body copy (Università, acompañamiento, oficialidad / italiano / expediente) | OK | Matches spec paragraphs verbatim |
| Button **Acceso a oficialidad** → `https://oficialidad.institutoraimongaja.com` | OK | `<a href="https://oficialidad...">`; test asserts label and URL |
| Plain URL below button if button fails | OK | Fallback block present (see note below) |
| Cierre: académico, WhatsApp, copyright | OK | All three strings present; tests assert email and phone |
| Aspect: logo top-left, white layout, `#0191c0` bold centered phrase, `#4db4e7` button, gray centered footer | OK | Styles and logo path; tests assert color hex values |
| Logo in module (`static/src/img/logo-irg.jpg`) | OK | File on disk (36605 bytes); `t-att-src` uses module path + `get_base_url()` |
| Default sender on template (composer default per spec send flow) | OK | `email_from` and `email_to` match brief/spec; test asserts |

## Known fix — course phrase and `<strong>`

Brief had `Para tu <strong t-out="course"/>` so only the course name was bold. Implementation uses `<strong>Para tu <t t-out="course"/></strong>`, so **Para tu** is bold together with the course name.

The design spec quotes plain text for «Para tu {curso} te facilitamos…» and does not require bold on the course name alone. It only mandates bold styling for «¡Estamos aquí para acompañarte!». This markup change therefore does **not** break the design spec; it is a minor visual drift from the Task 2 brief snippet, not from the approved design document.

Rendered plain text still matches the spec sentence (contiguous «Para tu Máster en Neuropsicología Clínica»), which the render test checks.

## Task 2 brief alignment

| Brief item | Status |
| --- | --- |
| Files created/updated as listed | OK |
| Template copy, colors, URL, button label | OK |
| Manifest `data` includes `mail_template_data.xml` | OK |
| `TestUnimarconiMailTemplate` with both render tests | OK |
| Inherits visibility setup from Task 1 | OK |

## Observations (non-blocking)

1. **Fallback URL text** — Spec says the same address appears as text under the button. The template shows `oficialidad.institutoraimongaja.com` (no `https://`), with helper copy from the brief. The link href is the full URL required by spec. Acceptable as human-readable fallback; not a functional gap.

2. **Extra line** — «Si tienes cualquier duda, puedes escribirnos:» appears before the cierre block. It is not listed in the design spec’s cierre bullets but matches the Task 2 brief and is consistent with taking aspect from the seguimiento family of templates. Required cierre lines are still present.

3. **Test coverage gaps** — No test for empty `first_name` (fallback to `name`), logo `src` in rendered HTML, or exact copyright string. Implementation covers the first in QWeb; gaps are test-only, not template spec gaps for this task.

4. **`noupdate="1"`** — Template edits after install require manual record update or DB cleanup (already noted in task report). Expected per spec.

## Out of scope (not evaluated)

- Button visibility, send method, composer action, chatter, `sudo()` rules, and visibility/send tests beyond what Task 2 added.

## Verdict rationale

All mandatory mail-template content, fields, styling, assets, and module wiring from `docs/superpowers/specs/2026-10-15-irg-admission-unimarconi-mail-design.md` are implemented. The course-name `<strong>` / `<t t-out>` adjustment preserves spec copy and does not contradict spec typography rules. No missing required element and no incorrect substitution of approved text.
