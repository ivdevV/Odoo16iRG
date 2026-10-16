# IRG Admission Unimarconi Mail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir en la admisión de máster oficial un botón que abre el compositor con la plantilla de iRG cuyo botón lleva a la aplicación de oficialidad.

**Architecture:** Módulo nuevo `irg_admission_unimarconi_mail` que hereda `op.admission`. Un campo calculado muestra el botón cuando el código de lote empieza por `MO`. La acción abre `mail.compose.message` con una plantilla `noupdate`. El formulario cumplimentado no se guarda aquí: la app de oficialidad ya lo envía como `matricula-unimarconi`.

**Tech Stack:** Odoo 16, `mail.template`, `TransactionCase`, `docker-compose.local.yml`, TestSprite en la validación.

## Global Constraints

- Código funcional solo bajo `addons-extra/extrairg/irg_admission_unimarconi_mail/`.
- No modificar `irg_student_oficialidad_documents` ni `irg_student_oficialidad_webhook`.
- Versión `16.0.1.0.0`. Dependencias: `openeducat_admission`, `mail`. Sin modelos nuevos y sin `ir.model.access.csv`.
- Botón de ficha: `Enviar matrícula Unimarconi`. Visible en todos los estados si `(batch_id.code or '').strip().upper().startswith('MO')`.
- `MONL…` muestra el botón. `MP…`, `MB…`, `MIA…` y el lote vacío no.
- Sin correo, `UserError` pidiendo el correo de la admisión. Sin prefijo `MO`, `UserError` diciendo que el envío solo corresponde a lotes cuyo código empieza por `MO`.
- Compositor: `mail.compose.message`, `target=new`, `default_composition_mode=comment`, `default_model=op.admission`, `default_res_id` de esa admisión.
- Remitente: `Instituto Raimon Gaja <academica@institutoraimongaja.com>`. Destinatario: `email` de la admisión.
- Asunto: `¡Tu formulario de matrícula en Unimarconi!`.
- Saludo: `¡Hola, {first_name}!`, y si `first_name` está vacío, `name`.
- Si `course_id.name` tiene texto, la frase es `Para tu {curso} te facilitamos…`. Si no, `Para tu máster te facilitamos…`.
- Botón del correo: `Acceso a oficialidad` → `https://oficialidad.institutoraimongaja.com`. Misma URL en texto debajo.
- Callout `#0191c0`. Botón fondo `#4db4e7` y letra `#ffffff`.
- No usar `sudo()` para leer la admisión ni para enviar.
- Plantilla con `noupdate="1"`.
- Runtime de pruebas: `docker-compose.local.yml`. E2E TestSprite obligatorio porque hay vista XML; `projectPath` = directorio del módulo.
- Misión `full`, tier `complex`. Security Advisor no aplica.
- Commit, push y PR requieren autorización explícita del usuario. No ejecutar el checkpoint de commit solo porque este plan lo liste.

## Knowledge and References

- Spec: `docs/superpowers/specs/2026-10-15-irg-admission-unimarconi-mail-design.md`
- Misión: `missions/irg-admission-unimarconi-mail/plan.md`
- Formulario a heredar: `addons-extra/community-16/openeducat_admission/views/admission_view.xml` (`view_op_admission_form`)
- Modelo: `addons-extra/community-16/openeducat_admission/models/admission.py` (`mail.thread`, `email` y `birth_date` obligatorios, `gender` obligatorio, `batch_id` opcional en borrador)
- Lote: `op.batch.code` es `Char` de tamaño 16 y único
- Fixture de admisión de referencia: `addons-extra/extrairg/irg_admission_gender_fix/tests/test_gender_mapping.py`
- Logo: `ppt/media/image1.jpg` dentro de `/Users/ivrogo/Downloads/plantillas-seguimiento-irg.pptx`

## File map

