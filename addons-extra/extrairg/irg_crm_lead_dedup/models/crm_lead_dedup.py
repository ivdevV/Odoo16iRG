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
        help='Marcado cuando este lead fue archivado por el proceso de deduplicación. '
             'Se excluye de futuros runs para evitar doble procesamiento.',
    )

    @api.model
    def action_dedup_leads(self):
        """
        Cron diario: detecta leads/oportunidades duplicados por email o teléfono,
        fusiona sus datos en el más nuevo y archiva los más antiguos.

        Reglas:
        - Los leads ganados (stage is_won) nunca se tocan.
        - Los leads ya procesados por este cron (irg_dedup_merged=True) se excluyen
          para evitar doble procesamiento en runs futuros.
        - Los leads perdidos (active=False, irg_dedup_merged=False) sí participan.
        - Modo incremental: solo procesa grupos con al menos un lead nuevo desde
          el último run exitoso. El watermark se guarda al final para evitar
          perder grupos si el cron falla a mitad de ejecución.
        """
        _logger.info("[irg_crm_lead_dedup] Iniciando deduplicación de leads")

        config = self.env['ir.config_parameter'].sudo()
        last_run_str = config.get_param(PARAM_LAST_RUN)
        last_run = datetime.fromisoformat(last_run_str) if last_run_str else None
        run_start = datetime.utcnow()

        if last_run:
            _logger.info("[irg_crm_lead_dedup] Modo incremental desde %s", last_run)
        else:
            _logger.info("[irg_crm_lead_dedup] Primera ejecución: procesando toda la base de datos")

        # --- FASE 1: cargar datos mínimos via SQL ---
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

        # Modo incremental: descartar grupos donde ningún lead sea nuevo desde el último run
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

            # Resolver winner→losers una sola vez por chunk (reutilizado en ORM y SQL)
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

            # Fusionar datos ORM (description, fecha_reactivacion) — un write por winner
            for winner_id, loser_ids in resolved:
                winner = self.with_context(active_test=False).browse(winner_id)
                losers = self.with_context(active_test=False).browse(loser_ids)
                _logger.info(
                    "[irg_crm_lead_dedup] Fusionando %d leads en #%d (%s)",
                    len(loser_ids), winner.id, winner.name
                )
                self._merge_losers_into_winner(winner, losers)
                total_merged += len(loser_ids)

            # Mensajes y actividades via SQL — un UPDATE por grupo
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

            # Archivar losers del chunk: un solo UPDATE, marcando irg_dedup_merged
            all_loser_ids = [lid for _, loser_ids in resolved for lid in loser_ids]
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

        # Guardar watermark DESPUÉS de completar exitosamente
        config.set_param(PARAM_LAST_RUN, run_start.isoformat())
        _logger.info(
            "[irg_crm_lead_dedup] Completado. Total leads fusionados: %d", total_merged
        )

    def _merge_losers_into_winner(self, winner, losers):
        """
        Acumula todos los datos de los losers y hace un único write al winner.
        """
        utm_m2o = {'campaign_id': 'Campaña', 'source_id': 'Fuente', 'medium_id': 'Medio'}
        description_parts = []
        if winner.description:
            description_parts.append(winner.description)

        new_fecha_reactivacion = getattr(winner, 'fecha_reactivacion', None)

        for loser in losers:
            utm_lines = [
                '%s: %s' % (label, loser[field].name)
                for field, label in utm_m2o.items() if loser[field]
            ]
            if loser.referred:
                utm_lines.append('Referido: %s' % loser.referred)
            if utm_lines:
                description_parts.append(
                    '---\n[UTMs lead fusionado #%d - %s]\n%s' % (
                        loser.id, loser.name, '\n'.join(utm_lines)
                    )
                )

            if loser.description:
                description_parts.append(
                    '---\n[Notas fusionadas desde lead #%d - %s]\n%s' % (
                        loser.id, loser.name, loser.description
                    )
                )

            loser_fecha = getattr(loser, 'fecha_reactivacion', None)
            if loser_fecha and (not new_fecha_reactivacion or loser_fecha > new_fecha_reactivacion):
                new_fecha_reactivacion = loser_fecha

        vals = {}
        new_description = '\n\n'.join(description_parts) or False
        if new_description != (winner.description or False):
            vals['description'] = new_description

        current_fecha = getattr(winner, 'fecha_reactivacion', None)
        if hasattr(winner, 'fecha_reactivacion') and new_fecha_reactivacion != current_fecha:
            vals['fecha_reactivacion'] = new_fecha_reactivacion

        if vals:
            winner.sudo().write(vals)


