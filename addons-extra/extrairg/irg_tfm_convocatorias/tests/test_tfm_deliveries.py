import base64
import io
import re
import struct
from datetime import date, timedelta
from threading import Barrier, Event, Thread
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree

from odoo import api, Command, http
from odoo.exceptions import AccessError, ValidationError
from odoo.modules.registry import Registry
from odoo.tests.common import HttpCase, TransactionCase, tagged


PDF_BYTES = (
    b'%PDF-1.4\n'
    b'1 0 obj\n<</Type /Catalog>>\nendobj\n'
    b'xref\n0 2\n0000000000 65535 f \n0000000009 00000 n \n'
    b'trailer\n<</Size 2 /Root 1 0 R>>\n'
    b'startxref\n45\n%%EOF\n'
)


def make_docx_bytes(extra_entries=0, compressed_payload=None):
    output = io.BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr(
            '[Content_Types].xml',
            '<?xml version="1.0"?><Types '
            'xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>',
        )
        archive.writestr(
            'word/document.xml',
            '<?xml version="1.0"?><w:document '
            'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
        )
        for index in range(extra_entries):
            archive.writestr('custom/item-%04d.bin' % index, b'')
        if compressed_payload is not None:
            archive.writestr('custom/compressed.bin', compressed_payload)
    return output.getvalue()


def forge_eocd_entry_count(raw, count):
    forged = bytearray(raw)
    eocd_offset = forged.rfind(b'PK\x05\x06')
    if eocd_offset < 0:
        raise ValueError('EOCD not found in test fixture')
    struct.pack_into('<HH', forged, eocd_offset + 8, count, count)
    return bytes(forged)


def make_doc_bytes(word_stream=None):
    free_sector = 0xFFFFFFFF
    end_of_chain = 0xFFFFFFFE
    fat_sector = 0xFFFFFFFD
    header = bytearray(512)
    header[:8] = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    struct.pack_into('<HHHH', header, 24, 0x003E, 3, 0xFFFE, 9)
    struct.pack_into('<H', header, 32, 6)
    struct.pack_into('<I', header, 44, 1)
    struct.pack_into('<I', header, 48, 0)
    struct.pack_into('<I', header, 56, 4096)
    struct.pack_into('<I', header, 60, end_of_chain)
    struct.pack_into('<I', header, 68, end_of_chain)
    for index in range(109):
        struct.pack_into('<I', header, 76 + (index * 4), free_sector)
    struct.pack_into('<I', header, 76, 1)

    directory = bytearray(512)

    def directory_entry(offset, name, object_type, start_sector, size, child=free_sector):
        encoded_name = (name + '\x00').encode('utf-16le')
        directory[offset:offset + len(encoded_name)] = encoded_name
        struct.pack_into('<HBB', directory, offset + 64, len(encoded_name), object_type, 1)
        struct.pack_into('<III', directory, offset + 68, free_sector, free_sector, child)
        struct.pack_into('<I', directory, offset + 116, start_sector)
        struct.pack_into('<Q', directory, offset + 120, size)

    directory_entry(0, 'Root Entry', 5, end_of_chain, 0, child=1)
    directory_entry(128, 'WordDocument', 2, 2, 4096)

    fat = [free_sector] * 128
    fat[0] = end_of_chain
    fat[1] = fat_sector
    for sector in range(2, 9):
        fat[sector] = sector + 1
    fat[9] = end_of_chain
    if word_stream is None:
        word_stream = bytearray(4096)
        struct.pack_into('<HH', word_stream, 0, 0xA5EC, 0x00C1)
        struct.pack_into('<H', word_stream, 12, 0x00BF)
        struct.pack_into('<H', word_stream, 32, 0x000E)
        struct.pack_into('<H', word_stream, 62, 0x0016)
        struct.pack_into('<H', word_stream, 152, 0x005D)
        word_stream = bytes(word_stream)
    if len(word_stream) != 4096:
        raise ValueError('The DOC test stream must occupy eight regular sectors.')
    return bytes(header + directory + struct.pack('<128I', *fat) + word_stream)


