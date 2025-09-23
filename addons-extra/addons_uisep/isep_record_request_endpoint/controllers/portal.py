import logging
import os
import base64
import mimetypes
from odoo import http
from odoo.http import request
from odoo.addons.isep_record_request.controllers.portal import CustomerPortal
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

ALLOW_EXT = {'.pdf', '.png', '.jpg', '.jpeg', '.webp'}

def _upload_file(filename: str, file_bytes: bytes, guessed_type: str):
    """
    Sube un archivo al endpoint /upload/.
    Devuelve (ok: bool, s3_filename: Optional[str], raw_body: str)
    """
    try:
        import requests
        from io import BytesIO
    except ImportError:
        _logger.error(
            "Falta dependencia 'requests'. Instálala con 'pip install requests' "
        )
        raise

    ctype = (guessed_type or '').strip() or 'application/octet-stream'

    def _do_req(payload):
        upload_url = http.request.env["ir.config_parameter"].sudo().get_param("upload_url")
        if not upload_url:
            raise ValueError("Parámetro 'upload_url' no configurado en ir.config_parameter")

        resp = requests.post(upload_url, files=payload, timeout=20)
        body = resp.text or ''
        try:
            data = resp.json()
        except Exception:
            data = None
        return resp, body, data

    try:
        resp, body, data = _do_req({'file': (filename, BytesIO(file_bytes), ctype)})
        if resp.status_code < 400:
            s3_name = None
            if isinstance(data, dict) and data.get('uploaded_files'):
                s3_name = data['uploaded_files'][0].get('s3_filename')
            _logger.info("Upload OK -> %s (%s) | resp: %s", filename, resp.status_code, body[:500])
            return True, s3_name, body
        _logger.warning("Upload 1/2 fallo %s -> %s | body: %s", filename, resp.status_code, body[:500])
    except Exception as e:
        _logger.warning("Upload 1/2 excepción %s: %s", filename, e)

    try:
        resp2, body2, data2 = _do_req({'file': (filename, BytesIO(file_bytes))})
        resp2.raise_for_status()
        s3_name = None
        if isinstance(data2, dict) and data2.get('uploaded_files'):
            s3_name = data2['uploaded_files'][0].get('s3_filename')
        _logger.info("Upload OK (reintento) -> %s (%s) | resp: %s", filename, resp2.status_code, body2[:500])
        return True, s3_name, body2
    except Exception as e:
        _logger.warning("Upload 2/2 excepción %s: %s", filename, e)
        return False, None, ''


def _call_ocr_raw_with_retry(faceselfie_name: str, ocrident_name: str = "onboarding-uisep",
                             retries: int = 3, delay_sec: float = 0.8) -> bool:
    """
    Llama al endpoint /ocr-raw/ enviando SOLO los nombres (JSON).
    Reintenta si el backend aún no ve el objeto en S3.
    """
    try:
        import requests
        import time
    except ImportError:
        _logger.error("Falta 'requests'. Instálala o declárala en external_dependencies.")
        raise

    ocr_raw_url = http.request.env["ir.config_parameter"].sudo().get_param("ocr_raw_url")
    if not ocr_raw_url:
        _logger.warning("Parámetro 'ocr_raw_url' no configurado; no se llama OCR-RAW.")
        return False

    payload = {"faceselfie": faceselfie_name, "ocrident": ocrident_name}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(ocr_raw_url, json=payload, timeout=20)
            txt = (resp.text or '')[:500]
            if resp.status_code < 400:
                _logger.info("OCR-RAW OK -> %s (%s)", faceselfie_name, resp.status_code)
                return True

            if resp.status_code == 400 and "S3_Access_Error" in txt:
                _logger.info(
                    "OCR-RAW aún no encuentra el objeto (intento %s/%s). "
                    "Esperando %.1fs… | body: %s",
                    attempt, retries, delay_sec, txt
                )
                time.sleep(delay_sec)
                continue

            _logger.warning("OCR-RAW fallo -> %s | body: %s", resp.status_code, txt)
            return False
        except Exception as e:
            _logger.exception("OCR-RAW excepción intento %s/%s: %s", attempt, retries, e)
            time.sleep(delay_sec)
    _logger.warning("OCR-RAW fallo definitivo tras %s intentos para %s", retries, faceselfie_name)
    return False


