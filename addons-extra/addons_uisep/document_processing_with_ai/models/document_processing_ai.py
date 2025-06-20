from odoo import models, _
from odoo.exceptions import UserError
import logging
from datetime import datetime
import uuid
import PyPDF2
from PIL import Image
from pytesseract import pytesseract
import re
import os
import openai
import base64
from io import BytesIO
from pdf2image import convert_from_bytes
import cv2
import numpy as np

_logger = logging.getLogger(__name__)


class DocumentProcessingAI(models.Model):
    _name = 'document_processing_ai'
    _description = ("Core model for document validation and analysis. Integrates OCR and GPT-based evaluation for "
                    "handling various document types.")

    def validar_fecha(self, fecha_str):
        # Lista de formatos a validar
        formatos = ['%Y-%m-%d', '%m/%d/%Y']  # Añade más formatos si es necesario
        for formato in formatos:
            try:
                # Intentar convertir la cadena a un objeto datetime
                fecha = datetime.strptime(fecha_str, formato)
                # Validar que el mes y el día sean correctos
                if 1 <= fecha.month <= 12 and 1 <= fecha.day <= 31:
                    # Verificar días válidos para cada mes
                    if (fecha.month == 2 and fecha.day > 29) or \
                            (fecha.month in [4, 6, 9, 11] and fecha.day > 30):
                        return False
                    return True  # La fecha es válida
            except ValueError:
                continue  # Si falla, prueba con el siguiente formato
        return False  # Ningún formato fue válido

    def verificar_apostille(self, texto, fecha_list):
        palabras = ['aspotille', 'apostilla', 'Apostille', 'Apostilla']

        for palabra in palabras:
            if palabra in texto:
                if palabra in ['apostilla', 'Apostille']:
                    patron = r'\b\d{1,2}/\d{1,2}/\d{4}\b'
                    # patron2 = r'(\d{1,2}) dias del mes de (\w+) del (\d{4})'
                    fecha = re.findall(patron, texto)
                    fecha_list.append(fecha)
                    return True
                else:
                    return False

    def verificar_registraduria(self, texto):
        palabras = ['registraduria', 'Registraduria', 'REGISTRADURIA', 'Registro', 'REGISTRO', 'registro', 'Civil',
                    'civil']
        count = 0
        for palabra in palabras:
            if palabra in texto:
                count += 1
        if count >= 2:
            return True
        else:
            return False

    def verificar_certificacion_nota(self, texto):
        palabras = ['Nota', 'nota', 'notas', 'Notas', 'periodo', 'Periodo', 'PERIODO', 'Pregrado', 'PREGRADO',
                    'pregrado']
        count = 0
        for palabra in palabras:
            if palabra in texto:
                count += 1

        if count >= 2:
            return True
        else:
            return False

    def verificar_acta_grado(self, texto):
        palabras = ['Acta', 'acta', 'Grado', 'grado', 'CERTIFICA', 'certifica', 'Certifica']
        count = 0
        for palabra in palabras:
            if palabra in texto:
                count += 1

        if count >= 2:
            return True
        else:
            return False

    def verificar_legalizacion(self, texto):
        palabras = ['LEGALIZACIÓN DE DOCUMENTOS DE EDUCACIÓN SUPERIOR', 'Institución', 'LEGALIZACIÓN',
                    'DOCUMENTOS DE EDUCACIÓN']
        count = 0
        for palabra in palabras:
            if palabra in texto:
                count += 1

        if count >= 2:
            return True
        else:
            return False

    def evaluar_legibilidad_documento(self, attachment):
        """
        Evalúa la legibilidad de un documento PDF almacenado como `ir.attachment` en Odoo.

        Args:
            attachment (ir.attachment): Objeto de adjunto en Odoo.

        Returns:
            str: Resultado general de la evaluación del documento (legible o no legible).
        """

        def convertir_pdf_a_imagen(pdf_data):
            """Convierte las páginas de un archivo PDF a imágenes usando datos en memoria."""
            try:
                paginas_imagenes = convert_from_bytes(pdf_data, 300)  # Usar bytes directamente
                return paginas_imagenes
            except Exception as e:
                _logger.debug(f"Error al convertir el PDF: {str(e)}")
                return []

        def analizar_legibilidad(imagen):
            """Analiza la legibilidad de la imagen mediante OCR y análisis de claridad, contraste y nitidez."""
            try:
                # Convertir a escala de grises
                imagen_gris = cv2.cvtColor(np.array(imagen), cv2.COLOR_RGB2GRAY)

                # Calcular contraste y claridad
                contraste = imagen_gris.std()  # Desviación estándar de los píxeles
                claridad = cv2.Laplacian(imagen_gris, cv2.CV_64F).var()  # Varianza del Laplaciano (nitidez)

                # Calcular nitidez (evaluando bordes detectados)
                bordes = cv2.Canny(imagen_gris, 100, 200)  # Bordes detectados con Canny
                nitidez = np.sum(bordes) / bordes.size  # Proporción de píxeles que son bordes

                # Umbrales
                umbral_contraste = [15, 80]  # Contraste mínimo aceptable
                umbral_claridad = [20, 2000]  # Claridad mínima aceptable
                umbral_nitidez = 0.02  # Nitidez mínima como proporción de bordes detectados

                # Evaluar si es legible
                if contraste < umbral_contraste[0] or contraste > umbral_contraste[1]:
                    return False
                if claridad < umbral_claridad[0] or claridad > umbral_claridad[1]:
                    return False
                if nitidez < umbral_nitidez:
                    return False
                return True
            except Exception as e:
                _logger.debug(f"Error al analizar la legibilidad de la imagen: {str(e)}")
                return False

        # Manejar el adjunto
        pdf_data = None

        try:
            if attachment.datas:  # Archivo almacenado en base64
                pdf_data = base64.b64decode(attachment.datas)
            else:
                _logger.debug("No se pudo obtener los datos del archivo PDF.")
                return False

            # Convertir el PDF a imágenes
            imagenes = convertir_pdf_a_imagen(pdf_data)
            if not imagenes:
                _logger.debug("Error al convertir el PDF. No se puede evaluar.")
                return False

            # Analizar cada página del documento
            for i, imagen in enumerate(imagenes):
                if not analizar_legibilidad(imagen):
                    _logger.debug(f"El documento no es legible. Problemas detectados en la página {i + 1}.")
                    return False

            return True

        except Exception as e:
            _logger.debug(f"Error durante la evaluación: {str(e)}")
            return False

    def formato_incorrecto(self, file, text_list, fecha_list):
        if 'acta' in file:
            if self.verificar_apostille(text_list[0], fecha_list):

                apostille_validate = 0
                acta_grado_validate = 0
                legalizacion_validate = 0
                for index in range(len(text_list)):

                    text_validate = text_list[index]

                    if self.verificar_apostille(text_validate, fecha_list):
                        apostille_validate += 1
                    if self.verificar_acta_grado(text_validate):
                        acta_grado_validate += 1
                    if self.verificar_legalizacion(text_validate):
                        legalizacion_validate += 1
                if apostille_validate + acta_grado_validate + legalizacion_validate >= 3:
                    return True
            else:
                return False

        elif 'diploma' in file:
            if self.verificar_apostille(text_list[0], fecha_list):

                apostille_validate = 0
                acta_grado_validate = 0
                legalizacion_validate = 0
                for index in range(len(text_list)):
                    text_validate = text_list[index]

                    if self.verificar_apostille(text_validate, fecha_list):
                        apostille_validate += 1
                    if self.verificar_acta_grado(text_validate):
                        acta_grado_validate += 1
                    if self.verificar_legalizacion(text_validate):
                        legalizacion_validate += 1
                if apostille_validate + acta_grado_validate + legalizacion_validate >= 3:
                    return True
            else:
                return False

        elif 'registro' in file:
            if self.verificar_apostille(text_list[0], fecha_list):

                apostille_validate = 0
                registraduria_validate = 0
                legalizacion_validate = 0
                for index in range(len(text_list)):
                    text_validate = text_list[index]

                    if self.verificar_apostille(text_validate, fecha_list):
                        apostille_validate += 1
                    if self.verificar_registraduria(text_validate):
                        registraduria_validate += 1
                    if self.verificar_legalizacion(text_validate):
                        legalizacion_validate += 1
                if apostille_validate + registraduria_validate + legalizacion_validate >= 3:
                    return True
            else:
                return False

        elif 'notas' in file:
            if self.verificar_apostille(text_list[0], fecha_list):

                apostille_validate = 0
                certificacion_validate = 0
                legalizacion_validate = 0
                for index in range(len(text_list)):
                    text_validate = text_list[index]

                    if self.verificar_apostille(text_validate, fecha_list):
                        apostille_validate += 1
                    if self.verificar_certificacion_nota(text_validate):
                        certificacion_validate += 1
                    if self.verificar_legalizacion(text_validate):
                        legalizacion_validate += 1
                if apostille_validate + certificacion_validate + legalizacion_validate >= 3:
                    return True
            else:
                return False

        return False

    def documento_incorrecto(self, fecha_list):
        if self.validar_fecha(fecha_list[0][0]):
            return True
        else:
            return False

    def add_comment(self, attachment_id, reason_for_observation):
        '''
            Creates a record in mail.message with the comment added in the wizard.
            Modify the state of attachment to observed.
            :return: None
        '''
        partner_id = attachment_id.partner_id
        body = '''
            <p>Observación en adjunto: <strong>{}</strong></p>
            <p>Detalle:</p>
            <p class="text-danger"><strong>{}</strong></p>
        '''.format(attachment_id.document, reason_for_observation)
        self.env['mail.message'].create({
            'message_type': 'comment',
            'model': 'res.partner',
            'res_id': partner_id.id,
            'subject': partner_id.name,
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'author_id': partner_id.id,
            'body': body
        })
        attachment_id.sudo().write({
            'state': 'observed',
            'reason_for_observation': reason_for_observation
        })

    def __ocr__(self, document):
        try:
            ruta_linux = self.env['ir.config_parameter'].search([('key', '=', 'tesseract_route_linux')]).value
            ruta_windows = self.env['ir.config_parameter'].search([('key', '=', 'tesseract_route_windows')]).value
            if ruta_linux:
                pytesseract.tesseract_cmd = f"{ruta_linux}"
            elif ruta_windows:
                pytesseract.tesseract_cmd = fr"{ruta_windows}"
            else:
                raise UserError(_("Configure Tesseract OCR path"))
        except:
            raise UserError(_("Configure Tesseract OCR path"))

        file_finish = document
        try:
            file_content = base64.b64decode(file_finish.datas)
            reader = PyPDF2.PdfReader(BytesIO(file_content))

            num_page = len(reader.pages)

            text_list = []

            count = 0
            for index_page in range(num_page):
                page = reader.pages[index_page]
                page_text = reader.pages[index_page]

                text = page_text.extract_text()
                text_list.append(text)

                for imagen_file in page.images:
                    image_path = f'img_{uuid.uuid4()}.jpg'
                    with open(image_path, "wb") as img:
                        img.write(imagen_file.data)

                    # Abrir la imagen con PIL
                    img_pil = Image.open(image_path)

                    # Extraer texto de la imagen usando pytesseract
                    text_img = pytesseract.image_to_string(img_pil, lang='spa')  # Cambia 'spa' por el idioma que necesites
                    # text_img = pytesseract.image_to_string(img_pil)
                    text_list.append(text_img)
                    os.remove(image_path)

                    count += 1

            return text_list
        except:
            return 'incorrect_format'

    def local_ocr(self, document):

        text_list = self.__ocr__(document)
        if text_list != 'incorrect_format':
            fecha_list = []

            if self.evaluar_legibilidad_documento(document):
                if self.formato_incorrecto(document.name, text_list, fecha_list):
                    if self.documento_incorrecto(fecha_list):
                        document.state = 'accepted'
                    else:
                        self.add_comment(document, 'incorrect_document')
                else:
                    self.add_comment(document, 'incorrect_format')
            else:
                self.add_comment(document, 'poor_readability')
        else:
            self.add_comment(document, 'incorrect_format')

    def _chat_gpt(self, document, parameters):
        if self.env['custom_ai_parameter'].prueba_de_conexion(view=False):
            try:
                openai.api_key = self.env['ir.config_parameter'].search([('key', '=', 'openai_api_key')]).value
                text_list = self.__ocr__(document)

                system_message = {
                    "role": "system",
                    "content":
                        "Eres un asistente de inteligencia artificial que evalúa la calidad de los documentos."
                        "Tendrás que tener en cuenta los siguiente factores:\n"
                        f"{parameters}\n"
                        "Se tienen que cumplir todos estrictamente para poder aprobar el documento. "
                        "\n\nSOLO PODRÁS RESPONDER CON UNO DE ESTAS OPCIONES EN CORRESPONDENCIA DE LA DESCICIÓN FINAL"
                        "Y NI UNA PALABRA MAS:\n"
                        "*accepted\n*incorrect_format\n*incorrect_document\n"
                        "#Un documento tiene formato incorrecto(incorrect_format) cuando no comienza con la apostilla, "
                        "\n"
                        "#Un documento es incorrecto (incorrect_document) cuando \n"
                }

                user_message = {
                    "role": "user",
                    "content": f"Por favor, analiza el siguiente texto extraído de un documento PDF:\n\n{''.join(text_list)}"
                }

                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[system_message, user_message],
                    request_timeout=10,
                )
                respuesta = response['choices'][0]['message']['content']
                if respuesta == 'accepted':
                    if self.evaluar_legibilidad_documento(document):
                        document.state = 'accepted'
                    else:
                        self.add_comment(document, 'poor_readability')
                elif respuesta == 'incorrect_format':
                    self.add_comment(document, 'incorrect_format')
                elif respuesta == 'incorrect_document':
                    self.add_comment(document, 'incorrect_document')

            except Exception as e:
                _logger.debug("Error al conectar con OpenAI:", e)
                self.local_ocr(document)
        else:
            _logger.debug("Error al conectar con OpenAI")
            self.local_ocr(document)

    def main__(self, document):
        parametro_doc = False
        if 'acta' in document.name.lower() or 'degree' in document.name.lower():
            parametro_doc = self.env['custom_ai_parameter'].search([('type_document', '=', 'degree_certificate')],
                                                                   limit=1)
        elif 'certificación' in document.name.lower() or 'certification' in document.name.lower():
            parametro_doc = self.env['custom_ai_parameter'].search([('type_document', '=', 'certification_notes')],
                                                                   limit=1)
        elif 'registro' in document.name.lower() or 'registry' in document.name.lower():
            parametro_doc = self.env['custom_ai_parameter'].search([('type_document', '=', 'civil_registry')],
                                                                   limit=1)

        if parametro_doc and parametro_doc.chat_gpt_ and parametro_doc.parameters_for_gpt:
            self._chat_gpt(document, parametro_doc.parameters_for_gpt)
        else:
            self.local_ocr(document)
