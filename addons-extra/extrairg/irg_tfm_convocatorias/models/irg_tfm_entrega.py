import base64
import io
import re
import struct
from datetime import datetime
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from psycopg2 import IntegrityError
from pytz import timezone
from werkzeug.utils import secure_filename

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


_MAX_UPLOAD_BYTES = 20 * 1024 * 1024
_VERSION_CONSTRAINT = 'irg_tfm_entrega_version_unique'
_MADRID_TZ = timezone('Europe/Madrid')
_MIMETYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}
_OLE_FREE_SECTOR = 0xFFFFFFFF
_OLE_END_OF_CHAIN = 0xFFFFFFFE
_OLE_RESERVED_SECTORS = {0xFFFFFFFC, 0xFFFFFFFD, _OLE_END_OF_CHAIN, _OLE_FREE_SECTOR}
_WORD_FIB_MIN_FC_LCB = {
    0x00C1: 0x005D,
    0x00D9: 0x006C,
    0x0101: 0x0088,
    0x010C: 0x00A4,
    0x0112: 0x00B7,
}
_DOCX_CONTENT_TYPES_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
_DOCX_WORD_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_DOCX_MAIN_CONTENT_TYPE = (
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'
)
_MAX_DOCX_ENTRIES = 256
_MAX_DOCX_CENTRAL_DIRECTORY_BYTES = 2 * 1024 * 1024
_MAX_DOCX_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
_MAX_DOCX_COMPRESSION_RATIO = 100
_MAX_DOCX_XML_BYTES = 5 * 1024 * 1024
_PDF_HEADER_RE = re.compile(br'%PDF-(?:1\.[0-7]|2\.0)')
_PDF_OBJECT_RE = re.compile(br'(?:^|[\r\n])[1-9][0-9]* [0-9]+ obj(?:[\r\n ])')


