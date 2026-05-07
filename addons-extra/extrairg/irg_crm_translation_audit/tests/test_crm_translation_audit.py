# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestCrmTranslationAudit(TransactionCase):

    def test_action_refresh_generates_summary(self):
        lang = self.env['res.lang'].search([], limit=1)
        wizard = self.env['irg.crm.translation.audit.wizard'].create({
            'lang_id': lang.id,
        })
        result = wizard.action_refresh()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertTrue(wizard.result_html)
