from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    irg_tfm_convocation_ids = fields.Many2many(
        'irg.tfm.convocatoria',
        'slide_slide_tfm_convocation_rel',
        'slide_id',
        'convocation_id',
        string='Convocatorias TFM',
        copy=True,
        help=(
            'Solo las categorías pueden configurar convocatorias. El contenido '
            'hereda la restricción efectiva de su categoría o padre; vacío '
            'significa contenido común dentro del canal TFM.'
        ),
    )

    def _irg_require_internal_tfm_convocation_edit(self, values):
        if (
            'irg_tfm_convocation_ids' in values
            and not self.env.user.has_group('base.group_user')
        ):
            raise AccessError(_(
                'Only internal users can configure TFM convocations.',
            ))

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            self._irg_require_internal_tfm_convocation_edit(values)
        return super().create(vals_list)

    def write(self, vals):
        self._irg_require_internal_tfm_convocation_edit(vals)
        return super().write(vals)

    @api.constrains('irg_tfm_convocation_ids', 'is_category')
    def _check_tfm_convocations_only_on_categories(self):
        for slide in self:
            if slide.irg_tfm_convocation_ids and not slide.is_category:
                raise ValidationError(_(
                    'TFM convocations can only be configured on eLearning categories.'
                ))

    def _irg_effective_tfm_convocation_ids(self):
        """Return the category-level TFM restriction inherited by this slide."""
        self.ensure_one()
        slide = self.sudo()
        if slide.is_category and slide.irg_tfm_convocation_ids:
            return slide.irg_tfm_convocation_ids
        if slide.is_category and slide.irg_original_slide_id:
            original = slide.irg_original_slide_id.sudo()
            homeclass = slide.channel_id.sudo().irg_homeclass_channel_id
            if original.is_category and homeclass and original.channel_id == homeclass:
                return original.irg_tfm_convocation_ids
            return self.env['irg.tfm.convocatoria']
        category = slide.category_id.sudo()
        if category:
            return category._irg_effective_tfm_convocation_ids()
        parent = slide.parent_slide_id.sudo()
        if parent:
            return parent._irg_effective_tfm_convocation_ids()
        return self.env['irg.tfm.convocatoria']

    def _irg_tfm_invalid_clone_origin(self):
        self.ensure_one()
        slide = self.sudo()
        if slide.is_category and slide.irg_original_slide_id:
            original = slide.irg_original_slide_id.sudo()
            homeclass = slide.channel_id.sudo().irg_homeclass_channel_id
            return not (
                original.is_category
                and homeclass
                and original.channel_id == homeclass
            )
        if slide.category_id:
            return slide.category_id._irg_tfm_invalid_clone_origin()
        if slide.parent_slide_id:
            return slide.parent_slide_id._irg_tfm_invalid_clone_origin()
        return False

    def irg_has_tfm_requirement(self):
        self.ensure_one()
        return bool(
            self._irg_tfm_invalid_clone_origin()
            or self._irg_effective_tfm_convocation_ids()
        )

    def _irg_tfm_current_convocation_for_user(self, user, channel=None):
        """Resolve one portal enrollment and its one active TFM record.

        This deliberately does not inspect slide memberships. A membership is
        useful to the generic eLearning stack, but it is not evidence that the
        portal user owns the current TFM enrollment.
        """
        self.ensure_one()
        user = user or self.env.user
        if not user or user._is_public() or user.has_group('base.group_user'):
            return self.env['irg.tfm.convocatoria']

        channel = (channel or self.sudo().channel_id).sudo()
        if not channel:
            return self.env['irg.tfm.convocatoria']
        thesis, effective_channel = channel._irg_tfm_route_for_user(user)
        if not thesis or effective_channel != channel:
            return self.env['irg.tfm.convocatoria']
        return thesis.irg_tfm_convocation_id

    def is_user_allowed_by_tfm_convocation(self, user=None):
        """Fail closed for portal users when a category is exclusive."""
        self.ensure_one()
        user = user or self.env.user
        if user and user.has_group('base.group_user'):
            return True
        if not user or user._is_public():
            return False
        if self._irg_tfm_invalid_clone_origin():
            return False

        required = self._irg_effective_tfm_convocation_ids()
        if not required:
            return True

        current = self._irg_tfm_current_convocation_for_user(user)
        return bool(current and current.id in required.ids)
