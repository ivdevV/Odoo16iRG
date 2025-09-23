from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class AffiliateProductPricelistItemInherit(models.Model):
    _inherit= "affiliate.product.pricelist.item"

    compute_price = fields.Selection(selection_add=[('monthly', 'Comisión Mensual')])
    jh_fee_percent = fields.Float(string="Porcentaje de la Mensualidad",
                                  help="Porcentaje de la mensualidad para calculo de comisión")
    jh_monthly_commission = fields.Integer(string='Maximo de Meses con Comisión',
                                           help='Cantidad de meses de la comisión')
    jh_duration = fields.Integer(string='Tiempo de Suscripción')


class AffiliateCommisionInherit(models.Model):
    _inherit = "advance.commision"

    def calc_commision_adv(
            self,
            adv_comsn_id,
            product_templ_id,
            product_price,
            partner_vat=None,
            affiliate_id=None,
            quantity=1,
            acumuladas=None,  # <-- cambia el default
    ):
        product_tmpl = self.env['product.template'].browse(product_templ_id)
        categ_ids = product_tmpl.public_categ_ids

        pricelist_items = self.env['affiliate.product.pricelist.item'].search([
            ('advance_commision_id', '=', adv_comsn_id)
        ])

        for item in pricelist_items:
            compute = item.compute_price
            apply = item.applied_on

            match_producto = apply == "1_product" and item.product_tmpl_id.id == product_templ_id
            match_categoria = apply == "2_product_category" and item.categ_id in categ_ids
            match_global = apply == "3_global"

            if not (match_producto or match_categoria or match_global):
                continue

            if compute == "fixed":
                return item.fixed_price, item.fixed_price * quantity, "fixed"

            if compute == "percentage":
                val = product_price * (item.percent_price / 100)
                return item.percent_price, val, "percentage"

            if compute == "monthly":
                percent = item.jh_fee_percent / 100 if item.jh_fee_percent else 0.0
                max_meses = item.jh_monthly_commission or 0

                # 🔐 Recalcular acumuladas si no se pasa como argumento
                if acumuladas is None and partner_vat and affiliate_id:
                    visitas_ciclo = self.env['affiliate.visit'].search([
                        ('sales_order_line_id.product_id.product_tmpl_id', '=', product_templ_id),
                        ('sales_order_line_id.order_id.partner_id.vat', '=', partner_vat),
                        ('affiliate_partner_id', '=', affiliate_id),
                        ('state', '=', 'confirm'),
                        # Opcional: incluir lógica de ciclo si querés respetar duración
                    ])
                    acumuladas = sum(v.product_quantity or 0 for v in visitas_ciclo)

                disponibles = max(max_meses - acumuladas, 0)
                unidades_aplicables = min(disponibles, quantity)

                base_comm = product_price * percent

                if unidades_aplicables == 0:
                    raise UserError('El afiliado ya alcanzó el tope de comisiones')
                elif unidades_aplicables < quantity:
                    comision_valida = base_comm / quantity * unidades_aplicables
                else:
                    comision_valida = base_comm

                return percent * 100, comision_valida, "percentage"

        return 0.0, 0.0, "none"


