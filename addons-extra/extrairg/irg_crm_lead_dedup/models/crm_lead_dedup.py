import logging
from odoo import models, api
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)


class CrmLeadDedup(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def action_dedup_leads(self):
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