| Path | Responsibility |
| --- | --- |
| `addons-extra/extrairg/irg_admission_unimarconi_mail/__manifest__.py` | Metadatos y data files |
| `addons-extra/extrairg/irg_admission_unimarconi_mail/__init__.py` | Importa `models` |
| `addons-extra/extrairg/irg_admission_unimarconi_mail/models/__init__.py` | Importa `op_admission` |
| `addons-extra/extrairg/irg_admission_unimarconi_mail/models/op_admission.py` | Prefijo, campo y acción |
| `addons-extra/extrairg/irg_admission_unimarconi_mail/views/op_admission_views.xml` | Botón en el header |
| `addons-extra/extrairg/irg_admission_unimarconi_mail/data/mail_template_data.xml` | Plantilla |
| `addons-extra/extrairg/irg_admission_unimarconi_mail/static/src/img/logo-irg.jpg` | Logo del correo |
| `addons-extra/extrairg/irg_admission_unimarconi_mail/tests/test_unimarconi_mail.py` | Prefijo, acción y cuerpo |
| `addons-extra/extrairg/irg_admission_unimarconi_mail/README.md` | Uso del módulo |

## Test command

Desde la raíz del repositorio, con el runtime local ya levantado:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf \
  -d test_irg_unimarconi_mail \
  -i irg_admission_unimarconi_mail \
  --test-enable \
  --test-tags=/irg_admission_unimarconi_mail \
  --stop-after-init \
  --http-port=8099 \
  --log-level=test
```

En una pasada posterior sobre la misma base, sustituir `-i` por `-u`. La base es desechable. El código de lote de cada test debe caber en 16 caracteres y ser único.

---

### Task 1: Visibility of official-master admissions

**Files:**
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/__init__.py`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/__manifest__.py`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/models/__init__.py`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/models/op_admission.py`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/tests/__init__.py`
- Test: `addons-extra/extrairg/irg_admission_unimarconi_mail/tests/test_unimarconi_mail.py`

**Interfaces:**
- Consumes: `op.admission`, `op.batch.code`, `op.course`, `op.admission.register`.
- Produces: `irg_batch_code_is_official_master(code) -> bool` and `op.admission.irg_show_unimarconi_mail` (Boolean, no almacenado).

- [ ] **Step 1: Write the failing test**

Create the module skeleton so Odoo can install it, with the compute still returning `False`. Then add the test.

`__init__.py`:

```python
from . import models
```

`models/__init__.py`:

```python
from . import op_admission
```

`__manifest__.py`:

```python
{
    'name': 'IRG Admission Unimarconi Mail',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Correo de matrícula Unimarconi en admisiones de máster oficial',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': ['openeducat_admission', 'mail'],
    'data': [],
    'installable': True,
    'application': False,
}
```

`models/op_admission.py` (skeleton, always hidden):

```python
from odoo import api, fields, models


def irg_batch_code_is_official_master(code):
    return False


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    irg_show_unimarconi_mail = fields.Boolean(
        compute='_compute_irg_show_unimarconi_mail',
        string='Mostrar correo Unimarconi',
    )

    @api.depends('batch_id', 'batch_id.code')
    def _compute_irg_show_unimarconi_mail(self):
        for admission in self:
            code = admission.batch_id.code if admission.batch_id else ''
            admission.irg_show_unimarconi_mail = (
                irg_batch_code_is_official_master(code)
            )
```

`tests/__init__.py`:

```python
from . import test_unimarconi_mail
```

`tests/test_unimarconi_mail.py`:

