from odoo import http
import logging
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class CustomWebsiteSale(WebsiteSale):



    def _checkout_form_save(self, mode, checkout, all_values):

        partner_id = super(CustomWebsiteSale, self)._checkout_form_save(mode, checkout, all_values)
        order_id = request.website.sale_get_order()


        if partner_id:
            partner = request.env['res.partner'].sudo().browse(partner_id)
            order = request.env['sale.order'].sudo().browse(order_id.id)
            order_line = request.env['sale.order.line'].sudo().search([('order_id', '=', order.id)])
            list_product_comb = []
            for ol in order_line:
                list_product_comb.append(int(ol.product_id.combination_indices))
            attribute = request.env['product.template.attribute.value'].sudo().search([('id', 'in', list_product_comb)])

            max_plazo = max(attribute.mapped('plazo')) if attribute else 1


            birth_date = all_values.get('birth_date', '')
            university = all_values.get('university', '')
            profession = all_values.get('profession', '')
            titulacion = all_values.get('titulacion', '')
            finalizacionestudios = all_values.get('finalizacionestudios', '')

            partner.write({
                'birth_date': birth_date,
                'university': university,
                'profession': profession,
                'titulacion': titulacion,
                'finalizacionestudios': finalizacionestudios
                })

            order.write({
                'recurring_rule_count':max_plazo,
            }) 

            period = relativedelta(day=0)
            duration = order.recurrence_id.duration*order.recurring_rule_count
            unit = order.recurrence_id.unit
            if  unit == 'month':
                period=relativedelta(months=duration)
            elif unit == 'day':
                period=relativedelta(days=duration)
            elif unit == 'week':
                period=relativedelta(weeks=duration)
            elif unit == 'year':
                period=relativedelta(years=duration)
            end_date = order.start_date + period - relativedelta(days=1)

            order.write({
                'end_date':end_date
            })        

        return partner_id