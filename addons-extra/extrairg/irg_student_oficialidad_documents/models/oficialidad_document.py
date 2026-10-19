# -*- coding: utf-8 -*-
from odoo import _, fields, models


class IrgOficialidadDocument(models.Model):
    _name = 'irg.oficialidad.document'
    _description = 'Documento de oficialidad IRG'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Documento', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Contacto',
        required=True,
        ondelete='cascade',
        index=True,
    )
    document_type_id = fields.Many2one(
        'irg.oficialidad.document.type',
        string='Tipo de documento',
        required=True,
        ondelete='restrict',
        index=True,
    )
    file = fields.Binary(string='Archivo', required=True, attachment=True)
    filename = fields.Char(string='Nombre de archivo', required=True)
    note = fields.Text(string='Observaciones')
    state = fields.Selection(
        selection=[
            ('submitted', 'Recibido'),
            ('accepted', 'Aceptado'),
            ('observed', 'Observado'),
        ],
        string='Estado',
        default='submitted',
        required=True,
    )

    _sql_constraints = [
        (
            'partner_document_type_uniq',
            'unique(partner_id, document_type_id)',
            'El contacto ya tiene un documento de este tipo.',
        ),
    ]

    def action_mark_submitted(self):
        self.write({'state': 'submitted'})

    def action_accept(self):
        self.write({'state': 'accepted'})

    def action_observe(self):
        self.write({'state': 'observed'})

    def name_get(self):
        result = []
        for document in self:
            label = document.name or _('Documento de oficialidad')
            if document.partner_id:
                label = '%s - %s' % (document.partner_id.display_name, label)
            result.append((document.id, label))
        return result
