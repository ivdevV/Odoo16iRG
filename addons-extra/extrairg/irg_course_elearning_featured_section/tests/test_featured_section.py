# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_course_elearning_featured_section')
class TestCourseElearningFeaturedSection(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.channel = cls.env['slide.channel'].create({
            'name': 'Featured Subject Channel',
            'channel_type': 'training',
            'enroll': 'public',
        })
        cls.subject = cls.env['op.subject'].create({
            'name': 'Featured Subject',
            'code': 'FTR-SUBJ',
            'slide_channel_id': cls.channel.id,
        })
        cls.course = cls.env['op.course'].create({
            'name': 'Featured Course',
            'code': 'FTR-COURSE',
            'lang': cls.env.lang or 'en_US',
            'subject_ids': [(6, 0, [cls.subject.id])],
        })

    def test_disabled_course_returns_no_featured_values(self):
        self.assertFalse(self.channel.irg_get_featured_course())
        self.assertEqual(self.channel.irg_get_featured_section_values(), {})

    def test_featured_course_is_resolved_from_channel_subjects(self):
        self.course.write({
            'irg_featured_section_enabled': True,
            'irg_featured_section_title': 'Bienvenida global',
            'irg_featured_section_body': '<p>Mensaje para todas las asignaturas.</p>',
            'irg_featured_section_url': 'https://example.com/directo',
            'irg_featured_section_button_label': 'Abrir recurso',
        })

        values = self.channel.irg_get_featured_section_values()

        self.assertEqual(values['course'], self.course)
        self.assertEqual(values['title'], 'Bienvenida global')
        self.assertIn('Mensaje para todas las asignaturas', values['body'])
        self.assertEqual(values['url'], 'https://example.com/directo')
        self.assertEqual(values['button_label'], 'Abrir recurso')

    def test_enabled_course_without_content_returns_no_featured_values(self):
        self.course.write({
            'irg_featured_section_enabled': True,
            'irg_featured_section_title': False,
            'irg_featured_section_body': False,
        })

        self.assertEqual(self.channel.irg_get_featured_section_values(), {})
