# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def action_get_books(self): 
        try:         
            # Encuestas / Cuestionarios / Certificaciones / Exámenes / Tareas
            result = self.env['survey.user_input'].search([                
                ('survey_type', 'in', ['exam', 'assignment', 'survey', 'cert']),
                ('state', '=', 'done'),
                ('test_entry', '=', False),
                ('send_to_book', '=', False)
            ])  
            _logger.info('action_get_books enviando %s resultados a libreta', len(result))  
           
            for rs in result: 
                rs.send_result()                
        except Exception as e:
            _logger.error('ERROR AL TRATAR DE PASAR A LIBRETA: %s', str(e))
