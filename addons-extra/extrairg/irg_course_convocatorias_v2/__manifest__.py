{
    'name': 'iRG Course Convocatorias V2',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Separación robusta de pestañas HomeClass y Online con visualización nativa de contenidos',
    'author': 'iRG',
    'depends': [
        'website_slides',
        'website_slides_survey',
        'openeducat_core',
        'irg_op_course_modality',
        'isep_elearning_custom',
        'irg_elearning_editable_sections',
        'irg_op_subject_visibility',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/irg_course_convocatoria_views.xml',
        'views/slide_channel_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