class TfmFixtureMixin:
    def _suffix(self):
        return uuid4().hex[:8]

    def _portal_case(self, progress=50, login=None):
        suffix = self._suffix()
        login = login or 'tfm.%s@example.test' % suffix
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'TFM portal %s' % suffix,
            'login': login,
            'email': login,
            'password': login,
            'groups_id': [Command.set([self.env.ref('base.group_portal').id])],
        })
        student = self.env['op.student'].create({
            'partner_id': user.partner_id.id,
            'user_id': user.id,
            'first_name': 'TFM',
            'last_name': suffix,
            'gender': 'o',
        })
        course = self.env['op.course'].create({
            'name': 'TFM course %s' % suffix,
            'code': 'TFM-%s' % suffix,
            'lang': 'en_US',
            'activate_tesis': True,
            'irg_tfm_channel_id': self.env['slide.channel'].create({
                'name': 'TFM delivery channel %s' % suffix,
            }).id,
        })
        batch = self.env['op.batch'].create({
            'name': 'TFM batch %s' % suffix,
            'code': 'HC2511',
            'course_id': course.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=60),
        })
        enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
            'roll_number': 'TFM-%s' % suffix,
        })
        with patch.object(
            type(enrollment),
            '_irg_tfm_completion_percentage',
            return_value=progress,
        ):
            thesis = enrollment._irg_ensure_tfm_record()
        return user, student, course, enrollment, thesis

    def _convocation(self, **overrides):
        today = date.today()
        values = {
            'name': 'Current convocation',
            'code': 'CONV-%s' % self._suffix(),
            'partial_open_date': today,
            'partial_close_date': today,
            'final_open_date': today,
            'final_close_date': today,
        }
        values.update(overrides)
        return self.env['irg.tfm.convocatoria'].create(values)


