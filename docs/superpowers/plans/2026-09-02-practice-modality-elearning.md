# Practice Modality eLearning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar la modalidad de prácticas en cada matrícula y usarla para mostrar u ocultar secciones de elearning, sin tocar módulos existentes.

**Architecture:** Dos addons nuevos. `irg_student_course_practice_modality` persiste `op.student.course.irg_practice_center_type_id` y lo sincroniza desde la última solicitud en `approved`/`progress`/`end`. `irg_practice_slide_restrictions` añade `slide.slide.irg_required_practice_type` (vacío = común) y bloquea en servidor con el mismo patrón que los lotes.

**Tech Stack:** Odoo 16, herencia `_inherit` / xpath, `TransactionCase`, `docker-compose.local.yml` + overlay del worktree.

**Spec:** `docs/superpowers/specs/2026-09-02-practice-modality-elearning-design.md`

**Constraints:**

- No modificar addons existentes.
- TDD: test que falle, luego código mínimo.
- Runtime Odoo solo con `docker-compose.local.yml` y overlay. Restaurar el servicio compartido al terminar.
- No commit, push ni PR sin autorización explícita nueva.
- `sudo()` solo para sync del Many2one y para leer matrícula/canal al decidir visibilidad.

**Knowledge:**

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`: addons en `addons-extra/extrairg/`, prefijo `irg_`.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_course_elearning_featured_section.md`: el canal se resuelve por `op_subject_ids` / `subject_ids`, no hay `course_id` fiable en `slide.channel`.

---

## File map

**Module A**

- Create: `addons-extra/extrairg/irg_student_course_practice_modality/__init__.py`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/__manifest__.py`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/models/__init__.py`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/models/op_student_course.py`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/models/op_student.py`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/models/practice_request.py`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/views/op_student_course_views.xml`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/views/user_profile_templates.xml`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/views/educational_info_portal.xml`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_student_course_practice_modality/tests/test_student_course_practice_modality.py`

**Module B**

- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/__init__.py`
- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/__manifest__.py`
- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/models/__init__.py`
- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/models/slide_slide.py`
- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/controllers/__init__.py`
- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/controllers/main.py`
- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/views/slide_slide_view.xml`
- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/views/templates.xml`
- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_practice_slide_restrictions/tests/test_practice_slide_restrictions.py`

**Mission**

- Create: `missions/irg-practice-modality-elearning/plan.md`
- Create: `missions/irg-practice-modality-elearning/execution.md`
- Create: `missions/irg-practice-modality-elearning/docker-compose.worktree.yml`
- Create: `missions/irg-practice-modality-elearning/artifacts/.gitkeep`

---

### Task 1: Skeleton A + tests RED de sync y campo

**Files:**

- Create: all Module A Python files and tests listed above
- Test: `addons-extra/extrairg/irg_student_course_practice_modality/tests/test_student_course_practice_modality.py`

- [ ] **Step 1: Write the failing tests** (helpers de curso/lote/matrícula/tipo/solicitud; asserts de campo, draft, approve, last-wins, dos cursos, reject no borra, staff write)

