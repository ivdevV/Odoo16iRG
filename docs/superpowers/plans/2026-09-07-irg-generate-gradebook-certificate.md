# IRG Generate Gradebook Certificate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `irg_generate_gradebook_certificate` so an AI agent can preview, approve, receive the private PDF as `file_b64`, verify the checksum, and pass the file on its own channel.

**Architecture:** Register a `kind=write` command on `irg.api.operation`. Preview validates payload and gradebook state. Approve creates `irg.certificate.wizard` and calls `action_generate()`. The verified snapshot includes identifiers, SHA-256 checksum and `file_b64`. The Odoo attachment stays `public=False`; no mail templates and no portal invoice.

**Tech Stack:** Odoo 16, `irg_business_api`, `irg_gradebook_certificates` wizard (soft), `TransactionCase`, `docker-compose.local.yml`.

---

## Global constraints

- Modify only `irg_business_api` production code, its tests and its docs. Do not edit `irg_gradebook_certificates`.
- Follow `irg_business_api_command_facade.md`: no RPC context flags; internal writes use `super().write()` already in `_irg_internal_write`.
- `sudo()` only via the existing academic_env path after group + allowlist.
- Do not commit, push or open a PR unless the user explicitly authorizes that action in the conversation. Suggested commit messages below are optional checkpoints, not permission.
- Use `docker-compose.local.yml` for Odoo tests. Disposable DB name: `test_irg_api_gradebook_cert`.
- TDD: no production code before a failing test for that behavior.
- E2E TestSprite is skipped (no views/QWeb/static/portal/HTTP controllers in the diff).

## Knowledge and references

- Design: `docs/superpowers/specs/2026-09-07-irg-generate-gradebook-certificate-design.md`
- Mission spec: `missions/irg-business-api-gradebook-certificate/00-spec.md`
- Facade gotchas: `.agents/knowledge/odoo_development_modding/artifacts/irg_business_api_command_facade.md`
- Wizard: `addons-extra/extrairg/irg_gradebook_certificates/wizard/certificate_wizard.py`
- Dispatch: `addons-extra/extrairg/irg_business_api/models/api_operation.py`
- Test helpers: `addons-extra/extrairg/irg_business_api/tests/common.py`

## File map

- Modify: `addons-extra/extrairg/irg_business_api/models/api_constants.py`
- Modify: `addons-extra/extrairg/irg_business_api/models/api_operation.py`
- Modify: `addons-extra/extrairg/irg_business_api/models/gradebook_service.py`
- Modify: `addons-extra/extrairg/irg_business_api/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py`
- Modify: `addons-extra/extrairg/irg_business_api/__manifest__.py` (version `16.0.1.2.0`)
- Modify: `addons-extra/extrairg/irg_business_api/doc/api-contract.md`
- Modify: `addons-extra/extrairg/irg_business_api/README.md`
- Modify: `doc/modules/extrairg/irg_business_api.md`
- Create: `missions/irg-business-api-gradebook-certificate/execution.md` (during implementation)
- Create: `missions/irg-business-api-gradebook-certificate/CHANGELOG.md` (documentation phase)

---

### Task 1: Mission journal and failing validation tests

**Files:**
- Create: `missions/irg-business-api-gradebook-certificate/execution.md`
- Create: `addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py`
- Modify: `addons-extra/extrairg/irg_business_api/tests/__init__.py`

- [ ] **Step 1: Start the execution journal**

Create `missions/irg-business-api-gradebook-certificate/execution.md` with base commit from:

```bash
git rev-parse HEAD
git status --short --branch
```

Record pre-existing dirty files and that this mission must not touch them.

- [ ] **Step 2: Write failing tests for payload and gradebook rules**

Append to `addons-extra/extrairg/irg_business_api/tests/__init__.py`:

```python
from . import test_gradebook_certificate
```

Create `addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py` with this exact content:

