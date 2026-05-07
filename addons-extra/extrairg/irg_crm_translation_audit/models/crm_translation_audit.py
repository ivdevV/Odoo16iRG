# -*- coding: utf-8 -*-
from collections import Counter

from markupsafe import escape

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


CORE_CRM_MODULES = (
    'crm',
    'irg_migration_fields',
    'irg_academic_adaptations',
    'irg_crm_extensions',
    'irg_crm_gclid',
    'irg_crm_lead_dedup',
    'irg_crm_reactivacion',
)

ISEP_CRM_MODULES = (
    'isep_crm_asiguser',
    'isep_crm_lead_checklist',
    'isep_mautic_sincrono',
    'isep_google_ads',
    'isep_tag_custom',
    'mk_typeform',
)


class IrgCrmTranslationAuditWizard(models.TransientModel):
    _name = 'irg.crm.translation.audit.wizard'
    _description = 'CRM Translation Audit Wizard'

    lang_id = fields.Many2one(
        'res.lang',
        string=_('Idioma'),
        default=lambda self: self.env['res.lang'].search([
            ('code', '=', self.env.context.get('lang') or self.env.user.lang)
        ], limit=1),
        required=True,
    )
    include_isep_crm = fields.Boolean(
        string=_('Incluir módulos CRM de addons_uisep'),
        default=True,
    )
    name_filter = fields.Char(
        string=_('Filtro técnico'),
        default='crm',
        help=_('Filtra por nombre técnico de término. Déjalo vacío para usar solo el filtro por módulo.'),
    )
    result_html = fields.Html(
        string=_('Resumen'),
        readonly=True,
    )

    def action_refresh(self):
        self.ensure_one()
        Translation = self._get_translation_model()
        module_names = self._module_names()
        domain = self._translation_domain(Translation, module_names)
        records = Translation.search(domain, limit=5000, order=self._translation_order(Translation))
        self.result_html = self._render_summary(Translation, records, module_names)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _get_translation_model(self):
        try:
            return self.env['ir.translation']
        except KeyError as error:
            raise UserError(_(
                'El modelo ir.translation no está disponible en esta instancia. '
                'No se puede auditar el catálogo clásico de traducciones.'
            )) from error

    def _module_names(self):
        modules = list(CORE_CRM_MODULES)
        if self.include_isep_crm:
            modules.extend(ISEP_CRM_MODULES)
        return modules

    def _translation_domain(self, Translation, module_names):
        domain = []
        if 'lang' in Translation._fields and self.lang_id.code:
            domain.append(('lang', '=', self.lang_id.code))

        technical_domains = []
        if 'module' in Translation._fields:
            technical_domains.append([('module', 'in', module_names)])
        if self.name_filter and 'name' in Translation._fields:
            technical_domains.append([('name', 'ilike', self.name_filter)])

        if technical_domains:
            domain = expression.AND([domain, expression.OR(technical_domains)])
        return domain

    def _translation_order(self, Translation):
        order_fields = [field_name for field_name in ('module', 'type', 'name') if field_name in Translation._fields]
        return ', '.join(order_fields) or 'id'

    def _render_summary(self, Translation, records, module_names):
        lang_code = self.lang_id.code or ''
        module_counter = Counter()
        type_counter = Counter()
        for record in records:
            module_counter[self._record_value(record, 'module') or _('Sin módulo')] += 1
            type_counter[self._record_value(record, 'type') or _('Sin tipo')] += 1

        parts = [
            '<div class="o_irg_crm_translation_audit">',
            '<h3>%s</h3>' % escape(_('Auditor de traducciones CRM')),
            '<p><strong>%s:</strong> %s</p>' % (escape(_('Idioma')), escape(lang_code)),
            '<p><strong>%s:</strong> %s</p>' % (
                escape(_('Módulos inspeccionados')),
                escape(', '.join(module_names)),
            ),
            '<p><strong>%s:</strong> %s</p>' % (
                escape(_('Términos encontrados')),
                escape(str(len(records))),
            ),
        ]

        if len(records) >= 5000:
            parts.append('<p class="text-warning">%s</p>' % escape(_(
                'El resultado llegó al límite de 5000 términos; afina el filtro si necesitas una lectura completa.'
            )))

        if not records:
            parts.append('<p>%s</p>' % escape(_(
                'No se encontraron términos en ir.translation para el filtro seleccionado. '
                'Esto no descarta traducciones almacenadas directamente en campos traducibles de Odoo 16.'
            )))
            parts.append('</div>')
            return ''.join(parts)

        parts.extend(self._render_counter_table(_('Términos por módulo'), module_counter))
        parts.extend(self._render_counter_table(_('Términos por tipo'), type_counter))
        parts.extend(self._render_sample_table(Translation, records[:25]))
        parts.append('</div>')
        return ''.join(parts)

    def _render_counter_table(self, title, counter):
        rows = ['<h4>%s</h4>' % escape(title), '<table class="table table-sm table-striped"><tbody>']
        for label, count in counter.most_common():
            rows.append('<tr><td>%s</td><td class="text-end">%s</td></tr>' % (escape(label), escape(str(count))))
        rows.append('</tbody></table>')
        return rows

    def _render_sample_table(self, Translation, records):
        header_fields = [field_name for field_name in ('module', 'type', 'name', 'src', 'value') if field_name in Translation._fields]
        rows = [
            '<h4>%s</h4>' % escape(_('Muestras')),
            '<table class="table table-sm table-hover">',
            '<thead><tr>%s</tr></thead>' % ''.join('<th>%s</th>' % escape(field_name) for field_name in header_fields),
            '<tbody>',
        ]
        for record in records:
            rows.append('<tr>%s</tr>' % ''.join(
                '<td>%s</td>' % escape(self._record_value(record, field_name))
                for field_name in header_fields
            ))
        rows.extend(['</tbody>', '</table>'])
        return rows

    def _record_value(self, record, field_name):
        if field_name not in record._fields:
            return ''
        value = record[field_name]
        if not value:
            return ''
        return str(value)
