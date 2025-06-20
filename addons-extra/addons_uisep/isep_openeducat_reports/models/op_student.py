# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class OpStudent(models.Model):
    _inherit = "op.student"


    def get_subscription_data(self):
        self.ensure_one()  # Ensure this method is called on a single record
        res = {
                't_recurring_rule_count': 0,
                't_amount_recurring_due': 0.0,
                't_amount_total_payment': 0.0,
                't_amount_total_sale': 0.0,
                't_amount_total_recurring': 0.0,
                't_amount_recurring_taxinc': 0.0,
                't_amount_no_recurring_taxinc': 0.0,
              }
        sale_orders = self.env['sale.order'].search([('is_subscription','=',True),('partner_id','=',self.partner_id.id),('state','=','sale')])
        for subscription in sale_orders:
            res['t_recurring_rule_count'] = res['t_recurring_rule_count'] + subscription.recurring_rule_count
            res['t_amount_recurring_due'] = res['t_amount_recurring_due'] + subscription.amount_recurring_due
            res['t_amount_total_payment'] = res['t_amount_total_payment'] + subscription.amount_total_payment
            res['t_amount_total_sale'] = res['t_amount_total_sale'] + subscription.amount_total_sale
            res['t_amount_total_recurring'] = res['t_amount_total_recurring'] + subscription.amount_total_recurring
            res['t_amount_recurring_taxinc'] = res['t_amount_recurring_taxinc'] + subscription.amount_recurring_taxinc
            res['t_amount_no_recurring_taxinc'] = res['t_amount_no_recurring_taxinc'] + subscription.amount_no_recurring_taxinc
        return res

