import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OpCourse(models.Model):
    _inherit = 'op.course'

    def name_get(self):
        # Importante que la asignatura muestre su codigo para evitar confusiones
        # Note: do NOT call self.read() here — in Odoo 16 the 'name' column may
        # still be character varying (not jsonb), causing a PostgreSQL operator
        # error when the ORM generates a translation query with the ->> operator.
        # Accessing .name / .code directly works without triggering that query.
        return [
            (rec.id, '%s%s' % (rec.code and '%s - ' % rec.code or '', rec.name or ''))
            for rec in self
        ]
    
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        return recs.name_get()