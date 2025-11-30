# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderAdmission(models.Model):
    _inherit = 'sale.order'

    admission_multi_ids = fields.One2many(
        'sale.order.admission.line', 'order_id', 
        string='Admisiones', copy=False)


    def auto_ad_active(self, course=None):
        ad = self.env['auto.admission.required'].search([], limit=1)
        lang = course.lang if course else (self.course_id.lang if self.course_id else False)

        if lang in ('es_MX', 'es_ES') and ad.mx_active:
            return True
        if lang == 'pt_BR' and ad.br_active:
            return True
        return False


    def _action_confirm(self):
        res = super(SaleOrderAdmission, self)._action_confirm()
        for order in self:
            if not order.period:
                order._compute_period()

            academic_lines = order.order_line.filtered(
                lambda l: l.product_template_id.is_academic_program and l.product_template_id.recurring_invoice
            )
            if not academic_lines:
                continue

            if len(academic_lines) == 1:
                line = academic_lines[0]
                _logger.info("Caso 1: flujo original para orden %s", order.name)

                admission = order._create_or_get_admission(line)
                if admission:
                    order.admission_id = admission
                    order.admission_register_id = admission.register_id
                    order.course_id = admission.course_id
                    order.product_template_id = line.product_template_id

                    order._process_auto_admission(admission, line)

            else:
                _logger.info("Caso 2: múltiples admisiones para orden %s → usando One2many", order.name)

                for line in academic_lines:
                    admission = order._create_or_get_admission(line)
                    if admission:
                        order._upsert_admission_row(
                            line,
                            register=admission.register_id,
                            admission=admission,
                            course=admission.course_id,
                            product_template=line.product_template_id,
                        )
                        order._process_auto_admission(admission, line)

        return res


    def _create_or_get_admission(self, line):
        # Search for course in both single and multi product fields
        domain = ['|', 
                 ('product_template_id', '=', line.product_template_id.id),
                 ('product_template_ids', 'in', line.product_template_id.id)]
        
        course = self.env['op.course'].search(domain, limit=1)
        
        if not course:
            self._upsert_admission_row(
                line,
                error_msg=f"No se encontró Curso para {line.product_template_id.display_name}.",
            )
            return False

        if not self.period:
            self._compute_period()
        if not self.period:
            self._upsert_admission_row(
                line,
                course=course,
                error_msg="No se pudo determinar el Periodo de Admisión.",
            )
            return False

        register = self._find_or_create_register(
            period=self.period,
            product_template=line.product_template_id,
            course=course,
        )

        admission = line.admission_id
        if not admission:
            partner = self.partner_id
            parts = (partner.name or '').split()
            first_name = ' '.join(parts[:-1]) if len(parts) > 1 else (parts[0] if parts else '-')
            last_name = parts[-1] if len(parts) > 1 else '-'

            admission = self.env['op.admission'].create({
                'name': partner.name,
                'first_name': (first_name or '-').strip(),
                'last_name': (last_name or '-').strip(),
                'sale_id': self.id,
                'email': partner.email,
                'mobile': partner.mobile,
                'phone': partner.phone,
                'partner_id': partner.id,
                'register_id': register.id,
                'course_id': register.course_id.id,
                'application_date': fields.Datetime.now(),
                'admission_date': fields.Datetime.now(),
                'fees_term_id': self.env['op.fees.terms'].search([], limit=1).id,
                'gender': self.gender or partner.gender or 'o',
                'batch_id': self.get_lot_id(course).id,
                'order_id': self.id,
            })
            line.admission_id = admission.id

        return admission


    def _process_auto_admission(self, admission, line):
        ad = self.env['auto.admission.required'].search([], limit=1)
        lang = admission.course_id.lang or False
        auto_ad = self.auto_ad_active(admission.course_id)

        if auto_ad and lang and admission:
            try:

                if lang in ('es_MX', 'es_ES'):
                    if ad.mx_state_admission_done:
                        admission.submit_form()
                        admission.confirm_in_progress()
                        admission.admission_confirm()
                        admission.enroll_student()
                    if ad.mx_auto_email_welcome and not admission.email_send_ok:
                        admission.send_mail_view()

                elif lang == 'pt_BR':
                    if ad.br_state_admission_done:
                        admission.submit_form()
                        admission.confirm_in_progress()
                        admission.admission_confirm()
                        admission.enroll_student()
                    if ad.br_auto_email_welcome and not admission.email_send_ok:
                        admission.send_mail_view()

            except Exception as e:
                self._upsert_admission_row(
                    line,
                    course=admission.course_id,
                    register=admission.register_id,
                    admission=admission,
                    error_msg="<b>Post-admisión:</b> %s" % str(e)[:500],
                )
                self.error_admission = True



    def _upsert_admission_row(self, line, *, register=None, admission=None,
                              course=None, product_template=None, error_msg=False):
        self.ensure_one()
        Row = self.env['sale.order.admission.line']
        row = Row.search([
            ('order_id', '=', self.id),
            ('sale_line_id', '=', line.id),
        ], limit=1)

        vals = {
            'order_id': self.id,
            'sale_line_id': line.id,
            'product_template_id': (product_template or line.product_template_id).id,
            'course_id': course.id if course else False,
            'admission_register_id': register.id if register else False,
            'admission_id': admission.id if admission else False,
            'admission_date': self.admission_date or fields.Date.context_today(self),
            'error_admission': bool(error_msg),
            'error_admission_msn': error_msg or False,
        }

        if row:
            row.write(vals)
        else:
            Row.create(vals)



    def _find_or_create_register(self, *, period, product_template, course):
        Register = self.env['op.admission.register']
        reg = Register.search([
            ('state', 'in', ['confirm', 'application', 'admission']),
            ('period', '=', period),
            '|',
            ('product_template_id', '=', product_template.id),
            ('product_template_ids', 'in', product_template.id),
        ], limit=1)

        if reg and reg.state == 'confirm':
            reg.start_application()

        if not reg:
            reg = Register.create({
                'course_id': course.id,
                'name': f"{period} {course.name}",
                'min_count': 1,
                'max_count': 500,
                'period': period,
                'start_date': fields.Date.today(),
                'end_date': self.gat_date_max_register(period),
                'product_template_id': product_template.id,
            })
            reg.start_application()

        return reg


    def get_admision_id(self, admission_register_id):
        return False


    def action_get_admision_id_manual(self):
        auto_ad = self.auto_ad_active()
        if auto_ad:
            if self.admission_register_id:
                self.create_admission_manual(self.admission_register_id)


    
    def create_admission_manual(self, admission_register_id):
        op_admission = self.env['op.admission']
        
        name = self.partner_id.name.replace('  ',' ').replace('   ',' ').replace('    ',' ').replace('     ',' ').replace('      ',' ').split(' ')
        
        first_name = '-'
        last_name = '-'
        if len(name)==1:
            first_name=name[0]
        if len(name)>1:
            first_name = ''
            for i in range(0,len(name)-1):
                first_name+=str(name[i])+' '
            last_name = name[-1]
        
        op_admission = op_admission.create({
            'name': self.partner_id.name,
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'sale_id': self.id,
            'email': self.partner_id.email,
            'mobile': self.partner_id.mobile,
            'phone':self.partner_id.phone,
            # 'product_template_id': self.product_template_id.id,
            'partner_id': self.partner_id.id,
            'register_id' : admission_register_id.id,
            'course_id' : admission_register_id.course_id.id,
            'application_date': fields.datetime.now(),
            'admission_date': fields.datetime.now(),
            'fees_term_id': self.env['op.fees.terms'].search([], limit=1).id,
            'gender': self.gender or self.partner_id.gender or 'o',
            'batch_id': self.get_lot_id(admission_register_id.course_id).id,
            'order_id': self.id,    
            
        })
        
        
        self.admission_id = op_admission.id

