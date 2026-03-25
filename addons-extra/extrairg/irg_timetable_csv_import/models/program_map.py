# -*- coding: utf-8 -*-
from odoo import _, fields, models


class IrgTimetableProgramMap(models.Model):
    """Tabla de equivalencias entre etiqueta CSV y curso/lote de Odoo.

    Ejemplo:
        csv_label  = "Calendario NC 365"
        course_id  = Máster en Neuropsicología Clínica… (código MNC)
        batch_id   = lote 2025-2026 (opcional; si vacío → todos los lotes activos)
    """

    _name = 'irg.timetable.program.map'
    _description = 'Mapeo etiqueta CSV → Curso/Lote Odoo'
    _order = 'csv_label'

    csv_label = fields.Char(
        string=_('Etiqueta CSV'),
        required=True,
        help='Texto exacto que aparece en la columna Máster/Programa del CSV '
             '(ej: "Calendario NC 365").',
    )
    course_id = fields.Many2one(
        'op.course',
        string=_('Curso'),
        required=True,
        ondelete='restrict',
    )
    batch_id = fields.Many2one(
        'op.batch',
        string=_('Lote específico'),
        domain="[('course_id','=',course_id)]",
        help='Deja vacío para asignar sesiones a todos los lotes activos del curso.',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('csv_label_uniq', 'unique(csv_label)', 'La etiqueta CSV debe ser única.'),
    ]
