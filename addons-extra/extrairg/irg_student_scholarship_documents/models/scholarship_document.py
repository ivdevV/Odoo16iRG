# -*- coding: utf-8 -*-

from odoo import _, fields, models


class IrgScholarshipDocument(models.Model):
    _name = 'irg.scholarship.document'
    _description = 'Documento de beca IRG'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Documento', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Contacto',
        required=True,
        ondelete='cascade',
        index=True,
    )
    scholarship_type_id = fields.Many2one(
        related='partner_id.irg_scholarship_type_id',
        string='Tipo de beca',
        store=True,
        readonly=True,
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

    def action_mark_submitted(self):
        self.write({'state': 'submitted'})

    def action_accept(self):
        self.write({'state': 'accepted'})

    def action_observe(self):
        self.write({'state': 'observed'})

    def name_get(self):
        result = []
        for document in self:
            label = document.name or _('Documento de beca')
            if document.partner_id:
                label = '%s - %s' % (document.partner_id.display_name, label)
            result.append((document.id, label))
        return result