```python
from odoo.tests.common import TransactionCase

from odoo.addons.irg_admission_unimarconi_mail.models.op_admission import (
    irg_batch_code_is_official_master,
)


class TestUnimarconiMailVisibility(TransactionCase):

    def setUp(self):
        super().setUp()
        self.course = self.env['op.course'].create({
            'name': 'Máster en Neuropsicología Clínica',
            'code': 'T-UNI-MAIL',
        })
        product = self.env['product.product'].create({
            'name': 'Producto test Unimarconi',
            'type': 'service',
        })
        self.register = self.env['op.admission.register'].create({
            'name': 'Registro test Unimarconi',
            'course_id': self.course.id,
            'period': '2026-10',
            'start_date': '2026-10-01',
            'end_date': '2026-10-31',
            'min_count': 1,
            'max_count': 100,
            'product_id': product.id,
            'minimum_age_criteria': 3,
        })

    def _batch(self, code):
        return self.env['op.batch'].create({
            'name': code[:32],
            'code': code,
            'course_id': self.course.id,
            'start_date': '2026-10-01',
            'end_date': '2026-12-31',
        })

    def _admission(self, batch_code, email='maria@example.com'):
        batch = self._batch(batch_code) if batch_code else False
        return self.env['op.admission'].create({
            'name': 'María López',
            'first_name': 'María',
            'last_name': 'López',
            'gender': 'f',
            'birth_date': '1990-01-01',
            'email': email,
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': batch.id if batch else False,
        })

    def test_prefix_helper(self):
        self.assertTrue(irg_batch_code_is_official_master('MOPCONL2606'))
        self.assertTrue(irg_batch_code_is_official_master('  moabc'))
        self.assertTrue(irg_batch_code_is_official_master('MONLHC2601'))
        self.assertFalse(irg_batch_code_is_official_master('MPTEST01'))
        self.assertFalse(irg_batch_code_is_official_master('MBTEST01'))
        self.assertFalse(irg_batch_code_is_official_master('MIAMONL2601'))
        self.assertFalse(irg_batch_code_is_official_master(''))
        self.assertFalse(irg_batch_code_is_official_master(False))

    def test_button_flag_follows_batch_code(self):
        official = self._admission('MOPCONL2606')
        lowercase = self._admission('moabc2601')
        neurologopedia = self._admission('MONLHC2601')
        propio = self._admission('MPTEST01')
        bonificado = self._admission('MBTEST01')
        other = self._admission('MIAMONL2601')
        empty = self._admission(False)
        self.assertTrue(official.irg_show_unimarconi_mail)
        self.assertTrue(lowercase.irg_show_unimarconi_mail)
        self.assertTrue(neurologopedia.irg_show_unimarconi_mail)
        self.assertFalse(propio.irg_show_unimarconi_mail)
        self.assertFalse(bonificado.irg_show_unimarconi_mail)
        self.assertFalse(other.irg_show_unimarconi_mail)
        self.assertFalse(empty.irg_show_unimarconi_mail)
        self.assertEqual(official.state, 'draft')
        official.state = 'done'
        self.assertTrue(official.irg_show_unimarconi_mail)
```

- [ ] **Step 2: Run the test and confirm it fails**

Run the test command from the header.

Expected: FAIL. `test_prefix_helper` fails because `MOPCONL2606` returns `False`.

- [ ] **Step 3: Implement the prefix**

Replace `irg_batch_code_is_official_master` with:

```python
def irg_batch_code_is_official_master(code):
    return (code or '').strip().upper().startswith('MO')
```

- [ ] **Step 4: Run the test and confirm it passes**

Run the same command with `-u irg_admission_unimarconi_mail` instead of `-i`.

Expected: the two visibility tests PASS.

- [ ] **Step 5: Commit checkpoint**

No ejecutar `git commit` sin autorización explícita del usuario. Si la hay:

```bash
git add addons-extra/extrairg/irg_admission_unimarconi_mail
git commit -m "$(cat <<'EOF'
Add official-master detection for the Unimarconi admission mail.

EOF
)"
```

---

### Task 2: Mail template and rendered body

**Files:**
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/data/mail_template_data.xml`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/static/src/img/logo-irg.jpg`
- Modify: `addons-extra/extrairg/irg_admission_unimarconi_mail/__manifest__.py`
- Test: `addons-extra/extrairg/irg_admission_unimarconi_mail/tests/test_unimarconi_mail.py`

**Interfaces:**
- Consumes: `op.admission` fields `first_name`, `name`, `course_id.name`, `email`, and `get_base_url()`.
- Produces: XML id `irg_admission_unimarconi_mail.email_template_admission_unimarconi` on `mail.template`.

- [ ] **Step 1: Write the failing render test**

Append this class to `tests/test_unimarconi_mail.py`. It reuses `_admission` by inheriting the visibility test class.

