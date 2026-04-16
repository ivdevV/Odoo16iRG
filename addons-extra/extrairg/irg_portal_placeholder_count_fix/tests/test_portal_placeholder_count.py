# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.http import request


@tagged('post_install', '-at_install')
class TestPortalPlaceholderCountFix(TransactionCase):
    def test_prepare_home_portal_values_adds_default_counters(self):
        from odoo.addons.irg_portal_placeholder_count_fix.controllers.portal import CustomerPortalPlaceholderCountFix

        old_env = getattr(request, 'env', None)
        request.env = self.env
        try:
            controller = CustomerPortalPlaceholderCountFix()
            values = controller._prepare_home_portal_values({})
            self.assertEqual(values.get('documents_quantity'), 0)
            self.assertEqual(values.get('documents_count'), 0)
            self.assertEqual(values.get('quotation_count'), 0)
            self.assertEqual(values.get('order_count'), 0)

            values = controller._prepare_home_portal_values(['documents_quantity', 'quotation_count'])
            self.assertEqual(values.get('documents_quantity'), 0)
            self.assertEqual(values.get('quotation_count'), 0)
        finally:
            if old_env is None:
                if hasattr(request, 'env'):
                    delattr(request, 'env')
            else:
                request.env = old_env
