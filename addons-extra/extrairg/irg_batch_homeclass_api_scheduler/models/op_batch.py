# -*- coding: utf-8 -*-
import logging
import requests
import urllib.parse
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class OpBatch(models.Model):
    _inherit = 'op.batch'

    is_homeclass_batch = fields.Boolean(
        string="Es HomeClass",
        compute="_compute_is_homeclass_batch",
    )

    @api.depends('modality_id', 'modality_id.code', 'modality_id.name', 'code', 'name')
    def _compute_is_homeclass_batch(self):
        for record in self:
            is_hc = False
            if record.modality_id:
                is_hc = (record.modality_id.code == 'HC') or ('homeclass' in (record.modality_id.name or '').lower())
            if not is_hc:
                # Fallback check on code or name
                code_upper = (record.code or '').upper()
                name_lower = (record.name or '').lower()
                is_hc = ('HC' in code_upper) or ('homeclass' in name_lower)
            record.is_homeclass_batch = is_hc


    def _sync_homeclass_calendar(self):
        """
        Connects to the external CRM Calendar API using the batch code.
        Finds the earliest date for each subject/block and schedules it.
        Also sets the overall batch class start date.
        """
        self.ensure_one()
        if not self.code:
            _logger.info("Sync HomeClass: Batch ID %s has no code, skipping sync.", self.id)
            return False

        if not self.is_homeclass_batch:
            _logger.info("Sync HomeClass: Batch %s is not HomeClass modality, skipping sync.", self.code)
            return False


        # Get API Base URL
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'irg_calendarios.api_base_url',
            default='https://calendario.institutoraimongaja.com'
        ).rstrip('/')

        # Request external API
        lote_encoded = urllib.parse.quote(self.code.strip())
        url = f"{base_url}/api/lotes/{lote_encoded}/calendario"

        _logger.info("Sync HomeClass: Syncing batch %s using URL: %s", self.code, url)
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 404:
                _logger.warning("Sync HomeClass: Batch %s not found in CRM Calendar API (404).", self.code)
                return False
            elif response.status_code != 200:
                _logger.error("Sync HomeClass: API returned error status %s for batch %s.", response.status_code, self.code)
                return False
            data = response.json()
        except Exception as e:
            _logger.error("Sync HomeClass: Exception occurred connecting to API for batch %s: %s", self.code, str(e))
            return False

        records = data.get('records', [])
        if not records:
            _logger.warning("Sync HomeClass: No records returned in calendar API for batch %s.", self.code)
            return False

        # Group minimum dates by block code and block name
        bloque_dates = {}
        for rec in records:
            fecha_str = rec.get('fecha')
            if not fecha_str:
                continue
            try:
                date_val = datetime.strptime(fecha_str.strip(), '%d/%m/%Y').date()
            except ValueError:
                _logger.warning("Sync HomeClass: Invalid date format '%s' for batch %s", fecha_str, self.code)
                continue

            bloque_code = rec.get('bloque')
            if bloque_code:
                b_code = str(bloque_code).strip().upper()
                if b_code not in bloque_dates or date_val < bloque_dates[b_code]:
                    bloque_dates[b_code] = date_val

            bloque_name = rec.get('bloqueAsignaturas')
            if bloque_name:
                b_name = str(bloque_name).strip().upper()
                if b_name not in bloque_dates or date_val < bloque_dates[b_name]:
                    bloque_dates[b_name] = date_val

        if not bloque_dates:
            _logger.warning("Sync HomeClass: No valid dates mapped from calendar API for batch %s.", self.code)
            return False

        # Match batch subjects (op.subject.to.batch) with API dates
        earliest_matched_class_date = False
        updated_lines = 0

        # We disable re-triggering this method during the write call
        self_ctx = self.with_context(skip_homeclass_sync=True)

        for line in self_ctx.subject_to_batch_ids:
            subject_code = str(line.code).strip().upper() if line.code else None
            subject_name = str(line.subject_id.name).strip().upper() if (line.subject_id and line.subject_id.name) else None

            match_date = None
            if subject_code and subject_code in bloque_dates:
                match_date = bloque_dates[subject_code]
            elif subject_name and subject_name in bloque_dates:
                match_date = bloque_dates[subject_name]

            if match_date:
                line.write({
                    'date_from': match_date,
                    'date_to': self_ctx.end_date,
                })
                updated_lines += 1
                if not earliest_matched_class_date or match_date < earliest_matched_class_date:
                    earliest_matched_class_date = match_date
            else:
                # If there's no match, default to batch start and end dates
                line.write({
                    'date_from': self_ctx.start_date,
                    'date_to': self_ctx.end_date,
                })

        # Update batch class start date
        if earliest_matched_class_date:
            _logger.info("Sync HomeClass: Setting date_start_class to %s for batch %s", earliest_matched_class_date, self.code)
            if self_ctx.date_start_class != earliest_matched_class_date:
                self_ctx.write({'date_start_class': earliest_matched_class_date})

        _logger.info("Sync HomeClass: Batch %s synced successfully. Scheduled %s subjects.", self.code, updated_lines)
        return True

    def action_sync_homeclass_calendar(self):
        """
        Manual button action to trigger calendar sync.
        Provides user feedback via notifications/exceptions.
        """
        self.ensure_one()
        if not self.is_homeclass_batch:
            raise UserError(_("Este lote no pertenece a la modalidad HomeClass o no se detectó como tal."))
        if not self.code:
            raise UserError(_("El lote debe tener un código asignado para poder sincronizar con la API."))


        success = self._sync_homeclass_calendar()
        if success:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sincronización Exitosa'),
                    'message': _('Las fechas de las asignaturas y del lote se han actualizado correctamente desde la API.'),
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    },
                },
            }
        else:
            raise UserError(_("No se pudo sincronizar el lote. Compruebe los logs del sistema o que el código del lote exista en la API de calendarios."))

    @api.model
    def create(self, vals):
        record = super(OpBatch, self.with_context(skip_homeclass_sync=True)).create(vals)
        if not self.env.context.get('skip_homeclass_sync'):
            # Run sync for HomeClass batches safely
            record.with_context(skip_homeclass_sync=True)._sync_homeclass_calendar()
        return record

    def write(self, vals):
        res = super(OpBatch, self.with_context(skip_homeclass_sync=True)).write(vals)
        if not self.env.context.get('skip_homeclass_sync'):
            # Only trigger sync if relevant fields changed
            if any(f in vals for f in ['code', 'start_date', 'end_date', 'modality_id', 'course_id', 'subject_to_batch_ids']):
                for record in self:
                    record.with_context(skip_homeclass_sync=True)._sync_homeclass_calendar()
        return res

