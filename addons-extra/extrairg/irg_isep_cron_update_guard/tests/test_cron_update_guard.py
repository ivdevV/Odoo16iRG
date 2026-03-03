from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCronUpdateGuard(TransactionCase):
    def test_module_operation_guard_returns_bool(self):
        tx = self.env["payment.transaction"]
        result = tx._irg_module_operation_in_progress()
        self.assertIn(result, (True, False))
