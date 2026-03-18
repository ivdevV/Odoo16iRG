# -*- coding: utf-8 -*-
import base64
import logging
from datetime import datetime

from odoo import http
from odoo.http import request
from odoo.addons.irg_sale_subscription_esp.controllers.main import IrgWebsiteSale

_logger = logging.getLogger(__name__)


class IrgWebsiteSaleFinancingSync(IrgWebsiteSale):
    """Final controller layer to keep checkout totals/lines consistent."""

    def _irg_parse_float(self, value):
        if not value:
            return 0.0
        normalized = str(value).replace('€', '').replace(' ', '').replace('.', '').replace(',', '.')
        try:
            return float(normalized)
        except Exception:
            return 0.0

    def _irg_parse_date(self, value):
        if not value:
            return False
        for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
            try:
                return datetime.strptime(value, fmt).date()
            except Exception:
                continue
        return False

    def _irg_save_address_extra_fields(self, order, post):
        if not order or not post:
            return

        partner = order.partner_id.sudo()
        partner_vals = {}

        vat = (post.get('vat') or '').strip()
        titulacion = (post.get('titulacion') or '').strip()
        university = (post.get('university') or '').strip()
        graduation_year = (post.get('graduation_year') or '').strip()
        profession = (post.get('profession') or '').strip()

        if vat:
            partner_vals['vat'] = vat
        if titulacion:
            if 'x_studio_titulacion' in partner._fields:
                partner_vals['x_studio_titulacion'] = titulacion
            if 'titulacion' in partner._fields:
                partner_vals['titulacion'] = titulacion
        if university:
            if 'x_studio_universidad' in partner._fields:
                partner_vals['x_studio_universidad'] = university
            if 'university' in partner._fields:
                partner_vals['university'] = university
        if graduation_year and 'x_studio_ano_de_graduacion' in partner._fields:
            partner_vals['x_studio_ano_de_graduacion'] = graduation_year
        if profession:
            if 'profession' in partner._fields:
                partner_vals['profession'] = profession
            if 'function' in partner._fields:
                partner_vals['function'] = profession

        if partner_vals:
            changed_vals = {}
            for field_name, new_value in partner_vals.items():
                current_value = partner[field_name]
                if str(current_value or '').strip() != str(new_value or '').strip():
                    changed_vals[field_name] = new_value

            if changed_vals:
                try:
                    partner.write(changed_vals)
                except Exception as exc:
                    # Do not block checkout progression if partner extra fields fail.
                    _logger.exception(
                        "IRG checkout: failed to write extra partner fields for order %s: %s",
                        order.name,
                        exc,
                    )

        # Client POST must NOT overwrite computed order-level academic/payment values.
        # Those values are server-computed (scheduled/order logic) and therefore
        # should not be modifiable from the checkout address form to avoid
        # tampering or accidental changes by the user.

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth='public', website=True, sitemap=False)
    def address(self, **kw):
        res = super(IrgWebsiteSaleFinancingSync, self).address(**kw)

        order = request.website.sale_get_order()
        if order and request.httprequest.method == 'POST':
            try:
                self._irg_save_address_extra_fields(order, kw)
            except Exception as exc:
                _logger.exception(
                    "IRG checkout: unexpected error in _irg_save_address_extra_fields for order %s: %s",
                    order.name,
                    exc,
                )
            self._irg_sync_checkout_order(recalculate=False)
        return res

    def _irg_sync_checkout_order(self, recalculate=False):
        order = request.website.sale_get_order()
        if not order:
            return
        try:
            recalc_marker = '_irg_auto_scheduled_order_done'
            ensure_marker = '_irg_financing_lines_sync_done'

            if recalculate:
                if getattr(request, recalc_marker, False):
                    recalculate = False
                else:
                    setattr(request, recalc_marker, True)

            if recalculate:
                order.sudo()._auto_scheduled_order()

            if getattr(request, ensure_marker, False):
                return
            order.sudo()._irg_ensure_financing_lines_consistent()
            setattr(request, ensure_marker, True)
        except Exception as exc:
            _logger.exception("IRG checkout sync failed for order %s: %s", order.name, exc)

    @http.route(['/shop/extra_info'], type='http', methods=['GET', 'POST'], auth='public', website=True, sitemap=False)
    def extra_info(self, **post):
        if request.httprequest.method == 'POST':
            self._irg_sync_checkout_order(recalculate=False)
        return super(IrgWebsiteSaleFinancingSync, self).extra_info(**post)

    @http.route(['/shop/payment'], type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, **post):
        self._irg_sync_checkout_order(recalculate=True)
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
