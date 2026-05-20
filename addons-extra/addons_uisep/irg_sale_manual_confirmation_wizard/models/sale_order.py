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
            lambda l: l.product_template_id.is_academic_program and l.product_template_id.recurring_invoice
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

    def _create_or_get_admission(self, line):
        """Override de isep_sale_order_admissions.
        Asegura que la fecha de inicio en la línea del presupuesto (o la fecha de admisión seleccionada)
        se propague al registro de admisión cuando este es creado o recuperado.
        Asegura además que birth_date tenga un valor válido (evitando fallas de tipo al matricular).
        """
        admission = super()._create_or_get_admission(line)
        if admission:
            vals = {}
            # Si el flujo viene del wizard manual, respetamos la fecha del wizard (self.admission_date).
            # En caso contrario, priorizamos la fecha de inicio de la línea (line.start_date_enroller).
            if self.env.context.get('irg_manual_wizard_passed'):
                admission_date = self.admission_date
            else:
                admission_date = line.start_date_enroller or self.admission_date

            if admission_date:
                _logger.info(
                    "IRG Manual Wizard: Propagando admission_date %s a la admisión %s desde línea/SO %s",
                    admission_date, admission.name, self.name
                )
                vals['admission_date'] = admission_date
            
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


