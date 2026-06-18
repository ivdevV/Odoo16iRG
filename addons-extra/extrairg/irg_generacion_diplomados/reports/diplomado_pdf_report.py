# -*- coding: utf-8 -*-
from odoo import models, api, modules
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
import io
import os

class DiplomadoReportPDF(models.AbstractModel):
    _name = 'report.irg_generacion_diplomados.diplomado_pdf'
    _description = 'Diplomado PDF Report'

    def _get_image_path(self, image_name):
        return modules.get_module_resource('irg_generacion_diplomados', 'static/src/img', image_name)

    def _generate_qr(self, url):
        import qrcode
        from reportlab.lib.utils import ImageReader
        import io
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return ImageReader(buffer)

    def _format_issue_date(self, date_val):
        if not date_val:
            return ''
        from datetime import date, datetime
        if isinstance(date_val, (date, datetime)):
            day = date_val.day
            month_num = date_val.month
            year = date_val.year
        else:
            date_str = str(date_val).strip()
            try:
                if '/' in date_str:
                    parts = date_str.split('/')
                    day = int(parts[0])
                    month_num = int(parts[1])
                    year = int(parts[2])
                elif '-' in date_str:
                    parts = date_str.split('-')
                    if len(parts[0]) == 4:
                        year = int(parts[0])
                        month_num = int(parts[1])
                        day = int(parts[2])
                    else:
                        day = int(parts[0])
                        month_num = int(parts[1])
                        year = int(parts[2])
                else:
                    return date_str
            except Exception:
                return date_str

        months = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        month_name = months.get(month_num, '')
        return f"{day} de {month_name} de {year}"

    @api.model
    def generate_diplomado_pdf(self, data):
        buffer = io.BytesIO()
        page_size = landscape(A4)
        page_width, page_height = page_size
        c = canvas.Canvas(buffer, pagesize=page_size)

        # ----------------- PAGINA 1: ANVERSO -----------------
        # 1. Fondo (Digital o Fisico)
        if data.get('diploma_type') == 'digital':
            bg_path = self._get_image_path('diploma_background.jpg')
            if bg_path and os.path.exists(bg_path):
                c.drawImage(bg_path, 0, 0, width=page_width, height=page_height)

        # 2. Logo Superior (digital)
        if data.get('diploma_type') == 'digital':
            logo_path = self._get_image_path('logo_irg.png')
            if logo_path and os.path.exists(logo_path):
                logo_w = 90 * mm
                logo_h = 25 * mm
                logo_x = (page_width - logo_w) / 2
                logo_y = page_height - 16 * mm - logo_h
                c.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')

        # Generar y dibujar el código QR a la izquierda en el anverso
        registry = data.get('registry_number', 'DRAFT')
        qr_url = data.get('qr_url')
        if not qr_url:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or 'https://app.institutoraimongaja.com'
            base_url = base_url.rstrip('/')
            qr_url = "{}/verificar/?id={}".format(base_url, registry)
        qr_image = self._generate_qr(qr_url)
        c.drawImage(qr_image, 22 * mm, 18 * mm, width=28 * mm, height=28 * mm)
        
        # Texto de registro debajo del QR
        registry = data.get('registry_number', 'DRAFT')
        reg_text = "Nº Registro: %s" % registry
        c.setFont('Helvetica-Bold', 8)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(22 * mm + (28 * mm) / 2.0, 12 * mm, reg_text)

        # 3. Certifica
        c.setFont('Helvetica-Oblique', 14)
        c.setFillColorRGB(0.447, 0.498, 0.467)  # #727F77
        c.drawCentredString(page_width / 2.0, page_height - 58 * mm, "certifica que")

        # 4. Nombre del Alumno
        c.setFont('Helvetica-Bold', 23)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(page_width / 2.0, page_height - 75 * mm, data.get('student_name', ''))

        # 5. Texto de aprobación (con Paragraph para wrapping automático)
        aprobacion_text = (
            "ha aprobado los estudios correspondientes al programa de contenidos que figura en el dorso, celebrado del "
            "<b>%s</b> al <b>%s</b>, con una duración de <b>%s horas</b>"
        ) % (data.get('start_date', ''), data.get('end_date', ''), data.get('duration_hours', 0))
        
        if data.get('duration_ects'):
            aprobacion_text += " (equivalente a <b>%s ECTS</b>)" % data.get('duration_ects')
        aprobacion_text += ", por lo que se expide el presente diploma:"

        style_aprobacion = ParagraphStyle(
            'Aprobacion',
            fontName='Helvetica',
            fontSize=13,
            leading=17,
            textColor='#6C7A71',
            alignment=1  # Centrado
        )
        p_aprobacion = Paragraph(aprobacion_text, style_aprobacion)
        p_aprobacion.wrapOn(c, 257 * mm, 40 * mm)
        p_aprobacion.drawOn(c, 20 * mm, page_height - 95 * mm)

        # 6. Nombre del Diplomado
        style_title = ParagraphStyle(
            'Title',
            fontName='Helvetica-Bold',
            fontSize=23,
            leading=27,
            textColor='#000000',
            alignment=1
        )
        p_title = Paragraph(data.get('diplomado_name', ''), style_title)
        p_title.wrapOn(c, 265 * mm, 30 * mm)
        p_title.drawOn(c, 16 * mm, page_height - 118 * mm)

        # 7. Frase final
        c.setFont('Helvetica-Oblique', 13)
        c.setFillColorRGB(0.423, 0.478, 0.443)  # #6C7A71
        c.drawCentredString(page_width / 2.0, page_height - 133 * mm, "que acredita haber superado con aprovechamiento las mencionadas enseñanzas.")

        # 8. Barcelona, a ...
        c.setFont('Helvetica', 13)
        c.setFillColorRGB(0.423, 0.478, 0.443)
        formatted_date = self._format_issue_date(data.get('issue_date', ''))
        c.drawCentredString(page_width / 2.0, 58 * mm, "Barcelona, a %s" % formatted_date)

        # 9. Firmas e Imágenes
        if data.get('diploma_type') == 'digital':
            # Firma Raimon Gaja
            sig_left_path = self._get_image_path('firma_izquierda.jpg')
            if sig_left_path and os.path.exists(sig_left_path):
                c.drawImage(sig_left_path, 72 * mm, 27 * mm, width=48 * mm, height=18 * mm, preserveAspectRatio=True, mask='auto')
            
            # Firma Fermín Carrillo
            sig_right_path = self._get_image_path('firma_derecha.jpg')
            if sig_right_path and os.path.exists(sig_right_path):
                c.drawImage(sig_right_path, 185 * mm, 27 * mm, width=52 * mm, height=18 * mm, preserveAspectRatio=True, mask='auto')

        # Textos de firmas
        style_sig = ParagraphStyle(
            'Signature',
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=13,
            textColor='#000000',
            alignment=1
        )
        p_sig_left = Paragraph("<b>Raimon Gaja Jaumeandreu</b><br/><font color='#666666' size='9.5'>Director General iRG</font>", style_sig)
        p_sig_left.wrapOn(c, 80 * mm, 15 * mm)
        p_sig_left.drawOn(c, 56 * mm, 12 * mm)

        p_sig_right = Paragraph("<b>Fermín Carrillo González</b><br/><font color='#666666' size='9.5'>Director de Relaciones Internacionales</font>", style_sig)
        p_sig_right.wrapOn(c, 80 * mm, 15 * mm)
        p_sig_right.drawOn(c, 171 * mm, 12 * mm)

        # ----------------- PAGINA 2: REVERSO -----------------
        c.showPage()  # Salto de página físico
        
        # 1. Fondo
        if data.get('diploma_type') == 'digital':
            bg_path = self._get_image_path('diploma_background.jpg')
            if bg_path and os.path.exists(bg_path):
                c.drawImage(bg_path, 0, 0, width=page_width, height=page_height)

        # 2. Logo Superior
        if data.get('diploma_type') == 'digital':
            logo_path = self._get_image_path('logo_irg.png')
            if logo_path and os.path.exists(logo_path):
                logo_w = 72 * mm
                logo_h = 20 * mm
                logo_x = (page_width - logo_w) / 2
                logo_y = page_height - 16 * mm - logo_h
                c.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')

        # Estilo de sección del reverso (Presenciales / Online)
        style_back_title = ParagraphStyle(
            'BackTitle',
            fontName='Helvetica-Bold',
            fontSize=14.5,
            leading=18,
            textColor='#033DAA',
            alignment=1
        )
        style_back_text = ParagraphStyle(
            'BackText',
            fontName='Helvetica',
            fontSize=13,
            leading=17,
            textColor='#333333',
            alignment=0  # Izquierda
        )
        style_back_empty = ParagraphStyle(
            'BackTextEmpty',
            fontName='Helvetica-Oblique',
            fontSize=8.2,
            leading=11,
            textColor='#777777',
            alignment=1  # Centrado
        )

        def draw_modules(title, text, start_y_pos):
            # Título de sección
            p_sec_title = Paragraph(title, style_back_title)
            p_sec_title.wrapOn(c, 227 * mm, 6 * mm)
            p_sec_title.drawOn(c, 35 * mm, start_y_pos)
            
            y_curr = start_y_pos - 8 * mm
            
            if text and text.strip():
                # Separar las asignaturas por líneas y añadir un bullet point a cada una
                subjects = [f"&bull; {s.strip()}" for s in text.split('\n') if s.strip()]
                
                # Distribuir en 2 columnas (estilo column-count: 2)
                half = (len(subjects) + 1) // 2
                col1_lines = subjects[:half]
                col2_lines = subjects[half:]
                
                col1_text = "<br/>".join(col1_lines)
                col2_text = "<br/>".join(col2_lines)
                
                # Columna 1 (Izquierda)
                p_col1 = Paragraph(col1_text, style_back_text)
                w1, h1 = p_col1.wrap(108 * mm, 100 * mm)
                p_col1.drawOn(c, 35 * mm, y_curr - h1)
                
                # Columna 2 (Derecha)
                p_col2 = Paragraph(col2_text, style_back_text)
                w2, h2 = p_col2.wrap(108 * mm, 100 * mm)
                p_col2.drawOn(c, 154 * mm, y_curr - h2)
            else:
                p_empty = Paragraph("No se registran módulos en esta modalidad.", style_back_empty)
                p_empty.wrapOn(c, 227 * mm, 8 * mm)
                p_empty.drawOn(c, 35 * mm, y_curr - 6 * mm)

        # Módulos Presenciales
        draw_modules("Módulos Presenciales", data.get('subjects_presencial', ''), page_height - 64 * mm)

        # Módulos Online
        draw_modules("Módulos Online", data.get('subjects_online', ''), page_height - 128 * mm)

        c.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content
