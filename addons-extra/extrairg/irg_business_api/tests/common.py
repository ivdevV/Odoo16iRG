# -*- coding: utf-8 -*-
"""Shared fixtures for irg_business_api tests."""
import json
import uuid
from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_business_api')
class IrgBusinessApiCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_api = cls.env.ref('irg_business_api.group_irg_business_api_user')
        cls.api_user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Lisa API',
            'login': 'lisa.api.%s' % uuid.uuid4().hex[:8],
            'email': 'lisa.api@example.com',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.group_api.id,
            ])],
        })
        cls.plain_user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Internal No API',
            'login': 'plain.api.%s' % uuid.uuid4().hex[:8],
            'email': 'plain.api@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.subject = cls.env['op.subject'].create({
            'name': 'API Subject A',
            'code': 'IRG-API-A-%s' % uuid.uuid4().hex[:6],
        })
        cls.subject_b = cls.env['op.subject'].create({
            'name': 'API Subject B',
            'code': 'IRG-API-B-%s' % uuid.uuid4().hex[:6],
            'parent_subject_id': cls.subject.id,
        })
        course_vals = {
            'name': 'API Course',
            'code': 'IRGAPI%s' % uuid.uuid4().hex[:4].upper(),
            'subject_ids': [(6, 0, [cls.subject.id, cls.subject_b.id])],
        }
        if 'lang' in cls.env['op.course']._fields:
            course_vals['lang'] = 'en_US'
        cls.course = cls.env['op.course'].create(course_vals)
        cls.batch = cls.env['op.batch'].create({
            'name': 'API Batch ONL',
            'code': 'MOPCONL%s' % uuid.uuid4().hex[:4].upper(),
            'course_id': cls.course.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
        })
        cls.channel = cls.env['slide.channel'].create({
            'name': 'API Channel',
            'channel_type': 'training',
            'is_published': True,
        })
        cls.section = cls.env['irg.slide.section'].create({
            'name': 'API Section',
            'sequence': 10,
            'channel_id': cls.channel.id,
        })
        cls.published_slide = cls.env['slide.slide'].create({
            'name': 'Published lesson',
            'channel_id': cls.channel.id,
            'slide_category': 'article',
            'html_content': '<p>Published</p>',
            'sequence': 10,
            'is_published': True,
            'irg_section_id': cls.section.id,
        })
        cls.draft_slide = cls.env['slide.slide'].create({
            'name': 'Draft lesson',
            'channel_id': cls.channel.id,
            'slide_category': 'article',
            'html_content': '<p>Draft</p>',
            'sequence': 20,
            'is_published': False,
            'irg_section_id': cls.section.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'API Fee',
            'type': 'service',
        })
        cls.register = cls.env['op.admission.register'].create({
            'name': 'API Register',
            'course_id': cls.course.id,
            'product_id': cls.product.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
            'min_count': 1,
            'max_count': 30,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'API Student',
            'email': 'api.student@example.com',
        })
        cls.admission = cls.env['op.admission'].create({
            'first_name': 'API',
            'last_name': 'Student',
            'name': 'API Student',
            'birth_date': date(1990, 1, 1),
            'gender': 'o',
            'email': 'api.student@example.com',
            'register_id': cls.register.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'admission_date': date(2026, 5, 7),
            'partner_id': cls.partner.id,
            'state': 'done',
        })
        cls.membership = cls.env['slide.channel.partner'].create({
            'channel_id': cls.channel.id,
            'partner_id': cls.partner.id,
            'batch_id': cls.batch.id,
            'op_subject_id': cls.subject.id,
            'admission_id': cls.admission.id,
            'date_from': date(2026, 1, 1),
            'date_to': date(2026, 6, 30),
            'active': True,
        })
        year_vals = {
            'name': 'API Year 2026',
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
        }
        cls.year = cls.env['op.academic.year'].create(year_vals)
        if 'op.academic.term' in cls.env:
            term_vals = {
                'name': 'API Term 1',
                'academic_year_id': cls.year.id,
            }
            Term = cls.env['op.academic.term']
            if 'term_start_date' in Term._fields:
                term_vals['term_start_date'] = date(2026, 1, 1)
                term_vals['term_end_date'] = date(2026, 6, 30)
            elif 'start_date' in Term._fields:
                term_vals['start_date'] = date(2026, 1, 1)
                term_vals['end_date'] = date(2026, 6, 30)
            cls.term = Term.create(term_vals)
        else:
            cls.term = False

    def api_env(self, user=None):
        return self.env['irg.api.operation'].with_user(user or self.api_user)

    def run_op(self, code, payload, key=None, user=None):
        key = key or 'k-%s' % uuid.uuid4().hex
        return self.api_env(user).create({
            'operation_code': code,
            'environment': 'test',
            'request_payload': json.dumps(payload),
            'idempotency_key': key,
        })

    def result_json(self, operation):
        return json.loads(operation.result_snapshot or '{}')

    def proposed_json(self, operation):
        return json.loads(operation.proposed_after or '{}')