```python
# -*- coding: utf-8 -*-
import base64
import hashlib
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import IrgBusinessApiCase

PDF_BYTES = (
    b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
    b'1 0 obj<</Type/Catalog>>endobj\n'
    b'trailer<>\n%%EOF\n'
)
PDF_CHECKSUM = hashlib.sha256(PDF_BYTES).hexdigest()


@tagged('post_install', '-at_install', 'irg_business_api')
class TestGradebookCertificateOperation(IrgBusinessApiCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if 'app.gradebook.student' not in cls.env or 'irg.certificate.wizard' not in cls.env:
            cls._certs_available = False
            return
        cls._certs_available = True
        tmpl_vals = {'name': 'API Cert Template'}
        GradebookTmpl = cls.env['app.gradebook']
        if 'gradebook_template_ids' in GradebookTmpl._fields:
            tmpl_vals['gradebook_template_ids'] = [(0, 0, {
                'type': 'exam',
                'qty': 1,
                'weight': 100,
            })]
        cls.gradebook_tmpl = GradebookTmpl.create(tmpl_vals)
        if 'gradebook_id' in cls.course._fields:
            cls.course.write({'gradebook_id': cls.gradebook_tmpl.id})
        cls.gradebook = cls.env['app.gradebook.student'].create({
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'admission_id': cls.admission.id,
        })
        if 'op.subject' in cls.env:
            subject = cls.subject
            cls.gb_subject = cls.env['app.gradebook.subject'].create({
                'gradebook_student_id': cls.gradebook.id,
                'op_subject_id': subject.id,
            })
            if 'app.gradebook.result' in cls.env:
                cls.env['app.gradebook.result'].create({
                    'gradebook_subject_id': cls.gb_subject.id,
                    'survey_type': 'exam',
                    'scoring_total': 8.0,
                })
                if hasattr(cls.gb_subject, 'compute_final_subject_note'):
                    cls.gb_subject.compute_final_subject_note()

    def setUp(self):
        super().setUp()
        if not getattr(self, '_certs_available', False):
            self.skipTest('Gradebook certificates are not installed.')

    def _payload(self, **overrides):
        data = {
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'signer': 'dpto_academico',
        }
        data.update(overrides)
        return data

    def _patch_pdf(self):
        return patch.object(
            type(self.env['irg.certificate.request']),
            '_convert_to_pdf',
            return_value=PDF_BYTES,
        )

    def test_unknown_payload_key_rejected(self):
        with self.assertRaises(UserError):
            self.run_op('irg_generate_gradebook_certificate', self._payload(sudo=True))

    def test_missing_signer_rejected(self):
        payload = self._payload()
        payload.pop('signer')
        with self.assertRaises(UserError):
            self.run_op('irg_generate_gradebook_certificate', payload, key='cert-no-signer')

    def test_invalid_signer_rejected(self):
        with self.assertRaises(UserError):
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(signer='someone_else'),
                key='cert-bad-signer',
            )

    def test_final_certificate_requires_done_gradebook(self):
        if self.gradebook.state == 'done':
            self.skipTest('Gradebook fixture already done.')
        with self.assertRaises(UserError):
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(document_type='gradebook'),
                key='cert-final-open',
            )

    def test_partial_allows_open_gradebook(self):
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(),
            key='cert-partial-open',
        )
        self.assertEqual(op.state, 'preview')
        proposed = self.proposed_json(op)
        self.assertEqual(proposed['document_type'], 'gradebook_partial')
        self.assertEqual(proposed['signer'], 'dpto_academico')
        self.assertNotIn('file_b64', proposed)

    def test_physical_requires_shipping(self):
        with self.assertRaises(UserError):
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(certificate_type='physical'),
                key='cert-phys-no-ship',
            )

    def test_approve_returns_private_pdf_and_checksum(self):
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(),
            key='cert-ok-1',
        )
        with self._patch_pdf():
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='cert-ok-1-ok')
        op.invalidate_recordset()
        data = self.result_json(op)
        self.assertEqual(op.state, 'verified')
        self.assertTrue(data['certificate_request_id'])
        self.assertTrue(data['attachment_id'])
        self.assertEqual(data['state'], 'done')
        self.assertTrue(data['name'])
        self.assertEqual(data['checksum'], PDF_CHECKSUM)
        raw = base64.b64decode(data['file_b64'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), data['checksum'])
        self.assertFalse(data['public'])
        attachment = self.env['ir.attachment'].browse(data['attachment_id'])
        self.assertFalse(attachment.public)
        cert = self.env['irg.certificate.request'].browse(data['certificate_request_id'])
        self.assertEqual(cert.origin, 'backend')
        self.assertFalse(cert.invoice_id)

    def test_same_idempotency_key_does_not_duplicate(self):
        payload = self._payload()
        first = self.run_op('irg_generate_gradebook_certificate', payload, key='cert-idem')
        with self._patch_pdf():
            self.run_op('irg_approve_operation', {'operation_id': first.id}, key='cert-idem-ok')
        first.invalidate_recordset()
        cert_id = self.result_json(first)['certificate_request_id']
        second = self.run_op('irg_generate_gradebook_certificate', payload, key='cert-idem')
        self.assertEqual(second.id, first.id)
        copies = self.env['irg.certificate.request'].search([
            ('gradebook_student_id', '=', self.gradebook.id),
            ('origin', '=', 'backend'),
        ])
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies.id, cert_id)

    def test_approve_does_not_queue_certificate_mail(self):
        Mail = self.env['mail.mail']
        before = Mail.search_count([])
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(),
            key='cert-no-mail',
        )
        with self._patch_pdf():
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='cert-no-mail-ok')
        self.assertEqual(Mail.search_count([]), before)
```

