# HomeClass Subject Lead Days Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tras un sync HomeClass exitoso, dejar `date_from` de cada asignatura
3 días antes de la fecha del scheduler original, sin tocar `date_to` ni
`date_start_class`.

**Architecture:** Addon nuevo `irg_batch_homeclass_subject_lead_days` que
hereda `op.batch`, llama a `super()._sync_homeclass_calendar()` y, solo si
ese resultado es verdadero, aplica
`_irg_apply_homeclass_subject_lead_days()`. El scheduler original no se
edita.

**Tech Stack:** Odoo 16 ORM, Python 3, `TransactionCase`, `unittest.mock`.

## Global Constraints

- No modificar `irg_batch_homeclass_api_scheduler` ni ningún módulo existente.
- El addon vive en `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/`.
- Offset fijo: `IRG_HOMECLASS_SUBJECT_LEAD_DAYS = 3`.
- Solo mutar `op.subject.to.batch.date_from` cuando está informado.
- No mutar `date_to` ni `op.batch.date_start_class`.
- No recortar contra `op.batch.start_date`.
- Tests con `@tagged('post_install', '-at_install')`.
- Tests no llaman a la API real: parchear
  `odoo.addons.irg_batch_homeclass_api_scheduler.models.op_batch.requests.get`
  y crear lotes con `skip_homeclass_sync`.
- No importar `tests` desde el `__init__.py` raíz del módulo.
- `auto_install` False. Versión `16.0.1.0.0`.
- E2E no forma parte de implementación: el validador lo registra `skipped`.
- No hay autorización de commit, push, PR ni despliegue; no ejecutar `git commit`.

---

### Task 1: Addon, tests RED y offset GREEN

**Files:**
- Create: `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/__init__.py`
- Create: `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/__manifest__.py`
- Create: `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/models/__init__.py`
- Create: `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/models/op_batch.py`
- Create: `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/tests/test_subject_lead_days.py`

**Interfaces:**
- Produces: `IRG_HOMECLASS_SUBJECT_LEAD_DAYS: int = 3`
- Produces: `OpBatch._irg_apply_homeclass_subject_lead_days(self) -> bool`
- Extends: `OpBatch._sync_homeclass_calendar(self) -> bool` (return value of `super()`)

- [ ] **Step 1: Write the failing tests and module skeleton without the offset**

Create `__init__.py`:

```python
# -*- coding: utf-8 -*-
from . import models
```

Create `__manifest__.py`:

```python
{
    'name': 'IRG Batch HomeClass Subject Lead Days',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Open HomeClass subjects three days before the calendar API date',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_batch_homeclass_api_scheduler',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
```

Create `models/__init__.py`:

```python
# -*- coding: utf-8 -*-
from . import op_batch
```

Create `models/op_batch.py` **without** applying the offset yet (RED):

```python
# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models

IRG_HOMECLASS_SUBJECT_LEAD_DAYS = 3


class OpBatch(models.Model):
    _inherit = 'op.batch'

    def _irg_apply_homeclass_subject_lead_days(self):
        return True

    def _sync_homeclass_calendar(self):
        result = super()._sync_homeclass_calendar()
        if result:
            self._irg_apply_homeclass_subject_lead_days()
        return result
```

Create `tests/__init__.py`:

```python
# -*- coding: utf-8 -*-
from . import test_subject_lead_days
```

Create `tests/test_subject_lead_days.py`:

```python
# -*- coding: utf-8 -*-
from datetime import date
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.irg_batch_homeclass_api_scheduler.models.op_batch import (
    OpBatch as SchedulerOpBatch,
)
from odoo.addons.irg_batch_homeclass_subject_lead_days.models.op_batch import (
    IRG_HOMECLASS_SUBJECT_LEAD_DAYS,
)


@tagged('post_install', '-at_install')
class TestHomeclassSubjectLeadDays(TransactionCase):

    def setUp(self):
        super().setUp()
        requests_patcher = patch(
            'odoo.addons.irg_batch_homeclass_api_scheduler.models.op_batch.requests.get',
            side_effect=AssertionError('Calendar API must not be called in these tests'),
        )
        requests_patcher.start()
        self.addCleanup(requests_patcher.stop)

        self.subject_matched = self.env['op.subject'].create({
            'name': 'IRG Lead Days Matched',
            'code': 'IRG-HCSLD-A',
        })
        self.subject_fallback = self.env['op.subject'].create({
            'name': 'IRG Lead Days Fallback',
            'code': 'IRG-HCSLD-B',
        })
        self.course = self.env['op.course'].create({
            'name': 'IRG Lead Days Course',
            'code': 'IRG-HCSLD-C',
            'subject_ids': [(6, 0, [
                self.subject_matched.id,
                self.subject_fallback.id,
            ])],
        })
        self.modality_hc = self.env['op.modality'].search(
            [('code', '=', 'HC')], limit=1
        )
        if not self.modality_hc:
            self.modality_hc = self.env['op.modality'].create({
                'name': 'HomeClass',
                'code': 'HC',
                'new_code': 'HC',
                'analytic_code': 'HC',
            })
        self.batch = self.env['op.batch'].with_context(
            skip_homeclass_sync=True,
        ).create({
            'name': 'IRG-HCSLD-HC01',
            'code': 'IRG-HCSLD-HC01',
            'course_id': self.course.id,
            'modality_id': self.modality_hc.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
            'date_start_class': date(2026, 2, 1),
        })
        self.assertTrue(self.batch.is_homeclass_batch)
        self.assertEqual(len(self.batch.subject_to_batch_ids), 2)

    def _line(self, subject):
        return self.batch.subject_to_batch_ids.filtered(
            lambda line: line.subject_id == subject
        )

    def _fake_parent_success(self, batch):
        batch.ensure_one()
        matched = batch.subject_to_batch_ids.filtered(
            lambda line: line.subject_id.code == 'IRG-HCSLD-A'
        )
        fallback = batch.subject_to_batch_ids - matched
        matched.write({
            'date_from': date(2026, 1, 16),
            'date_to': batch.end_date,
        })
        fallback.write({
            'date_from': batch.start_date,
            'date_to': batch.end_date,
        })
        batch.write({'date_start_class': date(2026, 1, 16)})
        return True

    def test_apply_shifts_date_from_only(self):
        self.batch.with_context(skip_homeclass_sync=True).write({
            'date_start_class': date(2026, 1, 16),
        })
        self._line(self.subject_matched).write({
            'date_from': date(2026, 1, 16),
            'date_to': date(2026, 12, 31),
        })
        self._line(self.subject_fallback).write({
            'date_from': date(2026, 1, 1),
            'date_to': date(2026, 12, 31),
        })

        self.batch._irg_apply_homeclass_subject_lead_days()

        self.assertEqual(IRG_HOMECLASS_SUBJECT_LEAD_DAYS, 3)
        self.assertEqual(
            self._line(self.subject_matched).date_from,
            date(2026, 1, 13),
        )
        self.assertEqual(
            self._line(self.subject_fallback).date_from,
            date(2025, 12, 29),
        )
        self.assertEqual(
            self._line(self.subject_matched).date_to,
            date(2026, 12, 31),
        )
        self.assertEqual(
            self._line(self.subject_fallback).date_to,
            date(2026, 12, 31),
        )
        self.assertEqual(self.batch.date_start_class, date(2026, 1, 16))

    def test_apply_skips_empty_date_from(self):
        line = self._line(self.subject_matched)
        line.write({'date_from': False, 'date_to': date(2026, 12, 31)})
        self.batch._irg_apply_homeclass_subject_lead_days()
        self.assertFalse(line.date_from)
        self.assertEqual(line.date_to, date(2026, 12, 31))

    def test_sync_success_shifts_and_keeps_class_start(self):
        with patch.object(
            SchedulerOpBatch,
            '_sync_homeclass_calendar',
            autospec=True,
            side_effect=self._fake_parent_success,
        ):
            result = self.batch._sync_homeclass_calendar()

        self.assertTrue(result)
        self.assertEqual(
            self._line(self.subject_matched).date_from,
            date(2026, 1, 13),
        )
        self.assertEqual(
            self._line(self.subject_fallback).date_from,
            date(2025, 12, 29),
        )
        self.assertEqual(
            self._line(self.subject_matched).date_to,
            date(2026, 12, 31),
        )
        self.assertEqual(self.batch.date_start_class, date(2026, 1, 16))

    def test_sync_failure_leaves_dates_untouched(self):
        self._line(self.subject_matched).write({
            'date_from': date(2026, 6, 1),
            'date_to': date(2026, 6, 30),
        })
        with patch.object(
            SchedulerOpBatch,
            '_sync_homeclass_calendar',
            autospec=True,
            return_value=False,
        ):
            result = self.batch._sync_homeclass_calendar()

        self.assertFalse(result)
        self.assertEqual(
            self._line(self.subject_matched).date_from,
            date(2026, 6, 1),
        )
        self.assertEqual(
            self._line(self.subject_matched).date_to,
            date(2026, 6, 30),
        )
        self.assertEqual(self.batch.date_start_class, date(2026, 2, 1))

    def test_sync_is_idempotent_against_parent_absolute_dates(self):
        with patch.object(
            SchedulerOpBatch,
            '_sync_homeclass_calendar',
            autospec=True,
            side_effect=self._fake_parent_success,
        ):
            self.batch._sync_homeclass_calendar()
            self.batch._sync_homeclass_calendar()

        self.assertEqual(
            self._line(self.subject_matched).date_from,
            date(2026, 1, 13),
        )
```

