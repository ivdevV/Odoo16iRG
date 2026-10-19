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