_logger = logging.getLogger(__name__)

CHUNK_SIZE = 50
PARAM_LAST_RUN = 'irg_crm_lead_dedup.last_run'


class CrmLeadDedup(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def action_dedup_leads(self):
        """
        Cron diario: detecta leads/oportunidades duplicados por email o teléfono,
        fusiona sus datos en el más nuevo y archiva los más antiguos.
        Los leads ganados nunca se tocan.

        Modo incremental: solo procesa grupos donde al menos un lead fue creado
        después del último run exitoso. El primer run procesa toda la base de datos.
        El watermark se guarda DESPUÉS de completar para evitar perder grupos
        si el cron falla a mitad de ejecución.
        """
        _logger.info("[irg_crm_lead_dedup] Iniciando deduplicación de leads")

        config = self.env['ir.config_parameter'].sudo()
        last_run_str = config.get_param(PARAM_LAST_RUN)
        last_run = datetime.fromisoformat(last_run_str) if last_run_str else None
        run_start = datetime.utcnow()

        if last_run:
            _logger.info("[irg_crm_lead_dedup] Modo incremental desde %s", last_run)
        else:
            _logger.info("[irg_crm_lead_dedup] Primera ejecución: procesando toda la base de datos")

        # --- FASE 1: cargar datos mínimos via SQL directo ---
        self.env.cr.execute("""
            SELECT id, email_from, phone, mobile, create_date, stage_id
            FROM crm_lead
            ORDER BY create_date ASC
        """)
        leads_data = self.env.cr.dictfetchall()
        _logger.info("[irg_crm_lead_dedup] Leads cargados: %d", len(leads_data))

        # Stages ganados en una sola query
        self.env.cr.execute("SELECT id FROM crm_stage WHERE is_won = TRUE")
        won_stage_ids = {row['id'] for row in self.env.cr.dictfetchall()}

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

        # Modo incremental: descartar grupos sin leads nuevos desde el último run
        if last_run:
            duplicate_groups = [
                ids for ids in duplicate_groups
                if any(
                    create_date_by_id[lid] and create_date_by_id[lid] > last_run
                    for lid in ids
                )
            ]

        _logger.info("[irg_crm_lead_dedup] Grupos a procesar: %d", len(duplicate_groups))

        # --- FASE 3: fusionar en chunks ---
        total_merged = 0
        total_chunks = max(1, (len(duplicate_groups) + CHUNK_SIZE - 1) // CHUNK_SIZE)

        for chunk_idx, chunk_start in enumerate(range(0, len(duplicate_groups), CHUNK_SIZE)):
            chunk = duplicate_groups[chunk_start:chunk_start + CHUNK_SIZE]

            # Resolver el mapa winner→losers una sola vez, reutilizado para SQL
            resolved = []  # lista de (winner_id, loser_ids)
            for group_ids in chunk:
                mergeable_ids = [
                    lid for lid in group_ids
                    if stage_by_lead.get(lid) not in won_stage_ids
                ]
                if len(mergeable_ids) < 2:
                    continue
                # Ordenar: más nuevo primero (winner)
                mergeable_ids.sort(key=lambda lid: create_date_by_id[lid], reverse=True)
                resolved.append((mergeable_ids[0], mergeable_ids[1:]))

            # Fusionar datos ORM (description, fecha_reactivacion)
            for winner_id, loser_ids in resolved:
                winner = self.with_context(active_test=False).browse(winner_id)
                losers = self.with_context(active_test=False).browse(loser_ids)
                _logger.info(
                    "[irg_crm_lead_dedup] Fusionando %d leads en #%d (%s)",
                    len(loser_ids), winner.id, winner.name
                )
                self._merge_losers_into_winner(winner, losers)
                total_merged += len(loser_ids)

            # Mensajes y actividades via SQL usando el mismo mapa winner→losers
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

            # Archivar todos los losers del chunk en un solo UPDATE
            all_loser_ids = [lid for _, loser_ids in resolved for lid in loser_ids]
            if all_loser_ids:
                self.env.cr.execute(
                    "UPDATE crm_lead SET active = FALSE WHERE id = ANY(%s)",
                    (all_loser_ids,)
                )

            self.env.cr.commit()
            _logger.info(
                "[irg_crm_lead_dedup] Chunk %d/%d completado (%d fusionados)",
                chunk_idx + 1, total_chunks, len(all_loser_ids)
            )

        # Guardar watermark DESPUÉS de completar exitosamente
        config.set_param(PARAM_LAST_RUN, run_start.isoformat())
        _logger.info(
            "[irg_crm_lead_dedup] Completado. Total leads fusionados: %d", total_merged
        )

    def _merge_losers_into_winner(self, winner, losers):
        """
        Acumula todos los datos de los losers y hace un único write al winner.
        """
        utm_m2o = {'campaign_id': 'Campaña', 'source_id': 'Fuente', 'medium_id': 'Medio'}
        description_parts = []
        if winner.description:
            description_parts.append(winner.description)

        new_fecha_reactivacion = getattr(winner, 'fecha_reactivacion', None)

        for loser in losers:
            # UTMs del loser → notas internas del winner
            utm_lines = [
                '%s: %s' % (label, loser[field].name)
                for field, label in utm_m2o.items() if loser[field]
            ]
            if loser.referred:
                utm_lines.append('Referido: %s' % loser.referred)
            if utm_lines:
                description_parts.append(
                    '---\n[UTMs lead fusionado #%d - %s]\n%s' % (
                        loser.id, loser.name, '\n'.join(utm_lines)
                    )
                )

            # Notas internas del loser
            if loser.description:
                description_parts.append(
                    '---\n[Notas fusionadas desde lead #%d - %s]\n%s' % (
                        loser.id, loser.name, loser.description
                    )
                )

            # fecha_reactivacion: conservar la más reciente
            loser_fecha = getattr(loser, 'fecha_reactivacion', None)
            if loser_fecha and (not new_fecha_reactivacion or loser_fecha > new_fecha_reactivacion):
                new_fecha_reactivacion = loser_fecha

        # Un único write con todos los cambios acumulados
        vals = {}
        new_description = '\n\n'.join(description_parts) or False
        if new_description != (winner.description or False):
            vals['description'] = new_description

        current_fecha = getattr(winner, 'fecha_reactivacion', None)
        if hasattr(winner, 'fecha_reactivacion') and new_fecha_reactivacion != current_fecha:
            vals['fecha_reactivacion'] = new_fecha_reactivacion

        if vals:
            winner.sudo().write(vals)


_logger = logging.getLogger(__name__)

CHUNK_SIZE = 50
PARAM_LAST_RUN = 'irg_crm_lead_dedup.last_run'


class CrmLeadDedup(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def action_dedup_leads(self):
        """
        Cron diario: detecta leads/oportunidades duplicados por email o teléfono,
        fusiona sus datos en el más nuevo y archiva los más antiguos.
        Los leads ganados nunca se tocan.

        Modo incremental: solo procesa grupos donde al menos un lead fue creado
        después del último run. El primer run procesa toda la base de datos.
        """
        _logger.info("[irg_crm_lead_dedup] Iniciando deduplicación de leads")

        # Leer y actualizar el watermark ANTES de procesar, así los leads que
        # entren durante la ejecución quedan incluidos en el siguiente run
        config = self.env['ir.config_parameter'].sudo()
        last_run_str = config.get_param(PARAM_LAST_RUN)
        last_run = datetime.fromisoformat(last_run_str) if last_run_str else None
        run_start = datetime.utcnow()
        config.set_param(PARAM_LAST_RUN, run_start.isoformat())

        if last_run:
            _logger.info("[irg_crm_lead_dedup] Modo incremental desde %s", last_run)
        else:
            _logger.info("[irg_crm_lead_dedup] Primera ejecución: procesando toda la base de datos")

        # --- FASE 1: cargar datos mínimos via SQL directo (más rápido que search_read) ---
        self.env.cr.execute("""
            SELECT id, email_from, phone, mobile, create_date, stage_id
            FROM crm_lead
            ORDER BY create_date ASC
        """)
        leads_data = self.env.cr.dictfetchall()
        _logger.info("[irg_crm_lead_dedup] Leads cargados: %d", len(leads_data))

        # Resolver stages ganados (una sola query)
        self.env.cr.execute("SELECT id FROM crm_stage WHERE is_won = TRUE")
        won_stage_ids = {row['id'] for row in self.env.cr.dictfetchall()}

        # Índices auxiliares
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

        # Solo grupos con duplicados
        duplicate_groups = [ids for ids in gid_to_ids.values() if len(ids) > 1]

        # Modo incremental: descartar grupos donde ningún miembro sea nuevo
        if last_run:
            duplicate_groups = [
                ids for ids in duplicate_groups
                if any(
                    create_date_by_id[lid] and create_date_by_id[lid] > last_run
                    for lid in ids
                )
            ]

        _logger.info(
            "[irg_crm_lead_dedup] Grupos a procesar: %d", len(duplicate_groups)
        )

        # --- FASE 3: fusionar en chunks ---
        total_merged = 0
        total_chunks = max(1, (len(duplicate_groups) + CHUNK_SIZE - 1) // CHUNK_SIZE)

        for chunk_idx, chunk_start in enumerate(range(0, len(duplicate_groups), CHUNK_SIZE)):
            chunk = duplicate_groups[chunk_start:chunk_start + CHUNK_SIZE]
            chunk_loser_ids = []

            for group_ids in chunk:
                mergeable_ids = [
                    lid for lid in group_ids
                    if stage_by_lead.get(lid) not in won_stage_ids
                ]
                if len(mergeable_ids) < 2:
                    continue

                mergeable_ids.sort(key=lambda lid: create_date_by_id[lid], reverse=True)
                winner_id = mergeable_ids[0]
                loser_ids = mergeable_ids[1:]

                winner = self.with_context(active_test=False).browse(winner_id)
                losers = self.with_context(active_test=False).browse(loser_ids)

                _logger.info(
                    "[irg_crm_lead_dedup] Fusionando %d leads en #%d (%s)",
                    len(loser_ids), winner.id, winner.name
                )

                # Acumular todos los cambios del winner en una sola pasada
                self._merge_losers_into_winner(winner, losers)
                total_merged += len(loser_ids)
                chunk_loser_ids.extend(loser_ids)

            # Archivar todos los losers del chunk en un solo UPDATE SQL
            if chunk_loser_ids:
                self.env.cr.execute(
                    "UPDATE crm_lead SET active = FALSE WHERE id = ANY(%s)",
                    (chunk_loser_ids,)
                )
                # Mover mensajes y actividades de todos los losers del chunk de una vez
                for group_ids in chunk:
                    mergeable_ids = [
                        lid for lid in group_ids
                        if stage_by_lead.get(lid) not in won_stage_ids
                    ]
                    if len(mergeable_ids) < 2:
                        continue
                    winner_id = mergeable_ids[0]
                    loser_ids = mergeable_ids[1:]
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

            self.env.cr.commit()
            _logger.info(
                "[irg_crm_lead_dedup] Chunk %d/%d completado (%d fusionados)",
                chunk_idx + 1, total_chunks, len(chunk_loser_ids)
            )

        _logger.info(
            "[irg_crm_lead_dedup] Completado. Total leads fusionados: %d", total_merged
        )

    def _merge_losers_into_winner(self, winner, losers):
        """
        Acumula todos los datos de todos los losers y hace un único write al winner.
        Evita múltiples writes ORM al mismo registro.
        """
        utm_m2o = {'campaign_id': 'Campaña', 'source_id': 'Fuente', 'medium_id': 'Medio'}
        description_parts = [winner.description or '']
        new_fecha_reactivacion = winner.fecha_reactivacion if hasattr(winner, 'fecha_reactivacion') else None

        for loser in losers:
            # UTMs → notas internas
            utm_lines = ['%s: %s' % (label, loser[field].name)
                         for field, label in utm_m2o.items() if loser[field]]
            if loser.referred:
                utm_lines.append('Referido: %s' % loser.referred)
            if utm_lines:
                description_parts.append(
                    '\n---\n[UTMs lead fusionado #%d - %s]\n%s' % (
                        loser.id, loser.name, '\n'.join(utm_lines)
                    )
                )

            # Notas internas
            if loser.description:
                description_parts.append(
                    '\n---\n[Notas fusionadas desde lead #%d - %s]\n%s' % (
                        loser.id, loser.name, loser.description
                    )
                )

            # fecha_reactivacion: la más reciente
            if hasattr(winner, 'fecha_reactivacion') and loser.fecha_reactivacion:
                if not new_fecha_reactivacion or loser.fecha_reactivacion > new_fecha_reactivacion:
                    new_fecha_reactivacion = loser.fecha_reactivacion

        # Un único write al winner con todos los cambios acumulados
        vals = {'description': '\n'.join(description_parts) if any(description_parts) else winner.description}
        if hasattr(winner, 'fecha_reactivacion') and new_fecha_reactivacion != winner.fecha_reactivacion:
            vals['fecha_reactivacion'] = new_fecha_reactivacion
        if vals:
            winner.sudo().write(vals)


    @api.model
    def action_dedup_leads(self):
        """
        Cron diario: detecta leads/oportunidades duplicados por email o teléfono,
        fusiona sus datos en el más nuevo y archiva los más antiguos.
        Los leads ganados nunca se tocan.
        """
        _logger.info("[irg_crm_lead_dedup] Iniciando deduplicación de leads")

        # --- FASE 1: leer solo los campos necesarios para detectar duplicados ---
        # search_read es mucho más ligero que browse() ya que no carga todos los campos ORM
        leads_data = self.with_context(active_test=False).search_read(
            [],
            fields=['id', 'email_from', 'phone', 'mobile', 'create_date', 'stage_id'],
            order='create_date asc',
        )

        # Resolver qué stage_ids tienen is_won=True (una sola query, fuera del bucle)
        all_stage_ids = {l['stage_id'][0] for l in leads_data if l['stage_id']}
        won_stage_ids = set()
        if all_stage_ids:
            won_stage_ids = set(
                self.env['crm.stage'].browse(list(all_stage_ids))
                .filtered('is_won').ids
            )

        # Índices auxiliares por id (evitan releer datos durante el procesamiento)
        stage_by_lead = {l['id']: (l['stage_id'][0] if l['stage_id'] else False) for l in leads_data}
        create_date_by_id = {l['id']: l['create_date'] for l in leads_data}

        # --- FASE 2: agrupar por clave de dedup ---
        # Algoritmo Union-Find simplificado: cuando un lead "puente" conecta dos grupos
        # distintos (mismo email que A, mismo teléfono que B), los fusiona en uno solo.
        key_to_gid = {}    # (tipo, valor) -> id de grupo
        gid_to_ids = {}    # id de grupo -> lista de lead ids
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
            phone_raw = lead['phone'] or lead['mobile'] or ''
            phone = re.sub(r'\D', '', phone_raw)  # solo dígitos
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
                # Varios grupos distintos conectados por este lead: fusionarlos
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
        _logger.info("[irg_crm_lead_dedup] Grupos duplicados encontrados: %d", len(duplicate_groups))

        # --- FASE 3: fusionar en chunks para no acumular una transacción gigante ---
        total_merged = 0
        total_chunks = (len(duplicate_groups) + CHUNK_SIZE - 1) // CHUNK_SIZE

        for chunk_idx, chunk_start in enumerate(range(0, len(duplicate_groups), CHUNK_SIZE)):
            chunk = duplicate_groups[chunk_start:chunk_start + CHUNK_SIZE]

            for group_ids in chunk:
                # Excluir leads ganados del grupo
                mergeable_ids = [
                    lid for lid in group_ids
                    if stage_by_lead.get(lid) not in won_stage_ids
                ]
                if len(mergeable_ids) < 2:
                    continue

                # El más nuevo (mayor create_date) es el winner
                mergeable_ids.sort(key=lambda lid: create_date_by_id[lid], reverse=True)
                winner_id = mergeable_ids[0]
                loser_ids = mergeable_ids[1:]

                winner = self.with_context(active_test=False).browse(winner_id)
                losers = self.with_context(active_test=False).browse(loser_ids)
                _logger.info(
                    "[irg_crm_lead_dedup] Fusionando %d leads en #%d (%s)",
                    len(loser_ids), winner.id, winner.name
                )

                for loser in losers:
                    self._merge_into_winner(winner, loser)
                    total_merged += 1

            # Commit tras cada chunk: libera locks y no bloquea el sistema
            self.env.cr.commit()
            _logger.info(
                "[irg_crm_lead_dedup] Chunk %d/%d completado",
                chunk_idx + 1, total_chunks
            )

        _logger.info(
            "[irg_crm_lead_dedup] Deduplicación completada. Leads fusionados: %d",
            total_merged
        )

    def _merge_into_winner(self, winner, loser):
        """Fusiona los datos de 'loser' en 'winner' y archiva 'loser'."""

        # --- UTMs del loser → notas internas del winner (los del winner no se tocan) ---
        utm_m2o = {'campaign_id': 'Campaña', 'source_id': 'Fuente', 'medium_id': 'Medio'}
        utm_lines = ['%s: %s' % (label, loser[field].name)
                     for field, label in utm_m2o.items() if loser[field]]
        if loser.referred:
            utm_lines.append('Referido: %s' % loser.referred)
        if utm_lines:
            utm_block = '\n\n---\n[UTMs lead fusionado #%d - %s]\n' % (loser.id, loser.name)
            utm_block += '\n'.join(utm_lines)
            winner.description = (winner.description or '') + utm_block

        # --- Notas internas del loser → concatenar al winner ---
        if loser.description:
            notes_block = '\n\n---\n[Notas fusionadas desde lead #%d - %s]\n' % (loser.id, loser.name)
            notes_block += loser.description
            winner.description = (winner.description or '') + notes_block

        # --- fecha_reactivacion: conservar la más reciente ---
        if hasattr(winner, 'fecha_reactivacion'):
            loser_fecha = loser.fecha_reactivacion
            winner_fecha = winner.fecha_reactivacion
            if loser_fecha and (not winner_fecha or loser_fecha > winner_fecha):
                winner.fecha_reactivacion = loser_fecha

        # --- Mensajes y actividades: SQL directo para no disparar eventos ORM masivos ---
        self.env.cr.execute(
            "UPDATE mail_message SET res_id = %s WHERE model = 'crm.lead' AND res_id = %s",
            (winner.id, loser.id)
        )
        self.env.cr.execute(
            "UPDATE mail_activity SET res_id = %s WHERE res_model = 'crm.lead' AND res_id = %s",
            (winner.id, loser.id)
        )

        # --- Archivar el loser ---
        loser.sudo().write({'active': False})

        _logger.info(
            "[irg_crm_lead_dedup] Lead #%d (%s) fusionado en #%d y archivado",
            loser.id, loser.name, winner.id
        )

        """
        Cron diario: detecta leads duplicados por email o teléfono,
        fusiona sus UTMs, notas internas y mensajes en el más nuevo,
        y elimina el/los más antiguo/s.
        """
        _logger.info("[irg_crm_lead_dedup] Iniciando proceso de deduplicación de leads")

        # Obtener todos los leads y oportunidades, incluyendo archivados y perdidos
        # Solo se excluirán los ganados más adelante, en el filtro por grupo
        all_leads = self.with_context(active_test=False).search([], order='create_date asc')

        # Agrupar por clave de dedup: email normalizado o teléfono normalizado.
        # Usamos un dict key->gid y otro gid->leads para poder fusionar grupos
        # cuando un lead "puente" conecta dos grupos distintos.
        key_to_gid = {}   # (tipo, valor) -> id de grupo
        gid_to_leads = {} # id de grupo -> lista de leads
        next_gid = [0]

        def _new_gid():
            gid = next_gid[0]
            next_gid[0] += 1
            return gid

        for lead in all_leads:
            keys = set()
            email_key = email_normalize(lead.email_from)
            if email_key:
                keys.add(('email', email_key))
            phone = (lead.phone or lead.mobile or '').strip().replace(' ', '').replace('-', '')
            if phone:
                keys.add(('phone', phone))

            if not keys:
                continue

            # Buscar todos los grupos existentes a los que conecta este lead
            found_gids = {key_to_gid[k] for k in keys if k in key_to_gid}

            if not found_gids:
                # Ningún grupo existente: crear uno nuevo
                gid = _new_gid()
                gid_to_leads[gid] = [lead]
            elif len(found_gids) == 1:
                # Un solo grupo: añadir el lead
                gid = next(iter(found_gids))
                gid_to_leads[gid].append(lead)
            else:
                # Varios grupos distintos: fusionarlos todos en el primero
                gids = list(found_gids)
                gid = gids[0]
                for other in gids[1:]:
                    gid_to_leads[gid].extend(gid_to_leads.pop(other))
                    for k, g in list(key_to_gid.items()):
                        if g == other:
                            key_to_gid[k] = gid
                gid_to_leads[gid].append(lead)

            for key in keys:
                key_to_gid[key] = gid

        duplicate_groups = [leads for leads in gid_to_leads.values() if len(leads) > 1]

        _logger.info("[irg_crm_lead_dedup] Grupos duplicados encontrados: %d", len(duplicate_groups))

        for group in duplicate_groups:
            # Excluir leads ganados: no participan en la fusión
            mergeable = [l for l in group if not l.stage_id.is_won]

            if len(mergeable) < 2:
                _logger.info(
                    "[irg_crm_lead_dedup] Grupo omitido (menos de 2 leads fusionables, ganados excluidos)"
                )
                continue

            # Ordenar: el más nuevo (mayor create_date) es el que se conserva
            group_sorted = sorted(mergeable, key=lambda l: l.create_date, reverse=True)
            winner = group_sorted[0]
            losers = group_sorted[1:]

            _logger.info(
                "[irg_crm_lead_dedup] Fusionando %d leads en lead #%d (%s)",
                len(losers), winner.id, winner.name
            )

            for loser in losers:
                self._merge_into_winner(winner, loser)

        _logger.info("[irg_crm_lead_dedup] Deduplicación completada")

    def _merge_into_winner(self, winner, loser):
        """Fusiona los datos de 'loser' en 'winner' y archiva 'loser'."""

        # --- UTMs del loser: pasar a notas internas del winner (no sobreescribir) ---
        utm_m2o = {'campaign_id': 'Campaña', 'source_id': 'Fuente', 'medium_id': 'Medio'}
        utm_lines = []
        for field, label in utm_m2o.items():
            val = loser[field]
            if val:
                utm_lines.append('%s: %s' % (label, val.name))
        if loser.referred:
            utm_lines.append('Referido: %s' % loser.referred)
        if utm_lines:
            utm_block = '\n\n---\n[UTMs lead fusionado #%d - %s]\n' % (loser.id, loser.name)
            utm_block += '\n'.join(utm_lines)
            winner.description = (winner.description or '') + utm_block

        # --- Notas internas del loser: concatenar al winner ---
        if loser.description:
            notes_block = '\n\n---\n[Notas fusionadas desde lead #%d - %s]\n' % (loser.id, loser.name)
            notes_block += loser.description
            winner.description = (winner.description or '') + notes_block

        # --- fecha_reactivacion: conservar la más reciente ---
        if hasattr(winner, 'fecha_reactivacion'):
            loser_fecha = loser.fecha_reactivacion
            winner_fecha = winner.fecha_reactivacion
            if loser_fecha and (not winner_fecha or loser_fecha > winner_fecha):
                winner.fecha_reactivacion = loser_fecha

        # --- Mensajes del chatter: reasignar al winner via SQL (sin disparar eventos ORM) ---
        self.env.cr.execute(
            "UPDATE mail_message SET res_id = %s WHERE model = 'crm.lead' AND res_id = %s",
            (winner.id, loser.id)
        )

        # --- Actividades: reasignar via SQL ---
        self.env.cr.execute(
            "UPDATE mail_activity SET res_id = %s WHERE res_model = 'crm.lead' AND res_id = %s",
            (winner.id, loser.id)
        )

        # --- Archivar el loser ---
        loser.sudo().write({'active': False})

        _logger.info(
            "[irg_crm_lead_dedup] Lead #%d (%s) fusionado en #%d y archivado",
            loser.id, loser.name, winner.id
        )
