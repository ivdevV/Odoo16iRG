# IRG Student Activity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar en la ficha de `op.student` una pestaña Actividad con historial cronológico de campus + evaluaciones y export CSV, sin tocar Acceso.

**Architecture:** Módulo nuevo `irg_student_activity`. Un servicio ensambla filas homogéneas desde `slide.slide.partner` y `survey.user_input`. La UI usa un `TransientModel` de líneas y un One2many computed en `op.student`. La autorización Facultad se comprueba en servidor; tras el check, lectura con `sudo()`.

**Tech Stack:** Odoo 16, `website_slides` / `website_slides_survey`, `isep_elearning_custom`, `TransactionCase`, `docker-compose.local.yml`, TestSprite en validación.

## Global Constraints

- Código funcional solo bajo `addons-extra/extrairg/irg_student_activity/`.
- No modificar `isep_student_access`, `irg_campus_activity_audit` ni la pestaña Acceso.
- Versión `16.0.1.0.0`. Dependencias: `openeducat_core`, `isep_student_access`, `isep_elearning_custom`, `website_slides_survey`.
- Grupo: `openeducat_core.group_op_faculty`. Sin grupo → `AccessError` en carga/export.
- Fuentes v1: solo campus + evaluaciones. Sin libreta, logins, Moodle, foros.
- Límite: 500 eventos más recientes (UI y CSV).
- Campus: solo filas con `slide.slide.partner` (no “No iniciada”). Slide publicado y no categoría (`is_category=False` si el campo existe).
- CSV UTF-8 con BOM (`utf-8-sig`), columnas fijas del spec.
- Sin tabla persistente de eventos históricos (TransientModel OK).
- Runtime de pruebas: `docker-compose.local.yml`. E2E TestSprite obligatorio; `projectPath` = directorio del módulo.
- Misión `full`, tier `standard`. Security Advisor no forzado.
- Commit, push y PR requieren autorización explícita del usuario. No ejecutar el checkpoint de commit solo porque este plan lo liste.

## Knowledge and References

- Spec: `docs/superpowers/specs/2026-10-15-irg-student-activity-design.md`
- Misión: `missions/irg-student-activity/plan.md`
- Informe lote (fuentes alineadas): `addons-extra/extrairg/irg_campus_activity_audit/wizard/campus_activity_audit_wizard.py` (`_published_slides`, `_activity_sheet_rows`, `_survey_sheet_rows`)
- Fixtures e-learning: `addons-extra/extrairg/irg_campus_activity_audit/tests/test_campus_activity_audit.py`
- Export CSV de referencia: `addons-extra/extrairg/irg_admission_register_export/wizard/admission_export_wizard.py` (`_build_csv`, BOM)
- Acceso (no tocar): `addons-extra/addons_uisep/isep_student_access/views/op_student_views.xml` (`page[@name='access']`)
- `slide.channel.partner.batch_id`: `addons-extra/addons_uisep/isep_elearning_custom/models/slide_channel_partner.py`
- `survey.user_input.slide_id`: `website_slides_survey`; batch related en `isep_survey`

## File map

| Path | Responsibility |
| --- | --- |
| `addons-extra/extrairg/irg_student_activity/__manifest__.py` | Metadatos, depends, data |
| `addons-extra/extrairg/irg_student_activity/__init__.py` | Importa models |
| `addons-extra/extrairg/irg_student_activity/models/__init__.py` | Importa módulos |
| `addons-extra/extrairg/irg_student_activity/models/activity_assemble.py` | Ensamblado puro de filas (dicts) |
| `addons-extra/extrairg/irg_student_activity/models/activity_line.py` | TransientModel de líneas |
| `addons-extra/extrairg/irg_student_activity/models/op_student.py` | Compute, assert, export |
| `addons-extra/extrairg/irg_student_activity/models/csv_export.py` | Builder CSV |
| `addons-extra/extrairg/irg_student_activity/views/op_student_views.xml` | Pestaña Actividad |
| `addons-extra/extrairg/irg_student_activity/security/ir.model.access.csv` | ACL transient + lectura |
| `addons-extra/extrairg/irg_student_activity/tests/__init__.py` | Import tests |
| `addons-extra/extrairg/irg_student_activity/tests/test_student_activity.py` | TransactionCase |
| `addons-extra/extrairg/irg_student_activity/README.md` | Uso |

