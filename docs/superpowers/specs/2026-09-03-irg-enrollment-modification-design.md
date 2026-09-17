# Modificación de matrícula — Design

## Objective

Add a custom Odoo 16 module that lets Academic staff open a wizard from the
student form, capture an enrollment-change request, fill the official Word
template, and keep the file on the student chatter. Academic approval writes
course, batch, modality and academic year. Accounting approval writes the
payment mode. The final PDF is attached only when the request is closed.

## Current Problem

Enrollment changes (course, batch, modality, academic year, payment mode) are
handled outside Odoo with a paper Word form. There is no button on `op.student`,
no structured request, and no audit trail in Actividades besides ad-hoc
messages.

## Knowledge

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
  — new `irg_` addon, inherit only, never edit existing modules.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_student_campus_block.md`
  — header button on `op.student`, `groups` plus server-side `has_group()`,
  chatter without `sudo()` for the author.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diploma_graduacion_student.md`
  — student wizard, `ir.attachment` on `op.student`.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_physical_certificates_docx_layout.md`
  — `python-docx` fill and LibreOffice conversion to PDF.

## Architecture

New addon `irg_enrollment_modification` under `addons-extra/extrairg/`.
Existing addons stay untouched. The student header button is injected with
xpath on `openeducat_core.view_op_student_form`.

```text
irg_enrollment_modification/
├── __init__.py
├── __manifest__.py
├── data/
│   └── ir_sequence_data.xml
├── models/
│   ├── __init__.py
│   ├── enrollment_change.py
│   └── op_student.py
├── reports/
│   └── enrollment_change_document.py
├── security/
│   ├── enrollment_change_security.xml
│   └── ir.model.access.csv
├── static/src/templates/
│   └── modificacion_matricula.docx
├── tests/
│   ├── __init__.py
│   └── test_enrollment_change.py
├── views/
│   ├── enrollment_change_views.xml
│   └── op_student_views.xml
└── wizard/
    ├── __init__.py
    ├── enrollment_change_wizard.py
    └── enrollment_change_wizard_views.xml
