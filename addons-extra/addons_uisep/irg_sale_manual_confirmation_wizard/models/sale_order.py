# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_course_product_domain(self, product_template):
        domain = [('product_template_id', '=', product_template.id)]
        if 'product_template_ids' in self.env['op.course']._fields:
            domain = ['|'] + domain + [('product_template_ids', 'in', product_template.id)]
        return domain

    def _is_academic_line(self, line):
        if line.price_unit < 0 or line.price_subtotal < 0:
            return False
        pt = line.product_template_id
        if not pt:
            return False
        # 1. Standard flags
        if pt.is_academic_program:
            return True
        # 2. Linked to an op.course
        if self.env['op.course'].search_count(self._get_course_product_domain(pt)) > 0:
            return True
        # 3. Linked to the order's course
        if line.order_id and line.order_id.course_id:
            course = line.order_id.course_id
            if pt.id in (course.product_template_id + course.product_template_ids).ids:
                return True
        # 4. Category code starts with DI or category name contains DIPLOMADO (case insensitive)
        categ = pt.categ_id
        if categ:
            if categ.code and categ.code.upper().startswith('DI'):
                return True
            if categ.name and 'DIPLOMADO' in categ.name.upper():
                return True
        # 5. Product name contains DIPLOMADO (case insensitive)
        if pt.name and 'DIPLOMADO' in pt.name.upper():
            return True
        return False

    def action_open_manual_confirmation_wizard(self):
        """Boton manual: abre wizard de validacion antes de confirmar."""
        self.ensure_one()
        # Asegurar que se calculan curso_id y product_template_id en el presupuesto
        self.get_academic_product_template_id()
        
        default_date = fields.Date.context_today(self)
            
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
        categ_name = False
        pt = line.product_template_id
        if pt and pt.categ_id:
            categ_code = pt.categ_id.code
            categ_name = pt.categ_id.name

        is_diplomado = False
        if categ_code and categ_code.upper().startswith('DI'):
            is_diplomado = True
        elif categ_name and 'DIPLOMADO' in categ_name.upper():
            is_diplomado = True
        elif pt and pt.name and 'DIPLOMADO' in pt.name.upper():
            is_diplomado = True

        if not is_diplomado:
            # Fallback check on course categories
            domain = self._get_course_product_domain(line.product_template_id)
            course = self.env['op.course'].search(domain, limit=1)
            if not course and line.order_id and line.order_id.course_id:
                course = line.order_id.course_id
            
            if course:
                if course.product_template_id and course.product_template_id.categ_id:
                    ccode = course.product_template_id.categ_id.code
                    cname = course.product_template_id.categ_id.name
                    if ccode and ccode.upper().startswith('DI'):
                        is_diplomado = True
                    elif cname and 'DIPLOMADO' in cname.upper():
                        is_diplomado = True
                if not is_diplomado and hasattr(course, 'product_template_ids') and course.product_template_ids:
                    for cpt in course.product_template_ids:
                        if cpt.categ_id:
                            if cpt.categ_id.code and cpt.categ_id.code.upper().startswith('DI'):
                                is_diplomado = True
                                break
                            if cpt.categ_id.name and 'DIPLOMADO' in cpt.categ_id.name.upper():
                                is_diplomado = True
                                break

        if is_diplomado:
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
        domain = self._get_course_product_domain(line.product_template_id)
        course = self.env['op.course'].search(domain, limit=1)

        ctx = {'irg_get_lot_line_id': line.id}
        if not self.auto_ad_active(course) and not self.env.context.get('irg_manual_wizard_passed'):
            ctx['irg_no_create_batch'] = True

        admission = super(SaleOrder, self.with_context(**ctx))._create_or_get_admission(line)
        if admission:
            vals = {}
            # La fecha de admision es la fecha real de confirmacion; la fecha de
            # inicio de clases se conserva aparte en irg_class_start_date.
            admission_date = fields.Date.context_today(self)

            if admission_date:
                _logger.info(
                    "IRG Manual Wizard: Propagando admission_date %s a la admisión %s desde confirmación SO %s",
                    admission_date, admission.name, self.name
                )
                vals['admission_date'] = admission_date
                if line.start_date_enroller:
                    vals['fees_start_date'] = line.start_date_enroller
                else:
                    vals['fees_start_date'] = admission_date
            
            # Propagar el precio subtotal de la línea de presupuesto como tarifa de la admisión (fees)
            _logger.info(
                "IRG Manual Wizard: Propagando precio %s como fees a la admisión %s desde línea %s",
                line.price_subtotal, admission.name, line.id
            )
            vals['fees'] = line.price_subtotal

            # Recalcular el lote correcto para esta línea específica usando su producto, fecha y precio.
            correct_batch = self.with_context(**ctx).get_lot_id(admission.course_id)
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

            if line.start_date_enroller:
                vals['irg_class_start_date'] = line.start_date_enroller

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
        Register = self.env['op.admission.register']
        periods = [period]
        if '-' in period:
            parts = period.split('-')
            if len(parts) == 2:
                year, term_code = parts
                if term_code.startswith('0') and len(term_code) > 1:
                    periods.append(f"{year}-{term_code[1:]}")
                elif not term_code.startswith('0'):
                    periods.append(f"{year}-0{term_code}")

        reg = Register.search([
            ('course_id', '=', course.id),
            ('period', 'in', periods),
            ('state', 'in', ['confirm', 'application', 'admission']),
        ], limit=1)

        if reg:
            if reg.state == 'confirm':
                reg.start_application()
            _logger.info(
                "IRG Manual Wizard: Reutilizando registro de admision existente %s para curso %s y periodo %s (buscado con %s)",
                reg.name, course.name, reg.period, period
            )
            return reg

        try:
            end_date = self.gat_date_max_register(period)
            today = fields.Date.today()
            if end_date and today > end_date:
                _logger.warning(
                    "IRG Manual Wizard: Creando registro de admision anticipadamente para periodo vencido %s. "
                    "Fecha fin (%s) anterior a hoy (%s). Forzando start_date = end_date.",
                    period, end_date, today
                )
                reg = Register.create({
                    'course_id': course.id,
                    'name': f"{period} {course.name}",
                    'min_count': 1,
                    'max_count': 500,
                    'period': period,
                    'start_date': end_date,
                    'end_date': end_date,
                    'product_template_id': product_template.id,
                })
                reg.start_application()
                return reg
        except Exception as e:
            _logger.warning(
                "IRG Manual Wizard: Fallo al pre-crear registro de admision para evitar ValidationError: %s", e
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
            academic_lines = order.order_line.filtered(lambda l: self._is_academic_line(l))
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

    def auto_ad_active(self, course=None):
        """Desactiva la automatrícula si el idioma del curso es es_ES (España)."""
        res = super().auto_ad_active(course)
        lang = course.lang if course else (self.course_id.lang if self.course_id else False)
        if lang == 'es_ES':
            return False
        return res