```python
class TestUnimarconiMailTemplate(TestUnimarconiMailVisibility):

    def _body(self, admission):
        template = self.env.ref(
            'irg_admission_unimarconi_mail.email_template_admission_unimarconi'
        )
        return str(template._render_field('body_html', [admission.id])[admission.id])

    def test_rendered_body_uses_course_and_oficialidad_url(self):
        admission = self._admission('MOBODY01')
        body = self._body(admission)
        subject = self.env.ref(
            'irg_admission_unimarconi_mail.email_template_admission_unimarconi'
        )._render_field('subject', [admission.id])[admission.id]
        self.assertEqual(subject, '¡Tu formulario de matrícula en Unimarconi!')
        self.assertIn('¡Hola, María!', body)
        self.assertIn('Para tu Máster en Neuropsicología Clínica', body)
        self.assertIn('¡Estamos aquí para acompañarte!', body)
        self.assertIn('https://oficialidad.institutoraimongaja.com', body)
        self.assertIn('Acceso a oficialidad', body)
        self.assertIn('#0191c0', body)
        self.assertIn('#4db4e7', body)
        self.assertIn('academica@institutoraimongaja.com', body)
        self.assertIn('+34 623 55 17 40', body)
        template = self.env.ref(
            'irg_admission_unimarconi_mail.email_template_admission_unimarconi'
        )
        self.assertEqual(
            template.email_from,
            'Instituto Raimon Gaja <academica@institutoraimongaja.com>',
        )
        self.assertEqual(template.email_to, '{{ object.email }}')

    def test_rendered_body_without_course_name(self):
        admission = self._admission('MOBODY02')
        self.course.write({'name': '   '})
        body = self._body(admission)
        self.assertIn('Para tu máster te facilitamos', body)
```

- [ ] **Step 2: Run the test and confirm it fails**

Expected: FAIL with missing XML id `email_template_admission_unimarconi`.

- [ ] **Step 3: Add the logo and the template**

```bash
mkdir -p addons-extra/extrairg/irg_admission_unimarconi_mail/static/src/img
unzip -p "/Users/ivrogo/Downloads/plantillas-seguimiento-irg.pptx" ppt/media/image1.jpg \
  > addons-extra/extrairg/irg_admission_unimarconi_mail/static/src/img/logo-irg.jpg
```

`data/mail_template_data.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <record id="email_template_admission_unimarconi" model="mail.template">
            <field name="name">Admisión: matrícula Unimarconi</field>
            <field name="model_id" ref="openeducat_admission.model_op_admission"/>
            <field name="subject">¡Tu formulario de matrícula en Unimarconi!</field>
            <field name="email_from">Instituto Raimon Gaja &lt;academica@institutoraimongaja.com&gt;</field>
            <field name="email_to">{{ object.email }}</field>
            <field name="body_html" type="html">
                <div style="font-family: Arial, Helvetica, sans-serif; font-size: 15px; line-height: 1.55; color: #333333;">
                    <img t-att-src="object.get_base_url() + '/irg_admission_unimarconi_mail/static/src/img/logo-irg.jpg'"
                         alt="Instituto Raimon Gaja"
                         style="width: 168px; height: auto; margin-bottom: 16px;"/>
                    <p>¡Hola, <t t-out="object.first_name or object.name"/>!</p>
                    <p t-if="(object.course_id.name or '').strip()">
                        Para tu <strong t-out="(object.course_id.name or '').strip()"/> te facilitamos el formulario de inscripción de la Università degli Studi Guglielmo Marconi.
                    </p>
                    <p t-else="">
                        Para tu máster te facilitamos el formulario de inscripción de la Università degli Studi Guglielmo Marconi.
                    </p>
                    <p style="text-align: center; font-size: 18px; font-weight: 700; color: #0191c0;">
                        ¡Estamos aquí para acompañarte!
                    </p>
                    <p>
                        Entra en la aplicación de oficialidad, descarga el formulario, complétalo y fírmalo. Está en italiano. Al subirlo queda en tu expediente como la matrícula Unimarconi cumplimentada, junto con el resto de la documentación.
                    </p>
                    <p style="text-align: center; margin: 22px 0 16px;">
                        <a href="https://oficialidad.institutoraimongaja.com"
                           style="background-color: #4db4e7; color: #ffffff; padding: 12px 22px; text-decoration: none; font-size: 15px; font-weight: 700; border-radius: 6px; display: inline-block;">
                            Acceso a oficialidad
                        </a>
                    </p>
                    <p style="font-size: 14px; color: #4a4a4a;">
                        Si el botón no funciona, copia esta dirección en tu navegador:<br/>
                        oficialidad.institutoraimongaja.com
                    </p>
                    <p>Si tienes cualquier duda, puedes escribirnos:</p>
                    <p style="font-size: 14px; color: #4a4a4a;">
                        Departamento Académico: academica@institutoraimongaja.com<br/>
                        WhatsApp Departamento Académico: +34 623 55 17 40
                    </p>
                    <p style="text-align: center; font-size: 12px; color: #8a8a8a;">
                        © Instituto Raimon Gaja | Formación de calidad para profesionales de la salud
                    </p>
                </div>
            </field>
            <field name="auto_delete" eval="False"/>
        </record>
    </data>
</odoo>
```

