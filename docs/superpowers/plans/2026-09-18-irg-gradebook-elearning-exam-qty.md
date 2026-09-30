# Gradebook E-learning Exam Qty Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detectar, por línea de libreta, cuántos exámenes hay en el canal
e-learning de esa asignatura con el lote de la libreta como requisito, y usar
ese N como `exam.qty` (sin entero en `op.batch`).

**Architecture:** Addon nuevo `irg_gradebook_elearning_exam_qty` que hereda
`app.gradebook.subject`, cuenta surveys únicos tipo `exam` publicados en
`op_subject.slide_channel_id` según `allowed_batch_ids`, y sustituye
`gradebook['exam']['qty']` en `_get_gradebook_info` si N > 0 y la libreta no
está `done`.

**Tech Stack:** Odoo 16 ORM, Python 3, `TransactionCase`.

## Global Constraints

- No modificar `isep_gradebook`, `irg_batch_slide_restrictions` ni ningún
  módulo existente.
- El addon vive en `addons-extra/extrairg/irg_gradebook_elearning_exam_qty/`.
- No crear campos en `op.batch` ni en `app.gradebook.student`.
- N es por `app.gradebook.subject` (canal de esa asignatura).
- Requisito de lote: `allowed_batch_ids` vacío cuenta para todos; si tiene
  valores, solo si `gradebook_student_id.batch_id` está en la lista.
- No usar `is_user_allowed_by_batch` (usuario ORM ≠ alumno).
- No filtrar por `scheduled_date`.
- N = 0 → qty de `super()`. Libreta `done` → no sustituir.
- Tests `@tagged('post_install', '-at_install')`.
- No importar `tests` desde el `__init__.py` raíz.
- `auto_install` False. Versión `16.0.1.0.0`.
- E2E no forma parte de implementación: el validador lo registra `skipped`.
- No hay autorización de commit, push, PR ni despliegue; no ejecutar
  `git commit`.

---

### Task 1: Addon, tests RED y recuento GREEN

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_elearning_exam_qty/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_elearning_exam_qty/__manifest__.py`
- Create: `addons-extra/extrairg/irg_gradebook_elearning_exam_qty/models/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_elearning_exam_qty/models/app_gradebook_subject.py`
- Create: `addons-extra/extrairg/irg_gradebook_elearning_exam_qty/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_elearning_exam_qty/tests/test_elearning_exam_qty.py`

**Interfaces:**
- Produces: `AppGradebookSubject._irg_slide_allows_gradebook_batch(self, slide, batch) -> bool`
- Produces: `AppGradebookSubject._irg_elearning_exam_qty(self) -> int`
- Extends: `AppGradebookSubject._get_gradebook_info(self, rec) -> dict`

- [ ] **Step 1: Write the failing tests and module skeleton without the override**

Create `__init__.py`:

```python
# -*- coding: utf-8 -*-
from . import models
```

Create `__manifest__.py`:

```python
# -*- coding: utf-8 -*-
{
    'name': 'IRG Gradebook E-learning Exam Qty',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': (
        'Set exam qty from e-learning exam slides allowed for the '
        'gradebook batch'
    ),
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'isep_gradebook',
        'irg_batch_slide_restrictions',
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
from . import app_gradebook_subject
```

Create `models/app_gradebook_subject.py` **without** substituting qty yet (RED):

```python
# -*- coding: utf-8 -*-
from odoo import models


class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    def _irg_slide_allows_gradebook_batch(self, slide, batch):
        self.ensure_one()
        allowed = slide.sudo().allowed_batch_ids
        if not allowed:
            return True
        return bool(batch) and batch in allowed

    def _irg_elearning_exam_qty(self):
        self.ensure_one()
        return 0

    def _get_gradebook_info(self, rec):
        return super()._get_gradebook_info(rec)