@tagged('post_install', '-at_install')
class TestTfmDeliveries(TfmFixtureMixin, TransactionCase):
    def test_backend_history_lists_delivery_details_and_hides_legacy_tfm_fields(self):
        view = self.env.ref('irg_tfm_convocatorias.view_tesis_model_form_irg_tfm')
        arch = etree.fromstring(view.get_combined_arch())
        tree = arch.xpath("//field[@name='irg_tfm_submission_ids']/tree")
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0].get('default_order'), 'submitted_at desc, id desc')
        columns = tree[0].xpath('./field/@name')
        self.assertEqual(columns, [
            'stage', 'version', 'attachment_id', 'comment', 'convocation_id',
            'submitted_by', 'submitted_at', 'internal_exception',
        ])
        legacy_phase = arch.xpath("//sheet/group/group/field[@name='status_thesis']")
        legacy_documents = arch.xpath("//page[.//field[@name='attachment2_ids']]")
        self.assertTrue(legacy_phase)
        self.assertTrue(legacy_documents)
        self.assertEqual(len(legacy_phase), 1)
        self.assertIn('irg_tfm_activated_at', legacy_phase[0].get('attrs') or '')
        self.assertTrue(
            all('irg_tfm_activated_at' in (node.get('attrs') or '') for node in legacy_documents),
        )

    def test_upload_validation_rejects_empty_oversize_extension_signature_mime_and_generic_zip(self):
        Delivery = self.env['irg.tfm.entrega']
        invalid = (
            (b'', 'empty.pdf', 'application/pdf'),
            (b'x' * (20 * 1024 * 1024 + 1), 'large.pdf', 'application/pdf'),
            (PDF_BYTES, 'notes.txt', 'application/pdf'),
            (b'not a pdf', 'fake.PDF', 'application/pdf'),
            (PDF_BYTES, 'paper.pdf', 'application/msword'),
            (b'https://example.test/file.pdf', 'link.pdf', 'application/pdf'),
            (b'%PDF-1.9\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n', 'bad-version.pdf', 'application/pdf'),
            (b'%PDF-1.4\n%%EOF\n', 'minimal.pdf', 'application/pdf'),
            (b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n', 'no-eof.pdf', 'application/pdf'),
            (
                b'PK\x03\x04generic', 'fake.docx',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            ),
            (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'not-word', 'fake.doc', 'application/msword'),
            (make_doc_bytes(b'W' * 4096), 'named-only.doc', 'application/msword'),
        )
        for raw, filename, mimetype in invalid:
            with self.subTest(filename=filename), self.assertRaises(ValidationError):
                Delivery._irg_validate_upload(raw, filename, mimetype)

    def test_docx_requires_word_content_type_and_well_formed_xml(self):
        Delivery = self.env['irg.tfm.entrega']

        def package(content_types, document):
            output = io.BytesIO()
            with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
                archive.writestr('[Content_Types].xml', content_types)
                archive.writestr('word/document.xml', document)
            return output.getvalue()

        invalid = (
            package(
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
            ),
            package(
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Override PartName="/word/document.xml" ContentType="text/plain"/>'
                '</Types>',
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
            ),
            package(
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                '</Types>',
                '<w:document',
            ),
        )
        for raw in invalid:
            with self.subTest(size=len(raw)), self.assertRaises(ValidationError):
                Delivery._irg_validate_upload(
                    raw,
                    'invalid.docx',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                )

    def test_docx_rejects_entry_flood_and_high_compression_ratio(self):
        Delivery = self.env['irg.tfm.entrega']
        invalid = (
            make_docx_bytes(extra_entries=255),
            make_docx_bytes(compressed_payload=b'0' * (1024 * 1024)),
        )
        for raw in invalid:
            self.assertLess(len(raw), 20 * 1024 * 1024)
            with self.subTest(size=len(raw)), self.assertRaises(ValidationError):
                Delivery._irg_validate_upload(
                    raw,
                    'bomb.docx',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                )

    def test_docx_preflight_rejects_forged_eocd_entry_count(self):
        raw = make_docx_bytes(extra_entries=255)
        forged = forge_eocd_entry_count(raw, 2)
        self.assertLess(len(forged), 20 * 1024 * 1024)

        self.assertIsNone(
            self.env['irg.tfm.entrega']._irg_docx_archive_preflight(forged),
            'preflight must count actual central records before constructing ZipFile',
        )

    def test_upload_validation_accepts_case_insensitive_pdf_and_real_docx_structure(self):
        Delivery = self.env['irg.tfm.entrega']
        safe_pdf = Delivery._irg_validate_upload(PDF_BYTES, '../Report.PDF', 'application/pdf')
        safe_docx = Delivery._irg_validate_upload(
            make_docx_bytes(),
            'Final.DOCX',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
        self.assertEqual(safe_pdf, ('Report.PDF', 'application/pdf'))
        self.assertEqual(
            safe_docx,
            ('Final.DOCX', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        )

    def test_upload_validation_accepts_ole_with_real_word_document_stream(self):
        safe_doc = self.env['irg.tfm.entrega']._irg_validate_upload(
            make_doc_bytes(), 'Legacy.DOC', 'application/msword',
        )
        self.assertEqual(safe_doc, ('Legacy.DOC', 'application/msword'))

    def test_outline_closes_on_assignment_and_reopens_on_removal(self):
        user, _student, course, _enrollment, thesis = self._portal_case()
        Delivery = self.env['irg.tfm.entrega'].with_user(user)

        first = Delivery._irg_create_portal_submission(
            course.id, 'outline', PDF_BYTES, 'outline.pdf', 'application/pdf', 'first',
        )
        self.assertEqual(first.stage, 'outline')
        self.assertFalse(first.convocation_id)

        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        with self.assertRaises(ValidationError):
            Delivery._irg_create_portal_submission(
                course.id, 'outline', PDF_BYTES, 'closed.pdf', 'application/pdf', '',
            )

        thesis.write({'irg_tfm_convocation_id': False})
        reopened = Delivery._irg_create_portal_submission(
            course.id, 'outline', PDF_BYTES, 'reopened.pdf', 'application/pdf', '',
        )
        self.assertEqual(reopened.version, 2)

    def test_partial_and_final_windows_are_inclusive_and_server_selects_current_snapshot(self):
        user, _student, course, _enrollment, thesis = self._portal_case()
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        Delivery = self.env['irg.tfm.entrega'].with_user(user)

        partial = Delivery._irg_create_portal_submission(
            course.id, 'partial', PDF_BYTES, 'partial.pdf', 'application/pdf', '',
        )
        final = Delivery._irg_create_portal_submission(
            course.id, 'final', PDF_BYTES, 'final.pdf', 'application/pdf', '',
        )
        self.assertEqual(partial.convocation_id, convocation)
        self.assertEqual(final.convocation_id, convocation)

        convocation.write({
            'partial_open_date': date.today() - timedelta(days=2),
            'partial_close_date': date.today() - timedelta(days=1),
        })
        with self.assertRaises(ValidationError):
            Delivery._irg_create_portal_submission(
                course.id, 'partial', PDF_BYTES, 'late.pdf', 'application/pdf', '',
            )

    def test_versions_are_per_stage_and_snapshot_and_attachments_are_private(self):
        user, _student, course, _enrollment, thesis = self._portal_case()
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        Delivery = self.env['irg.tfm.entrega'].with_user(user)
        first = Delivery._irg_create_portal_submission(
            course.id, 'partial', PDF_BYTES, 'one.pdf', 'application/pdf', '',
        )
        second = Delivery._irg_create_portal_submission(
            course.id, 'partial', PDF_BYTES, 'two.pdf', 'application/pdf', '',
        )
        self.assertEqual((first.version, second.version), (1, 2))
        self.assertEqual(first.attachment_id.res_model, 'irg.tfm.entrega')
        self.assertEqual(first.attachment_id.res_id, first.id)
        self.assertFalse(first.attachment_id.public)
        self.assertEqual(first.attachment_id.type, 'binary')

        replacement = self._convocation(name='Replacement')
        thesis.write({'irg_tfm_convocation_id': replacement.id})
        new_snapshot = Delivery._irg_create_portal_submission(
            course.id, 'partial', PDF_BYTES, 'replacement.pdf', 'application/pdf', '',
        )
        self.assertEqual(new_snapshot.version, 1)
        self.assertEqual(new_snapshot.convocation_id, replacement)
        self.assertTrue(first.exists())
        self.assertTrue(first.attachment_id.exists())

    def test_delivery_and_linked_attachment_are_immutable(self):
        user, _student, course, _enrollment, _thesis = self._portal_case()
        delivery = self.env['irg.tfm.entrega'].with_user(user)._irg_create_portal_submission(
            course.id, 'outline', PDF_BYTES, 'outline.pdf', 'application/pdf', '',
        )
        with self.assertRaises(AccessError):
            delivery.sudo().write({'comment': 'changed'})
        with self.assertRaises(AccessError):
            delivery.sudo().unlink()
        with self.assertRaises(AccessError):
            delivery.attachment_id.sudo().write({'datas': base64.b64encode(b'changed')})
        with self.assertRaises((AccessError, ValidationError)):
            delivery.attachment_id.sudo().unlink()

    def test_internal_exception_requires_group_and_reason_and_creates_new_version_with_chatter(self):
        portal_user, _student, course, _enrollment, thesis = self._portal_case()
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        previous = self.env['irg.tfm.entrega'].with_user(portal_user)._irg_create_portal_submission(
            course.id, 'partial', PDF_BYTES, 'on-time.pdf', 'application/pdf', '',
        )
        convocation.write({
            'partial_open_date': date.today() - timedelta(days=2),
            'partial_close_date': date.today() - timedelta(days=1),
        })

        with self.assertRaises(ValidationError):
            thesis._irg_create_delivery_exception('partial', PDF_BYTES, 'late.pdf', 'application/pdf', '')
        with self.assertRaises(AccessError):
            thesis.with_user(portal_user)._irg_create_delivery_exception(
                'partial', PDF_BYTES, 'late.pdf', 'application/pdf', 'approved late upload',
            )

        before = len(thesis.message_ids)
        delivery = thesis._irg_create_delivery_exception(
            'partial', PDF_BYTES, 'late.pdf', 'application/pdf', 'approved late upload',
        )
        self.assertTrue(delivery.internal_exception)
        self.assertEqual(delivery.exception_reason, 'approved late upload')
        self.assertNotEqual(delivery.id, previous.id)
        self.assertEqual(delivery.version, previous.version + 1)
        self.assertGreater(len(thesis.message_ids), before)

    def test_archived_convocation_rejects_regular_and_internal_late_deliveries(self):
        portal_user, _student, course, _enrollment, thesis = self._portal_case()
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        convocation.write({'active': False})

        with self.assertRaisesRegex(ValidationError, 'archived'):
            self.env['irg.tfm.entrega'].with_user(portal_user)._irg_create_portal_submission(
                course.id, 'partial', PDF_BYTES, 'blocked.pdf', 'application/pdf', '',
            )
        with self.assertRaisesRegex(ValidationError, 'archived'):
            thesis._irg_create_delivery_exception(
                'partial', PDF_BYTES, 'exception.pdf', 'application/pdf', 'manual exception',
            )

    def test_internal_exception_cannot_reopen_outline_after_assignment(self):
        _portal_user, _student, _course, _enrollment, thesis = self._portal_case()
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})

        with self.assertRaisesRegex(ValidationError, 'Outline submissions close'):
            thesis._irg_create_delivery_exception(
                'outline', PDF_BYTES, 'outline.pdf', 'application/pdf', 'manual exception',
            )

    def test_property_resolution_fails_closed_for_outsider_and_ambiguous_user(self):
        owner, _student, course, _enrollment, thesis = self._portal_case()
        outsider, _other_student, _other_course, _other_enrollment, _other_thesis = self._portal_case()
        self.assertEqual(
            self.env['tesis.model'].with_user(owner)._irg_portal_owned_thesis(course.id).id,
            thesis.id,
        )
        with self.assertRaises(AccessError):
            self.env['tesis.model'].with_user(outsider)._irg_portal_owned_thesis(course.id)

        self.env['op.student'].create({
            'partner_id': self.env['res.partner'].create({'name': 'Ambiguous'}).id,
            'user_id': owner.id,
            'first_name': 'Ambiguous',
            'last_name': 'Student',
            'gender': 'o',
        })
        with self.assertRaises(AccessError):
            self.env['tesis.model'].with_user(owner)._irg_portal_owned_thesis(course.id)

    def test_owned_diplomado_cannot_bypass_hidden_page_through_submission_service(self):
        owner, _student, course, _enrollment, _thesis = self._portal_case()
        course.write({'code': 'DI-TFM-DIRECT'})
        with self.assertRaises(AccessError):
            self.env['irg.tfm.entrega'].with_user(owner)._irg_create_portal_submission(
                course.id, 'outline', PDF_BYTES, 'blocked.pdf', 'application/pdf', '',
            )

    def _create_committed_submission_case(self, registry):
        original_env = self.env
        with registry.cursor() as cursor:
            env = api.Environment(cursor, self.env.uid, {})
            self.env = env
            user, student, course, enrollment, thesis = self._portal_case()
            values = {
                'user': user.id,
                'student': student.id,
                'partner': user.partner_id.id,
                'course': course.id,
                'channel': course.irg_tfm_channel_id.id,
                'batch': enrollment.batch_id.id,
                'enrollment': enrollment.id,
                'thesis': thesis.id,
            }
            cursor.commit()
        self.env = original_env
        return values

    def _create_committed_partial_case(self, registry):
        identifiers = self._create_committed_submission_case(registry)
        with registry.cursor() as cursor:
            env = api.Environment(cursor, self.env.uid, {})
            today = date.today()
            convocation = env['irg.tfm.convocatoria'].create({
                'name': 'Concurrent archive %s' % self._suffix(),
                'code': 'CONCURRENT-ARCHIVE-%s' % self._suffix(),
                'partial_open_date': today,
                'partial_close_date': today,
                'final_open_date': today,
                'final_close_date': today,
            })
            env['tesis.model'].browse(identifiers['thesis']).write({
                'irg_tfm_convocation_id': convocation.id,
            })
            identifiers['convocation'] = convocation.id
            cursor.commit()
        return identifiers

    def _cleanup_committed_submission_case(self, registry, identifiers):
        with registry.cursor() as cursor:
            env = api.Environment(cursor, self.env.uid, {})
            env['slide.channel.partner'].with_context(active_test=False).search([
                ('irg_tfm_thesis_ids', 'in', identifiers['thesis']),
            ]).unlink()
            cursor.execute(
                'SELECT attachment_id FROM irg_tfm_entrega WHERE thesis_id = %s',
                [identifiers['thesis']],
            )
            attachment_ids = [row[0] for row in cursor.fetchall() if row[0]]
            cursor.execute(
                'DELETE FROM irg_tfm_entrega WHERE thesis_id = %s',
                [identifiers['thesis']],
            )
            env['ir.attachment'].browse(attachment_ids).unlink()
            env['tesis.model'].browse(identifiers['thesis']).exists().unlink()
            if identifiers.get('convocation'):
                env['irg.tfm.convocatoria'].browse(identifiers['convocation']).exists().unlink()
            env['op.student.course'].browse(identifiers['enrollment']).exists().unlink()
            env['op.student'].browse(identifiers['student']).exists().unlink()
            env['op.batch'].browse(identifiers['batch']).exists().unlink()
            env['op.course'].browse(identifiers['course']).exists().unlink()
            env['slide.channel'].browse(identifiers['channel']).exists().unlink()
            env['res.users'].browse(identifiers['user']).exists().unlink()
            env['res.partner'].browse(identifiers['partner']).exists().unlink()
            cursor.commit()

    def test_concurrent_submissions_receive_distinct_atomic_versions(self):
        registry = Registry(self.env.cr.dbname)
        identifiers = self._create_committed_submission_case(registry)
        barrier = Barrier(2)
        errors = []

        def submit(index):
            try:
                with registry.cursor() as cursor:
                    env = api.Environment(cursor, identifiers['user'], {})
                    barrier.wait(timeout=10)
                    env['irg.tfm.entrega']._irg_create_portal_submission(
                        identifiers['course'], 'outline', PDF_BYTES,
                        'outline-%s.pdf' % index, 'application/pdf', '',
                    )
                    cursor.commit()
            except Exception as exc:
                errors.append(exc)

        workers = [Thread(target=submit, args=(index,)) for index in range(2)]
        try:
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=15)
            self.assertFalse(any(worker.is_alive() for worker in workers))
            self.assertFalse(errors)
            with registry.cursor() as cursor:
                env = api.Environment(cursor, self.env.uid, {})
                deliveries = env['irg.tfm.entrega'].search([
                    ('thesis_id', '=', identifiers['thesis']),
                    ('stage', '=', 'outline'),
                ], order='version')
                self.assertEqual(deliveries.mapped('version'), [1, 2])
        finally:
            self._cleanup_committed_submission_case(registry, identifiers)
            self.env.invalidate_all()

    def test_concurrent_archive_serializes_before_partial_submission(self):
        registry = Registry(self.env.cr.dbname)
        identifiers = self._create_committed_partial_case(registry)
        archive_updated = Event()
        release_archive = Event()
        submit_started = Event()
        submit_finished = Event()
        archive_errors = []
        submit_errors = []

        def archive_convocation():
            try:
                with registry.cursor() as cursor:
                    env = api.Environment(cursor, self.env.uid, {})
                    env['irg.tfm.convocatoria'].browse(identifiers['convocation']).write({
                        'active': False,
                    })
                    archive_updated.set()
                    if not release_archive.wait(timeout=10):
                        raise AssertionError('archive release timeout')
                    cursor.commit()
            except Exception as exc:
                archive_errors.append(exc)
                archive_updated.set()

        def submit_partial():
            try:
                if not archive_updated.wait(timeout=10):
                    raise AssertionError('archive update timeout')
                with registry.cursor() as cursor:
                    env = api.Environment(cursor, identifiers['user'], {})
                    submit_started.set()
                    env['irg.tfm.entrega']._irg_create_portal_submission(
                        identifiers['course'], 'partial', PDF_BYTES,
                        'concurrent.pdf', 'application/pdf', '',
                    )
                    cursor.commit()
            except Exception as exc:
                submit_errors.append(exc)
            finally:
                submit_finished.set()

        archive_worker = Thread(target=archive_convocation)
        submit_worker = Thread(target=submit_partial)
        try:
            archive_worker.start()
            submit_worker.start()
            self.assertTrue(archive_updated.wait(timeout=10))
            self.assertTrue(submit_started.wait(timeout=10))
            waited_for_locked_configuration = not submit_finished.wait(timeout=1)
            release_archive.set()
            archive_worker.join(timeout=15)
            submit_worker.join(timeout=15)
            self.assertFalse(archive_worker.is_alive())
            self.assertFalse(submit_worker.is_alive())
            self.assertTrue(waited_for_locked_configuration)
            self.assertFalse(archive_errors)
            self.assertEqual(len(submit_errors), 1)
            self.assertIsInstance(submit_errors[0], ValidationError)
            with registry.cursor() as cursor:
                env = api.Environment(cursor, self.env.uid, {})
                self.assertFalse(env['irg.tfm.entrega'].search([
                    ('thesis_id', '=', identifiers['thesis']),
                    ('stage', '=', 'partial'),
                ]))
        finally:
            release_archive.set()
            archive_worker.join(timeout=15)
            submit_worker.join(timeout=15)
            self._cleanup_committed_submission_case(registry, identifiers)
            self.env.invalidate_all()


