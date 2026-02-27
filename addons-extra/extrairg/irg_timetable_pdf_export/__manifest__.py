{
    'name': 'IRG Timetable PDF Export',
    'version': '16.0.1.0.0',
    'summary': 'Descarga en PDF del calendario académico en portal',
    'category': 'Education',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_timetable_enterprise',
        'irg_op_session_class_title',
    ],
    'data': [
        'report/timetable_pdf_report.xml',
        'views/timetable_portal_pdf_button.xml',
    ],
    'installable': True,
    'application': False,
}