```

Create `tests/__init__.py`:

```python
# -*- coding: utf-8 -*-
from . import test_elearning_exam_qty
```

Create `tests/test_elearning_exam_qty.py`:

```python
# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestElearningExamQty(TransactionCase):

    def setUp(self):
        super().setUp()
        self.counter = 0
        self.template = self.env['app.gradebook'].create({
            'name': 'IRG Exam Qty Template',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100.0,
                'qty': 1,
            })],
        })
        self.product = self.env['product.product'].create({
            'name': 'IRG Exam Qty Product',
            'type': 'service',
        })

    def _idx(self):
        self.counter += 1
        return self.counter

    def _create_survey(self, title, survey_type='exam'):
        return self.env['survey.survey'].create({
            'title': title,
            'survey_type': survey_type,
        })

    def _create_exam_slide(
            self, channel, title, batches=None, published=True,
            scheduled=None, survey=None, survey_type='exam'):
        survey = survey or self._create_survey(title, survey_type)
        values = {
            'name': title,
            'channel_id': channel.id,
            'slide_category': 'certification',
            'survey_id': survey.id,
            'is_published': published,
        }
        if batches:
            values['allowed_batch_ids'] = [(6, 0, [b.id for b in batches])]
        if scheduled:
            values['scheduled_date'] = scheduled
        return self.env['slide.slide'].create(values)

    def _create_gradebook(self, subject_count=1, batch=None, subjects=None):
        idx = self._idx()
        if batch:
            course = batch.course_id
            if not course.gradebook_id:
                course.gradebook_id = self.template.id
        else:
            course = self.env['op.course'].create({
                'name': 'IRG Exam Qty Course %s' % idx,
                'code': 'IRGEQ%03d' % idx,
                'lang': self.env.user.lang or 'en_US',
                'gradebook_id': self.template.id,
            })
            batch = self.env['op.batch'].create({
                'name': 'IRG-EQ-%s' % idx,
                'code': 'IRG-EQ-%s' % idx,
                'course_id': course.id,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            })
        partner = self.env['res.partner'].create({
            'name': 'IRG Exam Qty Student %s' % idx,
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'IRG',
            'last_name': 'Exam Qty %s' % idx,
            'gender': 'm',
        })
        register = self.env['op.admission.register'].create({
            'name': 'IRG Exam Qty Register %s' % idx,
            'course_id': course.id,
            'product_id': self.product.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
        })
        admission = self.env['op.admission'].create({
            'name': 'IRG Exam Qty Admission %s' % idx,
            'first_name': 'IRG',
            'last_name': 'Exam Qty %s' % idx,
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'irg.exam.qty.%s@example.com' % idx,
            'partner_id': partner.id,
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
            'register_id': register.id,
        })
        gradebook = self.env['app.gradebook.student'].create({
            'admission_id': admission.id,
            'state': 'in_progress',
        })
        lines = self.env['app.gradebook.subject']
        if subjects:
            for subject in subjects:
                lines |= self.env['app.gradebook.subject'].create({
                    'gradebook_student_id': gradebook.id,
                    'op_subject_id': subject.id,
                })
        else:
            for subject_index in range(1, subject_count + 1):
                channel = self.env['slide.channel'].create({
                    'name': 'IRG EQ Channel %s-%s' % (idx, subject_index),
                    'channel_type': 'training',
                })
                subject = self.env['op.subject'].create({
                    'name': 'IRG EQ Subject %s-%s' % (idx, subject_index),
                    'code': 'IRGEQ-%s-%s' % (idx, subject_index),
                    'subject_type': 'compulsory',
                    'course_id': course.id,
                    'slide_channel_id': channel.id,
                })
                lines |= self.env['app.gradebook.subject'].create({
                    'gradebook_student_id': gradebook.id,
                    'op_subject_id': subject.id,
                })
        return gradebook, lines, batch

    def _add_exam_result(self, line, score=10.0):
        return self.env['app.gradebook.result'].create({
            'gradebook_subject_id': line.id,
            'survey_type': 'exam',
            'scoring_total': score,
        })

    def test_unrestricted_published_exam_sets_qty_one(self):
        gradebook, lines, _batch = self._create_gradebook()
        line = lines[0]
        self._create_exam_slide(line.op_subject_id.slide_channel_id, 'Exam A')
        info = line._get_gradebook_info(line)
        self.assertEqual(info['exam']['qty'], 1)
        self.assertEqual(line._irg_elearning_exam_qty(), 1)

    def test_same_gradebook_can_require_three_and_two(self):
        gradebook, lines, batch = self._create_gradebook(subject_count=2)
        line_a, line_b = lines[0], lines[1]
        for name in ('A1', 'A2', 'A3'):
            self._create_exam_slide(
                line_a.op_subject_id.slide_channel_id,
                'Exam %s' % name,
                batches=[batch],
            )
        for name in ('B1', 'B2'):
            self._create_exam_slide(
                line_b.op_subject_id.slide_channel_id,
                'Exam %s' % name,
                batches=[batch],
            )
        self.assertEqual(line_a._get_gradebook_info(line_a)['exam']['qty'], 3)
        self.assertEqual(line_b._get_gradebook_info(line_b)['exam']['qty'], 2)

    def test_old_batch_ignores_exam_restricted_to_new_batch(self):
        _gradebook_old, lines_old, _batch_old = self._create_gradebook()
        line_old = lines_old[0]
        channel = line_old.op_subject_id.slide_channel_id
        self._create_exam_slide(channel, 'Legacy Exam')
        batch_new = self.env['op.batch'].create({
            'name': 'IRG-EQ-NEW',
            'code': 'IRG-EQ-NEW',
            'course_id': line_old.course_id.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
        })
        _gradebook_new, lines_new, _batch = self._create_gradebook(
            batch=batch_new,
            subjects=[line_old.op_subject_id],
        )
        line_new = lines_new[0]
        self._create_exam_slide(channel, 'New Exam', batches=[batch_new])
        self.assertEqual(
            line_old._get_gradebook_info(line_old)['exam']['qty'], 1,
        )
        self.assertEqual(
            line_new._get_gradebook_info(line_new)['exam']['qty'], 2,
        )

    def test_scheduled_future_exam_still_counts(self):
        gradebook, lines, batch = self._create_gradebook()
        line = lines[0]
        channel = line.op_subject_id.slide_channel_id
        self._create_exam_slide(channel, 'Now', batches=[batch])
        self._create_exam_slide(
            channel,
            'Later',
            batches=[batch],
            scheduled=fields.Date.today() + timedelta(days=30),
        )
        self.assertEqual(line._get_gradebook_info(line)['exam']['qty'], 2)

    def test_unpublished_assignment_and_duplicate_survey_do_not_inflate(self):
        gradebook, lines, batch = self._create_gradebook()
        line = lines[0]
        channel = line.op_subject_id.slide_channel_id
        survey = self._create_survey('Shared Exam')
        self._create_exam_slide(
            channel, 'Published', batches=[batch], survey=survey,
        )
        self._create_exam_slide(
            channel, 'Duplicate', batches=[batch], survey=survey,
        )
        self._create_exam_slide(
            channel, 'Draft', batches=[batch], published=False,
        )
        self._create_exam_slide(
            channel,
            'Homework',
            batches=[batch],
            survey_type='assignment',
        )
        self.assertEqual(line._get_gradebook_info(line)['exam']['qty'], 1)

    def test_no_channel_keeps_template_qty(self):
        gradebook, lines, _batch = self._create_gradebook()
        line = lines[0]
        line.op_subject_id.slide_channel_id = False
        info = line._get_gradebook_info(line)
        self.assertEqual(info['exam']['qty'], 1)
        self.assertEqual(line._irg_elearning_exam_qty(), 0)

    def test_close_requires_detected_qty(self):
        gradebook, lines, batch = self._create_gradebook()
        line = lines[0]
        channel = line.op_subject_id.slide_channel_id
        self._create_exam_slide(channel, 'E1', batches=[batch])
        self._create_exam_slide(channel, 'E2', batches=[batch])
        self._add_exam_result(line)
        with self.assertRaises(UserError):
            gradebook.state_to_done()
        self._add_exam_result(line, score=9.0)
        gradebook.state_to_done()
        self.assertEqual(gradebook.state, 'done')

    def test_done_gradebook_does_not_replace_qty(self):
        gradebook, lines, batch = self._create_gradebook()
        line = lines[0]
        self._create_exam_slide(
            line.op_subject_id.slide_channel_id, 'Only', batches=[batch],
        )
        self._add_exam_result(line)
        gradebook.state_to_done()
        self._create_exam_slide(
            line.op_subject_id.slide_channel_id,
            'After Close',
            batches=[batch],
        )
        self.assertEqual(line._get_gradebook_info(line)['exam']['qty'], 1)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_gb_exam_qty \
  -i irg_gradebook_elearning_exam_qty --test-enable \
  --test-tags=/irg_gradebook_elearning_exam_qty \
  --stop-after-init --http-port=8099 --log-level=test