## Test command

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf \
  -d test_irg_student_activity \
  -i irg_student_activity \
  --test-enable \
  --test-tags=/irg_student_activity \
  --stop-after-init \
  --http-port=8099 \
  --log-level=test
```

En pasadas posteriores sobre la misma base, sustituir `-i` por `-u`. Base desechable.

## Column contract

Orden y cabeceras CSV/UI (estables):

```python
CSV_HEADERS = [
    "Fecha",
    "Tipo",
    "Curso / canal",
    "Elemento",
    "Detalle",
    "Resultado",
    "Lote",
]
```

Dict de fila ensamblada:

```python
{
    "event_datetime": fields.Datetime,  # naive UTC Odoo
    "event_type": "campus" | "evaluation",
    "channel_name": str,
    "element_name": str,
    "detail": str,
    "result": str,
    "batch_code": str,
}
```

Límites y etiquetas:

```python
ACTIVITY_LIMIT = 500
TYPE_LABELS = {"campus": "Campus", "evaluation": "Evaluación"}
```

---

### Task 1: Scaffold + assembler contract (empty / access)

**Files:**
- Create: all scaffold paths in File map except full assemble logic and views (stubs OK)
- Test: `addons-extra/extrairg/irg_student_activity/tests/test_student_activity.py`

**Interfaces:**
- Produces: `assemble_student_activity_rows(env, student, limit=ACTIVITY_LIMIT) -> list[dict]`
- Produces: `OpStudent._assert_can_view_activity()`, `OpStudent._activity_event_rows()`
- Consumes: `op.student.partner_id`

- [ ] **Step 1: Write failing tests**

```python
# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install", "irg_student_activity")
class TestStudentActivity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.faculty_group = cls.env.ref("openeducat_core.group_op_faculty")
        cls.faculty_user = cls.env["res.users"].create({
            "name": "Faculty Activity",
            "login": "faculty_activity_%s" % cls.env.cr.dbname,
            "groups_id": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.faculty_group.id,
            ])],
        })
        cls.plain_user = cls.env["res.users"].create({
            "name": "Plain Activity",
            "login": "plain_activity_%s" % cls.env.cr.dbname,
            "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
        })
        partner = cls.env["res.partner"].create({
            "name": "Alumno Activity",
            "email": "alumno.activity@example.com",
        })
        vals = {
            "name": "Alumno Activity",
            "first_name": "Alumno",
            "last_name": "Activity",
            "birth_date": "1995-01-01",
            "email": partner.email,
            "partner_id": partner.id,
        }
        if "gender" in cls.env["op.student"]._fields:
            vals["gender"] = "m"
        cls.student = cls.env["op.student"].create(vals)
        cls.partner = partner

    def test_plain_user_cannot_view_activity(self):
        student = self.student.with_user(self.plain_user)
        with self.assertRaises(AccessError):
            student._assert_can_view_activity()

    def test_empty_partner_activity_is_empty_list(self):
        rows = self.student.with_user(self.faculty_user)._activity_event_rows()
        self.assertEqual(rows, [])
```

- [ ] **Step 2: Run tests — expect FAIL** (módulo/métodos inexistentes)

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_student_activity \
  -i irg_student_activity --test-enable --test-tags=/irg_student_activity \
  --stop-after-init --http-port=8099 --log-level=test
```

Expected: FAIL (module missing or methods missing).

- [ ] **Step 3: Minimal scaffold**

`__manifest__.py`:

```python
# -*- coding: utf-8 -*-
{
    "name": "iRG Student Activity",
    "version": "16.0.1.0.0",
    "category": "Education",
    "summary": "Historial de actividad de campus y evaluaciones en la ficha del alumno",
    "author": "iRG",
    "license": "LGPL-3",
    "depends": [
        "openeducat_core",
        "isep_student_access",
        "isep_elearning_custom",
        "website_slides_survey",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/op_student_views.xml",
    ],
    "installable": True,
    "application": False,
}
```

`models/activity_assemble.py`:

```python
# -*- coding: utf-8 -*-
ACTIVITY_LIMIT = 500
TYPE_LABELS = {"campus": "Campus", "evaluation": "Evaluación"}
CSV_HEADERS = [
    "Fecha", "Tipo", "Curso / canal", "Elemento", "Detalle", "Resultado", "Lote",
]


def assemble_student_activity_rows(env, student, limit=ACTIVITY_LIMIT):
    """Return list of event dicts for student, newest first, capped."""
    return []
```

