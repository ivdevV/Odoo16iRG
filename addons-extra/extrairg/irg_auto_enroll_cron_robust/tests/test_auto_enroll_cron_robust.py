from datetime import date, timedelta
from threading import Thread
from unittest.mock import patch
from uuid import uuid4

from lxml import etree
from psycopg2 import IntegrityError

from odoo import api
from odoo import tools
from odoo.exceptions import ValidationError
from odoo.modules.registry import Registry
from odoo.modules.module import get_module_resource
from odoo.tests.common import TransactionCase, tagged

from ..hooks import uninstall_hook


@tagged('post_install', '-at_install')
class TestAutoEnrollCronRobust(TransactionCase):
    def setUp(self):
        super().setUp()
        self.cron = self.env.ref('isep_elearning_custom.ir_cron_auto_enroll_students')

    def _trigger_ids(self):
        return set(self.env['ir.cron.trigger'].search([('cron_id', '=', self.cron.id)]).ids)

    def _memberships(self, admission):
        return self.env['slide.channel.partner'].sudo().with_context(active_test=False).search([
            ('partner_id', '=', admission.partner_id.id),
            ('batch_id', '=', admission.batch_id.id),
        ])

    def _subject_line_values(self):
        subject = self.env['op.subject'].create({'name': 'Robust subject', 'code': 'ROBUST'})
        course = self.env['op.course'].create({
            'name': 'Robust course',
            'code': 'ROBUST',
            'subject_ids': [(6, 0, subject.ids)],
            'lang': 'en_US',
        })
        batch = self.env['op.batch'].create({
            'name': 'Robust batch',
            'code': 'ROBUST',
            'course_id': course.id,
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today() + timedelta(days=30),
        })
        line = batch.subject_to_batch_ids[:1]
        if line:
            return line, subject, batch
        line = self.env['op.subject.to.batch'].create({
            'subject_id': subject.id,
            'batch_id': batch.id,
            'date_from': date.today() - timedelta(days=1),
            'date_to': date.today() + timedelta(days=1),
        })
        return line, subject, batch

    def _create_admission_case(self, subject=None):
        suffix = uuid4().hex[:8]
        subject = subject or self.env['op.subject'].create({
            'name': 'Robust admission subject %s' % suffix,
            'code': 'ROBUST-ADM-%s' % suffix,
        })
        channel = self.env['slide.channel'].create({
            'name': 'Robust admission channel %s' % suffix,
        })
        subject.slide_channel_id = channel
        course = self.env['op.course'].create({
            'name': 'Robust admission course %s' % suffix,
            'code': 'ROBUST-ADM-%s' % suffix,
            'subject_ids': [(6, 0, subject.ids)], 'lang': 'en_US',
        })
        batch = self.env['op.batch'].create({
            'name': 'Robust admission batch %s' % suffix,
            'code': 'ROBUST-ADM-%s' % suffix,
            'course_id': course.id,
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today() + timedelta(days=30),
        })
        line = batch.subject_to_batch_ids.filtered(lambda item: item.subject_id == subject)[:1]
        line.write({
            'date_from': date.today() - timedelta(days=1),
            'date_to': date.today() + timedelta(days=1),
        })
        product = self.env['product.product'].create({
            'name': 'Robust admission fee', 'type': 'service',
        })
        register = self.env['op.admission.register'].create({
            'name': 'Robust admission register %s' % suffix, 'course_id': course.id,
            'product_id': product.id,
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today() + timedelta(days=30),
            'min_count': 1, 'max_count': 30,
        })
        partner = self.env['res.partner'].create({
            'name': 'Robust admission student %s' % suffix,
            'email': 'robust.admission.%s@example.com' % suffix,
        })
        admission = self.env['op.admission'].create({
            'first_name': 'Robust', 'last_name': 'Student', 'name': 'Robust Student',
            'birth_date': date(1990, 1, 1), 'gender': 'o', 'email': partner.email,
            'register_id': register.id, 'course_id': course.id, 'batch_id': batch.id,
            'admission_date': date.today(), 'partner_id': partner.id,
            'state': 'done', 'modality': 'manual',
        })
        return admission, subject, channel, batch, line

    def _create_transition_case(
        self, initial_active_count, archived_count, activated_count=0,
    ):
        subjects = self.env['op.subject']
        for index in range(initial_active_count + activated_count):
            subject = self.env['op.subject'].create({
                'name': 'Guard subject %s' % index,
                'code': 'GUARD-%s' % index,
            })
            subject.slide_channel_id = self.env['slide.channel'].create({
                'name': 'Guard channel %s' % index,
            })
            subjects |= subject
        course = self.env['op.course'].create({
            'name': 'Guard course', 'code': 'GUARD',
            'subject_ids': [(6, 0, subjects.ids)], 'lang': 'en_US',
        })
        batch = self.env['op.batch'].create({
            'name': 'Guard batch', 'code': 'GUARD', 'course_id': course.id,
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today() + timedelta(days=30),
        })
        lines = batch.subject_to_batch_ids.sorted('id')
        lines[:archived_count].write({
            'date_from': date.today() - timedelta(days=2),
            'date_to': date.today() - timedelta(days=1),
        })
        lines[archived_count:].write({
            'date_from': date.today() - timedelta(days=1),
            'date_to': date.today() + timedelta(days=1),
        })
        product = self.env['product.product'].create({'name': 'Guard fee', 'type': 'service'})
        register = self.env['op.admission.register'].create({
            'name': 'Guard register', 'course_id': course.id, 'product_id': product.id,
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today() + timedelta(days=30), 'min_count': 1, 'max_count': 30,
        })
        partner = self.env['res.partner'].create({'name': 'Guard student'})
        admission = self.env['op.admission'].create({
            'first_name': 'Guard', 'last_name': 'Student', 'name': 'Guard Student',
            'birth_date': date(1990, 1, 1), 'gender': 'o',
            'email': 'guard@example.com', 'register_id': register.id,
            'course_id': course.id, 'batch_id': batch.id,
            'admission_date': date.today(), 'partner_id': partner.id,
            'state': 'done', 'modality': 'manual',
        })
        Membership = self.env['slide.channel.partner'].sudo().with_context(
            active_test=False, irg_skip_partner_sync=True,
        )
        for index, line in enumerate(lines):
            Membership.create({
                'partner_id': partner.id,
                'channel_id': line.subject_id.slide_channel_id.id,
                'batch_id': batch.id,
                'op_subject_id': line.subject_id.id,
                'admission_id': admission.id,
                'active': index < initial_active_count,
            })
        return admission, lines

    def _link_online_clone(self, home_channel):
        online_channel = self.env['slide.channel'].create({
            'name': '%s Online' % home_channel.name,
            'irg_homeclass_channel_id': home_channel.id,
        })
        home_channel.irg_online_channel_id = online_channel
        return online_channel

    def _create_committed_admission_case(self, registry):
        suffix = uuid4().hex[:8]
        with registry.cursor() as setup_cr:
            env = api.Environment(setup_cr, self.env.uid, {})
            cron_id = env.ref('isep_elearning_custom.ir_cron_auto_enroll_students').id
            setup_cr.execute(
                'SELECT id FROM ir_cron_trigger WHERE cron_id = %s', [cron_id]
            )
            trigger_baseline_ids = {row[0] for row in setup_cr.fetchall()}
            subject = env['op.subject'].create({
                'name': 'Concurrent subject %s' % suffix,
                'code': 'CONCURRENT-%s' % suffix,
            })
            channel = env['slide.channel'].create({'name': 'Concurrent channel %s' % suffix})
            subject.slide_channel_id = channel
            course = env['op.course'].create({
                'name': 'Concurrent course %s' % suffix,
                'code': 'CONCURRENT-%s' % suffix,
                'subject_ids': [(6, 0, subject.ids)], 'lang': 'en_US',
            })
            batch = env['op.batch'].create({
                'name': 'Concurrent batch %s' % suffix,
                'code': 'CONCURRENT-%s' % suffix, 'course_id': course.id,
                'start_date': date.today() - timedelta(days=30),
                'end_date': date.today() + timedelta(days=30),
            })
            batch.subject_to_batch_ids.write({
                'date_from': date.today() - timedelta(days=1),
                'date_to': date.today() + timedelta(days=1),
            })
            product = env['product.product'].create({
                'name': 'Concurrent fee %s' % suffix, 'type': 'service',
            })
            register = env['op.admission.register'].create({
                'name': 'Concurrent register %s' % suffix, 'course_id': course.id,
                'product_id': product.id,
                'start_date': date.today() - timedelta(days=30),
                'end_date': date.today() + timedelta(days=30),
                'min_count': 1, 'max_count': 30,
            })
            partner = env['res.partner'].create({'name': 'Concurrent student %s' % suffix})
            admission = env['op.admission'].create({
                'first_name': 'Concurrent', 'last_name': 'Student',
                'name': 'Concurrent Student %s' % suffix,
                'birth_date': date(1990, 1, 1), 'gender': 'o',
                'email': 'concurrent.%s@example.com' % suffix,
                'register_id': register.id, 'course_id': course.id,
                'batch_id': batch.id, 'admission_date': date.today(),
                'partner_id': partner.id, 'state': 'done', 'modality': 'manual',
            })
            identifiers = {
                'admission': admission.id, 'partner': partner.id, 'channel': channel.id,
                'batch': batch.id, 'register': register.id, 'course': course.id,
                'subject': subject.id, 'product': product.id, 'cron': cron_id,
                'trigger_baseline_ids': trigger_baseline_ids,
            }
            setup_cr.execute(
                'SELECT id FROM ir_cron_trigger WHERE cron_id = %s', [cron_id]
            )
            identifiers['trigger_ids'] = {
                row[0] for row in setup_cr.fetchall() if row[0] not in trigger_baseline_ids
            }
            setup_cr.commit()
            return identifiers

    def _cleanup_committed_admission_case(self, registry, identifiers):
        with registry.cursor() as cleanup_cr:
            env = api.Environment(cleanup_cr, self.env.uid, {})
            cleanup_cr.execute(
                'SELECT id FROM ir_cron_trigger WHERE cron_id = %s', [identifiers['cron']]
            )
            before_cleanup_trigger_ids = {row[0] for row in cleanup_cr.fetchall()}
            env['slide.channel.partner'].sudo().with_context(active_test=False).search([
                ('partner_id', '=', identifiers['partner']),
                ('batch_id', '=', identifiers['batch']),
            ]).with_context(irg_skip_partner_sync=True).unlink()
            env['op.admission'].browse(identifiers['admission']).unlink()
            env['op.admission.register'].browse(identifiers['register']).unlink()
            env['op.batch'].browse(identifiers['batch']).unlink()
            env['op.course'].browse(identifiers['course']).unlink()
            env['op.subject'].browse(identifiers['subject']).unlink()
            env['slide.channel'].browse(identifiers['channel']).unlink()
            env['res.partner'].browse(identifiers['partner']).unlink()
            env['product.product'].browse(identifiers['product']).unlink()
            cleanup_cr.execute(
                'SELECT id FROM ir_cron_trigger WHERE cron_id = %s', [identifiers['cron']]
            )
            unlink_trigger_ids = {
                row[0] for row in cleanup_cr.fetchall()
                if row[0] not in before_cleanup_trigger_ids
            }
            owned_trigger_ids = identifiers['trigger_ids'] | unlink_trigger_ids
            if owned_trigger_ids:
                cleanup_cr.execute(
                    'DELETE FROM ir_cron_trigger WHERE id = ANY(%s)',
                    [list(owned_trigger_ids)],
                )
            cleanup_cr.commit()

    def test_auto_enroll_cron_has_hourly_default(self):
        self.assertEqual((self.cron.interval_number, self.cron.interval_type), (1, 'hours'))

    def test_auto_enroll_cron_xml_is_noupdate(self):
        xml_path = get_module_resource(
            'isep_elearning_custom', 'data', 'cron_batch_slide_channel.xml'
        )
        root = etree.parse(xml_path).getroot()
        self.assertEqual(root.get('noupdate'), '1')

    def test_create_schedules_one_pending_trigger(self):
        baseline_ids = self._trigger_ids()
        self._subject_line_values()
        self.assertTrue(self._trigger_ids() - baseline_ids)

    def test_relevant_write_schedules_trigger(self):
        line, _subject, _batch = self._subject_line_values()
        baseline_ids = self._trigger_ids()
        line.write({'date_to': date.today() + timedelta(days=2)})
        self.assertTrue(self._trigger_ids() - baseline_ids)

    def test_irrelevant_write_does_not_schedule_trigger(self):
        line, _subject, _batch = self._subject_line_values()
        baseline_ids = self._trigger_ids()
        line.write({'code': 'UNCHANGED-BEHAVIOUR'})
        self.assertEqual(self._trigger_ids(), baseline_ids)

    def test_unlink_schedules_trigger(self):
        line, _subject, _batch = self._subject_line_values()
        baseline_ids = self._trigger_ids()
        line.unlink()
        self.assertTrue(self._trigger_ids() - baseline_ids)

    def test_change_committed_during_running_cron_keeps_trigger_for_next_run(self):
        registry = Registry(self.env.cr.dbname)
        cron_id = self.cron.id
        owned_trigger_ids = set()
        fixture_ids = {}
        with registry.cursor() as setup_cr:
            setup_env = api.Environment(setup_cr, self.env.uid, {})
            setup_cr.execute(
                'SELECT id FROM ir_cron_trigger WHERE cron_id = %s', [cron_id]
            )
            baseline_ids = {row[0] for row in setup_cr.fetchall()}
            suffix = uuid4().hex[:8]
            subject = setup_env['op.subject'].create({
                'name': 'Concurrent trigger subject %s' % suffix,
                'code': 'TRIGGER-%s' % suffix,
            })
            course = setup_env['op.course'].create({
                'name': 'Concurrent trigger course %s' % suffix,
                'code': 'TRIGGER-%s' % suffix,
                'subject_ids': [(6, 0, subject.ids)],
                'lang': 'en_US',
            })
            batch = setup_env['op.batch'].create({
                'name': 'Concurrent trigger batch %s' % suffix,
                'code': 'TRIGGER-%s' % suffix,
                'course_id': course.id,
                'start_date': date.today() - timedelta(days=30),
                'end_date': date.today() + timedelta(days=30),
            })
            line = batch.subject_to_batch_ids[:1]
            if not line:
                line = setup_env['op.subject.to.batch'].create({
                    'subject_id': subject.id,
                    'batch_id': batch.id,
                    'date_from': date.today() - timedelta(days=1),
                    'date_to': date.today() + timedelta(days=1),
                })
            setup_cr.execute(
                'SELECT id FROM ir_cron_trigger WHERE cron_id = %s', [cron_id]
            )
            setup_trigger_ids = {
                row[0] for row in setup_cr.fetchall() if row[0] not in baseline_ids
            }
            owned_trigger_ids.update(setup_trigger_ids)
            fixture_ids = {
                'line': line.id,
                'batch': batch.id,
                'course': course.id,
                'subject': subject.id,
            }
            setup_cr.commit()
        try:
            with registry.cursor() as running_cr:
                running_cr.execute(
                    'SELECT count(*) FROM ir_cron_trigger WHERE cron_id = %s', [cron_id]
                )
                running_cr.fetchone()
                with registry.cursor() as change_cr:
                    change_env = api.Environment(change_cr, self.env.uid, {})
                    change_env['op.subject.to.batch'].browse(fixture_ids['line']).write({
                        'date_to': date.today() + timedelta(days=2),
                    })
                    change_cr.execute(
                        'SELECT id FROM ir_cron_trigger WHERE cron_id = %s', [cron_id]
                    )
                    write_trigger_ids = {
                        row[0] for row in change_cr.fetchall()
                        if row[0] not in baseline_ids and row[0] not in setup_trigger_ids
                    }
                    self.assertTrue(write_trigger_ids)
                    owned_trigger_ids.update(write_trigger_ids)
                    change_cr.commit()
                if setup_trigger_ids:
                    running_cr.execute(
                        'DELETE FROM ir_cron_trigger WHERE id = ANY(%s)',
                        [list(setup_trigger_ids)],
                    )
                running_cr.commit()
            with registry.cursor() as verify_cr:
                verify_cr.execute(
                    'SELECT count(*) FROM ir_cron_trigger WHERE id = ANY(%s)',
                    [list(write_trigger_ids)],
                )
                self.assertEqual(verify_cr.fetchone()[0], len(write_trigger_ids))
        finally:
            with registry.cursor() as cleanup_cr:
                cleanup_env = api.Environment(cleanup_cr, self.env.uid, {})
                cleanup_cr.execute(
                    'SELECT id FROM ir_cron_trigger WHERE cron_id = %s', [cron_id]
                )
                before_unlink_ids = {row[0] for row in cleanup_cr.fetchall()}
                line = cleanup_env['op.subject.to.batch'].browse(fixture_ids['line']).exists()
                if line:
                    line.unlink()
                cleanup_cr.execute(
                    'SELECT id FROM ir_cron_trigger WHERE cron_id = %s', [cron_id]
                )
                unlink_trigger_ids = {
                    row[0] for row in cleanup_cr.fetchall() if row[0] not in before_unlink_ids
                }
                owned_trigger_ids.update(unlink_trigger_ids)
                cleanup_env['op.batch'].browse(fixture_ids['batch']).exists().unlink()
                cleanup_env['op.course'].browse(fixture_ids['course']).exists().unlink()
                cleanup_env['op.subject'].browse(fixture_ids['subject']).exists().unlink()
                if owned_trigger_ids:
                    cleanup_cr.execute(
                        'DELETE FROM ir_cron_trigger WHERE id = ANY(%s)',
                        [list(owned_trigger_ids)],
                    )
                cleanup_cr.commit()
            with registry.cursor() as cleanup_verify_cr:
                cleanup_verify_cr.execute(
                    'SELECT count(*) FROM ir_cron_trigger WHERE id = ANY(%s)',
                    [list(owned_trigger_ids) or [0]],
                )
                self.assertEqual(cleanup_verify_cr.fetchone()[0], 0)
                cleanup_verify_cr.execute(
                    'SELECT count(*) FROM ir_cron_trigger WHERE id = ANY(%s)',
                    [list(baseline_ids) or [0]],
                )
                self.assertEqual(cleanup_verify_cr.fetchone()[0], len(baseline_ids))
            self.env.invalidate_all()

    def test_mass_archive_ratio_zero_when_initial_scope_has_no_active_memberships(self):
        admission, _lines = self._create_transition_case(
            initial_active_count=0, archived_count=0, activated_count=1,
        )

        self.env['op.admission'].cron_auto_enroll_student()

        self.assertEqual(len(self._memberships(admission).filtered('active')), 1)

    def test_mass_archive_guard_allows_single_archive_in_larger_initial_scope(self):
        admission, _lines = self._create_transition_case(
            initial_active_count=10, archived_count=1,
        )

        self.env['op.admission'].cron_auto_enroll_student()

        memberships = self._memberships(admission)
        self.assertEqual(len(memberships.filtered('active')), 9)
        self.assertEqual(len(memberships.filtered(lambda membership: not membership.active)), 1)

    def test_mass_archive_guard_allows_exactly_thirty_percent(self):
        admission, _lines = self._create_transition_case(
            initial_active_count=10, archived_count=3,
        )

        self.env['op.admission'].cron_auto_enroll_student()

        memberships = self._memberships(admission)
        self.assertEqual(len(memberships.filtered('active')), 7)
        self.assertEqual(len(memberships.filtered(lambda membership: not membership.active)), 3)

    def test_same_partner_channel_batch_cannot_have_two_active_memberships(self):
        _admission, _subject, channel, batch, _line = self._create_admission_case()
        partner = self.env['res.partner'].create({'name': 'Unique membership student'})
        values = {'partner_id': partner.id, 'channel_id': channel.id, 'batch_id': batch.id}
        self.env['slide.channel.partner'].create(values)
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.env['slide.channel.partner'].create(values)

    def test_partial_unique_index_is_installed_and_uninstall_hook_drops_it(self):
        index_name = 'irg_scp_active_partner_channel_batch_uniq'
        self.assertTrue(tools.index_exists(self.env.cr, index_name))
        uninstall_hook(self.env.cr, self.env.registry)
        self.assertFalse(tools.index_exists(self.env.cr, index_name))
        self.env.cr.execute("""
            CREATE UNIQUE INDEX irg_scp_active_partner_channel_batch_uniq
                ON slide_channel_partner (partner_id, channel_id, batch_id)
             WHERE active IS TRUE AND batch_id IS NOT NULL
        """)
        self.assertTrue(tools.index_exists(self.env.cr, index_name))

    def test_index_preflight_rejects_existing_active_duplicate_without_deleting_it(self):
        _admission, _subject, channel, batch, _line = self._create_admission_case()
        partner = self.env['res.partner'].create({'name': 'Preflight duplicate student'})
        membership = self.env['slide.channel.partner'].create({
            'partner_id': partner.id, 'channel_id': channel.id, 'batch_id': batch.id,
        })
        index_name = 'irg_scp_active_partner_channel_batch_uniq'
        tools.drop_index(self.env.cr, index_name, 'slide_channel_partner')
        try:
            self.env.cr.execute("""
                INSERT INTO slide_channel_partner
                    (partner_id, channel_id, batch_id, active,
                     create_uid, write_uid, create_date, write_date)
                SELECT partner_id, channel_id, batch_id, active,
                       create_uid, write_uid, create_date, write_date
                  FROM slide_channel_partner
                 WHERE id = %s
                RETURNING id
            """, [membership.id])
            duplicate_id = self.env.cr.fetchone()[0]

            with self.assertRaises(ValidationError):
                self.env['slide.channel.partner']._irg_assert_no_active_membership_duplicates()

            self.env.cr.execute(
                'SELECT count(*) FROM slide_channel_partner WHERE id IN %s',
                [(membership.id, duplicate_id)],
            )
            self.assertEqual(self.env.cr.fetchone()[0], 2)
        finally:
            self.env.cr.execute(
                'DELETE FROM slide_channel_partner '
                'WHERE partner_id = %s AND channel_id = %s AND batch_id = %s AND id != %s',
                [partner.id, channel.id, batch.id, membership.id],
            )
            self.env.cr.execute("""
                CREATE UNIQUE INDEX irg_scp_active_partner_channel_batch_uniq
                    ON slide_channel_partner (partner_id, channel_id, batch_id)
                 WHERE active IS TRUE AND batch_id IS NOT NULL
            """)

    def test_same_partner_channel_different_batch_is_allowed_by_index(self):
        _admission, _subject, channel, batch, _line = self._create_admission_case()
        other_batch = batch.copy({'name': 'Other robust batch', 'code': 'ROBUST-OTHER'})
        partner = self.env['res.partner'].create({'name': 'Cross batch student'})
        Membership = self.env['slide.channel.partner']
        Membership.create({'partner_id': partner.id, 'channel_id': channel.id, 'batch_id': batch.id})
        Membership.create({
            'partner_id': partner.id, 'channel_id': channel.id, 'batch_id': other_batch.id,
        })
        self.assertEqual(Membership.search_count([
            ('partner_id', '=', partner.id), ('channel_id', '=', channel.id),
        ]), 2)

    def test_concurrent_auto_enroll_keeps_one_active_membership(self):
        registry = Registry(self.env.cr.dbname)
        identifiers = self._create_committed_admission_case(registry)
        button_cr = registry.cursor()
        cron_errors = []

        def run_cron_transaction():
            try:
                with registry.cursor() as cron_cr:
                    cron_env = api.Environment(cron_cr, self.env.uid, {})
                    cron_env['op.admission'].cron_auto_enroll_student()
                    cron_cr.commit()
            except Exception as exc:  # surfaced in the main test thread below
                cron_errors.append(exc)

        try:
            button_env = api.Environment(button_cr, self.env.uid, {})
            button_env['op.admission'].browse(identifiers['admission']).auto_enroll_student()
            cron_thread = Thread(target=run_cron_transaction)
            cron_thread.start()
            cron_thread.join(timeout=0.25)
            self.assertTrue(cron_thread.is_alive(), 'cron transaction did not contend on the membership')
            button_cr.commit()
            cron_thread.join(timeout=10)
            self.assertFalse(cron_thread.is_alive(), 'cron transaction remained blocked')
            self.assertFalse(cron_errors)
            with registry.cursor() as verify_cr:
                verify_env = api.Environment(verify_cr, self.env.uid, {})
                count = verify_env['slide.channel.partner'].search_count([
                    ('partner_id', '=', identifiers['partner']),
                    ('channel_id', '=', identifiers['channel']),
                    ('batch_id', '=', identifiers['batch']),
                    ('active', '=', True),
                ])
                self.assertEqual(count, 1)
        finally:
            button_cr.rollback()
            button_cr.close()
            self._cleanup_committed_admission_case(registry, identifiers)
            self.env.invalidate_all()

    def test_homeclass_to_online_uses_clone_and_both_memberships_coexist(self):
        admission, subject, home_channel, batch, _line = self._create_admission_case()
        batch.code = 'ROBUST-ONL'
        online_channel = self._link_online_clone(home_channel)
        home_membership = self.env['slide.channel.partner'].with_context(
            irg_skip_partner_sync=True,
        ).create({
            'partner_id': admission.partner_id.id, 'channel_id': home_channel.id,
            'batch_id': batch.id, 'op_subject_id': subject.id,
            'admission_id': admission.id,
        })

        admission._irg_reconcile_online_clone_channel_partners()

        online_membership = self.env['slide.channel.partner'].search([
            ('partner_id', '=', admission.partner_id.id),
            ('channel_id', '=', online_channel.id), ('batch_id', '=', batch.id),
        ])
        self.assertEqual(len(online_membership), 1)
        self.assertTrue(home_membership.active)
        self.assertTrue(online_membership.active)

    def test_clone_sync_does_not_reassign_membership_from_other_batch(self):
        admission, subject, home_channel, batch, _line = self._create_admission_case()
        batch.code = 'ROBUST-ONL'
        online_channel = self._link_online_clone(home_channel)
        other_batch = batch.copy({'name': 'Clone other batch', 'code': 'CLONE-OTHER'})
        other_membership = self.env['slide.channel.partner'].with_context(
            active_test=False, irg_skip_partner_sync=True,
        ).create({
            'partner_id': admission.partner_id.id, 'channel_id': online_channel.id,
            'batch_id': other_batch.id, 'op_subject_id': subject.id, 'active': False,
        })
        self.env['slide.channel.partner'].with_context(irg_skip_partner_sync=True).create({
            'partner_id': admission.partner_id.id, 'channel_id': home_channel.id,
            'batch_id': batch.id, 'op_subject_id': subject.id,
            'admission_id': admission.id,
        })

        admission._irg_reconcile_online_clone_channel_partners()

        other_membership.invalidate_recordset()
        self.assertEqual(other_membership.batch_id, other_batch)
        self.assertEqual(self.env['slide.channel.partner'].with_context(active_test=False).search_count([
            ('partner_id', '=', admission.partner_id.id),
            ('channel_id', '=', online_channel.id), ('batch_id', '=', batch.id),
        ]), 1)

    def test_active_membership_is_preferred_over_older_archived_membership(self):
        admission, subject, channel, batch, _line = self._create_admission_case()
        Membership = self.env['slide.channel.partner'].with_context(active_test=False)
        archived = Membership.create({
            'partner_id': admission.partner_id.id, 'channel_id': channel.id,
            'batch_id': batch.id, 'op_subject_id': subject.id, 'active': False,
        })
        active = Membership.create({
            'partner_id': admission.partner_id.id, 'channel_id': channel.id,
            'batch_id': batch.id, 'op_subject_id': subject.id,
        })

        admission.auto_enroll_student()

        self.assertFalse(archived.active)
        self.assertTrue(active.active)
        self.assertEqual(active.admission_id, admission)

    def test_archived_membership_is_reactivated_without_duplicate(self):
        admission, subject, channel, batch, _line = self._create_admission_case()
        membership = self.env['slide.channel.partner'].create({
            'partner_id': admission.partner_id.id, 'channel_id': channel.id,
            'batch_id': batch.id, 'op_subject_id': subject.id, 'active': False,
        })
        admission.auto_enroll_student()
        memberships = self.env['slide.channel.partner'].with_context(active_test=False).search([
            ('partner_id', '=', admission.partner_id.id), ('channel_id', '=', channel.id),
            ('batch_id', '=', batch.id),
        ])
        self.assertEqual(memberships.ids, membership.ids)
        self.assertTrue(memberships.active)

    def test_historical_completed_parent_same_batch_unlocks_child(self):
        parent = self.env['op.subject'].create({'name': 'Parent same batch', 'code': 'P-SAME'})
        child = self.env['op.subject'].create({
            'name': 'Child same batch', 'code': 'C-SAME', 'parent_subject_id': parent.id,
        })
        admission, _subject, _channel, batch, _line = self._create_admission_case(child)
        parent_channel = self.env['slide.channel'].create({'name': 'Parent same channel'})
        self.env['slide.channel.partner'].create({
            'partner_id': admission.partner_id.id, 'channel_id': parent_channel.id,
            'batch_id': batch.id, 'op_subject_id': parent.id,
            'completed': True, 'active': False,
        })
        self.assertTrue(admission._irg_subject_precedence_is_satisfied(child))

    def test_historical_completed_parent_other_batch_does_not_unlock_child(self):
        parent = self.env['op.subject'].create({'name': 'Parent other batch', 'code': 'P-OTHER'})
        child = self.env['op.subject'].create({
            'name': 'Child other batch', 'code': 'C-OTHER', 'parent_subject_id': parent.id,
        })
        admission, _subject, _channel, batch, _line = self._create_admission_case(child)
        other_batch = batch.copy({'name': 'Historical other batch', 'code': 'HIST-OTHER'})
        parent_channel = self.env['slide.channel'].create({'name': 'Parent other channel'})
        self.env['slide.channel.partner'].create({
            'partner_id': admission.partner_id.id, 'channel_id': parent_channel.id,
            'batch_id': other_batch.id, 'op_subject_id': parent.id,
            'completed': True, 'active': False,
        })
        self.assertFalse(admission._irg_subject_precedence_is_satisfied(child))

    def test_cron_processes_manual_modality(self):
        admission, _subject, channel, batch, _line = self._create_admission_case()

        self.env['op.admission'].cron_auto_enroll_student()

        self.assertEqual(self.env['slide.channel.partner'].search_count([
            ('partner_id', '=', admission.partner_id.id),
            ('channel_id', '=', channel.id), ('batch_id', '=', batch.id),
        ]), 1)

    def test_cron_and_button_produce_equivalent_memberships(self):
        button_admission, _subject, _channel, _batch, _line = self._create_admission_case()
        cron_admission, _subject2, _channel2, _batch2, _line2 = self._create_admission_case()
        cron_admission.partner_id = self.env['res.partner'].create({'name': 'Cron student'})
        button_admission.auto_enroll_student()

        self.env['op.admission'].cron_auto_enroll_student()

        button_membership = self._memberships(button_admission)
        cron_membership = self._memberships(cron_admission)
        self.assertEqual(len(button_membership), 1)
        self.assertEqual(len(cron_membership), 1)
        compared_fields = ('active', 'date_from', 'date_to')
        self.assertEqual(
            [button_membership[field] for field in compared_fields],
            [cron_membership[field] for field in compared_fields],
        )
        self.assertEqual(button_membership.course_id, button_admission.course_id)
        self.assertEqual(cron_membership.course_id, cron_admission.course_id)
        self.assertEqual(button_membership.register_id, button_admission.register_id)
        self.assertEqual(cron_membership.register_id, cron_admission.register_id)
        self.assertEqual(button_membership.op_subject_id, _subject)
        self.assertEqual(cron_membership.op_subject_id, _subject2)

    def test_cron_continues_after_one_admission_fails(self):
        failing, _subject, _channel, _batch, _line = self._create_admission_case()
        succeeding, _subject2, channel, batch, _line2 = self._create_admission_case()
        original = type(failing).auto_enroll_student

        def fail_one(records):
            if failing.id in records.ids:
                raise RuntimeError('expected isolated admission failure')
            return original(records)

        with patch.object(type(failing), 'auto_enroll_student', fail_one):
            self.env['op.admission'].cron_auto_enroll_student()

        self.assertFalse(self._memberships(failing))
        self.assertEqual(self.env['slide.channel.partner'].search_count([
            ('partner_id', '=', succeeding.partner_id.id),
            ('channel_id', '=', channel.id), ('batch_id', '=', batch.id),
        ]), 1)

    def test_mass_archive_guard_rolls_back_above_thirty_percent(self):
        admission, _lines = self._create_transition_case(
            initial_active_count=10, archived_count=4,
        )
        before = {membership.id: membership.active for membership in self._memberships(admission)}

        with self.assertRaises(ValidationError):
            self.env['op.admission'].cron_auto_enroll_student()

        self.env.invalidate_all()
        after = {membership.id: membership.active for membership in self._memberships(admission)}
        self.assertEqual(after, before)

    def test_date_change_past_archives_future_reactivates_and_two_runs_are_idempotent(self):
        admission, lines = self._create_transition_case(
            initial_active_count=10, archived_count=0,
        )
        line = lines[:1]
        memberships = self._memberships(admission)
        membership_ids = memberships.ids
        line.write({'date_to': date.today() - timedelta(days=1)})

        self.env['op.admission'].cron_auto_enroll_student()
        target_membership = self._memberships(admission).filtered(
            lambda membership: membership.op_subject_id == line.subject_id
        )
        self.assertFalse(target_membership.active)
        line.write({'date_to': date.today() + timedelta(days=1)})
        self.env['op.admission'].cron_auto_enroll_student()
        self.env['op.admission'].cron_auto_enroll_student()

        memberships = self._memberships(admission)
        self.assertEqual(memberships.ids, membership_ids)
        self.assertEqual(len(memberships.filtered('active')), 10)

    def test_cron_online_branch_end_to_end_without_batch_dates(self):
        admission, subject, channel, batch, _line = self._create_admission_case()
        batch.code = 'ROBUST-ONL'
        batch.subject_to_batch_ids.unlink()
        admission.admission_date = date.today()

        self.env['op.admission'].cron_auto_enroll_student()

        membership = self._memberships(admission).filtered(
            lambda record: record.channel_id == channel and record.op_subject_id == subject
        )
        self.assertEqual(len(membership), 1)
        self.assertTrue(membership.active)
