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
        if a financed product has no financing line, recreate it from the
        difference between the financed variant and its contado sibling.
        Uses the same product lookup chain as _auto_scheduled_order.
        """
        financing_product = self.env.ref(
            'irg_sale_subscription_esp.product_financing_fees',
            raise_if_not_found=False,
        )
        if not financing_product:
            financing_product = self.env['product.product'].search(
                [('default_code', '=', 'GASTOS_FIN')], limit=1,
            )
        if not financing_product:
            candidate = self.env['product.product'].browse(108)
            financing_product = candidate if candidate.exists() else False
        if not financing_product:
            return

        for order in self:
            for line in order.order_line.filtered(
                lambda l: not l.display_type
                and l.irg_line_type not in ('financing', 'matricula', 'matricula_discount')
            ):
                plan_ptav = line.product_id.product_template_attribute_value_ids.filtered(
                    lambda x: x.attribute_id.name == 'Planes'
                )
                plan_ptav = plan_ptav[0] if plan_ptav else False

                is_financed_plan = bool(plan_ptav and 'contado' not in (plan_ptav.name or '').lower())
                is_multiterm_master = bool((order.term_number or 0) > 1 and line.irg_line_type == 'master')
                if not (is_financed_plan or is_multiterm_master):
                    continue

                existing_fin_line = order.order_line.filtered(
                    lambda l: l.irg_line_type == 'financing'
                    and l.irg_parent_line_id == line
                )
                if existing_fin_line:
                    continue

                # --- Calcular fee: misma lógica multi-nivel que _auto_scheduled_order ---
                # Nivel 1: buscar variante contado hermana
                other_attrs = line.product_id.product_template_attribute_value_ids.filtered(
                    lambda x: x.attribute_id.name != 'Planes'
                )
                contado_av = plan_ptav and plan_ptav.attribute_id.value_ids.filtered(
                    lambda x: 'contado' in x.name.lower()
                ) or False
                sibling_contado = False
                if contado_av:
                    domain = [
                        ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                        ('product_template_attribute_value_ids.product_attribute_value_id', 'in', contado_av.ids),
                    ]
                    for attr in other_attrs:
                        domain.append(('product_template_attribute_value_ids', 'in', attr.ids))
                    sibling_contado = self.env['product.product'].search(domain, limit=1)

                financing_fee_unit = 0.0
                if sibling_contado:
                    # Preferir pricelist si existe
                    raw_variant = line.price_unit or line.product_id.lst_price
                    raw_contado = sibling_contado.lst_price
                    if order.pricelist_id:
                        qty = line.product_uom_qty or 1.0
                        pv = order.pricelist_id._get_product_price(line.product_id, qty)
                        pc = order.pricelist_id._get_product_price(sibling_contado, qty)
                        if pv and pv > 0:
                            raw_variant = pv
                        if pc and pc > 0:
                            raw_contado = pc
                    financing_fee_unit = raw_variant - raw_contado

                # Fallback al price_extra del atributo
                if financing_fee_unit <= 0:
                    contado_ptav = line.product_id.product_tmpl_id.attribute_line_ids.filtered(
                        lambda l: plan_ptav and l.attribute_id.id == plan_ptav.attribute_id.id
                    ).product_template_value_ids.filtered(
                        lambda v: 'contado' in (v.name or '').lower()
                    )
                    contado_extra = contado_ptav[0].price_extra if contado_ptav else 0.0
                    plan_extra = (plan_ptav.price_extra or 0.0) if plan_ptav else 0.0
                    financing_fee_unit = plan_extra - contado_extra

                # Último fallback: variante financiada en lst_price vs línea actual (normalmente contado)
                if financing_fee_unit <= 0:
                    financing_fee_unit = (line.product_id.lst_price or 0.0) - (line.price_unit or 0.0)

                if financing_fee_unit <= 0:
                    continue

                if line.irg_line_type != 'master':
                    line.write({'irg_line_type': 'master'})

                self.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'product_id': financing_product.id,
                    'name': "Gastos de Financiación (%s) - %s" % ((plan_ptav and plan_ptav.name) or ('%s meses' % (order.term_number or 1)), line.product_id.name),
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
