import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    # Este campo se mantiene por compatibilidad, pero en la nueva lógica
    # la vinculación real se hace a nivel de account.move.line (apuntes)
    schedule_id = fields.Many2one(
        string="Plazo en cronograma",
        comodel_name="sale.subscription.schedule",        
        ondelete='set null'
    )

    order_subscription_id = fields.Many2one(
        string="Suscripción",
        comodel_name="sale.order",
    )
    aux_disassociate = fields.Boolean('Desvincular')
    
    def open_full_view_invoice(self):
        self.ensure_one()
        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
        result['views'] = [(self.env.ref('account.view_move_form', False).id, 'form')]
        result['res_id'] = self.id
        return result

    def search_order_schedule_id(self, order):
        """
        Busca vincular esta factura a un plazo específico.
        MODIFICADO: Si es la factura global (total), no la vincula a un solo plazo.
        """
        self.ensure_one()
        
        # --- NUEVA LÓGICA: DETECCION DE FACTURA GLOBAL ---
        # Si el monto de la factura es igual (o muy cercano) al total de la orden,
        # asumimos que es la Factura Única Española y NO la intentamos meter en un solo plazo.
        # Dejamos que sale_order.py se encargue de dividir los vencimientos.
        if order.amount_total > 0:
            comparison = float_compare(self.amount_total, order.amount_total, precision_digits=2)
            if comparison == 0: # Son iguales
                _logger.info("Factura %s detectada como Global. Se omite vinculación a plazo único.", self.name)
                return

        # --- LÓGICA ANTIGUA (MANTENIDA PARA FACTURAS PARCIALES O EXTRAS) ---
        subscription_schedule = order.subscription_schedule
        match_found = False

        for lsc in subscription_schedule.filtered(lambda x: x.payment_state in ('not_paid','partial')):
            amount_recurring_taxinc =  lsc.amount_recurring_taxinc
            total_invoiced = lsc.total_invoiced
            
            # Verificamos si cabe en este plazo
            if total_invoiced <= amount_recurring_taxinc:
                invoiced_pending = amount_recurring_taxinc - total_invoiced
                
                # Tolerancia de 1 céntimo para evitar problemas de redondeo
                if self.amount_total <= (invoiced_pending + 0.01):
                    self.schedule_id = lsc.id
                    match_found = True
                    break
            
        # Si no se encontró match y NO es la factura global, lanzamos el warning
        if not self.schedule_id and not match_found:
            # Doble check: si ya tiene apuntes vinculados por la nueva lógica, no dar warning
            has_linked_lines = any(line.id in order.subscription_schedule.mapped('move_line_id').ids for line in self.line_ids)
            
            if not has_linked_lines:
                order.write({
                    'invoice_warning_ids': [(4, self.id)]
                })

    def search_order_subscription_id(self):
        self.ensure_one()
        # Busca si alguna linea de la factura viene de una Sale Order
        source_orders = self.line_ids.sale_line_ids.order_id
        if source_orders:
            for order in source_orders:
                self.order_subscription_id = order.id
                break
    
    @api.model_create_multi
    def create(self, vals):
        records = super(AccountMove, self).create(vals)
        for rec in records:
             # 1. Intentar encontrar la orden de origen
             rec.search_order_subscription_id()
             
             # 2. Si hay orden, intentar vincular a un plazo (si aplica)
             if rec.order_subscription_id and not rec.schedule_id:
                  rec.search_order_schedule_id(rec.order_subscription_id)
        return records