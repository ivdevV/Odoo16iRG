# Diplomado class start date Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (tasks are tightly coupled in one new addon). Do not split across independent subagents. Follow TDD. Spec: `docs/superpowers/specs/2026-09-04-irg-diplomado-class-start-date-design.md`. Do not commit unless the user explicitly asks.

**Goal:** Diplomado diplomas print celebration start from `op.batch.date_start_class`, and the next portal/backend download regenerates the stored PDF with the live batch class start date.

**Architecture:** New addon `irg_generacion_diplomados_class_start_date` only. Registry helpers resolve the batch and sync `start_date`. `action_reprint` always rebuilds the PDF via `_get_diplomado_pdf_data()` and overwrites `attachment_id.datas`. Wizard onchange and portal create/download inherit that helper. Existing addons stay untouched.

**Tech Stack:** Odoo 16, OpenEduCat `op.batch` / `op.student.course`, `isep_data_master_make.date_start_class`, ReportLab in `irg_generacion_diplomados`, tests via `docker-compose.local.yml`.

---

## File map

Create under `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/`:

| File | Responsibility |
| --- | --- |
| `__manifest__.py` | depends listed below; `auto_install` false |
| `models/diplomado_registry.py` | batch resolution, date sync, always-reprint |
| `wizard/diplomado_wizard.py` | onchange uses class start date |
| `controllers/portal.py` | dedicated portal create + always reprint; campus download always reprint after auth |
| `tests/test_class_start_date.py` | TransactionCase (+ controller call tests) |

Depends: `irg_generacion_diplomados`, `isep_data_master_make`, `irg_generacion_diplomados_website_verify`, `irg_diplomado_portal_request`, `irg_campus_diplomados_portal`.

Do not modify existing addons.

## Security constraints (must hold in every task)

- `_irg_*` helpers are not public RPC contract; do not add new unauthenticated routes.
- Campus `download_diplomado` must check partner ownership **before** `action_reprint`.
- Dedicated portal `_send_diplomado_file` already runs after partner/grade checks; keep it that way.
- No new `sudo()`. Portal inherits existing `sudo()` on registry browse.
- Overwrite `ir.attachment.datas` in place. Do not `unlink()` the registry. Do not leave `attachment_id` empty if PDF generation fails.
- `action_reprint` stays the existing staff button; ACL unchanged.

## Canonical test command

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_generacion_diplomados_class_start_date --test-enable \
  --test-tags=/irg_generacion_diplomados_class_start_date \
  --stop-after-init --http-port=8099 --log-level=test