Add the data file to `__manifest__.py`:

```python
'data': [
    'data/mail_template_data.xml',
],
```

- [ ] **Step 4: Run the render tests**

Expected: `test_rendered_body_uses_course_and_oficialidad_url` and `test_rendered_body_without_course_name` PASS.

- [ ] **Step 5: Commit checkpoint**

No ejecutar sin autorización del usuario.

```bash
git add addons-extra/extrairg/irg_admission_unimarconi_mail
git commit -m "$(cat <<'EOF'
Add the Unimarconi admission mail template.

EOF
)"
```

---

### Task 3: Composer action and form button

**Files:**
- Modify: `addons-extra/extrairg/irg_admission_unimarconi_mail/models/op_admission.py`
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/views/op_admission_views.xml`
- Modify: `addons-extra/extrairg/irg_admission_unimarconi_mail/__manifest__.py`
- Test: `addons-extra/extrairg/irg_admission_unimarconi_mail/tests/test_unimarconi_mail.py`

**Interfaces:**
- Consumes: `irg_batch_code_is_official_master`, XML id `email_template_admission_unimarconi`, `mail.email_compose_message_wizard_form`.
- Produces: `op.admission.action_send_unimarconi_mail()` returning an `ir.actions.act_window` dict. View XML id `irg_admission_unimarconi_mail.view_op_admission_form_unimarconi_mail`.

- [ ] **Step 1: Write the failing action and view tests**

```python
from odoo.exceptions import UserError


