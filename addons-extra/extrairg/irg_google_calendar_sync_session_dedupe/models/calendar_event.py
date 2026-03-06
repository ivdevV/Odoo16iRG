import logging
import re

from odoo import models


_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def _sync_to_openeducat(self):
        self.ensure_one()
        strict_mode = self._is_strict_sync_enabled()

        if not self.google_event_id:
            return super()._sync_to_openeducat()

        if not self.name:
            return

        match = re.match(r'^\[(.*?)\]\s*(.*)$', self.name)
        if match:
            course_name = match.group(1).strip()
            subject_name = match.group(2).strip()
        elif self.name.startswith('['):
            course_name = self.name[1:].strip()
            subject_name = ''
        else:
            return

        Course = self.env['op.course']
        course = self._resolve_course_for_sync(course_name)
        if not course:
            if strict_mode:
                return self._sync_skip(f"Curso no encontrado (match exacto): '{course_name}'")
            course = Course.create({
                'name': course_name,
                'code': self._get_unique_code('op.course', course_name, 16),
                'evaluation_type': 'normal',
                'lang': self.env.user.lang or 'es_ES',
            })

        bloque_name = self._parse_bloque_from_description()
        search_subject_name = bloque_name if bloque_name else subject_name

        Subject = self.env['op.subject']
        subject = self._resolve_subject_for_sync(course, search_subject_name)
        if not subject:
            if strict_mode:
                return self._sync_skip(f"Asignatura no encontrada en el curso '{course.display_name}': '{search_subject_name}'")
            final_subject_name = bloque_name if bloque_name else subject_name
            subject = Subject.create({
                'name': final_subject_name,
                'code': self._get_unique_code('op.subject', final_subject_name, 256),
                'type': 'theory',
                'subject_type': 'compulsory',
            })

        if subject.id not in course.subject_ids.ids:
            course.write({'subject_ids': [(4, subject.id)]})

        faculty = self._find_or_create_faculty_from_description()
        batch = self._find_or_create_batch(course)
        if not batch:
            if strict_mode:
                return self._sync_skip(f"Lote no encontrado para el curso '{course.display_name}'")
            return

        Session = self.env['op.session']

        existing_session = Session.search([
            ('google_event_id', '=', self.google_event_id),
        ], limit=1)

        if not existing_session:
            legacy_domain = [
                ('start_datetime', '=', self.start),
                ('end_datetime', '=', self.stop),
                ('course_id', '=', course.id),
                ('subject_id', '=', subject.id),
                ('batch_id', '=', batch.id),
            ]
            if faculty:
                legacy_domain.append(('faculty_id', '=', faculty.id))

            legacy_sessions = Session.search(legacy_domain, order='id asc')
            if legacy_sessions:
                existing_session = legacy_sessions[0]
                if not existing_session.google_event_id:
                    existing_session.google_event_id = self.google_event_id
                if len(legacy_sessions) > 1:
                    _logger.warning(
                        'Google sync duplicates detected for %s: %s sessions',
                        self.google_event_id,
                        len(legacy_sessions),
                    )

        session_vals = {
            'start_datetime': self.start,
            'end_datetime': self.stop,
            'course_id': course.id,
            'subject_id': subject.id,
            'batch_id': batch.id,
            'faculty_id': faculty.id if faculty else self._get_default_faculty(),
            'google_event_id': self.google_event_id,
        }

        meeting_url = self.videocall_location
        if not meeting_url:
            meeting_url = self._parse_url_from_description()
        if meeting_url:
            meeting_url = meeting_url.strip().strip('"').strip("'")
            for field_name in ['time_url_metting', 'time_url_meeting', 'attendee_meeting_url', 'meeting_url', 'url']:
                if field_name in Session._fields:
                    session_vals[field_name] = meeting_url
                    break

        if existing_session:
            existing_session.write(session_vals)
            msg = f'Sincronización OpenEducat: Sesión actualizada ({existing_session.name})'
        else:
            session = Session.create(session_vals)
            msg = f'Sincronización OpenEducat: Sesión creada ({session.name})'

        if hasattr(self, 'message_post'):
            self.message_post(body=msg)
