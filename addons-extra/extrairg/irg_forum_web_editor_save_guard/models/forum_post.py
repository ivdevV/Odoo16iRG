import logging

from markupsafe import escape

from odoo import api, models
from odoo.tools import html_sanitize

_logger = logging.getLogger(__name__)


class ForumPost(models.Model):
    _inherit = "forum.post"

    _GUARDED_CONTENT_FIELDS = ("content", "description", "body")

    @staticmethod
    def _fallback_html(value):
        text = (value or "").replace("\r\n", "\n").replace("\r", "\n")
        text = escape(text)
        text = text.replace("\n", "<br/>")
        return "<p>%s</p>" % text if text else ""

    @classmethod
    def _prepare_guarded_vals(cls, values):
        sanitized = dict(values or {})
        for field_name in cls._GUARDED_CONTENT_FIELDS:
            value = sanitized.get(field_name)
            if isinstance(value, str):
                try:
                    sanitized[field_name] = html_sanitize(value)
                except Exception:
                    sanitized[field_name] = cls._fallback_html(value)
        return sanitized

    @api.model_create_multi
    def create(self, vals_list):
        safe_vals_list = [self._prepare_guarded_vals(vals) for vals in vals_list]
        try:
            return super().create(safe_vals_list)
        except Exception:
            _logger.exception("Forum post create failed after sanitization; retrying with fallback HTML.")
            fallback_vals = []
            for vals in safe_vals_list:
                retry_vals = dict(vals)
                for field_name in self._GUARDED_CONTENT_FIELDS:
                    if isinstance(retry_vals.get(field_name), str):
                        retry_vals[field_name] = self._fallback_html(retry_vals[field_name])
                fallback_vals.append(retry_vals)
            return super().create(fallback_vals)

    def write(self, values):
        safe_values = self._prepare_guarded_vals(values)
        try:
            return super().write(safe_values)
        except Exception:
            _logger.exception("Forum post write failed after sanitization; retrying with fallback HTML.")
            fallback_values = dict(safe_values)
            for field_name in self._GUARDED_CONTENT_FIELDS:
                if isinstance(fallback_values.get(field_name), str):
                    fallback_values[field_name] = self._fallback_html(fallback_values[field_name])
            return super().write(fallback_values)