`models/activity_line.py`:

```python
# -*- coding: utf-8 -*-
from odoo import fields, models


class IrgStudentActivityLine(models.TransientModel):
    _name = "irg.student.activity.line"
    _description = "Línea de actividad del alumno"
    _order = "event_datetime desc, id desc"

    student_id = fields.Many2one("op.student", required=True, ondelete="cascade")
    event_datetime = fields.Datetime(string="Fecha", readonly=True)
    event_type = fields.Selection(
        [("campus", "Campus"), ("evaluation", "Evaluación")],
        string="Tipo",
        readonly=True,
    )
    channel_name = fields.Char(string="Curso / canal", readonly=True)
    element_name = fields.Char(string="Elemento", readonly=True)
    detail = fields.Char(string="Detalle", readonly=True)
    result = fields.Char(string="Resultado", readonly=True)
    batch_code = fields.Char(string="Lote", readonly=True)
```

`models/op_student.py`:

```python
# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError

from .activity_assemble import ACTIVITY_LIMIT, assemble_student_activity_rows


class OpStudent(models.Model):
    _inherit = "op.student"

    activity_line_ids = fields.One2many(
        "irg.student.activity.line",
        "student_id",
        string="Actividad",
        compute="_compute_activity_line_ids",
        readonly=True,
    )

    def _assert_can_view_activity(self):
        if not self.env.su and not self.env.user.has_group(
            "openeducat_core.group_op_faculty"
        ):
            raise AccessError(
                _("Solo el personal de Facultad puede ver la actividad del alumno.")
            )

    def _activity_event_rows(self):
        self.ensure_one()
        self._assert_can_view_activity()
        return assemble_student_activity_rows(
            self.env, self, limit=ACTIVITY_LIMIT
        )

    @api.depends("partner_id")
    def _compute_activity_line_ids(self):
        for student in self:
            student.activity_line_ids = [(5, 0, 0)]
```

`security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_irg_student_activity_line_faculty,irg.student.activity.line.faculty,model_irg_student_activity_line,openeducat_core.group_op_faculty,1,1,1,1
```

Stub `views/op_student_views.xml` (página mínima; se completa en Task 4):

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_op_student_form_activity" model="ir.ui.view">
        <field name="name">op.student.form.activity</field>
        <field name="model">op.student</field>
        <field name="inherit_id" ref="openeducat_core.view_op_student_form"/>
        <field name="arch" type="xml">
            <xpath expr="//page[@name='access']" position="after">
                <page name="activity" string="Actividad" groups="openeducat_core.group_op_faculty">
                    <group>
                        <div/>
                    </group>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
```

Wire `__init__.py` files. Implement empty `assemble_student_activity_rows` returning `[]`.

- [ ] **Step 4: Run tests — expect PASS** for Task 1 cases

- [ ] **Step 5: Commit only if the user authorized commit**

```bash
# Do not run unless explicitly authorized
git add addons-extra/extrairg/irg_student_activity docs/superpowers/plans/2026-10-15-irg-student-activity.md
git commit -m "$(cat <<'EOF'
feat(irg_student_activity): scaffold activity tab module

