# -*- coding: utf-8 -*-

import json
from urllib import error, request

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class IrgOficialidadWebhookService(models.AbstractModel):
    _name = 'irg.oficialidad.webhook.service'
    _description = 'Servicio webhook de oficialidad'

    _TECHNICAL_FIELDS = frozenset({
        'message_ids',
        'message_follower_ids',
        'message_partner_ids',
        'message_main_attachment_id',
        'activity_ids',
        'activity_calendar_event_id',
        'website_message_ids',
        'message_attachment_count',
        'message_has_error',
        'message_has_error_counter',
        'message_needaction',
        'message_needaction_counter',
        'message_has_sms_error',
        'message_is_follower',
        'message_unread',
        'message_unread_counter',
        'access_token',
        'access_url',
        'access_warning',
        '__last_update',
        'image',
        'image_1920',
        'image_1024',
        'image_512',
        'image_256',
        'image_128',
        'image_medium',
        'image_small',
    })
    _SCALAR_FIELD_TYPES = frozenset({
        'char',
        'text',
        'html',
        'selection',
        'boolean',
        'integer',
        'float',
        'monetary',
    })

    @api.model
    def _get_int_param(self, key, default=0, minimum=None, maximum=None):
        raw_value = self.env['ir.config_parameter'].sudo().get_param(
            key, str(default)
        )
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = default
        if minimum is not None:
            value = max(minimum, value)
        if maximum is not None:
            value = min(maximum, value)
        return value

    @api.model
    def _get_config(self):
        params = self.env['ir.config_parameter'].sudo()
        return {
            'webhook_url': str(params.get_param(
                'irg_oficialidad_webhook.webhook_url', ''
            ) or '').strip(),
            'auth_token': str(params.get_param(
                'irg_oficialidad_webhook.auth_token', ''
            ) or '').strip(),
            'timeout': self._get_int_param(
                'irg_oficialidad_webhook.timeout',
                15,
                minimum=1,
                maximum=120,
            ),
        }

    @api.model
    def _post_json(self, webhook_url, payload_json, auth_token, timeout):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer %s' % auth_token,
        }
        req = request.Request(
            webhook_url,
            data=payload_json.encode('utf-8'),
            headers=headers,
            method='POST',
        )
        try:
            with request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode('utf-8', errors='replace')[:2000]
                return response.getcode(), body
        except error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')[:2000]
            return exc.code, body

    @api.model
    def _serialize_record(self, record):
        if not record:
            return {}
        record.ensure_one()
        serialized = {}
        for field_name, field_definition in record._fields.items():
            field_type = field_definition.type
            if (
                field_name in self._TECHNICAL_FIELDS
                or field_type in ('binary', 'image')
            ):
                continue
            if field_type not in self._SCALAR_FIELD_TYPES | {
                'date', 'datetime', 'many2one', 'many2many', 'one2many'
            }:
                continue
            try:
                value = record[field_name]
                if field_type in self._SCALAR_FIELD_TYPES:
                    serialized[field_name] = value
                elif field_type == 'date':
                    serialized[field_name] = (
                        fields.Date.to_string(value) if value else False
                    )
                elif field_type == 'datetime':
                    serialized[field_name] = (
                        fields.Datetime.to_string(value) if value else False
                    )
                elif field_type == 'many2one':
                    serialized[field_name] = (
                        {'id': value.id, 'name': value.display_name}
                        if value else False
                    )
                else:
                    serialized[field_name] = [
                        {'id': related.id, 'name': related.display_name}
                        for related in value
                    ]
            except Exception:
                continue
        return serialized

    @api.model
    def _build_payload(self, register, admissions):
        register.ensure_one()
        course = register.course_id
        academic_term = getattr(register, 'academic_term_id', False)
        period = getattr(register, 'period', False)
        if not period and academic_term:
            period = academic_term.display_name
        students = []
        for admission in admissions:
            student = getattr(admission, 'student_id', False)
            partner = getattr(admission, 'partner_id', False)
            if not partner and student:
                partner = getattr(student, 'partner_id', False)
            students.append({
                'admission': self._serialize_record(admission),
                'student': self._serialize_record(student),
                'partner': self._serialize_record(partner),
            })
        company = self.env.company
        return {
            'odoo': {
                'database': self.env.cr.dbname,
                'base_url': self.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url', ''
                ),
                'company_id': company.id,
                'company_name': company.name,
            },
            'register': {
                'id': register.id,
                'name': register.name or '',
                'period': period or '',
                'course_id': course.id if course else False,
                'course_name': course.display_name if course else '',
                'start_date': (
                    fields.Date.to_string(register.start_date)
                    if register.start_date else False
                ),
                'end_date': (
                    fields.Date.to_string(register.end_date)
                    if register.end_date else False
                ),
            },
            'students': students,
            'sent_at': fields.Datetime.to_string(fields.Datetime.now()),
            'sent_by': {
                'user_id': self.env.user.id,
                'user_name': self.env.user.name,
            },
        }

    @api.model
    def send_oficialidad(self, register, admissions):
        config = self._get_config()
        missing = []
        if not config['webhook_url']:
            missing.append('irg_oficialidad_webhook.webhook_url')
        if not config['auth_token']:
            missing.append('irg_oficialidad_webhook.auth_token')
        if missing:
            raise UserError(_(
                'Configure los siguientes parámetros del webhook de oficialidad: %s'
            ) % ', '.join(missing))

        payload_json = json.dumps(
            self._build_payload(register, admissions),
            ensure_ascii=False,
        )
        try:
            status, body = self._post_json(
                config['webhook_url'],
                payload_json,
                config['auth_token'],
                config['timeout'],
            )
        except Exception as exc:
            raise UserError(
                _('No se pudo contactar con el webhook de oficialidad: %s') % exc
            ) from exc
        if not 200 <= status < 300:
            raise UserError(_(
                'El webhook de oficialidad respondió con estado HTTP %(status)s: '
                '%(detail)s'
            ) % {
                'status': status,
                'detail': (body or '')[:500],
            })
        return status, body
