from odoo import fields, models, _
from odoo.exceptions import UserError


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    irg_tfm_template_only = fields.Boolean(
        string='Solo plantilla TFM',
        copy=False,
        help=(
            'Impide crear intentos nativos de Encuestas. Las preguntas se usan '
            'únicamente como plantilla editable del cuestionario de Esquema TFM.'
        ),
    )

    def _create_answer(
        self,
        user=False,
        partner=False,
        email=False,
        test_entry=False,
        check_attempts=True,
        **additional_vals
    ):
        if any(self.mapped('irg_tfm_template_only')):
            raise UserError(_(
                'Esta encuesta es una plantilla TFM y no admite respuestas '
                'por las rutas nativas de Encuestas.'
            ))
        return super()._create_answer(
            user=user,
            partner=partner,
            email=email,
            test_entry=test_entry,
            check_attempts=check_attempts,
            **additional_vals
        )