- [ ] **Step 3: Run tests and confirm RED**

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d test_irg_api_gradebook_cert \
  -i irg_gradebook_certificates,irg_certificate_partial,irg_business_api \
  --test-enable --test-tags /irg_business_api \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test
```

Expected: FAIL because `irg_generate_gradebook_certificate` is unknown (`Unknown or unpublished operation.`). Capture the tail in `missions/irg-business-api-gradebook-certificate/artifacts/red-tests.txt`.

If the DB already exists from a previous run, use `-u irg_business_api` instead of `-i` after the first create.

---

### Task 2: Register the command and implement preview/apply

**Files:**
- Modify: `addons-extra/extrairg/irg_business_api/models/api_constants.py`
- Modify: `addons-extra/extrairg/irg_business_api/models/gradebook_service.py`
- Modify: `addons-extra/extrairg/irg_business_api/models/api_operation.py`
- Modify: `addons-extra/extrairg/irg_business_api/__manifest__.py`

- [ ] **Step 1: Register the operation**

In `api_constants.py`, append this tuple to `OPERATION_CODES` (before the closing `]`):

```python
    ('irg_generate_gradebook_certificate', 'Generate gradebook certificate PDF'),
```

Add this spec to `OPERATION_SPECS`:

```python
    'irg_generate_gradebook_certificate': {
        'kind': 'write',
        'keys': {
            'gradebook_student_id',
            'document_type',
            'certificate_type',
            'signer',
            'shipping_type',
            'custom_description',
            'custom_options',
        },
    },
```

Bump `__manifest__.py` `'version'` to `'16.0.1.2.0'`.

- [ ] **Step 2: Implement GradebookService helpers**

Replace `addons-extra/extrairg/irg_business_api/models/gradebook_service.py` so existing read methods stay and the new command is added. Full file:

```python
# -*- coding: utf-8 -*-
import base64
import hashlib
import re

from odoo.exceptions import UserError
from odoo.tools.translate import _

from . import api_serializer as ser

DOCUMENT_TYPES = {'gradebook', 'gradebook_partial'}
CERTIFICATE_TYPES = {'digital', 'physical', 'custom', 'physical_apostilled'}
PHYSICAL_TYPES = {'physical', 'physical_apostilled'}
SIGNERS = {'dpto_academico', 'raimon'}
SHIPPING_TYPES = {'national', 'international'}
CUSTOM_OPTIONS = {'language_en', 'language_fr', 'specific_subjects', 'official_seal'}
CONTENT_ID_RE = re.compile(r'/web/content/(\d+)')