- [ ] **Step 2: Run RED**

Run:

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_hc_lead \
  -i irg_batch_homeclass_subject_lead_days --test-enable \
  --test-tags=/irg_batch_homeclass_subject_lead_days \
  --stop-after-init --http-port=8099 --log-level=test
```

Expected: install succeeds; `test_apply_shifts_date_from_only`,
`test_sync_success_shifts_and_keeps_class_start` and
`test_sync_is_idempotent_against_parent_absolute_dates` FAIL because
`date_from` stays on 16/01/2026 and 01/01/2026. Save the tail of the log to
`missions/irg-batch-homeclass-subject-lead-days/artifacts/red-tests.txt`.
If the database `test_irg_hc_lead` does not exist, create it with the same
command (Odoo creates it on `-i` when permitted) or use a disposable name
and record it in `execution.md`.

- [ ] **Step 3: Implement the offset**

Replace `_irg_apply_homeclass_subject_lead_days` in
`addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/models/op_batch.py`
with:

```python
# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models

IRG_HOMECLASS_SUBJECT_LEAD_DAYS = 3


class OpBatch(models.Model):
    _inherit = 'op.batch'

    def _irg_apply_homeclass_subject_lead_days(self):
        self.ensure_one()
        lead = timedelta(days=IRG_HOMECLASS_SUBJECT_LEAD_DAYS)
        self_ctx = self.with_context(skip_homeclass_sync=True)
        for line in self_ctx.subject_to_batch_ids:
            if not line.date_from:
                continue
            new_date = line.date_from - lead
            if new_date != line.date_from:
                line.write({'date_from': new_date})
        return True

    def _sync_homeclass_calendar(self):
        result = super()._sync_homeclass_calendar()
        if result:
            self._irg_apply_homeclass_subject_lead_days()
        return result
```

- [ ] **Step 4: Run GREEN**

Run the same docker command as Step 2. Expected: all tests in
`/irg_batch_homeclass_subject_lead_days` PASS, 0 failed, 0 errors. Save the
tail to
`missions/irg-batch-homeclass-subject-lead-days/artifacts/green-tests.txt`.
Update `execution.md` with the command, database name and counts.

- [ ] **Step 5: Syntax check**

Run:

```bash
python3 -m py_compile \
  addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/__init__.py \
  addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/__manifest__.py \
  addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/models/__init__.py \
  addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/models/op_batch.py \
  addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/tests/__init__.py \
  addons-extra/extrairg/irg_batch_homeclass_subject_lead_days/tests/test_subject_lead_days.py
```

Expected: exit 0. `__manifest__.py` is a dict module; if `py_compile`
rejects it, compile only the `.py` files that are not the manifest.

Do not commit.
