from odoo.tests.common import TransactionCase


class TestIrgOpCourseModality(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.modality_presencial = cls.env.ref(
            'irg_op_course_modality.modality_presencial'
        )
        cls.modality_homeclass = cls.env.ref(
            'irg_op_course_modality.modality_homeclass'
        )
        cls.modality_online = cls.env.ref(
            'irg_op_course_modality.modality_online'
        )

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------

    def test_seed_three_modalities_exist(self):
        """Los tres registros semilla deben existir con los códigos correctos."""
        self.assertEqual(self.modality_presencial.code, 'presencial')
        self.assertEqual(self.modality_homeclass.code, 'homeclass')
        self.assertEqual(self.modality_online.code, 'online')

    def test_seed_modalities_active(self):
        """Las modalidades semilla deben estar activas."""
        for m in (
            self.modality_presencial,
            self.modality_homeclass,
            self.modality_online,
        ):
            self.assertTrue(m.active, f'Modalidad {m.code} debería estar activa')

    # ------------------------------------------------------------------
    # Campo en op.course
    # ------------------------------------------------------------------

    def test_course_without_modality(self):
        """Un curso sin modalidades asignadas debe tener irg_modality_ids vacío."""
        course = self.env['op.course'].create({
            'name': 'Test Course Sin Modalidad',
            'code': 'TST-NOMOD',
            'evaluation_type': 'normal',
        })
        self.assertFalse(course.irg_modality_ids)

    def test_course_single_modality(self):
        """Se puede asignar una sola modalidad a un curso."""
        course = self.env['op.course'].create({
            'name': 'Test Course Presencial',
            'code': 'TST-PRES',
            'evaluation_type': 'normal',
            'irg_modality_ids': [(6, 0, [self.modality_presencial.id])],
        })
        self.assertEqual(len(course.irg_modality_ids), 1)
        self.assertEqual(course.irg_modality_ids.code, 'presencial')

    def test_course_multiple_modalities(self):
        """Se pueden asignar varias modalidades simultáneamente."""
        course = self.env['op.course'].create({
            'name': 'Test Course Multi Modalidad',
            'code': 'TST-MULTI',
            'evaluation_type': 'normal',
            'irg_modality_ids': [(6, 0, [
                self.modality_presencial.id,
                self.modality_homeclass.id,
                self.modality_online.id,
            ])],
        })
        self.assertEqual(len(course.irg_modality_ids), 3)
        codes = set(course.irg_modality_ids.mapped('code'))
        self.assertEqual(codes, {'presencial', 'homeclass', 'online'})

    def test_modality_persistence_after_write(self):
        """Las modalidades deben persistir tras un write posterior."""
        course = self.env['op.course'].create({
            'name': 'Test Course Write',
            'code': 'TST-WRITE',
            'evaluation_type': 'normal',
        })
        self.assertFalse(course.irg_modality_ids)
        course.write({
            'irg_modality_ids': [(4, self.modality_online.id)],
        })
        self.assertIn(self.modality_online, course.irg_modality_ids)

    def test_code_uniqueness_constraint(self):
        """No deben poderse crear dos modalidades con el mismo código."""
        from odoo.exceptions import UserError, IntegrityError
        with self.assertRaises((UserError, IntegrityError)):
            self.env['irg.course.modality'].create({
                'name': 'Duplicado Presencial',
                'code': 'presencial',
            })
