# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    academic_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Documentación académica',
        compute='_compute_academic_attachment_ids',
        readonly=True,
    )
    academic_attachment_count = fields.Integer(
        string='Nº documentos académicos',
        compute='_compute_academic_attachment_ids',
        readonly=True,
    )

    @api.depends('message_attachment_count')
    def _compute_academic_attachment_ids(self):
        attachment_model = self.env['ir.attachment'].sudo()
        for order in self:
            attachments = attachment_model.search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id),
                ('description', 'ilike', 'Documentación académica subida desde ecommerce'),
            ], order='create_date desc')
            order.academic_attachment_ids = attachments
            order.academic_attachment_count = len(attachments)

    def _irg_ensure_financing_lines_consistent(self):
        """
        Safety fallback for checkout pages:
        if a financed product has no financing line, recreate it from Planes price_extra.
        """
        financing_product = self.env.ref('irg_sale_subscription_esp.product_financing_fees', raise_if_not_found=False)
        if not financing_product:
            return

        for order in self:
            for line in order.order_line.filtered(
                lambda l: not l.display_type and l.irg_line_type not in ('financing', 'matricula', 'matricula_discount') and l.product_id.recurring_invoice
            ):
                plan_ptav = line.product_id.product_template_attribute_value_ids.filtered(
                    lambda x: x.attribute_id.name == 'Planes'
                )
                if not plan_ptav:
                    continue
                plan_ptav = plan_ptav[0]
                if 'contado' in (plan_ptav.name or '').lower():
                    continue

                existing_fin_line = order.order_line.filtered(
                    lambda l: l.irg_line_type == 'financing' and l.irg_parent_line_id == line
                )
                if existing_fin_line:
                    continue

                contado_ptav = line.product_id.product_tmpl_id.attribute_line_ids.filtered(
                    lambda l: l.attribute_id.id == plan_ptav.attribute_id.id
                ).product_template_value_ids.filtered(
                    lambda v: 'contado' in (v.name or '').lower()
                )

                contado_extra = contado_ptav[0].price_extra if contado_ptav else 0.0
                financing_fee_unit = (plan_ptav.price_extra or 0.0) - contado_extra
                if financing_fee_unit <= 0:
                    continue

                if line.irg_line_type != 'master':
                    line.write({'irg_line_type': 'master'})

                self.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'product_id': financing_product.id,
                    'name': "Gastos de Financiación (%s) - %s" % (plan_ptav.name, line.product_id.name),
                    'product_uom_qty': line.product_uom_qty,
                    'price_unit': financing_fee_unit,
                    'tax_id': [(6, 0, financing_product.taxes_id.ids)],
                    'irg_line_type': 'financing',
                    'irg_parent_line_id': line.id,
                })

    def _process_custom_form(self, partner_id, form_data):
        """
        Completa la sincronización de campos web -> partner/sale.order
        para que el reporte de matrícula no quede con huecos.
        """
        res = super(SaleOrder, self)._process_custom_form(partner_id, form_data)
        if not form_data:
            return res

        data_dict = {}
        for row in form_data.split('\n'):
            if ' : ' in row:
                key, value = row.split(' : ', 1)
                data_dict[key.strip()] = value.strip()

        partner = partner_id if hasattr(partner_id, '_name') else self.env['res.partner'].browse(partner_id or self.partner_id.id)
        partner = partner.sudo()

        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, '%d/%m/%Y').date()
            except Exception:
                return False

        finalizacion = parse_date(data_dict.get('finalizacionestudios', ''))
        graduation_year = str(finalizacion.year) if finalizacion else False
        phone = data_dict.get('phone')
        profession = data_dict.get('profession')
        university = data_dict.get('university')
        titulacion = data_dict.get('titulacion')
        vat = data_dict.get('vat')

        partner_vals = {}
        if vat and 'vat' in partner._fields:
            partner_vals['vat'] = vat
        if phone:
            if 'phone' in partner._fields:
                partner_vals['phone'] = phone
            if 'mobile' in partner._fields:
                partner_vals['mobile'] = phone
        if profession:
            if 'profession' in partner._fields:
                partner_vals['profession'] = profession
            if 'function' in partner._fields:
                partner_vals['function'] = profession
        if university:
            if 'university' in partner._fields:
                partner_vals['university'] = university
            if 'x_studio_universidad' in partner._fields:
                partner_vals['x_studio_universidad'] = university
        if titulacion:
            if 'titulacion' in partner._fields:
                partner_vals['titulacion'] = titulacion
            if 'x_studio_titulacion' in partner._fields:
                partner_vals['x_studio_titulacion'] = titulacion
        if graduation_year and 'x_studio_ano_de_graduacion' in partner._fields:
            partner_vals['x_studio_ano_de_graduacion'] = graduation_year

        if partner_vals:
            partner.write(partner_vals)

        student = self.student_id.sudo() if self.student_id else False
        if student and student.id != partner.id:
            student_vals = {key: value for key, value in partner_vals.items() if key in student._fields}
            if student_vals:
                student.write(student_vals)

        return res
