# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


# Mapeo mes -> (numero_trimestre, mes_inicio_trimestre)
QUARTER_MAP = {
    1: ('1', 1), 2: ('1', 1), 3: ('1', 1),
    4: ('2', 4), 5: ('2', 4), 6: ('2', 4),
    7: ('3', 7), 8: ('3', 7), 9: ('3', 7),
    10: ('4', 10), 11: ('4', 10), 12: ('4', 10),
}


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_lot_id(self, course_id):
        """Override de irg_openeducat_sale_lote_custom.

        Solo modifica la logica cuando la modalidad detectada es Online (ONL).
        Para HC/PRS/GE delega 100% en el comportamiento del super().
        """
        ad = self.env['auto.admission.required'].search([], limit=1)
        if not ad or not ad.quarterly_online_enabled:
            return super().get_lot_id(course_id)

        # Retrieve line from context if available
        line_id = self.env.context.get('irg_get_lot_line_id')
        line = self.env['sale.order.line'].browse(line_id) if line_id else None

        is_online = False
        matching_line = line

        if matching_line:
            is_online = self._irg_quarterly_line_is_online(matching_line)
        else:
            for l in self.order_line:
                if self._irg_quarterly_line_matches(l, course_id):
                    if self._irg_quarterly_line_is_online(l):
                        is_online = True
                        matching_line = l
                        break

        if not is_online:
            return super().get_lot_id(course_id)

        _logger.info("IRG Quarterly: rama trimestral activada para curso %s con linea %s", course_id.name, matching_line)

        # Resolve date: prioritize matching_line.start_date_enroller, fallback to self.admission_date, fallback to today
        date = False
        if matching_line:
            date = matching_line.start_date_enroller
        if not date:
            date = self.admission_date
        if not date:
            date = fields.Date.today()

        # Categoria (prefix_01) - misma logica que el super
        profix_01 = ''
        if course_id.product_template_id:
            profix_01 = course_id.product_template_id.categ_id.code or ''
        elif hasattr(course_id, 'product_template_ids') and course_id.product_template_ids:
            profix_01 = course_id.product_template_ids[0].categ_id.code or ''
        
        if matching_line and matching_line.product_id.categ_id.code:
            profix_01 = matching_line.product_id.categ_id.code

        # Check if bonificado (price <= 0) - ONLY FOR ONL modality
        if matching_line and (matching_line.price_unit <= 0 or matching_line.price_subtotal <= 0):
            if profix_01.startswith('M'):
                profix_01 = 'M' + 'B' + profix_01[1:]

        prefix_011 = course_id.code or ''
        prefix_02 = 'ONL'

        quarter_letter, quarter_start_month = QUARTER_MAP[date.month]
        year = date.strftime("%y")

        # Codigo: {categ}{curso}ONL{YY}{LETRA}  ej. MX123ONL25A
        code = profix_01 + prefix_011 + prefix_02 + year + quarter_letter
        _logger.info("IRG Quarterly: codigo trimestral generado: %s", code)

        op_batch = self.env['op.batch']
        lot_id = op_batch.search([('code', '=', code)], limit=1)
        if lot_id:
            _logger.info("IRG Quarterly: lote trimestral existente reusado: %s", lot_id.name)
            if not lot_id.tutor_id:
                vals_to_write = {}
                if course_id.lang == 'pt_BR':
                    vals_to_write.update({
                        'tutor_id': ad.br_tutor_id.id if ad.br_tutor_id else False,
                        'professor_id': ad.br_professor_id.id if ad.br_professor_id and not lot_id.professor_id else False,
                        'coordinator': ad.br_coordinator.id if ad.br_coordinator and not lot_id.coordinator else False,
                    })
                else:
                    vals_to_write.update({
                        'tutor_id': ad.mx_tutor_id.id if ad.mx_tutor_id else False,
                        'professor_id': ad.mx_professor_id.id if ad.mx_professor_id and not lot_id.professor_id else False,
                        'coordinator': ad.mx_coordinator.id if ad.mx_coordinator and not lot_id.coordinator else False,
                    })
                vals_to_write = {k: v for k, v in vals_to_write.items() if v}
                if vals_to_write:
                    _logger.info("IRG Quarterly: auto-completando tutor/profesor/coordinador del lote existente %s con: %s", lot_id.name, vals_to_write)
                    lot_id.write(vals_to_write)
            return lot_id

        # Crear lote nuevo con valores del singleton segun idioma
        lot_values = {}
        if course_id.lang == 'pt_BR':
            lot_values.update({
                'tutor_id': ad.br_tutor_id.id if ad.br_tutor_id else False,
                'professor_id': ad.br_professor_id.id if ad.br_professor_id else False,
                'coordinator': ad.br_coordinator.id if ad.br_coordinator else False,
                'teams_domain': ad.br_teams_domain if ad.br_teams_domain else False,
                'teams_link': ad.br_teams_link if ad.br_teams_link else False,
                'teams_msg': ad.br_teams_msg if ad.br_teams_msg else False,
                'modality_id': ad.br_modality_id.id if ad.br_modality_id else False,
            })
        else:
            lot_values.update({
                'tutor_id': ad.mx_tutor_id.id if ad.mx_tutor_id else False,
                'professor_id': ad.mx_professor_id.id if ad.mx_professor_id else False,
                'coordinator': ad.mx_coordinator.id if ad.mx_coordinator else False,
                'teams_domain': ad.mx_teams_domain if ad.mx_teams_domain else False,
                'teams_link': ad.mx_teams_link if ad.mx_teams_link else False,
                'teams_msg': ad.mx_teams_msg if ad.mx_teams_msg else False,
                'modality_id': ad.mx_modality_id.id if ad.mx_modality_id else False,
            })

        batch_start_date = date.replace(day=1, month=quarter_start_month)
        
        course_code = (course_id.code or '').strip().upper()
        duration_months = 24 if course_code == 'NC' else 16
        batch_end_date = batch_start_date + relativedelta(months=duration_months, days=-1)

        lot_values.update({
            'name': code,
            'code': code,
            'course_id': course_id.id,
            'start_date': batch_start_date,
            'end_date': batch_end_date,
            'date_start_class': batch_start_date,
        })
        _logger.info("IRG Quarterly: creando lote trimestral %s (%s -> %s)",
                     code, batch_start_date, batch_end_date)
        return op_batch.create(lot_values)

    # ----------------------------------------------------------------
    # Helpers internos
    # ----------------------------------------------------------------

    def _irg_quarterly_line_matches(self, line, course_id):
        if hasattr(line.product_id, 'course_id') and line.product_id.course_id.id == course_id.id:
            return True
        if course_id.product_template_id and line.product_id.product_tmpl_id.id == course_id.product_template_id.id:
            return True
        if hasattr(course_id, 'product_template_ids') and line.product_id.product_tmpl_id.id in course_id.product_template_ids.ids:
            return True
        return False

    def _irg_quarterly_is_online_course(self, course_id):
        """True si la linea que matchea el curso tiene atributo Modalidad = Online."""
        for line in self.order_line:
            if not self._irg_quarterly_line_matches(line, course_id):
                continue
            if self._irg_quarterly_line_is_online(line):
                return True
        return False

    def _irg_quarterly_line_is_online(self, line):
        """True si la linea tiene atributo Modalidad = Online."""
        for ptav in line.product_id.product_template_attribute_value_ids:
            if ptav.attribute_id.name == 'Modalidad':
                val_name = (ptav.product_attribute_value_id.name or '').strip()
                return val_name == 'Online'
        return False
