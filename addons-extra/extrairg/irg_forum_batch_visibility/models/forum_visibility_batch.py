from odoo import fields, models


class ForumVisibilityBatch(models.Model):
    _name = 'forum.visibility.batch'
    _description = 'Forum Visibility Batch'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    description = fields.Text()

    _sql_constraints = [
        ('forum_visibility_batch_name_uniq', 'unique(name)', 'Batch name must be unique.'),
    ]
