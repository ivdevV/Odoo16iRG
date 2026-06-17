# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrgCertificateRequest(models.Model):
    _inherit = 'irg.certificate.request'

    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        compute='_compute_student_id',
        store=True,
        index=True,
        readonly=True,
    )
    diploma_registry_id = fields.Many2one(
        'irg.diploma.registry',
        string='Registro de Diploma',
        copy=False,
        readonly=True,
        index=True,
    )
    payment_amount = fields.Monetary(
        string='Importe de Pago',
        currency_field='payment_currency_id',
        copy=False,
        readonly=True,
    )
    payment_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda de Pago',
        copy=False,
        readonly=True,
        default=lambda self: self.env.company.currency_id,
    )
    payment_concept = fields.Char(
        string='Concepto de Pago',
        copy=False,
        readonly=True,
    )
    payment_success_date = fields.Datetime(
        string='Fecha de Pago Confirmado',
        copy=False,
        readonly=True,
    )
    stripe_checkout_session_id = fields.Char(
        string='Stripe Checkout Session',
        copy=False,
        readonly=True,
        index=True,
    )
    stripe_payment_intent_id = fields.Char(
        string='Stripe PaymentIntent',
        copy=False,
        readonly=True,
        index=True,
    )
    stripe_invoice_id = fields.Char(
        string='Factura Stripe',
        copy=False,
        readonly=True,
        index=True,
    )
    stripe_invoice_url = fields.Char(
        string='URL Factura Stripe',
        copy=False,
        readonly=True,
    )
    stripe_invoice_pdf = fields.Char(
        string='PDF Factura Stripe',
        copy=False,
        readonly=True,
    )
    stripe_receipt_url = fields.Char(
        string='Recibo Stripe',
        copy=False,
        readonly=True,
    )
    stripe_payment_status = fields.Char(
        string='Estado Pago Stripe',
        copy=False,
        readonly=True,
    )
    academic_payment_validation_state = fields.Selection(
        selection=[
            ('not_checked', 'No comprobado'),
            ('eligible', 'Apto'),
            ('blocked', 'Bloqueado'),
        ],
        string='Validacion Pagos Alumno',
        default='not_checked',
        copy=False,
        readonly=True,
    )
    academic_payment_validation_date = fields.Datetime(
        string='Fecha Validacion Pagos',
        copy=False,
        readonly=True,
    )
    academic_payment_block_reason = fields.Text(
        string='Motivo Bloqueo Pagos',
        copy=False,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        requests = super().create(vals_list)
        for request, vals in zip(requests, vals_list):
            if vals.get('origin') == 'portal':
                request._check_academic_payment_eligibility(raise_if_blocked=True)
        return requests

    @api.depends('gradebook_student_id.student_id', 'partner_id')
    def _compute_student_id(self):
        Student = self.env['op.student'].sudo()
        for request in self:
            student = request.gradebook_student_id.student_id
            if not student and request.partner_id:
                student = Student.search([('partner_id', '=', request.partner_id.id)], limit=1)
            request.student_id = student

    def _get_academic_course_product_templates(self):
        self.ensure_one()
        templates = self.env['product.template']
        course = self.course_id
        if not course:
            return templates
        if 'product_template_id' in course._fields and course.product_template_id:
            templates |= course.product_template_id
        if 'product_template_ids' in course._fields and course.product_template_ids:
            templates |= course.product_template_ids
        return templates

    def _get_academic_sale_orders(self):
        self.ensure_one()
        partner = self.partner_id
        if not partner:
            return self.env['sale.order']

        orders = self.env['sale.order'].sudo().search([
            ('state', 'not in', ('draft', 'sent', 'cancel')),
            '|',
            ('student_id', '=', partner.id),
            ('partner_id', '=', partner.id),
        ])
        course_templates = self._get_academic_course_product_templates()
        if not course_templates:
            return orders

        course_orders = orders.filtered(
            lambda order: any(
                line.product_template_id in course_templates
                for line in order.order_line
            )
        )
        return course_orders or orders

    def _get_academic_invoices(self, orders=None):
        self.ensure_one()
        partner = self.partner_id
        if not partner:
            return self.env['account.move']

        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            '|',
            ('partner_id', '=', partner.id),
            ('irg_student_partner_id', '=', partner.id),
        ]
        invoices = self.env['account.move'].sudo().search(domain)
        if orders:
            order_invoices = orders.mapped('invoice_ids').filtered(
                lambda move: move.move_type == 'out_invoice' and move.state == 'posted'
            )
            invoices |= order_invoices

        # Exclude invoices related to certificate requests
        cert_requests = self.env['irg.certificate.request'].sudo().search([
            ('partner_id', '=', partner.id),
            ('invoice_id', '!=', False)
        ])
        if cert_requests:
            invoices = invoices.filtered(lambda inv: inv.id not in cert_requests.mapped('invoice_id').ids)

        return invoices

    def _has_overdue_academic_debt(self, orders, invoices):
        today = fields.Date.context_today(self)
        for order in orders:
            schedules = order.subscription_schedule if 'subscription_schedule' in order._fields else False
            if schedules:
                overdue = schedules.filtered(
                    lambda line: line.payment_state != 'paid'
                    and (
                        line.date_due
                        or (line.date_schedule if 'date_schedule' in line._fields else False)
                        or today
                    ) <= today
                )
                if overdue:
                    return True

        unpaid_due_invoices = invoices.filtered(
            lambda move: move.payment_state not in ('paid', 'in_payment', 'reversed')
            and (move.invoice_date_due or move.invoice_date or today) <= today
            and move.amount_residual > 0
        )
        return bool(unpaid_due_invoices)

    def _has_pending_master_balance(self, orders, invoices):
        for order in orders:
            schedules = order.subscription_schedule if 'subscription_schedule' in order._fields else False
            if schedules and schedules.filtered(lambda line: line.payment_state != 'paid'):
                return True
            if not schedules and order.invoice_ids.filtered(
                lambda move: move.move_type == 'out_invoice'
                and move.state == 'posted'
                and move.payment_state not in ('paid', 'in_payment', 'reversed')
                and move.amount_residual > 0
            ):
                return True

        pending_invoices = invoices.filtered(
            lambda move: move.payment_state not in ('paid', 'in_payment', 'reversed')
            and move.amount_residual > 0
        )
        return bool(pending_invoices)

    def _get_subscription_data_debt_reason(self):
        self.ensure_one()
        student = self.student_id
        if not student or not hasattr(student, 'get_subscription_data'):
            return False
        sub_data = student.sudo().get_subscription_data()
        if sub_data.get('t_adeuda') or (sub_data.get('t_amount_due_data') or 0) > 0:
            return _(
                'El alumno tiene cuotas de matricula pendientes de pago.'
            )
        return False

    def _check_academic_payment_eligibility(self, raise_if_blocked=False):
        """Validate academic payment status before requesting/generating docs."""
        self.ensure_one()
        reason = False
        final_documents = ('gradebook', 'diploma')

        if not self.partner_id:
            reason = _('No se ha podido identificar el alumno de la solicitud.')
        else:
            orders = self._get_academic_sale_orders()
            invoices = self._get_academic_invoices(orders=orders)
            reason = self._get_subscription_data_debt_reason()

            if not reason and self.document_type in final_documents:
                if not orders and not invoices:
                    reason = _(
                        'No hay informacion de venta o facturacion para comprobar que el master esta completamente pagado.'
                    )
                elif self._has_pending_master_balance(orders, invoices):
                    reason = _(
                        'Para solicitar este documento el master debe estar completamente pagado.'
                    )
            elif not reason and self._has_overdue_academic_debt(orders, invoices):
                reason = _(
                    'El alumno no esta al dia de pagos academicos.'
                )

        self.sudo().write({
            'academic_payment_validation_state': 'blocked' if reason else 'eligible',
            'academic_payment_validation_date': fields.Datetime.now(),
            'academic_payment_block_reason': reason or False,
        })
        if reason and raise_if_blocked:
            raise ValidationError(reason)
        return not bool(reason)

    def _generate_and_attach_pdf(self):
        Registry = self.env['irg.diploma.registry'].sudo()
        for request in self:
            request._check_academic_payment_eligibility(raise_if_blocked=True)
            registry_domain = []
            existing_registries = Registry
            if request.document_type == 'diploma':
                student = request.student_id or request.gradebook_student_id.student_id
                registry_domain = [('student_id', '=', student.id)] if student else []
                if registry_domain:
                    existing_registries = Registry.search(registry_domain)

            super(IrgCertificateRequest, request)._generate_and_attach_pdf()

            if request.document_type == 'diploma' and request.attachment_id:
                new_registry = Registry
                if registry_domain:
                    new_registry = Registry.search(
                        registry_domain + [('id', 'not in', existing_registries.ids)],
                        order='id desc',
                        limit=1,
                    )
                if not new_registry:
                    new_registry = Registry.search(
                        registry_domain + [('attachment_id', '=', False)] if registry_domain else [('attachment_id', '=', False)],
                        order='id desc',
                        limit=1,
                    )
                if new_registry:
                    new_registry.write({'attachment_id': request.attachment_id.id})
                    request.sudo().write({'diploma_registry_id': new_registry.id})

    def action_generate_pdf(self):
        for request in self:
            request._check_academic_payment_eligibility(raise_if_blocked=True)
        return super().action_generate_pdf()

    def _process_payment(self):
        for request in self:
            request._check_academic_payment_eligibility(raise_if_blocked=True)
        return super()._process_payment()