```python
# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativelta
from lxml import etree

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_student_course_practice_modality')
class TestStudentCoursePracticeModality(TransactionCase):

    def _make_enrollment(self, suffix):
        today = fields.Date.today()
        course = self.env['op.course'].create({
            'name': 'Curso practicas %s' % suffix,
            'code': 'IRG-PM-%s' % suffix,
        })
        batch = self.env['op.batch'].create({
            'name': 'Lote %s' % suffix,
            'code': 'IRG-PM-B-%s' % suffix,
            'course_id': course.id,
            'start_date': today,
            'end_date': today + relativedelta(months=1),
        })
        partner = self.env['res.partner'].create({
            'name': 'Alumno %s' % suffix,
            'email': 'alumno.%s@example.test' % suffix.lower(),
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'Alumno',
            'last_name': suffix,
            'gender': 'o',
        })
        enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
        })
        return course, student, enrollment

    def _make_practice_type(self, type_of_practice):
        return self.env['practice.center.type'].create({
            'type_of_practice': type_of_practice,
        })

    def _make_request(self, enrollment, practice_type, state='draft'):
        return self.env['practice.request'].create({
            'name': enrollment.student_id.name,
            'email': enrollment.student_id.email or 'alumno@example.test',
            'course_id': enrollment.id,
            'practice_center_type_id': practice_type.id,
            'state': state,
        })

    def test_enrollment_field_exists(self):
        self.assertIn(
            'irg_practice_center_type_id',
            self.env['op.student.course']._fields,
        )

    def test_draft_request_does_not_sync(self):
        _course, _student, enrollment = self._make_enrollment('DRAFT')
        practice_type = self._make_practice_type('on_site')
        self._make_request(enrollment, practice_type, state='draft')
        self.assertFalse(enrollment.irg_practice_center_type_id)

    def test_approve_syncs_modality_to_enrollment(self):
        _course, _student, enrollment = self._make_enrollment('APPR')
        practice_type = self._make_practice_type('tfm_validation')
        request = self._make_request(enrollment, practice_type, state='draft')
        request.action_approve()
        self.assertEqual(enrollment.irg_practice_center_type_id, practice_type)

    def test_progress_and_end_keep_syncing(self):
        _course, _student, enrollment = self._make_enrollment('PROG')
        practice_type = self._make_practice_type('validation')
        request = self._make_request(enrollment, practice_type, state='draft')
        request.action_approve()
        request.action_progress()
        self.assertEqual(enrollment.irg_practice_center_type_id, practice_type)
        request.action_end()
        self.assertEqual(enrollment.irg_practice_center_type_id, practice_type)

    def test_latest_synced_request_wins(self):
        _course, _student, enrollment = self._make_enrollment('WIN')
        first_type = self._make_practice_type('on_site')
        second_type = self._make_practice_type('on_site_origin')
        first = self._make_request(enrollment, first_type, state='draft')
        first.action_approve()
        second = self._make_request(enrollment, second_type, state='draft')
        second.action_approve()
        self.assertEqual(enrollment.irg_practice_center_type_id, second_type)

    def test_two_courses_are_independent(self):
        _c1, _s1, enrollment_a = self._make_enrollment('A')
        _c2, student_b, enrollment_b = self._make_enrollment('B')
        enrollment_b.student_id = enrollment_a.student_id
        student_b.unlink()
        type_a = self._make_practice_type('homeclass_sincronas')
        type_b = self._make_practice_type('homeclass_asincronas')
        req_a = self._make_request(enrollment_a, type_a, state='draft')
        req_b = self._make_request(enrollment_b, type_b, state='draft')
        req_a.action_approve()
        req_b.action_approve()
        self.assertEqual(enrollment_a.irg_practice_center_type_id, type_a)
        self.assertEqual(enrollment_b.irg_practice_center_type_id, type_b)

    def test_reject_does_not_clear_enrollment(self):
        _course, _student, enrollment = self._make_enrollment('REJ')
        approved_type = self._make_practice_type('on_site')
        other_type = self._make_practice_type('distance')
        approved = self._make_request(enrollment, approved_type, state='draft')
        approved.action_approve()
        rejected = self._make_request(enrollment, other_type, state='draft')
        rejected.action_reject()
        self.assertEqual(enrollment.irg_practice_center_type_id, approved_type)

    def test_staff_can_write_enrollment_field(self):
        _course, _student, enrollment = self._make_enrollment('STAFF')
        practice_type = self._make_practice_type('tfm_validation')
        enrollment.write({'irg_practice_center_type_id': practice_type.id})
        self.assertEqual(enrollment.irg_practice_center_type_id, practice_type)

    def test_backend_views_include_practice_field(self):
        tree = self.env.ref(
            'irg_student_course_practice_modality.view_op_student_course_tree_practice_modality'
        )
        form = self.env.ref(
            'irg_student_course_practice_modality.view_op_student_course_form_practice_modality'
        )
        for view in (tree, form):
            arch = etree.fromstring(view.arch_db)
            self.assertTrue(arch.xpath('//field[@name="irg_practice_center_type_id"]'))
```

