from odoo import http
from odoo.http import request


class IrgBlockingStatusController(http.Controller):
    @http.route("/irg/blocking_process/status", type="json", auth="user")
    def blocking_process_status(self):
        return request.env["irg.blocking.process.service"].sudo().get_status()
