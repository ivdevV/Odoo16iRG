# Fecha de inicio de clases en diplomas de diplomados — Design

## Objective

The phrase «celebrado del … al …» on diplomado diplomas must use the batch
**class start date** (`op.batch.date_start_class`), not the batch start date
(`op.batch.start_date`).

A later change of that class start date on the batch must appear on the **next**
download from campus or backend. PDFs already saved on a student's device are
out of reach and are not in scope.

## Current Problem

Three independent copies freeze the wrong date:

1. The generation wizard (`irg.diplomado.wizard`) defaults `start_date` from
   `student_course.batch_id.start_date`.
2. The dedicated portal (`irg_diplomado_portal_request`) writes
   `batch.start_date` when creating `irg.diplomado.registry`.
3. The PDF is stored on `irg.diplomado.registry.attachment_id`.
   `action_reprint()` and both portal download paths reuse that attachment when
   it exists, so editing the batch date does not change what the student gets.

The visible sentence is built in ReportLab from `data['start_date']`, which
comes from `registry.start_date`. QWeb in `diplomado_templates.xml` is not the
runtime path for issued files.

## Knowledge

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
  — new `irg_` addon under `addons-extra/extrairg/`, inherit only, never edit
  existing modules.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_portal_request.md`
  — portal creates or reuses `irg.diplomado.registry` and downloads via
  `action_reprint()` only when the PDF is missing.
- `.agents/knowledge/odoo_development_modding/artifacts/portal_diplomados_download.md`
  — older campus path `/campus/certificates/download/diplomado/<id>` has the
  same missing-attachment regeneration pattern.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_website_verify_qr.md`
  — `irg_generacion_diplomados_website_verify` owns `_get_diplomado_pdf_data()`
  and replaces `action_reprint()` without `super()`.
- `doc/flujo_automatricula_analisis.md` — `date_start_class` lives on `op.batch`
  via `isep_data_master_make` and is distinct from `start_date`.

## Decisions

1. **Date source:** celebration start on new and re-downloaded diplomas is
   `batch.date_start_class`.
2. **Fallback:** if `date_start_class` is empty, use `batch.start_date` so the
   diploma is not printed with a blank date.
3. **Stale PDF:** staff **Reimprimir** always rebuilds the PDF. Portal
   download rebuilds when the stored PDF is missing **or** `registry.start_date`
   is set and differs from the live batch class start. Empty `start_date` plus
   an existing attachment is left as-is (the fixture pattern of the older
   portal tests; issued diplomas always persist a start_date). No mass job.
   No on-write hook on `op.batch`.
4. **End date and issue date:** unchanged. End date stays `batch.end_date` on
   first create and is not resynced. Issue date stays the existing 26 September
   rule from `irg_generacion_diplomados_fixed_issue_date`.
5. **Wizard override:** the wizard may still show an editable `start_date`. The
   next download overwrites it with the batch class start date. That is
   intentional.
6. **Attachment:** overwrite `attachment_id.datas` in place. Do not create a
   second attachment per download.
7. **Out of scope:** graduation diplomas (`irg.diploma.registry` /
   `irg_diploma_graduacion_student`), files already on student devices, and
   changing celebration end date.

## Architecture

New addon `irg_generacion_diplomados_class_start_date` under
`addons-extra/extrairg/`. Existing addons stay untouched.

```text
irg_generacion_diplomados_class_start_date/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── portal.py
├── models/
│   ├── __init__.py
│   └── diplomado_registry.py
├── tests/
│   ├── __init__.py
│   └── test_class_start_date.py
└── wizard/
    ├── __init__.py
    └── diplomado_wizard.py
```

Depends:

- `irg_generacion_diplomados`
- `isep_data_master_make` (`date_start_class`)
- `irg_generacion_diplomados_website_verify` so this module's `action_reprint`
  wins MRO and can call `_get_diplomado_pdf_data()`
- `irg_diplomado_portal_request`
- `irg_campus_diplomados_portal`

`auto_install` is false. The module is installed explicitly per environment.

### Components

| Unit | Responsibility |
| --- | --- |
| `irg.diplomado.registry` inherit | Resolve the student's batch for the course; sync `start_date`; always regenerate PDF in `action_reprint`. |
| `irg.diplomado.wizard` inherit | After `super()` on student/course onchange, set `start_date` from class start date. |
| Portal controller inherit | Dedicated portal: create registry with class start date; always call `action_reprint` before sending the file. |
| Campus controller inherit | Certificates path: always call `action_reprint` before sending the file. |

### Batch resolution

Used by reprint/download sync. First match wins:

1. `op.student.course` for `registry.student_id` and `registry.course_id`,
   preferring `state == 'finished'`, otherwise any line, `id desc`.
2. Else `app.gradebook.student` for the same student and course, `id desc`,
   using `gradebook.batch_id`.
3. Else do not change `registry.start_date`.

If a batch is found: `start_date = batch.date_start_class or batch.start_date`.

### Data flow

**New diploma (wizard)**

1. Onchange loads `start_date` from `date_start_class` (fallback `start_date`).
2. Confirm stores that value on `irg.diplomado.registry` and generates the PDF
   as today.

**New diploma (portal `/campus/diplomados/...`)**

1. Create registry with `start_date` from the gradebook batch's class start
   date (same fallback).
2. Download always calls `action_reprint`.

**Existing diploma (any download or Reimprimir)**

1. Resolve batch.
2. Write `registry.start_date` if the resolved date differs.
3. Render PDF with `_get_diplomado_pdf_data()` (QR and stamp unchanged).
4. Write the binary onto the existing `ir.attachment`, or create one if missing.
5. Return the file.

If PDF generation fails, keep the previous attachment and surface the existing
portal `no_pdf` error. Do not leave `attachment_id` empty.

## Security and historical documents

This change mutates an already issued PDF by design. Access rules on
`irg.diplomado.registry` do not change. Portal downloads stay scoped to the
logged-in student's partner, as today. No new model, no `sudo()` beyond what
the inherited portal already uses. No deletion of registry rows.

## Testing

Module tests (Odoo `TransactionCase` / `HttpCase` where the portal already uses
it):

1. Wizard onchange: `date_start_class` distinct from `start_date` → wizard
   `start_date` equals class start date.
2. Wizard onchange: empty `date_start_class` → fallback to `batch.start_date`.
3. Portal `_create_diplomado_registry` uses class start date, not batch start.
4. `action_reprint` with an existing attachment: after changing
   `batch.date_start_class`, `registry.start_date` and the PDF payload use the
   new date; `attachment_id` is the same record.
5. `action_reprint` with no batch found: `start_date` unchanged; PDF still
   regenerates from stored fields.
6. Dedicated portal `_send_diplomado_file` calls `action_reprint` even when the
   attachment already exists (mock reprint if needed to avoid full ReportLab
   in the HTTP test).

E2E (`e2e_testsprite`) is mandatory because the diff inherits HTTP portal
controllers. It runs only after module tests pass, against local
`docker-compose.local.yml` port `8069` and a disposable database.

## Acceptance

- A new diplomado diploma prints «celebrado del {date_start_class} al {end_date}».
- Changing `date_start_class` on the batch and downloading again (portal or
  Reimprimir) prints the new class start date.
- The registry keeps a single PDF attachment.
- Graduation diplomas and celebration end dates are untouched.
