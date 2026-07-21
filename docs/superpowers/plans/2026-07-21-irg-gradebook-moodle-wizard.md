# Wizard «Sincronizar con Moodle» en la libreta de calificaciones — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Botón en la libreta de un alumno (`app.gradebook.student`) que abre un wizard con las notas encontradas en Moodle por asignatura (mapeo a nivel de actividad) y, al confirmar, escribe/actualiza líneas `app.gradebook.result` tipadas (quiz→exam, tarea→assignment) sin tocar los computes de `isep_gradebook`.

**Architecture:** Módulo puente nuevo `irg_gradebook_moodle_wizard` en `addons-extra/extrairg/`, dependiente de `isep_gradebook` + `irg_moodle_grades_sync`. Mapeo propio a nivel actividad (`irg.gradebook.moodle.map` + líneas) importado del Excel de n8n (hoja `MAP_ASIGNATURAS`). Servicio `GradebookMoodleService` que extiende `MoodleGradeService` para leer grade items individuales. Escritura por upsert con marca `is_moodle` en `app.gradebook.result`.

**Tech Stack:** Odoo 16, Python, Moodle WS REST (`gradereport_user_get_grade_items`, `core_enrol_get_enrolled_users`). Tests: `odoo.tests.TransactionCase` con el servicio mockeado (`unittest.mock.patch`). Entorno local: DB `test_irg_db` (Docker), `addons_uisep` y `extrairg` en addons path.

**Decisiones cerradas (del brainstorming):**
- Alcance: botón solo en la libreta de un alumno (no batch).
- Destino: líneas `app.gradebook.result`; quiz→`survey_type='exam'`, tarea→`survey_type='assignment'`. Una línea por asignatura×tipo con la media de sus actividades con nota.
- Mapeo: tabla propia a nivel actividad, importada una vez del Excel `~/Downloads/Migracion_Notas.xlsx` (hoja `MAP_ASIGNATURAS`). La tabla `irg.moodle.subject.map` del cron NO se toca.
- Conversión de escala: por actividad, `graderaw / grademax * grading_scale` de la libreta; luego media.
- Nota editable en el wizard antes de aplicar.
- Upsert key: (`gradebook_subject_id`, `is_moodle=True`, `survey_type`) → re-sincronizar actualiza, nunca duplica.
- Matching alumno (libreta→Moodle): `res.partner.md_id` → email → nombre normalizado (`irg_moodle_grades_sync.models.utils.normalize_name`).

**⚠️ Verificación previa obligatoria (Task 6, paso 1):** los IDs de `Moodle IDs List` del Excel pueden ser `id` de grade item o `cmid`. El filtro acepta match por cualquiera de los dos (`item['id']` o `item['cmid']`); verificar contra una respuesta real del WS en el primer smoke test y anotar el resultado en `02-progress` o en el commit.

**Flujo git:** rama `feat/gradebook-moodle-wizard` creada desde `Dev_iRG` actualizada (NUNCA desde `main` — convención del repo). Commits frecuentes en español, formato `feat(gradebook): …`.

> **Estado de ejecución (2026-07-21):** la implementación, Review,
> validación automatizada y smoke UI han finalizado. Los snippets de este
> documento representan el diseño inicial; el código final incorpora el
> hardening exigido por TDD, Security Advisor y Review. La documentación
> operativa vigente está en el `README.md` del addon y el resultado del gate
> en `missions/irg-gradebook-moodle-wizard/verification.json`. Quedan
> pendientes únicamente el smoke contra un WS Moodle real, por ausencia de
> credenciales locales, y la publicación.

**Decisión posterior — opción 1:** se mantiene una sola línea agregada por
asignatura×tipo. Si el template efectivo tiene `qty != 1` o existe una línea
manual del mismo tipo, el wizard marca el caso como incompatible. No se
alteran los computes base de `isep_gradebook`.

---

## Estructura de ficheros

```
addons-extra/extrairg/irg_gradebook_moodle_wizard/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── moodle_map.py            # irg.gradebook.moodle.map + .line
│   ├── app_gradebook_result.py  # _inherit: campo is_moodle
│   ├── app_gradebook_student.py # _inherit: método que abre el wizard
│   └── gradebook_service.py     # GradebookMoodleService (extiende MoodleGradeService)
├── wizard/
│   ├── __init__.py
│   └── moodle_sync_wizard.py    # irg.gradebook.moodle.sync.wizard + .line
├── views/
│   ├── moodle_map_views.xml
│   ├── moodle_sync_wizard_views.xml
│   └── app_gradebook_student_views.xml   # botón en el header
├── security/
│   └── ir.model.access.csv
├── tools/
│   └── import_map_csv.py        # import one-off del CSV exportado del Excel
└── tests/
    ├── __init__.py
    └── test_moodle_sync_wizard.py
```

---

