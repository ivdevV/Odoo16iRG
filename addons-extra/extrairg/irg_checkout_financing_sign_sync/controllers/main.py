# -*- coding: utf-8 -*-
import base64
import logging

from odoo import http
from odoo.http import request
from odoo.addons.irg_sale_subscription_esp.controllers.main import IrgWebsiteSale

_logger = logging.getLogger(__name__)


class IrgWebsiteSaleFinancingSync(IrgWebsiteSale):
    """Final controller layer to keep checkout totals/lines consistent."""

    def _irg_sync_checkout_order(self, recalculate=False):
        order = request.website.sale_get_order()
        if not order:
            return
        try:
            if recalculate:
                order.sudo()._auto_scheduled_order()
            order.sudo()._irg_ensure_financing_lines_consistent()
        except Exception as exc:
            _logger.exception("IRG checkout sync failed for order %s: %s", order.name, exc)

    @http.route(['/shop/extra_info'], type='http', methods=['GET', 'POST'], auth='public', website=True, sitemap=False)
    def extra_info(self, **post):
        self._irg_sync_checkout_order(recalculate=False)
        return super(IrgWebsiteSaleFinancingSync, self).extra_info(**post)

    @http.route(['/shop/payment'], type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, **post):
        self._irg_sync_checkout_order(recalculate=False)
        return super().shop_payment(**post)

    @http.route(['/shop/academic_documents/upload'], type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def upload_academic_documents(self, **post):
        """Upload academic documents after payment confirmation."""
        session_last_order_id = request.session.get('sale_last_order_id')
        posted_order_id = int(post.get('order_id', 0) or 0)

        if not session_last_order_id or posted_order_id != int(session_last_order_id):
            return request.redirect('/shop/confirmation?academic_upload=forbidden')

        order = request.env['sale.order'].sudo().browse(posted_order_id)
        if not order.exists():
            return request.redirect('/shop/confirmation?academic_upload=missing_order')

        uploads = request.httprequest.files.getlist('academic_documents')
        created = 0
        for upload in uploads:
            if not upload or not upload.filename:
                continue
            file_data = upload.read()
            if not file_data:
                continue
            request.env['ir.attachment'].sudo().create({
                'name': upload.filename,
                'type': 'binary',
                'datas': base64.b64encode(file_data),
                'res_model': 'sale.order',
                'res_id': order.id,
                'mimetype': upload.content_type or 'application/octet-stream',
                'description': 'Documentación académica subida desde ecommerce',
            })
            created += 1

        if created:
            order.message_post(body='Se han adjuntado %s documento(s) académicos desde la web.' % created)
            return request.redirect('/shop/confirmation?academic_upload=ok')
        return request.redirect('/shop/confirmation?academic_upload=empty')
