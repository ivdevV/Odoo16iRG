# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCertificatesTileQwebGuard(TransactionCase):

    def _certificates_tile_t_if(self):
        view = self.env.ref('isep_website_custom.user_profile_content_details')
        arch = view.get_combined_arch()
        root = etree.fromstring(arch.encode() if isinstance(arch, str) else arch)
        nodes = root.xpath("//*[@name='certificates_and_diplomas']")
        self.assertEqual(
            len(nodes),
            1,
            'Expected a single certificates_and_diplomas tile in the combined profile template',
        )
        t_if = nodes[0].get('t-if')
        self.assertTrue(t_if, 'certificates_and_diplomas tile must have a t-if guard')
        return t_if

    def _render_guard(self, t_if, course):
        snippet = (
            '<t t-name="irg_campus_certificates_tile_qweb_fix.test_guard">'
            '<span t-if="%s">shown</span>'
            '</t>'
        ) % t_if
        test_view = self.env['ir.ui.view'].create({
            'name': 'irg_campus_certificates_tile_qweb_fix.test_guard',
            'type': 'qweb',
            'key': 'irg_campus_certificates_tile_qweb_fix.test_guard',
            'arch': snippet,
        })
        return self.env['ir.qweb']._render(test_view.id, {'course_id': course})

    def test_combined_t_if_does_not_use_hasattr(self):
        t_if = self._certificates_tile_t_if()
        self.assertNotIn('hasattr', t_if)
        self.assertIn('course_id.is_diplomado()', t_if)

    def test_master_tile_guard_renders_without_typeerror(self):
        t_if = self._certificates_tile_t_if()
        course = self.env['op.course'].create({
            'name': 'Master Tile Qweb Guard',
            'code': 'MTQG01',
            'lang': self.env.user.lang or 'en_US',
        })
        html = self._render_guard(t_if, course)
        self.assertIn('shown', html)

    def test_diplomado_tile_guard_hides_tile(self):
        t_if = self._certificates_tile_t_if()
        course = self.env['op.course'].create({
            'name': 'Diplomado Tile Qweb Guard',
            'code': 'DIQG01',
            'lang': self.env.user.lang or 'en_US',
        })
        html = self._render_guard(t_if, course)
        self.assertNotIn('shown', html)
