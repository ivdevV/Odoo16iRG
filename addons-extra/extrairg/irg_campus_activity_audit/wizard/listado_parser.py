# -*- coding: utf-8 -*-
"""Parse a student listado XLSX (first sheet) into row dicts."""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

_EMAIL_HEADERS = {
    "email",
    "e-mail",
    "correo",
    "correo electronico",
    "correo electrónico",
    "mail",
}
_COURSE_HEADERS = {
    "curso",
    "course",
    "codigo",
    "código",
    "codigo_curso",
    "código_curso",
    "course_code",
}
_NAME_HEADERS = {
    "nombre",
    "name",
    "alumno",
    "estudiante",
    "nombre completo",
}
_COUNTRY_HEADERS = {
    "pais",
    "país",
    "country",
}
_MODALITY_HEADERS = {
    "modalidad",
    "modality",
}

_COURSE_CODE_RE = re.compile(r"\(([^()]+)\)\s*$")


def _col_row(ref: str) -> tuple[int, int]:
    match = re.match(r"([A-Z]+)(\d+)", ref or "")
    if not match:
        return 0, 0
    col = 0
    for ch in match.group(1):
        col = col * 26 + (ord(ch) - 64)
    return col, int(match.group(2))


def _cell_text(cell, shared_strings: list[str]) -> str:
    value_node = cell.find("m:v", NS)
    if value_node is None or value_node.text is None:
        is_nodes = cell.findall(".//m:t", NS)
        if is_nodes:
            return "".join(node.text or "" for node in is_nodes).strip()
        return ""
    if cell.attrib.get("t") == "s":
        try:
            return (shared_strings[int(value_node.text)] or "").strip()
        except (ValueError, IndexError):
            return ""
    return (value_node.text or "").strip()


def _header_key(label: str) -> str:
    return (label or "").strip().lower()


def extract_course_code(course_label: str) -> str:
    """Return the code in trailing parentheses, or a compact label as-is."""
    text = (course_label or "").strip()
    if not text:
        return ""
    match = _COURSE_CODE_RE.search(text)
    if match:
        return match.group(1).strip()
    if " " not in text:
        return text
    return ""


def parse_listado_xlsx(data: bytes) -> list[dict]:
    """Return rows with email, course, name, country and modality."""
    if not data:
        return []
    with zipfile.ZipFile(BytesIO(data)) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                shared_strings.append(
                    "".join(node.text or "" for node in si.findall(".//m:t", NS))
                )
        sheet_name = next(
            (
                name
                for name in archive.namelist()
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
            ),
            None,
        )
        if not sheet_name:
            return []
        sheet = ET.fromstring(archive.read(sheet_name))

    rows: dict[int, dict[int, str]] = {}
    for cell in sheet.findall(".//m:c", NS):
        ref = cell.attrib.get("r")
        if not ref:
            continue
        col, row = _col_row(ref)
        if row:
            rows.setdefault(row, {})[col] = _cell_text(cell, shared_strings)

    if not rows:
        return []
    header_row = min(rows)
    headers = rows.get(header_row, {})
    email_col = course_col = name_col = country_col = modality_col = None
    for col, label in headers.items():
        key = _header_key(label)
        if email_col is None and key in _EMAIL_HEADERS:
            email_col = col
        elif course_col is None and key in _COURSE_HEADERS:
            course_col = col
        elif name_col is None and key in _NAME_HEADERS:
            name_col = col
        elif country_col is None and key in _COUNTRY_HEADERS:
            country_col = col
        elif modality_col is None and key in _MODALITY_HEADERS:
            modality_col = col
    if email_col is None:
        email_col = min(headers) if headers else 1

    result = []
    for row_number in sorted(r for r in rows if r > header_row):
        data_row = rows.get(row_number, {})
        email = (data_row.get(email_col) or "").strip()
        if not email:
            continue
        course_label = ""
        if course_col is not None:
            course_label = (data_row.get(course_col) or "").strip()
        result.append(
            {
                "excel_row": row_number,
                "email": email,
                "email_norm": email.lower(),
                "course_label": course_label,
                "course_code": extract_course_code(course_label),
                "name": (data_row.get(name_col) or "").strip() if name_col else "",
                "country": (data_row.get(country_col) or "").strip() if country_col else "",
                "modality": (data_row.get(modality_col) or "").strip() if modality_col else "",
            }
        )
    return result
