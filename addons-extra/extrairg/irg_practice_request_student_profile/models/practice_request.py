# -*- coding: utf-8 -*-

from odoo import fields
from odoo import models


class PracticeRequest(models.Model):
    _inherit = 'practice.request'

    irg_age = fields.Integer(string='Edad')
    irg_academic_degrees = fields.Text(
        string='¿Qué grados académicos has obtenido? Indica institución y año.'
    )
    irg_postgraduate_training = fields.Text(
        string='¿Has realizado otra formación de posgrado? Indica programa, institución y año.'
    )
    irg_related_work_experience = fields.Text(
        string='Describe tu experiencia laboral, voluntariado o investigación relacionada con el área del Máster.'
    )
    irg_currently_working = fields.Text(
        string='¿Trabajas actualmente? Indica puesto, empresa y sector.'
    )
    irg_current_job_related_to_master = fields.Selection(
        selection=[
            ('yes', 'Sí'),
            ('no', 'No'),
            ('partial', 'Parcialmente'),
        ],
        string='¿Tu empleo actual se relaciona con el tema del Máster?',
    )
    irg_master_motivation = fields.Text(
        string='¿Cuál es tu motivación principal para cursar este Máster?'
    )
    irg_master_expectations = fields.Text(
        string='¿Qué expectativas tienes sobre el Máster?'
    )
    irg_long_term_professional_goals = fields.Text(
        string='¿Cuáles son tus objetivos profesionales a largo plazo?'
    )
    irg_topics_to_deepen = fields.Text(
        string='¿Qué temas te gustaría profundizar durante la práctica?'
    )
    irg_future_training_interest = fields.Text(
        string='¿Qué formación futura te interesaría realizar?'
    )
