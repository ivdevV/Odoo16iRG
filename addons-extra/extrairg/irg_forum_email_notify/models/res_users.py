from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    forum_email_optout_ids = fields.Many2many(
        'forum.forum',
        'res_users_forum_email_optout_rel',
        'user_id',
        'forum_id',
        string='Foros sin notificaciones',
        help='Foros de los que este usuario ha cancelado las notificaciones por email.',
    )