### Task 1: Scaffold del módulo

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_moodle_wizard/__manifest__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_wizard/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_wizard/models/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_wizard/wizard/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_wizard/tests/__init__.py`

- [x] **Step 1: Crear rama desde Dev_iRG**

```bash
git checkout Dev_iRG && git pull && git checkout -b feat/gradebook-moodle-wizard
```

- [x] **Step 2: Escribir manifest e inits**

`__manifest__.py`:
```python
{
    'name': 'iRG Gradebook Moodle Wizard',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Botón en la libreta de calificaciones para traer notas de Moodle vía wizard',
    'description': """
Sincronización puntual Moodle -> libreta de calificaciones (isep_gradebook)
===========================================================================
Botón «Sincronizar con Moodle» en la libreta de un alumno. Abre un wizard
que muestra, por asignatura, las actividades evaluativas encontradas en
Moodle (mapeo a nivel de actividad, importado del flujo n8n) y la nota que
se escribirá. Al confirmar, hace upsert de líneas app.gradebook.result
tipadas (quiz -> exam, tarea -> assignment) marcadas con is_moodle.
    """,
    'author': 'iRG',
    'depends': ['isep_gradebook', 'irg_moodle_grades_sync'],
    'data': [
        'security/ir.model.access.csv',
        'views/moodle_map_views.xml',
        'views/moodle_sync_wizard_views.xml',
        'views/app_gradebook_student_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
```

`__init__.py` (raíz):
```python
from . import models
from . import wizard
```

`models/__init__.py`:
```python
from . import moodle_map
from . import app_gradebook_result
from . import app_gradebook_student
from . import gradebook_service
```

`wizard/__init__.py`:
```python
from . import moodle_sync_wizard
```

`tests/__init__.py`:
```python
from . import test_moodle_sync_wizard
```

(Los ficheros referenciados aún no existen; se crean en las tasks siguientes. No instalar todavía.)

- [x] **Step 3: Commit**

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_wizard
git commit -m "feat(gradebook): scaffold del módulo irg_gradebook_moodle_wizard"
```

---

### Task 2: Modelo de mapeo a nivel actividad

**Files:**
- Create: `models/moodle_map.py`
- Create: `security/ir.model.access.csv`
- Create: `views/moodle_map_views.xml`

- [x] **Step 1: Escribir `models/moodle_map.py`**

```python
from odoo import models, fields


class IrgGradebookMoodleMap(models.Model):
    _name = 'irg.gradebook.moodle.map'
    _description = 'Mapeo asignatura Odoo -> actividades Moodle (libreta)'
    _order = 'op_subject_id'
    _rec_name = 'op_subject_id'

    op_subject_id = fields.Many2one(
        'op.subject', string='Asignatura Odoo', required=True, index=True,
        ondelete='cascade')
    moodle_course_id = fields.Integer(
        string='ID curso Moodle', required=True, index=True)
    moodle_course_name = fields.Char(string='Curso Moodle')
    line_ids = fields.One2many(
        'irg.gradebook.moodle.map.line', 'map_id', string='Actividades')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('subject_course_uniq', 'unique(op_subject_id, moodle_course_id)',
         'Ya existe un mapeo para esta asignatura y curso de Moodle.'),
    ]


class IrgGradebookMoodleMapLine(models.Model):
    _name = 'irg.gradebook.moodle.map.line'
    _description = 'Actividad Moodle mapeada a una asignatura'
    _order = 'map_id, moodle_activity_id'

    map_id = fields.Many2one(
        'irg.gradebook.moodle.map', required=True, ondelete='cascade')
    moodle_activity_id = fields.Integer(
        string='ID actividad Moodle', required=True, index=True)
    name = fields.Char(string='Nombre actividad')
    activity_type = fields.Selection(
        [('quiz', 'Quiz'), ('assign', 'Tarea')],
        string='Tipo', default='quiz', required=True)
```

- [x] **Step 2: Escribir `security/ir.model.access.csv`**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_irg_gradebook_moodle_map_user,irg.gradebook.moodle.map user,model_irg_gradebook_moodle_map,base.group_user,1,0,0,0
access_irg_gradebook_moodle_map_system,irg.gradebook.moodle.map admin,model_irg_gradebook_moodle_map,base.group_system,1,1,1,1
access_irg_gradebook_moodle_map_line_user,irg.gradebook.moodle.map.line user,model_irg_gradebook_moodle_map_line,base.group_user,1,0,0,0
access_irg_gradebook_moodle_map_line_system,irg.gradebook.moodle.map.line admin,model_irg_gradebook_moodle_map_line,base.group_system,1,1,1,1
access_irg_gradebook_moodle_sync_wizard,irg.gradebook.moodle.sync.wizard,model_irg_gradebook_moodle_sync_wizard,base.group_user,1,1,1,1
access_irg_gradebook_moodle_sync_wizard_line,irg.gradebook.moodle.sync.wizard.line,model_irg_gradebook_moodle_sync_wizard_line,base.group_user,1,1,1,1
```

(Las dos últimas filas referencian el wizard de la Task 5; el CSV se carga entero al instalar, cuando ya existirá.)

- [x] **Step 3: Escribir `views/moodle_map_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="irg_gradebook_moodle_map_tree" model="ir.ui.view">
        <field name="name">irg.gradebook.moodle.map.tree</field>
        <field name="model">irg.gradebook.moodle.map</field>
        <field name="arch" type="xml">
            <tree>
                <field name="op_subject_id"/>
                <field name="moodle_course_id"/>
                <field name="moodle_course_name"/>
            </tree>
        </field>
    </record>

    <record id="irg_gradebook_moodle_map_form" model="ir.ui.view">
        <field name="name">irg.gradebook.moodle.map.form</field>
        <field name="model">irg.gradebook.moodle.map</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="op_subject_id"/>
                        <field name="moodle_course_id"/>
                        <field name="moodle_course_name"/>
                        <field name="active" widget="boolean_toggle"/>
                    </group>
                    <field name="line_ids">
                        <tree editable="bottom">
                            <field name="moodle_activity_id"/>
                            <field name="name"/>
                            <field name="activity_type"/>
                        </tree>
                    </field>
                </sheet>
            </form>
        </field>
    </record>

    <record id="act_irg_gradebook_moodle_map" model="ir.actions.act_window">
        <field name="name">Mapeo Moodle libreta</field>
        <field name="res_model">irg.gradebook.moodle.map</field>
        <field name="view_mode">tree,form</field>
    </record>

    <menuitem id="menu_irg_gradebook_moodle_map"
        name="Mapeo Moodle libreta"
        parent="isep_gradebook.gradebook_menu_root"
        action="act_irg_gradebook_moodle_map" sequence="90"/>
</odoo>
```

**Nota:** verificar el xml_id real del menú raíz de `isep_gradebook` en `addons-extra/addons_uisep/isep_gradebook/views/menu.xml` antes de usar `isep_gradebook.gradebook_menu_root`; si difiere, usar el correcto.

- [x] **Step 4: Commit**

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_wizard
git commit -m "feat(gradebook): modelo de mapeo asignatura-actividades Moodle"
```

---

### Task 3: Campo `is_moodle` en `app.gradebook.result` y stub del botón

**Files:**
- Create: `models/app_gradebook_result.py`
- Create: `models/app_gradebook_student.py`

- [x] **Step 1: Escribir `models/app_gradebook_result.py`**

```python
from odoo import models, fields


class AppGradebookResult(models.Model):
    _inherit = 'app.gradebook.result'

    is_moodle = fields.Boolean(
        string='Origen Moodle', default=False, index=True,
        help='Línea creada/actualizada por el wizard de sincronización Moodle.')
```

- [x] **Step 2: Escribir `models/app_gradebook_student.py`**

```python
from odoo import models, _
from odoo.exceptions import UserError


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def action_open_moodle_sync_wizard(self):
        self.ensure_one()
        wizard = self.env['irg.gradebook.moodle.sync.wizard'].create({
            'gradebook_student_id': self.id,
        })
        wizard.action_load_moodle_data()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sincronizar con Moodle'),
            'res_model': 'irg.gradebook.moodle.sync.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
```

- [x] **Step 3: Commit**

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_wizard
git commit -m "feat(gradebook): is_moodle en resultados y acción de apertura del wizard"
```

---

### Task 4: Servicio de grade items

**Files:**
- Create: `models/gradebook_service.py`

- [x] **Step 1: Escribir `models/gradebook_service.py`**

```python
import logging

from odoo.addons.irg_moodle_grades_sync.models import constants
from odoo.addons.irg_moodle_grades_sync.models.grade_service import (
    MoodleGradeService,
)

_logger = logging.getLogger(__name__)


class GradebookMoodleService(MoodleGradeService):
    """Extiende el servicio de notas para exponer los grade items
    individuales de un curso (no solo el total itemtype=='course')."""

    def get_user_grade_items(self, moodle_course_id):
        """Devuelve (usergrades, emails) de un curso Moodle.

        usergrades: lista cruda de gradereport_user_get_grade_items
          [{'userid', 'userfullname', 'gradeitems': [{'id', 'cmid',
            'itemname', 'itemmodule', 'graderaw', 'grademax', ...}]}]
        emails: {moodle_user_id: email} del endpoint de matrícula.
        """
        payload, err = self._call(
            constants.MDL_GRADE_GET_ITEMS_FUNC,
            {'courseid': moodle_course_id})
        if err or not isinstance(payload, dict):
            return [], {}
        emails = self.get_enrolled_emails(moodle_course_id)
        return payload.get('usergrades', []), emails
```

**Nota:** `_call` y `get_enrolled_emails` son heredados de `MoodleGradeService` (un solo underscore → accesibles desde la subclase). Los atributos `__credentials` etc. tienen name-mangling pero no se necesitan directamente.

- [x] **Step 2: Commit**

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_wizard
git commit -m "feat(gradebook): servicio Moodle de grade items individuales"
```

---

### Task 5: Wizard — modelos y lógica

**Files:**
- Create: `wizard/moodle_sync_wizard.py`

- [x] **Step 1: Escribir el wizard completo**

```python
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons.odoo_moodle_connector.models import utils as connector_utils
from odoo.addons.irg_moodle_grades_sync.models import utils as sync_utils
from odoo.addons.irg_moodle_grades_sync.models.utils import parse_grade

from ..models.gradebook_service import GradebookMoodleService

_logger = logging.getLogger(__name__)

TYPE_BY_ACTIVITY = {'quiz': 'exam', 'assign': 'assignment'}


class IrgGradebookMoodleSyncWizard(models.TransientModel):
    _name = 'irg.gradebook.moodle.sync.wizard'
    _description = 'Wizard sincronización notas Moodle -> libreta'

    gradebook_student_id = fields.Many2one(
        'app.gradebook.student', string='Libreta', required=True)
    student_id = fields.Many2one(
        related='gradebook_student_id.student_id', string='Alumno')
    match_method = fields.Char(string='Emparejado por', readonly=True)
    line_ids = fields.One2many(
        'irg.gradebook.moodle.sync.wizard.line', 'wizard_id',
        string='Notas encontradas')

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------
    def _get_service(self):
        credentials = connector_utils.get_moodle_credentials(self.env)
        if not credentials:
            raise UserError(_(
                'No hay credenciales de Moodle configuradas. '
                'Configúralas en el módulo Odoo Moodle Connector.'))
        return GradebookMoodleService(credentials, self.env)

    @staticmethod
    def _find_student_entry(partner, student_name, usergrades, emails):
        """Localiza la fila del alumno de la libreta en usergrades.

        Cadena: md_id -> email -> nombre normalizado (única).
        Devuelve (entry|None, metodo|None).
        """
        md_id = getattr(partner, 'md_id', False)
        if md_id:
            for entry in usergrades:
                if entry.get('userid') == md_id:
                    return entry, 'md_id'
        email = (partner.email or '').strip().lower()
        if email:
            for entry in usergrades:
                if (emails.get(entry.get('userid'), '')
                        .strip().lower() == email):
                    return entry, 'email'
        target = sync_utils.normalize_name(student_name)
        if target:
            matches = [e for e in usergrades
                       if sync_utils.normalize_name(
                           e.get('userfullname')) == target]
            if len(matches) == 1:
                return matches[0], 'name'
        return None, None

    @staticmethod
    def _grades_by_type(entry, map_lines, grading_scale):
        """Agrega los grade items del alumno por tipo de actividad.

        Match del item contra la línea de mapeo por item['id'] o
        item['cmid'] (los IDs del Excel pueden ser cualquiera de los dos).
        Convierte cada nota a la escala de la libreta y promedia.
        Devuelve {'exam': {'avg': float|None, 'found': [str], 'graded': int},
                  'assignment': {...}}
        """
        wanted = {}
        for ml in map_lines:
            wanted[ml.moodle_activity_id] = TYPE_BY_ACTIVITY.get(
                ml.activity_type, 'exam')
        buckets = {'exam': [], 'assignment': []}
        found = {'exam': [], 'assignment': []}
        for item in entry.get('gradeitems', []):
            key = None
            if item.get('id') in wanted:
                key = item['id']
            elif item.get('cmid') in wanted:
                key = item['cmid']
            if key is None:
                continue
            rtype = wanted[key]
            found[rtype].append(item.get('itemname') or str(key))
            grade = parse_grade(item.get('graderaw'))
            if grade is None:
                continue
            grademax = item.get('grademax') or 0.0
            if grademax and grading_scale:
                grade = grade / grademax * grading_scale
            buckets[rtype].append(grade)
        out = {}
        for rtype in ('exam', 'assignment'):
            vals = buckets[rtype]
            out[rtype] = {
                'avg': (sum(vals) / len(vals)) if vals else None,
                'found': found[rtype],
                'graded': len(vals),
            }
        return out

    def action_load_moodle_data(self):
        self.ensure_one()
        self.line_ids.unlink()
        service = self._get_service()
        gb_student = self.gradebook_student_id
        scale = gb_student.gradebook_id.grading_scale or 10.0
        map_model = self.env['irg.gradebook.moodle.map']
        line_model = self.env['irg.gradebook.moodle.sync.wizard.line']
        result_model = self.env['app.gradebook.result']

        course_cache = {}   # moodle_course_id -> (usergrades, emails)
        methods = set()

        for gb_subject in gb_student.gradebook_subject_ids:
            subject = gb_subject.op_subject_id
            smap = map_model.search([
                ('op_subject_id', '=', subject.id),
                ('active', '=', True)], limit=1)
            base_vals = {
                'wizard_id': self.id,
                'gradebook_subject_id': gb_subject.id,
                'subject_id': subject.id,
            }
            if not smap or not smap.line_ids:
                line_model.create(dict(
                    base_vals, state='sin_mapeo', apply_line=False))
                continue
            if smap.moodle_course_id not in course_cache:
                course_cache[smap.moodle_course_id] = \
                    service.get_user_grade_items(smap.moodle_course_id)
            usergrades, emails = course_cache[smap.moodle_course_id]
            entry, method = self._find_student_entry(
                gb_student.partner_id, gb_student.student_id.name,
                usergrades, emails)
            if entry is None:
                line_model.create(dict(
                    base_vals, state='alumno_no_encontrado',
                    apply_line=False,
                    moodle_info=smap.moodle_course_name or ''))
                continue
            methods.add(method)
            per_type = self._grades_by_type(entry, smap.line_ids, scale)
            for rtype, data in per_type.items():
                if not data['found']:
                    continue  # la asignatura no tiene actividades de este tipo
                current = result_model.search([
                    ('gradebook_subject_id', '=', gb_subject.id),
                    ('is_moodle', '=', True),
                    ('survey_type', '=', rtype)], limit=1)
                if data['avg'] is None:
                    line_model.create(dict(
                        base_vals, state='sin_nota', apply_line=False,
                        survey_type=rtype,
                        moodle_info=' | '.join(data['found'])))
                    continue
                line_model.create(dict(
                    base_vals, state='ok', apply_line=True,
                    survey_type=rtype,
                    moodle_grade=round(data['avg'], 2),
                    grade_to_apply=round(data['avg'], 2),
                    current_grade=current.scoring_total if current else 0.0,
                    graded_count=data['graded'],
                    moodle_info=' | '.join(data['found'])))
        self.match_method = ', '.join(sorted(methods)) or False
        return True

    # ------------------------------------------------------------------
    # Aplicar
    # ------------------------------------------------------------------
    def action_apply(self):
        self.ensure_one()
        result_model = self.env['app.gradebook.result']
        applied = 0
        for line in self.line_ids.filtered(
                lambda l: l.apply_line and l.state == 'ok'):
            vals = {
                'scoring_total': line.grade_to_apply,
                'description': _('Moodle · media de %s actividades') %
                line.graded_count,
                'is_moodle': True,
                'survey_type': line.survey_type,
                'gradebook_subject_id': line.gradebook_subject_id.id,
            }
            existing = result_model.search([
                ('gradebook_subject_id', '=', line.gradebook_subject_id.id),
                ('is_moodle', '=', True),
                ('survey_type', '=', line.survey_type)], limit=1)
            if existing:
                existing.write(vals)
            else:
                result_model.create(vals)
            applied += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Notas Moodle aplicadas'),
                'message': _('%s líneas escritas en la libreta.') % applied,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }


class IrgGradebookMoodleSyncWizardLine(models.TransientModel):
    _name = 'irg.gradebook.moodle.sync.wizard.line'
    _description = 'Línea del wizard de sincronización Moodle'
    _order = 'subject_id, survey_type'

    wizard_id = fields.Many2one(
        'irg.gradebook.moodle.sync.wizard', required=True,
        ondelete='cascade')
    gradebook_subject_id = fields.Many2one(
        'app.gradebook.subject', string='Asignatura libreta')
    subject_id = fields.Many2one('op.subject', string='Asignatura')
    survey_type = fields.Selection(
        [('exam', 'Examen'), ('assignment', 'Asignación')],
        string='Tipo')
    moodle_info = fields.Text(string='Actividades Moodle')
    graded_count = fields.Integer(string='Con nota')
    moodle_grade = fields.Float(string='Nota Moodle (escala libreta)')
    grade_to_apply = fields.Float(string='Nota a aplicar')
    current_grade = fields.Float(string='Nota actual', readonly=True)
    state = fields.Selection([
        ('ok', 'Encontrada'),
        ('sin_mapeo', 'Sin mapeo'),
        ('sin_nota', 'Sin nota en Moodle'),
        ('alumno_no_encontrado', 'Alumno no encontrado'),
    ], string='Estado', default='ok')
    apply_line = fields.Boolean(string='Aplicar', default=True)
```

**Nota (riesgo conocido):** `app.gradebook.result.compute_name` es compute/store — verificar en el primer test que no falla al crear una línea sin `survey_user_input_id`/`channel_id` (línea Moodle no viene de survey). Si falla, extender `compute_name` vía `_inherit` en `models/app_gradebook_result.py` para que use `description` cuando `is_moodle=True`.

- [x] **Step 2: Commit**

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_wizard
git commit -m "feat(gradebook): wizard de sincronización de notas Moodle"
```

---

### Task 6: Vistas — wizard y botón en la libreta

**Files:**
- Create: `views/moodle_sync_wizard_views.xml`
- Create: `views/app_gradebook_student_views.xml`

- [x] **Step 1: Escribir `views/moodle_sync_wizard_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="irg_gradebook_moodle_sync_wizard_form" model="ir.ui.view">
        <field name="name">irg.gradebook.moodle.sync.wizard.form</field>
        <field name="model">irg.gradebook.moodle.sync.wizard</field>
        <field name="arch" type="xml">
            <form string="Sincronizar con Moodle">
                <group>
                    <field name="gradebook_student_id" readonly="1"/>
                    <field name="student_id" readonly="1"/>
                    <field name="match_method" readonly="1"/>
                </group>
                <field name="line_ids">
                    <tree editable="bottom" create="0" delete="0"
                          decoration-success="state == 'ok'"
                          decoration-muted="state in ('sin_mapeo', 'sin_nota')"
                          decoration-danger="state == 'alumno_no_encontrado'">
                        <field name="apply_line" widget="boolean_toggle"
                               attrs="{'readonly': [('state', '!=', 'ok')]}"/>
                        <field name="subject_id" readonly="1"/>
                        <field name="survey_type" readonly="1"/>
                        <field name="state" readonly="1"/>
                        <field name="graded_count" readonly="1"/>
                        <field name="moodle_grade" readonly="1"/>
                        <field name="current_grade" readonly="1"/>
                        <field name="grade_to_apply"
                               attrs="{'readonly': [('state', '!=', 'ok')]}"/>
                        <field name="moodle_info" readonly="1" optional="show"/>
                        <field name="gradebook_subject_id" invisible="1"/>
                    </tree>
                </field>
                <footer>
                    <button name="action_apply" string="Aplicar notas"
                            type="object" class="btn-primary"/>
                    <button name="action_load_moodle_data" string="Recargar"
                            type="object"/>
                    <button string="Cancelar" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
```

- [x] **Step 2: Escribir `views/app_gradebook_student_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="app_gradebook_student_form_moodle" model="ir.ui.view">
        <field name="name">app.gradebook.student.form.moodle</field>
        <field name="model">app.gradebook.student</field>
        <field name="inherit_id"
               ref="isep_gradebook.app_gradebook_student_form"/>
        <field name="arch" type="xml">
            <xpath expr="//header" position="inside">
                <button name="action_open_moodle_sync_wizard"
                        string="Sincronizar con Moodle" type="object"
                        class="btn-secondary"/>
            </xpath>
        </field>
    </record>
</odoo>
```

- [ ] **Step 3: Instalar el módulo en test_irg_db y smoke test**

**Estado de ejecución (2026-07-21): parcial.** La instalación, el upgrade y
el smoke UI end-to-end pasaron contra un Moodle local simulado. La verificación
contra un WS real quedó `skipped`: ninguna de las 101 bases locales contiene
credenciales Moodle, por lo que no pudo resolverse empíricamente `id` frente a
`cmid`. El addon acepta ambos espacios de IDs y rechaza colisiones.

```bash
# Contenedor local Docker con Odoo 16 (mismo entorno usado para irg_online_subject_opening)
docker exec odoo16irg_local odoo -d test_irg_db -i irg_gradebook_moodle_wizard --stop-after-init
```

Expected: instalación sin errores (sin tracebacks de vistas ni ACL). Después, en la UI: abrir una libreta → botón visible. **Verificar aquí la semántica de los IDs** (`id` vs `cmid`) contra una respuesta real del WS con un curso mapeado, y anotar el resultado.

- [x] **Step 4: Commit**

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_wizard
git commit -m "feat(gradebook): vistas del wizard y botón en la libreta"
```

---

### Task 7: Tests con servicio mockeado

**Files:**
- Create: `tests/test_moodle_sync_wizard.py`

- [x] **Step 1: Escribir los tests**

```python
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

SERVICE_PATH = ('odoo.addons.irg_gradebook_moodle_wizard.wizard.'
                'moodle_sync_wizard')


def _fake_usergrades(md_user_id=777):
    return [{
        'userid': md_user_id,
        'userfullname': 'Alumno De Prueba',
        'gradeitems': [
            {'id': 395, 'cmid': 4395, 'itemname': 'TEST 1.1',
             'itemmodule': 'quiz', 'graderaw': 8.0, 'grademax': 10.0},
            {'id': 397, 'cmid': 4397, 'itemname': 'TEST 1.2',
             'itemmodule': 'quiz', 'graderaw': 90.0, 'grademax': 100.0},
            {'id': 500, 'cmid': 4500, 'itemname': 'Tarea 1',
             'itemmodule': 'assign', 'graderaw': None, 'grademax': 10.0},
        ],
    }]


@tagged('post_install', '-at_install')
class TestMoodleSyncWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Datos mínimos: curso, asignatura, admisión, libreta.
        # Reutilizar el patrón de setup de
        # addons-extra/extrairg/irg_online_subject_opening/tests/
        # (creación de op.course/op.batch/op.student/op.admission).
        cls.course = cls.env['op.course'].create({
            'name': 'Curso Test Moodle', 'code': 'CTM'})
        cls.subject = cls.env['op.subject'].create({
            'name': 'Asignatura Test', 'code': 'AT01',
            'course_id': cls.course.id})
        cls.partner = cls.env['res.partner'].create({
            'name': 'Alumno De Prueba',
            'email': 'alumno.test@example.com'})
        # md_id: campo del connector en res.partner
        cls.partner.md_id = 777
        cls.student = cls.env['op.student'].create({
            'first_name': 'Alumno', 'last_name': 'De Prueba',
            'partner_id': cls.partner.id})
        cls.batch = cls.env['op.batch'].create({
            'name': 'Batch Test', 'code': 'BT01',
            'course_id': cls.course.id,
            'start_date': '2026-01-01', 'end_date': '2026-12-31'})
        cls.admission = cls.env['op.admission'].create({
            'name': 'Adm Test', 'student_id': cls.student.id,
            'course_id': cls.course.id, 'batch_id': cls.batch.id,
            'partner_id': cls.partner.id,
            'admission_date': '2026-01-01'})
        cls.gradebook = cls.env['app.gradebook'].create({
            'name': 'Plantilla Test', 'grading_scale': 10})
        cls.gb_student = cls.env['app.gradebook.student'].create({
            'admission_id': cls.admission.id})
        cls.gb_subject = cls.env['app.gradebook.subject'].create({
            'gradebook_student_id': cls.gb_student.id,
            'op_subject_id': cls.subject.id})
        cls.map = cls.env['irg.gradebook.moodle.map'].create({
            'op_subject_id': cls.subject.id,
            'moodle_course_id': 44,
            'line_ids': [
                (0, 0, {'moodle_activity_id': 395, 'activity_type': 'quiz'}),
                (0, 0, {'moodle_activity_id': 397, 'activity_type': 'quiz'}),
                (0, 0, {'moodle_activity_id': 500,
                        'activity_type': 'assign'}),
            ],
        })

    def _open_wizard(self, usergrades=None, emails=None):
        usergrades = usergrades if usergrades is not None \
            else _fake_usergrades()
        emails = emails or {777: 'alumno.test@example.com'}
        with patch(SERVICE_PATH + '.GradebookMoodleService') as MockSvc, \
                patch('odoo.addons.odoo_moodle_connector.models.utils.'
                      'get_moodle_credentials',
                      return_value={'access_token': 'x',
                                    'base_url': 'http://test'}):
            MockSvc.return_value.get_user_grade_items.return_value = (
                usergrades, emails)
            wizard = self.env['irg.gradebook.moodle.sync.wizard'].create({
                'gradebook_student_id': self.gb_student.id})
            wizard.action_load_moodle_data()
        return wizard

    def test_load_ok_exam_average_and_scale(self):
        """Dos quizzes con nota (8/10 y 90/100) -> media exam 8.5."""
        wizard = self._open_wizard()
        exam = wizard.line_ids.filtered(
            lambda l: l.survey_type == 'exam')
        self.assertEqual(len(exam), 1)
        self.assertEqual(exam.state, 'ok')
        self.assertAlmostEqual(exam.moodle_grade, 8.5, places=2)
        self.assertEqual(exam.graded_count, 2)
        self.assertEqual(wizard.match_method, 'md_id')

    def test_load_assign_without_grade(self):
        """La tarea mapeada sin graderaw -> línea sin_nota, no aplicable."""
        wizard = self._open_wizard()
        assign = wizard.line_ids.filtered(
            lambda l: l.survey_type == 'assignment')
        self.assertEqual(assign.state, 'sin_nota')
        self.assertFalse(assign.apply_line)

    def test_load_no_map(self):
        """Asignatura sin mapeo -> línea sin_mapeo."""
        self.map.active = False
        wizard = self._open_wizard()
        self.assertEqual(wizard.line_ids.state, 'sin_mapeo')

    def test_load_student_not_found(self):
        """Sin md_id, email ni nombre coincidente -> alumno_no_encontrado."""
        self.partner.md_id = False
        wizard = self._open_wizard(
            usergrades=[{'userid': 999, 'userfullname': 'Otra Persona',
                         'gradeitems': []}],
            emails={999: 'otra@example.com'})
        self.assertEqual(wizard.line_ids.state, 'alumno_no_encontrado')

    def test_match_by_cmid(self):
        """IDs del mapeo como cmid (no grade item id) también matchean."""
        self.map.line_ids.unlink()
        self.env['irg.gradebook.moodle.map.line'].create({
            'map_id': self.map.id, 'moodle_activity_id': 4395,
            'activity_type': 'quiz'})
        wizard = self._open_wizard()
        exam = wizard.line_ids.filtered(lambda l: l.survey_type == 'exam')
        self.assertEqual(exam.state, 'ok')
        self.assertAlmostEqual(exam.moodle_grade, 8.0, places=2)

    def test_apply_creates_and_upserts(self):
        """Aplicar crea la línea de resultado; re-aplicar la actualiza."""
        wizard = self._open_wizard()
        wizard.action_apply()
        result = self.env['app.gradebook.result'].search([
            ('gradebook_subject_id', '=', self.gb_subject.id),
            ('is_moodle', '=', True), ('survey_type', '=', 'exam')])
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.scoring_total, 8.5, places=2)
        # Segunda pasada con nota editada -> misma línea, valor nuevo.
        wizard2 = self._open_wizard()
        exam2 = wizard2.line_ids.filtered(
            lambda l: l.survey_type == 'exam')
        exam2.grade_to_apply = 9.0
        wizard2.action_apply()
        result2 = self.env['app.gradebook.result'].search([
            ('gradebook_subject_id', '=', self.gb_subject.id),
            ('is_moodle', '=', True), ('survey_type', '=', 'exam')])
        self.assertEqual(len(result2), 1)
        self.assertAlmostEqual(result2.scoring_total, 9.0, places=2)

    def test_apply_recomputes_subject_average(self):
        """Tras aplicar, el AVG de exámenes de la asignatura refleja la nota."""
        wizard = self._open_wizard()
        wizard.action_apply()
        self.gb_subject.invalidate_recordset()
        self.assertAlmostEqual(
            self.gb_subject.point_average_exam, 8.5, places=2)
```

**Notas para el implementador:**
- Los `create()` de `op.student`/`op.admission` pueden requerir más campos obligatorios según los módulos instalados (openeducat + overrides iRG). Copiar el setup que ya funciona en `addons-extra/extrairg/irg_online_subject_opening/tests/test_online_subject_opening.py` y ajustar.
- Si `res.partner.md_id` no es asignable directamente (compute/readonly), crear el partner con `md_id` en el `create()` o usar `sudo().write()`; ver definición en `odoo_moodle_connector/models/res_partner.py`.
- Si `compute_name` de `app.gradebook.result` peta con líneas sin survey (ver riesgo en Task 5), añadir el override en `models/app_gradebook_result.py` y test correspondiente.

- [x] **Step 2: Ejecutar los tests (deben fallar antes de instalar, pasar después)**

```bash
docker exec odoo16irg_local odoo -d test_irg_db \
  -u irg_gradebook_moodle_wizard --test-enable --stop-after-init \
  --log-level=test 2>&1 | grep -E "test_|FAIL|ERROR|OK"
```

Expected: `7 tests` ejecutados, `0 failed, 0 error(s)`.

- [x] **Step 3: Commit**

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_wizard
git commit -m "test(gradebook): suite del wizard de sincronización Moodle"
```

---

### Task 8: Import del mapeo desde el Excel de n8n

**Files:**
- Create: `tools/import_map_csv.py`

- [x] **Step 1: Exportar la hoja `MAP_ASIGNATURAS` a CSV**

Desde `~/Downloads/Migracion_Notas.xlsx`, exportar la hoja `MAP_ASIGNATURAS` como `map_asignaturas.csv` (UTF-8). Columnas relevantes: `Moodle Course ID`, `Odoo Subject ID`, `Odoo Subject Name`, `Curso Nombre`, `Moodle IDs List` (coma-separado), `Moodle Names Found` (separado por `|`).

Alternativa sin abrir Excel:
```bash
python3 -c "
import csv, openpyxl
wb = openpyxl.load_workbook('/Users/ivrogo/Downloads/Migracion_Notas.xlsx', read_only=True, data_only=True)
ws = wb['MAP_ASIGNATURAS']
with open('map_asignaturas.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    for row in ws.iter_rows(values_only=True):
        w.writerow(row)
"
```

- [x] **Step 2: Escribir `tools/import_map_csv.py`**

```python
"""Import one-off del mapeo n8n (hoja MAP_ASIGNATURAS) a
irg.gradebook.moodle.map.

Uso (dentro de odoo shell):
    docker exec -i odoo16irg_local odoo shell -d test_irg_db <<'EOF'
    exec(open('/mnt/extra-addons/extrairg/irg_gradebook_moodle_wizard/'
              'tools/import_map_csv.py').read())
    run_import(env, '/tmp/map_asignaturas.csv')
    env.cr.commit()
    EOF

Idempotente: upsert por (op_subject_id, moodle_course_id); las líneas de
actividad se regeneran en cada import.
"""
import csv


def run_import(env, csv_path):
    map_model = env['irg.gradebook.moodle.map']
    subject_model = env['op.subject']
    created = updated = skipped = 0
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                subject_id = int(float(row['Odoo Subject ID']))
                course_id = int(float(row['Moodle Course ID']))
            except (ValueError, TypeError, KeyError):
                skipped += 1
                continue
            subject = subject_model.browse(subject_id).exists()
            if not subject:
                print(f"SKIP: op.subject {subject_id} no existe "
                      f"({row.get('Odoo Subject Name')})")
                skipped += 1
                continue
            ids_raw = (row.get('Moodle IDs List') or '').strip()
            names_raw = (row.get('Moodle Names Found') or '').strip()
            if not ids_raw:
                skipped += 1
                continue
            act_ids = [int(x) for x in ids_raw.replace(' ', '').split(',')
                       if x.strip().isdigit()]
            names = [n.strip() for n in names_raw.split('|')]
            lines = []
            for i, act_id in enumerate(act_ids):
                lines.append((0, 0, {
                    'moodle_activity_id': act_id,
                    'name': names[i] if i < len(names) else '',
                    'activity_type': 'quiz',  # MAP_ASIGNATURAS: todo Quiz
                }))
            existing = map_model.with_context(active_test=False).search([
                ('op_subject_id', '=', subject_id),
                ('moodle_course_id', '=', course_id)], limit=1)
            vals = {
                'moodle_course_name': row.get('Curso Nombre') or '',
                'line_ids': [(5, 0, 0)] + lines,
            }
            if existing:
                existing.write(vals)
                updated += 1
            else:
                map_model.create(dict(
                    vals, op_subject_id=subject_id,
                    moodle_course_id=course_id))
                created += 1
    print(f'Import mapeo: {created} creados, {updated} actualizados, '
          f'{skipped} saltados.')
```

**Nota:** los `Odoo Subject ID` del Excel son IDs de la BD de producción. En `test_irg_db` pueden no coincidir — para probar en local, validar contra `Odoo Subject Code` (`PC01`…) como fallback o cargar solo un subconjunto a mano. El import definitivo se hace contra la BD real (vía el flujo de despliegue habitual, no directamente sobre la BD del servidor).

- [x] **Step 3: Ejecutar el import en local y verificar**

```bash
docker cp map_asignaturas.csv odoo16irg_local:/tmp/
# ejecutar el bloque de odoo shell del docstring
```

Expected: `Import mapeo: N creados, 0 actualizados, M saltados.` Revisar en la UI (menú Mapeo Moodle libreta) que las asignaturas y actividades aparecen.

- [x] **Step 4: Commit**

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_wizard
git commit -m "feat(gradebook): script de import del mapeo n8n a la tabla de mapeo"
```

---

### Task 9: Verificación end-to-end y PR

- [x] **Step 1: Update completo del módulo + tests**

```bash
docker exec odoo16irg_local odoo -d test_irg_db \
  -u irg_gradebook_moodle_wizard --test-enable --stop-after-init \
  --log-level=test 2>&1 | tail -20
```

Expected: 0 failed, 0 errors.

- [x] **Step 2: Prueba manual en UI**

Abrir libreta de un alumno con asignaturas mapeadas → «Sincronizar con Moodle» → verificar: líneas por asignatura×tipo, estados correctos, nota editable, «Aplicar notas» crea las líneas de resultado y el promedio de la asignatura cambia. Repetir sync → no duplica.

- [ ] **Step 3: Push y PR contra Dev_iRG**

```bash
git push -u origin feat/gradebook-moodle-wizard
gh pr create --base Dev_iRG --title "feat(gradebook): wizard de sincronización de notas Moodle en la libreta" \
  --body "Botón en app.gradebook.student que abre un wizard con las notas de Moodle (mapeo a nivel actividad importado de n8n) y hace upsert de líneas app.gradebook.result tipadas (is_moodle). Ver docs/superpowers/plans/2026-07-21-irg-gradebook-moodle-wizard.md"
```

El merge lo hace el usuario.

---

## Fuera de alcance (explícito)

- Sync masivo por curso/batch (posible v2 reutilizando el wizard).
- Mapeo HomeClass (`Mapeo HomeClass` / `MAPEO todos los cursos` del Excel): el modelo y el script lo soportan (mismo formato), pero el import inicial cubre solo `MAP_ASIGNATURAS` (ONLINE).
- Tocar `irg.moodle.subject.map` o el cron de `irg_moodle_grades_sync`.
- Actividades tipo tarea (`assign`): soportadas por el modelo y el wizard, pero el Excel actual solo mapea quizzes; no hay datos de tareas que importar hoy.