```

The Word template is the file provided at
`/Users/ivrogo/Downloads/Modificación de matrícula.docx`, copied into the
module. The template layout is not redesigned.

### Components

| Unit | Responsibility |
| --- | --- |
| `op.student` inherit | Header button; opens the wizard with `active_id`. |
| `irg.enrollment.change.wizard` | Transient form: origin enrollment + five expandable changes. Creates the request and the Word. Writes nothing to course or sale order. |
| `irg.enrollment.change` | Persistent request (`mail.thread`). States, approvals, chatter. Server-side ACL on each action. |
| Document builder | Fills labels on the Word (`python-docx`). Converts to PDF with LibreOffice only when the request closes successfully. |
| Academic approve | Writes marked academic fields on the origin `op.student.course` (and modality on the linked sale order line). |
| Accounting approve | Writes `payment_mode_id` on the linked `sale.order`. |

### Data flow

1. Academic user clicks **Modificación de matrícula** on `op.student`.
2. Wizard requires an origin `op.student.course` even if there is only one.
3. Each marked change expands to read-only origin and required destination.
4. Confirm creates `irg.enrollment.change` in `submitted`, posts `solicitud.docx`
   on the student chatter, and does not write enrollment or payment.
5. Academic approve writes marked academic fields. If payment is not marked,
   state becomes `done` and `final.pdf` is posted on the student chatter.
6. If payment is marked, state becomes `waiting_finance`. No PDF yet.
7. Accounting approve writes payment mode, state becomes `done`, posts
   `final.pdf` with Área Financiera marked.
8. Refuse:
   - From `submitted` (Academic): no enrollment or payment write. No PDF.
     Original Word stays. State `refused`.
   - From `academic_approved` (Accounting): academic writes already applied
     are not reverted. Payment is not written. No PDF. State `refused`.
     Chatter states that the academic change stands and payment was denied.

## Button and wizard

- Button string: `Modificación de matrícula`.
- Placement: form header of `op.student`, `oe_highlight` / `btn-primary`, same
  dark style as Diploma / Acta.
- Visible to the new Academic group and Settings / superuser.

Wizard fields:

- `student_id` — from context, readonly.
- `student_course_id` — required Many2one, domain `student_id`. Always shown.
- Five booleans: course, batch, modality, academic year, payment mode.
- For each True boolean: origin (computed, readonly) and destination (required).
- Batch destination domain: destination course if course is marked, else origin
  course (`op.batch.course_id`).
- Payment marked: required `sale_order_id`. Default: latest confirmed/done
  order for `student.partner_id` whose course matches the origin enrollment
  when `course_id` exists on `sale.order`. If zero or several, the user picks.
- At least one boolean must be True.
- Footer: Cancel, **Crear solicitud**.

Origin values:

- Course, batch, academic year: from `op.student.course`.
- Modality: `x_studio_modalidad` on the linked sale order line when present.
- Payment mode: `payment_mode_id` on the linked `sale.order`.

## Request model

`irg.enrollment.change` (`mail.thread`, `mail.activity.mixin`):

- `name` — sequence.
- `student_id`, `student_course_id`, `sale_order_id`.
- Booleans and origin/destination snapshots for the five change types
  (stored at create so later edits of the student do not rewrite the form).
- `state`: `submitted` → `academic_approved` → `done` | `refused`.
  `academic_approved` is the waiting-finance state and is only used when
  payment is marked.
- `academic_user_id`, `academic_date`, `finance_user_id`, `finance_date`,
  `refuse_user_id`.
- `request_attachment_id`, `final_attachment_id`.

Academic write (in place on `student_course_id`, only marked fields):

- `course_id`, `batch_id`, `academic_years_id`.
- Modality: `x_studio_modalidad` on the sale order line(s) of `sale_order_id`
  when that field exists. `op.student.course` has no modality field.

Finance write: `sale_order_id.payment_mode_id`.

Refuse from `submitted` writes no enrollment or payment fields. Refuse from
`academic_approved` does not revert the academic write and does not write
payment.

## Document fill

The template has no merge fields. The builder finds the existing labels and
writes after them, preserving layout.

| Label | solicitud.docx | final.pdf |
| --- | --- | --- |
| Fecha de solicitud | Today | Same |
| Delegación | `sale.order.team_id` or student commercial team; empty if missing | Same |
| Nombre y apellidos | `op.student.name` | Same |
| Cambio de curso/grupo | Filled only if course and/or batch marked. Origin and destination concatenated into that section. | Same |
| Cambio de modalidad | Filled only if marked | Same |
| Cambio de año académico | Filled only if marked | Same |
| Cambio de forma de pago | Filled only if marked | Same |
| Firma del alumno | Empty | Empty |
| Propuesta hecha por | Creating user | Same |
| X Área académica | As in the template | As in the template |
| Resolución / APROBADA / DENEGADA | Empty | X APROBADA and resolver name |
| Área financiera | Empty | Marked only if accounting approved |

Unmarked sections stay blank on both files.

Denied requests do not generate a PDF.

PDF conversion uses LibreOffice, same approach as
`irg_gradebook_certificates`. If conversion fails after a successful approve,
the data write stays; the user can retry PDF generation from the request.

## Security

New category/group `Departamento académico (matrícula)`
(`irg_enrollment_modification.group_academic`).

| Action | Who |
| --- | --- |
| Button, create request, academic approve, refuse from `submitted` | `group_academic` and Settings |
| Finance approve or refuse from `academic_approved` | `account.group_account_invoice` and Settings |
| Academic users cannot finance-approve | Enforced with `has_group()` in the method, not only `groups` on the button |

ACL: Academic users get create/read/write on the request and wizard.
Accounting users get read plus the finance method. No portal access.

`sudo()` is allowed only for the narrow writes to `op.student.course` and
`sale.order` after the acting user has passed the group check. Chatter posts
run as the acting user.

## Errors

Stop the action; do not leave a partial write:

- Missing origin enrollment or no change marked.
- Marked change without destination.
- Payment marked without `sale_order_id`.
- Destination batch not belonging to the destination (or origin) course.
- Unique `(student, course, batch)` collision after the academic write.
- Unauthorized approve/refuse → `AccessError`, no write.

## Testing

Runtime: `docker-compose.local.yml`. TDD on
`irg_enrollment_modification/tests/`. Disposable database; cleanup after.

Module tests:

- Create posts Word on the student, does not change `op.student.course` or
  `payment_mode_id`.
- Expandable changes require destination; zero marks → `ValidationError`.
- Academic approve writes only marked academic fields; no payment mark →
  `done` + PDF.
- Payment mark → `academic_approved` and no PDF until finance approve.
- Finance approve writes `payment_mode_id` and posts PDF with Área Financiera.
- Refuse does not write and does not attach PDF.
- HTTP JSON-RPC: Academic user cannot call finance approve; accounting user
  cannot call create from the student button path.

E2E (`e2e_testsprite`): required. The diff includes student and wizard XML
views. Run after the other checks pass, against local `8069` and a disposable
DB. Never beta or production.

## Out of scope

- Capturing the student signature.
- Email to the student.
- Moodle / campus / timetable side effects of a batch change.
- Rewriting posted invoices.
- Student portal self-service.
- Redesigning the Word layout.
- Intermediate PDF while waiting for accounting.

## Publication

Work on `feat/irg-enrollment-modification` created from current `Dev_iRG`.
Push to `Dev_iRG` only after Review and Validation pass, with the
authorization given for that delivery.

## Mission classification

Full mission. Feature, new models, security groups, student chatter, sale
order payment write. Tier `standard`. Security Advisor required before
implementation (new groups, `sudo()` writes, payment mode).
