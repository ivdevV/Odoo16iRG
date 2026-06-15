# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestUrlSlide(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.channel = cls.env['slide.channel'].create({
            'name': 'URL Test Course',
            'channel_type': 'training',
        })

    def test_url_slide_type(self):
        slide = self.env['slide.slide'].create({
            'name': 'Live Class',
            'channel_id': self.channel.id,
            'slide_category': 'url',
            'irg_url': 'https://example.com/class',
        })

        self.assertEqual(slide.slide_type, 'url')
        self.assertIn('https://example.com/class', slide.embed_code)

    def test_url_slide_requires_http_url(self):
        with self.assertRaises(ValidationError):
            self.env['slide.slide'].create({
                'name': 'Invalid Class',
                'channel_id': self.channel.id,
                'slide_category': 'url',
                'irg_url': 'javascript:alert(1)',
            })
