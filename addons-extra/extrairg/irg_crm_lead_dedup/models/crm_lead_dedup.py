import logging
import re
from datetime import datetime
from odoo import models, fields, api
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)

CHUNK_SIZE = 50
PARAM_LAST_RUN = 'irg_crm_lead_dedup.last_run'


class CrmLeadDedup(models.Model):
    _inherit = 'crm.lead'

    irg_dedup_merged = fields.Boolean(
        string='Fusionado por dedup',
        default=False,
        help='Marcado cuando este lead fue archivado por el proceso de deduplicacion. '
             'Se excluye de futuros runs para evitar doble procesamiento.',
    )

    @api.model
    def action_dedup_leads(self):
        """
        Cron diario: detecta leads/oportunidades duplicados por email o telefono,
        fusiona sus datos en el mas nuevo y archiva los mas antiguos.

        Reglas:
        - Los leads ganados (stage is_won) nunca se tocan.
        - Los leads ya procesados (irg_dedup_merged=True) se excluyen para
          evitar doble procesamiento en runs futuros.
        - Los leads perdidos (active=False, irg_dedup_merged=False) si participan.
        - Modo incremental: solo procesa grupos con al menos un lead nuevo desde
          el ultimo run exitoso. El watermark se guarda al final para evitar
          perder grupos si el cron falla a mitad de ejecucion.
        """
        _logger.info("[irg_crm_lead_dedup] Iniciando deduplicacion de leads")

        config = self.env['ir.config_parameter'].sudo()
        last_run_str = config.get_param(PARAM_LAST_RUN)
        last_run = datetime.fromisoformat(last_run_str) if last_run_str else None
        run_start = datetime.utcnow()

        if last_run:
            _logger.info("[irg_crm_lead_dedup] Modo incremental desde %s", last_run)
        else:
            _logger.info("[irg_crm_lead_dedup] Primera ejecucion: procesando toda la base de datos")

        # --- FASE 1: cargar datos minimos via SQL ---
        # Excluye leads ya archivados por este cron (irg_dedup_merged = TRUE)
        # Incluye leads perdidos (active = FALSE, irg_dedup_merged IS NOT TRUE)
        self.env.cr.execute("""
            SELECT id, email_from, phone, mobile, create_date, stage_id
            FROM crm_lead
            WHERE irg_dedup_merged IS NOT TRUE
            ORDER BY create_date ASC
        """)
        leads_data = self.env.cr.dictfetchall()
        _logger.info("[irg_crm_lead_dedup] Leads cargados: %d", len(leads_data))

        if not leads_data:
            _logger.info("[irg_crm_lead_dedup] Sin leads que procesar.")
            return

        # Stages ganados en una sola query
        self.env.cr.execute("SELECT id FROM crm_stage WHERE is_won = TRUE")
        won_stage_ids = {row['id'] for row in self.env.cr.dictfetchall()}

        # Lookups UTM: cargados una sola vez para todo el run
        self.env.cr.execute("SELECT id, name FROM utm_campaign")
        utm_campaigns = {r['id']: r['name'] for r in self.env.cr.dictfetchall()}
        self.env.cr.execute("SELECT id, name FROM utm_source")
        utm_sources = {r['id']: r['name'] for r in self.env.cr.dictfetchall()}
        self.env.cr.execute("SELECT id, name FROM utm_medium")
        utm_mediums = {r['id']: r['name'] for r in self.env.cr.dictfetchall()}
        utm_lookups = {
            'campaign_id': ('Campana', utm_campaigns),
            'source_id': ('Fuente', utm_sources),
            'medium_id': ('Medio', utm_mediums),
        }

        stage_by_lead = {l['id']: l['stage_id'] for l in leads_data}
        create_date_by_id = {l['id']: l['create_date'] for l in leads_data}

        # --- FASE 2: agrupar por clave de dedup (Union-Find) ---
        key_to_gid = {}
        gid_to_ids = {}
        next_gid = [0]

        def _new_gid():
            gid = next_gid[0]
            next_gid[0] += 1
            return gid

        for lead in leads_data:
            keys = set()
            email_key = email_normalize(lead['email_from'] or '')
            if email_key:
                keys.add(('email', email_key))
            phone = re.sub(r'\D', '', lead['phone'] or lead['mobile'] or '')
            if phone:
                keys.add(('phone', phone))

            if not keys:
                continue

            found_gids = {key_to_gid[k] for k in keys if k in key_to_gid}

            if not found_gids:
                gid = _new_gid()
                gid_to_ids[gid] = [lead['id']]
            elif len(found_gids) == 1:
                gid = next(iter(found_gids))
                gid_to_ids[gid].append(lead['id'])
            else:
                # Varios grupos conectados por este lead: fusionarlos en uno
                gids = list(found_gids)
                gid = gids[0]
                for other in gids[1:]:
                    gid_to_ids[gid].extend(gid_to_ids.pop(other))
                    for k, g in list(key_to_gid.items()):
                        if g == other:
                            key_to_gid[k] = gid
                gid_to_ids[gid].append(lead['id'])

            for key in keys:
                key_to_gid[key] = gid

        duplicate_groups = [ids for ids in gid_to_ids.values() if len(ids) > 1]

        # Modo incremental: descartar grupos donde ningun lead sea nuevo desde el ultimo run
        if last_run:
            duplicate_groups = [
                ids for ids in duplicate_groups
                if any(
                    create_date_by_id[lid] and create_date_by_id[lid] > last_run
                    for lid in ids
                )
            ]

        _logger.info("[irg_crm_lead_dedup] Grupos a procesar: %d", len(duplicate_groups))

        if not duplicate_groups:
            config.set_param(PARAM_LAST_RUN, run_start.isoformat())
            _logger.info("[irg_crm_lead_dedup] Sin duplicados. Watermark actualizado.")
            return

        # --- FASE 3: fusionar en chunks ---
        total_merged = 0
        total_chunks = max(1, (len(duplicate_groups) + CHUNK_SIZE - 1) // CHUNK_SIZE)

        for chunk_idx, chunk_start in enumerate(range(0, len(duplicate_groups), CHUNK_SIZE)):
            chunk = duplicate_groups[chunk_start:chunk_start + CHUNK_SIZE]

            # Resolver winner->losers una sola vez por chunk
            resolved = []
            for group_ids in chunk:
                mergeable_ids = [
                    lid for lid in group_ids
                    if stage_by_lead.get(lid) not in won_stage_ids
                ]
                if len(mergeable_ids) < 2:
                    continue
                mergeable_ids.sort(key=lambda lid: create_date_by_id[lid], reverse=True)
                resolved.append((mergeable_ids[0], mergeable_ids[1:]))

            if not resolved:
                continue

            # Cargar description/fecha_reactivacion/UTMs/referred via SQL para este chunk
            all_ids_in_chunk = [lid for wid, lids in resolved for lid in [wid] + lids]
            self.env.cr.execute(
                "SELECT id, description, fecha_reactivacion, campaign_id, source_id, "
                "medium_id, referred, name FROM crm_lead WHERE id = ANY(%s)",
                (all_ids_in_chunk,)
            )
            leads_by_id = {r['id']: r for r in self.env.cr.dictfetchall()}

            # Calcular vals y actualizar winner via SQL directa (sin ORM, sin tracking)
            for winner_id, loser_ids in resolved:
                winner_data = leads_by_id.get(winner_id, {})
                loser_data_list = [leads_by_id[lid] for lid in loser_ids if lid in leads_by_id]
                _logger.info(
                    "[irg_crm_lead_dedup] Fusionando %d leads en #%d (%s)",
                    len(loser_ids), winner_id, winner_data.get('name', '')
                )
                vals = self._build_merge_vals(winner_data, loser_data_list, utm_lookups)
                if vals:
                    set_clauses = ', '.join('%s = %%s' % k for k in vals)
                    self.env.cr.execute(
                        "UPDATE crm_lead SET %s WHERE id = %%s" % set_clauses,
                        list(vals.values()) + [winner_id]
                    )
                total_merged += len(loser_ids)

            # Reasignar mensajes y actividades via SQL
            for winner_id, loser_ids in resolved:
                self.env.cr.execute(
                    "UPDATE mail_message SET res_id = %s "
                    "WHERE model = 'crm.lead' AND res_id = ANY(%s)",
                    (winner_id, loser_ids)
                )
                self.env.cr.execute(
                    "UPDATE mail_activity SET res_id = %s "
                    "WHERE res_model = 'crm.lead' AND res_id = ANY(%s)",
                    (winner_id, loser_ids)
                )

            # Archivar losers del chunk: un solo UPDATE marcando irg_dedup_merged
            all_loser_ids = [lid for _, lids in resolved for lid in lids]
            self.env.cr.execute(
                "UPDATE crm_lead SET active = FALSE, irg_dedup_merged = TRUE "
                "WHERE id = ANY(%s)",
                (all_loser_ids,)
            )

            self.env.cr.commit()
            _logger.info(
                "[irg_crm_lead_dedup] Chunk %d/%d completado (%d losers archivados)",
                chunk_idx + 1, total_chunks, len(all_loser_ids)
            )

        # Guardar watermark DESPUES de completar exitosamente
        config.set_param(PARAM_LAST_RUN, run_start.isoformat())
        _logger.info(
            "[irg_crm_lead_dedup] Completado. Total leads fusionados: %d", total_merged
        )

    def _build_merge_vals(self, winner_data, loser_data_list, utm_lookups):
        """
        Construye el dict de valores a escribir en el winner.
        Trabaja solo con dicts raw de SQL: sin ORM, sin queries adicionales.
        utm_lookups: {'campaign_id': ('Campana', {id: name}), ...}
        """
        description_parts = []
        if winner_data.get('description'):
            description_parts.append(winner_data['description'])

        new_fecha = winner_data.get('fecha_reactivacion')

        for loser in loser_data_list:
            utm_lines = []
            for field, (label, lookup) in utm_lookups.items():
                fk = loser.get(field)
                if fk:
                    utm_lines.append('%s: %s' % (label, lookup.get(fk, str(fk))))
            if loser.get('referred'):
                utm_lines.append('Referido: %s' % loser['referred'])
            if utm_lines:
                description_parts.append(
                    '---\n[UTMs lead fusionado #%d - %s]\n%s' % (
                        loser['id'], loser.get('name', ''), '\n'.join(utm_lines)
                    )
                )

            if loser.get('description'):
                description_parts.append(
                    '---\n[Notas fusionadas desde lead #%d - %s]\n%s' % (
                        loser['id'], loser.get('name', ''), loser['description']
                    )
                )

            loser_fecha = loser.get('fecha_reactivacion')
            if loser_fecha and (not new_fecha or loser_fecha > new_fecha):
                new_fecha = loser_fecha

        vals = {}
        new_description = '\n\n'.join(description_parts) or None
        if new_description != (winner_data.get('description') or None):
            vals['description'] = new_description

        current_fecha = winner_data.get('fecha_reactivacion')
        if new_fecha != current_fecha:
            vals['fecha_reactivacion'] = new_fecha

        return vals
