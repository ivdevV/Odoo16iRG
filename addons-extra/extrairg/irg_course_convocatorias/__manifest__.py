{
    'name': 'iRG Course Convocatorias',
    'version': '16.0.1.1.0',
    'category': 'Website/eLearning',
    'summary': 'Pestañas HomeClass y Online con convocatorias anuales en el formulario de curso',
    'author': 'iRG',
    'depends': [
        'website_slides',
        'openeducat_core',
        'irg_op_course_modality',
        'isep_elearning_custom',
        'irg_elearning_editable_sections',
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
