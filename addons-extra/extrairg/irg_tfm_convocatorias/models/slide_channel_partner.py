import logging

from psycopg2 import IntegrityError

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


_TFM_ACTIVE_UNIQUE_INDEX = 'irg_scp_active_partner_channel_batch_uniq'
_TFM_SYNC_CONTEXT = 'irg_tfm_membership_sync'
_TFM_SERVICE_CONTEXT = {
    _TFM_SYNC_CONTEXT: True,
    'irg_skip_partner_sync': True,
}
_TFM_ALLOWED_MEMBERSHIP_FIELDS = {
    'id', 'display_name', 'channel_id', 'partner_id', 'batch_id', 'active',
    'irg_tfm_created', 'irg_tfm_thesis_ids', 'create_uid', 'create_date',
    'write_uid', 'write_date', '__last_update',
}
_logger = logging.getLogger(__name__)


class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    irg_tfm_created = fields.Boolean(
        string='Creada por TFM',
        default=False,
        index=True,
        copy=False,
        readonly=True,
        help='Indica que la fila fue creada por la sincronización de TFM.',
    )
    irg_tfm_thesis_ids = fields.Many2many(
        'tesis.model',
        'slide_channel_partner_tfm_thesis_rel',
        'membership_id',
        'thesis_id',
        string='Expedientes TFM',
        copy=False,
        readonly=True,
        help='Expedientes TFM que usan esta membership creada por TFM.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get(_TFM_SYNC_CONTEXT):
            for vals in vals_list:
                if vals.get('irg_tfm_created') or vals.get('irg_tfm_thesis_ids'):
                    raise AccessError(_(
                        'TFM membership provenance can only be changed by its service.'
                    ))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get(_TFM_SYNC_CONTEXT) and {
            'irg_tfm_created', 'irg_tfm_thesis_ids',
        }.intersection(vals):
            raise AccessError(_(
                'TFM membership provenance can only be changed by its service.'
            ))
        return super().write(vals)

    def _irg_tfm_has_foreign_signals(self):
        """Detect academic ownership fields that TFM must never overwrite."""
        self.ensure_one()
        for field_name, field in self._fields.items():
            if field_name in _TFM_ALLOWED_MEMBERSHIP_FIELDS:
                continue
            if field_name.startswith('__') or (field.compute and not field.store):
                continue
            try:
                value = self[field_name]
            except (AccessError, KeyError):
                continue
            if value:
                return True
        return False

    def _irg_tfm_target_values(self, thesis):
        thesis.ensure_one()
        enrollment = thesis.course_id
        course = enrollment.course_id
        configured_channel = course.irg_tfm_channel_id
        channel = (
            configured_channel._irg_tfm_effective_channel(enrollment)
            if configured_channel else self.env['slide.channel']
        )
        partner = enrollment.student_id.partner_id
        if not channel or not partner or not enrollment:
            return False
        values = {
            'partner_id': partner.id,
            'channel_id': channel.id,
            'active': True,
        }
        if 'batch_id' in self._fields:
            values['batch_id'] = enrollment.batch_id.id or False
        return values

    def _irg_tfm_same_target_domain(self, values):
        domain = [
            ('partner_id', '=', values['partner_id']),
            ('channel_id', '=', values['channel_id']),
        ]
        if 'batch_id' in self._fields:
            domain.append(('batch_id', '=', values.get('batch_id') or False))
        return domain

    def _irg_tfm_remove_reference(self, membership, thesis):
        references = membership.irg_tfm_thesis_ids - thesis
        membership.with_context(**_TFM_SERVICE_CONTEXT).write({
            'irg_tfm_thesis_ids': [(6, 0, references.ids)],
        })
        if (
            not references
            and membership.irg_tfm_created
            and not membership._irg_tfm_has_foreign_signals()
        ):
            membership.with_context(**_TFM_SERVICE_CONTEXT).write({'active': False})

    def _irg_tfm_find_active_target(self, values):
        memberships = self.with_context(active_test=False).search(
            self._irg_tfm_same_target_domain(values) + [('active', '=', True)],
            order='id',
        )
        if not memberships:
            return self.browse(), False
        owned = memberships.filtered(
            lambda membership: membership.irg_tfm_created
            and not membership._irg_tfm_has_foreign_signals()
        )
        if owned:
            return owned[:1], False
        # A foreign active row already grants generic channel visibility. It is
        # intentionally returned separately so no provenance field is changed.
        return self.browse(), True

    def _irg_tfm_reactivate_archived_target(self, values, thesis):
        memberships = self.with_context(active_test=False).search(
            self._irg_tfm_same_target_domain(values) + [
                ('active', '=', False),
                ('irg_tfm_created', '=', True),
                ('irg_tfm_thesis_ids', 'in', thesis.id),
            ],
            order='id',
        )
        for membership in memberships:
            if membership._irg_tfm_has_foreign_signals():
                continue
            membership.with_context(**_TFM_SERVICE_CONTEXT).write({'active': True})
            return membership
        return self.browse()

    def _irg_tfm_create_target(self, values, thesis):
        create_values = dict(values)
        create_values.update({
            'irg_tfm_created': True,
            'irg_tfm_thesis_ids': [(4, thesis.id)],
        })
        try:
            with self.env.cr.savepoint():
                return self.with_context(**_TFM_SERVICE_CONTEXT).create(create_values)
        except IntegrityError as exc:
            if getattr(exc.diag, 'constraint_name', None) != _TFM_ACTIVE_UNIQUE_INDEX:
                raise
            _logger.info(
                'Concurrent TFM membership already exists for partner %s and channel %s',
                values['partner_id'], values['channel_id'],
            )
            active, foreign = self._irg_tfm_find_active_target(values)
            if active:
                active.with_context(**_TFM_SERVICE_CONTEXT).write({
                    'irg_tfm_thesis_ids': [(4, thesis.id)],
                })
                return active
            if foreign:
                return self.browse()
            raise ValidationError(_(
                'The TFM membership could not be allocated because the active '
                'membership changed concurrently.'
            ))

    def _irg_sync_tfm_membership(self, thesis):
        """Reconcile one thesis membership without mutating foreign rows."""
        # This check must remain before every sudo: UI visibility is not auth.
        if not self.env.user.has_group('base.group_user'):
            raise AccessError(_('Only internal users can synchronize TFM memberships.'))
        thesis.ensure_one()

        self.env.cr.execute(
            'SELECT id FROM tesis_model WHERE id = %s FOR UPDATE', [thesis.id]
        )
        thesis.invalidate_recordset()
        thesis = thesis.exists()
        if not thesis:
            return True

        Membership = self.sudo().with_context(active_test=False)
        linked = Membership.search([('irg_tfm_thesis_ids', 'in', thesis.id)])
        target_values = self._irg_tfm_target_values(thesis)
        if not thesis.irg_tfm_convocation_id or not target_values:
            for membership in linked:
                self._irg_tfm_remove_reference(membership, thesis)
            return True

        active_target, foreign_active = Membership._irg_tfm_find_active_target(target_values)
        selected = active_target
        if not selected and not foreign_active:
            selected = Membership._irg_tfm_reactivate_archived_target(target_values, thesis)
        if not selected and not foreign_active:
            selected = Membership._irg_tfm_create_target(target_values, thesis)
            if selected:
                selected = selected[:1]

        # Detach old channel/batch rows after deciding the destination. This
        # preserves a shared TFM-created row while retiring stale references.
        for membership in linked:
            if not selected or membership.id != selected.id:
                self._irg_tfm_remove_reference(membership, thesis)
        if selected and thesis.id not in selected.irg_tfm_thesis_ids.ids:
            selected.with_context(**_TFM_SERVICE_CONTEXT).write({
                'irg_tfm_thesis_ids': [(4, thesis.id)],
            })
        return True
