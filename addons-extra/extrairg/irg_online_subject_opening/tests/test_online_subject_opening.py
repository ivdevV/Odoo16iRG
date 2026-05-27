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

    def _create_batch_no_subject_dates(self, code):
        """Crea lote ONL sin fechas en subject_to_batch_ids para probar lógica individual."""
        batch = self._create_batch(code)
        # isep_elearning_custom auto-crea subjects con fechas; las quitamos para
        # que _irg_is_online_subject_opening_batch() devuelva True (lógica individual).
        batch.subject_to_batch_ids.unlink()
        return batch

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

    # ------------------------------------------------------------------
    # Lógica individual (lote ONL sin fechas en asignaturas)
    # ------------------------------------------------------------------

    def test_onl_batch_generates_openings_ordered_by_subject_code(self):
        admission = self._create_admission(self._create_batch_no_subject_dates('MOPCONL'))

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

    def test_admission_date_change_regenerates_opening_dates(self):
        admission = self._create_admission(self._create_batch_no_subject_dates('MOPCONL'))

        admission.write({'admission_date': date(2026, 5, 10)})
        openings = admission.irg_online_subject_opening_ids.sorted('sequence')

        self.assertEqual(openings.mapped('opening_date'), [
            date(2026, 5, 10),
            date(2026, 6, 9),
            date(2026, 7, 9),
        ])

    def test_sync_without_slide_channels_keeps_schedule_and_does_not_create_memberships(self):
        admission = self._create_admission(self._create_batch_no_subject_dates('MOPCONL'))

        admission._irg_sync_online_channel_partners()

        memberships = self.env['slide.channel.partner'].search([('admission_id', '=', admission.id)])
        self.assertFalse(memberships)
        self.assertEqual(len(admission.irg_online_subject_opening_ids), 3)

    # ------------------------------------------------------------------
    # Lógica de lote (lote ONL con fechas en asignaturas — caso real)
    # ------------------------------------------------------------------

    def test_onl_batch_with_subject_dates_uses_batch_logic_not_individual_openings(self):
        """Lote ONL con fechas en subject_to_batch_ids (caso normal) no genera aperturas individuales."""
        # _create_batch auto-crea subject_to_batch_ids con fechas via _schedule_onl_subjects
        batch = self._create_batch('MOPCONL261')
        self.assertTrue(batch.subject_to_batch_ids.filtered(lambda s: s.date_from and s.date_to))

        admission = self._create_admission(batch)

        self.assertFalse(admission.irg_is_online_subject_opening)
        self.assertFalse(admission.irg_online_subject_opening_ids)

    # ------------------------------------------------------------------
    # Exclusiones
    # ------------------------------------------------------------------

    def test_monl_batch_is_excluded_even_when_it_contains_onl(self):
        admission = self._create_admission(self._create_batch('IRGMONL'))

        self.assertFalse(admission.irg_is_online_subject_opening)
        self.assertFalse(admission.irg_online_subject_opening_ids)

    def test_batch_without_onl_is_not_processed(self):
        admission = self._create_admission(self._create_batch('IRGPRES'))

        self.assertFalse(admission.irg_is_online_subject_opening)
        self.assertFalse(admission.irg_online_subject_opening_ids)

    def test_get_subjects_visible_for_batch_online(self):
        batch = self._create_batch_no_subject_dates('MOPCONL')
        # Set admission_date to today so that the first subject is visible today
        admission = self._create_admission(batch, admission_date=date.today())

        # Call the modified method
        visible_subjects = self.course.get_subjects_visible_for_batch(batch, admission)

        # The first subject 'IRG-OO-A' should be visible
        self.assertEqual(len(visible_subjects), 1)
        self.assertEqual(visible_subjects.code, 'IRG-OO-A')
