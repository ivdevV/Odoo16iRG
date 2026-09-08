# -*- coding: utf-8 -*-
import base64
import hashlib
import re

from odoo.exceptions import UserError
from odoo.tools.translate import _

from . import api_serializer as ser

DOCUMENT_TYPES = {'gradebook', 'gradebook_partial'}
MOVED_DOCUMENT_TYPES = {
    'diploma': 'irg_generate_diploma',
    'enrollment': 'irg_generate_enrollment_certificate',
    'attendance': 'irg_generate_attendance_certificate',
}
CERTIFICATE_TYPES = {'digital', 'physical', 'custom', 'physical_apostilled'}
PHYSICAL_TYPES = {'physical', 'physical_apostilled'}
SIGNERS = {'dpto_academico', 'raimon'}
SHIPPING_TYPES = {'national', 'international'}
CUSTOM_OPTIONS = {'language_en', 'language_fr', 'specific_subjects', 'official_seal'}
CONTENT_ID_RE = re.compile(r'/web/content/(\d+)')


class GradebookService:

    def __init__(self, env):
        self.env = env

    def get_gradebook_summary(self, payload):
        if 'app.gradebook.student' not in self.env:
            return {'available': False, 'results': []}
        domain = []
        if payload.get('admission_id'):
            domain.append(('admission_id', '=', ser.require_positive_id(payload, 'admission_id')))
        elif payload.get('partner_id'):
            domain.append(('partner_id', '=', ser.require_positive_id(payload, 'partner_id')))
        else:
            raise UserError(_('admission_id or partner_id is required.'))
        books = self.env['app.gradebook.student'].search(domain)
        results = []
        for book in books:
            subjects = []
            for subject in book.gradebook_subject_ids:
                source_results = []
                if 'gradebook_result_ids' in subject._fields:
                    for result in subject.gradebook_result_ids:
                        source_results.append({
                            'id': result.id,
                            'survey_type': result.survey_type,
                            'scoring_total': result.scoring_total,
                            'survey_user_input_id': (
                                result.survey_user_input_id.id
                                if result.survey_user_input_id else False
                            ),
                        })
                subjects.append({
                    'id': subject.id,
                    'subject_id': subject.op_subject_id.id if subject.op_subject_id else False,
                    'final_subject_note': (
                        subject.final_subject_note
                        if 'final_subject_note' in subject._fields else False
                    ),
                    'results': source_results,
                })
            results.append({
                'id': book.id,
                'state': book.state,
                'admission_id': book.admission_id.id if book.admission_id else False,
                'subjects': subjects,
            })
        return {'available': True, 'results': results}

    def get_student_grade_evidence(self, payload):
        summary = self.get_gradebook_summary(payload)
        if not summary.get('available'):
            return summary
        subject_id = payload.get('subject_id')
        if subject_id:
            wanted = ser.require_positive_id(payload, 'subject_id')
            for book in summary.get('results') or []:
                book['subjects'] = [
                    subject for subject in book.get('subjects') or []
                    if subject.get('subject_id') == wanted
                ]
        return summary

    def _require_certificates(self):
        if 'irg.certificate.wizard' not in self.env or 'irg.certificate.request' not in self.env:
            raise UserError(_('Gradebook certificates are not installed.'))
        if 'app.gradebook.student' not in self.env:
            raise UserError(_('Gradebook is not installed.'))

    def _gradebook(self, payload):
        self._require_certificates()
        gradebook = self.env['app.gradebook.student'].browse(
            ser.require_positive_id(payload, 'gradebook_student_id')
        )
        if not gradebook.exists():
            raise UserError(_('Unknown gradebook_student_id.'))
        return gradebook

    def _validated_certificate_vals(self, payload):
        gradebook = self._gradebook(payload)
        document_type = (payload.get('document_type') or '').strip()
        if document_type in MOVED_DOCUMENT_TYPES:
            raise UserError(_(
                'Use %s. This command only generates gradebook certificates.'
            ) % MOVED_DOCUMENT_TYPES[document_type])
        if document_type not in DOCUMENT_TYPES:
            raise UserError(_('document_type must be gradebook or gradebook_partial.'))
        certificate_type = (payload.get('certificate_type') or '').strip()
        if certificate_type not in CERTIFICATE_TYPES:
            raise UserError(_('certificate_type is not valid.'))
        signer = (payload.get('signer') or '').strip()
        if signer not in SIGNERS:
            raise UserError(_('signer is required and must be dpto_academico or raimon.'))
        shipping_type = (payload.get('shipping_type') or '').strip() or False
        if certificate_type in PHYSICAL_TYPES:
            if shipping_type not in SHIPPING_TYPES:
                raise UserError(_('shipping_type is required for physical certificates.'))
        elif shipping_type:
            raise UserError(_('shipping_type is only allowed for physical certificates.'))
        custom_options = payload.get('custom_options') or False
        if custom_options and custom_options not in CUSTOM_OPTIONS:
            raise UserError(_('custom_options is not valid.'))
        if document_type == 'gradebook' and gradebook.state != 'done':
            raise UserError(_(
                "Para solicitar un Certificado de Notas Completo, la libreta académica "
                "debe estar finalizada (estado 'Finalizado')."
            ))
        vals = {
            'gradebook_student_id': gradebook.id,
            'document_type': document_type,
            'certificate_type': certificate_type,
            'signer': signer,
            'shipping_type': shipping_type,
        }
        custom_description = payload.get('custom_description') or False
        if custom_description:
            vals['custom_description'] = custom_description
        if custom_options:
            vals['custom_options'] = custom_options
        return gradebook, vals

    def _certificate_from_download_action(self, action):
        url = (action or {}).get('url') or ''
        match = CONTENT_ID_RE.search(url)
        if not match:
            raise UserError(_('Certificate PDF was not generated.'))
        attachment = self.env['ir.attachment'].with_context(bin_size=False).browse(int(match.group(1)))
        if not attachment.exists():
            raise UserError(_('Certificate PDF was not generated.'))
        if attachment.res_model != 'irg.certificate.request':
            raise UserError(_('Certificate PDF was not generated.'))
        cert = self.env['irg.certificate.request'].browse(attachment.res_id)
        if not cert.exists():
            raise UserError(_('Certificate PDF was not generated.'))
        return cert, attachment

    def preview_generate_gradebook_certificate(self, payload):
        gradebook, vals = self._validated_certificate_vals(payload)
        self.env['irg.certificate.wizard'].create(vals)
        count = self.env['irg.certificate.request'].search_count([
            ('gradebook_student_id', '=', gradebook.id),
        ])
        before = {
            'gradebook_student_id': gradebook.id,
            'gradebook_state': gradebook.state,
            'certificate_count': count,
        }
        proposed = dict(vals)
        proposed['gradebook_state'] = gradebook.state
        proposed['will_call'] = 'irg.certificate.wizard.action_generate'
        return before, proposed, {'model': 'app.gradebook.student', 'id': gradebook.id}

    def apply_generate_gradebook_certificate(self, proposed, before):
        payload = {
            'gradebook_student_id': proposed.get('gradebook_student_id'),
            'document_type': proposed.get('document_type'),
            'certificate_type': proposed.get('certificate_type'),
            'signer': proposed.get('signer'),
            'shipping_type': proposed.get('shipping_type') or False,
        }
        if proposed.get('custom_description'):
            payload['custom_description'] = proposed['custom_description']
        if proposed.get('custom_options'):
            payload['custom_options'] = proposed['custom_options']
        gradebook, vals = self._validated_certificate_vals(payload)
        if gradebook.state != before.get('gradebook_state'):
            raise UserError(_('The gradebook changed after preview.'))
        wizard = self.env['irg.certificate.wizard'].create(vals)
        action = wizard.action_generate()
        cert, attachment = self._certificate_from_download_action(action)
        if 'public' in attachment._fields and attachment.public:
            raise UserError(_('Certificate PDF must remain private.'))
        raw = base64.b64decode(attachment.datas or b'')
        if not raw:
            raise UserError(_('Certificate PDF was not generated.'))
        checksum = hashlib.sha256(raw).hexdigest()
        file_b64 = attachment.datas
        if isinstance(file_b64, bytes):
            file_b64 = file_b64.decode('ascii')
        return {
            'certificate_request_id': cert.id,
            'name': cert.name,
            'state': cert.state,
            'attachment_id': attachment.id,
            'attachment_name': attachment.name,
            'mimetype': attachment.mimetype or 'application/pdf',
            'checksum': checksum,
            'file_b64': file_b64,
            'public': False,
        }