class GradebookService:

    def __init__(self, env):
        self.env = env

    def get_gradebook_summary(self, payload):
        if 'app.gradebook.student' not in self.env:
            return {'available': False, 'results': []}
        domain = []
        if payload.get('admission_id'):
            domain.append(('admission_id', '=', ser.require_positive_id(payload, 'admission_id')))
        elif payload.get('partner_id'):
            domain.append(('partner_id', '=', ser.require_positive_id(payload, 'partner_id')))
        else:
            raise UserError(_('admission_id or partner_id is required.'))
        books = self.env['app.gradebook.student'].search(domain)
        results = []
        for book in books:
            subjects = []
            for subject in book.gradebook_subject_ids:
                source_results = []
                if 'gradebook_result_ids' in subject._fields:
                    for result in subject.gradebook_result_ids:
                        source_results.append({
                            'id': result.id,
                            'survey_type': result.survey_type,
                            'scoring_total': result.scoring_total,
                            'survey_user_input_id': (
                                result.survey_user_input_id.id
                                if result.survey_user_input_id else False
                            ),
                        })
                subjects.append({
                    'id': subject.id,
                    'subject_id': subject.op_subject_id.id if subject.op_subject_id else False,
                    'final_subject_note': (
                        subject.final_subject_note
                        if 'final_subject_note' in subject._fields else False
                    ),
                    'results': source_results,
                })
            results.append({
                'id': book.id,
                'state': book.state,
                'admission_id': book.admission_id.id if book.admission_id else False,
                'subjects': subjects,
            })
        return {'available': True, 'results': results}

    def get_student_grade_evidence(self, payload):
        summary = self.get_gradebook_summary(payload)
        if not summary.get('available'):
            return summary
        subject_id = payload.get('subject_id')
        if subject_id:
            wanted = ser.require_positive_id(payload, 'subject_id')
            for book in summary.get('results') or []:
                book['subjects'] = [
                    subject for subject in book.get('subjects') or []
                    if subject.get('subject_id') == wanted
                ]
        return summary

    def _require_certificates(self):
        if 'irg.certificate.wizard' not in self.env or 'irg.certificate.request' not in self.env:
            raise UserError(_('Gradebook certificates are not installed.'))
        if 'app.gradebook.student' not in self.env:
            raise UserError(_('Gradebook is not installed.'))

    def _gradebook(self, payload):
        self._require_certificates()
        gradebook = self.env['app.gradebook.student'].browse(
            ser.require_positive_id(payload, 'gradebook_student_id')
        )
        if not gradebook.exists():
            raise UserError(_('Unknown gradebook_student_id.'))
        return gradebook

    def _validated_certificate_vals(self, payload):
        gradebook = self._gradebook(payload)
        document_type = (payload.get('document_type') or '').strip()
        if document_type not in DOCUMENT_TYPES:
            raise UserError(_('document_type must be gradebook or gradebook_partial.'))
        certificate_type = (payload.get('certificate_type') or '').strip()
        if certificate_type not in CERTIFICATE_TYPES:
            raise UserError(_('certificate_type is not valid.'))
        signer = (payload.get('signer') or '').strip()
        if signer not in SIGNERS:
            raise UserError(_('signer is required and must be dpto_academico or raimon.'))
        shipping_type = (payload.get('shipping_type') or '').strip() or False
        if certificate_type in PHYSICAL_TYPES:
            if shipping_type not in SHIPPING_TYPES:
                raise UserError(_('shipping_type is required for physical certificates.'))
        elif shipping_type:
            raise UserError(_('shipping_type is only allowed for physical certificates.'))
        custom_options = payload.get('custom_options') or False
        if custom_options and custom_options not in CUSTOM_OPTIONS:
            raise UserError(_('custom_options is not valid.'))
        if document_type == 'gradebook' and gradebook.state != 'done':
            raise UserError(_(
                "Para solicitar un Certificado de Notas Completo, la libreta académica "
                "debe estar finalizada (estado 'Finalizado')."
            ))
        vals = {
            'gradebook_student_id': gradebook.id,
            'document_type': document_type,
            'certificate_type': certificate_type,
            'signer': signer,
            'shipping_type': shipping_type,
        }
        custom_description = payload.get('custom_description') or False
        if custom_description:
            vals['custom_description'] = custom_description
        if custom_options:
            vals['custom_options'] = custom_options
        return gradebook, vals

    def _certificate_from_download_action(self, action):
        url = (action or {}).get('url') or ''
        match = CONTENT_ID_RE.search(url)
        if not match:
            raise UserError(_('Certificate PDF was not generated.'))
        attachment = self.env['ir.attachment'].with_context(bin_size=False).browse(int(match.group(1)))
        if not attachment.exists():
            raise UserError(_('Certificate PDF was not generated.'))
        if attachment.res_model != 'irg.certificate.request':
            raise UserError(_('Certificate PDF was not generated.'))
        cert = self.env['irg.certificate.request'].browse(attachment.res_id)
        if not cert.exists():
            raise UserError(_('Certificate PDF was not generated.'))
        return cert, attachment

    def preview_generate_gradebook_certificate(self, payload):
        gradebook, vals = self._validated_certificate_vals(payload)
        self.env['irg.certificate.wizard'].create(vals)
        count = self.env['irg.certificate.request'].search_count([
            ('gradebook_student_id', '=', gradebook.id),
        ])
        before = {
            'gradebook_student_id': gradebook.id,
            'gradebook_state': gradebook.state,
            'certificate_count': count,
        }
        proposed = dict(vals)
        proposed['gradebook_state'] = gradebook.state
        proposed['will_call'] = 'irg.certificate.wizard.action_generate'
        return before, proposed, {'model': 'app.gradebook.student', 'id': gradebook.id}

    def apply_generate_gradebook_certificate(self, proposed, before):
        payload = {
            'gradebook_student_id': proposed.get('gradebook_student_id'),
            'document_type': proposed.get('document_type'),
            'certificate_type': proposed.get('certificate_type'),
            'signer': proposed.get('signer'),
            'shipping_type': proposed.get('shipping_type') or False,
        }
        if proposed.get('custom_description'):
            payload['custom_description'] = proposed['custom_description']
        if proposed.get('custom_options'):
            payload['custom_options'] = proposed['custom_options']
        gradebook, vals = self._validated_certificate_vals(payload)
        if gradebook.state != before.get('gradebook_state'):
            raise UserError(_('The gradebook changed after preview.'))
        wizard = self.env['irg.certificate.wizard'].create(vals)
        action = wizard.action_generate()
        cert, attachment = self._certificate_from_download_action(action)
        if 'public' in attachment._fields and attachment.public:
            raise UserError(_('Certificate PDF must remain private.'))
        raw = base64.b64decode(attachment.datas or b'')
        if not raw:
            raise UserError(_('Certificate PDF was not generated.'))
        checksum = hashlib.sha256(raw).hexdigest()
        file_b64 = attachment.datas
        if isinstance(file_b64, bytes):
            file_b64 = file_b64.decode('ascii')
        return {
            'certificate_request_id': cert.id,
            'name': cert.name,
            'state': cert.state,
            'attachment_id': attachment.id,
            'attachment_name': attachment.name,
            'mimetype': attachment.mimetype or 'application/pdf',
            'checksum': checksum,
            'file_b64': file_b64,
            'public': False,
        }