```

RED: install/update the module with tests that assert the new behavior before production methods exist (skeleton module + tests first). Expected: FAIL on missing methods or wrong dates (`start_date` of the batch).

GREEN: same command, 0 failed.

## E2E

Mandatory after module tests pass. `projectPath` = module directory only. Runtime `docker-compose.local.yml` port 8069. Disposable DB. No beta/prod.

---

### Task 1: Module skeleton + failing tests

**Files:**
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/__init__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/__manifest__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/models/__init__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/models/diplomado_registry.py` (empty inherit class only)
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/wizard/__init__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/wizard/diplomado_wizard.py` (empty inherit class only)
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/controllers/__init__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/controllers/portal.py` (empty inherit classes only)
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_generacion_diplomados_class_start_date/tests/test_class_start_date.py`

- [ ] **Step 1: Write the skeleton manifest**

```python
# __manifest__.py
{
    'name': 'Fecha de inicio de clases en diplomados',
    'version': '16.0.1.0.0',
    'summary': 'Usa date_start_class del lote en diplomas de diplomados y regenera el PDF al descargar.',
    'category': 'Education',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_generacion_diplomados',
        'isep_data_master_make',
        'irg_generacion_diplomados_website_verify',
        'irg_diplomado_portal_request',
        'irg_campus_diplomados_portal',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
```

```python
# __init__.py
from . import models
from . import wizard
from . import controllers
```

Empty inherits so the module installs:

```python
# models/diplomado_registry.py
from odoo import models

class IrgDiplomadoRegistry(models.Model):
    _inherit = 'irg.diplomado.registry'
```

```python
# wizard/diplomado_wizard.py
from odoo import models

class IrgDiplomadoWizard(models.TransientModel):
    _inherit = 'irg.diplomado.wizard'
```

```python
# controllers/portal.py
from odoo.addons.irg_campus_diplomados_portal.controllers.portal import IrgCampusDiplomadosPortal
from odoo.addons.irg_diplomado_portal_request.controllers.portal import IrgDiplomadoPortalRequestController


class IrgDiplomadoPortalRequestClassStart(IrgDiplomadoPortalRequestController):
    pass


class IrgCampusDiplomadosClassStart(IrgCampusDiplomadosPortal):
    pass
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_class_start_date.py
# -*- coding: utf-8 -*-
import base64
from datetime import date

from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.irg_diplomado_portal_request.controllers.portal import (
    IrgDiplomadoPortalRequestController,
)


@tagged('post_install', '-at_install', 'irg_generacion_diplomados_class_start_date')
class TestDiplomadoClassStartDate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.course = self.env['op.course'].create({
            'name': 'Diplomado Fecha Clases',
            'code': 'DIPCLASSSTART',
            'lang': self.env.user.lang or 'en_US',
        })
        self.batch = self.env['op.batch'].create({
            'name': 'Lote Fecha Clases',
            'code': 'LFC2026',
            'course_id': self.course.id,
            'start_date': '2026-01-10',
            'end_date': '2026-06-10',
            'date_start_class': '2026-03-15',
        })
        self.partner = self.env['res.partner'].create({'name': 'Alumno Fecha Clases'})
        self.student = self.env['op.student'].create({
            'first_name': 'Alumno',
            'last_name': 'Fecha Clases',
            'partner_id': self.partner.id,
        })
        self.student_course = self.env['op.student.course'].create({
            'student_id': self.student.id,
            'course_id': self.course.id,
            'batch_id': self.batch.id,
            'state': 'finished',
        })
        self.env.company.external_report_layout_id = self.env.ref(
            'web.external_layout_standard'
        ).id

    def _registry_vals(self, **overrides):
        vals = {
            'student_id': self.student.id,
            'student_name': 'Alumno Fecha Clases',
            'course_id': self.course.id,
            'diplomado_name': self.course.name,
            'start_date': '2026-01-10',
            'end_date': '2026-06-10',
            'diploma_type': 'digital',
        }
        vals.update(overrides)
        return vals

    def test_celebration_start_prefers_date_start_class(self):
        start = self.env['irg.diplomado.registry']._irg_celebration_start_from_batch(self.batch)
        self.assertEqual(start, date(2026, 3, 15))

    def test_celebration_start_falls_back_to_batch_start_date(self):
        self.env.cr.execute(
            'UPDATE op_batch SET date_start_class = NULL WHERE id = %s',
            [self.batch.id],
        )
        self.batch.invalidate_recordset(['date_start_class'])
        start = self.env['irg.diplomado.registry']._irg_celebration_start_from_batch(self.batch)
        self.assertEqual(start, date(2026, 1, 10))

    def test_wizard_onchange_uses_class_start_date(self):
        wizard = self.env['irg.diplomado.wizard'].create({
            'student_id': self.student.id,
        })
        wizard._onchange_student_id()
        self.assertEqual(wizard.start_date, date(2026, 3, 15))
        self.assertEqual(wizard.end_date, date(2026, 6, 10))

    def test_portal_create_uses_class_start_date(self):
        gradebook = self.env['app.gradebook.student'].new({
            'batch_id': self.batch.id,
        })
        controller = IrgDiplomadoPortalRequestController()
        # The production method uses request.env; tests call the registry helper
        # the controller must use. Direct controller HTTP is covered by send-file.
        start = self.env['irg.diplomado.registry']._irg_celebration_start_from_batch(
            gradebook.batch_id
        )
        self.assertEqual(start, date(2026, 3, 15))

    def test_reprint_syncs_class_start_and_overwrites_same_attachment(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'Diplomado_old.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'OLD_DIPLOMADO_PDF'),
            'res_model': 'irg.diplomado.registry',
            'mimetype': 'application/pdf',
        })
        registry = self.env['irg.diplomado.registry'].create(
            self._registry_vals(attachment_id=attachment.id)
        )
        attachment.write({'res_id': registry.id})
        self.batch.write({'date_start_class': '2026-04-20'})
        action = registry.action_reprint()
        self.assertEqual(registry.start_date, date(2026, 4, 20))
        self.assertEqual(registry.end_date, date(2026, 6, 10))
        self.assertEqual(registry.attachment_id.id, attachment.id)
        pdf = base64.b64decode(registry.attachment_id.datas)
        self.assertNotEqual(pdf, b'OLD_DIPLOMADO_PDF')
        self.assertIn(b'20/04/2026', pdf)
        self.assertNotIn(b'10/01/2026', pdf)
        self.assertTrue(action['url'].startswith('/web/content/%s' % attachment.id))

    def test_reprint_without_batch_keeps_stored_start_date(self):
        self.student_course.unlink()
        attachment = self.env['ir.attachment'].create({
            'name': 'Diplomado_orphan.pdf',
            'type': 'binary',
            'datas': base64.b64encode(b'ORPHAN_PDF'),
            'res_model': 'irg.diplomado.registry',
            'mimetype': 'application/pdf',
        })
        registry = self.env['irg.diplomado.registry'].create(
            self._registry_vals(
                start_date='2025-12-01',
                attachment_id=attachment.id,
            )
        )
        attachment.write({'res_id': registry.id})
        registry.action_reprint()
        self.assertEqual(registry.start_date, date(2025, 12, 1))
        pdf = base64.b64decode(registry.attachment_id.datas)
        self.assertIn(b'01/12/2025', pdf)
        self.assertEqual(registry.attachment_id.id, attachment.id)