EOF
)"
```

---

### Task 2: Campus events in assembler

**Files:**
- Modify: `models/activity_assemble.py`
- Test: `tests/test_student_activity.py`

**Interfaces:**
- Consumes: `slide.slide.partner`, `slide.slide`, `slide.channel.partner.batch_id`
- Produces: campus dicts with `event_type="campus"`

- [ ] **Step 1: Write failing tests**

```python
    def _create_channel(self, name):
        vals = {
            "name": name,
            "channel_type": "training",
            "is_published": True,
        }
        Channel = self.env["slide.channel"]
        if "category_id" in Channel._fields and "moodle.categories" in self.env:
            category = self.env["moodle.categories"].search([], limit=1)
            if not category:
                category = self.env["moodle.categories"].create({"name": "Cat Activity"})
            vals["category_id"] = category.id
        return Channel.create(vals)

    def _create_slide(self, channel, name, **extra):
        vals = {
            "name": name,
            "channel_id": channel.id,
            "slide_category": "article",
            "is_published": True,
        }
        if "html_content" in self.env["slide.slide"]._fields:
            vals["html_content"] = "<p>ok</p>"
        vals.update(extra)
        return self.env["slide.slide"].create(vals)

    def test_campus_completed_appears_and_skips_not_started(self):
        channel = self._create_channel("Canal Activity")
        done_slide = self._create_slide(channel, "Hecho")
        self._create_slide(channel, "Sin empezar")
        self.env["slide.channel.partner"].create({
            "channel_id": channel.id,
            "partner_id": self.partner.id,
        })
        self.env["slide.slide.partner"].create({
            "slide_id": done_slide.id,
            "partner_id": self.partner.id,
            "completed": True,
        })
        rows = self.student.with_user(self.faculty_user)._activity_event_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_type"], "campus")
        self.assertEqual(rows[0]["element_name"], "Hecho")
        self.assertEqual(rows[0]["detail"], "Completada")
        self.assertEqual(rows[0]["result"], "Completada")
        self.assertEqual(rows[0]["channel_name"], channel.name)
```

- [ ] **Step 2: Run — expect FAIL** (assembler still returns `[]`)

- [ ] **Step 3: Implement campus collection**

In `activity_assemble.py`:

```python
# -*- coding: utf-8 -*-
from odoo import _

ACTIVITY_LIMIT = 500
TYPE_LABELS = {"campus": "Campus", "evaluation": "Evaluación"}
CSV_HEADERS = [
    "Fecha", "Tipo", "Curso / canal", "Elemento", "Detalle", "Resultado", "Lote",
]


def _published_slide_domain(channel):
    domain = [("channel_id", "=", channel.id)]
    Slide = channel.env["slide.slide"]
    if "active" in Slide._fields:
        domain.append(("active", "=", True))
    if "is_category" in Slide._fields:
        domain.append(("is_category", "=", False))
    if "is_published" in Slide._fields:
        domain.append(("is_published", "=", True))
    return domain


def _batch_code_for_channel(env, partner, channel):
    PartnerChannel = env["slide.channel.partner"]
    domain = [
        ("partner_id", "=", partner.id),
        ("channel_id", "=", channel.id),
    ]
    if "active" in PartnerChannel._fields:
        domain.append(("active", "=", True))
    membership = PartnerChannel.search(domain, limit=1)
    if membership and "batch_id" in membership._fields and membership.batch_id:
        return membership.batch_id.code or ""
    return ""


def _campus_rows(env, partner):
    if not partner:
        return []
    SlidePartner = env["slide.slide.partner"]
    records = SlidePartner.search([("partner_id", "=", partner.id)])
    rows = []
    for sp in records:
        slide = sp.slide_id
        if not slide:
            continue
        if "is_category" in slide._fields and slide.is_category:
            continue
        if "is_published" in slide._fields and not slide.is_published:
            continue
        if "active" in slide._fields and not slide.active:
            continue
        channel = slide.channel_id
        completed = bool(sp.completed)
        detail = _("Completada") if completed else _("En curso")
        result = _("Completada") if completed else ""
        event_dt = sp.write_date or sp.create_date
        rows.append({
            "event_datetime": event_dt,
            "event_type": "campus",
            "channel_name": channel.name if channel else "",
            "element_name": slide.name or "",
            "detail": detail,
            "result": result,
            "batch_code": _batch_code_for_channel(env, partner, channel) if channel else "",
        })
    return rows


def assemble_student_activity_rows(env, student, limit=ACTIVITY_LIMIT):
    partner = student.partner_id
    if not partner:
        return []
    rows = _campus_rows(env, partner)
    rows.sort(
        key=lambda r: (r["event_datetime"] or "", r["element_name"] or ""),
        reverse=True,
    )
    return rows[:limit]
```

Call assembler under `sudo()` only from `op_student` after assert (Task 1 already asserts before call — update `_activity_event_rows`):

```python
    def _activity_event_rows(self):
        self.ensure_one()
        self._assert_can_view_activity()
        return assemble_student_activity_rows(
            self.sudo().env, self.sudo(), limit=ACTIVITY_LIMIT
        )
