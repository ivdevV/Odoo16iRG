# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import _

ACTIVITY_LIMIT = 500
TYPE_LABELS = {"campus": "Campus", "evaluation": "Evaluación"}
CSV_HEADERS = [
    "Fecha", "Tipo", "Curso / canal", "Elemento", "Detalle", "Resultado", "Lote",
]


def _slide_is_published(slide):
    """Published, non-section slide, evaluated on the already-loaded record.

    Mirrors the domain used by the batch report (active, not category,
    published) without issuing one query per row.
    """
    if not slide or not slide.channel_id:
        return False
    fields_map = slide._fields
    if "active" in fields_map and not slide.active:
        return False
    if "is_category" in fields_map and slide.is_category:
        return False
    if "is_published" in fields_map and not slide.is_published:
        return False
    return True


def _activity_sort_key(row):
    return (row.get("event_datetime") or datetime.min, row.get("element_name") or "")


def _batch_code_for_channel(env, partner, channel, cache=None):
    key = (partner.id, channel.id)
    if cache is not None and key in cache:
        return cache[key]
    PartnerChannel = env["slide.channel.partner"]
    domain = [
        ("partner_id", "=", partner.id),
        ("channel_id", "=", channel.id),
    ]
    if "active" in PartnerChannel._fields:
        domain.append(("active", "=", True))
    membership = PartnerChannel.search(domain, limit=1)
    code = ""
    if membership and "batch_id" in membership._fields and membership.batch_id:
        code = membership.batch_id.code or ""
    if cache is not None:
        cache[key] = code
    return code


def _campus_rows(env, partner, cache=None):
    if not partner:
        return []
    SlidePartner = env["slide.slide.partner"]
    records = SlidePartner.search([("partner_id", "=", partner.id)])
    rows = []
    for sp in records:
        slide = sp.slide_id
        if not _slide_is_published(slide):
            continue
        channel = slide.channel_id
        completed = bool(sp.completed)
        detail = _("Completada") if completed else _("En curso")
        result = _("Completada") if completed else ""
        event_dt = sp.write_date or sp.create_date
        rows.append({
            "event_datetime": event_dt,
            "event_type": "campus",
            "channel_name": channel.name if channel else "",
            "element_name": slide.name or "",
            "detail": detail,
            "result": result,
            "batch_code": (
                _batch_code_for_channel(env, partner, channel, cache)
                if channel else ""
            ),
        })
    return rows


def _evaluation_rows(env, partner, cache=None):
    if not partner:
        return []
    Input = env["survey.user_input"]
    if "slide_id" not in Input._fields:
        return []
    attempts = Input.search([
        ("partner_id", "=", partner.id),
        ("slide_id", "!=", False),
    ])
    state_labels = {}
    if "state" in Input._fields:
        state_labels = dict(Input._fields["state"]._description_selection(env))
    rows = []
    for attempt in attempts:
        slide = attempt.slide_id
        channel = slide.channel_id if slide else False
        if "end_datetime" in attempt._fields and attempt.end_datetime:
            event_dt = attempt.end_datetime
        else:
            event_dt = attempt.create_date
        scoring = ""
        scored = (
            "scoring_percentage" in attempt._fields
            and attempt.state == "done"
            and attempt.scoring_percentage is not None
            and (
                "scoring_type" not in attempt._fields
                or attempt.scoring_type != "no_scoring"
            )
        )
        if scored:
            scoring = "%.2f%%" % attempt.scoring_percentage
        if "scoring_success" in attempt._fields and attempt.scoring_success:
            scoring = (scoring + " " if scoring else "") + _("Éxito")
        rows.append({
            "event_datetime": event_dt,
            "event_type": "evaluation",
            "channel_name": channel.name if channel else "",
            "element_name": slide.name if slide else (attempt.survey_id.title or ""),
            "detail": state_labels.get(attempt.state, attempt.state or ""),
            "result": scoring,
            "batch_code": (
                _batch_code_for_channel(env, partner, channel, cache)
                if channel else ""
            ),
        })
    return rows


def assemble_student_activity_rows(env, student, limit=ACTIVITY_LIMIT):
    partner = student.partner_id
    if not partner:
        return []
    cache = {}
    rows = (
        _campus_rows(env, partner, cache)
        + _evaluation_rows(env, partner, cache)
    )
    rows.sort(key=_activity_sort_key, reverse=True)
    return rows[:limit]