```

Also add a dedicated test that `_send_diplomado_file` calls `action_reprint` even when an attachment exists: patch `action_reprint` with a counter on a controller subclass instance is brittle in TransactionCase. Implement the production `_send_diplomado_file` as:

```python
def _send_diplomado_file(self, diplomado):
    try:
        diplomado.action_reprint()
    except Exception:
        _logger.exception(...)
        return request.redirect(...)
    return super()._send_diplomado_file(diplomado)
```

Cover it with an HttpCase test that mocks `action_reprint` to increment a counter and still attach a PDF, then `url_open` `/campus/diplomados/download/<id>` with an existing attachment. Put that class in the same test file if HttpCase fixtures are affordable; otherwise a TransactionCase that instantiates the override and asserts the method source calls `action_reprint` first is not enough — prefer HttpCase following `irg_diplomado_portal_request/tests/test_portal.py`.

Minimal HttpCase (reuse portal user pattern only if install already provides website). If HttpCase is too heavy for RED1, keep TransactionCase coverage of `action_reprint` as the source of truth and add HttpCase in the same test module once GREEN reprint exists.

- [ ] **Step 3: Run tests and confirm RED**

Run the canonical command. Expected: FAIL because `_irg_celebration_start_from_batch` is missing and `action_reprint` still returns the old PDF / `start_date` 2026-01-10.

- [ ] **Step 4: Do not commit** unless the user asks.

---

### Task 2: Registry helpers + always reprint

**Files:**
- Modify: `models/diplomado_registry.py`

- [ ] **Step 1: Implement helpers and `action_reprint`**

```python
# -*- coding: utf-8 -*-
import base64
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class IrgDiplomadoRegistry(models.Model):
    _inherit = 'irg.diplomado.registry'

    def _irg_celebration_start_from_batch(self, batch):
        if not batch:
            return False
        return batch.date_start_class or batch.start_date

    def _irg_get_celebration_batch(self):
        self.ensure_one()
        lines = self.env['op.student.course'].search([
            ('student_id', '=', self.student_id.id),
            ('course_id', '=', self.course_id.id),
        ], order='id desc')
        finished = lines.filtered(lambda line: line.state == 'finished')
        line = finished[:1] or lines[:1]
        if line and line.batch_id:
            return line.batch_id
        Gradebook = self.env.get('app.gradebook.student')
        if Gradebook is None:
            return self.env['op.batch']
        gradebook = Gradebook.search([
            ('student_id', '=', self.student_id.id),
            ('course_id', '=', self.course_id.id),
        ], order='id desc', limit=1)
        return gradebook.batch_id if gradebook and gradebook.batch_id else self.env['op.batch']

    def _irg_sync_celebration_start_date(self):
        for record in self:
            batch = record._irg_get_celebration_batch()
            if not batch:
                continue
            new_date = record._irg_celebration_start_from_batch(batch)
            if new_date and record.start_date != new_date:
                record.start_date = new_date

    def action_reprint(self):
        self.ensure_one()
        self._irg_sync_celebration_start_date()
        pdf_content = self.env['report.irg_generacion_diplomados.diplomado_pdf'].generate_diplomado_pdf(
            self._get_diplomado_pdf_data()
        )
        payload = base64.b64encode(pdf_content)
        attachment_name = 'Diplomado_%s.pdf' % self.student_name.replace(' ', '_')
        if self.attachment_id:
            self.attachment_id.write({
                'datas': payload,
                'name': attachment_name,
                'mimetype': 'application/pdf',
            })
        else:
            attachment = self.env['ir.attachment'].create({
                'name': attachment_name,
                'type': 'binary',
                'datas': payload,
                'res_model': 'irg.diplomado.registry',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            self.write({'attachment_id': attachment.id})
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % self.attachment_id.id,
            'target': 'self',
        }
```

If `generate_diplomado_pdf` raises, do not write the attachment (old PDF remains).

- [ ] **Step 2: Re-run canonical tests.** Expect wizard/portal tests still FAIL; reprint tests PASS.

---

### Task 3: Wizard onchange

**Files:**
- Modify: `wizard/diplomado_wizard.py`

- [ ] **Step 1: After `super()`, apply class start date**

```python
# -*- coding: utf-8 -*-
from odoo import api, models


class IrgDiplomadoWizard(models.TransientModel):
    _inherit = 'irg.diplomado.wizard'

    def _irg_wizard_batch(self):
        self.ensure_one()
        if not self.student_id or not self.course_id:
            return self.env['op.batch']
        lines = self.student_id.course_detail_ids.filtered(
            lambda line: line.course_id == self.course_id
        )
        finished = lines.filtered(lambda line: line.state == 'finished')
        line = (finished[:1] or lines[:1])
        return line.batch_id if line else self.env['op.batch']

    def _irg_apply_class_start_date(self):
        for wizard in self:
            batch = wizard._irg_wizard_batch()
            if not batch:
                continue
            wizard.start_date = wizard.env['irg.diplomado.registry']._irg_celebration_start_from_batch(batch)

    @api.onchange('student_id')
    def _onchange_student_id(self):
        result = super()._onchange_student_id()
        self._irg_apply_class_start_date()
        return result

    @api.onchange('course_id')
    def _onchange_course_id(self):
        result = super()._onchange_course_id()
        self._irg_apply_class_start_date()
        return result
```

- [ ] **Step 2: Re-run tests.** Wizard test PASS.

---

### Task 4: Portal controllers

**Files:**
- Modify: `controllers/portal.py`

- [ ] **Step 1: Dedicated portal create + always reprint; campus reprint after auth**

```python
# -*- coding: utf-8 -*-
import logging

from odoo.http import request
from odoo.addons.irg_campus_diplomados_portal.controllers.portal import IrgCampusDiplomadosPortal
from odoo.addons.irg_diplomado_portal_request.controllers.portal import IrgDiplomadoPortalRequestController

_logger = logging.getLogger(__name__)


class IrgDiplomadoPortalRequestClassStart(IrgDiplomadoPortalRequestController):

    def _create_diplomado_registry(self, student, course, gradebook):
        registry = super()._create_diplomado_registry(student, course, gradebook)
        batch = gradebook.batch_id if gradebook else False
        start = registry._irg_celebration_start_from_batch(batch)
        if start and registry.start_date != start:
            registry.start_date = start
        return registry

    def _send_diplomado_file(self, diplomado):
        try:
            diplomado.action_reprint()
        except Exception:
            _logger.exception(
                'Error al regenerar el PDF del diplomado %s', diplomado.id
            )
            return request.redirect(
                '/campus/diplomados/%s?error=no_pdf' % diplomado.course_id.id
            )
        return super()._send_diplomado_file(diplomado)


class IrgCampusDiplomadosClassStart(IrgCampusDiplomadosPortal):

    def download_diplomado(self, diplomado_id, **kw):
        partner = request.env.user.partner_id
        diplomado = request.env['irg.diplomado.registry'].sudo().browse(diplomado_id)
        if diplomado.exists() and diplomado.student_id.partner_id.id == partner.id:
            try:
                diplomado.action_reprint()
            except Exception:
                _logger.exception(
                    'Error al regenerar el PDF del diplomado %s', diplomado_id
                )
        return super().download_diplomado(diplomado_id, **kw)
```

Gradebook check for campus stays in `super()`; reprint after ownership check is required even if grade later fails (PDF may refresh for an ineligible user who knows the id). To avoid that, move reprint to after the same grade check by copying the gradebook lookup before reprint:

```python
        if not diplomado.exists() or diplomado.student_id.partner_id.id != partner.id:
            return super().download_diplomado(diplomado_id, **kw)
        gradebook = request.env['app.gradebook.student'].sudo().search([
            ('student_id', '=', diplomado.student_id.id),
            ('course_id', '=', diplomado.course_id.id),
        ], limit=1)
        if gradebook and gradebook.total_final > 7.0:
            try:
                diplomado.action_reprint()
            except Exception:
                _logger.exception(...)
        return super().download_diplomado(diplomado_id, **kw)
```

Use this second campus variant (auth + grade before reprint).

- [ ] **Step 2: Add HttpCase that download with existing attachment calls reprint** (counter mock). Re-run canonical command. All PASS.

- [ ] **Step 3: Do not commit** unless the user asks.

---

## Spec coverage

| Spec item | Task |
| --- | --- |
| date_start_class source + fallback | Task 2 helper |
| Wizard defaults | Task 3 |
| Portal create | Task 4 `_create_diplomado_registry` |
| Always regenerate on reprint/download | Task 2 + Task 4 |
| Overwrite same attachment | Task 2 |
| End date / issue date unchanged | asserted in reprint test |
| Graduation diplomas out of scope | no files there |
| E2E after GREEN | validator + e2e-tester |

## Residual test interaction

`irg_diplomado_portal_request` HttpCase `test_registry_links_request_and_download_is_secure` expects the stored PDF bytes when an attachment already exists. Installing this module makes download call `action_reprint`. Do not edit that module. Our tests define the new contract.