```

- [ ] **Step 4: Run — expect PASS** for campus test + Task 1

- [ ] **Step 5: Commit only if authorized**

---

### Task 3: Evaluation events + merge + limit

**Files:**
- Modify: `models/activity_assemble.py`
- Test: `tests/test_student_activity.py`

**Interfaces:**
- Consumes: `survey.user_input` with `slide_id`
- Produces: merged list sorted desc, capped at 500

- [ ] **Step 1: Write failing tests**

```python
    def test_evaluation_row_and_order_with_campus(self):
        channel = self._create_channel("Canal Eval")
        slide = self._create_slide(channel, "Quiz slide", slide_category="certification")
        self.env["slide.channel.partner"].create({
            "channel_id": channel.id,
            "partner_id": self.partner.id,
        })
        self.env["slide.slide.partner"].create({
            "slide_id": slide.id,
            "partner_id": self.partner.id,
            "completed": False,
        })
        survey = self.env["survey.survey"].create({"title": "Survey Activity"})
        Input = self.env["survey.user_input"]
        vals = {
            "survey_id": survey.id,
            "partner_id": self.partner.id,
            "state": "done",
        }
        if "slide_id" in Input._fields:
            vals["slide_id"] = slide.id
        attempt = Input.create(vals)
        if "end_datetime" in attempt._fields:
            attempt.write({"end_datetime": "2026-10-15 18:00:00"})
        # force campus older
        sp = self.env["slide.slide.partner"].search([
            ("slide_id", "=", slide.id),
            ("partner_id", "=", self.partner.id),
        ], limit=1)
        self.env.cr.execute(
            "UPDATE slide_slide_partner SET write_date = %s, create_date = %s WHERE id = %s",
            ("2026-10-01 10:00:00", "2026-10-01 10:00:00", sp.id),
        )
        rows = self.student.with_user(self.faculty_user)._activity_event_rows()
        self.assertGreaterEqual(len(rows), 2)
        self.assertEqual(rows[0]["event_type"], "evaluation")
        self.assertEqual(rows[0]["element_name"], slide.name)

    def test_activity_limit_500(self):
        channel = self._create_channel("Canal Limit")
        for i in range(505):
            slide = self._create_slide(channel, "S%s" % i)
            self.env["slide.slide.partner"].create({
                "slide_id": slide.id,
                "partner_id": self.partner.id,
                "completed": True,
            })
        rows = self.student.with_user(self.faculty_user)._activity_event_rows()
        self.assertEqual(len(rows), 500)
```

Note: if creating 505 slides is too slow in CI, reduce to a unit test of `assemble_student_activity_rows` with monkeypatched `_campus_rows` returning 505 fake dicts — prefer that if runtime suffers:

```python
    def test_activity_limit_500(self):
        from odoo.addons.irg_student_activity.models import activity_assemble as mod

        fake = [{
            "event_datetime": "2026-01-01 00:00:00",
            "event_type": "campus",
            "channel_name": "C",
            "element_name": "E%s" % i,
            "detail": "Completada",
            "result": "Completada",
            "batch_code": "",
        } for i in range(505)]
        original = mod._campus_rows
        mod._campus_rows = lambda env, partner: fake
        try:
            rows = mod.assemble_student_activity_rows(self.env, self.student, limit=500)
        finally:
            mod._campus_rows = original
        self.assertEqual(len(rows), 500)
```

- [ ] **Step 2: Run — expect FAIL** on evaluation/order

- [ ] **Step 3: Implement `_evaluation_rows` and merge**

```python
def _evaluation_rows(env, partner):
    if not partner:
        return []
    Input = env["survey.user_input"]
    if "slide_id" not in Input._fields:
        return []
    attempts = Input.search([
        ("partner_id", "=", partner.id),
        ("slide_id", "!=", False),
    ])
    rows = []
    for attempt in attempts:
        slide = attempt.slide_id
        channel = slide.channel_id if slide else False
        event_dt = False
        if "end_datetime" in attempt._fields and attempt.end_datetime:
            event_dt = attempt.end_datetime
        else:
            event_dt = attempt.create_date
        scoring = ""
        if "scoring_percentage" in attempt._fields and attempt.scoring_percentage is not False:
            scoring = "%s%%" % attempt.scoring_percentage
        if "scoring_success" in attempt._fields and attempt.scoring_success:
            scoring = (scoring + " " if scoring else "") + _("Éxito")
        rows.append({
            "event_datetime": event_dt,
            "event_type": "evaluation",
            "channel_name": channel.name if channel else "",
            "element_name": slide.name if slide else (attempt.survey_id.title or ""),
            "detail": attempt.state or "",
            "result": scoring,
            "batch_code": _batch_code_for_channel(env, partner, channel) if channel else "",
        })
    return rows