- [ ] **Step 2: Add module skeleton so tests are discoverable, without sync logic yet** (`__manifest__.py` depends `openeducat_core`, `isep_practices_2`, `isep_website_custom`; models vacíos salvo el campo en `op.student.course` si hace falta para que el test de campo no pete por import — el test de campo DEBE fallar si el campo no existe; por tanto el skeleton NO incluye el campo todavía).

Para RED real: skeleton con `__manifest__` y tests, **sin** `irg_practice_center_type_id`. El primer test falla con `AssertionError`. El resto fallará al acceder al campo.

- [ ] **Step 3: Run RED**

```bash
docker compose -f /Users/ivrogo/Workspace/Proyectos\ iRG/Odoo16iRG/docker-compose.local.yml \
  -f missions/irg-practice-modality-elearning/docker-compose.worktree.yml \
  run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_practice_modality \
  -i irg_student_course_practice_modality --test-enable \
  --test-tags /irg_student_course_practice_modality \
  --stop-after-init --workers=0 --http-port=18069 --log-level=test
```

Expected: FAIL `test_enrollment_field_exists`. Guardar salida en `missions/irg-practice-modality-elearning/artifacts/red-module-a.txt`.

- [ ] **Step 4: Implement Module A**

`models/op_student_course.py`:

```python
# -*- coding: utf-8 -*-
from odoo import fields, models


class OpStudentCourse(models.Model):
    _inherit = 'op.student.course'

    irg_practice_center_type_id = fields.Many2one(
        'practice.center.type',
        string='Modalidad de prácticas',
        tracking=True,
        help='Tipo de prácticas de esta matrícula. Lo rellena la última '
             'solicitud aprobada o posterior y secretaría puede corregirlo.',
    )
```

`models/op_student.py`:

```python
# -*- coding: utf-8 -*-
from odoo import models


class OpStudent(models.Model):
    _inherit = 'op.student'

    def irg_get_practice_center_type(self, course):
        self.ensure_one()
        if not course:
            return self.env['practice.center.type']
        enrollment = self.course_detail_ids.filtered(
            lambda rec: rec.course_id.id == course.id
        )[:1]
        return enrollment.irg_practice_center_type_id
```

`models/practice_request.py`:

```python
# -*- coding: utf-8 -*-
from odoo import api, models

IRG_PRACTICE_MODALITY_SYNC_STATES = ('approved', 'progress', 'end')


class PracticeRequest(models.Model):
    _inherit = 'practice.request'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_sync_practice_modality_to_enrollment()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ('state', 'practice_center_type_id', 'course_id')):
            self._irg_sync_practice_modality_to_enrollment()
        return res

    def _irg_sync_practice_modality_to_enrollment(self):
        enrollments = self.mapped('course_id').filtered(lambda rec: rec)
        Request = self.env['practice.request'].sudo()
        for enrollment in enrollments:
            latest = Request.search([
                ('course_id', '=', enrollment.id),
                ('state', 'in', IRG_PRACTICE_MODALITY_SYNC_STATES),
            ], order='request_date desc, id desc', limit=1)
            if not latest or not latest.practice_center_type_id:
                continue
            if enrollment.irg_practice_center_type_id == latest.practice_center_type_id:
                continue
            enrollment.sudo().write({
                'irg_practice_center_type_id': latest.practice_center_type_id.id,
            })
```

Views: xpath `course_id` after en tree y form de `openeducat_core.view_op_student_course_*`. Campus: párrafo bajo el `h5` del curso. Portal educativo: `<th>` y `<td>` de modalidad.

- [ ] **Step 5: Run GREEN** with the same docker command. Expected: tests A pass. Evidence: `artifacts/green-module-a.txt`.

---

