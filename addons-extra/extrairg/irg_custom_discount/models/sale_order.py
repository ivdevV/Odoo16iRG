# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    irg_discount_program_id = fields.Many2one(
        'irg.discount.program',
        string='Descuento IRG aplicado',
        readonly=True,
        copy=False,
    )
    irg_discount_code = fields.Char(
        string='Código descuento IRG',
        copy=False,
    )

    def _irg_try_apply_discount_code(self, code):
        """
        Busca un programa de descuento IRG por código y lo aplica si es válido.
        Retorna: (True, mensaje_exito) o (False, mensaje_error)
        """
        self.ensure_one()
        code = code.strip().upper() if code else ''
        if not code:
            return False, _("Introduce un código de descuento.")

        program = self.env['irg.discount.program'].sudo().search([
            ('code', '=ilike', code),
            ('active', '=', True),
        ], limit=1)

        if not program:
            return False, ''  # Vacío = no es nuestro código, dejamos pasar al loyalty

        # Validar restricciones
        is_valid, error_msg = program._is_valid(self)
        if not is_valid:
            return False, error_msg

        # Comprobar si ya tiene un descuento IRG aplicado
        if self.irg_discount_program_id and not self.irg_discount_program_id.combinable:
            # Eliminar el anterior
            self._irg_remove_discount_lines()

        # Calcular descuento
        discount_amount = program._compute_discount(self)
        if discount_amount <= 0:
            return False, _("El descuento no aplica para este pedido.")

        # Obtener producto de descuento
        discount_product = self.env.ref(
            'irg_custom_discount.product_irg_discount', raise_if_not_found=False
        )
        if not discount_product:
            discount_product = self.env['product.product'].search(
                [('default_code', '=', 'IRG_DISCOUNT')], limit=1
            )
        if not discount_product:
            _logger.error("IRG Discount: Producto de descuento no encontrado")
            return False, _("Error interno al aplicar el descuento.")

        # Crear línea de descuento (precio negativo)
        description = program.description or program.name
        line_name = _("Descuento: %s (%s)") % (description, code)

        self.env['sale.order.line'].sudo().create({
            'order_id': self.id,
            'product_id': discount_product.id,
            'name': line_name,
            'product_uom_qty': 1,
            'price_unit': -discount_amount,
            'tax_id': [(5, 0, 0)],  # Sin impuestos
        })

        # Registrar en la orden
        self.write({
            'irg_discount_program_id': program.id,
            'irg_discount_code': code,
        })

        # Incrementar contador de uso
        program.sudo().write({
            'usage_count': program.usage_count + 1,
        })

        _logger.info(
            "IRG Discount: Aplicado '%s' (-%s€) al pedido %s",
            code, discount_amount, self.name
        )

        return True, _("¡Descuento de %s€ aplicado correctamente!") % discount_amount

    def _irg_remove_discount_lines(self):
        """Elimina las líneas de descuento IRG del pedido."""
        self.ensure_one()
        discount_product = self.env.ref(
            'irg_custom_discount.product_irg_discount', raise_if_not_found=False
        )
        if not discount_product:
            discount_product = self.env['product.product'].search(
                [('default_code', '=', 'IRG_DISCOUNT')], limit=1
            )
        if discount_product:
            lines = self.order_line.filtered(
                lambda l: l.product_id.id == discount_product.id
            )
            if lines:
                # Decrementar el contador de uso del programa anterior
                if self.irg_discount_program_id:
                    count = max(0, self.irg_discount_program_id.usage_count - 1)
                    self.irg_discount_program_id.sudo().write({'usage_count': count})
                lines.unlink()

        self.write({
            'irg_discount_program_id': False,
            'irg_discount_code': False,
        })
