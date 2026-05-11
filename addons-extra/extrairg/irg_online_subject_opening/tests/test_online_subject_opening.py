from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOnlineSubjectOpening(TransactionCase):
    def setUp(self):
        super().setUp()
        self.subject_a = self.env['op.subject'].create({
            'name': 'Online Opening A',
            'code': 'IRG-OO-A',
        })
        self.subject_b = self.env['op.subject'].create({
            'name': 'Online Opening B',
            'code': 'IRG-OO-B',
        })
        self.subject_c = self.env['op.subject'].create({
            'name': 'Online Opening C',
            'code': 'IRG-OO-C',
        })
        self.course = self.env['op.course'].create({
            'name': 'Online Opening Course',
            'code': 'IRGOO',
            'subject_ids': [(6, 0, [self.subject_c.id, self.subject_a.id, self.subject_b.id])],
        })
        self.product = self.env['product.product'].create({
            'name': 'Online Opening Fee',
            'type': 'service',
        })
        self.register = self.env['op.admission.register'].create({
            'name': 'Online Opening Register',
            'course_id': self.course.id,
            'product_id': self.product.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
            'min_count': 1,
            'max_count': 30,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Online Opening Student',
            'email': 'online.opening@example.com',
        })

    def _create_batch(self, code):
        return self.env['op.batch'].create({
            'name': 'Online Opening %s' % code,
            'code': code,
            'course_id': self.course.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
        })

    def _create_admission(self, batch, admission_date=date(2026, 5, 7)):
        return self.env['op.admission'].create({
            'first_name': 'Online',
            'last_name': 'Opening',
            'name': 'Online Opening',
            'birth_date': date(1990, 1, 1),
            'gender': 'o',
            'email': 'online.opening@example.com',
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': batch.id,
            'admission_date': admission_date,
            'partner_id': self.partner.id,
            'state': 'done',
        })

    def test_onl_batch_generates_openings_ordered_by_subject_code(self):
        admission = self._create_admission(self._create_batch('MOPCONL'))

        openings = admission.irg_online_subject_opening_ids.sorted('sequence')

        self.assertEqual(openings.mapped('subject_code'), ['IRG-OO-A', 'IRG-OO-B', 'IRG-OO-C'])
        self.assertEqual(openings.mapped('opening_date'), [
            date(2026, 5, 7),
            date(2026, 6, 6),
            date(2026, 7, 6),
        ])
        self.assertEqual(openings.mapped('closing_date'), [
            date(2026, 6, 5),
            date(2026, 7, 5),
            date(2026, 8, 4),
        ])

    def test_monl_batch_is_excluded_even_when_it_contains_onl(self):
        admission = self._create_admission(self._create_batch('IRGMONL'))

        self.assertFalse(admission.irg_is_online_subject_opening)
        self.assertFalse(admission.irg_online_subject_opening_ids)

    def test_batch_without_onl_is_not_processed(self):
        admission = self._create_admission(self._create_batch('IRGPRES'))

        self.assertFalse(admission.irg_is_online_subject_opening)
        self.assertFalse(admission.irg_online_subject_opening_ids)

    def test_admission_date_change_regenerates_opening_dates(self):
        admission = self._create_admission(self._create_batch('MOPCONL'))

        admission.write({'admission_date': date(2026, 5, 10)})
        openings = admission.irg_online_subject_opening_ids.sorted('sequence')

        self.assertEqual(openings.mapped('opening_date'), [
            date(2026, 5, 10),
            date(2026, 6, 9),
            date(2026, 7, 9),
        ])

    def test_sync_without_slide_channels_keeps_schedule_and_does_not_create_memberships(self):
        admission = self._create_admission(self._create_batch('MOPCONL'))

        admission._irg_sync_online_channel_partners()

        memberships = self.env['slide.channel.partner'].search([('admission_id', '=', admission.id)])
        self.assertFalse(memberships)
        self.assertEqual(len(admission.irg_online_subject_opening_ids), 3)