def assemble_student_activity_rows(env, student, limit=ACTIVITY_LIMIT):
    partner = student.partner_id
    if not partner:
        return []
    rows = _campus_rows(env, partner) + _evaluation_rows(env, partner)
    rows.sort(
        key=lambda r: (r["event_datetime"] or "", r.get("element_name") or ""),
        reverse=True,
    )
    return rows[:limit]
```

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit only if authorized**

---

### Task 4: Computed lines UI + export CSV action

**Files:**
- Modify: `models/op_student.py`, `views/op_student_views.xml`
- Create: `models/csv_export.py`
- Test: `tests/test_student_activity.py`

**Interfaces:**
- Produces: `build_activity_csv(rows) -> bytes`
- Produces: `OpStudent.action_export_activity_csv() -> act_url dict`
- Consumes: `assemble_student_activity_rows` / `_activity_event_rows`

- [ ] **Step 1: Write failing tests**

```python
    def test_compute_activity_line_ids_populated(self):
        channel = self._create_channel("Canal UI")
        slide = self._create_slide(channel, "UI slide")
        self.env["slide.slide.partner"].create({
            "slide_id": slide.id,
            "partner_id": self.partner.id,
            "completed": True,
        })
        student = self.student.with_user(self.faculty_user)
        student._compute_activity_line_ids()
        self.assertEqual(len(student.activity_line_ids), 1)
        self.assertEqual(student.activity_line_ids.element_name, "UI slide")

    def test_export_csv_headers_and_row(self):
        channel = self._create_channel("Canal CSV")
        slide = self._create_slide(channel, "CSV slide")
        self.env["slide.slide.partner"].create({
            "slide_id": slide.id,
            "partner_id": self.partner.id,
            "completed": True,
        })
        action = self.student.with_user(self.faculty_user).action_export_activity_csv()
        self.assertEqual(action["type"], "ir.actions.act_url")
        att_id = int(action["url"].split("/web/content/")[1].split("?")[0])
        att = self.env["ir.attachment"].browse(att_id)
        raw = att.raw or __import__("base64").b64decode(att.datas)
        text = raw.decode("utf-8-sig")
        self.assertTrue(text.startswith("Fecha,Tipo,"))
        self.assertIn("CSV slide", text)

    def test_export_denied_without_faculty(self):
        with self.assertRaises(AccessError):
            self.student.with_user(self.plain_user).action_export_activity_csv()
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement compute, CSV, view**

`csv_export.py`:

```python
# -*- coding: utf-8 -*-
import csv
import io

from .activity_assemble import CSV_HEADERS, TYPE_LABELS


def build_activity_csv(rows):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(CSV_HEADERS)
    for row in rows:
        writer.writerow([
            row.get("event_datetime") or "",
            TYPE_LABELS.get(row.get("event_type"), row.get("event_type") or ""),
            row.get("channel_name") or "",
            row.get("element_name") or "",
            row.get("detail") or "",
            row.get("result") or "",
            row.get("batch_code") or "",
        ])
    return output.getvalue().encode("utf-8-sig")
```

`op_student.py` additions:

```python
import base64
import re
from odoo import fields
from odoo.exceptions import UserError
from .csv_export import build_activity_csv


    @api.depends("partner_id")
    def _compute_activity_line_ids(self):
        for student in self:
            commands = [(5, 0, 0)]
            try:
                rows = student._activity_event_rows()
            except AccessError:
                student.activity_line_ids = commands
                continue
            for row in rows:
                commands.append((0, 0, {
                    "event_datetime": row["event_datetime"],
                    "event_type": row["event_type"],
                    "channel_name": row["channel_name"],
                    "element_name": row["element_name"],
                    "detail": row["detail"],
                    "result": row["result"],
                    "batch_code": row["batch_code"],
                }))
            student.activity_line_ids = commands

    def action_export_activity_csv(self):
        self.ensure_one()
        try:
            rows = self._activity_event_rows()
            payload = build_activity_csv(rows)
        except AccessError:
            raise
        except Exception as error:
            raise UserError(
                _("No se pudo generar el CSV de actividad: %s") % error
            ) from error
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", (self.name or "alumno").strip())[:40]
        filename = "actividad_%s_%s.csv" % (
            slug or "alumno",
            fields.Date.today().strftime("%Y%m%d"),
        )
        attachment = self.env["ir.attachment"].sudo().create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(payload),
            "mimetype": "text/csv",
            "res_model": self._name,
            "res_id": self.id,
            "public": False,
        })
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }
```

