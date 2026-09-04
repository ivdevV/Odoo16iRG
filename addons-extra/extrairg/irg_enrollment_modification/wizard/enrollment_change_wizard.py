# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

MODALITY_SELECTION = [
    ('Online', 'Online'),
    ('Presencial', 'Presencial'),
    ('Homeclass', 'Homeclass'),
]


class IrgEnrollmentChangeWizard(models.TransientModel):
    _name = 'irg.enrollment.change.wizard'
    _description = 'Asistente de modificación de matrícula'

    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        required=True,
        readonly=True,
    )
    student_partner_id = fields.Many2one(
        related='student_id.partner_id',
        string='Empresa del estudiante',
        readonly=True,
    )
    student_course_id = fields.Many2one(
        'op.student.course',
        string='Matrícula de origen',
        required=True,
        domain="[('student_id', '=', student_id)]",
    )
    change_course = fields.Boolean(string='Cambio de curso')
    change_batch = fields.Boolean(string='Cambio de lote')
    change_modality = fields.Boolean(string='Cambio de modalidad')
    change_year = fields.Boolean(string='Cambio de año académico')
    change_payment = fields.Boolean(string='Cambio de forma de pago')
    origin_course_id = fields.Many2one('op.course', string='Curso de origen', readonly=True)
    dest_course_id = fields.Many2one('op.course', string='Curso de destino')
    origin_batch_id = fields.Many2one('op.batch', string='Lote de origen', readonly=True)
    dest_batch_id = fields.Many2one(
        'op.batch',
        string='Lote de destino',
        domain="[('course_id', '=', dest_batch_course_id)]",
    )
    dest_batch_course_id = fields.Many2one(
        'op.course',
        compute='_compute_dest_batch_course_id',
        string='Curso del lote de destino',
    )
    origin_modality = fields.Selection(MODALITY_SELECTION, string='Modalidad de origen', readonly=True)
    dest_modality = fields.Selection(MODALITY_SELECTION, string='Modalidad de destino')
    origin_year_id = fields.Many2one('op.academic.year', string='Año de origen', readonly=True)
    dest_year_id = fields.Many2one('op.academic.year', string='Año de destino')
    origin_payment_mode_id = fields.Many2one(
        'account.payment.mode',
        string='Forma de pago de origen',
        readonly=True,
    )
    dest_payment_mode_id = fields.Many2one(
        'account.payment.mode',
        string='Forma de pago de destino',
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de venta',
        domain="[('partner_id', '=', student_partner_id), ('state', 'in', ['sale', 'done'])]",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'student_id' in fields_list and not res.get('student_id'):
            res['student_id'] = (
                self.env.context.get('default_student_id')
                or self.env.context.get('active_id')
            )
        return res

    @api.depends('change_course', 'dest_course_id', 'student_course_id', 'origin_course_id')
    def _compute_dest_batch_course_id(self):
        for wizard in self:
            if wizard.change_course:
                wizard.dest_batch_course_id = wizard.dest_course_id
            else:
                wizard.dest_batch_course_id = (
                    wizard.origin_course_id
                    or wizard.student_course_id.course_id
                )

    @api.onchange('student_course_id')
    def _onchange_student_course_id(self):
        enrollment = self.student_course_id
        self.origin_course_id = enrollment.course_id
        self.origin_batch_id = enrollment.batch_id
        self.origin_year_id = enrollment.academic_years_id
        orders = self._find_sale_orders()
        if len(orders) == 1:
            self.sale_order_id = orders
        elif self.sale_order_id and self.sale_order_id not in orders:
            self.sale_order_id = False
        self._fill_from_sale_order()

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        self._fill_from_sale_order()

    def _fill_from_sale_order(self):
        order = self.sale_order_id
        self.origin_payment_mode_id = order.payment_mode_id if order else False
        modality = False
        if order and 'x_studio_modalidad' in order.order_line._fields:
            for line in order.order_line:
                if line.x_studio_modalidad:
                    modality = line.x_studio_modalidad
                    break
        self.origin_modality = modality

    def _find_sale_orders(self):
        student = self.student_id
        if not student:
            return self.env['sale.order']
        partner = student.partner_id
        Order = self.env['sale.order']
        domain = [
            ('state', 'in', ('sale', 'done')),
            ('partner_id', '=', partner.id),
        ]
        if 'student_id' in Order._fields:
            domain = [
                ('state', 'in', ('sale', 'done')),
                '|',
                ('partner_id', '=', partner.id),
                ('student_id', '=', partner.id),
            ]
        orders = Order.search(domain, order='date_order desc, id desc')
        course = self.student_course_id.course_id
        if course and 'course_id' in Order._fields:
            matched = orders.filtered(lambda order: order.course_id == course)
            if matched:
                orders = matched
        return orders

    def _validate_wizard(self):
        self.ensure_one()
        if not any((
            self.change_course,
            self.change_batch,
            self.change_modality,
            self.change_year,
            self.change_payment,
        )):
            raise ValidationError(_('Marque al menos un cambio de matrícula.'))
        if not self.student_course_id:
            raise ValidationError(_('Seleccione la matrícula de origen.'))
        if self.change_course and not self.dest_course_id:
            raise ValidationError(_('Indique el curso de destino.'))
        if self.change_batch and not self.dest_batch_id:
            raise ValidationError(_('Indique el lote de destino.'))
        if self.change_modality and not self.dest_modality:
            raise ValidationError(_('Indique la modalidad de destino.'))
        if self.change_year and not self.dest_year_id:
            raise ValidationError(_('Indique el año académico de destino.'))
        if self.change_payment or self.change_modality:
            if not self.sale_order_id:
                raise ValidationError(
                    _('Seleccione el pedido de venta para el cambio de modalidad o de forma de pago.')
                )
        if self.change_payment:
            if not self.dest_payment_mode_id:
                raise ValidationError(_('Indique la forma de pago de destino.'))
        expected_course = (
            self.dest_course_id if self.change_course else self.student_course_id.course_id
        )
        if self.change_batch and self.dest_batch_id.course_id != expected_course:
            raise ValidationError(
                _('El lote de destino debe pertenecer al curso correspondiente.')
            )
        if self.change_course and not self.change_batch:
            current_batch = self.student_course_id.batch_id
            if current_batch.course_id != self.dest_course_id:
                raise ValidationError(
                    _('El lote actual no pertenece al curso de destino. '
                      'Marque también el cambio de lote.')
                )

    def action_create_request(self):
        self.ensure_one()
        Change = self.env['irg.enrollment.change']
        Change._check_academic_user()
        self._validate_wizard()
        enrollment = self.student_course_id
        if not self.origin_course_id:
            self.origin_course_id = enrollment.course_id
        if not self.origin_batch_id:
            self.origin_batch_id = enrollment.batch_id
        if not self.origin_year_id:
            self.origin_year_id = enrollment.academic_years_id
        if self.sale_order_id and not self.origin_payment_mode_id:
            self.origin_payment_mode_id = self.sale_order_id.payment_mode_id
        if self.sale_order_id and not self.origin_modality:
            self._fill_from_sale_order()
        change = Change.create({
            'student_id': self.student_id.id,
            'student_course_id': self.student_course_id.id,
            'sale_order_id': self.sale_order_id.id,
            'change_course': self.change_course,
            'change_batch': self.change_batch,
            'change_modality': self.change_modality,
            'change_year': self.change_year,
            'change_payment': self.change_payment,
            'origin_course_id': self.origin_course_id.id,
            'dest_course_id': self.dest_course_id.id,
            'origin_batch_id': self.origin_batch_id.id,
            'dest_batch_id': self.dest_batch_id.id,
            'origin_modality': self.origin_modality,
            'dest_modality': self.dest_modality,
            'origin_year_id': self.origin_year_id.id,
            'dest_year_id': self.dest_year_id.id,
            'origin_payment_mode_id': self.origin_payment_mode_id.id,
            'dest_payment_mode_id': self.dest_payment_mode_id.id,
        })
        change._generate_request_docx()
        return {
            'name': _('Modificación de matrícula'),
            'type': 'ir.actions.act_window',
            'res_model': 'irg.enrollment.change',
            'res_id': change.id,
            'view_mode': 'form',
            'target': 'current',
        }