```

Expected: FAIL. `_get_gradebook_info` still returns plantilla `qty=1` when
there are 2–3 exam slides. Guardar salida en
`missions/irg-gradebook-elearning-exam-qty/artifacts/red-tests.txt`.

Si `op.course` o `op.batch` exigen más campos (`lang`, `modality_id`),
ajustar solo el fixture de test, no el diseño.

- [ ] **Step 3: Write the minimal implementation**

Replace `models/app_gradebook_subject.py` with:

```python
# -*- coding: utf-8 -*-
from odoo import models


class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    def _irg_slide_allows_gradebook_batch(self, slide, batch):
        self.ensure_one()
        allowed = slide.sudo().allowed_batch_ids
        if not allowed:
            return True
        return bool(batch) and batch in allowed

    def _irg_elearning_exam_qty(self):
        self.ensure_one()
        channel = self.op_subject_id.slide_channel_id
        if not channel:
            return 0
        batch = self.gradebook_student_id.batch_id
        survey_ids = set()
        for slide in channel.slide_ids.sudo():
            if slide.is_category or not slide.is_published:
                continue
            survey = slide.survey_id
            if not survey or survey.survey_type != 'exam':
                continue
            if not self._irg_slide_allows_gradebook_batch(slide, batch):
                continue
            survey_ids.add(survey.id)
        return len(survey_ids)

    def _get_gradebook_info(self, rec):
        info = super()._get_gradebook_info(rec)
        if rec.gradebook_student_id.state == 'done':
            return info
        qty = rec._irg_elearning_exam_qty()
        if qty:
            info['exam']['qty'] = qty
        return info