class AffiliateVisitInherit(models.Model):
    _inherit = 'affiliate.visit'

    jh_type_compute = fields.Char(
        string='Método de Cálculo',
        store=True
    )

    jh_quantity_commission = fields.Integer(
        string='Actual de Comisiones',
        compute='_compute_jh_quantity_commission',
        store=False
    )

    def advance_pps_type_calc(self):
        if not self.sales_order_line_id \
                or not self.sales_order_line_id.order_id \
                or not self.sales_order_line_id.order_id.partner_id \
                or not self.affiliate_partner_id \
                or not self.affiliate_program_id.advance_commision_id \
                or not self.sales_order_line_id.product_id:
            self.commission_amt = 0.0
            self.amt_type = "Datos incompletos"
            self.jh_type_compute = "Sin cálculo"
            return 0.0, 0.0, "none"

        order = self.sales_order_line_id.order_id
        cliente = order.partner_id
        afiliado = self.affiliate_partner_id
        producto = self.sales_order_line_id.product_id
        programa = self.affiliate_program_id.advance_commision_id
        acumuladas_qty = self.jh_quantity_commission or 0

        adv_amt, comm_val, comm_type = programa.calc_commision_adv(
            adv_comsn_id=programa.id,
            product_templ_id=producto.product_tmpl_id.id,
            product_price=self.unit_price,
            partner_vat=cliente.vat,
            affiliate_id=afiliado.id,
            quantity=self.product_quantity,
            acumuladas=acumuladas_qty
        )

        self.commission_amt = comm_val
        self.amt_type = (
            f"{int(adv_amt)}% aplicado — comisionadas: {acumuladas_qty} — tipo: {comm_type}"
            if comm_type == "percentage"
            else "Comisión fija aplicada"
        )
        self.jh_type_compute = "Comisión por Mensualidad"

        return adv_amt, comm_val, comm_type

    def get_commission_cycle_base(self, producto, cliente_vat, afiliado_id, duracion_meses):
        assert self._name == 'affiliate.visit' and len(self) == 1, "Este método debe llamarse sobre una visita única"

        visitas_grupo = self.env['affiliate.visit'].search([
            ('sales_order_line_id.product_id', '=', producto.id),
            ('sales_order_line_id.order_id.partner_id.vat', '=', cliente_vat),
            ('affiliate_partner_id', '=', afiliado_id),
            ('state', '=', 'confirm')
        ], order='create_date asc')

        hoy = self.create_date.replace(tzinfo=None)
        ciclo_encontrado = False

        for v in visitas_grupo:
            inicio = v.create_date.replace(tzinfo=None)
            fin = inicio + relativedelta(months=duracion_meses)
            if inicio <= hoy <= fin:
                ciclo_encontrado = True
                return inicio, fin

        # Si no se encuentra ciclo existente, se genera uno nuevo desde la visita actual
        return hoy, hoy + relativedelta(months=duracion_meses)

    @api.depends(
        'sales_order_line_id.product_id',
        'sales_order_line_id.order_id.partner_id.vat',
        'affiliate_partner_id',
        'affiliate_program_id.advance_commision_id.pricelist_item_ids.compute_price',
        'affiliate_program_id.advance_commision_id.pricelist_item_ids.jh_monthly_commission',
        'state',
        'create_date'
    )

    def _compute_jh_quantity_commission(self):
        for visit in self:
            producto = visit.sales_order_line_id.product_id
            cliente_vat = visit.sales_order_line_id.order_id.partner_id.vat
            afiliado_id = visit.affiliate_partner_id.id

            if not producto or not cliente_vat or not afiliado_id:
                visit.jh_quantity_commission = 0
                continue

            item = next((
                i for i in visit.affiliate_program_id.advance_commision_id.pricelist_item_ids
                if i.compute_price == "monthly" and (
                    (i.applied_on == "1_product" and i.product_tmpl_id.id == producto.product_tmpl_id.id)
                    or (
                                i.applied_on == "2_product_category" and i.categ_id in producto.product_tmpl_id.public_categ_ids)
                    or i.applied_on == "3_global")
            ), None)

            if not item:
                visit.jh_quantity_commission = 0
                continue

            duracion_meses = item.jh_duration or 0
            if duracion_meses <= 0:
                visit.jh_quantity_commission = 0
                continue

            inicio_ciclo, fin_ciclo = visit.get_commission_cycle_base(producto, cliente_vat, afiliado_id,
                                                                      duracion_meses)

            domain = [
                ('sales_order_line_id.product_id', '=', producto.id),
                ('sales_order_line_id.order_id.partner_id.vat', '=', cliente_vat),
                ('affiliate_partner_id', '=', afiliado_id),
                ('state', '=', 'confirm'),
                ('create_date', '>=', inicio_ciclo),
                ('create_date', '<=', fin_ciclo),
            ]

            if visit.id:
                domain.append(('id', '!=', visit.id))

            visitas_ciclo = self.env['affiliate.visit'].search(domain)
            visit.jh_quantity_commission = sum(v.product_quantity or 0 for v in visitas_ciclo)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    jh_affiliate_id = fields.Many2one(
        comodel_name='res.partner',
        string='Afiliado',
        domain="[('is_affiliate', '=', True)]"
    )

    def get_orders_with_pending_visits(self):
        """
        Retorna sólo las órdenes con alguna factura pendiente de visita.
        """
        pending_orders = self.filtered(lambda so: not so._has_affiliate_visit())
        _logger.info('Órdenes pendientes de visita: %s', pending_orders.mapped('name'))
        return pending_orders

    def _has_affiliate_visit(self):
        """
        Confirma si ya existe una comisión registrada para la factura actual
        en la línea principal de esta orden.
        Evalúa cada factura individualmente.
        """
        main_line = self.order_line.filtered(lambda l: not l.display_type)[:1]
        invoice_ids = self.invoice_ids

        _logger.info('[%s] Verificando visitas afiliadas por factura: main_line=%s, invoice_ids=%s',
                     self.name, main_line.ids, invoice_ids.ids)

        if not main_line or not invoice_ids:
            return False

        for factura in invoice_ids:
            visita_existente = self.env['affiliate.visit'].search_count([
                ('sales_order_line_id', '=', main_line.id),
                ('act_invoice_id', '=', factura.id)
            ]) > 0

            _logger.info('[%s] Factura %s ya tiene visita: %s', self.name, factura.name, visita_existente)

            if not visita_existente:
                return False  # Al menos una factura no procesada

        return True  # Todas las facturas ya tienen visitas


    def create_affiliate_visit_precise(self, line, invoice):
        self.ensure_one()
        if not self.jh_affiliate_id or not invoice or not line:
            return False

        existing = self.env['affiliate.visit'].search([
            ('sales_order_line_id', '=', line.id),
            ('act_invoice_id', '=', invoice.id)
        ])
        if existing:
            return False

        self.env['affiliate.visit'].create({
            'sales_order_line_id': line.id,
            'affiliate_partner_id': self.jh_affiliate_id.id,
            'currency_id': self.currency_id.id,
            'act_invoice_id': invoice.id,
            'product_quantity': line.product_uom_qty,
            'name': self.name,
            'convert_date': fields.Date.today(),
            'type_id': line.product_id.product_tmpl_id.id,
            'affiliate_method': 'pps',
            'affiliate_type': 'product',
            'affiliate_key': self.jh_affiliate_id.res_affiliate_key or '',
            'url': '', 'ip_address': '', 'amt_type': '',
            'state': 'draft', 'is_converted': True,
            'commission_amt': 0.0, 'jh_type_compute': '',
        })
        return True