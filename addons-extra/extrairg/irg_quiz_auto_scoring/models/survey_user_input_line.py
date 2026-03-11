from odoo import models


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    def _get_selected_answer(self):
        self.ensure_one()
        line = self
        if hasattr(line, 'answer_id') and line.answer_id:
            return line.answer_id
        if hasattr(line, 'suggested_answer_id') and line.suggested_answer_id:
            return line.suggested_answer_id
        if hasattr(line, 'value_answer_id') and line.value_answer_id:
            return line.value_answer_id
        if hasattr(line, 'value_answer_ids') and line.value_answer_ids:
            return line.value_answer_ids[0]
        val_text = getattr(line, 'value_text', False) or getattr(line, 'value', False) or None
        if val_text and getattr(line, 'question_id', False):
            for a in line.question_id.suggested_answer_ids:
                if (a.name or '').strip() == (val_text or '').strip():
                    return a
        return None

    def _fill_answer_score_from_selected(self):
        to_write = []
        for line in self:
            try:
                has_correct_flag = getattr(line, 'answer_is_correct', False) or getattr(line, 'is_correct', False) or getattr(line, 'correct', False)
            except Exception:
                has_correct_flag = False
            if not has_correct_flag:
                continue
            # Permitir actualizar score incluso si ya existe (para recálculos)
            ans = line._get_selected_answer()
            if ans:
                to_write.append((line, ans.answer_score or 0.0))

        for line, score in to_write:
            try:
                line.sudo().write({'answer_score': score})
            except Exception:
                # best-effort: ignore failures
                continue

    def write(self, vals):
        res = super(SurveyUserInputLine, self).write(vals)
        try:
            self._fill_answer_score_from_selected()
        except Exception:
            pass
        return res

    def create(self, vals_list):
        records = super(SurveyUserInputLine, self).create(vals_list)
        try:
            records._fill_answer_score_from_selected()
        except Exception:
            pass
        return records
