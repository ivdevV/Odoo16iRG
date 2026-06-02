# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWelcomeDiplomadoTemplateSelector(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ad = self.env['auto.admission.required'].search([], limit=1)
        if not self.ad:
            self.ad = self.env['auto.admission.required'].create({})
        self.ad.manual_wizard_enabled = True

        self.category_di = self.env['product.category'].create({
            'name': 'Diplomados Test',
            'code': 'DI',
        })
        self.category_regular = self.env['product.category'].create({
            'name': 'Regular Test',
            'code': 'MA',
        })
        self.product_di = self.env['product.template'].create({
            'name': 'Diplomado Test',
            'type': 'service',
            'categ_id': self.category_di.id,
        })
        self.product_regular = self.env['product.template'].create({
            'name': 'Regular Test',
            'type': 'service',
            'categ_id': self.category_regular.id,
        })
        self.course_di = self.env['op.course'].create({
            'name': 'Diplomado Course Test',
            'code': 'DCT',
            'product_template_id': self.product_di.id,
        })
        self.course_regular = self.env['op.course'].create({
            'name': 'Regular Course Test',
            'code': 'RCT',
            'product_template_id': self.product_regular.id,
        })
        self.product_fee = self.env['product.product'].create({
            'name': 'Diplomado Fee Test',
            'type': 'service',
        })
        self.register = self.env['op.admission.register'].create({
            'name': 'Diplomado Register Test',
            'course_id': self.course_regular.id,
            'product_id': self.product_fee.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'min_count': 1,
            'max_count': 100,
        })

    def _batch(self, code, course):
        return self.env['op.batch'].create({
            'name': code,
            'code': code,
            'course_id': course.id,
            'start_date': '2026-06-01',
            'end_date': '2026-12-31',
        })

    def _admission(self, batch, course):
        partner = self.env['res.partner'].create({
            'name': 'Student %s' % batch.code,
            'email': 'student-%s@example.com' % batch.code.lower(),
        })
        return self.env['op.admission'].create({
            'name': partner.name,
            'first_name': 'Student',
            'last_name': batch.code,
            'birth_date': '2000-01-01',
            'gender': 'o',
            'email': partner.email,
            'partner_id': partner.id,
            'batch_id': batch.id,
            'register_id': self.register.id,
            'course_id': course.id,
            'application_date': '2026-05-15',
            'email_send_ok': False,
        })

    def test_detects_diplomado_by_batch_code_prefix(self):
        admission = self._admission(self._batch('DIIA2606', self.course_regular), self.course_regular)

        self.assertTrue(admission._irg_is_diplomado_welcome())

    def test_detects_diplomado_by_category_code_prefix(self):
        admission = self._admission(self._batch('MAONL2602', self.course_di), self.course_di)

        self.assertTrue(admission._irg_is_diplomado_welcome())

    def test_resolves_configured_diplomado_template_before_fallback(self):
        template = self.env['mail.template'].create({
            'name': 'Diplomado Configured Test',
            'model_id': self.env['ir.model']._get_id('op.admission'),
            'subject': 'Diplomado',
            'body_html': '<p>Diplomado</p>',
        })
        self.ad.welcome_template_diplomado_id = template
        admission = self._admission(self._batch('DIIA2606', self.course_regular), self.course_regular)

        resolved, route = admission._irg_resolve_welcome_template(self.ad)

        self.assertEqual(route, 'diplomado')
        self.assertEqual(resolved, template)

    def test_resolves_created_diplomado_template_before_default(self):
        self.ad.welcome_template_diplomado_id = False
        copied = self.env.ref(
            'irg_welcome_diplomado_template_selector.email_op_admission_confirm_diplomado',
            raise_if_not_found=False,
        )
        admission = self._admission(self._batch('DIIA2606', self.course_regular), self.course_regular)

        resolved, route = admission._irg_resolve_welcome_template(self.ad)

        self.assertEqual(route, 'diplomado')
        if copied:
            self.assertEqual(resolved, copied)
        else:
            self.assertEqual(
                resolved,
                self.env.ref('isep_elearning_custom.email_op_admission_confirm', raise_if_not_found=False),
            )