@tagged('post_install', '-at_install')
class TestTfmPortal(TfmFixtureMixin, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        helper = TfmFixtureMixin()
        helper.env = cls.env
        cls.low_user, _student, cls.low_course, _enrollment, _thesis = helper._portal_case(
            progress=49.99, login='tfm_low_portal',
        )
        cls.owner, _student, cls.course, _enrollment, cls.thesis = helper._portal_case(
            progress=50, login='tfm_owner_portal',
        )
        cls.outsider, _student, _course, _enrollment, _thesis = helper._portal_case(
            progress=50, login='tfm_outsider_portal',
        )
        cls.diploma_owner, _student, cls.diploma_course, _enrollment, cls.diploma_thesis = helper._portal_case(
            progress=50, login='tfm_diploma_portal',
        )
        cls.diploma_course.write({'code': 'DI-TFM-PORTAL'})
        cls.delivery = cls.thesis._irg_create_delivery_exception(
            'outline', PDF_BYTES, 'private.pdf', 'application/pdf', 'fixture',
        )

    def test_course_tile_appears_only_after_activation_with_exact_text(self):
        self.authenticate(self.low_user.login, self.low_user.login)
        low = self.url_open('/campus/course/%s' % self.low_course.id)
        self.assertNotIn('Trabajo Final de Máster', low.text)

        self.authenticate(self.owner.login, self.owner.login)
        active = self.url_open('/campus/course/%s' % self.course.id)
        self.assertIn('Trabajo Final de Máster', active.text)

    def test_tfm_page_is_owned_and_contains_csrf_protected_form(self):
        convocation = self._convocation()
        self.thesis.write({'irg_tfm_convocation_id': convocation.id})
        self.authenticate(self.owner.login, self.owner.login)
        page = self.url_open('/campus/course/%s/tfm' % self.course.id)
        self.assertEqual(page.status_code, 200)
        self.assertIn('Trabajo Final de Máster', page.text)
        self.assertIn('Guía y recursos para el TFM', page.text)
        self.assertIn(date.today().strftime('%d/%m/%Y'), page.text)
        self.assertNotIn('Acceder al contenido eLearning', page.text)
        self.assertRegex(page.text, r'name="csrf_token"\s+value="[^"]+"')

        self.authenticate(self.outsider.login, self.outsider.login)
        denied = self.url_open('/campus/course/%s/tfm' % self.course.id, allow_redirects=False)
        self.assertEqual(denied.status_code, 404)

    def test_archived_convocation_keeps_history_but_hides_delivery_forms(self):
        convocation = self._convocation()
        self.thesis.write({'irg_tfm_convocation_id': convocation.id})
        convocation.write({'active': False})
        self.authenticate(self.owner.login, self.owner.login)

        page = self.url_open('/campus/course/%s/tfm' % self.course.id)

        self.assertEqual(page.status_code, 200)
        self.assertIn('Entrega parcial', page.text)
        self.assertNotRegex(page.text, r'name="stage"\s+value="(?:partial|final)"')

    def test_owned_diplomado_keeps_late_controller_and_tile_restrictions(self):
        self.authenticate(self.diploma_owner.login, self.diploma_owner.login)
        page = self.url_open(
            '/campus/course/%s/tfm' % self.diploma_course.id,
            allow_redirects=False,
        )
        dashboard = self.url_open('/campus/course/%s' % self.diploma_course.id)
        self.assertNotIn('name="stage"', page.text)
        self.assertNotIn('Trabajo Final de Máster', page.text)
        self.assertNotIn('Trabajo Final de Máster', dashboard.text)

    def test_submit_without_csrf_is_rejected_without_creating_delivery(self):
        self.authenticate(self.owner.login, self.owner.login)
        before = self.env['irg.tfm.entrega'].sudo().search_count([
            ('thesis_id', '=', self.thesis.id),
        ])
        response = self.url_open(
            '/campus/course/%s/tfm/submit' % self.course.id,
            data={'stage': 'outline'},
            allow_redirects=False,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self.env['irg.tfm.entrega'].sudo().search_count([('thesis_id', '=', self.thesis.id)]),
            before,
        )

    def test_diplomado_submit_with_csrf_and_file_is_denied_without_tfm_content_or_delivery(self):
        self.authenticate(self.diploma_owner.login, self.diploma_owner.login)
        delivery_domain = [('thesis_id', '=', self.diploma_thesis.id)]
        attachment_domain = [
            ('res_model', '=', 'irg.tfm.entrega'),
            ('name', '=', 'diploma.pdf'),
        ]
        before_deliveries = self.env['irg.tfm.entrega'].sudo().search_count(delivery_domain)
        before_attachments = self.env['ir.attachment'].sudo().search_count(attachment_domain)

        response = self.url_open(
            '/campus/course/%s/tfm/submit' % self.diploma_course.id,
            data={
                'csrf_token': http.Request.csrf_token(self),
                'stage': 'outline',
                'comment': 'must stay denied',
            },
            files={'file': ('diploma.pdf', PDF_BYTES, 'application/pdf')},
            allow_redirects=False,
        )

        self.assertIn(response.status_code, (403, 404))
        self.assertNotIn('Trabajo Final de Máster', response.text)
        self.assertNotIn('name="stage"', response.text)
        self.assertEqual(
            self.env['irg.tfm.entrega'].sudo().search_count(delivery_domain),
            before_deliveries,
        )
        self.assertEqual(
            self.env['ir.attachment'].sudo().search_count(attachment_domain),
            before_attachments,
        )

    def test_foreign_delivery_download_and_web_content_are_denied(self):
        self.authenticate(self.outsider.login, self.outsider.login)
        secure = self.url_open(
            '/campus/tfm/delivery/%s/download' % self.delivery.id,
            allow_redirects=False,
        )
        direct = self.url_open('/web/content/%s' % self.delivery.attachment_id.id, allow_redirects=False)
        self.assertIn(secure.status_code, (403, 404))
        self.assertIn(direct.status_code, (403, 404))

    def test_legacy_routes_are_neutralized_and_do_not_mutate(self):
        self.authenticate(self.owner.login, self.owner.login)
        state = self.thesis.state
        delivery_id = self.delivery.id
        attachment_id = self.delivery.attachment_id.id

        def assert_history_exists():
            self.assertTrue(self.env['irg.tfm.entrega'].sudo().browse(delivery_id).exists())
            self.assertTrue(self.env['ir.attachment'].sudo().browse(attachment_id).exists())

        get_urls = (
            '/my/tesis_models/new',
            '/my/tesis_models2',
            '/my/tesis_model/%s' % self.thesis.id,
            '/my/notificacionestr/download/%s' % self.delivery.attachment_id.id,
            '/my/notificacionestr/borrar/%s/%s' % (self.delivery.attachment_id.id, self.thesis.id),
            '/my/notificacionestr/comment/%s' % self.delivery.attachment_id.id,
        )
        for url in get_urls:
            with self.subTest(url=url):
                response = self.url_open(url, allow_redirects=False)
                self.assertIn(response.status_code, (302, 303, 404))
                assert_history_exists()

        post_urls = (
            '/my/tesis_models/new',
            '/my/tesis_models2/accept',
            '/my/tesis_models2/decline',
            '/web/submit_documenttr',
        )
        for url in post_urls:
            with self.subTest(url=url):
                response = self.url_open(
                    url,
                    data={'request_id': str(self.thesis.id), 'tesis_model_id': str(self.thesis.id)},
                    allow_redirects=False,
                )
                self.assertIn(response.status_code, (400, 404))
                assert_history_exists()
        self.assertEqual(self.thesis.state, state)

    def test_legacy_portal_tile_and_counter_are_absent(self):
        self.authenticate(self.owner.login, self.owner.login)
        page = self.url_open('/my')
        self.assertNotIn('/my/tesis_models2', page.text)
        self.assertNotIn('tesis_models_count', page.text)
