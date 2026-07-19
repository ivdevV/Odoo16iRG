from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSubjectPrecedence(TransactionCase):
    """Tests de `OpSubject.can_be_taken` cubriendo el caso de asignaturas
    compartidas entre dos cursos (el bug de course_id único) y el
    comportamiento de precedencia/modalidad que debe seguir intacto.
    """

    def setUp(self):
        super().setUp()
        self.course_a = self.env['op.course'].create({
            'name': 'Subject Precedence Course A',
            'code': 'ISP-CA',
            'modality': 'manual',
        })
        self.course_b = self.env['op.course'].create({
            'name': 'Subject Precedence Course B',
            'code': 'ISP-CB',
            'modality': 'manual',
        })
        self.product = self.env['product.product'].create({
            'name': 'Subject Precedence Fee',
            'type': 'service',
        })
        self.register_a = self._create_register('A', self.course_a)
        self.register_b = self._create_register('B', self.course_b)

    def _create_register(self, code, course):
        return self.env['op.admission.register'].create({
            'name': 'Subject Precedence Register %s' % code,
            'course_id': course.id,
            'product_id': self.product.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
            'min_count': 1,
            'max_count': 30,
        })

    def _create_subject(self, code, parent_subject=None):
        vals = {'name': 'Subject %s' % code, 'code': code}
        if parent_subject:
            vals['parent_subject_id'] = parent_subject.id
        return self.env['op.subject'].create(vals)

    def _create_student_user(self, code):
        email = 'subject.precedence.%s@example.com' % code.lower()
        partner = self.env['res.partner'].create({
            'name': 'Subject Precedence Student %s' % code,
            'email': email,
        })
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Subject Precedence Student %s' % code,
            'login': email,
            'email': email,
            'partner_id': partner.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        student = self.env['op.student'].create({
            'first_name': 'Subject',
            'last_name': 'Precedence %s' % code,
            'name': 'Subject Precedence %s' % code,
            'gender': 'o',
            'birth_date': date(1990, 1, 1),
            'email': email,
            'user_id': user.id,
        })
        return partner, user, student

    def _create_admission(self, course, register, partner, student, state='done', modality='auto'):
        return self.env['op.admission'].create({
            'first_name': 'Subject',
            'last_name': 'Precedence',
            'name': 'Subject Precedence',
            'birth_date': date(1990, 1, 1),
            'gender': 'o',
            'email': partner.email,
            'register_id': register.id,
            'course_id': course.id,
            'partner_id': partner.id,
            'student_id': student.id,
            'state': state,
            'modality': modality,
        })

    # ------------------------------------------------------------------
    # Caso a: asignatura compartida, course_id "equivocado"
    # ------------------------------------------------------------------

    def test_shared_course_no_precedence_can_be_taken(self):
        subject = self._create_subject('ISP-SH1')
        self.course_a.write({'subject_ids': [(4, subject.id)]})
        self.course_b.write({'subject_ids': [(4, subject.id)]})
        # course_id queda apuntando al curso "equivocado" (A), aunque la
        # admisión done del alumno está en el curso B.
        subject.write({'course_id': self.course_a.id})

        partner, user, student = self._create_student_user('SH1')
        self._create_admission(self.course_b, self.register_b, partner, student)

        self.assertTrue(subject.can_be_taken(user.id))

    # ------------------------------------------------------------------
    # Caso b: precedencia no completada -> False
    # ------------------------------------------------------------------

    def test_precedence_not_completed_cannot_be_taken(self):
        parent = self._create_subject('ISP-P1')
        child = self._create_subject('ISP-C1', parent_subject=parent)
        self.course_a.write({'subject_ids': [(4, parent.id), (4, child.id)]})

        partner, user, student = self._create_student_user('P1')
        self._create_admission(self.course_a, self.register_a, partner, student)

        self.assertFalse(child.can_be_taken(user.id))

    # ------------------------------------------------------------------
    # Caso c: precedencia completada -> True
    # ------------------------------------------------------------------

    def test_precedence_completed_can_be_taken(self):
        parent = self._create_subject('ISP-P2')
        child = self._create_subject('ISP-C2', parent_subject=parent)
        self.course_a.write({'subject_ids': [(4, parent.id), (4, child.id)]})

        partner, user, student = self._create_student_user('P2')
        admission = self._create_admission(self.course_a, self.register_a, partner, student)

        channel = self.env['slide.channel'].create({'name': 'Subject Precedence Channel P2'})
        self.env['slide.channel.partner'].create({
            'channel_id': channel.id,
            'partner_id': partner.id,
            'op_subject_id': parent.id,
            'admission_id': admission.id,
            'completed': True,
        })

        self.assertTrue(child.can_be_taken(user.id))

    # ------------------------------------------------------------------
    # Caso d: sin admisión done en ningún curso de la asignatura -> False
    # ------------------------------------------------------------------

    def test_no_done_admission_for_any_course_of_subject_cannot_be_taken(self):
        subject = self._create_subject('ISP-D1')
        self.course_a.write({'subject_ids': [(4, subject.id)]})

        partner, user, student = self._create_student_user('D1')
        # Admisión done, pero en un curso (B) que NO contiene la asignatura.
        self._create_admission(self.course_b, self.register_b, partner, student)

        self.assertFalse(subject.can_be_taken(user.id))

    # ------------------------------------------------------------------
    # Caso e: modalidad manual con precedencia sin completar -> True
    # ------------------------------------------------------------------

    def test_manual_modality_with_uncompleted_precedence_can_be_taken(self):
        parent = self._create_subject('ISP-P3')
        child = self._create_subject('ISP-C3', parent_subject=parent)
        self.course_a.write({'subject_ids': [(4, parent.id), (4, child.id)]})

        partner, user, student = self._create_student_user('P3')
        self._create_admission(self.course_a, self.register_a, partner, student, modality='manual')

        self.assertTrue(child.can_be_taken(user.id))

    # ------------------------------------------------------------------
    # No-regresión: asignatura de un solo curso sin precedencia -> True
    # ------------------------------------------------------------------

    def test_single_course_no_precedence_can_be_taken(self):
        subject = self._create_subject('ISP-S1')
        self.course_a.write({'subject_ids': [(4, subject.id)]})

        partner, user, student = self._create_student_user('S1')
        self._create_admission(self.course_a, self.register_a, partner, student)

        self.assertTrue(subject.can_be_taken(user.id))
