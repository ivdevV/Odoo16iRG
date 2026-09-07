from datetime import date, timedelta
from unittest.mock import patch
from uuid import uuid4

from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import HttpCase, TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestTfmElearning(TransactionCase):
    """RED suite for TFM eLearning visibility and membership provenance."""

    def _suffix(self):
        return uuid4().hex[:8]

    def _portal_case(self, channel=None, progress=50):
        suffix = self._suffix()
        partner = self.env['res.partner'].create({
            'name': 'TFM eLearning %s' % suffix,
            'email': 'tfm.elearning.%s@example.test' % suffix,
        })
        user = new_test_user(
            self.env,
            login=partner.email,
            groups='base.group_portal',
            name=partner.name,
        )
        user.partner_id = partner
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'user_id': user.id,
            'first_name': 'TFM',
            'last_name': suffix,
            'gender': 'o',
        })
        channel = channel or self.env['slide.channel'].create({
            'name': 'TFM eLearning channel %s' % suffix,
        })
        course = self.env['op.course'].create({
            'name': 'TFM eLearning course %s' % suffix,
            'code': 'TFM-ELEARN-%s' % suffix,
            'lang': 'en_US',
            'activate_tesis': True,
            'irg_tfm_channel_id': channel.id,
        })
        batch = self.env['op.batch'].create({
            'name': 'TFM eLearning batch %s' % suffix,
            'code': 'HC2511',
            'course_id': course.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
        })
        enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
            'roll_number': 'TFM-ELEARN-%s' % suffix,
        })
        with patch.object(
            type(enrollment),
            '_irg_tfm_completion_percentage',
            return_value=progress,
        ):
            thesis = enrollment._irg_ensure_tfm_record()
        return user, partner, student, channel, course, batch, enrollment, thesis

    def _convocation(self, name='Current'):
        today = date.today()
        return self.env['irg.tfm.convocatoria'].create({
            'name': '%s %s' % (name, self._suffix()),
            'code': 'ELEARN-%s' % self._suffix(),
            'partial_open_date': today,
            'partial_close_date': today,
            'final_open_date': today,
            'final_close_date': today,
        })

    def _category(self, channel, convocations=None, name='TFM category'):
        values = {
            'name': '%s %s' % (name, self._suffix()),
            'channel_id': channel.id,
            'is_category': True,
        }
        category = self.env['slide.slide'].create(values)
        if convocations:
            category.write({'irg_tfm_convocation_ids': [Command.set(convocations.ids)]})
        return category

    def _content(self, channel, category=None, parent=None, name='TFM content'):
        return self.env['slide.slide'].create({
            'name': '%s %s' % (name, self._suffix()),
            'channel_id': channel.id,
            'category_id': category.id if category else False,
            'parent_slide_id': parent.id if parent else False,
            'slide_category': 'article',
        })

    def test_tfm_convocation_field_is_configurable_only_on_categories(self):
        self.assertIn('irg_tfm_convocation_ids', self.env['slide.slide']._fields)
        _user, _partner, _student, channel, _course, _batch, _enrollment, _thesis = self._portal_case()
        convocation = self._convocation()
        category = self._category(channel, convocation)
        self.assertEqual(category.irg_tfm_convocation_ids, convocation)
        content = self._content(channel, category=category)
        with self.assertRaises(ValidationError):
            content.write({'irg_tfm_convocation_ids': [Command.set(convocation.ids)]})

    def test_content_inherits_category_or_parent_restriction_and_empty_is_common(self):
        _user, _partner, _student, channel, _course, _batch, _enrollment, _thesis = self._portal_case()
        convocation = self._convocation()
        category = self._category(channel, convocation)
        child = self._content(channel, category=category)
        self.assertEqual(child._irg_effective_tfm_convocation_ids(), convocation)
        common = self._content(channel)
        self.assertFalse(common._irg_effective_tfm_convocation_ids())

        parent = self._category(channel, name='Parent')
        parent.write({'irg_tfm_convocation_ids': [Command.set(convocation.ids)]})
        nested = self._content(channel, parent=parent)
        self.assertEqual(nested._irg_effective_tfm_convocation_ids(), convocation)

    def test_exclusive_predicate_fails_closed_for_public_outsider_ambiguity_and_foreign_membership(self):
        owner, partner, student, channel, course, batch, enrollment, thesis = self._portal_case()
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        category = self._category(channel, convocation)
        slide = self._content(channel, category=category)
        self.assertTrue(slide.is_user_allowed_by_tfm_convocation(self.env.user))
        self.assertTrue(slide.is_user_allowed_by_tfm_convocation(owner))

        outsider, _op, _os, _oc, _course, _batch, _enrollment, _thesis = self._portal_case(
            channel=channel,
        )
        self.assertFalse(slide.is_user_allowed_by_tfm_convocation(outsider))
        self.assertFalse(
            slide.is_user_allowed_by_tfm_convocation(self.env.ref('base.public_user'))
        )

        self.env['slide.channel.partner'].sudo().create({
            'partner_id': partner.id,
            'channel_id': channel.id,
            'batch_id': batch.id,
        })
        other_course = self.env['op.course'].create({
            'name': 'Ambiguous TFM course %s' % self._suffix(),
            'code': 'TFM-AMB-%s' % self._suffix(),
            'lang': 'en_US',
            'activate_tesis': True,
            'irg_tfm_channel_id': channel.id,
        })
        other_batch = self.env['op.batch'].create({
            'name': 'Ambiguous TFM batch %s' % self._suffix(),
            'code': 'HC2511',
            'course_id': other_course.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
        })
        ambiguous_enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': other_course.id,
            'batch_id': other_batch.id,
            'roll_number': 'TFM-AMB-%s' % self._suffix(),
        })
        with patch.object(
            type(ambiguous_enrollment),
            '_irg_tfm_completion_percentage',
            return_value=50,
        ):
            ambiguous_enrollment._irg_ensure_tfm_record()
        self.assertFalse(slide.is_user_allowed_by_tfm_convocation(owner))

    def test_assignment_requires_tfm_channel_and_reconciles_idempotently(self):
        _user, _partner, _student, _channel, _course, _batch, _enrollment, thesis = self._portal_case()
        convocation = self._convocation()
        thesis.course_id.course_id.write({'irg_tfm_channel_id': False})
        with self.assertRaisesRegex(ValidationError, 'channel'):
            thesis.write({'irg_tfm_convocation_id': convocation.id})

        _user, partner, _student, channel, _course, batch, _enrollment, thesis = self._portal_case()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        membership_model = self.env['slide.channel.partner'].sudo().with_context(active_test=False)
        memberships = membership_model.search([
            ('partner_id', '=', partner.id),
            ('channel_id', '=', channel.id),
            ('batch_id', '=', batch.id),
        ])
        self.assertEqual(len(memberships), 1)
        self.assertTrue(memberships.irg_tfm_created)
        self.assertIn(thesis.id, memberships.irg_tfm_thesis_ids.ids)
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        self.assertEqual(membership_model.search_count([
            ('partner_id', '=', partner.id),
            ('channel_id', '=', channel.id),
            ('batch_id', '=', batch.id),
            ('active', '=', True),
        ]), 1)

    def test_foreign_active_and_archived_memberships_are_never_modified_or_reactivated(self):
        _user, partner, _student, channel, _course, batch, _enrollment, thesis = self._portal_case()
        membership_model = self.env['slide.channel.partner'].sudo().with_context(active_test=False)
        foreign_active = membership_model.create({
            'partner_id': partner.id,
            'channel_id': channel.id,
            'batch_id': batch.id,
        })
        foreign_archived = membership_model.create({
            'partner_id': partner.id,
            'channel_id': channel.id,
            'batch_id': batch.id,
            'active': False,
        })
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        self.assertTrue(foreign_active.active)
        self.assertFalse(foreign_active.irg_tfm_created)
        self.assertFalse(foreign_active.irg_tfm_thesis_ids)
        self.assertFalse(foreign_archived.active)
        self.assertFalse(foreign_archived.irg_tfm_created)
        self.assertFalse(foreign_archived.irg_tfm_thesis_ids)

    def test_shared_tfm_membership_removal_keeps_remaining_thesis_and_is_idempotent(self):
        _user, partner, student, channel, course, batch, _enrollment, thesis = self._portal_case()
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})

        other_course = self.env['op.course'].create({
            'name': 'TFM shared course %s' % self._suffix(),
            'code': 'TFM-SHARED-COURSE-%s' % self._suffix(),
            'lang': 'en_US',
            'activate_tesis': True,
            'parent_id': course.id,
            'irg_tfm_channel_id': channel.id,
        })
        second_enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': other_course.id,
            'batch_id': batch.id,
            'roll_number': 'TFM-SHARED-%s' % self._suffix(),
        })
        with patch.object(
            type(second_enrollment),
            '_irg_tfm_completion_percentage',
            return_value=50,
        ):
            second_enrollment._irg_ensure_tfm_record()
        self.assertNotEqual(second_enrollment.course_id, thesis.course_id.course_id)
        self.assertEqual(second_enrollment.batch_id, batch)
        self.assertEqual(second_enrollment.course_id.irg_tfm_channel_id, channel)
        second_thesis = self.env['tesis.model'].search([
            ('course_id', '=', second_enrollment.id),
        ], limit=1)
        self.assertTrue(second_thesis, 'eligible second enrollment must create a TFM thesis')
        second_thesis.write({'irg_tfm_convocation_id': convocation.id})

        membership = self.env['slide.channel.partner'].sudo().with_context(active_test=False).search([
            ('partner_id', '=', partner.id),
            ('channel_id', '=', channel.id),
            ('batch_id', '=', batch.id),
        ], limit=1)
        self.assertTrue(membership.active)
        self.assertEqual(
            set(membership.irg_tfm_thesis_ids.ids),
            {thesis.id, second_thesis.id},
        )

        thesis.write({'irg_tfm_convocation_id': False})
        thesis.write({'irg_tfm_convocation_id': False})
        membership.invalidate_recordset()
        self.assertTrue(membership.active)
        self.assertEqual(membership.irg_tfm_thesis_ids.ids, second_thesis.ids)

        second_thesis.write({'irg_tfm_convocation_id': False})
        membership.invalidate_recordset()
        self.assertFalse(membership.active)
        self.assertFalse(membership.irg_tfm_thesis_ids)
        self.assertTrue(membership.exists())

    def test_removal_keeps_foreign_signals_active(self):
        _user, partner, _student, channel, _course, batch, _enrollment, thesis = self._portal_case()
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        membership = self.env['slide.channel.partner'].sudo().with_context(active_test=False).search([
            ('partner_id', '=', partner.id),
            ('channel_id', '=', channel.id),
            ('batch_id', '=', batch.id),
        ], limit=1)
        membership.write({'course_id': thesis.course_id.course_id.id})
        thesis.write({'irg_tfm_convocation_id': False})
        membership.invalidate_recordset()
        self.assertTrue(membership.active)

    def test_reassignment_reconciles_source_and_destination_channels_without_touching_history(self):
        _user, partner, _student, source, course, batch, _enrollment, thesis = self._portal_case()
        destination = self.env['slide.channel'].create({'name': 'TFM destination %s' % self._suffix()})
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        source_membership = self.env['slide.channel.partner'].sudo().with_context(active_test=False).search([
            ('partner_id', '=', partner.id),
            ('channel_id', '=', source.id),
            ('batch_id', '=', batch.id),
        ], limit=1)
        course.write({'irg_tfm_channel_id': destination.id})
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        source_membership.invalidate_recordset()
        self.assertFalse(source_membership.active)
        destination_membership = self.env['slide.channel.partner'].sudo().search([
            ('partner_id', '=', partner.id),
            ('channel_id', '=', destination.id),
            ('batch_id', '=', batch.id),
            ('active', '=', True),
        ])
        self.assertEqual(len(destination_membership), 1)
        self.assertIn(thesis.id, destination_membership.irg_tfm_thesis_ids.ids)

    def test_backend_category_view_exposes_internal_convocation_tags_and_help(self):
        view = self.env.ref('irg_tfm_convocatorias.view_slide_slide_form_tfm_convocations')
        arch = etree.fromstring(view.get_combined_arch())
        field_nodes = arch.xpath("//field[@name='irg_tfm_convocation_ids']")
        self.assertTrue(field_nodes)
        self.assertTrue(any(node.get('help') or node.get('string') for node in field_nodes))

    def test_controller_and_qweb_keep_batch_practice_and_date_layers(self):
        controller_path = __import__(
            'pathlib', fromlist=['Path'],
        ).Path(__file__).resolve().parents[1] / 'controllers' / 'portal.py'
        source = controller_path.read_text(encoding='utf-8')
        self.assertIn('WebsiteSlidesPracticeRestrictions', source)
        self.assertIn('irg_practice_slide_restrictions', source)
        self.assertIn('return super().slide_view(slide, **kwargs)', source)
        self.assertIn('tfm_blocked_slide_ids', source)
        self.assertNotIn('.action_set_viewed(', source)
        template = self.env.ref('irg_tfm_convocatorias.slide_fullscreen_sidebar_tfm_hide')
        template_arch = (template.get_combined_arch() or '').lower()
        self.assertIn('batch_blocked_slide_ids', template_arch)
        self.assertIn('practice_blocked_slide_ids', template_arch)
        self.assertIn('tfm_blocked_slide_ids', template_arch)
        section_template = self.env.ref(
            'irg_tfm_convocatorias.fullscreen_sidebar_hide_tfm_sections',
        )
        section_arch = (section_template.get_combined_arch() or '').lower()
        self.assertIn('allowed_batch_ids', section_arch)
        self.assertIn('irg_has_practice_requirement', section_arch)
        self.assertIn('irg_has_tfm_requirement', section_arch)
        section_listing = self.env.ref(
            'irg_tfm_convocatorias.course_slides_list_hide_tfm_sections',
        )
        section_listing_arch = (section_listing.get_combined_arch() or '').lower()
        self.assertIn('allowed_batch_ids', section_listing_arch)
        self.assertIn('irg_has_practice_requirement', section_listing_arch)
        self.assertIn('irg_has_tfm_requirement', section_listing_arch)
        batch_controller_path = (
            controller_path.parents[3]
            / 'addons_uisep' / 'irg_batch_slide_restrictions'
            / 'controllers' / 'main.py'
        )
        self.assertIn('scheduled_date', batch_controller_path.read_text(encoding='utf-8'))
        listing = self.env.ref('irg_tfm_convocatorias.course_slides_list_hide_tfm_content')
        listing_arch = (listing.get_combined_arch() or '').lower()
        self.assertIn('irg_has_tfm_requirement', listing_arch)