```

- [ ] **Step 4: Run tests to verify they pass**

Same docker command as Step 2.

Expected: 0 failed, 0 error(s). Guardar salida en
`missions/irg-gradebook-elearning-exam-qty/artifacts/green-tests.txt`.

- [ ] **Step 5: Do not commit**

No hay autorización de commit. Actualizar
`missions/irg-gradebook-elearning-exam-qty/execution.md` con RED/GREEN.

---

## Spec coverage (self-review)

| Requisito | Task |
|-----------|------|
| N por asignatura/canal, no por lote | Task 1 `test_same_gradebook_can_require_three_and_two` |
| `allowed_batch_ids` como requisito | Task 1 `test_old_batch_ignores_exam_restricted_to_new_batch` |
| Vacío = sin requisito (cuenta para todos) | Task 1 `test_unrestricted_published_exam_sets_qty_one` |
| No filtrar `scheduled_date` | Task 1 `test_scheduled_future_exam_still_counts` |
| Unpublished / assignment / duplicado | Task 1 `test_unpublished_assignment_and_duplicate_survey_do_not_inflate` |
| N=0 → plantilla | Task 1 `test_no_channel_keeps_template_qty` |
| Cierre usa N detectado | Task 1 `test_close_requires_detected_qty` |
| `done` no sustituye | Task 1 `test_done_gradebook_does_not_replace_qty` |
| No campo en `op.batch` | Constraint + ningún write a batch |
