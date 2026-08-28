# -*- coding: utf-8 -*-
import base64
import hashlib

from odoo.exceptions import UserError
from odoo.tools.translate import _

from . import api_serializer as ser
from .api_constants import MAX_ATTACHMENT_BYTES, MAX_TITLE_CHARS


class SurveyService:

    def __init__(self, env):
        self.env = env

    def _survey(self, survey_id):
        if 'survey.survey' not in self.env:
            raise UserError(_('Surveys are not installed.'))
        survey = self.env['survey.survey'].browse(survey_id)
        if not survey.exists():
            raise UserError(_('Unknown survey id %s.') % survey_id)
        return survey

    def preview_create_survey_draft(self, payload):
        title = (payload.get('title') or '').strip()
        if not title:
            raise UserError(_('title is required.'))
        if len(title) > MAX_TITLE_CHARS:
            raise UserError(_('title exceeds %s characters.') % MAX_TITLE_CHARS)
        before = {'survey_count': self.env['survey.survey'].search_count([])}
        proposed = {'title': title, 'state': 'draft'}
        return before, proposed, {'model': 'survey.survey', 'id': False}

    def apply_create_survey_draft(self, proposed, before):
        vals = {'title': proposed['title']}
        Survey = self.env['survey.survey']
        if 'state' in Survey._fields:
            vals['state'] = 'draft'
        survey = Survey.create(vals)
        return {'id': survey.id, 'title': survey.title}

    def preview_update_survey_draft(self, payload):
        survey = self._survey(ser.require_positive_id(payload, 'survey_id'))
        if 'state' in survey._fields and survey.state not in (False, 'draft', 'new'):
            raise UserError(_('Only draft surveys can be updated.'))
        title = (payload.get('title') or survey.title or '').strip()
        if not title:
            raise UserError(_('title is required.'))
        before = {'id': survey.id, 'title': survey.title}
        proposed = {'id': survey.id, 'title': title}
        return before, proposed, {'model': 'survey.survey', 'id': survey.id}

    def apply_update_survey_draft(self, proposed, before):
        survey = self._survey(proposed['id'])
        if survey.title != before.get('title'):
            raise UserError(_('The survey changed after preview.'))
        survey.write({'title': proposed['title']})
        return {'id': survey.id, 'title': survey.title}

    def describe_auto_score(self, payload):
        survey = self._survey(ser.require_positive_id(payload, 'survey_id'))
        questions = survey.question_ids.filtered(
            lambda question: question.question_type not in ['section_heading']
        ) if 'question_ids' in survey._fields else survey.env['survey.question']
        return {
            'survey_id': survey.id,
            'question_count': len(questions),
            'will_call': 'action_auto_score_quiz',
        }

    def preview_apply_auto_score(self, payload):
        plan = self.describe_auto_score(payload)
        return plan, dict(plan), {'model': 'survey.survey', 'id': plan['survey_id']}

    def apply_auto_score(self, proposed, before):
        survey = self._survey(proposed['survey_id'])
        if not hasattr(survey, 'action_auto_score_quiz'):
            raise UserError(_('Auto-score is not available.'))
        survey.action_auto_score_quiz()
        return {'survey_id': survey.id, 'applied': True}

    def describe_regrade(self, payload):
        if 'survey.user_input' not in self.env:
            raise UserError(_('Survey attempts are not installed.'))
        attempt = self.env['survey.user_input'].browse(
            ser.require_positive_id(payload, 'user_input_id')
        )
        if not attempt.exists():
            raise UserError(_('Unknown attempt id.'))
        return {
            'user_input_id': attempt.id,
            'scoring_total': attempt.scoring_total if 'scoring_total' in attempt._fields else False,
            'will_call': '_regrade_single_attempt',
        }

    def preview_apply_regrade(self, payload):
        plan = self.describe_regrade(payload)
        return plan, dict(plan), {'model': 'survey.user_input', 'id': plan['user_input_id']}

    def apply_regrade(self, proposed, before):
        attempt = self.env['survey.user_input'].browse(proposed['user_input_id'])
        if not hasattr(attempt, '_regrade_single_attempt'):
            raise UserError(_('Regrade is not available.'))
        attempt._regrade_single_attempt()
        return {
            'user_input_id': attempt.id,
            'scoring_total': attempt.scoring_total if 'scoring_total' in attempt._fields else False,
        }

    def describe_feedback_import(self, payload):
        survey = self._survey(ser.require_positive_id(payload, 'survey_id'))
        txt_content = payload.get('txt_content') or ''
        if not isinstance(txt_content, str) or not txt_content.strip():
            raise UserError(_('txt_content is required.'))
        digest = hashlib.sha256(txt_content.encode('utf-8')).hexdigest()
        question_count = txt_content.count('\nP:') + (1 if txt_content.lstrip().startswith('P:') else 0)
        return {
            'survey_id': survey.id,
            'txt_hash': digest,
            'approx_questions': question_count,
            'txt_content': txt_content,
        }

    def preview_apply_feedback_import(self, payload):
        plan = self.describe_feedback_import(payload)
        return {'survey_id': plan['survey_id']}, plan, {'model': 'survey.survey', 'id': plan['survey_id']}

    def apply_feedback_import(self, proposed, before):
        if 'irg.survey.txt.import.wizard' not in self.env:
            raise UserError(_('TXT import wizard is not installed.'))
        wizard = self.env['irg.survey.txt.import.wizard'].create({
            'survey_id': proposed['survey_id'],
            'txt_file': base64.b64encode(proposed['txt_content'].encode('utf-8')),
            'txt_filename': 'api-import.txt',
        })
        wizard.action_import()
        return {
            'survey_id': proposed['survey_id'],
            'txt_hash': proposed.get('txt_hash'),
        }

    def get_attachment_metadata(self, payload):
        attachment = self.env['ir.attachment'].browse(
            ser.require_positive_id(payload, 'attachment_id')
        )
        if not attachment.exists():
            raise UserError(_('Unknown attachment id.'))
        return {
            'id': attachment.id,
            'name': attachment.name,
            'mimetype': attachment.mimetype,
            'file_size': attachment.file_size,
            'public': bool(attachment.public) if 'public' in attachment._fields else False,
            'res_model': attachment.res_model,
            'res_id': attachment.res_id,
        }

    def preview_upload_private_attachment(self, payload):
        name = (payload.get('name') or '').strip()
        if not name:
            raise UserError(_('name is required.'))
        datas = payload.get('file_b64') or payload.get('datas') or ''
        raw = base64.b64decode(datas) if datas else b''
        if len(raw) > MAX_ATTACHMENT_BYTES:
            raise UserError(_('Attachment exceeds %s bytes.') % MAX_ATTACHMENT_BYTES)
        if not raw:
            raise UserError(_('datas is required.'))
        res_model = (payload.get('res_model') or '').strip()
        res_id = int(payload.get('res_id') or 0)
        if not res_model or res_id <= 0:
            raise UserError(_('res_model and res_id are required.'))
        before = {'res_model': res_model, 'res_id': res_id}
        proposed = {
            'name': name,
            'datas': datas,
            'mimetype': payload.get('mimetype') or 'application/octet-stream',
            'res_model': res_model,
            'res_id': res_id,
            'public': False,
        }
        return before, proposed, {'model': 'ir.attachment', 'id': False}

    def apply_upload_private_attachment(self, proposed, before):
        vals = {
            'name': proposed['name'],
            'datas': proposed['datas'],
            'res_model': proposed['res_model'],
            'res_id': proposed['res_id'],
            'mimetype': proposed.get('mimetype') or 'application/octet-stream',
        }
        if 'public' in self.env['ir.attachment']._fields:
            vals['public'] = False
        attachment = self.env['ir.attachment'].create(vals)
        if attachment.public:
            raise UserError(_('Private upload must not be public.'))
        return {
            'id': attachment.id,
            'name': attachment.name,
            'public': bool(attachment.public) if 'public' in attachment._fields else False,
            'file_size': attachment.file_size,
        }
