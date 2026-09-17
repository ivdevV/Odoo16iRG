# -*- coding: utf-8 -*-
"""Build the campus activity audit workbook."""
from __future__ import annotations

import io
from datetime import datetime

try:
    import xlsxwriter
except ImportError:  # pragma: no cover
    xlsxwriter = None

SHEET_ORDER = [
    "Resumen alumnos",
    "Progreso por asignatura",
    "Actividades",
    "Evaluaciones",
    "Libreta alumnos",
    "Libreta asignaturas",
    "Libreta examenes",
    "No encontrados",
    "Metodologia",
]


def build_xlsx(sheets: dict) -> bytes:
    """sheets: name -> (headers, rows). Extra names keep insertion order after SHEET_ORDER."""
    if xlsxwriter is None:
        raise RuntimeError("xlsxwriter is not installed")
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True, "remove_timezone": True})
    header_fmt = workbook.add_format(
        {"bold": True, "bg_color": "#1F4E79", "font_color": "white", "border": 1}
    )
    names = [name for name in SHEET_ORDER if name in sheets]
    names.extend(name for name in sheets if name not in names)
    for title in names:
        headers, rows = sheets[title]
        worksheet = workbook.add_worksheet(title[:31])
        last_col = max(len(headers) - 1, 0)
        last_row = max(len(rows), 1)
        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, last_row, last_col)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_fmt)
            worksheet.set_column(col, col, min(max(len(str(header)) + 2, 14), 42))
        for row_index, row in enumerate(rows, start=1):
            for col_index, value in enumerate(row):
                if value is None:
                    worksheet.write_blank(row_index, col_index, None)
                else:
                    worksheet.write(row_index, col_index, value)
    workbook.close()
    return output.getvalue()


def methodology_rows(
    generated_at=None,
    listado_name="",
    listado_count=0,
    matched_count=0,
    unmatched_count=0,
):
    stamp = generated_at or datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    return [
        ["Campo", "Valor"],
        ["Generado", stamp],
        ["Origen", "Listado Excel de alumnos"],
        ["Archivo de listado", listado_name or ""],
        ["Filas del listado", listado_count],
        ["Matrículas encontradas", matched_count],
        ["No encontrados", unmatched_count],
        ["Consulta", "Solo lectura sobre matrícula, campus y libreta"],
        [
            "matricula_finalizada",
            "op.student.course.state = finished",
        ],
        [
            "libreta_100",
            "completion_porc >= 100 (obligatorias con nota final >= 8)",
        ],
        [
            "campus_completado",
            "Todos los contenidos publicados de la matrícula están completados",
        ],
        [
            "Fuera de alcance",
            "Foros, asistencia, tareas OpenEduCat, Moodle, auditlog OCA",
        ],
    ]
