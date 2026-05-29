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

    def _fit_single_line_font_size(self, c, text, font_name, max_font_size, min_font_size, max_width, step=0.5):
        """Return the biggest font size that keeps text on a single line inside max_width."""
        if not text:
            return max_font_size

        font_size = max_font_size
        while font_size > min_font_size and c.stringWidth(text, font_name, font_size) > max_width:
            font_size -= step

        return max(font_size, min_font_size)

    def _normalize_catalan_course_name(self, course_name):
        """Normalize common accent differences for Catalan rendering.

        Also convert the Spanish conjunction " y " to Catalan " i " when it appears
        in the course title, since source data may be entered in Spanish but the
        Catalan version should use the correct word.
        """
        if not course_name:
            return course_name

        normalized = course_name
        normalized = normalized.replace("Máster", "Màster")
        normalized = normalized.replace("máster", "màster")
        normalized = normalized.replace("Master", "Màster")
        normalized = normalized.replace("master", "màster")
        normalized = normalized.replace("Salud", "Salut")
        normalized = normalized.replace("salud", "salut")
        # convert Spanish conjunction y to Catalan i when surrounded by spaces
        normalized = normalized.replace(" y ", " i ")
        normalized = normalized.replace(" Y ", " I ")
        return normalized

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

        # Base reference: A4 landscape proportions
        base_width, base_height = landscape(A4)
        scale_factor = min(page_width / base_width, page_height / base_height)

        def sp(value):
            return value * scale_factor

        def sf(value, min_size=7):
            # global reduction to make all typographies a little smaller
            return max(min_size, value * scale_factor * 0.95)

        # small upward shift to lift most of the text slightly nearer the top edge
        # bumped up a bit after review; diplomas were sitting too low
        # increased again based on latest feedback
        y_shift = sp(25)

        logo_width_base = 150
        # aggressively reduce margins/gutter to widen side columns as requested
        if diploma_type == 'physical':
            side_margin = page_width * 0.090
            gutter = sp(logo_width_base) * 0.40
        else:
            side_margin = page_width * 0.050
            gutter = sp(logo_width_base) * 0.80
        col_width = (page_width - (2 * side_margin) - gutter) / 2
        left_col_x = side_margin
        right_col_x = left_col_x + col_width + gutter
        
        # Keep a very small width boost for title only; previous value was too
        # wide and produced undesirable wrapping balance. The final per-column
        # width will be adjusted later based on title length so short titles
        # can use a noticeably narrower block.
        title_extra = gutter * 0.1
        default_title_width = col_width + title_extra
        # title_left_x/_right_x will be computed after we know the title text
        
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
                logo_width = sp(logo_width_base)
                logo_height = sp(76)
                logo_x = (page_width - logo_width) / 2
                logo_y = page_height - sp(118)
                c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
        
        # --- CONTENT POSITIONING ---
        # move the starting Y a bit higher overall (y_shift)
        start_y = page_height - sp(188) + y_shift
        
        # Colors
        c.setFillColorRGB(0, 0, 0)  # Black text
        
        # --- COURSE NAME ---
        y = start_y
        y -= sp(48)
        course_cat = self._normalize_catalan_course_name(data.get('course_name_cat', ''))
        course_es = data.get('course_name_es', '')

        # Base course title sizes for each language; reduce if very long
        course_font_size_cat = sf(19)
        course_font_size_es = sf(19)
        try:
            if course_cat and len(course_cat.strip()) > 62:
                course_font_size_cat = max(sf(8), course_font_size_cat - 2)
        except Exception:
            pass
        try:
            if course_es and len(course_es.strip()) > 62:
                course_font_size_es = max(sf(8), course_font_size_es - 2)
        except Exception:
            pass
        # Apply an additional 1pt reduction for physical diplomas
        try:
            if diploma_type == 'physical':
                course_font_size_cat = max(sf(8), course_font_size_cat - 1)
                course_font_size_es = max(sf(8), course_font_size_es - 1)
        except Exception:
            pass

        # If a title is short we make its block more narrow so it visually
        # sits closer to the centre; otherwise use the default wider block.
        left_title_width = default_title_width
        right_title_width = default_title_width
        try:
            if course_cat and len(course_cat.strip()) < 45:
                left_title_width = col_width * 0.8
        except Exception:
            pass
        try:
            if course_es and len(course_es.strip()) < 45:
                right_title_width = col_width * 0.8
        except Exception:
            pass

        # compute X anchors so that the narrower title block is centred inside
        # its original column area
        title_left_x = left_col_x + (col_width - left_title_width) / 2
        title_right_x = right_col_x + (col_width - right_title_width) / 2

        # --- INTRO TEXT ---
        # Draw the intro lines inside the same narrower blocks as the titles
        y_intro = start_y
        intro_font_size = sf(9.5) if diploma_type == 'physical' else sf(11)
        self._draw_text_in_column(c, "L'Institut Raimon Gaja atorga el present diploma de",
                       title_left_x, y_intro, left_title_width, font_regular, intro_font_size, align='right')
        self._draw_text_in_column(c, "El Instituto Raimon Gaja otorga el presente diploma de",
                       title_right_x, y_intro, right_title_width, font_regular, intro_font_size, align='left')

        # --- COURSE NAME ---
        # Draw full title text and let wrapping be controlled only by width.
        y_next_cat = self._draw_wrapped_text_in_column(
            c,
            course_cat,
            title_left_x,
            y,
            left_title_width,
            font_bold,
            course_font_size_cat,
            align='right',
        )
        y_next_es = self._draw_wrapped_text_in_column(
            c,
            course_es,
            title_right_x,
            y,
            right_title_width,
            font_bold,
            course_font_size_es,
            align='left',
        )
        
        # Update Y to the lowest point from both columns
        y = min(y_next_cat, y_next_es)
        
        # --- "a" ---
        # lift the "a" a bit when we've moved elements upward earlier
        y -= sp(14)
        self._draw_centered_text(c, "a", y, font_regular, sf(13), page_width)
        
        # --- STUDENT NAME ---
        y -= sp(22)
        student_name = data.get('student_name', '')
        student_max_width = page_width - (2 * side_margin)
        student_font_size = self._fit_single_line_font_size(
            c,
            student_name,
            font_bold,
            max_font_size=sf(20),
            min_font_size=sf(12),
            max_width=student_max_width,
        )
        self._draw_centered_text(c, student_name, y, font_bold, student_font_size, page_width)
        
        # --- BODY TEXT CATALAN ---
        # this block contains the longer paragraph on the left side of the
        # diploma. the customer requested it be left-aligned (not centred/right),
        # so we specify align='left' below.  if you need to tweak the X offset
        # for the text area itself, adjust `left_col_x` or add/subtract an extra
        # value here (e.g. left_col_x + sp(5)).
        y -= sp(46)
        y_start_body = y
        body_font_size = sf(8.5) if diploma_type == 'physical' else sf(10)
        body_line_gap = sp(13) if diploma_type == 'physical' else sp(15)
        body_cat_1 = "En reconeixement del rendiment acadèmic i a l'aprofitament"
        body_cat_2 = "dels estudis cursats en el programa del màster."
        body_cat_3 = "Aquest màster té el reconeixement d'excel·lència acadèmica"
        body_cat_4 = "de l'European Association of Applied Psychology."
        
        body_sec_gap = sp(12) if diploma_type == 'physical' else sp(25)
        self._draw_text_in_column(c, body_cat_1, left_col_x, y, col_width, font_regular, body_font_size, align='right')
        y -= body_line_gap
        self._draw_text_in_column(c, body_cat_2, left_col_x, y, col_width, font_regular, body_font_size, align='right')
        y -= body_sec_gap
        self._draw_text_in_column(c, body_cat_3, left_col_x, y, col_width, font_regular, body_font_size, align='right')
        y -= body_line_gap
        self._draw_text_in_column(c, body_cat_4, left_col_x, y, col_width, font_regular, body_font_size, align='right')
        
        # --- BODY TEXT SPANISH ---
        y_es = y_start_body
        body_es_1 = "En reconocimiento al rendimiento académico y al aprovechamiento"
        body_es_2 = "de los estudios cursados en el programa del máster."
        body_es_3 = "Este máster cuenta con el reconocimiento de excelencia académica"
        body_es_4 = "de la European Association of Applied Psychology."
        
        self._draw_text_in_column(c, body_es_1, right_col_x, y_es, col_width, font_regular, body_font_size, align='left')
        y_es -= body_line_gap
        self._draw_text_in_column(c, body_es_2, right_col_x, y_es, col_width, font_regular, body_font_size, align='left')
        y_es -= body_sec_gap
        self._draw_text_in_column(c, body_es_3, right_col_x, y_es, col_width, font_regular, body_font_size, align='left')
        y_es -= body_line_gap
        self._draw_text_in_column(c, body_es_4, right_col_x, y_es, col_width, font_regular, body_font_size, align='left')
        y = min(y, y_es)
        
        # --- DATES ---
        y -= sp(48)
        date_cat = data.get('date_cat', '')
        date_es = data.get('date_es', '')
        
        date_font_size = sf(9.5) if diploma_type == 'physical' else sf(11)
        # avoid double "de de" in the left date
        clean_cat = date_cat.replace(' de de ', ' de ')
        self._draw_text_in_column(c, f"Barcelona, a {clean_cat}", left_col_x, y, col_width, font_regular, date_font_size, align='right')
        self._draw_text_in_column(c, f"Barcelona, a {date_es}", right_col_x, y, col_width, font_regular, date_font_size, align='left')
        
        
        # --- SIGNATURES ---
        # in this section we draw lines/names for digital and physical diplomas.
        # horizontal (x) positions are calculated using three column anchors
        # defined earlier: left_col_x, right_col_x and gutter.  if you want to
        # slide any of the three zones horizontally:
        #   * adjust left_col_x or right_col_x at the top of the method
        #   * or modify the expressions below that add offsets to those anchors
        #     (e.g. add/subtract sp(10) to nudge a particular column left/right).
        # for example, the centre signature zone is positioned by
        #   left_col_x + col_width + gutter/2
        # changing that expression will move only the middle column.
        # move further down to make space and lower the signature area
        y -= sp(34) if diploma_type == 'physical' else sp(54)

        # Store Y for images (bottom of signature area). push signatures
        # a bit further down so they sit below the date. increase the
        # offset slightly for digital diplomas so labels won't overlap.
        y_images = y - sp(34) if diploma_type == 'digital' else y - sp(12)

        # compute QR coordinates now so that later branches can reference qr_y
        qr_url = data.get('qr_url', 'https://institutoraimongaja.com')
        registry = data.get('registry_number', 'DRAFT')
        qr_size = sp(46)
        qr_x = side_margin + sp(36)
        # For physical diplomas move the QR slightly towards the centre
        # (away from the left margin).
        if diploma_type == 'physical':
            qr_x = left_col_x + sp(5)
        # Initial QR bottom aligned to signature images baseline; may be
        # adjusted below for digital diplomas so it doesn't overlap labels
        qr_y = y_images

        if diploma_type == 'digital':
            # Signature Raimon (left)
            sign_raimon_path = self._get_image_path('firma_raimon.png')
            if sign_raimon_path and os.path.exists(sign_raimon_path):
                sig_width = sp(95)
                sig_height = sp(47)
                # nudge signatures noticeably towards the centre for digital
                # diplomas and center them under the date (column centre).
                sig_shift = sp(48)
                left_center = left_col_x + col_width / 2
                sig_x = left_center + sig_shift - (sig_width / 2)
                c.drawImage(sign_raimon_path, sig_x, y_images, width=sig_width, height=sig_height, preserveAspectRatio=True, mask='auto')
            
            # Signature Grecia (right)
            sign_grecia_path = self._get_image_path('firmaferminv2.jpg')
            sig_width = sp(95)
            sig_height = sp(47)
            if sign_grecia_path and os.path.exists(sign_grecia_path):
                right_center = right_col_x + col_width / 2
                sig_x = right_center - sig_shift - (sig_width / 2)
                c.drawImage(sign_grecia_path, sig_x, y_images, width=sig_width, height=sig_height, preserveAspectRatio=True, mask='auto')

            # Text Names (Aligned) – place labels below the signature images
            # so they do not overlap; compute an explicit label start Y
            label_start_y = y_images - sp(6)
            # apply same horizontal nudge to text labels so they line up with
            # the nudged signature images (use column-centred anchors)
            self._draw_text_in_column(c, "Raimon Gaja", left_col_x + sig_shift, label_start_y, col_width, font_bold, sf(13), align='center')
            self._draw_text_in_column(c, "Fermín Carrillo", right_col_x - sig_shift, label_start_y, col_width, font_bold, sf(13), align='center')

            role_y = label_start_y - sp(16)
            self._draw_text_in_column(c, "Director", left_col_x + sig_shift, role_y, col_width, font_regular, sf(10), align='center')
            self._draw_text_in_column(c, "Director Académico", right_col_x - sig_shift, role_y, col_width, font_regular, sf(10), align='center')

            footer_y = role_y - sp(14)
            self._draw_text_in_column(c, "Fundador", left_col_x + sig_shift, footer_y, col_width, font_regular, sf(10), align='center')
            self._draw_text_in_column(c, "Director Acadèmic", right_col_x - sig_shift, footer_y, col_width, font_regular, sf(10), align='center')
            # place the QR a bit above the footer baseline so it does not
            # overlap the registry text; keep registry baseline at footer_y
            qr_y = role_y + sp(12)
            reg_baseline_y = role_y
        else:
            # physical diploma: reserve three signature zones for handwritten
            # users will sign above these labels, so we don't draw images.
            # earlier versions drew faint guideline lines, which have now been
            # removed per customer request. the remaining code simply leaves room
            # and prints the labels.

            # Lower the QR a bit so the registry text can be aligned with
            # the signature labels below. Move it further down so the QR
            # sits closer to its registry text baseline and shift slightly
            # right to better center under its text.
            qr_y = y_images - sp(30)

            # position signatures labels much lower so there is room above
            # for a handwritten signature to be placed without overlapping
            # the printed text. Reduce the downward offset so the labels
            # (and signing area) sit a bit higher on the page.
            sign_text_y = qr_y - sp(28)
            # left column should show the student/interested name rather than
            # the director's name; original variable defined above.  shift it
            # slightly right to balance the QR code on the far left.
            left_student_x = left_col_x + sp(12)
            self._draw_text_in_column(c, student_name, left_student_x, sign_text_y, col_width, font_bold, sf(10), align='center')
            # place Raimon exactly at page centre rather than using a
            # column width; draw_centered_text does the job directly and
            # avoids the extra horizontal offset caused by col_width.
            self._draw_centered_text(
                c,
                "Raimon Gaja",
                sign_text_y,
                font_bold,
                sf(10),
                page_width,
            )
            self._draw_text_in_column(c, "Fermín Carrillo", right_col_x, sign_text_y, col_width, font_bold, sf(10), align='center')

            # second row: roles titles/labels (left = interested, centre=Director, right=Acad.)
            role_y = sign_text_y - sp(18)
            # split Spanish / Catalan onto two lines instead of one long string
            self._draw_text_in_column(c, "Interesado/a", left_student_x, role_y, col_width, font_regular, sf(9), align='center')
            self._draw_text_in_column(c, "Interessat/da", left_student_x, role_y - sp(10), col_width, font_regular, sf(9), align='center')
            # keep Director centered on page
            self._draw_centered_text(c, "Director", role_y, font_regular, sf(9), page_width)
            self._draw_text_in_column(c, "Director Académico", right_col_x, role_y, col_width, font_regular, sf(9), align='center')

            # third row: footer names (keep them lower to allow signing above)
            footer_y = role_y - sp(12)
            self._draw_centered_text(c, "Fundador", footer_y, font_regular, sf(9), page_width)
            self._draw_text_in_column(c, "Director Acadèmic", right_col_x, footer_y, col_width, font_regular, sf(9), align='center')
            # set registry baseline for physical diplomas so the registry
            # text aligns vertically with the 'Interessat/da' label by
            # placing it at the same baseline.
            reg_baseline_y = role_y
            # place the QR so its bottom sits a few points above the
            # registry text baseline, ensuring the image is directly
            # above "Nº Registro:" for physical diplomas.
            qr_y = reg_baseline_y + sp(10)

        # --- QR CODE & REGISTRY ---
        qr_image = self._generate_qr(qr_url)
        c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)

        c.setFont(font_bold, sf(8))
        # centre registry text under QR
        reg_text = f"Nº Registro: {registry}"
        text_width = c.stringWidth(reg_text, font_bold, sf(8))
        text_x = qr_x + (qr_size - text_width) / 2
        # replace final two-digit year in registry text with the year
        # taken from the diploma date (prefer Spanish version). if date isn't
        # parseable we leave the text untouched.
        try:
            import re
            # get year from diploma date as before
            year = None
            for dfield in ('date_es', 'date_cat'):
                dval = data.get(dfield)
                if dval:
                    m = re.search(r"(\d{4})$", dval)
                    if m:
                        year = m.group(1)
                        break
            if year:
                # replace any two-digit year between dashes with full year
                reg_text = re.sub(r"-(\d{2})-", f"-{year}-", reg_text)
        except Exception:
            pass
        # place registry text so its baseline aligns with the signature
        # footer baseline (use reg_baseline_y when available to align with
        # 'Fundador'); otherwise fall back slightly below the QR to avoid
        # overlap for non-digital diplomas.
        try:
            c.drawString(text_x, reg_baseline_y, reg_text)
        except NameError:
            c.drawString(text_x, qr_y - sp(10), reg_text)
        
        # Finalize
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer.getvalue()
