# -*- coding: utf-8 -*-
import re

from markupsafe import Markup

from odoo import api, fields, models, _

_DNI_RE = re.compile(r'^\d{8}[A-Z]$')
_NIE_RE = re.compile(r'^[XYZ]\d{7}[A-Z]$')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    irg_oficialidad_student_type = fields.Selection(
        selection=[
            ('nacional', 'Nacional'),
            ('internacional', 'Internacional'),
        ],
        string='Tipo de alumno (oficialidad)',
        groups='base.group_user',
    )
    irg_oficialidad_document_ids = fields.One2many(
        'irg.oficialidad.document',
        'partner_id',
        string='Documentacion de oficialidad',
        groups='base.group_user',
    )
    irg_oficialidad_expected_count = fields.Integer(
        string='Documentos esperados',
        compute='_compute_irg_oficialidad_summary',
        groups='base.group_user',
    )
    irg_oficialidad_received_count = fields.Integer(
        string='Documentos recibidos',
        compute='_compute_irg_oficialidad_summary',
        groups='base.group_user',
    )
    irg_oficialidad_completeness = fields.Char(
        string='Completitud oficialidad',
        compute='_compute_irg_oficialidad_summary',
        groups='base.group_user',
    )
    irg_oficialidad_is_complete = fields.Boolean(
        string='Documentacion de oficialidad completa',
        compute='_compute_irg_oficialidad_summary',
        groups='base.group_user',
    )
    irg_oficialidad_last_received_at = fields.Datetime(
        string='Ultima recepcion',
        compute='_compute_irg_oficialidad_summary',
        groups='base.group_user',
    )
    irg_oficialidad_vat_hint = fields.Selection(
        selection=[
            ('nacional', 'Nacional'),
            ('internacional', 'Internacional'),
            ('unknown', 'Desconocido'),
        ],
        string='Tipo sugerido por documento de identidad',
        compute='_compute_irg_oficialidad_vat_hint',
        groups='base.group_user',
    )
    irg_oficialidad_type_mismatch = fields.Boolean(
        string='Tipo de alumno discrepante',
        compute='_compute_irg_oficialidad_vat_hint',
        groups='base.group_user',
    )
    irg_oficialidad_checklist_html = fields.Html(
        string='Checklist de oficialidad',
        compute='_compute_irg_oficialidad_summary',
        sanitize=False,
        readonly=True,
        groups='base.group_user',
    )

    @api.model
    def _irg_oficialidad_vat_hint_from_vat(self, vat):
        if not vat:
            return 'unknown'
        normalized = re.sub(r'[\s.\-]', '', vat).upper()
        if normalized.startswith('ES'):
            normalized = normalized[2:]
        if _DNI_RE.match(normalized) or _NIE_RE.match(normalized):
            return 'nacional'
        return 'internacional'

    @api.depends('vat', 'irg_oficialidad_student_type')
    def _compute_irg_oficialidad_vat_hint(self):
        for partner in self:
            hint = self._irg_oficialidad_vat_hint_from_vat(partner.vat)
            partner.irg_oficialidad_vat_hint = hint
            partner.irg_oficialidad_type_mismatch = bool(
                partner.irg_oficialidad_student_type
                and hint != 'unknown'
                and hint != partner.irg_oficialidad_student_type
            )

    @api.depends(
        'irg_oficialidad_student_type',
        'irg_oficialidad_document_ids.document_type_id',
        'irg_oficialidad_document_ids.state',
        'irg_oficialidad_document_ids.write_date',
    )
    def _compute_irg_oficialidad_summary(self):
        type_model = self.env['irg.oficialidad.document.type'].sudo()
        state_labels = dict(
            self.env['irg.oficialidad.document']._fields['state']._description_selection(self.env)
        )
        expected_by_type = {}
        for partner in self:
            student_type = partner.irg_oficialidad_student_type
            if student_type not in expected_by_type:
                keys = type_model.get_expected_keys(student_type) if student_type else []
                types_by_key = {
                    rec.key: rec
                    for rec in type_model.search([('key', 'in', keys)])
                } if keys else {}
                expected_by_type[student_type] = [types_by_key[k] for k in keys if k in types_by_key]
            expected_types = expected_by_type[student_type]
            docs_by_type = {}
            for doc in partner.irg_oficialidad_document_ids:
                docs_by_type.setdefault(doc.document_type_id.id, doc)

            expected = len(expected_types)
            received_docs = [
                docs_by_type[t.id] for t in expected_types if t.id in docs_by_type
            ]
            received = len(received_docs)
            partner.irg_oficialidad_expected_count = expected
            partner.irg_oficialidad_received_count = received
            partner.irg_oficialidad_completeness = (
                '%d/%d' % (received, expected) if expected else False
            )
            partner.irg_oficialidad_is_complete = bool(expected and received == expected)
            stamps = [d.write_date or d.create_date for d in received_docs]
            stamps = [s for s in stamps if s]
            partner.irg_oficialidad_last_received_at = max(stamps) if stamps else False

            if not expected:
                partner.irg_oficialidad_checklist_html = False
                continue
            items = []
            for doc_type in expected_types:
                doc = docs_by_type.get(doc_type.id)
                if doc:
                    status = _('Recibido')
                    detail = state_labels.get(doc.state, doc.state)
                    items.append(Markup('<li><strong>%s</strong>: %s (%s)</li>') % (
                        doc_type.name, status, detail,
                    ))
                else:
                    items.append(Markup('<li><strong>%s</strong>: %s</li>') % (
                        doc_type.name, _('Pendiente'),
                    ))
            partner.irg_oficialidad_checklist_html = (
                Markup('<ul class="mb-0">%s</ul>') % Markup('').join(items)
            )