class TestUnimarconiMailAction(TestUnimarconiMailVisibility):

    def test_non_official_batch_does_not_open_composer(self):
        admission = self._admission('MPBLOCK1')
        with self.assertRaises(UserError) as caught:
            admission.action_send_unimarconi_mail()
        self.assertIn('MO', str(caught.exception))

    def test_empty_email_does_not_open_composer(self):
        admission = self._admission('MOMAIL01')
        self.env.cr.execute(
            "UPDATE op_admission SET email = NULL WHERE id = %s",
            (admission.id,),
        )
        admission.invalidate_recordset(['email'])
        with self.assertRaises(UserError) as caught:
            admission.action_send_unimarconi_mail()
        self.assertIn('correo', str(caught.exception).lower())

    def test_official_admission_opens_composer(self):
        admission = self._admission('MOOPEN01')
        action = admission.action_send_unimarconi_mail()
        template = self.env.ref(
            'irg_admission_unimarconi_mail.email_template_admission_unimarconi'
        )
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'mail.compose.message')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['default_model'], 'op.admission')
        self.assertEqual(action['context']['default_res_id'], admission.id)
        self.assertEqual(action['context']['default_composition_mode'], 'comment')
        self.assertTrue(action['context']['default_use_template'])
        self.assertEqual(action['context']['default_template_id'], template.id)

    def test_send_posts_on_chatter_and_can_be_repeated(self):
        admission = self._admission('MOSEND01')
        template = self.env.ref(
            'irg_admission_unimarconi_mail.email_template_admission_unimarconi'
        )
        before = len(admission.message_ids)
        composer = self.env['mail.compose.message'].with_context(
            default_model='op.admission',
            default_res_id=admission.id,
            default_composition_mode='comment',
            default_template_id=template.id,
            default_use_template=True,
        ).create({
            'model': 'op.admission',
            'res_id': admission.id,
            'composition_mode': 'comment',
            'template_id': template.id,
        })
        composer._onchange_template_id_wrapper()
        composer.action_send_mail()
        self.assertGreater(len(admission.message_ids), before)
        again = admission.action_send_unimarconi_mail()
        self.assertEqual(again['res_model'], 'mail.compose.message')

    def test_missing_template_raises(self):
        admission = self._admission('MOTPL01')
        self.env.ref(
            'irg_admission_unimarconi_mail.email_template_admission_unimarconi'
        ).unlink()
        with self.assertRaises(UserError) as caught:
            admission.action_send_unimarconi_mail()
        self.assertIn('plantilla', str(caught.exception).lower())

    def test_form_view_adds_the_button(self):
        view = self.env.ref(
            'irg_admission_unimarconi_mail.view_op_admission_form_unimarconi_mail'
        )
        arch = view.arch
        self.assertIn('action_send_unimarconi_mail', arch)
        self.assertIn('Enviar matrícula Unimarconi', arch)
        self.assertIn('irg_show_unimarconi_mail', arch)
        self.assertEqual(view.inherit_id, self.env.ref(
            'openeducat_admission.view_op_admission_form'
        ))
```

- [ ] **Step 2: Run the tests and confirm they fail**

Expected: FAIL because `action_send_unimarconi_mail` does not exist and the view XML id is missing.

- [ ] **Step 3: Implement the action and the view**

Replace `models/op_admission.py` with this complete file. Keep the compute from Task 1 and add the action:

```python
from odoo import _, api, fields, models
from odoo.exceptions import UserError

TEMPLATE_XMLID = (
    'irg_admission_unimarconi_mail.email_template_admission_unimarconi'
)


def irg_batch_code_is_official_master(code):
    return (code or '').strip().upper().startswith('MO')


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    irg_show_unimarconi_mail = fields.Boolean(
        compute='_compute_irg_show_unimarconi_mail',
        string='Mostrar correo Unimarconi',
    )

    @api.depends('batch_id', 'batch_id.code')
    def _compute_irg_show_unimarconi_mail(self):
        for admission in self:
            code = admission.batch_id.code if admission.batch_id else ''
            admission.irg_show_unimarconi_mail = (
                irg_batch_code_is_official_master(code)
            )

    def action_send_unimarconi_mail(self):
        self.ensure_one()
        code = self.batch_id.code if self.batch_id else ''
        if not irg_batch_code_is_official_master(code):
            raise UserError(_(
                'El envío solo corresponde a lotes cuyo código empieza por MO.'
            ))
        if not (self.email or '').strip():
            raise UserError(_(
                'Indica el correo de la admisión antes de enviar la matrícula Unimarconi.'
            ))
        template = self.env.ref(TEMPLATE_XMLID, raise_if_not_found=False)
        if not template:
            raise UserError(_(
                'No está instalada la plantilla de matrícula Unimarconi.'
            ))
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        return {
            'name': _('Enviar matrícula Unimarconi'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': {
                'default_model': 'op.admission',
                'default_res_id': self.id,
                'default_use_template': True,
                'default_template_id': template.id,
                'default_composition_mode': 'comment',
                'force_email': True,
            },
        }