class IrgTfmEntrega(models.Model):
    _name = 'irg.tfm.entrega'
    _description = 'Entrega TFM'
    _order = 'submitted_at desc, id desc'

    thesis_id = fields.Many2one(
        'tesis.model', required=True, readonly=True, index=True, ondelete='restrict',
    )
    stage = fields.Selection(
        [('outline', 'Esquema'), ('partial', 'Entrega parcial'), ('final', 'Entrega final')],
        required=True,
        readonly=True,
        index=True,
    )
    convocation_id = fields.Many2one(
        'irg.tfm.convocatoria', readonly=True, index=True, ondelete='restrict',
    )
    # PostgreSQL UNIQUE treats NULLs as distinct. This stable key is zero for
    # outline submissions without a snapshot and the convocation id otherwise.
    convocation_key = fields.Integer(required=True, readonly=True, default=0)
    version = fields.Integer(required=True, readonly=True)
    attachment_id = fields.Many2one(
        'ir.attachment', readonly=True, copy=False, ondelete='restrict',
    )
    comment = fields.Text(readonly=True)
    submitted_by = fields.Many2one(
        'res.users', required=True, readonly=True, ondelete='restrict',
    )
    submitted_at = fields.Datetime(required=True, readonly=True)
    internal_exception = fields.Boolean(readonly=True)
    exception_reason = fields.Text(readonly=True)

    _sql_constraints = [
        (
            _VERSION_CONSTRAINT,
            'unique(thesis_id, stage, convocation_key, version)',
            'La versión de la entrega ya existe para esta etapa y convocatoria.',
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('_irg_tfm_private_create'):
            raise AccessError(_('TFM deliveries can only be created through the submission service.'))
        for vals in vals_list:
            convocation_id = vals.get('convocation_id') or 0
            if vals.get('convocation_key', 0) != convocation_id:
                raise ValidationError(_('The delivery snapshot key is inconsistent.'))
            if vals.get('stage') in ('partial', 'final') and not convocation_id:
                raise ValidationError(_('A convocation snapshot is required for this delivery stage.'))
            if int(vals.get('version') or 0) < 1:
                raise ValidationError(_('The delivery version must be positive.'))
            if vals.get('internal_exception') and not (vals.get('exception_reason') or '').strip():
                raise ValidationError(_('An exception reason is required.'))
            if vals.get('attachment_id'):
                raise ValidationError(_('The delivery attachment must be bound after row creation.'))
        return super().create(vals_list)

    def write(self, vals):
        if not (
            self.env.context.get('_irg_tfm_private_create')
            and set(vals) == {'attachment_id'}
            and all(not record.attachment_id for record in self)
        ):
            raise AccessError(_('TFM delivery history is immutable.'))
        for record in self:
            attachment = self.env['ir.attachment'].sudo().browse(vals['attachment_id']).exists()
            if (
                len(attachment) != 1
                or attachment.res_model != self._name
                or attachment.res_id != record.id
                or attachment.type != 'binary'
                or attachment.public
            ):
                raise ValidationError(_('The attachment is not privately bound to this delivery.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(_('TFM delivery history cannot be deleted.'))

    def _irg_is_tfm_outline_submission(self):
        self.ensure_one()
        return self.stage == 'outline'

    @api.model
    def _irg_portal_owned_delivery(self, delivery_id, raise_missing=True):
        student = self.env['tesis.model']._irg_portal_student(raise_missing=raise_missing)
        if not student:
            return self.browse()
        try:
            delivery_id = int(delivery_id)
        except (TypeError, ValueError):
            delivery_id = 0
        deliveries = self.sudo().search([
            ('id', '=', delivery_id),
            ('thesis_id.irg_tfm_activated_at', '!=', False),
            ('thesis_id.course_id.student_id', '=', student.id),
            ('thesis_id.course_id.student_id.user_id', '=', self.env.uid),
        ], limit=2)
        if len(deliveries) != 1:
            if raise_missing:
                raise AccessError(_('The requested TFM delivery is unavailable.'))
            return self.browse()
        course_id = deliveries.thesis_id.course_id.course_id.id
        thesis = self.env['tesis.model']._irg_portal_owned_thesis(
            course_id, raise_missing=raise_missing,
        )
        if thesis.id != deliveries.thesis_id.id:
            if raise_missing:
                raise AccessError(_('The requested TFM delivery is unavailable.'))
            return self.browse()
        if thesis.course_id.course_id.is_diplomado():
            if raise_missing:
                raise AccessError(_('The requested TFM delivery is unavailable.'))
            return self.browse()
        return deliveries

    @api.model
    def _irg_validate_upload(self, raw, filename, declared_mimetype):
        if not isinstance(raw, bytes) or not raw:
            raise ValidationError(_('The uploaded file is empty.'))
        if len(raw) > _MAX_UPLOAD_BYTES:
            raise ValidationError(_('The uploaded file exceeds the 20 MiB limit.'))

        safe_name = secure_filename(filename or '')
        if not safe_name or '.' not in safe_name:
            raise ValidationError(_('The uploaded filename is invalid.'))
        extension = safe_name.rsplit('.', 1)[1].lower()
        if extension not in _MIMETYPES:
            raise ValidationError(_('Only PDF, DOC and DOCX files are accepted.'))

        canonical_mimetype = _MIMETYPES[extension]
        normalized_mimetype = (declared_mimetype or '').split(';', 1)[0].strip().lower()
        if normalized_mimetype != canonical_mimetype:
            raise ValidationError(_('The declared MIME type does not match the filename.'))

        if extension == 'pdf':
            valid = self._irg_is_pdf(raw)
        elif extension == 'doc':
            valid = self._irg_is_word_ole(raw)
        else:
            valid = self._irg_is_docx(raw)
        if not valid:
            raise ValidationError(_('The file content does not match its declared format.'))
        return safe_name, canonical_mimetype

    @api.model
    def _irg_is_pdf(self, raw):
        header_end = len(raw)
        for separator in (b'\r', b'\n'):
            position = raw.find(separator, 0, 16)
            if position >= 0:
                header_end = min(header_end, position)
        if not _PDF_HEADER_RE.fullmatch(raw[:header_end]):
            return False
        stripped = raw.rstrip(b'\x00\t\n\f\r ')
        if not stripped.endswith(b'%%EOF'):
            return False
        eof_position = stripped.rfind(b'%%EOF')
        trailer_position = stripped.rfind(b'trailer', 0, eof_position)
        startxref_position = stripped.rfind(b'startxref', 0, eof_position)
        if trailer_position < 0 or startxref_position <= trailer_position:
            return False
        trailer_open = stripped.find(b'<<', trailer_position, startxref_position)
        trailer_close = stripped.find(b'>>', trailer_open + 2, startxref_position)
        if trailer_open < 0 or trailer_close < 0:
            return False
        trailer = stripped[trailer_open:trailer_close + 2]
        if b'/Size' not in trailer or b'/Root' not in trailer:
            return False
        offset = stripped[startxref_position + len(b'startxref'):eof_position].strip()
        if not offset.isdigit() or not _PDF_OBJECT_RE.search(stripped[:trailer_position]):
            return False
        return True

    @api.model
    def _irg_is_word_ole(self, raw):
        signature = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
        if len(raw) < 1536 or not raw.startswith(signature):
            return False
        try:
            byte_order, sector_shift = struct.unpack_from('<HH', raw, 28)
            if byte_order != 0xFFFE or sector_shift not in (9, 12):
                return False
            sector_size = 1 << sector_shift
            if len(raw) % sector_size or len(raw) < sector_size * 3:
                return False
            sector_count = (len(raw) // sector_size) - 1

            def read_sector(sector_id):
                if sector_id in _OLE_RESERVED_SECTORS or sector_id >= sector_count:
                    raise ValueError('invalid OLE sector')
                start = (sector_id + 1) * sector_size
                return raw[start:start + sector_size]

            fat_count = struct.unpack_from('<I', raw, 44)[0]
            first_directory_sector = struct.unpack_from('<I', raw, 48)[0]
            first_difat_sector = struct.unpack_from('<I', raw, 68)[0]
            difat_sector_count = struct.unpack_from('<I', raw, 72)[0]
            fat_sector_ids = list(struct.unpack_from('<109I', raw, 76))
            current_difat = first_difat_sector
            seen_difat = set()
            for _index in range(difat_sector_count):
                if current_difat in seen_difat:
                    return False
                seen_difat.add(current_difat)
                values = struct.unpack('<%sI' % (sector_size // 4), read_sector(current_difat))
                fat_sector_ids.extend(values[:-1])
                current_difat = values[-1]
            fat_sector_ids = [
                sector_id for sector_id in fat_sector_ids
                if sector_id != _OLE_FREE_SECTOR
            ]
            if fat_count < 1 or len(fat_sector_ids) < fat_count:
                return False
            fat = []
            for sector_id in fat_sector_ids[:fat_count]:
                fat.extend(struct.unpack('<%sI' % (sector_size // 4), read_sector(sector_id)))

            def read_chain(first_sector, expected_size=None):
                chunks = []
                current = first_sector
                seen = set()
                while current != _OLE_END_OF_CHAIN:
                    if current in seen or current >= len(fat) or len(seen) > sector_count:
                        raise ValueError('invalid OLE chain')
                    seen.add(current)
                    chunks.append(read_sector(current))
                    current = fat[current]
                content = b''.join(chunks)
                if expected_size is not None:
                    if expected_size > len(content):
                        raise ValueError('truncated OLE stream')
                    content = content[:expected_size]
                return content

            directory = read_chain(first_directory_sector)
            for offset in range(0, len(directory), 128):
                entry = directory[offset:offset + 128]
                if len(entry) != 128:
                    continue
                name_size = struct.unpack_from('<H', entry, 64)[0]
                object_type = entry[66]
                if object_type != 2 or name_size < 2 or name_size > 64 or name_size % 2:
                    continue
                encoded_name = entry[:name_size]
                if not encoded_name.endswith(b'\x00\x00'):
                    continue
                name = encoded_name[:-2].decode('utf-16le')
                if name != 'WordDocument':
                    continue
                start_sector = struct.unpack_from('<I', entry, 116)[0]
                stream_size = struct.unpack_from('<Q', entry, 120)[0]
                # A real binary Word stream is normally at least the regular
                # stream cutoff. Rejecting tiny mini-stream claims is safer
                # than accepting a forged directory entry.
                if stream_size < 4096 or stream_size > len(raw):
                    return False
                word_stream = read_chain(start_sector, stream_size)
                return self._irg_has_valid_word_fib(word_stream)
            return False
        except (IndexError, struct.error, UnicodeDecodeError, ValueError):
            return False

    @api.model
    def _irg_has_valid_word_fib(self, word_stream):
        if len(word_stream) < 154:
            return False
        try:
            identifier, fib_version = struct.unpack_from('<HH', word_stream, 0)
            if identifier != 0xA5EC or fib_version not in _WORD_FIB_MIN_FC_LCB:
                return False
            fib_back = struct.unpack_from('<H', word_stream, 12)[0]
            if not 0x0065 <= fib_back <= fib_version:
                return False

            short_count = struct.unpack_from('<H', word_stream, 32)[0]
            if short_count != 0x000E:
                return False
            long_count_offset = 34 + (short_count * 2)
            if long_count_offset + 2 > len(word_stream):
                return False
            long_count = struct.unpack_from('<H', word_stream, long_count_offset)[0]
            if long_count != 0x0016:
                return False
            fc_lcb_count_offset = long_count_offset + 2 + (long_count * 4)
            if fc_lcb_count_offset + 2 > len(word_stream):
                return False
            fc_lcb_count = struct.unpack_from('<H', word_stream, fc_lcb_count_offset)[0]
            if fc_lcb_count < _WORD_FIB_MIN_FC_LCB[fib_version]:
                return False
            return fc_lcb_count_offset + 2 + (fc_lcb_count * 8) <= len(word_stream)
        except struct.error:
            return False

    @api.model
    def _irg_is_docx(self, raw):
        expected_entries = self._irg_docx_archive_preflight(raw)
        if expected_entries is None:
            return False
        try:
            with ZipFile(io.BytesIO(raw)) as archive:
                required = {'[Content_Types].xml', 'word/document.xml'}
                infos = archive.infolist()
                if len(infos) != expected_entries or len(infos) > _MAX_DOCX_ENTRIES:
                    return False
                uncompressed_size = sum(info.file_size for info in infos)
                compressed_size = sum(info.compress_size for info in infos)
                if (
                    uncompressed_size > _MAX_DOCX_UNCOMPRESSED_BYTES
                    or uncompressed_size > max(compressed_size, 1) * _MAX_DOCX_COMPRESSION_RATIO
                ):
                    return False
                names = [info.filename for info in infos]
                if not required.issubset(names) or any(names.count(name) != 1 for name in required):
                    return False
                parsed = {}
                for name in required:
                    info = archive.getinfo(name)
                    if (
                        info.is_dir()
                        or info.flag_bits & 0x1
                        or info.file_size <= 0
                        or info.file_size > _MAX_DOCX_XML_BYTES
                    ):
                        return False
                    xml_content = self._irg_read_bounded_zip_member(archive, info)
                    if xml_content is None:
                        return False
                    parsed[name] = self._irg_parse_safe_xml(xml_content)
                    if parsed[name] is None:
                        return False
                content_types = parsed['[Content_Types].xml']
                if content_types.tag != '{%s}Types' % _DOCX_CONTENT_TYPES_NS:
                    return False
                overrides = content_types.findall('{%s}Override' % _DOCX_CONTENT_TYPES_NS)
                if not any(
                    node.get('PartName') == '/word/document.xml'
                    and node.get('ContentType') == _DOCX_MAIN_CONTENT_TYPE
                    for node in overrides
                ):
                    return False
                document = parsed['word/document.xml']
                return document.tag == '{%s}document' % _DOCX_WORD_NS
        except (BadZipFile, ElementTree.ParseError, KeyError, OSError, RuntimeError, ValueError):
            return False

    @api.model
    def _irg_docx_archive_preflight(self, raw):
        # Reject ZIP64/multidisk and oversized central directories before
        # ZipFile materializes one ZipInfo object per attacker-controlled entry.
        eocd_window_start = max(0, len(raw) - (22 + 0xFFFF))
        eocd_offset = raw.rfind(b'PK\x05\x06', eocd_window_start)
        if eocd_offset < 0 or eocd_offset + 22 > len(raw):
            return None
        try:
            (
                signature,
                disk_number,
                central_disk,
                disk_entries,
                total_entries,
                central_size,
                central_offset,
                comment_size,
            ) = struct.unpack_from('<4s4H2IH', raw, eocd_offset)
        except struct.error:
            return None
        if (
            signature != b'PK\x05\x06'
            or disk_number
            or central_disk
            or disk_entries != total_entries
            or total_entries == 0xFFFF
            or total_entries > _MAX_DOCX_ENTRIES
            or central_size > _MAX_DOCX_CENTRAL_DIRECTORY_BYTES
            or central_offset + central_size != eocd_offset
            or eocd_offset + 22 + comment_size != len(raw)
        ):
            return None

        central_cursor = central_offset
        central_end = central_offset + central_size
        actual_entries = 0
        while central_cursor < central_end:
            if central_end - central_cursor < 46:
                return None
            if raw[central_cursor:central_cursor + 4] != b'PK\x01\x02':
                return None
            try:
                compressed_size, uncompressed_size = struct.unpack_from(
                    '<II', raw, central_cursor + 20,
                )
                filename_size, extra_size, entry_comment_size = struct.unpack_from(
                    '<HHH', raw, central_cursor + 28,
                )
                disk_start = struct.unpack_from('<H', raw, central_cursor + 34)[0]
                local_header_offset = struct.unpack_from('<I', raw, central_cursor + 42)[0]
            except struct.error:
                return None
            central_record_end = (
                central_cursor + 46 + filename_size + extra_size + entry_comment_size
            )
            if (
                not filename_size
                or disk_start
                or compressed_size == 0xFFFFFFFF
                or uncompressed_size == 0xFFFFFFFF
                or local_header_offset + 30 > central_offset
                or central_record_end > central_end
                or raw[local_header_offset:local_header_offset + 4] != b'PK\x03\x04'
            ):
                return None
            try:
                local_filename_size, local_extra_size = struct.unpack_from(
                    '<HH', raw, local_header_offset + 26,
                )
            except struct.error:
                return None
            local_data_start = (
                local_header_offset + 30 + local_filename_size + local_extra_size
            )
            if local_data_start + compressed_size > central_offset:
                return None
            central_filename = raw[
                central_cursor + 46:central_cursor + 46 + filename_size
            ]
            local_filename = raw[
                local_header_offset + 30:local_header_offset + 30 + local_filename_size
            ]
            if local_filename_size != filename_size or local_filename != central_filename:
                return None
            actual_entries += 1
            if actual_entries > _MAX_DOCX_ENTRIES:
                return None
            central_cursor = central_record_end
        if central_cursor != central_end or actual_entries != total_entries:
            return None
        return actual_entries

    @api.model
    def _irg_read_bounded_zip_member(self, archive, info):
        with archive.open(info, 'r') as member:
            content = member.read(_MAX_DOCX_XML_BYTES + 1)
            if len(content) > _MAX_DOCX_XML_BYTES or member.read(1):
                return None
        return content

    @api.model
    def _irg_parse_safe_xml(self, raw):
        lowered = raw.lower()
        if b'<!doctype' in lowered or b'<!entity' in lowered:
            return None
        return ElementTree.fromstring(raw)

    @api.model
    def _irg_madrid_today(self):
        return datetime.now(_MADRID_TZ).date()

    @api.model
    def _irg_validate_stage(self, thesis, stage, today, internal_exception=False):
        if stage not in ('outline', 'partial', 'final'):
            raise ValidationError(_('Invalid TFM delivery stage.'))
        convocation = thesis.irg_tfm_convocation_id
        if stage == 'outline':
            if convocation:
                raise ValidationError(_('Outline submissions close when a convocation is assigned.'))
            return self.env['irg.tfm.convocatoria']
        if not convocation:
            raise ValidationError(_('A convocation is required for this delivery stage.'))
        if not convocation.active:
            raise ValidationError(_('An archived TFM convocation cannot accept new deliveries.'))
        if internal_exception:
            return convocation
        opening = convocation.partial_open_date if stage == 'partial' else convocation.final_open_date
        closing = convocation.partial_close_date if stage == 'partial' else convocation.final_close_date
        if not opening or not closing or not (opening <= today <= closing):
            raise ValidationError(_('This TFM delivery window is closed.'))
        return convocation

    @api.model
    def _irg_create_portal_submission(
        self, course_id, stage, raw, filename, declared_mimetype, comment=None,
    ):
        thesis = self.env['tesis.model']._irg_portal_owned_thesis(course_id)
        if thesis.course_id.course_id.is_diplomado():
            raise AccessError(_('TFM submissions are not available for this course.'))
        safe_name, mimetype = self._irg_validate_upload(raw, filename, declared_mimetype)
        return self._irg_create_locked_submission(
            thesis,
            stage,
            raw,
            safe_name,
            mimetype,
            comment=comment,
            portal_course_id=course_id,
        )

    @api.model
    def _irg_create_locked_submission(
        self,
        thesis,
        stage,
        raw,
        safe_name,
        mimetype,
        comment=None,
        internal_exception=False,
        exception_reason=None,
        portal_course_id=None,
    ):
        thesis.ensure_one()
        if portal_course_id is None:
            if not self.env.user.has_group('base.group_user'):
                raise AccessError(_('Only internal users can create TFM delivery exceptions.'))
        else:
            owned = self.env['tesis.model']._irg_portal_owned_thesis(portal_course_id)
            if owned.id != thesis.id:
                raise AccessError(_('The requested TFM record is unavailable.'))
        thesis = self._irg_lock_submission_configuration(thesis)
        if portal_course_id is not None:
            owned = self.env['tesis.model']._irg_portal_owned_thesis(portal_course_id)
            if owned.id != thesis.id:
                raise AccessError(_('The requested TFM record is unavailable.'))

        convocation = self._irg_validate_stage(
            thesis,
            stage,
            self._irg_madrid_today(),
            internal_exception=internal_exception,
        )
        convocation_key = convocation.id if convocation else 0
        Delivery = self.sudo().with_context(_irg_tfm_private_create=True)
        domain = [
            ('thesis_id', '=', thesis.id),
            ('stage', '=', stage),
            ('convocation_key', '=', convocation_key),
        ]
        delivery = self.browse()
        for attempt in range(2):
            previous = Delivery.search(domain, order='version desc', limit=1)
            try:
                with self.env.cr.savepoint():
                    delivery = Delivery.create({
                        'thesis_id': thesis.id,
                        'stage': stage,
                        'convocation_id': convocation.id if convocation else False,
                        'convocation_key': convocation_key,
                        'version': (previous.version or 0) + 1,
                        'comment': comment or False,
                        'submitted_by': self.env.user.id,
                        'submitted_at': fields.Datetime.now(),
                        'internal_exception': internal_exception,
                        'exception_reason': exception_reason or False,
                    })
                break
            except IntegrityError as exc:
                if getattr(exc.diag, 'constraint_name', None) != _VERSION_CONSTRAINT:
                    raise
                if attempt:
                    raise ValidationError(_('Could not allocate a unique delivery version.'))
                Delivery.invalidate_model(['version'])

        attachment = self.env['ir.attachment'].sudo().create({
            'name': safe_name,
            'type': 'binary',
            'datas': base64.b64encode(raw),
            'mimetype': mimetype,
            'public': False,
            'res_model': self._name,
            'res_id': delivery.id,
        })
        delivery.write({'attachment_id': attachment.id})
        return delivery

    @api.model
    def _irg_lock_submission_configuration(self, thesis):
        """Lock and reread delivery configuration in the global TFM order."""
        thesis.ensure_one()
        self.env.cr.execute(
            '''
                SELECT enrollment.course_id, thesis.irg_tfm_convocation_id
                  FROM tesis_model AS thesis
                  JOIN op_student_course AS enrollment ON enrollment.id = thesis.course_id
                 WHERE thesis.id = %s
            ''',
            [thesis.id],
        )
        configuration = self.env.cr.fetchone()
        if not configuration:
            raise AccessError(_('The requested TFM record is unavailable.'))
        course_id, convocation_id = configuration

        if convocation_id:
            self.env.cr.execute(
                'SELECT id FROM irg_tfm_convocatoria WHERE id = %s FOR UPDATE',
                [convocation_id],
            )
            if not self.env.cr.fetchone():
                raise ValidationError(_('The assigned TFM convocation is unavailable.'))
        self.env.cr.execute(
            'SELECT id FROM op_course WHERE id = %s FOR UPDATE',
            [course_id],
        )
        if not self.env.cr.fetchone():
            raise AccessError(_('The requested TFM course is unavailable.'))
        self.env.cr.execute(
            'SELECT id FROM tesis_model WHERE id = %s FOR UPDATE',
            [thesis.id],
        )
        if not self.env.cr.fetchone():
            raise AccessError(_('The requested TFM record is unavailable.'))

        thesis.invalidate_recordset(['course_id', 'irg_tfm_convocation_id'])
        thesis = thesis.exists()
        if not thesis:
            raise AccessError(_('The requested TFM record is unavailable.'))
        current_course = thesis.course_id.course_id
        current_convocation = thesis.irg_tfm_convocation_id
        if current_course.id != course_id or current_convocation.id != (convocation_id or False):
            raise ValidationError(_(
                'The TFM delivery configuration changed concurrently; retry the submission.'
            ))
        current_course.invalidate_recordset(['irg_tfm_channel_id'])
        if current_convocation:
            current_convocation.invalidate_recordset([
                'active',
                'partial_open_date',
                'partial_close_date',
                'final_open_date',
                'final_close_date',
            ])
        return thesis


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _irg_is_tfm_delivery_attachment(self):
        if not self.ids:
            return False
        return bool(self.env['irg.tfm.entrega'].sudo().search_count([
            ('attachment_id', 'in', self.ids),
        ]))

    def write(self, vals):
        if self._irg_is_tfm_delivery_attachment():
            raise AccessError(_('TFM delivery attachments are immutable.'))
        return super().write(vals)

    def unlink(self):
        if self._irg_is_tfm_delivery_attachment():
            raise AccessError(_('TFM delivery attachments cannot be deleted.'))
        return super().unlink()
