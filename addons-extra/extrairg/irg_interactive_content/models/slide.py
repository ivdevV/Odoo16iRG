# -*- coding: utf-8 -*-
import json

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html_sanitize


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    x_is_interactive = fields.Boolean(string='Is Interactive', copy=False)
    x_interactive_json = fields.Text(string='Interactive JSON', copy=False)
    x_original_slide_id = fields.Many2one(
        'slide.slide',
        string='Original PDF Slide',
        ondelete='set null',
        copy=False,
    )

    def _load_interactive_json(self):
        self.ensure_one()
        payload = self.x_interactive_json or '{}'
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def _get_interactive_payload(self):
        self.ensure_one()
        data = self._load_interactive_json()

        flashcards = data.get('flashcards') if isinstance(data.get('flashcards'), list) else []
        quiz = data.get('quiz') if isinstance(data.get('quiz'), list) else []
        mermaid_code = data.get('mermaid_code') if isinstance(data.get('mermaid_code'), str) else ''
        content_html = data.get('content_html') if isinstance(data.get('content_html'), str) else ''

        normalized_flashcards = []
        for card in flashcards:
            if isinstance(card, dict):
                normalized_flashcards.append({
                    'term': card.get('term', ''),
                    'definition': card.get('definition', ''),
                })

        normalized_quiz = []
        for question in quiz:
            if not isinstance(question, dict):
                continue
            options = question.get('options') if isinstance(question.get('options'), list) else []
            clean_options = [option for option in options if isinstance(option, str)]
            correct_answer = question.get('correct_answer', '')
            correct_index = clean_options.index(correct_answer) if correct_answer in clean_options else -1
            normalized_quiz.append({
                'question': question.get('question', ''),
                'options': clean_options,
                'correct_answer': correct_answer,
                'correct_index': correct_index,
            })

        return {
            'mermaid_code': mermaid_code,
            'flashcards': normalized_flashcards,
            'content_html': html_sanitize(content_html),
            'quiz': normalized_quiz,
        }

    def _is_valid_interactive_json(self):
        self.ensure_one()
        if not self.x_interactive_json:
            return True
        try:
            decoded = json.loads(self.x_interactive_json)
        except json.JSONDecodeError:
            return False
        return isinstance(decoded, dict)

    def _validate_interactive_json(self):
        for slide in self:
            if not slide._is_valid_interactive_json():
                raise ValidationError(
                    _('The field "Interactive JSON" must contain a valid JSON object.')
                )

    def create(self, vals_list):
        records = super().create(vals_list)
        records._validate_interactive_json()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._validate_interactive_json()
        return result
