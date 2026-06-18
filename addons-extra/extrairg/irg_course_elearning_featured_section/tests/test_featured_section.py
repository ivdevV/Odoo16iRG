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
            'irg_featured_section_embed_code': '<iframe src="https://example.com/embed"></iframe>',
            'irg_featured_section_url': 'https://example.com/directo',
            'irg_featured_section_button_label': 'Abrir recurso',
        })

        values = self.channel.irg_get_featured_section_values()

        self.assertEqual(values['course'], self.course)
        self.assertEqual(values['title'], 'Bienvenida global')
        self.assertIn('Mensaje para todas las asignaturas', values['body'])
        self.assertIn('<iframe src="https://example.com/embed"></iframe>', values['embed_code'])
        self.assertEqual(values['url'], 'https://example.com/directo')
        self.assertEqual(values['button_label'], 'Abrir recurso')

    def test_enabled_course_with_only_embed_code_returns_featured_values(self):
        self.course.write({
            'irg_featured_section_enabled': True,
            'irg_featured_section_title': False,
            'irg_featured_section_body': False,
            'irg_featured_section_embed_code': '<iframe src="https://example.com/embed-only"></iframe>',
        })

        values = self.channel.irg_get_featured_section_values()
        self.assertIn('embed-only', values['embed_code'])

    def test_enabled_course_without_content_returns_no_featured_values(self):
        self.course.write({
            'irg_featured_section_enabled': True,
            'irg_featured_section_title': False,
            'irg_featured_section_body': False,
            'irg_featured_section_embed_code': False,
        })

        self.assertEqual(self.channel.irg_get_featured_section_values(), {})

    def test_featured_course_resolved_for_clone_channel(self):
        if 'irg_homeclass_channel_id' in self.env['slide.channel']._fields:
            # Create a clone channel
            clone_channel = self.env['slide.channel'].create({
                'name': 'Clone Channel',
                'channel_type': 'training',
                'enroll': 'public',
                'irg_homeclass_channel_id': self.channel.id,
            })
            
            # Configure featured course on main channel
            self.course.write({
                'irg_featured_section_enabled': True,
                'irg_featured_section_title': 'Destacado para clone',
                'irg_featured_section_body': '<p>Cuerpo</p>',
            })
            
            # Get values as portal user
            portal_user = self.env['res.users'].create({
                'name': 'Portal User Test',
                'login': 'portal_user_test',
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
            })
            
            # Run the values function on the clone channel as the portal user
            values = clone_channel.with_env(self.env(user=portal_user)).irg_get_featured_section_values()
            self.assertEqual(values.get('title'), 'Destacado para clone')
