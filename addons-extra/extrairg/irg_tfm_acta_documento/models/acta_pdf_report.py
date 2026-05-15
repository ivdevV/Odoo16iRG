# -*- coding: utf-8 -*-
import io
import os
from odoo import models, api, modules
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader


class ActaPDFReport(models.AbstractModel):
    _name = 'report.irg_tfm_acta_documento.acta_pdf'
    _description = 'Acta TFM/TFG PDF Report'

    def _get_image_path(self, image_name):
        return modules.get_module_resource(
            'irg_generacion_diplomas',
            'static/src/img',
            image_name,
        )

    def _register_fonts(self):
        font_regular = 'Helvetica'
        font_bold = 'Helvetica-Bold'
        try:
            font_path = modules.get_module_resource(
                'irg_generacion_diplomas',
                'static/src/fonts',
                'Inter-Regular.ttf',
            )
            if font_path and os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Inter', font_path))
                font_regular = 'Inter'

            font_bold_path = modules.get_module_resource(
                'irg_generacion_diplomas',
                'static/src/fonts',
                'Inter-Bold.ttf',
            )
            if font_bold_path and os.path.exists(font_bold_path):
                pdfmetrics.registerFont(TTFont('Inter-Bold', font_bold_path))
                font_bold = 'Inter-Bold'
        except Exception:
            pass
        return font_regular, font_bold

    def _draw_centered(self, c, text, y, font_name, font_size):
        c.setFont(font_name, font_size)
        width = c._pagesize[0]
        text_width = c.stringWidth(text, font_name, font_size)
        c.drawString((width - text_width) / 2, y, text)

    def _draw_wrapped(self, c, text, x, y, width, font_name, font_size, leading=None):
        if leading is None:
            leading = font_size * 1.2
        c.setFont(font_name, font_size)
        from reportlab.lib.utils import simpleSplit

        lines = simpleSplit(text or '', font_name, font_size, width)
        current_y = y
        for line in lines:
            c.drawString(x, current_y, line)
            current_y -= leading
        return current_y

    def _draw_label_value(self, c, label, value, x, y, font_name, font_size, line_width=0):
        c.setFont(font_name, font_size)
        c.drawString(x, y, label)
        c.setFont(font_name, font_size)
        c.drawString(x + 70 * mm, y, value or '')
        if line_width:
            c.line(x + 70 * mm, y - 2, x + 70 * mm + line_width, y - 2)

    def generate_acta_pdf(self, data, acta_type='tfm'):
        font_regular, font_bold = self._register_fonts()
        page_width, page_height = A4
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        logo_path = self._get_image_path('logo_irg.png')
        if logo_path and os.path.exists(logo_path):
            try:
                logo = ImageReader(logo_path)
                logo_width = 70 * mm
                logo_height = 20 * mm
                c.drawImage(
                    logo,
                    (page_width - logo_width) / 2,
                    page_height - 35 * mm,
                    width=logo_width,
                    height=logo_height,
                    preserveAspectRatio=True,
                    mask='auto',
                )
            except Exception:
                pass

        y = page_height - 60 * mm
        self._draw_centered(c, 'ACTA DE EVALUACIÓN', y, font_bold, 18)
        y -= 10 * mm
        subtype = 'TFM' if acta_type == 'tfm' else 'TFG'
        self._draw_centered(c, f'TRABAJO FINAL DE {subtype}', y, font_regular, 12)

        y -= 18 * mm
        c.setFont(font_bold, 11)
        c.drawString(25 * mm, y, 'Alumno:')
        c.setFont(font_regular, 11)
        c.drawString(60 * mm, y, f"{data.get('student_name', '')} {data.get('student_surnames', '')}")

        y -= 8 * mm
        self._draw_label_value(
            c,
            'DNI:',
            data.get('student_dni', ''),
            25 * mm,
            y,
            font_regular,
            11,
        )

        y -= 12 * mm
        self._draw_label_value(
            c,
            'Curso Académico:',
            data.get('academic_year', ''),
            25 * mm,
            y,
            font_regular,
            11,
        )

        y -= 12 * mm
        self._draw_label_value(
            c,
            'Titulación:',
            data.get('degree_name', ''),
            25 * mm,
            y,
            font_regular,
            11,
            line_width=85 * mm,
        )

        y -= 15 * mm
        c.setFont(font_bold, 11)
        c.drawString(25 * mm, y, 'Título del Trabajo:')
        y -= 8 * mm
        y = self._draw_wrapped(
            c,
            data.get('tfm_title', ''),
            25 * mm,
            y,
            page_width - 50 * mm,
            font_regular,
            11,
            leading=13,
        )

        y -= 10 * mm
        c.setFont(font_bold, 11)
        c.drawString(25 * mm, y, 'Tribunal:')
        y -= 8 * mm
        c.setFont(font_regular, 11)
        c.drawString(30 * mm, y, f"Presidente: {data.get('president_name', '')} {data.get('president_surnames', '')}")
        y -= 8 * mm
        c.drawString(30 * mm, y, f"Secretario/a: {data.get('secretary_name', '')} {data.get('secretary_surnames', '')}")
        y -= 12 * mm
        c.drawString(30 * mm, y, f"Director/a: {data.get('director_name', '')} {data.get('director_surnames', '')}")

        c.showPage()

        y = page_height - 40 * mm
        self._draw_centered(c, 'ACTA EDITABLE', y, font_bold, 16)
        y -= 18 * mm

        c.setFont(font_regular, 11)
        c.drawString(25 * mm, y, 'Fecha de Defensa:')
        c.line(70 * mm, y - 2, page_width - 25 * mm, y - 2)
        y -= 14 * mm

        c.drawString(25 * mm, y, 'Calificación:')
        c.line(70 * mm, y - 2, page_width - 25 * mm, y - 2)
        y -= 18 * mm

        c.drawString(25 * mm, y, 'Observaciones:')
        line_y = y - 4 * mm
        for _ in range(6):
            c.line(25 * mm, line_y, page_width - 25 * mm, line_y)
            line_y -= 8 * mm
        y = line_y - 10 * mm

        c.drawString(25 * mm, y, 'Firma del Secretario/a:')
        c.line(70 * mm, y - 2, page_width - 25 * mm, y - 2)

        c.save()
        buffer.seek(0)
        return buffer.getvalue()
