import re
import logging
import random
from datetime import timedelta
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    @api.model_create_multi
    def create(self, vals_list):
        events = super().create(vals_list)
        for event in events:
            # We delay the sync to ensure all fields are computed/saved if needed
            event._sync_to_openeducat()
        return events

    def write(self, vals):
        res = super().write(vals)
        for event in self:
            event._sync_to_openeducat()
        return res

    def action_manual_sync_openeducat(self):
        """Allow manual triggering from the UI"""
        for event in self:
            _logger.info(f"Manual sync triggered for event: {event.name}")
            event._sync_to_openeducat()

    def _sync_to_openeducat(self):
        """
        Syncs the calendar event to OpenEduCat op.session if it matches the pattern.
        Pattern: [Course Name] Subject Name
        Description: Professor: Name
        """
        self.ensure_one()
        if not self.name:
            return

        # Pattern: [Course Name] Subject Name
        match = re.match(r'^\[(.*?)\]\s*(.*)$', self.name)
        if not match:
            _logger.warning(f"Event '{self.name}' (ID: {self.id}) skipped OpenEducat sync: Title format does not match '[Course] Subject'")
            return

        course_name = match.group(1).strip()
        subject_name = match.group(2).strip()

        # Find or Create Course
        Course = self.env['op.course']
        # First try to use courses already selected in the event (from calendar.event.course_ids)
        course = False
        if hasattr(self, 'course_ids') and self.course_ids:
            course = self.course_ids[0]
            _logger.info(f"Using course from event selection: {course.name}")
        
        if not course:
            # Normalize for accent-insensitive comparison using unaccent if available
            # Fallback: search by containment of key words
            course = Course.search([('name', 'ilike', course_name)], limit=1)
        
        if not course:
            # Try partial matching - extract key words
            key_words = [w for w in course_name.split() if len(w) > 4]
            for word in key_words[:3]:  # Try first 3 significant words
                course = Course.search([('name', 'ilike', word)], limit=1)
                if course:
                    _logger.info(f"Found course by keyword '{word}': {course.name}")
                    break
            
        if not course:
            course_code = self._get_unique_code('op.course', course_name, 16)
            course = Course.create({
                'name': course_name, 
                'code': course_code,
                'evaluation_type': 'normal',
                'lang': self.env.user.lang or 'es_ES'
            })
            _logger.info(f"Created new Course: {course.name} ({course.code})")

        # Parse "Bloque: ..." from description to use as subject name
        bloque_name = self._parse_bloque_from_description()
        search_subject_name = bloque_name if bloque_name else subject_name
        
        # Find or Create Subject
        Subject = self.env['op.subject']
        _logger.info(f"Searching for subject using: {search_subject_name}")
        
        # First try to find exact match
        subject = Subject.search([('name', '=', search_subject_name)], limit=1)
        
        if not subject:
            # Try ilike (partial/case-insensitive)
            subject = Subject.search([('name', 'ilike', search_subject_name)], limit=1)
            if subject:
                _logger.info(f"Found subject by ilike: {subject.name}")
        
        if not subject:
            # Try searching for significant parts (split by dash or comma)
            parts = re.split(r'[-,]', search_subject_name)
            for part in parts:
                part = part.strip()
                if len(part) > 10:  # Only meaningful parts
                    subject = Subject.search([('name', 'ilike', part)], limit=1)
                    if subject:
                        _logger.info(f"Found subject by part '{part}': {subject.name}")
                        break
        
        if not subject:
            # Try partial matching - extract key words (min 5 chars to be meaningful)
            key_words = [w for w in search_subject_name.split() if len(w) > 5]
            for word in key_words[:5]:
                subject = Subject.search([('name', 'ilike', word)], limit=1)
                if subject:
                    _logger.info(f"Found subject by keyword '{word}': {subject.name}")
                    break
        
        if not subject:
            # Create new subject - use bloque_name if available, else subject_name
            final_subject_name = bloque_name if bloque_name else subject_name
            subject_code = self._get_unique_code('op.subject', final_subject_name, 256)
            subject = Subject.create({
                'name': final_subject_name, 
                'code': subject_code,
                'type': 'theory', 
                'subject_type': 'compulsory'
            })
            _logger.info(f"Created new Subject: {subject.name} ({subject.code})")
        
        # Link Subject to Course (op.course has subject_ids)
        if subject.id not in course.subject_ids.ids:
            course.write({'subject_ids': [(4, subject.id)]})

        # Parse Description for Professor
        faculty = self._find_or_create_faculty_from_description()
        
        # Find or Create Batch
        batch = self._find_or_create_batch(course)

        # Create or Update Session
        Session = self.env['op.session']
        
        # Avoid duplicate sessions for the same event time/details
        domain = [
            ('start_datetime', '=', self.start),
            ('end_datetime', '=', self.stop),
            ('course_id', '=', course.id),
            ('subject_id', '=', subject.id),
            ('batch_id', '=', batch.id),
        ]
        if faculty:
            domain.append(('faculty_id', '=', faculty.id))
        
        existing_session = Session.search(domain, limit=1)
        
        session_vals = {
            'start_datetime': self.start,
            'end_datetime': self.stop,
            'course_id': course.id,
            'subject_id': subject.id,
            'batch_id': batch.id,
            'faculty_id': faculty.id if faculty else self._get_default_faculty(),
            # 'name' is computed
        }

        # Add Google Meet URL - Check for the correct field name
        meeting_url = self.videocall_location
        _logger.info(f"videocall_location = {meeting_url}")
        
        if not meeting_url:
            meeting_url = self._parse_url_from_description()
            _logger.info(f"URL from description = {meeting_url}")
        
        if meeting_url:
            # Clean URL if needed (remove trailing quotes, etc)
            meeting_url = meeting_url.strip().strip('"').strip("'")
            _logger.info(f"Final meeting_url = {meeting_url}")
            
            # The field is called time_url_metting (with typo in original module)
            # Try different field names that might exist in op.session
            url_fields = ['time_url_metting', 'time_url_meeting', 'attendee_meeting_url', 'meeting_url', 'url']
            for field_name in url_fields:
                if field_name in Session._fields:
                    session_vals[field_name] = meeting_url
                    _logger.info(f"Setting {field_name} = {meeting_url}")
                    break
                else:
                    _logger.debug(f"Field {field_name} not found in op.session")

        if existing_session:
            existing_session.write(session_vals)
            msg = f"Sincronización OpenEducat: Sesión actualizada ({existing_session.name})"
            _logger.info(f"Updated OpSession {existing_session.id} for event {self.name}")
        else:
            session = Session.create(session_vals)
            msg = f"Sincronización OpenEducat: Sesión creada ({session.name})"
            _logger.info(f"Created OpSession {session.id} for event {self.name}")
        
        # Post message to chatter if available
        if hasattr(self, 'message_post'):
            self.message_post(body=msg)

    def _get_unique_code(self, model_name, base_name, size_limit):
        """Generates a unique code based on the base_name."""
        Model = self.env[model_name]
        # Cleanup name to be code-like
        base_code = re.sub(r'[^A-Z0-9]', '', base_name.upper()) 
        if not base_code:
            base_code = "CODE"
        
        # Truncate
        base_code = base_code[:size_limit-4] # Reserve space for suffix
        
        code = base_code
        if not Model.search_count([('code', '=', code)]):
            return code
            
        counter = 1
        while True:
            suffix = f"{counter:03d}"
            # Ensure we don't exceed limit
            truncated_base = base_code[:size_limit - len(suffix)]
            new_code = f"{truncated_base}{suffix}"
            if not Model.search_count([('code', '=', new_code)]):
                return new_code
            counter += 1

    def _find_or_create_faculty_from_description(self):
        """
        Parses description for 'Professor: Name' or 'Profesor: Name' or 'Profesor/a: Name'
        """
        if not self.description:
            return None
        
        # Clean HTML to text-like format for easier parsing
        desc_text = self.description
        # Replace block endings with newlines
        desc_text = re.sub(r'<(div|p|br|/p|/div)[^>]*>', '\n', desc_text, flags=re.IGNORECASE)
        # Remove remaining tags
        desc_text = re.sub(r'<[^>]+>', '', desc_text)
        
        faculty_name = None
        # Use regex to find lines starting with Professor keywords
        # Matches "Profesor:", "Profesor/a:", "Docente:", "Professor:"
        pattern = r'(?:Profesor(?:/a)?|Professor|Docente)\s*:\s*(.*)'
        
        lines = desc_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                faculty_name = match.group(1).strip()
                # Stop reading if we hit another keyword or just take the first meaningful part
                # In case "Professor: Name Link: ..." 
                # (Though with newline replacement this is less likely)
                break

        if faculty_name:
            Faculty = self.env['op.faculty']
            
            # Search loosely
            domain = ['|', '|', ('first_name', 'ilike', faculty_name), ('last_name', 'ilike', faculty_name), ('name', 'ilike', faculty_name)]
            
            # Let's search on partner_id.name via 'name' (inherits)
            faculty = Faculty.search([('name', 'ilike', faculty_name)], limit=1)
            
            if not faculty:
                parts = faculty_name.split()
                first_name = parts[0]
                last_name = ' '.join(parts[1:]) if len(parts) > 1 else 'Professor'
                
                # Check for "Prof." prefix
                if first_name.lower().replace('.', '') in ['prof', 'dr', 'mr', 'ms', 'mrs']:
                     if len(parts) > 1:
                        first_name = parts[1]
                        last_name = ' '.join(parts[2:]) if len(parts) > 2 else 'Professor'

                # Ensure we have a valid name to avoid constraint errors
                full_name = f"{first_name} {last_name}"
                
                faculty = Faculty.create({
                    'name': full_name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'birth_date': '1980-01-01', 
                    'gender': 'male', 
                })
                _logger.info(f"Created new Faculty: {faculty.name}")
            return faculty
        return None

    def _get_default_faculty(self):
        Faculty = self.env['op.faculty']
        faculty = Faculty.search([('last_name', '=', 'Professor'), ('first_name', '=', 'Unknown')], limit=1)
        if not faculty:
            faculty = Faculty.create({
                'name': 'Unknown Professor',
                'first_name': 'Unknown',
                'last_name': 'Professor',
                'birth_date': '1980-01-01',
                'gender': 'male',
            })
        return faculty.id

    def _parse_bloque_from_description(self):
        """
        Parses description for 'Bloque: Name' to use as subject name.
        Returns the bloque name or None if not found.
        """
        if not self.description:
            return None
        
        # Clean HTML to text-like format for easier parsing
        desc_text = self.description
        # Replace block endings with newlines
        desc_text = re.sub(r'<(div|p|br|/p|/div)[^>]*>', '\n', desc_text, flags=re.IGNORECASE)
        # Remove remaining tags
        desc_text = re.sub(r'<[^>]+>', '', desc_text)
        
        # Match "Bloque: ..." or "Asignatura: ..." or "Materia: ..."
        pattern = r'(?:Bloque|Asignatura|Materia)\s*:\s*(.*)'
        
        lines = desc_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                bloque_name = match.group(1).strip()
                if bloque_name:
                    _logger.info(f"Found Bloque in description: {bloque_name}")
                    return bloque_name
        
        return None

    def _parse_url_from_description(self):
        if not self.description:
            return None
        
        # Clean HTML first
        desc_text = self.description
        # Extract href values from anchor tags
        href_pattern = r'href=["\']?(https?://[^"\'>\s]+)["\']?'
        href_match = re.search(href_pattern, desc_text, re.IGNORECASE)
        if href_match:
            url = href_match.group(1)
            _logger.info(f"Found URL in href: {url}")
            return url
        
        # Fallback: Enlace a clase: "url"
        pattern = r'(?:Enlace a clase|Link|Videollamada|meet\.google\.com)\s*:?\s*["\']?(https?://[^\s"\'<>]+)["\']?'
        match = re.search(pattern, desc_text, re.IGNORECASE)
        if match:
            url = match.group(1)
            _logger.info(f"Found URL in text: {url}")
            return url
        
        # Try to find any Google Meet URL
        meet_pattern = r'(https?://meet\.google\.com/[a-z\-]+)'
        meet_match = re.search(meet_pattern, desc_text, re.IGNORECASE)
        if meet_match:
            url = meet_match.group(1)
            _logger.info(f"Found Google Meet URL: {url}")
            return url
            
        return None

    def _find_or_create_batch(self, course):
        Batch = self.env['op.batch']
        event_date = self.start.date()
        
        # 1. Try to parse "Grupo: XYZ" or "Lote: XYZ" from description
        batch_name_from_desc = None
        if self.description:
            pattern = r'(?:Grupo|Lote|Batch)\s*:\s*(.*)'
            match = re.search(pattern, self.description, re.IGNORECASE)
            if match:
                batch_name_from_desc = match.group(1).strip()
                # Remove HTML tags if any
                batch_name_from_desc = re.sub('<[^<]+?>', '', batch_name_from_desc).strip()

        if batch_name_from_desc:
             # Search by code or name
             batch = Batch.search(['|', ('code', '=', batch_name_from_desc), ('name', '=', batch_name_from_desc)], limit=1)
             if batch:
                 return batch
             else:
                 # Create it with this code
                 # We need start/end dates. Default to current year.
                 year = self.start.year
                 batch_code = batch_name_from_desc
                 if len(batch_code) > 16:
                     # If too long for code, try to generate a code
                     batch_code = self._get_unique_code('op.batch', batch_name_from_desc, 16)
                 
                 # Ensure uniqueness
                 if Batch.search_count([('code', '=', batch_code)]):
                      batch_code = self._get_unique_code('op.batch', batch_code, 16)

                 batch = Batch.create({
                    'name': batch_name_from_desc,
                    'code': batch_code,
                    'course_id': course.id,
                    'start_date': f"{year}-01-01",
                    'end_date': f"{year}-12-31"
                 })
                 _logger.info(f"Created new Batch from description: {batch.name}")
                 return batch

        # 2. Standard Logic
        batches = Batch.search([
            ('course_id', '=', course.id),
            ('start_date', '<=', event_date),
            ('end_date', '>=', event_date)
        ])
        
        if batches:
            return batches[0]
            
        # Fallback: Create a batch for the current year
        year = event_date.year
        batch_name = f"{course.name} - {year}"
        
        batch_code = self._get_unique_code('op.batch', f"{course.code}-{year}", 16)
        
        batch = Batch.create({
            'name': batch_name,
            'code': batch_code,
            'course_id': course.id,
            'start_date': f"{year}-01-01",
            'end_date': f"{year}-12-31"
        })
        _logger.info(f"Created new Batch: {batch.name}")
        
        return batch

