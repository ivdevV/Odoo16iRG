# -*- coding: utf-8 -*-
MAX_PAYLOAD_BYTES = 65536
MAX_HTML_CHARS = 32768
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20
MAX_TITLE_CHARS = 200
ALLOWED_ENVIRONMENTS = ('test', 'beta')
SECRET_TOKENS = (
    'password', 'token', 'secret', 'api_key', 'apikey', 'access_token',
    'refresh_token', 'private_key', 'authorization', 'wstoken', 'smtp_pass',
    'datas', 'raw', 'bin_size',
)

OPERATION_CODES = [
    ('irg_list_academic_periods', 'List academic periods'),
    ('irg_list_courses', 'List courses'),
    ('irg_get_course_overview', 'Get course overview'),
    ('irg_get_course_batches', 'Get course batches'),
    ('irg_list_subjects', 'List subjects'),
    ('irg_get_course_structure', 'Get course structure'),
    ('irg_get_slide', 'Get slide'),
    ('irg_get_admission_overview', 'Get admission overview'),
    ('irg_get_admission_subject_openings', 'Get admission subject openings'),
    ('irg_get_student_access', 'Get student access'),
    ('irg_get_student_academic_360', 'Get student academic 360'),
    ('irg_get_gradebook_summary', 'Get gradebook summary'),
    ('irg_get_moodle_sync_status', 'Get Moodle sync status'),
    ('irg_get_survey_structure', 'Get survey structure'),
    ('irg_get_academic_incidents', 'Get academic incidents'),
    ('irg_create_slide_draft', 'Create unpublished article slide'),
    ('irg_update_slide_draft', 'Update unpublished article slide'),
    ('irg_create_course_section', 'Create course section'),
    ('irg_reorder_course_section', 'Reorder course sections'),
    ('irg_publish_slide', 'Publish a reviewed slide'),
    ('irg_unpublish_slide', 'Unpublish a slide'),
    ('irg_approve_operation', 'Approve a previewed operation'),
    ('irg_reject_operation', 'Reject a previewed operation'),
]

OPERATION_SPECS = {
    'irg_list_academic_periods': {'kind': 'read', 'keys': {'limit', 'offset'}},
    'irg_list_courses': {'kind': 'read', 'keys': {'limit', 'offset', 'name', 'code'}},
    'irg_get_course_overview': {'kind': 'read', 'keys': {'course_id'}},
    'irg_get_course_batches': {'kind': 'read', 'keys': {'course_id', 'limit', 'offset'}},
    'irg_list_subjects': {'kind': 'read', 'keys': {'course_id', 'limit', 'offset'}},
    'irg_get_course_structure': {'kind': 'read', 'keys': {'channel_id'}},
    'irg_get_slide': {'kind': 'read', 'keys': {'slide_id'}},
    'irg_get_admission_overview': {'kind': 'read', 'keys': {'admission_id'}},
    'irg_get_admission_subject_openings': {'kind': 'read', 'keys': {'admission_id'}},
    'irg_get_student_access': {'kind': 'read', 'keys': {'admission_id', 'partner_id'}},
    'irg_get_student_academic_360': {'kind': 'read', 'keys': {'admission_id'}},
    'irg_get_gradebook_summary': {'kind': 'read', 'keys': {'admission_id', 'partner_id'}},
    'irg_get_moodle_sync_status': {'kind': 'read', 'keys': {'course_id', 'admission_id'}},
    'irg_get_survey_structure': {'kind': 'read', 'keys': {'survey_id'}},
    'irg_get_academic_incidents': {'kind': 'read', 'keys': {'admission_id', 'course_id'}},
    'irg_create_slide_draft': {
        'kind': 'write',
        'keys': {'channel_id', 'name', 'html_content', 'sequence', 'irg_section_id', 'is_published'},
    },
    'irg_update_slide_draft': {
        'kind': 'write',
        'keys': {'slide_id', 'name', 'html_content', 'sequence', 'irg_section_id'},
    },
    'irg_create_course_section': {
        'kind': 'write',
        'keys': {'channel_id', 'name', 'sequence'},
    },
    'irg_reorder_course_section': {
        'kind': 'write',
        'keys': {'channel_id', 'section_ids'},
    },
    'irg_publish_slide': {'kind': 'write', 'keys': {'slide_id'}},
    'irg_unpublish_slide': {'kind': 'write', 'keys': {'slide_id'}},
    'irg_approve_operation': {'kind': 'meta', 'keys': {'operation_id'}},
    'irg_reject_operation': {'kind': 'meta', 'keys': {'operation_id'}},
}
