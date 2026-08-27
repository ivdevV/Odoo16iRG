# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import html_sanitize
from odoo import fields
import datetime

from . import api_serializer as ser
from .api_constants import MAX_HTML_CHARS, MAX_TITLE_CHARS


SLIDE_READ_FIELDS = [
    'id', 'name', 'channel_id', 'sequence', 'slide_category', 'is_published',
    'is_category', 'html_content',
]


class ElearningService:

    def __init__(self, env):
        self.env = env

    def get_course_structure(self, payload):
        channel = self._channel(ser.require_positive_id(payload, 'channel_id'))
        sections = self.env['irg.slide.section'].search([
            ('channel_id', '=', channel.id),
        ], order='sequence, id')
        slides = self.env['slide.slide'].search([
            ('channel_id', '=', channel.id),
        ], order='sequence, id')
        slide_rows = []
        for slide in slides:
            row = ser.record_dict(slide, [
                'id', 'name', 'sequence', 'slide_category', 'is_published',
                'is_category',
            ])
            row['irg_section_id'] = (
                slide.irg_section_id.id if 'irg_section_id' in slide._fields and slide.irg_section_id else False
            )
            row['parent_slide_id'] = (
                slide.parent_slide_id.id if 'parent_slide_id' in slide._fields and slide.parent_slide_id else False
            )
            slide_rows.append(row)
        return {
            'channel': ser.record_dict(channel, ['id', 'name', 'is_published']),
            'sections': [ser.record_dict(section, ['id', 'name', 'sequence', 'active']) for section in sections],
            'slides': slide_rows,
        }

    def get_slide(self, payload):
        slide = self._slide(ser.require_positive_id(payload, 'slide_id'))
        data = ser.record_dict(slide, SLIDE_READ_FIELDS)
        if 'irg_section_id' in slide._fields:
            data['irg_section_id'] = slide.irg_section_id.id if slide.irg_section_id else False
        if 'survey_id' in slide._fields:
            data['survey_id'] = slide.survey_id.id if slide.survey_id else False
        if 'parent_slide_id' in slide._fields:
            data['parent_slide_id'] = slide.parent_slide_id.id if slide.parent_slide_id else False
        return data

    def preview_create_slide(self, payload):
        channel = self._channel(ser.require_positive_id(payload, 'channel_id'))
        vals = self._draft_slide_vals(payload, channel)
        before = {
            'channel_id': channel.id,
            'slide_count': self.env['slide.slide'].search_count([('channel_id', '=', channel.id)]),
        }
        return before, vals, {'model': 'slide.slide', 'id': False}

    def apply_create_slide(self, proposed):
        allowed = ('name', 'channel_id', 'html_content', 'sequence', 'irg_section_id')
        vals = {key: proposed[key] for key in allowed if key in proposed}
        vals['is_published'] = False
        vals['slide_category'] = 'article'
        slide = self.env['slide.slide'].create(vals)
        return ser.record_dict(slide, SLIDE_READ_FIELDS)

    def preview_update_slide(self, payload):
        slide = self._slide(ser.require_positive_id(payload, 'slide_id'))
        if slide.slide_category != 'article' and not slide.is_category:
            raise UserError(_('Only article slides can be updated through this operation.'))
        before = ser.record_dict(slide, ['id', 'name', 'html_content', 'sequence', 'is_published', 'write_date'])
        if 'irg_section_id' in slide._fields:
            before['irg_section_id'] = slide.irg_section_id.id if slide.irg_section_id else False
        proposed = dict(before)
        if 'name' in payload:
            proposed['name'] = self._title(payload['name'])
        if 'html_content' in payload:
            proposed['html_content'] = self._html(payload['html_content'])
        if 'sequence' in payload:
            try:
                proposed['sequence'] = int(payload['sequence'])
            except (TypeError, ValueError) as err:
                raise UserError(_('sequence must be an integer.')) from err
        if 'irg_section_id' in payload:
            section = self._section(int(payload['irg_section_id']))
            if section.channel_id != slide.channel_id:
                raise UserError(_('The section does not belong to the slide channel.'))
            proposed['irg_section_id'] = section.id
        return before, proposed, {'model': 'slide.slide', 'id': slide.id}

    def apply_update_slide(self, proposed, before):
        slide = self._slide(proposed['id'])
        self._assert_preview_fresh(slide, before)
        if slide.is_published:
            raise UserError(_('The slide was published after preview.'))
        vals = {}
        for key in ('name', 'html_content', 'sequence', 'irg_section_id'):
            if key in proposed and proposed[key] != before.get(key):
                vals[key] = proposed[key]
        if vals:
            slide.write(vals)
        return ser.record_dict(slide, SLIDE_READ_FIELDS)

    def preview_create_section(self, payload):
        channel = self._channel(ser.require_positive_id(payload, 'channel_id'))
        vals = {
            'name': self._title(payload.get('name')),
            'channel_id': channel.id,
            'sequence': self._sequence(payload.get('sequence') or 10),
        }
        before = {
            'channel_id': channel.id,
            'section_count': self.env['irg.slide.section'].search_count([
                ('channel_id', '=', channel.id),
            ]),
        }
        return before, vals, {'model': 'irg.slide.section', 'id': False}

    def apply_create_section(self, proposed):
        allowed = ('name', 'channel_id', 'sequence')
        vals = {key: proposed[key] for key in allowed if key in proposed}
        section = self.env['irg.slide.section'].create(vals)
        return ser.record_dict(section, ['id', 'name', 'sequence', 'channel_id'])

    def preview_reorder_sections(self, payload):
        channel = self._channel(ser.require_positive_id(payload, 'channel_id'))
        section_ids = payload.get('section_ids') or []
        if not isinstance(section_ids, list) or not section_ids:
            raise UserError(_('section_ids must be a non-empty list.'))
        ids = [int(item) for item in section_ids]
        sections = self.env['irg.slide.section'].browse(ids)
        if set(sections.exists().ids) != set(ids):
            raise UserError(_('Unknown section ids in reorder payload.'))
        if sections.filtered(lambda section: section.channel_id != channel):
            raise UserError(_('All sections must belong to the indicated channel.'))
        before = {
            'channel_id': channel.id,
            'sequences': {str(section.id): section.sequence for section in sections},
            'write_dates': {
                str(section.id): fields.Datetime.to_string(section.write_date)
                for section in sections
            },
        }
        proposed = {
            'channel_id': channel.id,
            'section_ids': [int(item) for item in section_ids],
        }
        return before, proposed, {'model': 'irg.slide.section', 'id': channel.id}

    def apply_reorder_sections(self, proposed, before):
        channel = self._channel(proposed['channel_id'])
        for index, section_id in enumerate(proposed['section_ids'], start=1):
            section = self.env['irg.slide.section'].browse(section_id)
            expected = self._norm_write_date(
                (before.get('write_dates') or {}).get(str(section_id))
            )
            current = self._norm_write_date(section.write_date)
            if expected and current != expected:
                raise UserError(_('Section %s changed after preview.') % section_id)
            section.write({'sequence': index * 10})
        return {
            'channel_id': channel.id,
            'section_ids': proposed['section_ids'],
        }

    def preview_publish(self, payload, publish=True):
        slide = self._slide(ser.require_positive_id(payload, 'slide_id'))
        before = {
            'id': slide.id,
            'is_published': bool(slide.is_published),
            'write_date': fields.Datetime.to_string(slide.write_date),
        }
        proposed = dict(before)
        proposed['is_published'] = publish
        return before, proposed, {'model': 'slide.slide', 'id': slide.id}

    def apply_publish(self, proposed, before):
        slide = self._slide(proposed['id'])
        if bool(slide.is_published) != bool(before.get('is_published')):
            raise UserError(_('The record changed after preview.'))
        self._assert_write_date(slide, before)
        slide.write({'is_published': bool(proposed.get('is_published'))})
        return {
            'id': slide.id,
            'is_published': bool(slide.is_published),
        }

    def verify_create_slide(self, result):
        slide = self._slide(result['id'])
        if slide.is_published:
            raise UserError(_('Draft creation published the slide.'))
        if slide.slide_category != 'article':
            raise UserError(_('Draft creation did not produce an article.'))
        return True

    def _draft_slide_vals(self, payload, channel):
        vals = {
            'name': self._title(payload.get('name')),
            'channel_id': channel.id,
            'slide_category': 'article',
            'html_content': self._html(payload.get('html_content') or '<p></p>'),
            'sequence': self._sequence(payload.get('sequence') or 10),
            'is_published': False,
        }
        if payload.get('irg_section_id'):
            section = self._section(int(payload['irg_section_id']))
            if section.channel_id != channel:
                raise UserError(_('The section does not belong to the channel.'))
            vals['irg_section_id'] = section.id
        return vals

    def _title(self, name):
        title = (name or '').strip()
        if not title:
            raise UserError(_('name is required.'))
        if len(title) > MAX_TITLE_CHARS:
            raise UserError(_('name exceeds %s characters.') % MAX_TITLE_CHARS)
        return title

    def _sequence(self, value):
        try:
            return int(value)
        except (TypeError, ValueError) as err:
            raise UserError(_('sequence must be an integer.')) from err

    def _html(self, html):
        if html is None:
            html = ''
        if not isinstance(html, str):
            raise UserError(_('html_content must be text.'))
        if len(html) > MAX_HTML_CHARS:
            raise UserError(_('html_content exceeds %s characters.') % MAX_HTML_CHARS)
        return html_sanitize(html) or '<p></p>'

    def _assert_preview_fresh(self, slide, before):
        if before.get('name') not in (None, False) and slide.name != before.get('name'):
            raise UserError(_('The record changed after preview.'))
        if 'is_published' in before and bool(slide.is_published) != bool(before.get('is_published')):
            raise UserError(_('The record changed after preview.'))
        self._assert_write_date(slide, before)

    def _assert_write_date(self, record, before):
        expected = self._norm_write_date(before.get('write_date'))
        current = self._norm_write_date(record.write_date)
        if expected and current != expected:
            raise UserError(_('The record changed after preview.'))

    def _norm_write_date(self, value):
        if not value:
            return False
        if isinstance(value, datetime.datetime):
            value = fields.Datetime.to_string(value)
        return str(value).replace('T', ' ')[:19]

    def _channel(self, channel_id):
        channel = self.env['slide.channel'].browse(channel_id)
        if not channel.exists():
            raise UserError(_('Unknown channel id %s.') % channel_id)
        return channel

    def _slide(self, slide_id):
        slide = self.env['slide.slide'].browse(slide_id)
        if not slide.exists():
            raise UserError(_('Unknown slide id %s.') % slide_id)
        return slide

    def _section(self, section_id):
        section = self.env['irg.slide.section'].browse(section_id)
        if not section.exists():
            raise UserError(_('Unknown section id %s.') % section_id)
        return section
