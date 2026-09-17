from odoo import api, models


def fence_orders(env, order_ids):
    """Version the parent row so REPEATABLE READ cannot miss line phantoms.

    Both line mutations and guard capture/approval participate. A stale snapshot
    raises SerializationFailure, which must reach Odoo's whole-RPC retry loop.
    No business fields or audit timestamps are changed by this fence.
    """
    env['sale.order'].flush_model()
    for order_id in sorted(set(order_ids)):
        env.cr.execute(
            'UPDATE sale_order SET id = id WHERE id = %s', (order_id,))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access_rights('create')
        # Resolve the same model/context/ir.default value the ORM would use,
        # once, before the fence. Passing it explicitly prevents a later default
        # from selecting an order whose row we did not version.
        default_order_id = False
        if any('order_id' not in vals for vals in vals_list):
            default_order_id = self.default_get(['order_id']).get('order_id', False)
        prepared = [dict(vals) if 'order_id' in vals
                    else dict(vals, order_id=default_order_id) for vals in vals_list]
        fence_orders(self.env, [vals['order_id'] for vals in prepared if vals.get('order_id')])
        return super().create(prepared)

    def write(self, vals):
        if {'order_id', 'x_studio_modalidad'} & vals.keys():
            self.check_access_rights('write')
            self.check_access_rule('write')
            order_ids = self.order_id.ids
            if vals.get('order_id'):
                order_ids.append(vals['order_id'])
            fence_orders(self.env, order_ids)
        return super().write(vals)

    def unlink(self):
        self.check_access_rights('unlink')
        self.check_access_rule('unlink')
        fence_orders(self.env, self.order_id.ids)
        return super().unlink()
