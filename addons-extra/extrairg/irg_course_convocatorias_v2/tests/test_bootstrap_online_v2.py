from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_course_convocatorias_v2')
class TestBootstrapOnlineFromHomeClassV2(TransactionCase):
    """Verifica la rutina de bootstrap HomeClass -> Online del módulo
    irg_course_convocatorias_v2.

    Cubre los tres síntomas reportados antes del rediseño:
      * que las copias NO modifiquen los slides HomeClass originales,
      * que se respete la jerarquía (categorías, parent, secciones iRG),
      * que se copie todo el contenido HomeClass elegible.
    """

    def setUp(self):
        super().setUp()
        self.Channel = self.env['slide.channel']
        self.Slide = self.env['slide.slide']
        self.Section = self.env['irg.slide.section']

        self.channel = self.Channel.create({
            'name': 'Curso iRG bootstrap test V2',
            'channel_type': 'training',
        })

        self.product = self.env['product.product'].create({
            'name': 'Online Opening Fee Test V2',
            'type': 'service',
        })

        # Sección iRG con y sin slides asociados.
        self.section_with_slides = self.Section.create({
            'name': 'Sección con slides V2',
            'sequence': 10,
            'channel_id': self.channel.id,
        })
        self.section_empty = self.Section.create({
            'name': 'Sección vacía V2',
            'sequence': 20,
            'channel_id': self.channel.id,
        })

        # Categoría + 2 slides (uno con padre, otro sin) + 1 slide suelto.
        self.category = self.Slide.create({
            'name': 'Bloque 1 V2',
            'channel_id': self.channel.id,
            'is_category': True,
            'sequence': 10,
        })
        self.slide_in_cat = self.Slide.create({
            'name': 'Lección 1 V2',
            'channel_id': self.channel.id,
            'sequence': 20,
            'slide_category': 'article',
            'category_id': self.category.id,
            'irg_section_id': self.section_with_slides.id,
        })
        self.slide_child = self.Slide.create({
            'name': 'Lección 1.1 V2',
            'channel_id': self.channel.id,
            'sequence': 30,
            'slide_category': 'article',
            'parent_slide_id': self.slide_in_cat.id,
        })
        relation_updates = {}
        if 'prerequisite_slide_id' in self.slide_child._fields:
            relation_updates['prerequisite_slide_id'] = self.slide_in_cat.id
        if 'restriction_slide_ids' in self.slide_child._fields:
            relation_updates['restriction_slide_ids'] = [(6, 0, [self.slide_in_cat.id])]
        if relation_updates:
            self.slide_child.write(relation_updates)
        self.slide_loose = self.Slide.create({
            'name': 'Lección suelta V2',
            'channel_id': self.channel.id,
            'sequence': 40,
            'slide_category': 'article',
        })

        # Snapshot de HomeClass para comparar después del bootstrap.
        self._homeclass_ids = self.channel.slide_ids.ids
        self._homeclass_sequences = {s.id: s.sequence for s in self.channel.slide_ids}
        self._homeclass_section_ids = self.channel.irg_section_ids.ids

    def _homeclass_slides(self):
        return self.channel.slide_ids.filtered(
            lambda s: s.irg_content_modality in (False, 'homeclass')
        )

    def _online_slides(self):
        return self.channel.irg_online_channel_id.slide_ids

    def test_bootstrap_creates_independent_online_copies(self):
        result = self.channel.action_copy_homeclass_to_online()
        self.assertEqual(result['type'], 'ir.actions.client')

        online = self._online_slides()
        self.assertEqual(
            len(online), len(self._homeclass_ids),
            "Se debe copiar un slide Online por cada slide HomeClass elegible",
        )
        self.assertTrue(self.channel.irg_online_channel_id)
        self.assertEqual(
            self.channel.irg_online_channel_id.irg_homeclass_channel_id,
            self.channel,
            "El contenido Online debe vivir en un canal independiente enlazado al HomeClass",
        )

        # HomeClass intacto: mismos ids y mismas secuencias.
        homeclass = self._homeclass_slides()
        self.assertEqual(set(homeclass.ids), set(self._homeclass_ids))
        self.assertFalse(
            set(online.ids) & set(self.channel.slide_ids.ids),
            "Las copias Online no deben pertenecer al slide_ids del canal HomeClass",
        )
        for slide in homeclass:
            self.assertEqual(
                slide.sequence, self._homeclass_sequences[slide.id],
                "La secuencia de los slides HomeClass no debe cambiar",
            )
        self.assertEqual(
            online.sorted(lambda slide: (slide.sequence, slide.id)).mapped('name'),
            self.channel.slide_ids.sorted(lambda slide: (slide.sequence, slide.id)).mapped('name'),
            "El canal Online debe conservar el orden relativo de HomeClass",
        )

    def test_bootstrap_remaps_hierarchy_within_online(self):
        self.channel.action_copy_homeclass_to_online()
        online = self._online_slides()

        copy_of_category = online.filtered(lambda s: s.name == 'Bloque 1 V2' and s.is_category)
        copy_of_lesson = online.filtered(lambda s: s.name == 'Lección 1 V2')
        copy_of_child = online.filtered(lambda s: s.name == 'Lección 1.1 V2')
        self.assertEqual(len(copy_of_category), 1)
        self.assertEqual(len(copy_of_lesson), 1)
        self.assertEqual(len(copy_of_child), 1)
        self.assertEqual(
            copy_of_category.slide_category, 'article',
            "La sección Online debe conservar la categoría técnica de sección, no document",
        )
        self.assertEqual(
            copy_of_category.irg_content_modality, 'online',
            "La sección copiada debe quedar fuera del dominio HomeClass",
        )

        self.assertEqual(
            copy_of_lesson.category_id, copy_of_category,
            "La categoría de la copia debe apuntar a la copia de la categoría, no al original",
        )
        self.assertEqual(
            copy_of_child.parent_slide_id, copy_of_lesson,
            "El parent_slide_id debe remapearse a la copia online",
        )
        if 'prerequisite_slide_id' in copy_of_child._fields:
            self.assertEqual(
                copy_of_child.prerequisite_slide_id, copy_of_lesson,
                "El prerequisite_slide_id debe remapearse a la copia online",
            )
        if 'restriction_slide_ids' in copy_of_child._fields:
            self.assertEqual(
                copy_of_child.restriction_slide_ids, copy_of_lesson,
                "restriction_slide_ids debe remapearse a copias online",
            )
        self.assertNotIn(
            copy_of_lesson.id, self._homeclass_ids,
            "La lección copiada no debe ser el original",
        )

    def test_bootstrap_clones_all_irg_sections(self):
        self.channel.action_copy_homeclass_to_online()
        online_sections = self.env['irg.slide.section'].search([
            ('channel_id', '=', self.channel.irg_online_channel_id.id),
        ])
        # Todas las secciones del canal HomeClass se clonan al canal Online independiente.
        self.assertEqual(
            len(online_sections),
            len(self._homeclass_section_ids),
            "Se deben clonar todas las secciones iRG del canal, también las vacías",
        )

    def test_bootstrap_empty_when_no_homeclass(self):
        empty_channel = self.Channel.create({
            'name': 'Canal vacío V2',
            'channel_type': 'training',
        })
        result = empty_channel.action_copy_homeclass_to_online()
        self.assertEqual(result['params']['type'], 'warning')
        self.assertFalse(empty_channel.slide_ids)

    def test_bootstrap_does_not_duplicate_existing_online_content(self):
        self.channel.action_copy_homeclass_to_online()
        first_online = self._online_slides()
        result = self.channel.action_copy_homeclass_to_online()
        second_online = self._online_slides()
        self.assertEqual(
            second_online,
            first_online,
            "La segunda ejecución no debe duplicar contenido Online existente",
        )
        self.assertEqual(result['params']['type'], 'warning')

    def test_open_online_content_action_uses_online_channel(self):
        action = self.channel.action_open_online_channel()
        self.assertEqual(action['res_model'], 'slide.channel')
        self.assertEqual(action['res_id'], self.channel.irg_online_channel_id.id)
        self.assertEqual(action['view_mode'], 'form')
        self.assertTrue(self.channel.irg_online_channel_id.irg_is_online_clone)

    def test_original_slide_id_set_during_bootstrap(self):
        self.channel.action_copy_homeclass_to_online()
        online_slides = self._online_slides()
        for online_slide in online_slides:
            if not online_slide.is_category:
                original_slide = self.channel.slide_ids.filtered(
                    lambda s: s.name == online_slide.name and s.irg_content_modality in (False, 'homeclass')
                )
                self.assertEqual(online_slide.irg_original_slide_id, original_slide)

    def test_student_modality_detection(self):
        Course = self.env['op.course']
        Subject = self.env['op.subject']
        Batch = self.env['op.batch']
        Admission = self.env['op.admission']
        Partner = self.env['res.partner']

        course = Course.create({'name': 'Curso de Prueba', 'code': 'TEST-DETECTION'})
        Subject.create({
            'name': 'Asignatura de Prueba',
            'code': 'SUBJ-DETECTION',
            'course_id': course.id,
            'slide_channel_id': self.channel.id,
        })

        today = date.today()
        register = self.env['op.admission.register'].create({
            'name': 'Admission Register Detection',
            'course_id': course.id,
            'product_id': self.product.id,
            'start_date': today - timedelta(days=20),
            'end_date': today + timedelta(days=20),
            'min_count': 1,
            'max_count': 30,
            'state': 'admission',
        })

        # Partner A: Active Online Student (code has ONL)
        partner_a = Partner.create({'name': 'Student Online'})
        batch_online = Batch.create({
            'name': 'Batch Online',
            'code': 'ONL-2026',
            'course_id': course.id,
            'start_date': today - timedelta(days=10),
            'end_date': today + timedelta(days=10),
        })
        Admission.create({
            'name': 'Student Online',
            'first_name': 'Student',
            'last_name': 'Online',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'student.online@example.com',
            'state': 'confirm',
            'partner_id': partner_a.id,
            'batch_id': batch_online.id,
            'course_id': course.id,
            'register_id': register.id,
        })

        # Partner B: Active HomeClass Student (code has HC)
        partner_b = Partner.create({'name': 'Student HomeClass'})
        batch_homeclass = Batch.create({
            'name': 'Batch HC',
            'code': 'HC-2026',
            'course_id': course.id,
            'start_date': today - timedelta(days=10),
            'end_date': today + timedelta(days=10),
        })
        Admission.create({
            'name': 'Student HomeClass',
            'first_name': 'Student',
            'last_name': 'HomeClass',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'student.homeclass@example.com',
            'state': 'confirm',
            'partner_id': partner_b.id,
            'batch_id': batch_homeclass.id,
            'course_id': course.id,
            'register_id': register.id,
        })

        # Partner C: Expired Online Student
        partner_c = Partner.create({'name': 'Student Expired'})
        batch_expired = Batch.create({
            'name': 'Batch Expired',
            'code': 'ONL-2025',
            'course_id': course.id,
            'start_date': today - timedelta(days=20),
            'end_date': today - timedelta(days=5),
        })
        Admission.create({
            'name': 'Student Expired',
            'first_name': 'Student',
            'last_name': 'Expired',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'student.expired@example.com',
            'state': 'confirm',
            'partner_id': partner_c.id,
            'batch_id': batch_expired.id,
            'course_id': course.id,
            'register_id': register.id,
        })

        # Partner D: Batch code contains MONL (excluded)
        partner_d = Partner.create({'name': 'Student MONL'})
        batch_monl = Batch.create({
            'name': 'Batch MONL',
            'code': 'MONL-2026',
            'course_id': course.id,
            'start_date': today - timedelta(days=10),
            'end_date': today + timedelta(days=10),
        })
        Admission.create({
            'name': 'Student MONL',
            'first_name': 'Student',
            'last_name': 'MONL',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'student.monl@example.com',
            'state': 'confirm',
            'partner_id': partner_d.id,
            'batch_id': batch_monl.id,
            'course_id': course.id,
            'register_id': register.id,
        })

        # Verify modality detection
        self.assertTrue(self.channel._irg_is_partner_online_student_for_channel(partner_a))
        self.assertFalse(self.channel._irg_is_partner_online_student_for_channel(partner_b))
        self.assertFalse(self.channel._irg_is_partner_online_student_for_channel(partner_c))
        self.assertFalse(self.channel._irg_is_partner_online_student_for_channel(partner_d))

    def test_slide_channel_partner_synchronization(self):
        Course = self.env['op.course']
        Subject = self.env['op.subject']
        Batch = self.env['op.batch']
        Admission = self.env['op.admission']
        Partner = self.env['res.partner']

        course = Course.create({'name': 'Curso de Prueba', 'code': 'TEST-SYNC'})
        Subject.create({
            'name': 'Asignatura de Prueba',
            'code': 'SUBJ-SYNC',
            'course_id': course.id,
            'slide_channel_id': self.channel.id,
        })

        today = date.today()
        register = self.env['op.admission.register'].create({
            'name': 'Admission Register Sync',
            'course_id': course.id,
            'product_id': self.product.id,
            'start_date': today - timedelta(days=20),
            'end_date': today + timedelta(days=20),
            'min_count': 1,
            'max_count': 30,
            'state': 'admission',
        })

        # Online Student
        partner_online = Partner.create({'name': 'Student Online'})
        batch_online = Batch.create({
            'name': 'Batch Online',
            'code': 'ONL-2026',
            'course_id': course.id,
            'start_date': today - timedelta(days=10),
            'end_date': today + timedelta(days=10),
        })
        Admission.create({
            'name': 'Student Online Sync',
            'first_name': 'Student',
            'last_name': 'Online',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'student.onlinesync@example.com',
            'state': 'confirm',
            'partner_id': partner_online.id,
            'batch_id': batch_online.id,
            'course_id': course.id,
            'register_id': register.id,
        })

        # HomeClass Student
        partner_homeclass = Partner.create({'name': 'Student HomeClass'})
        batch_homeclass = Batch.create({
            'name': 'Batch HC',
            'code': 'HC-2026',
            'course_id': course.id,
            'start_date': today - timedelta(days=10),
            'end_date': today + timedelta(days=10),
        })
        Admission.create({
            'name': 'Student HomeClass Sync',
            'first_name': 'Student',
            'last_name': 'HomeClass',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'student.homeclasssync@example.com',
            'state': 'confirm',
            'partner_id': partner_homeclass.id,
            'batch_id': batch_homeclass.id,
            'course_id': course.id,
            'register_id': register.id,
        })

        # Bootstrap to create the online channel clone
        self.channel.action_copy_homeclass_to_online()
        online_channel = self.channel.irg_online_channel_id

        # 1. Create membership on HomeClass for Online student
        cp_online = self.env['slide.channel.partner'].create({
            'channel_id': self.channel.id,
            'partner_id': partner_online.id,
        })
        # Verify it synchronized to the online clone
        clone_cp_online = self.env['slide.channel.partner'].search([
            ('channel_id', '=', online_channel.id),
            ('partner_id', '=', partner_online.id),
        ])
        self.assertEqual(len(clone_cp_online), 1)

        # 2. Create membership on HomeClass for HomeClass student
        self.env['slide.channel.partner'].create({
            'channel_id': self.channel.id,
            'partner_id': partner_homeclass.id,
        })
        # Verify it did NOT synchronize to the online clone
        clone_cp_hc = self.env['slide.channel.partner'].search([
            ('channel_id', '=', online_channel.id),
            ('partner_id', '=', partner_homeclass.id),
        ])
        self.assertEqual(len(clone_cp_hc), 0)

        # 3. Update membership on HomeClass for Online student (mark as completed)
        cp_online.write({'completed': True})
        # Verify it updated in the online clone
        self.assertTrue(clone_cp_online.completed)

        # 4. Unlink membership on HomeClass for Online student
        cp_online.unlink()
        # Verify it was deleted in the online clone
        clone_cp_online_check = self.env['slide.channel.partner'].search([
            ('channel_id', '=', online_channel.id),
            ('partner_id', '=', partner_online.id),
        ])
        self.assertEqual(len(clone_cp_online_check), 0)

