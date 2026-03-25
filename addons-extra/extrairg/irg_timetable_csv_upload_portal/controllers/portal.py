# -*- coding: utf-8 -*-
import csv
import io
import logging
import os
import shutil
from datetime import datetime

from odoo import _
from odoo.exceptions import AccessError, ValidationError
from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)

# Límite de tamaño: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Columnas requeridas en el CSV
REQUIRED_COLUMNS = {
    'máster/programa',
    'fecha',
    'nombre asignatura',
    'docente',
}


class TimetableCSVUploadController(Controller):
    """Controlador para upload web de calendarios."""

    def _check_access(self):
        """Valida que el usuario sea gestor o admin.
        
        Lanza AccessError si el usuario no tiene permisos.
        """
        user = request.env.user
        
        # Permitir: website.group_website_publisher (gestor de sitio)
        #          o base.group_erp_manager (admin Odoo)
        is_manager = user.has_group('website.group_website_publisher')
        is_admin = user.has_group('base.group_erp_manager')
        
        if not (is_manager or is_admin):
            raise AccessError(
                _('Acceso denegado. Solo gestores y administradores pueden subir calendarios.')
            )

    @route('/campus/csv-upload', auth='user', website=True)
    def upload_page(self, **kwargs):
        """Página de upload de CSV.
        
        GET: muestra formulario + historial de últimos 5 uploads
        """
        try:
            self._check_access()
        except AccessError as e:
            return request.render('website.403', {'error': str(e)})

        # Obtener últimos 5 uploads del usuario actual
        CSVUpload = request.env['irg.timetable.csv.upload']
        uploads = CSVUpload.search([], limit=5)

        # Contexto para template
        values = {
            'uploads': uploads,
            'user': request.env.user,
        }

        return request.render(
            'irg_timetable_csv_upload_portal.portal_upload_page',
            values,
        )

    @route(
        '/campus/csv-upload/action',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def upload_action(self, **kwargs):
        """Procesa el upload del archivo CSV.
        
        POST: valida, almacena, copia a watch_dir y redirige
        """
        try:
            self._check_access()
        except AccessError as e:
            return request.render('website.403', {'error': str(e)})

        # Recuperar archivo
        csv_file = request.files.get('csv_file')
        if not csv_file:
            return self._upload_error('No se seleccionó ningún archivo.')

        filename = csv_file.filename.strip()
        file_content = csv_file.read()

        # ─── Validaciones ───────────────────────────────────────────────
        error = self._validate_csv_file(filename, file_content)
        if error:
            return self._upload_error(error)

        # ─── Decodificar CSV ────────────────────────────────────────────
        try:
            text_content = file_content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                return self._upload_error(
                    'El archivo no está codificado en UTF-8. '
                    'Guarda el CSV con codificación UTF-8.'
                )

        # ─── Validar columnas ───────────────────────────────────────────
        error = self._validate_csv_columns(text_content)
        if error:
            return self._upload_error(error)

        # ─── Crear registro de upload ────────────────────────────────────
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f'{timestamp}_{filename}'
            
            CSVUpload = request.env['irg.timetable.csv.upload']
            upload_record = CSVUpload.sudo().create({
                'name': safe_filename,
                'file_size': len(file_content),
                'state': 'pending',
            })

            _logger.info(
                'irg_timetable_csv_upload_portal: Upload creado [%d] por %s',
                upload_record.id, request.env.user.name,
            )

        except Exception as e:
            _logger.exception('Error creando registro de upload')
            return self._upload_error(
                f'Error al guardar el upload: {str(e)}'
            )

        # ─── Copiar a watch_dir ────────────────────────────────────────
        error = self._copy_to_watch_dir(safe_filename, text_content, upload_record)
        if error:
            return self._upload_error(error)

        # ─── Redirigir con mensaje de éxito ─────────────────────────────
        return request.redirect(
            f'/campus/csv-upload?success={upload_record.id}'
        )

    # ─── Métodos auxiliares ──────────────────────────────────────────────

    def _validate_csv_file(self, filename, content):
        """Valida extensión y tamaño del archivo.
        
        Returns:
            str: mensaje de error si hay problema, None si OK
        """
        if not filename.lower().endswith('.csv'):
            return 'El archivo debe ser un CSV (.csv).'

        if len(content) > MAX_FILE_SIZE_BYTES:
            size_mb = len(content) / (1024 * 1024)
            return f'El archivo es muy grande ({size_mb:.1f} MB). Máximo: 10 MB.'

        if len(content) == 0:
            return 'El archivo está vacío.'

        return None

    def _validate_csv_columns(self, text_content):
        """Valida que el CSV tenga las columnas requeridas.
        
        Returns:
            str: mensaje de error si faltan columnas, None si OK
        """
        try:
            reader = csv.reader(
                io.StringIO(text_content),
                delimiter=';' if text_content.count(';') >= text_content.count(',') else ',',
            )
            
            # Leer encabezado
            header_row = next(reader, None)
            if not header_row:
                return 'El archivo CSV está vacío o no tiene encabezado.'

            # Normalizar nombres de columnas
            header_lower = {col.strip().lower() for col in header_row}

            # Verificar columnas requeridas
            missing = REQUIRED_COLUMNS - header_lower
            if missing:
                return (
                    f'Faltan columnas requeridas: {", ".join(sorted(missing))}. '
                    f'El CSV debe tener: {", ".join(sorted(REQUIRED_COLUMNS))}'
                )

            return None

        except Exception as e:
            return f'Error al validar el CSV: {str(e)}'

    def _copy_to_watch_dir(self, filename, text_content, upload_record):
        """Copia el archivo a watch_dir para procesamiento.
        
        Args:
            filename (str): nombre del archivo (con timestamp)
            text_content (str): contenido decodificado del CSV
            upload_record (irg.timetable.csv.upload): registro creado
            
        Returns:
            str: mensaje de error si hay problema, None si OK
        """
        ICP = request.env['ir.config_parameter'].sudo()
        watch_dir = ICP.get_param('irg_timetable_csv_import.watch_dir', '')

        if not watch_dir:
            upload_record.sudo().write({
                'state': 'error',
                'error_message': (
                    'watch_dir no configurado en el servidor. '
                    'Contacta al administrador.'
                ),
            })
            return (
                'Error: El directorio de procesamiento no está configurado en el servidor. '
                'Contacta al administrador.'
            )

        if not os.path.isdir(watch_dir):
            upload_record.sudo().write({
                'state': 'error',
                'error_message': f'watch_dir no existe: {watch_dir}',
            })
            return (
                'Error: El directorio de procesamiento no existe en el servidor. '
                'Contacta al administrador.'
            )

        # Escribir el archivo
        try:
            file_path = os.path.join(watch_dir, filename)
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write(text_content)

            upload_record.sudo().write({
                'state': 'processing',
            })

            _logger.info(
                'irg_timetable_csv_upload_portal: Archivo copiado a watch_dir: %s',
                file_path,
            )

            return None

        except Exception as e:
            _logger.exception('Error copiando archivo a watch_dir')
            upload_record.sudo().write({
                'state': 'error',
                'error_message': f'Error al copiar archivo: {str(e)}',
            })
            return f'Error al procesar el archivo: {str(e)}'

    def _upload_error(self, message):
        """Renderiza página de error con mensaje.
        
        Args:
            message (str): mensaje de error a mostrar
        """
        self._check_access()  # Validar acceso nuevamente

        CSVUpload = request.env['irg.timetable.csv.upload']
        uploads = CSVUpload.search([], limit=5)

        values = {
            'error': message,
            'uploads': uploads,
            'user': request.env.user,
        }

        return request.render(
            'irg_timetable_csv_upload_portal.portal_upload_page',
            values,
        )