### Task 2: Skeleton B + tests RED de visibilidad

**Files:** Module B tests first, then implementation.

Tests cubren: vacío permite; sin modalidad bloquea requisito; match permite; otra modalidad bloquea; dos cursos no cruzan; hijo hereda; QWeb de error contiene “Contenido Bloqueado”.

`is_user_allowed_by_practice_type(user)` es el contrato.

- [ ] **Step 1: Write failing tests** in `tests/test_practice_slide_restrictions.py` (tag `/irg_practice_slide_restrictions`).
- [ ] **Step 2: Run RED** `-i irg_practice_slide_restrictions` (instala A por dependencia). Expected: FAIL field missing. Evidence: `artifacts/red-module-b.txt`.
- [ ] **Step 3: Implement Module B**

Campo:

```python
irg_required_practice_type = fields.Selection(
    selection=lambda self: self.env['practice.center.type']._fields[
        'type_of_practice'
    ]._description_selection(self.env),
    string='Modalidad de prácticas requerida',
    help='Vacío: visible para todos. Con valor: solo alumnos cuya matrícula '
         'de este curso tenga esa modalidad.',
)
```

Resolver cursos del canal:

```python
def _irg_courses_for_channel(self):
    self.ensure_one()
    channel = self.channel_id
    Course = self.env['op.course'].sudo()
    subjects = channel.op_subject_ids if 'op_subject_ids' in channel._fields else Course.browse()
    courses = Course.search([('subject_ids', 'in', subjects.ids)]) if subjects else Course.browse()
    if 'slide_channel_ids' in Course._fields:
        courses |= Course.search([('slide_channel_ids', 'in', channel.id)])
    return courses
```

Controller hereda `WebsiteSlidesBatchRestrictions`. Plantilla copiada del aviso de lotes, texto: no pueden visualizar ese documento por la modalidad de prácticas. QWeb índice/sidebar: `t-if` como `allowed_batch_ids` pero con `is_user_allowed_by_practice_type`.

Herencia de padre: override `_apply_parent_limitations` y el onchange equivalente copiando `irg_required_practice_type` si el hijo está vacío.

- [ ] **Step 4: Run GREEN** `--test-tags /irg_student_course_practice_modality,/irg_practice_slide_restrictions`. Evidence: `artifacts/green-modules.txt`.
- [ ] **Step 5: Restore shared compose** (no dejar el servicio montando el worktree). Cleanup de la base `test_irg_practice_modality` si se creó con `run --rm`.

---

### Task 3: Docs de módulo y knowledge

- Create: `doc/modules/extrairg/irg_student_course_practice_modality.md`
- Create: `doc/modules/extrairg/irg_practice_slide_restrictions.md`
- Create: `missions/irg-practice-modality-elearning/CHANGELOG.md`
- Create: `.agents/knowledge/odoo_development_modding/artifacts/irg_practice_modality_elearning.md` — solo el patrón reutilizable: variable en matrícula + requisito vacío=común en slides; no mezclar con `irg_content_modality`; sync por última solicitud `approved/progress/end`.

Solo después de Review y Validación `passed`.

---

## Overlay

`missions/irg-practice-modality-elearning/docker-compose.worktree.yml`:

```yaml
services:
  odoo_local:
    volumes:
      - /Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/.worktrees/irg-practice-modality-elearning/addons-extra:/mnt/extra-addons:ro
```

Comando siempre con `-f docker-compose.local.yml` del checkout principal y este overlay, `run --rm --no-deps`.

## E2E

Disparo: sí (QWeb portal y website_slides). Check `e2e_testsprite` tras el resto en verde. `projectPath` = `addons-extra/extrairg/irg_practice_slide_restrictions`. Puerto 8069, base desechable, nunca beta/prod.

## Security Advisor

Cambio de visibilidad de contenido, no de autenticación de usuarios ni borrado. Control en servidor. `[YES] Reason: protected GET is enforced server-side; sudo is scoped to enrollment sync and visibility reads; no secrets or historical deletion.`
