# -*- coding: utf-8 -*-
import datetime
import hashlib
import json

from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo import fields

from .api_constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    SECRET_TOKENS,
)


def canonical_dumps(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def payload_hash(payload):
    return hashlib.sha256(canonical_dumps(payload).encode('utf-8')).hexdigest()


def parse_payload(raw):
    if raw in (False, None, ''):
        return {}
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise UserError(_('request_payload must be a JSON object.'))
    try:
        data = json.loads(raw)
    except ValueError as err:
        raise UserError(_('Malformed JSON payload.')) from err
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise UserError(_('request_payload must be a JSON object.'))
    return data


def dumps_public(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def contains_secret_key(key):
    lowered = (key or '').lower()
    return any(token in lowered for token in SECRET_TOKENS)


def sanitize_mapping(value):
    if isinstance(value, dict):
        return {
            key: sanitize_mapping(item)
            for key, item in value.items()
            if not contains_secret_key(str(key))
        }
    if isinstance(value, list):
        return [sanitize_mapping(item) for item in value]
    if isinstance(value, datetime.datetime):
        return fields.Datetime.to_string(value)
    if isinstance(value, datetime.date):
        return fields.Date.to_string(value)
    if hasattr(value, '__html__'):
        return str(value)
    return value


def record_dict(record, field_names):
    data = {}
    for name in field_names:
        if name not in record._fields or contains_secret_key(name):
            continue
        value = record[name]
        field = record._fields[name]
        if field.type == 'many2one':
            data[name] = value.id if value else False
            if value and name.endswith('_id') and 'name' in value._fields:
                data[name.replace('_id', '_name')] = value.name
        elif field.type in ('one2many', 'many2many'):
            data[name] = value.ids
        elif field.type == 'binary':
            continue
        else:
            data[name] = value
    return data


def paginate(records, payload):
    try:
        offset = int(payload.get('offset') or 0)
        limit = int(payload.get('limit') or DEFAULT_PAGE_SIZE)
    except (TypeError, ValueError) as err:
        raise UserError(_('limit and offset must be integers.')) from err
    if offset < 0:
        raise UserError(_('offset must be >= 0.'))
    if limit < 1 or limit > MAX_PAGE_SIZE:
        raise UserError(_('limit must be between 1 and %s.') % MAX_PAGE_SIZE)
    total = len(records)
    page = records[offset:offset + limit]
    return page, {'offset': offset, 'limit': limit, 'total': total}


def require_positive_id(payload, key):
    value = payload.get(key)
    try:
        record_id = int(value)
    except (TypeError, ValueError):
        record_id = 0
    if record_id < 1:
        raise UserError(_('%s must be a positive integer.') % key)
    return record_id
