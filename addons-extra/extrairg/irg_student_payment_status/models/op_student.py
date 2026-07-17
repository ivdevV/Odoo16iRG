# -*- coding: utf-8 -*-

import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.tools.misc import format_amount


_logger = logging.getLogger(__name__)


class OpStudent(models.Model):
    _inherit = 'op.student'

    _IRG_DEFAULT_MOROSO_THRESHOLD = 2
    _IRG_DEFAULT_GRACE_DAYS = 15
    _IRG_DEFAULT_ACTIVITY_SUMMARY = 'Seguimiento de morosidad'

    irg_payment_status = fields.Selection(
        selection=[
            ('al_dia', 'Al día'),
            ('atrasado', 'Atrasado'),
            ('moroso', 'Moroso'),
        ],
        string='Estado de pago',
        default='al_dia',
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    irg_overdue_invoice_count = fields.Integer(
        string='Facturas vencidas',
        compute='_compute_irg_overdue_metrics',
    )
    irg_overdue_amount = fields.Monetary(
        string='Deuda vencida',
        currency_field='irg_payment_currency_id',
        compute='_compute_irg_overdue_metrics',
    )
    irg_payment_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda de deuda',
        compute='_compute_irg_overdue_metrics',
    )
    irg_payment_status_date = fields.Date(
        string='Última transición de pago',
        readonly=True,
        copy=False,
    )

    @api.model
    def _irg_get_nonnegative_int_param(self, key, default, minimum=0):
        value = self.env['ir.config_parameter'].sudo().get_param(key)
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed >= minimum else default

    @api.model
    def _irg_get_moroso_threshold(self):
        return self._irg_get_nonnegative_int_param(
            'irg_student_payment.moroso_threshold',
            self._IRG_DEFAULT_MOROSO_THRESHOLD,
            minimum=1,
        )

    @api.model
    def _irg_get_grace_days(self):
        return self._irg_get_nonnegative_int_param(
            'irg_student_payment.grace_days',
            self._IRG_DEFAULT_GRACE_DAYS,
        )

    def _get_irg_overdue_invoices(self):
        self.ensure_one()
        if not self.partner_id:
            return self.env['account.move'].browse()
        cutoff_date = fields.Date.today() - timedelta(
            days=self._irg_get_grace_days()
        )
        domain = self._get_irg_academic_invoice_domain() + [
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('invoice_date_due', '<', cutoff_date),
        ]
        return self.env['account.move'].sudo().search(domain)

    @api.depends('partner_id', 'company_id')
    def _compute_irg_overdue_metrics(self):
        for student in self:
            currency = student.company_id.currency_id or self.env.company.currency_id
            invoices = student._get_irg_overdue_invoices()
            student.irg_overdue_invoice_count = len(invoices)
            student.irg_overdue_amount = sum(
                invoices.mapped('amount_residual_signed')
            )
            student.irg_payment_currency_id = currency

    @api.model
    def _irg_payment_status_from_overdue_count(self, overdue_count,
                                               threshold=None):
        threshold = threshold or self._irg_get_moroso_threshold()
        if not overdue_count:
            return 'al_dia'
        if overdue_count >= threshold:
            return 'moroso'
        return 'atrasado'

    def _irg_compute_payment_status(self):
        threshold = self._irg_get_moroso_threshold()
        statuses = {}
        for student in self:
            overdue_count = len(student._get_irg_overdue_invoices())
            statuses[student.id] = self._irg_payment_status_from_overdue_count(
                overdue_count, threshold=threshold
            )
        if len(self) == 1:
            return statuses[self.id]
        return statuses

    @api.model
    def _irg_get_payment_activity_user(self):
        users = self.env['res.users'].sudo().with_context(active_test=False)
        configured_id = self.env['ir.config_parameter'].sudo().get_param(
            'irg_student_payment.activity_user_id'
        )
        try:
            configured_id = int(configured_id)
        except (TypeError, ValueError):
            configured_id = 0
        configured_user = users.browse(configured_id).exists()
        if configured_user and configured_user.active and not configured_user.share:
            return configured_user

        group = self.env.ref('openeducat_core.group_op_back_office_admin')
        candidates = group.sudo().users.filtered(
            lambda user: user.active and not user.share
        ).sorted('id')
        admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        if admin and admin in candidates:
            return admin
        return candidates[:1]

    def _irg_find_default_activities(self):
        self.ensure_one()
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        model = self.env['ir.model']._get(self._name)
        return self.env['mail.activity'].sudo().search([
            ('activity_type_id', '=', activity_type.id),
            ('res_model_id', '=', model.id),
            ('res_id', '=', self.id),
            ('summary', '=', self._IRG_DEFAULT_ACTIVITY_SUMMARY),
        ])

    def _irg_schedule_default_activity(self):
        self.ensure_one()
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        existing = self._irg_find_default_activities()
        user = self._irg_get_payment_activity_user()
        if not existing and user:
            self.sudo().activity_schedule(
                activity_type_id=activity_type.id,
                user_id=user.id,
                summary=self._IRG_DEFAULT_ACTIVITY_SUMMARY,
                note=_('Revisar la deuda académica vencida del alumno.'),
            )

    def _irg_close_default_activities(self):
        self.ensure_one()
        activities = self._irg_find_default_activities()
        if activities:
            activities.action_feedback(
                feedback=_('Seguimiento de morosidad cerrado al salir de moroso.')
            )

    def _irg_post_status_transition(self, old_status, new_status, invoices,
                                    grace_days):
        self.ensure_one()
        currency = self.company_id.currency_id or self.env.company.currency_id
        amount = sum(invoices.mapped('amount_residual_signed'))
        labels = dict(self._fields['irg_payment_status'].selection)
        body = _(
            'Estado de pago actualizado: %(old)s → %(new)s. '
            'Facturas vencidas: %(count)s. Deuda residual: %(amount)s. '
            'Gracia aplicada: %(grace)s días.',
            old=labels.get(old_status, old_status),
            new=labels.get(new_status, new_status),
            count=len(invoices),
            amount=format_amount(self.env, amount, currency),
            grace=grace_days,
        )
        if old_status == 'moroso' and new_status == 'al_dia':
            body += ' ' + _('Situación de pago regularizada.')
        self.sudo().message_post(body=body, subtype_xmlid='mail.mt_note')

    def _irg_update_payment_statuses(self):
        grace_days = self._irg_get_grace_days()
        counters = {'processed': 0, 'changed': 0, 'moroso': 0}
        for student in self:
            counters['processed'] += 1
            invoices = student._get_irg_overdue_invoices()
            new_status = student._irg_payment_status_from_overdue_count(
                len(invoices)
            )
            old_status = student.irg_payment_status or 'al_dia'
            if old_status == new_status:
                continue
            student.sudo().write({
                'irg_payment_status': new_status,
                'irg_payment_status_date': fields.Date.today(),
            })
            student._irg_post_status_transition(
                old_status, new_status, invoices, grace_days
            )
            if new_status == 'moroso':
                counters['moroso'] += 1
                student._irg_schedule_default_activity()
            elif old_status == 'moroso':
                student._irg_close_default_activities()
            student._irg_on_status_change(old_status, new_status)
            counters['changed'] += 1
        return counters

    def action_irg_update_payment_status(self):
        if not self.env.user.has_group(
                'openeducat_core.group_op_back_office_admin'):
            raise AccessError(_(
                'Solo los administradores de back-office pueden actualizar '
                'manualmente el estado de pago.'
            ))
        self.check_access_rights('write')
        self.check_access_rule('write')
        self._irg_update_payment_statuses()
        return True

    @api.model
    def _cron_update_payment_status(self):
        students = self.sudo().search([('partner_id', '!=', False)])
        counters = students._irg_update_payment_statuses()
        _logger.info(
            'Student payment status cron: processed=%s changed=%s moroso=%s',
            counters['processed'], counters['changed'], counters['moroso'],
        )
        return counters

    def _irg_on_status_change(self, old_status, new_status):
        """Extension hook called after a payment status transition is saved."""
        return None

    def action_view_irg_overdue_invoices(self):
        self.ensure_one()
        invoices = self._get_irg_overdue_invoices()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_move_out_invoice_type'
        )
        action.update({
            'domain': [('id', 'in', invoices.ids)],
            'context': {
                'create': False,
                'default_move_type': 'out_invoice',
                'default_partner_id': self.partner_id.id,
            },
        })
        if len(invoices) == 1:
            form_view = self.env.ref(
                'account.view_move_form', raise_if_not_found=False
            )
            action.update({
                'views': [(form_view.id if form_view else False, 'form')],
                'res_id': invoices.id,
            })
        return action