`views/op_student_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_op_student_form_activity" model="ir.ui.view">
        <field name="name">op.student.form.activity</field>
        <field name="model">op.student</field>
        <field name="inherit_id" ref="openeducat_core.view_op_student_form"/>
        <field name="arch" type="xml">
            <xpath expr="//page[@name='access']" position="after">
                <page name="activity" string="Actividad" groups="openeducat_core.group_op_faculty">
                    <group>
                        <button name="action_export_activity_csv"
                                type="object"
                                string="Exportar CSV"
                                class="btn-secondary"
                                groups="openeducat_core.group_op_faculty"/>
                    </group>
                    <field name="activity_line_ids" readonly="1" nolabel="1">
                        <tree create="0" delete="0" edit="0">
                            <field name="event_datetime" string="Fecha"/>
                            <field name="event_type" string="Tipo"/>
                            <field name="channel_name" string="Curso / canal"/>
                            <field name="element_name" string="Elemento"/>
                            <field name="detail" string="Detalle"/>
                            <field name="result" string="Resultado"/>
                            <field name="batch_code" string="Lote"/>
                        </tree>
                    </field>
                </page>
            </xpath>
        </field>
    </record>
</odoo>
```

- [ ] **Step 4: Run full tag — expect PASS**

- [ ] **Step 5: Commit only if authorized**

---

### Task 5: README + mission execution stub

**Files:**
- Create: `addons-extra/extrairg/irg_student_activity/README.md`
- Create/update: `missions/irg-student-activity/execution.md`

**Interfaces:** none

- [ ] **Step 1: Write README**

```markdown
# irg_student_activity

Pestaña **Actividad** en la ficha de alumno (`op.student`) para Facultad:
historial cronológico de contenidos de campus y evaluaciones, con export CSV.

## Uso

1. Abrir un alumno.
2. Pestaña **Actividad** (tras **Acceso**).
3. Revisar la tabla (máx. 500 eventos recientes).
4. **Exportar CSV** si hace falta.

## Permisos

Grupo `Facultad` (`openeducat_core.group_op_faculty`). La UI no basta: el
servidor comprueba el grupo en lectura y export.

## Fuera de alcance

Libreta, logins, Moodle, foros, import de listados. El Excel por lote sigue
en `irg_campus_activity_audit`.
```

- [ ] **Step 2: Append execution note** with test command and RED/GREEN outcomes when run

- [ ] **Step 3: No functional commit required** unless user asks to commit docs

---

## Spec coverage checklist

| Spec requirement | Task |
| --- | --- |
| Pestaña Actividad tras Acceso | 4 |
| Historial campus + evaluaciones ordenado | 2, 3 |
| No tocar Acceso | Global + no files there |
| Export CSV mismas columnas / 500 | 3, 4 |
| Facultad server-side + sudo lectura | 1, 4 |
| Sin tabla histórica persistente | TransientModel Task 1 |
| Excluir No iniciada | 2 |
| Vacío sin error | 1 |
| E2E TestSprite | Validación (fuera de coding tasks; gate validador) |
| Pruebas módulo | 1–4 |

## E2E (validation gate)

Tras Review + checks de módulo en verde, el validador dispara `e2e_testsprite` con:

- `projectPath`: `addons-extra/extrairg/irg_student_activity`
- Runtime: `docker-compose.local.yml` puerto `8069`, DB desechable
- Credenciales: usuario Facultad de la DB local (nunca cuentas reales)

---

## Self-review notes

- Sin TBD/TODO pendientes en pasos.
- Firmas alineadas: `assemble_student_activity_rows`, `_activity_event_rows`, `build_activity_csv`, `action_export_activity_csv`.
- Límite 500 cubierto en Task 3; denegación en Tasks 1 y 4.
