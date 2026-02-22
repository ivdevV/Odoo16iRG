from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    irg_section_id = fields.Many2one(
        'irg.slide.section',
        string='Sección iRG',
        ondelete='set null',
        help='Sección personalizada iRG para organizar contenidos sin depender de secciones nativas.',
    )

    parent_slide_id = fields.Many2one(
        'slide.slide',
        string='Elemento padre',
        domain="[('channel_id', '=', channel_id), ('id', '!=', id)]",
        ondelete='set null',
        help='Permite organizar contenidos como elementos hijos dentro del mismo curso.'
    )

    child_slide_ids = fields.One2many(
        'slide.slide',
        'parent_slide_id',
        string='Elementos hijos'
    )

    inherit_limitations_from_parent = fields.Boolean(
        string='Heredar límites del padre',
        default=True,
        help='Si está activo, copiará automáticamente lote permitido y fecha programada del elemento padre cuando estén vacíos.'
    )

    @api.onchange('parent_slide_id', 'inherit_limitations_from_parent')
    def _onchange_parent_slide_apply_limitations(self):
        for slide in self:
            parent_slide = slide.parent_slide_id
            if not parent_slide:
                continue

            if parent_slide.is_category:
                slide.category_id = parent_slide
            elif parent_slide.category_id:
                slide.category_id = parent_slide.category_id

            if slide.inherit_limitations_from_parent:
                if not slide.allowed_batch_ids and parent_slide.allowed_batch_ids:
                    slide.allowed_batch_ids = [(6, 0, parent_slide.allowed_batch_ids.ids)]
                if not slide.scheduled_date and parent_slide.scheduled_date:
                    slide.scheduled_date = parent_slide.scheduled_date

    @api.onchange('category_id')
    def _onchange_category_id_set_parent(self):
        for slide in self:
            if slide.category_id:
                slide.parent_slide_id = slide.category_id

    @api.constrains('irg_section_id', 'channel_id')
    def _check_irg_section_channel(self):
        for slide in self:
            if slide.irg_section_id and slide.channel_id and slide.irg_section_id.channel_id != slide.channel_id:
                raise ValidationError('La sección iRG debe pertenecer al mismo curso que el contenido.')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._apply_parent_hierarchy()
        records._apply_parent_limitations(only_empty=True)
        return records

    def write(self, vals):
        res = super().write(vals)
        if {'parent_slide_id', 'category_id', 'inherit_limitations_from_parent'} & set(vals):
            self._apply_parent_hierarchy()
            self._apply_parent_limitations(only_empty=True)
        return res

    def _apply_parent_hierarchy(self):
        for slide in self.filtered(lambda s: s.parent_slide_id):
            updates = {}
            parent_slide = slide.parent_slide_id.sudo()

            if parent_slide.is_category:
                updates['category_id'] = parent_slide.id
            elif parent_slide.category_id:
                updates['category_id'] = parent_slide.category_id.id

            if updates and (
                ('category_id' in updates and slide.category_id.id != updates['category_id'])
            ):
                super(SlideSlide, slide).write(updates)

    def _apply_parent_limitations(self, only_empty=True):
        for slide in self.filtered(lambda s: s.parent_slide_id and s.inherit_limitations_from_parent):
            updates = {}
            parent_slide = slide.parent_slide_id.sudo()

            if parent_slide.allowed_batch_ids and (not only_empty or not slide.allowed_batch_ids):
                updates['allowed_batch_ids'] = [(6, 0, parent_slide.allowed_batch_ids.ids)]

            if parent_slide.scheduled_date and (not only_empty or not slide.scheduled_date):
                updates['scheduled_date'] = parent_slide.scheduled_date

            if updates:
                super(SlideSlide, slide).write(updates)
