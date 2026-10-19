# -*- coding: utf-8 -*-
import csv
import io

from odoo import fields

from .activity_assemble import CSV_HEADERS, TYPE_LABELS


def _format_local_datetime(record, value):
    if not value:
        return ""
    local = fields.Datetime.context_timestamp(record, value)
    return local.strftime("%Y-%m-%d %H:%M:%S")


def build_activity_csv(rows, record):
    """Build the CSV; ``record`` provides the env/user timezone for dates."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(CSV_HEADERS)
    for row in rows:
        writer.writerow([
            _format_local_datetime(record, row.get("event_datetime")),
            TYPE_LABELS.get(row.get("event_type"), row.get("event_type") or ""),
            row.get("channel_name") or "",
            row.get("element_name") or "",
            row.get("detail") or "",
            row.get("result") or "",
            row.get("batch_code") or "",
        ])
    return output.getvalue().encode("utf-8-sig")