```

`views/op_admission_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_op_admission_form_unimarconi_mail" model="ir.ui.view">
        <field name="name">op.admission.form.unimarconi.mail</field>
        <field name="model">op.admission</field>
        <field name="inherit_id" ref="openeducat_admission.view_op_admission_form"/>
        <field name="arch" type="xml">
            <xpath expr="//header" position="inside">
                <field name="irg_show_unimarconi_mail" invisible="1"/>
                <button name="action_send_unimarconi_mail"
                        type="object"
                        string="Enviar matrícula Unimarconi"
                        attrs="{'invisible': [('irg_show_unimarconi_mail', '=', False)]}"/>
            </xpath>
        </field>
    </record>
</odoo>
```

Manifest `data`, in this order:

```python
'data': [
    'data/mail_template_data.xml',
    'views/op_admission_views.xml',
],
```

- [ ] **Step 4: Run the full module tests**

Expected: every test in `test_unimarconi_mail.py` PASS, including visibility, render, action and view. `0 failed, 0 error`.

- [ ] **Step 5: Commit checkpoint**

No ejecutar sin autorización del usuario.

```bash
git add addons-extra/extrairg/irg_admission_unimarconi_mail
git commit -m "$(cat <<'EOF'
Open the Unimarconi mail composer from official-master admissions.

EOF
)"
```

---

### Task 4: Module readme

**Files:**
- Create: `addons-extra/extrairg/irg_admission_unimarconi_mail/README.md`

**Interfaces:**
- Consumes: the finished module behavior.
- Produces: the usage note the documenter can extend after validation.

- [ ] **Step 1: Write the readme**

```markdown
# irg_admission_unimarconi_mail

Botón **Enviar matrícula Unimarconi** en la ficha de `op.admission`.

Aparece cuando el código del lote, sin espacios iniciales y en mayúsculas,
empieza por `MO`. Abre el compositor de Odoo con la plantilla
`Admisión: matrícula Unimarconi`. El botón del correo abre
https://oficialidad.institutoraimongaja.com.

El formulario cumplimentado no se guarda en este módulo. La aplicación de
oficialidad lo envía y `irg_student_oficialidad_webhook` lo archiva como
`matricula-unimarconi`.

## Dependencias

`openeducat_admission`, `mail`.

## Pruebas

    docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
      -c /etc/odoo/odoo.conf -d test_irg_unimarconi_mail \
      -u irg_admission_unimarconi_mail --test-enable \
      --test-tags=/irg_admission_unimarconi_mail --stop-after-init \
      --http-port=8099 --log-level=test
```

- [ ] **Step 2: Confirm the module tree**

```bash
find addons-extra/extrairg/irg_admission_unimarconi_mail -type f | sort
```

Expected paths: `__init__.py`, `__manifest__.py`, `README.md`, `models/__init__.py`, `models/op_admission.py`, `views/op_admission_views.xml`, `data/mail_template_data.xml`, `static/src/img/logo-irg.jpg`, `tests/__init__.py`, `tests/test_unimarconi_mail.py`.

No files outside this directory. `git diff --stat` does not list `irg_student_oficialidad_documents` nor `irg_student_oficialidad_webhook`.

- [ ] **Step 3: Commit checkpoint**

No ejecutar sin autorización del usuario.

---

### Task 5: Validation handoff

This task is for the validator and the E2E tester, after Review. It does not change production code.

- [ ] **Step 1: Repeat the module tests on a disposable database**

Use the test command from the header. Record the summary in `missions/irg-admission-unimarconi-mail/artifacts/`.

- [ ] **Step 2: Run TestSprite**

Follow `.claude/agents/e2e-tester.md`. `projectPath` is `addons-extra/extrairg/irg_admission_unimarconi_mail`. Runtime is `docker-compose.local.yml` on port `8069`, against a disposable database. Do not point TestSprite at beta or production.

The flow to exercise: open an admission whose batch code starts with `MO`, confirm **Enviar matrícula Unimarconi** is visible, open the composer, and confirm the body contains the oficialidad link. Open an admission whose batch code starts with `MP` and confirm the button is absent.

- [ ] **Step 3: Write `verification.json`**

`status` is `passed` only when the module tests pass and `e2e_testsprite` is `pass`. A view change cannot skip E2E.
