# -*- coding: utf-8 -*-
import io
import os
from odoo import models, api, modules
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from reportlab.lib import colors


class DiplomaGraduacionReportPDF(models.AbstractModel):
    _name = 'report.irg_diploma_graduacion_student.diploma_pdf'
    _description = 'Diploma de Graduación PDF Report'

    def _get_image_path(self, image_name):
        """Get full path to image in module's static folder"""
        return modules.get_module_resource('irg_diploma_graduacion_student', 'static/src/img', image_name)

    def _register_fonts(self):
        """Register Inter fonts if available, otherwise use Helvetica"""
        font_regular = 'Helvetica'
        font_bold = 'Helvetica-Bold'
        
        try:
            # Check our own module first
            font_path = modules.get_module_resource('irg_diploma_graduacion_student', 'static/src/fonts', 'Inter-Regular.ttf')
            if not font_path or not os.path.exists(font_path):
                # Check irg_generacion_diplomas
                font_path = modules.get_module_resource('irg_generacion_diplomas', 'static/src/fonts', 'Inter-Regular.ttf')
            if not font_path or not os.path.exists(font_path):
                font_path = modules.get_module_resource('irg_generacion_diplomas', 'static/src/fonts', 'Inter-regular.ttf')
                
            if font_path and os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Inter', font_path))
                font_regular = 'Inter'

            # Bold font
            font_bold_path = modules.get_module_resource('irg_diploma_graduacion_student', 'static/src/fonts', 'Inter-Bold.ttf')
            if not font_bold_path or not os.path.exists(font_bold_path):
                font_bold_path = modules.get_module_resource('irg_generacion_diplomas', 'static/src/fonts', 'Inter-Bold.ttf')
            if not font_bold_path or not os.path.exists(font_bold_path):
                font_bold_path = modules.get_module_resource('irg_generacion_diplomas', 'static/src/fonts', 'Inter-bold.ttf')
                
            if font_bold_path and os.path.exists(font_bold_path):
                pdfmetrics.registerFont(TTFont('Inter-Bold', font_bold_path))
                font_bold = 'Inter-Bold'
        except Exception:
            pass
            
        return font_regular, font_bold

    def _normalize_catalan_course_name(self, course_name):
        """Normalize common accent differences for Catalan rendering."""
        if not course_name:
            return ""
        normalized = course_name
        normalized = normalized.replace("Máster", "Màster")
        normalized = normalized.replace("máster", "màster")
        normalized = normalized.replace("Master", "Màster")
        normalized = normalized.replace("master", "màster")
        normalized = normalized.replace("Salud", "Salut")
        normalized = normalized.replace("salud", "salut")
        normalized = normalized.replace(" y ", " i ")
        normalized = normalized.replace(" Y ", " I ")
        return normalized

    @api.model
    def generate_diploma_pdf(self, data):
        """Generate the A3 landscape diploma PDF and return bytes"""
        buffer = io.BytesIO()
        
        # A3 Landscape size: Width 1190.55 pt, Height 841.89 pt
        page_width, page_height = landscape(A3)
        
        # Create canvas
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        
        # Register and fetch fonts
        font_regular, font_bold = self._register_fonts()
        
        # Centred X coordinate
        center_x = page_width / 2.0
        
        # --- WATERMARK "Sin validez" ---
        # Rotated 30 degrees, light gray HexColor('#EAEAEA')
        c.saveState()
        c.setFont(font_bold, 100)
        c.setFillColor(colors.HexColor('#EBEBEB'))
        c.translate(center_x, page_height / 2.0)
        c.rotate(30)
        c.drawCentredString(0, -30, "Sin validez")
        c.restoreState()
        
        # Colors
        header_blue = colors.HexColor('#3092C0')
        master_blue = colors.HexColor('#02448A')
        light_blue = colors.Color(60/255.0, 160/255.0, 220/255.0)
        
        # --- HEADER ---
        c.setFillColor(header_blue)
        c.setFont(font_bold, 24)
        c.drawCentredString(center_x, 620, "Diploma de Graduación")
        c.drawCentredString(center_x, 592, "Diploma de Graduació")
        
        # --- COURSE NAMES (Columns) ---
        # Gutter margins: Left column aligned to the right at 545.27 pt
        # Right column aligned to the left at 645.27 pt
        x1 = 397.6
        x2 = 792.9
        
        course_name_cat = data.get('course_name_cat') or ""
        course_name_es = data.get('course_name_es') or ""
        
        course_name_cat = self._normalize_catalan_course_name(course_name_cat)
        
        # Lógica de tamaño de fuente e interlineado (estándar de 32 pt)
        font_size = 32
        leading = 36
        curr_y_start = 510
        
        # Reducción exclusiva y selectiva únicamente para el Máster de Neurodesarrollo
        if "Neurodesarrollo" in course_name_es:
            font_size = 24
            leading = 28
            curr_y_start = 525
            
        lines_course_cat = simpleSplit(course_name_cat, font_bold, font_size, 450)
        lines_course_es = simpleSplit(course_name_es, font_bold, font_size, 450)

        c.setFont(font_bold, font_size)
        c.setFillColor(master_blue)
        
        # Left (Catalan) Column - Aligned to Right
        curr_y = curr_y_start
        for line in lines_course_cat:
            c.drawRightString(545.27, curr_y, line)
            curr_y -= leading
            
        # Right (Spanish) Column - Aligned to Left
        curr_y = curr_y_start
        for line in lines_course_es:
            c.drawString(645.27, curr_y, line)
            curr_y -= leading
        
        # --- MIDDLE CONTENT ---
        c.setFillColor(colors.black)
        c.setFont(font_regular, 16)
        c.drawCentredString(center_x, 430, "a")
        
        student_name = data.get('student_name') or ""
        c.setFillColor(light_blue)
        c.setFont(font_bold, 36)
        c.drawCentredString(center_x, 380, student_name)
        
        # --- DESCRIPTIVE TEXTS ---
        # Left column aligned to Right (at 545.27 pt)
        # Right column aligned to Left (at 645.27 pt)
        desc_cat = "En reconeixement del rendiment acadèmic i a l'aprofitament dels estudis cursats en el programa del màster."
        desc_es = "En reconocimiento al rendimiento académico y al aprovechamiento de los estudios cursados en el programa del máster."
        
        c.setFillColor(colors.black)
        c.setFont(font_regular, 13.5)
        
        # Left (Catalan) Column - Aligned to Right
        lines_cat = simpleSplit(desc_cat, font_regular, 13.5, 450)
        curr_y = 310
        for line in lines_cat:
            c.drawRightString(545.27, curr_y, line)
            curr_y -= 18
            
        # Right (Spanish) Column - Aligned to Left
        lines_es = simpleSplit(desc_es, font_regular, 13.5, 450)
        curr_y = 310
        for line in lines_es:
            c.drawString(645.27, curr_y, line)
            curr_y -= 18
            
        # --- DATES ---
        # Left column aligned to Right, Right column aligned to Left
        date_cat = data.get('date_cat') or ""
        date_es = data.get('date_es') or ""
        
        c.setFont(font_regular, 13.5)
        c.drawRightString(545.27, 220, "Barcelona, a " + date_cat)
        c.drawString(645.27, 220, "Barcelona, a " + date_es)
        
        # --- SIGNATURES (Column Footers) ---
        # Left (Raimon Gaja): Centred in X1 = 297.6, Y = 110, W = 160, H = 60
        raimon_sig_path = self._get_image_path('firma_raimon.png')
        if raimon_sig_path and os.path.exists(raimon_sig_path):
            c.drawImage(raimon_sig_path, x1 - 80, 110, width=160, height=60, preserveAspectRatio=True, mask='auto')
            
        c.setFont(font_bold, 12)
        c.drawCentredString(x1, 80, "Raimon Gaja")
        c.setFont(font_regular, 12)
        c.drawCentredString(x1, 66, "Director")
        c.drawCentredString(x1, 52, "Fundador")
        
        # Right (Fermín Carrillo): Centred in X2 = 892.9, Y = 110, W = 160, H = 60
        fermin_sig_path = self._get_image_path('firmaferminv2.jpg')
        if fermin_sig_path and os.path.exists(fermin_sig_path):
            c.drawImage(fermin_sig_path, x2 - 80, 110, width=160, height=60, preserveAspectRatio=True, mask='auto')
            
        c.setFont(font_bold, 12)
        c.drawCentredString(x2, 80, "Fermín Carrillo")
        c.setFont(font_regular, 12)
        c.drawCentredString(x2, 66, "Director Académico")
        c.drawCentredString(x2, 52, "Director Acadèmic")
        
        # Save page and close canvas
        c.showPage()
        c.save()
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
