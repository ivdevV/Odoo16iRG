import re
import logging
import random
import requests
from datetime import datetime, timedelta, timezone
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    google_event_id = fields.Char(string='Google Event ID', index=True, copy=False)

    @api.model
    def _cron_sync_google_calendar(self):
        """Cron job to sync events from Google Calendar"""
        ICP = self.env['ir.config_parameter'].sudo()
        
        enabled = ICP.get_param('irg_google_calendar_sync.enabled', 'False')
        if enabled.lower() != 'true':
            _logger.info("Google Calendar sync is disabled")
            return
        
        api_key = ICP.get_param('irg_google_calendar_sync.api_key', '')
        calendar_id = ICP.get_param('irg_google_calendar_sync.calendar_id', '')
        sync_days = int(ICP.get_param('irg_google_calendar_sync.sync_days', '730'))
        
        if not api_key or not calendar_id:
            _logger.warning("Google Calendar sync: API Key or Calendar ID not configured")
            return
        
        _logger.info(f"Starting Google Calendar sync for calendar: {calendar_id}")
        
        try:
            self._fetch_and_sync_google_events(api_key, calendar_id, sync_days)
        except Exception as e:
            _logger.error(f"Error syncing Google Calendar: {str(e)}")

    def _fetch_and_sync_google_events(self, api_key, calendar_id, sync_days):
        """Fetch events from Google Calendar API and create/update in Odoo"""
        
        # Calculate time range
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=sync_days)).isoformat() + 'Z'
        
        # Google Calendar API endpoint
        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        
        base_params = {
            'key': api_key,
            'timeMin': time_min,
            'timeMax': time_max,
            'singleEvents': 'true',
            'orderBy': 'startTime',
            'maxResults': 250,
        }

        events = []
        next_page_token = None
        page_count = 0

        while True:
            params = dict(base_params)
            if next_page_token:
                params['pageToken'] = next_page_token

            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 200:
                _logger.error(f"Google Calendar API error: {response.status_code} - {response.text}")
                return

            data = response.json()
            page_events = data.get('items', [])
            events.extend(page_events)
            page_count += 1

            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break

        _logger.info(f"Fetched {len(events)} events from Google Calendar in {page_count} page(s)")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for g_event in events:
            try:
                summary = g_event.get('summary', '')
                _logger.info(f"Processing event: {summary[:80]}...")
                result = self._process_google_event(g_event)
                if result == 'created':
                    created_count += 1
                elif result == 'updated':
                    updated_count += 1
                else:
                    skipped_count += 1
                    _logger.info(f"Event skipped: {summary[:50]}... (reason: {result})")
            except Exception as e:
                _logger.error(f"Error processing Google event {g_event.get('id')}: {str(e)}")
        
        _logger.info(f"Google Calendar sync completed: {created_count} created, {updated_count} updated, {skipped_count} skipped")

    def _process_google_event(self, g_event):
        """Process a single Google Calendar event"""
        google_event_id = g_event.get('id')
        summary = g_event.get('summary', '')
        description = g_event.get('description', '')
        
        if not summary:
            _logger.warning("Skipping event with empty summary")
            return 'skipped_format'
        
        # Normalize brackets (some systems use different unicode brackets)
        summary = summary.replace('［', '[').replace('］', ']')
        
        # Try to match [Course] Subject format
        match = re.match(r'^\[(.+?)\]\s*(.*)$', summary)
        
        if not match:
            # Handle case where title is too long and ] is missing
            # If starts with [ treat everything as course name, subject will come from Bloque
            if summary.startswith('['):
                # Extract course name without the opening bracket
                course_name = summary[1:].strip()
                _logger.info(f"Event title missing ']' - using full title as course: {course_name[:50]}...")
                # We'll process it but need to handle differently in the vals
                match = None  # Will use special handling below
            else:
                _logger.warning(f"Skipping event - doesn't start with [: {summary[:100]}")
                return 'skipped_format'
        
        # Parse start/end times
        start_data = g_event.get('start', {})
        end_data = g_event.get('end', {})
        
        if 'dateTime' in start_data:
            # Timed event
            start_str = start_data['dateTime']
            end_str = end_data.get('dateTime', start_str)
            allday = False
            
            # Parse ISO format datetime
            start_dt = self._parse_google_datetime(start_str)
            end_dt = self._parse_google_datetime(end_str)
        elif 'date' in start_data:
            # All-day event
            start_dt = datetime.strptime(start_data['date'], '%Y-%m-%d')
            end_dt = datetime.strptime(end_data.get('date', start_data['date']), '%Y-%m-%d')
            allday = True
        else:
            _logger.warning(f"Event {google_event_id} has no valid start time")
            return 'skipped'
        
        # Check if event already exists
        existing = self.search([('google_event_id', '=', google_event_id)], limit=1)
        
        # Get video call URL from Google Meet
        video_url = ''
        hangout_link = g_event.get('hangoutLink', '')
        if hangout_link:
            video_url = hangout_link
        
        # Also check conferenceData
        conference_data = g_event.get('conferenceData', {})
        entry_points = conference_data.get('entryPoints', [])
        for ep in entry_points:
            if ep.get('entryPointType') == 'video':
                video_url = ep.get('uri', video_url)
                break
        
        # Build description with video URL if not already there
        full_description = description
        if video_url and 'Enlace a clase' not in full_description:
            full_description = f'{description}<p>Enlace a clase: "{video_url}"</p>' if description else f'<p>Enlace a clase: "{video_url}"</p>'
        
        vals = {
            'name': summary,
            'description': full_description,
            'start': start_dt,
            'stop': end_dt,
            'allday': allday,
            'google_event_id': google_event_id,
        }
        
        # Add video URL to videocall_location if field exists
        if video_url and 'videocall_location' in self._fields:
            vals['videocall_location'] = video_url
        
        if existing:
            # Check if update is needed
            if (existing.name != summary or 
                existing.start != start_dt or 
                existing.stop != end_dt or
                existing.description != full_description):
                existing.write(vals)
                _logger.info(f"Updated event: {summary}")
                return 'updated'
            _logger.info(f"Event unchanged, skipping: {summary[:50]}...")
            return 'skipped_unchanged'
        else:
            # Create new event
            new_event = self.create(vals)
            _logger.info(f"Created event from Google: {summary} (ID: {new_event.id})")
            return 'created'

    def _parse_google_datetime(self, dt_str):
        """Parse Google Calendar datetime format"""
        # Google returns ISO 8601 with timezone (e.g. +01:00 or Z).
        # Odoo stores datetime as naive UTC, so we must preserve tz and convert.
        raw_value = (dt_str or '').strip()

        # Python's fromisoformat doesn't always accept trailing Z in all versions.
        if raw_value.endswith('Z'):
            raw_value = f"{raw_value[:-1]}+00:00"

        try:
            parsed_dt = datetime.fromisoformat(raw_value)
        except ValueError:
            # Fallback for uncommon payloads without timezone.
            if '.' in raw_value:
                raw_value = raw_value.split('.')[0]
            parsed_dt = datetime.strptime(raw_value, '%Y-%m-%dT%H:%M:%S')

        if parsed_dt.tzinfo:
            return parsed_dt.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed_dt

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
        Pattern: [Course Name] Subject Name  OR  [Course Name (without closing bracket)
        Description: Professor: Name, Bloque: Subject Name
        """
        self.ensure_one()
        if not self.name:
            return

        # Pattern: [Course Name] Subject Name
        match = re.match(r'^\[(.*?)\]\s*(.*)$', self.name)
        
        if match:
            course_name = match.group(1).strip()
            subject_name = match.group(2).strip()
        elif self.name.startswith('['):
            # Handle case where title is too long and ] is missing
            # Use everything after [ as course name, subject from Bloque
            course_name = self.name[1:].strip()
            subject_name = ''  # Will be filled from Bloque
            _logger.info(f"Event title missing ']' - using as course: {course_name[:50]}...")
        else:
            _logger.warning(f"Event '{self.name}' (ID: {self.id}) skipped OpenEducat sync: Title format does not match '[Course]'")
            return

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
            # Clean HTML first to work with plain text lines
            desc_text = self.description
            desc_text = re.sub(r'<(div|p|br|/p|/div)[^>]*>', '\n', desc_text, flags=re.IGNORECASE)
            desc_text = re.sub(r'<[^>]+>', '', desc_text)
            
            # Search line by line for Grupo/Lote/Batch
            pattern = r'(?:Grupo|Lote|Batch)\s*:\s*(\S+)'
            for line in desc_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    batch_name_from_desc = match.group(1).strip()
                    _logger.info(f"Found Batch/Grupo in description: {batch_name_from_desc}")
                    break

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