@tagged('post_install', '-at_install')
class TestTfmElearningHttp(HttpCase):
    """Exercise the TFM guard through the public slide HTTP route."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        suffix = uuid4().hex[:8]
        password = 'tfm-elearning-http'
        portal_group = cls.env.ref('base.group_portal')
        cls.owner = cls.env['res.users'].with_context(
            no_reset_password=True,
        ).create({
            'name': 'TFM HTTP owner %s' % suffix,
            'login': 'tfm-http-owner-%s@example.test' % suffix,
            'password': password,
            'groups_id': [(6, 0, portal_group.ids)],
        })
        cls.outsider = cls.env['res.users'].with_context(
            no_reset_password=True,
        ).create({
            'name': 'TFM HTTP outsider %s' % suffix,
            'login': 'tfm-http-outsider-%s@example.test' % suffix,
            'password': password,
            'groups_id': [(6, 0, portal_group.ids)],
        })
        cls.student = cls.env['op.student'].create({
            'partner_id': cls.owner.partner_id.id,
            'user_id': cls.owner.id,
            'first_name': 'TFM HTTP',
            'last_name': suffix,
            'gender': 'o',
        })
        cls.channel = cls.env['slide.channel'].create({
            'name': 'TFM HTTP channel %s' % suffix,
            'is_published': True,
        })
        course = cls.env['op.course'].create({
            'name': 'TFM HTTP course %s' % suffix,
            'code': 'TFM-HTTP-%s' % suffix,
            'lang': 'en_US',
            'activate_tesis': True,
            'irg_tfm_channel_id': cls.channel.id,
        })
        batch = cls.env['op.batch'].create({
            'name': 'TFM HTTP batch %s' % suffix,
            'code': 'HC2511',
            'course_id': course.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
        })
        enrollment = cls.env['op.student.course'].create({
            'student_id': cls.student.id,
            'course_id': course.id,
            'batch_id': batch.id,
            'roll_number': 'TFM-HTTP-%s' % suffix,
        })
        with patch.object(
            type(enrollment),
            '_irg_tfm_completion_percentage',
            return_value=50,
        ):
            cls.thesis = enrollment._irg_ensure_tfm_record()
        today = date.today()
        convocation = cls.env['irg.tfm.convocatoria'].create({
            'name': 'TFM HTTP current %s' % suffix,
            'code': 'TFM-HTTP-CONV-%s' % suffix,
            'partial_open_date': today,
            'partial_close_date': today,
            'final_open_date': today,
            'final_close_date': today,
        })
        cls.thesis.write({'irg_tfm_convocation_id': convocation.id})
        cls.category = cls.env['slide.slide'].create({
            'name': 'TFM HTTP restricted category %s' % suffix,
            'channel_id': cls.channel.id,
            'is_category': True,
            'is_published': True,
        })
        cls.category.write({
            'irg_tfm_convocation_ids': [Command.set(convocation.ids)],
        })
        cls.slide = cls.env['slide.slide'].create({
            'name': 'TFM HTTP restricted slide %s' % suffix,
            'channel_id': cls.channel.id,
            'category_id': cls.category.id,
            'slide_category': 'article',
            'is_published': True,
        })
        cls.password = password

    def test_restricted_slide_route_denies_before_inherited_controller_and_allows_owner(self):
        membership_model = self.env['slide.slide.partner'].sudo()
        self.authenticate(self.outsider.login, self.password)
        before = membership_model.search_count([
            ('slide_id', '=', self.slide.id),
            ('partner_id', '=', self.outsider.partner_id.id),
        ])
        response = self.url_open('/slides/slide/%s' % self.slide.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Contenido Bloqueado', response.text)
        self.assertNotIn(self.slide.name, response.text)
        self.assertEqual(before, membership_model.search_count([
            ('slide_id', '=', self.slide.id),
            ('partner_id', '=', self.outsider.partner_id.id),
        ]))

        self.authenticate(self.owner.login, self.password)
        response = self.url_open('/slides/slide/%s' % self.slide.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.slide.name, response.text)

    def test_tfm_category_and_content_are_omitted_from_channel_listing_for_outsider(self):
        listing_url = self.channel.website_url or '/slides/%s' % self.channel.id
        self.authenticate(self.outsider.login, self.password)
        response = self.url_open(listing_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.category.name, response.text)
        self.assertNotIn(self.slide.name, response.text)

        self.authenticate(self.owner.login, self.password)
        response = self.url_open(listing_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.category.name, response.text)
        self.assertIn(self.slide.name, response.text)
