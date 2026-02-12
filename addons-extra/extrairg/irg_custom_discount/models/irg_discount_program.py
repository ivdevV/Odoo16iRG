# -*- coding: utf-8 -*-
import logging
from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class IrgDiscountProgram(models.Model):
    _name = 'irg.discount.program'
    _description = 'Programa de Descuento con Fórmula Personalizada'
    _order = 'sequence, id'

    name = fields.Char(string='Nombre', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)
    code = fields.Char(
        string='Código de Descuento',
        required=True,
        help='Código que el cliente introduce en el ecommerce.'
    )
    description = fields.Text(
        string='Descripción',
        help='Descripción visible para el cliente en la línea de descuento.'
    )
    target_product_id = fields.Many2one(
        'product.product',
        string='Producto objetivo',
        help='Producto sobre el que se calcula la variable product_amount. Si está vacío, product_amount será 0.'
    )
    target_product_ids = fields.Many2many(
        'product.product',
        'irg_discount_program_product_rel',
        'program_id',
        'product_id',
        string='Productos objetivo',
        help='Productos sobre los que se calcula la variable product_amount. Si está vacío, product_amount será 0.'
    )
    formula = fields.Text(
        string='Fórmula de Descuento',
        required=True,
        help="""Expresión Python que devuelve el importe de descuento (positivo).
Variables disponibles:
  - amount_untaxed: Total sin impuestos
  - amount_total: Total con impuestos
  - qty_total: Cantidad total de productos
  - line_count: Número de líneas de producto
    - product_amount: Subtotal sin impuestos de los productos objetivo en el pedido
  - order: El objeto sale.order completo

Ejemplos:
  amount_untaxed * 0.10            → 10%% de descuento
    product_amount * 0.20            → 20%% del importe de los productos objetivo
  min(amount_untaxed * 0.15, 500)  → 15%% con tope de 500€
  100 if amount_untaxed > 1000 else 50
  amount_untaxed * 0.05 if qty_total >= 2 else 0
"""
    )

    # --- Restricciones ---
    date_from = fields.Date(string='Válido desde')
    date_to = fields.Date(string='Válido hasta')
    min_amount = fields.Float(
        string='Importe mínimo del pedido',
        default=0.0,
        help='El pedido debe superar este importe (sin impuestos) para aplicar el descuento.'
    )
    max_discount = fields.Float(
        string='Descuento máximo (€)',
        default=0.0,
        help='Tope máximo del descuento. 0 = sin límite.'
    )
    usage_limit = fields.Integer(
        string='Límite de usos',
        default=0,
        help='Número máximo de veces que se puede usar. 0 = ilimitado.'
    )
    usage_count = fields.Integer(
        string='Usos actuales',
        default=0,
        readonly=True,
    )
    partner_ids = fields.Many2many(
        'res.partner',
        string='Clientes específicos',
        help='Dejar vacío para que cualquier cliente pueda usarlo.'
    )
    combinable = fields.Boolean(
        string='Combinable con otros descuentos',
        default=False,
        help='Si se permite usar junto con otros códigos de descuento IRG.'
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código de descuento debe ser único.'),
    ]

    def _table_exists(self, table_name):
        self.env.cr.execute("SELECT to_regclass(%s)", (table_name,))
        return bool(self.env.cr.fetchone()[0])

    def _column_exists(self, table_name, column_name):
        self.env.cr.execute(
            """
            SELECT 1
              FROM information_schema.columns
             WHERE table_name = %s
               AND column_name = %s
             LIMIT 1
            """,
            (table_name, column_name),
        )
        return bool(self.env.cr.fetchone())

    @api.constrains('formula')
    def _check_formula(self):
        """Valida que la fórmula sea sintácticamente correcta."""
        for rec in self:
            if rec.formula:
                try:
                    # Test con valores ficticios
                    test_vars = {
                        'amount_untaxed': 1000.0,
                        'amount_total': 1210.0,
                        'qty_total': 2.0,
                        'line_count': 2,
                        'product_amount': 300.0,
                        'min': min,
                        'max': max,
                        'abs': abs,
                        'round': round,
                    }
                    result = eval(rec.formula.strip(), {"__builtins__": {}}, test_vars)
                    if not isinstance(result, (int, float)):
                        raise ValidationError(
                            _("La fórmula debe devolver un número. Resultado obtenido: %s") % type(result).__name__
                        )
                except ValidationError:
                    raise
                except Exception as e:
                    raise ValidationError(
                        _("Error en la fórmula: %s") % str(e)
                    )

    def _is_valid(self, order):
        """Comprueba si el programa es válido para el pedido dado."""
        self.ensure_one()
        today = date.today()

        # Fechas
        if self.date_from and today < self.date_from:
            return False, _("Este código aún no es válido.")
        if self.date_to and today > self.date_to:
            return False, _("Este código ha expirado.")

        # Usos
        if self.usage_limit > 0 and self.usage_count >= self.usage_limit:
            return False, _("Este código ha alcanzado el límite de usos.")

        # Importe mínimo
        if self.min_amount > 0 and order.amount_untaxed < self.min_amount:
            return False, _("El pedido debe ser de al menos %s€ para usar este código.") % self.min_amount

        # Clientes específicos
        if self.partner_ids and order.partner_id not in self.partner_ids:
            return False, _("Este código no es válido para tu cuenta.")

        return True, ''

    def _compute_discount(self, order):
        """Evalúa la fórmula y devuelve el importe de descuento."""
        self.ensure_one()

        # Calcular qty_total excluyendo líneas de descuento
        product_lines = order.order_line.filtered(
            lambda l: not l.display_type and l.price_unit >= 0
        )
        qty_total = sum(product_lines.mapped('product_uom_qty'))
        line_count = len(product_lines)
        product_amount = 0.0

        target_products = self.env['product.product']
        if self._table_exists('irg_discount_program_product_rel'):
            target_products = self.target_product_ids

        if not target_products and self._column_exists('irg_discount_program', 'target_product_id'):
            target_products = self.target_product_id

        if target_products:
            target_templates = target_products.mapped('product_tmpl_id')
            target_lines = product_lines.filtered(
                lambda l: l.product_id in target_products or l.product_id.product_tmpl_id in target_templates
            )
            product_amount = sum(target_lines.mapped('price_subtotal'))

        safe_vars = {
            'amount_untaxed': order.amount_untaxed,
            'amount_total': order.amount_total,
            'qty_total': qty_total,
            'line_count': line_count,
            'product_amount': product_amount,
            'order': order,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
        }

        try:
            discount = eval(self.formula.strip(), {"__builtins__": {}}, safe_vars)
            discount = float(discount)
        except Exception as e:
            _logger.error("IRG Discount: Error evaluando fórmula '%s': %s", self.formula, str(e))
            return 0.0

        # Garantizar que es positivo
        discount = abs(discount)

        # Aplicar tope
        if self.max_discount > 0:
            discount = min(discount, self.max_discount)

        # No puede exceder el total del pedido
        discount = min(discount, order.amount_untaxed)

        return round(discount, 2)
