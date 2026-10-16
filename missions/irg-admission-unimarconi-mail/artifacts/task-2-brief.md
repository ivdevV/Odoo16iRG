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

