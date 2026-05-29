# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_open_manual_confirmation_wizard(self):
        """Boton manual: abre wizard de validacion antes de confirmar."""
        self.ensure_one()
        # Asegurar que se calculan curso_id y product_template_id en el presupuesto
        self.get_academic_product_template_id()
        
        # Buscar fecha de inicio de la línea de presupuesto
        academic_lines = self.order_line.filtered(
            lambda l: (l.product_template_id.is_academic_program and l.product_template_id.recurring_invoice) or
                      self.env['op.course'].search_count([
                          '|',
                          ('product_template_id', '=', l.product_template_id.id),
                          ('product_template_ids', 'in', l.product_template_id.id)
                      ]) > 0
        )
        line_start_date = False
        if academic_lines:
            line_start_date = academic_lines[0].start_date_enroller

        today = fields.Date.today()
        current = line_start_date or self.admission_date
        
        if line_start_date:
            default_date = line_start_date
        elif not current or current.month != today.month or current.year != today.year:
            default_date = today.replace(day=1)
        else:
            default_date = current
            
        wizard = self.env['irg.manual.confirmation.wizard'].create({
            'order_id': self.id,
            'admission_date': default_date,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirmar presupuesto (validar fechas)'),
            'res_model': 'irg.manual.confirmation.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _get_line_modality(self, line):
        if not line:
            return ''
        categ_code = False
        if line.product_id and line.product_id.categ_id and line.product_id.categ_id.code:
            categ_code = line.product_id.categ_id.code
        elif line.product_template_id and line.product_template_id.categ_id and line.product_template_id.categ_id.code:
            categ_code = line.product_template_id.categ_id.code
        elif hasattr(line, 'course_id') and line.course_id and line.course_id.product_template_id and line.course_id.product_template_id.categ_id and line.course_id.product_template_id.categ_id.code:
            categ_code = line.course_id.product_template_id.categ_id.code

        if categ_code and categ_code.upper().startswith('DI'):
            return 'HC'

        if not line.product_id:
            return ''
        for ptav in line.product_id.product_template_attribute_value_ids:
            if ptav.attribute_id.name == 'Modalidad':
                name = (ptav.product_attribute_value_id.name or '').strip()
                if name == 'Online':
                    return 'ONL'
                if name == 'HomeClass':
                    return 'HC'
                if name == 'Presencial':
                    return 'PRS'
                return name[:3].upper() if name else 'GE'
        return 'GE'

    def _create_or_get_admission(self, line):
        """Override de isep_sale_order_admissions.
        Asegura que la fecha de inicio en la línea del presupuesto (o la fecha de admisión seleccionada),
        el precio (fees) de la línea, y la fecha de inicio de cuotas (fees_start_date)
        se propaguen al registro de admisión cuando este es creado o recuperado.
        Asegura además que birth_date tenga un valor válido (evitando fallas de tipo al matricular).
        """
        admission = super(SaleOrder, self.with_context(irg_get_lot_line_id=line.id))._create_or_get_admission(line)
        if admission:
            vals = {}
            # Priorizamos la fecha de inicio de la línea (line.start_date_enroller),
            # y usamos self.admission_date (seleccionada en el wizard o guardada) como fallback.
            admission_date = line.start_date_enroller or self.admission_date

            if admission_date:
                modality = self._get_line_modality(line)
                today = fields.Date.today()
                if modality in ('HC', 'PRS') and today.day > 7 and admission_date.month == today.month and admission_date.year == today.year:
                    from dateutil.relativedelta import relativedelta
                    admission_date = admission_date + relativedelta(months=1)
                
                # HC Summer Period Rule: everything entering (or shifted to) between July and Sept 1st goes to September (09)
                if modality == 'HC':
                    if admission_date.month in (7, 8) or (admission_date.month == 9 and admission_date.day == 1):
                        admission_date = admission_date.replace(month=9, day=1)

                _logger.info(
                    "IRG Manual Wizard: Propagando admission_date %s y fees_start_date a la admisión %s desde línea/SO %s",
                    admission_date, admission.name, self.name
                )
                vals['admission_date'] = admission_date
                vals['fees_start_date'] = admission_date
            
            # Propagar el precio subtotal de la línea de presupuesto como tarifa de la admisión (fees)
            _logger.info(
                "IRG Manual Wizard: Propagando precio %s como fees a la admisión %s desde línea %s",
                line.price_subtotal, admission.name, line.id
            )
            vals['fees'] = line.price_subtotal

            # Recalcular el lote correcto para esta línea específica usando su producto, fecha y precio.
            correct_batch = self.with_context(irg_get_lot_line_id=line.id).get_lot_id(admission.course_id)
            if correct_batch and admission.batch_id != correct_batch:
                _logger.info(
                    "IRG Manual Wizard: Corrigiendo batch del default %s al específico de la línea %s",
                    admission.batch_id.name, correct_batch.name
                )
                vals['batch_id'] = correct_batch.id
            
            if not admission.birth_date:
                default_birth = self.partner_id.birth_date or fields.Date.to_date('2000-01-01')
                _logger.info(
                    "IRG Manual Wizard: Estableciendo birth_date %s en la admisión %s",
                    default_birth, admission.name
                )
                vals['birth_date'] = default_birth

            if vals:
                admission.write(vals)
        return admission

    def _find_or_create_register(self, *, period, product_template, course):
        """Override de isep_sale_order_admissions.
        Si estamos procesando una línea específica (pasada en contexto), calculamos el periodo
        en función de su fecha de inicio (start_date_enroller) en lugar de la del presupuesto general.
        """
        line_id = self.env.context.get('irg_get_lot_line_id')
        if line_id:
            line = self.env['sale.order.line'].browse(line_id)
            line_date = line.start_date_enroller
            if line_date:
                modality = self._get_line_modality(line)
                today = fields.Date.today()
                if modality in ('HC', 'PRS') and today.day > 7 and line_date.month == today.month and line_date.year == today.year:
                    from dateutil.relativedelta import relativedelta
                    line_date = line_date + relativedelta(months=1)
                
                # HC Summer Period Rule: everything entering (or shifted to) between July and Sept 1st goes to September (09)
                if modality == 'HC':
                    if line_date.month in (7, 8) or (line_date.month == 9 and line_date.day == 1):
                        line_date = line_date.replace(month=9, day=1)

                if 'code' in self.env['op.academic.term']._fields:
                    term = self.env['op.academic.term'].search([
                        ('term_start_date', '<=', line_date),
                        ('term_end_date', '>=', line_date)
                    ], limit=1)
                    if term:
                        period = f"{term.academic_year_id.name}-{term.code}"
                else:
                    # Fallback to standard isep_openeducat_sale logic
                    year = line_date.year
                    month = line_date.month
                    if month in (1, 2, 3, 4):
                        period = f'{year}-01'
                    elif month in (5, 6, 7):
                        period = f'{year}-02'
                    elif month in (8, 9, 10, 11, 12):
                        period = f'{year}-03'
                _logger.info(
                    "IRG Manual Wizard: Recalculando período del registro a %s para línea %s",
                    period, line.id
                )
        return super()._find_or_create_register(period=period, product_template=product_template, course=course)


    def _upsert_admission_row(self, line, *, register=None, admission=None,
                              course=None, product_template=None, error_msg=False):
        """Override de isep_sale_order_admissions.
        Asegura que la fecha de admisión de la línea se guarde como la de la línea de presupuesto
        (start_date_enroller) en lugar de la del presupuesto general.
        """
        # Forzar el line_id en el contexto para cualquier llamada anidada
        res = super(SaleOrder, self.with_context(irg_get_lot_line_id=line.id))._upsert_admission_row(
            line, register=register, admission=admission,
            course=course, product_template=product_template, error_msg=error_msg
        )
        if line.start_date_enroller:
            line_date = line.start_date_enroller
            modality = self._get_line_modality(line)
            today = fields.Date.today()
            if modality in ('HC', 'PRS') and today.day > 7 and line_date.month == today.month and line_date.year == today.year:
                from dateutil.relativedelta import relativedelta
                line_date = line_date + relativedelta(months=1)
            
            # HC Summer Period Rule: everything entering (or shifted to) between July and Sept 1st goes to September (09)
            if modality == 'HC':
                if line_date.month in (7, 8) or (line_date.month == 9 and line_date.day == 1):
                    line_date = line_date.replace(month=9, day=1)

            row = self.env['sale.order.admission.line'].search([
                ('order_id', '=', self.id),
                ('sale_line_id', '=', line.id),
            ], limit=1)
            if row and row.admission_date != line_date:
                row.write({'admission_date': line_date})
        return res

    def _process_auto_admission(self, admission, line):
        """Override de isep_sale_order_admissions.
        Cuando la confirmación proviene del asistente de confirmación manual,
        forzamos el flujo completo de estados de la admisión y el envío del correo,
        además de registrar la nota correspondiente en el chatter de la admisión.
        """
        if self.env.context.get('irg_manual_wizard_passed'):
            _logger.info(
                "IRG Manual Wizard: Forzando proceso de admisión manual para admisión %s",
                admission.name
            )
            # Ejecutamos el flujo completo de matriculación
            admission.submit_form()
            admission.confirm_in_progress()
            admission.admission_confirm()
            admission.enroll_student()
            
            # Forzamos el envío del correo de bienvenida usando send_mail_view
            if not admission.email_send_ok:
                admission.send_mail_view()
            
            # Postear nota explicativa en el chatter de la admisión
            admission.message_post(
                body=_("Admisión procesada, matriculada y confirmada mediante el Asistente de Confirmación Manual.")
            )
            return
            
        super()._process_auto_admission(admission, line)

    def _action_confirm(self):
        # Auto-correct product template flags if academic product is linked to a course but has flags set to False.
        # This guarantees standard admissions logic can find all lines correctly.
        for order in self:
            academic_lines = order.order_line.filtered(
                lambda l: (l.product_template_id.is_academic_program and l.product_template_id.recurring_invoice) or
                          self.env['op.course'].search_count([
                              '|',
                              ('product_template_id', '=', l.product_template_id.id),
                              ('product_template_ids', 'in', l.product_template_id.id)
                          ]) > 0
            )
            for line in academic_lines:
                pt = line.product_template_id.sudo()
                if not pt.is_academic_program or not pt.recurring_invoice:
                    _logger.info(
                        "IRG Manual Wizard: Autocorrigiendo flags de programa académico para %s",
                        pt.name
                    )
                    pt.write({
                        'is_academic_program': True,
                        'recurring_invoice': True,
                    })
        return super()._action_confirm()


