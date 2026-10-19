from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.irg_admission_unimarconi_mail.models.op_admission import (
    irg_batch_code_is_official_master,
)


@tagged('post_install', '-at_install')
class TestUnimarconiMailVisibility(TransactionCase):

    def setUp(self):
        super().setUp()
        self.course = self.env['op.course'].create({
            'name': 'Máster en Neuropsicología Clínica',
            'code': 'T-UNI-MAIL',
            'lang': self.env.user.lang or 'en_US',
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


class TestUnimarconiMailAction(TestUnimarconiMailVisibility):

    def _admission(self, batch_code, email='maria@example.com'):
        admission = super()._admission(batch_code, email=email)
        # op.admission.email is related to partner_id.email and is not stored,
        # so the value passed to create() is discarded unless a partner holds it.
        if email and not (admission.email or '').strip():
            admission.partner_id = self.env['res.partner'].create({
                'name': admission.name or email,
                'email': email,
            })
        return admission

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
        if admission.partner_id:
            self.env.cr.execute(
                "UPDATE res_partner SET email = NULL WHERE id = %s",
                (admission.partner_id.id,),
            )
            admission.partner_id.invalidate_recordset(['email'])
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
