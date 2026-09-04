# Enrollment Modification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (tasks are tightly coupled in one new addon). Do not split across independent subagents. Follow TDD. Spec: `docs/superpowers/specs/2026-09-03-irg-enrollment-modification-design.md`.

**Goal:** Add `irg_enrollment_modification` so Academic staff can request an enrollment change from `op.student`, attach a filled Word form, then apply academic fields and (if marked) payment mode after separate approvals, attaching a PDF only when the request closes.

**Architecture:** New addon only. Transient wizard creates `irg.enrollment.change` and posts `solicitud.docx` on the student. Academic `action_approve_academic` writes marked `op.student.course` fields (and line modality when the field exists). Accounting `action_approve_finance` writes `sale.order.payment_mode_id`. LibreOffice converts the filled Word to PDF on close. Group checks run in the methods before any `sudo()` write.

**Tech Stack:** Odoo 16, OpenEduCat `op.student` / `op.student.course`, `account_payment_sale.payment_mode_id`, `python-docx`, LibreOffice, tests via `docker-compose.local.yml`.

---

## File map

Create under `addons-extra/extrairg/irg_enrollment_modification/`:

| File | Responsibility |
| --- | --- |
| `__manifest__.py` | depends `openeducat_core`, `mail`, `sale`, `account_payment_sale`; `python: ['docx']` |
| `security/enrollment_change_security.xml` | category + `group_academic` |
| `security/ir.model.access.csv` | wizard + request ACLs |
| `models/enrollment_change.py` | request, approvals, document orchestration |
| `models/op_student.py` | `action_open_enrollment_change_wizard` |
| `wizard/enrollment_change_wizard.py` | origin + five expandable changes; `action_create_request` |
| `reports/enrollment_change_document.py` | fill Word labels; LibreOffice PDF |
| `static/src/templates/modificacion_matricula.docx` | copy of the official template |
| `views/op_student_views.xml` | header button |
| `views/enrollment_change_views.xml` | form/tree/action |
| `wizard/enrollment_change_wizard_views.xml` | wizard form |
| `data/ir_sequence_data.xml` | `irg.enrollment.change` |
| `tests/test_enrollment_change.py` | TransactionCase + HTTP denials |

Do not modify existing addons.

## Security constraints (must hold in every task)

- `action_create_request`, `action_approve_academic`, `action_refuse` require `irg_enrollment_modification.group_academic` or Settings.
- `action_approve_finance` requires `account.group_account_invoice` or Settings.
- Writes to `op.student.course` / `sale.order` use `sudo()` only after `has_group()`.
- Chatter `message_post` without `sudo()`.
- Public methods that mutate data must re-check groups (UI `groups=` is not enough).

## Canonical test command

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_enrollment_modification --test-enable \
  --test-tags=/irg_enrollment_modification \
  --stop-after-init --http-port=8099 --log-level=test