```

Keep the existing `get_gradebook_summary` / `get_student_grade_evidence` bodies identical to the current file; do not refactor them beyond copying.

- [ ] **Step 3: Wire dispatch**

In `api_operation.py` `_irg_write_preview_handlers`, add:

```python
            'irg_generate_gradebook_certificate': GradebookService(env).preview_generate_gradebook_certificate,
```

In `_irg_write_apply_handlers`, add:

```python
            'irg_generate_gradebook_certificate': GradebookService(env).apply_generate_gradebook_certificate,
```

`GradebookService` is already imported at the top of `api_operation.py`.

- [ ] **Step 4: Run tests and confirm GREEN**

Same docker command as Task 1 Step 3, typically `-u irg_business_api`.

Expected: the new class passes. Save tail to `missions/irg-business-api-gradebook-certificate/artifacts/green-tests.txt`.

If `_fill_template` fails before `_convert_to_pdf`, patch `_generate_and_attach_pdf` instead so it still creates a private `ir.attachment` with `PDF_BYTES`, `res_model='irg.certificate.request'`, `public=False`, and assign `attachment_id`. Record that fallback and why in `execution.md`. Do not skip calling `action_generate()`.

---

### Task 3: Contract docs

**Files:**
- Modify: `addons-extra/extrairg/irg_business_api/doc/api-contract.md`
- Modify: `addons-extra/extrairg/irg_business_api/README.md`
- Modify: `doc/modules/extrairg/irg_business_api.md`

- [ ] **Step 1: Document the command**

In `doc/api-contract.md`, add a row under Fases 3–6:

```markdown
| `irg_generate_gradebook_certificate` | `gradebook_student_id`, `document_type`, `certificate_type`, `signer`, `shipping_type?` | Write: preview → approve. Wizard oficial. Resultado: ids, `checksum`, `file_b64`. Adjunto `public=False`. Sin mail. |
```

In README.md, in Limitaciones or Uso, add one sentence: the generate command returns `file_b64` after approve so an agent can pass the PDF; Odoo does not email or publish it.

In `doc/modules/extrairg/irg_business_api.md`, mention the new command and version `16.0.1.2.0`.

- [ ] **Step 2: Syntax check**

```bash
python3 -m py_compile \
  addons-extra/extrairg/irg_business_api/models/api_constants.py \
  addons-extra/extrairg/irg_business_api/models/api_operation.py \
  addons-extra/extrairg/irg_business_api/models/gradebook_service.py \
  addons-extra/extrairg/irg_business_api/tests/test_gradebook_certificate.py
