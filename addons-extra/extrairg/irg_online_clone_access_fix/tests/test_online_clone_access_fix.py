import base64
from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOnlineCloneAccessFix(TransactionCase):
    def setUp(self):
        super().setUp()
        self.home_channel = self.env['slide.channel'].create({
            'name': 'HomeClass Clone Access Test',
            'channel_type': 'training',
        })
        self.online_channel = self.env['slide.channel'].create({
            'name': 'Online Clone Access Test',
            'channel_type': 'training',
            'irg_homeclass_channel_id': self.home_channel.id,
        })
        self.home_channel.irg_online_channel_id = self.online_channel
        self.subject = self.env['op.subject'].create({
            'name': 'Online Clone Access Subject',
            'code': 'IRG-OCAF',
            'slide_channel_id': self.home_channel.id,
        })
        self.course = self.env['op.course'].create({
            'name': 'Online Clone Access Course',
            'code': 'IRGOCAF',
            'subject_ids': [(6, 0, [self.subject.id])],
        })
        self.product = self.env['product.product'].create({
            'name': 'Online Clone Access Fee',
            'type': 'service',
        })
        self.register = self.env['op.admission.register'].create({
            'name': 'Online Clone Access Register',
            'course_id': self.course.id,
            'product_id': self.product.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
            'min_count': 1,
            'max_count': 30,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Online Clone Access Student',
            'email': 'online.clone.access@example.com',
        })

    def _create_batch_no_subject_dates(self, code='MOPCONL'):
        batch = self.env['op.batch'].create({
            'name': 'Online Clone Access %s' % code,
            'code': code,
            'course_id': self.course.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
        })
        batch.subject_to_batch_ids.unlink()
        return batch

    def _create_online_admission(self):
        return self.env['op.admission'].create({
            'first_name': 'Online',
            'last_name': 'Clone',
            'name': 'Online Clone Access',
            'birth_date': date(1990, 1, 1),
            'gender': 'o',
            'email': 'online.clone.access@example.com',
            'register_id': self.register.id,
            'course_id': self.course.id,
            'batch_id': self._create_batch_no_subject_dates().id,
            'admission_date': date.today(),
            'partner_id': self.partner.id,
            'state': 'done',
        })

    def test_effective_channel_returns_online_clone_for_online_admission(self):
        admission = self._create_online_admission()

        effective_channel = self.subject.irg_get_effective_slide_channel(self.partner, admission)

        self.assertEqual(effective_channel, self.online_channel)

    def test_opening_sync_creates_membership_on_online_clone(self):
        admission = self._create_online_admission()

        admission._irg_sync_online_channel_partners()

        memberships = self.env['slide.channel.partner'].search([
            ('partner_id', '=', self.partner.id),
            ('admission_id', '=', admission.id),
        ])
        self.assertEqual(memberships.channel_id, self.online_channel)
        self.assertEqual(memberships.admission_id, admission)
        self.assertEqual(memberships.batch_id, admission.batch_id)
        self.assertEqual(memberships.op_subject_id, self.subject)
        self.assertFalse(self.env['slide.channel.partner'].search([
            ('partner_id', '=', self.partner.id),
            ('channel_id', '=', self.home_channel.id),
            ('admission_id', '=', admission.id),
        ]))

    def test_reconcile_existing_homeclass_membership_creates_online_clone_membership(self):
        admission = self._create_online_admission()
        self.env['slide.channel.partner'].with_context(irg_skip_partner_sync=True).create({
            'active': True,
            'channel_id': self.home_channel.id,
            'partner_id': self.partner.id,
            'course_id': self.course.id,
            'batch_id': admission.batch_id.id,
            'op_subject_id': self.subject.id,
            'register_id': self.register.id,
            'admission_id': admission.id,
        })

        admission._irg_reconcile_online_clone_channel_partners()

        clone_membership = self.env['slide.channel.partner'].search([
            ('partner_id', '=', self.partner.id),
            ('channel_id', '=', self.online_channel.id),
            ('admission_id', '=', admission.id),
        ])
        self.assertEqual(len(clone_membership), 1)
        self.assertEqual(clone_membership.batch_id, admission.batch_id)
        self.assertEqual(clone_membership.op_subject_id, self.subject)

    def test_bootstrap_online_copies_document_binary_content(self):
        if 'document_binary_content' not in self.env['slide.slide']._fields:
            self.skipTest('slide.slide.document_binary_content is not available')

        pdf_content = base64.b64encode(b'%PDF-1.4 online clone access fix').decode('ascii')
        vals = {
            'name': 'Document With Binary Content',
            'channel_id': self.home_channel.id,
            'slide_category': 'document',
            'document_binary_content': pdf_content,
        }
        if 'document_binary_content_filename' in self.env['slide.slide']._fields:
            vals['document_binary_content_filename'] = 'document.pdf'
        source_slide = self.env['slide.slide'].create(vals)

        self.home_channel.action_copy_homeclass_to_online()

        cloned_slide = self.online_channel.slide_ids.filtered(
            lambda slide: slide.irg_original_slide_id == source_slide
        )
        self.assertEqual(len(cloned_slide), 1)
        self.assertEqual(cloned_slide.document_binary_content, source_slide.document_binary_content)
        if 'document_binary_content_filename' in cloned_slide._fields:
            self.assertEqual(cloned_slide.document_binary_content_filename, 'document.pdf')

    def test_repair_existing_online_clone_document_binary_content(self):
        if 'document_binary_content' not in self.env['slide.slide']._fields:
            self.skipTest('slide.slide.document_binary_content is not available')

        pdf_content = base64.b64encode(b'%PDF-1.4 repair existing clone').decode('ascii')
        source_slide = self.env['slide.slide'].create({
            'name': 'Original Document For Repair',
            'channel_id': self.home_channel.id,
            'slide_category': 'document',
            'document_binary_content': pdf_content,
        })
        cloned_slide = self.env['slide.slide'].create({
            'name': 'Original Document For Repair',
            'channel_id': self.online_channel.id,
            'slide_category': 'document',
            'irg_content_modality': 'online',
            'irg_original_slide_id': source_slide.id,
        })
        self.assertFalse(cloned_slide.document_binary_content)

        self.home_channel.action_repair_online_clone_documents()

        self.assertEqual(cloned_slide.document_binary_content, source_slide.document_binary_content)
