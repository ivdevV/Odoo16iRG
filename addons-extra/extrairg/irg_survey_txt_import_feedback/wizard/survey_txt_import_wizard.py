import base64

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SurveyTxtImportWizard(models.TransientModel):
    _name = 'irg.survey.txt.import.wizard'
    _description = 'Wizard de importacion de preguntas tipo test desde TXT'

    survey_id = fields.Many2one('survey.survey', string='Encuesta', required=True)
    txt_file = fields.Binary(string='Archivo TXT', required=True)
    txt_filename = fields.Char(string='Nombre de archivo')
    preview_text = fields.Text(string='Vista previa', readonly=True)
    parsed_count = fields.Integer(string='Preguntas detectadas', readonly=True)
    sample_format = fields.Text(string='Formato', readonly=True, default=lambda self: self._default_sample())

    @api.model
    def _default_sample(self):
        return (
            'P: Que es Odoo?\n'
            'A: CRM\n'
            'B: ERP modular\n'
            'C: Navegador\n'
            'D: Hoja de calculo\n'
            'RC: B\n'
            'FG: Odoo es un ERP modular; CRM es solo una parte.\n\n'
            'P: Cuanto es 2+2?\n'
            'A: 3\n'
            'B: 5\n'
            'C: 4\n'
            'D: 6\n'
            'RC: C\n'
            'FG: La suma correcta de 2+2 es 4.'
        )

    def action_preview(self):
        self.ensure_one()
        parsed = self._parse_file()
        lines = []
        for idx, question in enumerate(parsed, start=1):
            lines.append(f"{idx}. {question['P']}")
            option_keys = sorted([k for k in question.keys() if len(k) == 1 and k.isupper() and k != 'P'])
            for option_key in option_keys:
                lines.append(f"   {option_key}) {question[option_key]}")
            lines.append(f"   RC: {question['RC']}")
            if question.get('FG'):
                lines.append(f"   FG: {question['FG']}")
            lines.append('')
        self.preview_text = '\n'.join(lines).strip()
        self.parsed_count = len(parsed)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        self.ensure_one()
        parsed = self._parse_file()
        question_model = self.env['survey.question']
        answer_model = self.env['survey.question.answer']

        q_fields = question_model._fields
        a_fields = answer_model._fields

        created = 0
        for question in parsed:
            question_vals = {
                'survey_id': self.survey_id.id,
                'title': question['P'],
                'question_type': 'simple_choice',
            }
            if 'is_scored_question' in q_fields:
                question_vals['is_scored_question'] = True
            if 'answer_score' in q_fields:
                question_vals['answer_score'] = 1.0
            if 'x_feedback_generic' in q_fields:
                question_vals['x_feedback_generic'] = question.get('FG') or False

            new_question = question_model.create(question_vals)

            option_keys = sorted([k for k in question.keys() if len(k) == 1 and k.isupper() and k != 'P'])
            for option_key in option_keys:
                answer_vals = {
                    'question_id': new_question.id,
                    'value': question[option_key],
                }
                if 'is_correct' in a_fields:
                    answer_vals['is_correct'] = (option_key == question['RC'])
                if 'answer_score' in a_fields:
                    answer_vals['answer_score'] = 1.0 if option_key == question['RC'] else 0.0
                answer_model.create(answer_vals)

            created += 1

        self.preview_text = _('Importacion completada. Preguntas creadas: %s') % created
        self.parsed_count = created
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _parse_file(self):
        self.ensure_one()
        if not self.txt_file:
            raise ValidationError(_('Debes adjuntar un archivo TXT.'))

        raw = base64.b64decode(self.txt_file)
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            raise ValidationError(_('El archivo debe estar codificado en UTF-8.'))

        blocks = [block.strip() for block in text.replace('\r\n', '\n').split('\n\n') if block.strip()]
        if not blocks:
            raise ValidationError(_('No se detectaron preguntas en el archivo.'))

        parsed = []
        required = {'P', 'RC'}

        for idx, block in enumerate(blocks, start=1):
            data = {}
            for line_no, line in enumerate(block.split('\n'), start=1):
                clean = line.strip()
                if not clean:
                    continue
                if ':' not in clean:
                    raise ValidationError(_('Pregunta %s, linea %s: formato invalido. Usa KEY: valor.') % (idx, line_no))
                key, value = clean.split(':', 1)
                key = key.strip().upper()
                value = value.strip()
                data[key] = value

            missing = sorted(required - set(data.keys()))
            if missing:
                raise ValidationError(_('Pregunta %s: faltan campos obligatorios: %s') % (idx, ', '.join(missing)))

            option_keys = sorted([k for k in data.keys() if len(k) == 1 and k.isupper() and k != 'P'])
            if len(option_keys) < 2:
                raise ValidationError(_('Pregunta %s: debe tener al menos dos opciones (A, B, ...).') % idx)

            expected_options = [chr(65 + i) for i in range(len(option_keys))]
            if option_keys != expected_options:
                raise ValidationError(_('Pregunta %s: las opciones deben ser consecutivas empezando por la A (e.g. %s).') % (idx, ', '.join(expected_options)))

            if data['RC'] not in option_keys:
                raise ValidationError(_('Pregunta %s: RC invalida (%s). Debe ser una de las opciones (%s).') % (idx, data['RC'], ', '.join(option_keys)))

            parsed.append(data)

        return parsed
