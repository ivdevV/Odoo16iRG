from odoo import api, fields, models
from odoo.tools.translate import _


class IrgCourseConvocatoria(models.Model):
    _name = 'irg.course.convocatoria'
    _description = 'Convocatoria de Curso (HomeClass / Online)'
    _order = 'modality, year desc, sequence, id'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Ejemplo: HomeClass 2026, Online Enero 2026',
    )
    modality = fields.Selection(
        selection=[('homeclass', 'HomeClass'), ('online', 'Online')],
        string='Modalidad',
        required=True,
        default='homeclass',
    )
    year = fields.Char(
        string='Año',
        help='Año de la convocatoria, p. ej. 2026',
    )
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(default=True)

    channel_id = fields.Many2one(
        'slide.channel',
        string='Curso',
        required=True,
        ondelete='cascade',
        index=True,
    )

    batch_ids = fields.Many2many(
        'op.batch',
        'irg_convocatoria_batch_rel',
        'convocatoria_id',
        'batch_id',
        string='Lotes',
        help='Lotes (op.batch) asociados a esta convocatoria',
    )

    # Solo relevante para modalidad Online
    online_variant_id = fields.Many2one(
        'product.product',
        string='Variante Online',
        help='Variante de producto con modalidad Online vinculada a este curso',
    )

    irg_section_ids = fields.One2many(
        'irg.slide.section',
        'convocatoria_id',
        string='Secciones',
    )

    section_count = fields.Integer(
        string='Secciones',
        compute='_compute_section_count',
    )

    @api.depends('irg_section_ids')
    def _compute_section_count(self):
        for conv in self:
            conv.section_count = len(conv.irg_section_ids)

    @api.onchange('modality', 'year')
    def _onchange_auto_name(self):
        """Sugiere un nombre automático cuando cambian modalidad o año."""
        if self.modality and self.year and not self.name:
            modality_label = dict(self._fields['modality'].selection).get(self.modality, '')
            self.name = _('%s %s') % (modality_label, self.year)