```

Expected: no output, exit 0.

Do not commit unless the user asks.

---

### Task 4: Independent review, validation, documentation

This task is not for the coder.

- [ ] **Step 1: Code review** by a different agent. Review only production code, tests, security and runtime config. Do not review plan/execution/docs unless they contain executable code. Write `missions/irg-business-api-gradebook-certificate/02b-review.md`. Blocking findings reopen implementation.

- [ ] **Step 2: Validation** by a different agent. Re-run py_compile and the docker test command. Do not trust coder artifacts. Write `missions/irg-business-api-gradebook-certificate/03-validation.md` and `verification.json`.

`e2e_testsprite` must be `skipped` with detail: diff does not touch views, QWeb, static, portal, website or HTTP controllers.

- [ ] **Step 3: Documentation** only after review and validation passed. Write `missions/irg-business-api-gradebook-certificate/CHANGELOG.md`. Persist a short knowledge note in `.agents/knowledge/odoo_development_modding/artifacts/` only if there is a reusable gotcha (recommended: `file_b64` in snapshots is allowed for this command; `datas` remains stripped; `bin_size=False` when reading attachment bytes).

---

## Spec coverage

| Requirement | Task |
| --- | --- |
| Explicit payload + operation idempotency_key | Task 1–2 |
| Partial allows open gradebook | Task 1 `test_partial_allows_open_gradebook` |
| Final requires done | Task 1 `test_final_certificate_requires_done_gradebook` |
| Signer required and valid | Task 1 missing/invalid signer tests |
| No duplicate same key | Task 1 `test_same_idempotency_key_does_not_duplicate` |
| Official wizard PDF | Task 2 `action_generate` |
| Return ids, state, name, checksum, file_b64 | Task 1 `test_approve_returns_private_pdf_and_checksum` |
| Private, no auto send/publish | Task 1 public + mail tests |
| Agent can pass the PDF | `file_b64` in verified snapshot |

## Anti-patterns

- Do not add `irg_generate_gradebook_certificate` as `kind=read`.
- Do not put `file_b64` in preview/`proposed_after`.
- Do not name the binary key `datas` (serializer strips it).
- Do not call `_send_digital_notification` or set `public=True`.
- Do not use `self.env.context.get('irg_api_internal')`.
- Do not use `self.env.sudo()`; the facade already uses `self.sudo().env`.
- Do not search “latest certificate” to resolve the PDF; parse `/web/content/<id>`.
- Do not add a hard `depends` on `irg_gradebook_certificates`.
- Do not fix Google Chat credentials in this mission.
