# -*- coding: utf-8 -*-
from odoo import models, api, modules
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader, simpleSplit
from babel.dates import format_date
import io
import os
import qrcode


class DiplomaReportPDF(models.AbstractModel):
    _name = 'report.irg_generacion_diplomas.diploma_pdf'
    _description = 'Diploma PDF Report'

    def _get_image_path(self, image_name):
        """Get full path to image in module's static folder"""
        return modules.get_module_resource('irg_generacion_diplomas', 'static/src/img', image_name)

    def _register_fonts(self):
        """Register Inter fonts if available, otherwise use Helvetica"""
        font_regular = 'Helvetica'
        font_bold = 'Helvetica-Bold'
        
        try:
            # Check Regular
            font_path = modules.get_module_resource('irg_generacion_diplomas', 'static/src/fonts', 'Inter-Regular.ttf')
            if not (font_path and os.path.exists(font_path)):
                 font_path = modules.get_module_resource('irg_generacion_diplomas', 'static/src/fonts', 'Inter-regular.ttf')
            
            if font_path and os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Inter', font_path))
                font_regular = 'Inter'

            # Check Bold
            font_bold_path = modules.get_module_resource('irg_generacion_diplomas', 'static/src/fonts', 'Inter-Bold.ttf')
            if not (font_bold_path and os.path.exists(font_bold_path)):
                 font_bold_path = modules.get_module_resource('irg_generacion_diplomas', 'static/src/fonts', 'Inter-bold.ttf')
            
            if font_bold_path and os.path.exists(font_bold_path):
                pdfmetrics.registerFont(TTFont('Inter-Bold', font_bold_path))
                font_bold = 'Inter-Bold'
                
        except Exception as e:
            # Log error but fallback to Helvetica
            pass
            
        return font_regular, font_bold

    def _generate_qr(self, url, size=90):
        """Generate QR code image"""
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return ImageReader(buffer)

    def _draw_centered_text(self, c, text, y, font_name, font_size, page_width):
        """Draw text centered on page"""
        c.setFont(font_name, font_size)
        text_width = c.stringWidth(text, font_name, font_size)
        x = (page_width - text_width) / 2
        c.drawString(x, y, text)

    def _draw_text_in_column(self, c, text, x, y, width, font_name, font_size, align='center'):
        """Draw text within a column area"""
        c.setFont(font_name, font_size)
        text_width = c.stringWidth(text, font_name, font_size)
        
        if align == 'center':
            draw_x = x + (width - text_width) / 2
        elif align == 'left':
            draw_x = x
        else:
            draw_x = x + width - text_width
            
        c.drawString(draw_x, y, text)

    def _draw_wrapped_text_in_column(self, c, text, x, y, width, font_name, font_size, align='center', leading=None):
        """Draw text wrapping to new lines if needed. Returns new Y position."""
        if leading is None:
            leading = font_size * 1.2
            
        c.setFont(font_name, font_size)
        lines = simpleSplit(text, font_name, font_size, width)
        
        current_y = y
        for line in lines:
            self._draw_text_in_column(c, line, x, current_y, width, font_name, font_size, align)
            current_y -= leading
            
        return current_y

    @api.model
    def _get_report_values(self, docids, data=None):
        return {'data': data}

    @api.model
    def generate_diploma_pdf(self, data, diploma_type='digital'):
        """Generate the diploma PDF and return bytes"""
        
        # Register fonts
        font_regular, font_bold = self._register_fonts()
        
        # Page setup
        if diploma_type == 'physical':
            page_size = landscape(A3)
        else:
            page_size = landscape(A4)
        
        page_width, page_height = page_size
        
        # Create PDF buffer
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=page_size)
        
        # --- BACKGROUND (only for digital) ---
        if diploma_type == 'digital':
            bg_path = self._get_image_path('digital_bg.png')
            if bg_path and os.path.exists(bg_path):
                c.drawImage(bg_path, 0, 0, width=page_width, height=page_height)
        
        # --- LOGO (only for digital) ---
        if diploma_type == 'digital':
            logo_path = self._get_image_path('logo_irg.png')
            if logo_path and os.path.exists(logo_path):
                logo_width = 150
                logo_height = 80
                logo_x = (page_width - logo_width) / 2
                logo_y = page_height - 120
                c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
        
        # --- CONTENT POSITIONING ---
        # Adjust Y positions based on page size
        start_y = page_height - 140
        
        col_width = page_width / 2
        left_col_x = 60
        right_col_x = page_width / 2 + 20
        
        # Colors
        c.setFillColorRGB(0, 0, 0)  # Black text
        
        # --- INTRO TEXT ---
        y = start_y
        self._draw_text_in_column(c, "L'Institut Raimon Gaja atorga el present diploma de", 
                                   left_col_x, y, col_width - 80, font_regular, 12, align='right')
        self._draw_text_in_column(c, "El Instituto Raimon Gaja otorga el presente diploma de", 
                                   right_col_x, y, col_width - 80, font_regular, 12, align='left')
        
        # --- COURSE NAME ---
        y -= 30  # Reduced gap
        course_cat = data.get('course_name_cat', '')
        course_es = data.get('course_name_es', '')
        
        course_font_size = 24  # Same as student name
        
        # Draw wrapped text and get new Y
        # Draw wrapped text and get new Y
        y_next_cat = self._draw_wrapped_text_in_column(c, course_cat, left_col_x, y, col_width - 80, font_bold, course_font_size, align='right')
        y_next_es = self._draw_wrapped_text_in_column(c, course_es, right_col_x, y, col_width - 80, font_bold, course_font_size, align='left')
        
        # Update Y to the lowest point from both columns
        y = min(y_next_cat, y_next_es)
        
        # --- "a" ---
        
        # --- "a" ---
        y -= 30  # Reduced gap
        self._draw_centered_text(c, "a", y, font_regular, 14, page_width)
        
        # --- STUDENT NAME ---
        y -= 30  # Reduced gap
        student_name = data.get('student_name', '')
        self._draw_centered_text(c, student_name, y, font_bold, 24, page_width)
        
        # --- BODY TEXT CATALAN ---
        y -= 40  # Reduced gap
        body_cat_1 = "En reconeixement del rendiment acadèmic i a l'aprofitament"
        body_cat_2 = "dels estudis cursats en el programa del màster."
        body_cat_3 = "Aquest màster té el reconeixement d'excel·lència acadèmica"
        body_cat_4 = "de l'European Association of Applied Psychology."
        
        self._draw_text_in_column(c, body_cat_1, left_col_x, y, col_width - 80, font_regular, 11, align='right')
        y -= 15
        self._draw_text_in_column(c, body_cat_2, left_col_x, y, col_width - 80, font_regular, 11, align='right')
        y -= 25
        self._draw_text_in_column(c, body_cat_3, left_col_x, y, col_width - 80, font_regular, 11, align='right')
        y -= 15
        self._draw_text_in_column(c, body_cat_4, left_col_x, y, col_width - 80, font_regular, 11, align='right')
        
        # --- BODY TEXT SPANISH ---
        y_es = y + 55  # Reset Y for right column
        body_es_1 = "En reconocimiento al rendimiento académico y al aprovechamiento"
        body_es_2 = "de los estudios cursados en el programa del máster."
        body_es_3 = "Este máster cuenta con el reconocimiento de excelencia académica"
        body_es_4 = "de la European Association of Applied Psychology."
        
        self._draw_text_in_column(c, body_es_1, right_col_x, y_es, col_width - 80, font_regular, 11, align='left')
        y_es -= 15
        self._draw_text_in_column(c, body_es_2, right_col_x, y_es, col_width - 80, font_regular, 11, align='left')
        y_es -= 25
        self._draw_text_in_column(c, body_es_3, right_col_x, y_es, col_width - 80, font_regular, 11, align='left')
        y_es -= 15
        self._draw_text_in_column(c, body_es_4, right_col_x, y_es, col_width - 80, font_regular, 11, align='left')
        
        # --- DATES ---
        y -= 40  # Reduced gap
        date_cat = data.get('date_cat', '')
        date_es = data.get('date_es', '')
        
        self._draw_text_in_column(c, f"Barcelona, a {date_cat}", left_col_x, y, col_width - 80, font_regular, 12, align='center')
        self._draw_text_in_column(c, f"Barcelona, a {date_es}", right_col_x, y, col_width - 80, font_regular, 12, align='center')
        
        
        # --- SIGNATURES ---
        y -= 60  # Reduced gap
        
        # Store Y for images (top of signature area)
        y_images = y
        
        # Signature Raimon (left)
        sign_raimon_path = self._get_image_path('firma_raimon.png')
        if sign_raimon_path and os.path.exists(sign_raimon_path):
            # Align center of left column
            # Left column starts at left_col_x, width is (col_width - 80)
            # Center of column is left_col_x + (col_width - 80) / 2
            # Draw X = Center - Image Width / 2
            sig_x = left_col_x + (col_width - 80 - 100) / 2
            c.drawImage(sign_raimon_path, sig_x, y_images, width=100, height=50, preserveAspectRatio=True, mask='auto')
        
        # Signature Grecia (right)
        sign_grecia_path = self._get_image_path('firma_grecia.png')
        img_width = 100
        if sign_grecia_path and os.path.exists(sign_grecia_path):
            # Align center of right column
            # Right column starts at right_col_x, width is (col_width - 80)
            sig_x = right_col_x + (col_width - 80 - img_width) / 2
            c.drawImage(sign_grecia_path, sig_x, y_images, width=img_width, height=50, preserveAspectRatio=True, mask='auto')

        # Text Names (Aligned)
        y -= 10  # Reduced gap
        self._draw_text_in_column(c, "Raimon Gaja", left_col_x, y, col_width - 80, font_bold, 14, align='center')
        self._draw_text_in_column(c, "Grecia Malcotti", right_col_x, y, col_width - 80, font_bold, 14, align='center')
        
        y -= 15
        self._draw_text_in_column(c, "Director", left_col_x, y, col_width - 80, font_regular, 11, align='center')
        self._draw_text_in_column(c, "Directora Académica", right_col_x, y, col_width - 80, font_regular, 11, align='center')
        
        y -= 13
        self._draw_text_in_column(c, "Fundador", left_col_x, y, col_width - 80, font_regular, 11, align='center')
        self._draw_text_in_column(c, "Directora Acadèmica", right_col_x, y, col_width - 80, font_regular, 11, align='center')
        
        # --- QR CODE & REGISTRY ---
        qr_url = data.get('qr_url', 'https://institutoraimongaja.com')
        registry = data.get('registry_number', 'DRAFT')
        
        qr_image = self._generate_qr(qr_url)
        c.drawImage(qr_image, 50, 40, width=50, height=50)
        
        c.setFont(font_bold, 9)
        c.drawString(50, 28, f"Nº Registro: {registry}")
        
        # Finalize
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer.getvalue()