```

First RED may use a disposable DB (`-i` on a throwaway name). Syntax gate: `python3 -m py_compile` on all new `.py` and `ET.parse` on XML.

---

### Task 1: Scaffold, group, sequence, failing create test

**Files:**
- Create: all `__init__.py`, `__manifest__.py`, security XML/CSV, empty models/wizard stubs, `tests/test_enrollment_change.py`
- Copy: template docx into `static/src/templates/modificacion_matricula.docx`

- [ ] **Step 1: Write failing tests** for create-does-not-write-enrollment

```python
@tagged("post_install", "-at_install", "irg_enrollment_modification")
class TestEnrollmentChange(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.academic = new_test_user(
            cls.env, login="enroll.acad@example.test",
            groups="irg_enrollment_modification.group_academic",
            name="Academic Enroll",
        )
        cls.accountant = new_test_user(
            cls.env, login="enroll.acct@example.test",
            groups="account.group_account_invoice",
            name="Accounting Enroll",
        )
        # partner, student (gender required), course, batch, academic year,
        # op.student.course, sale.order + payment_mode_id, optional SOL modalidad
```

Assert `action_create_request`:
- creates `irg.enrollment.change` in `submitted`
- posts a `.docx` on `op.student` chatter (`message_ids` attachment)
- does not change `student_course.course_id` / `batch_id` / `academic_years_id`
- does not change `sale_order.payment_mode_id`

Also: zero marks → `ValidationError`; marked course without destination → `ValidationError`.

- [ ] **Step 2: Run tests (RED)** — expected: model/wizard missing or methods missing.
- [ ] **Step 3: Minimal scaffold** so Odoo loads the module; wizard `action_create_request` still incomplete until Task 2.
- [ ] **Step 4: Syntax compile** of new Python/XML.

---

### Task 2: Wizard create request (no course/order write)

**Files:**
- Create/Modify: `wizard/enrollment_change_wizard.py`, views, `models/enrollment_change.py`

Wizard fields (exact names):

- `student_id`, `student_course_id` (required, domain student)
- `change_course`, `change_batch`, `change_modality`, `change_year`, `change_payment` (booleans)
- origin/dest: `origin_course_id`, `dest_course_id`, `origin_batch_id`, `dest_batch_id`, `origin_modality`, `dest_modality`, `origin_year_id`, `dest_year_id`, `origin_payment_mode_id`, `dest_payment_mode_id`
- `sale_order_id` required if `change_payment`

`default_get` sets student from `active_id`. Onchange `student_course_id` fills origins from the enrollment (year, course, batch) and from the linked sale order (payment, modality via `x_studio_modalidad` if present).

`action_create_request`:
1. `_check_academic_user()`
2. `_validate_wizard()`
3. create request with snapshots
4. `_generate_request_docx()` → attachment on student + `request_attachment_id`
5. `student.message_post` with attachment_ids
6. return act_window on the request

Batch dest domain: `course_id` = dest course if `change_course` else origin course.

- [ ] **Step 1:** Keep Task 1 tests; they must go GREEN for create path.
- [ ] **Step 2:** Implement wizard + request create only.
- [ ] **Step 3:** Run tagged tests. Expected: create tests PASS; approve tests still fail or absent.

---

### Task 3: Word fill

**Files:** `reports/enrollment_change_document.py`

Fill by locating labels in paragraphs and table cells (`python-docx`). After label, write the value. Unmarked change sections stay without origin/destino values.

Labels (Spanish, as in the template):

- `FECHA DE SOLICITUD:` today
- `DELEGACIÓN:` `sale_order.team_id.name` or empty
- `NOMBRE Y APELLIDOS:` student name
- `Grupo de origen:` / `Grupo de destino:` under curso/grupo if course or batch marked (format `"%s / %s" % (course.name, batch.name)`)
- modalidad / año / pago sections only if marked
- `Nombre:` under propuesta: `request.create_uid.name`
- Do not fill `FIRMA DEL ALUMNO`, Área Financiera, APROBADA/DENEGADA on the request Word

- [ ] **Step 1: Test** that the generated docx bytes contain student name and destination batch name, and do not contain Área Financiera as a checked mark.
- [ ] **Step 2: RED** then implement `_fill_docx(request, stage)` with `stage in ('request', 'final')`.
- [ ] **Step 3: GREEN**

---

### Task 4: Academic approve

**Files:** `models/enrollment_change.py`

`action_approve_academic`:
1. `_check_academic_user()`
2. state must be `submitted`
3. write marked fields on `student_course_id.sudo()`: course, batch, year
4. if `change_modality` and SOL has `x_studio_modalidad`, write dest on those lines (`sudo()` after check)
5. if not `change_payment`: `_close_with_pdf(final=True)` → state `done`
6. else: state `academic_approved`
7. chatter on student and request as acting user

- [ ] **Step 1: Test** academic user changes batch/year; payment mode unchanged; no PDF if payment marked; PDF + `done` if payment not marked.
- [ ] **Step 2: Test** accountant calling `action_approve_academic` → `AccessError`, course unchanged.
- [ ] **Step 3: RED/GREEN**

---

### Task 5: Finance approve, refuse, PDF retry

`action_approve_finance`:
1. `_check_finance_user()` (`account.group_account_invoice` or Settings)
2. state `academic_approved` and `change_payment`
3. `sale_order_id.sudo().payment_mode_id = dest`
4. `_close_with_pdf` with Área Financiera marked; state `done`

`action_refuse`:
- `submitted` + academic → `refused`, no writes
- `academic_approved` + finance → `refused`, academic writes stay, payment unchanged, no PDF

`action_retry_pdf` if LibreOffice failed after approve: group of the closing step, regenerate PDF.

LibreOffice: copy `_convert_to_pdf` pattern from `irg_gradebook_certificates` (`libreoffice --headless --convert-to pdf`). If missing, `UserError` and leave state as after the data write (`done` or keep a `pdf_error` boolean `pdf_pending`).

Spec: data write stays; button to regenerate. Use `pdf_pending` boolean default False, True when conversion fails.

- [ ] **Step 1: Tests** for finance write, academic cannot finance-approve, refuse from submitted, refuse from academic_approved.
- [ ] **Step 2: RED/GREEN**

---

### Task 6: Views and student button

- Header button on `openeducat_core.view_op_student_form`, `class="oe_highlight"`, `groups="irg_enrollment_modification.group_academic"`, `type="object"` `action_open_enrollment_change_wizard`.
- Wizard form: student_course always; attrs invisible on dest fields unless the boolean is true; payment boolean shows sale_order_id.
- Request form: statusbar, approve/refuse/finance buttons with groups; attachment fields.

- [ ] **Step 1: Test** xpath: inherited form arch contains `action_open_enrollment_change_wizard` (lxml like campus-block).
- [ ] **Step 2: XML + GREEN**

---

### Task 7: Docker install + tagged tests + E2E flag

- [ ] Run compose install/tests; save stdout to `missions/irg-enrollment-modification/artifacts/`.
- [ ] `e2e_testsprite` is in scope (views XML). Run e2e-tester after other checks pass, or record skip only if TestSprite MCP is unavailable — then `verification.json` skip must justify.
- [ ] Fill `execution.md` with commands.

---

## Spec coverage

| Spec item | Task |
| --- | --- |
| New module, no edits to others | 1 |
| Wizard five expandable changes + always pick enrollment | 2 |
| Word on create, no data write | 2–3 |
| Academic write; PDF if no payment | 4 |
| Finance write; PDF with Área Financiera | 5 |
| Refuse semantics | 5 |
| Button dark header | 6 |
| Groups + server-side checks | 1, 4, 5 |
| E2E | 7 |

## Publication

Commits on `feat/irg-enrollment-modification`. Do not push `Dev_iRG` until the user authorizes that push again after the code lands.