class CustomerPortalInh(CustomerPortal):
    @http.route(['/my/documents'], type='http', methods=['GET', 'POST'], auth='public', website=True, priority=1001)
    def document_form_view(self, **kwargs):
        """
        Actualiza adjuntos del partner + sube a /upload/ y llama /ocr-raw/
        enviando SOLO los nombres (JSON) tal como el curl.
        """
        user_id = request.env.uid
        current_user = request.env['res.users'].sudo().browse(user_id)

        values = {
            'page_name': 'document_form_view',
            'partner_id': current_user.partner_id,
            'ir_attachment_ids': current_user.partner_id.ir_attachment_ids,
        }

        if request.httprequest.method == 'GET':
            return request.render('isep_record_request.document_form_view', values)

        redirect_url = '/my'
        files_dict = request.httprequest.files
        form_dict = request.httprequest.form

        try:
            for _k in files_dict:
                _fs = files_dict.get(_k)
                _name = (getattr(_fs, 'filename', '') or '').strip()
                _logger.info("POST file key=%s filename=%s", _k, _name)
        except Exception:
            pass

        roles_map = {}
        for k in form_dict:
            if not k.startswith('role_update_document_'):
                continue
            try:
                rid = int(k.split('role_update_document_')[1])
                roles_map[rid] = (form_dict.get(k) or '').strip()
            except Exception:
                continue

        documents_to_update = []
        for key in files_dict:
            if not key.startswith('update_document_'):
                continue
            try:
                doc_id = int(key.split('update_document_')[1])
            except Exception:
                continue

            fs = files_dict.get(key)
            if not fs:
                continue

            filename = (getattr(fs, 'filename', '') or '').strip()
            if not filename:
                continue

            try:
                fs.stream.seek(0)
            except Exception:
                pass
            file_bytes = fs.stream.read()
            if not file_bytes:
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ALLOW_EXT and ext not in ALLOW_EXT:
                _logger.warning("Extensión no permitida: %s (permitidas: %s)", ext, ALLOW_EXT)
                continue

            documents_to_update.append({
                'document_id': doc_id,
                'file': fs,
                'filename': filename,
                'file_bytes': file_bytes,
            })

        try:
            for item in documents_to_update:
                fs = item['file']
                filename = item['filename']
                file_bytes = item['file_bytes']
                doc_id = item['document_id']

                decoded_file = base64.b64encode(file_bytes)
                attachment = request.env['ir.attachment'].sudo().browse(doc_id)
                if not attachment.exists():
                    _logger.warning("Attachment id=%s no existe; se omite.", doc_id)
                    continue

                attachment.write({
                    'datas': decoded_file,
                    'name': filename,
                    'public': True,
                    'res_model': 'res.partner',
                    'res_id': current_user.partner_id.id,
                    'state': 'on_hold',
                })

                guessed_type = getattr(fs, 'mimetype', None) or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                ok_upload, s3_key, upload_body = _upload_file(filename, file_bytes, guessed_type)
                if not ok_upload:
                    _logger.warning("No se pudo subir %s a /upload/. Se omite OCR-RAW.", filename)
                    continue

                faceselfie_name = s3_key or filename
                _call_ocr_raw_with_retry(faceselfie_name, "onboarding-uisep")

            return request.redirect(redirect_url)

        except ValidationError as ve:
            _logger.error('******************* ACTUALIZACIÓN DE DOCUMENTO FALLIDA *******************')
            _logger.error('***************** Valores incorrectos. Razón: %s *****************', ve)
            return request.redirect(redirect_url)

        except Exception as e:
            _logger.error('******************* ACTUALIZACIÓN DE DOCUMENTO FALLIDA *******************')
            _logger.error('****** Archivo inválido o demasiado grande. Razón: %s ******', e)
            return request.redirect(redirect_url)