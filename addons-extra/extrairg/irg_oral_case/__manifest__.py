# -*- coding: utf-8 -*-
{
    'name': 'IRG Caso oral',
    'summary': 'Entrega de un caso oral de eLearning a n8n y confirmación docente de la nota',
    'version': '16.0.2.1.0',
    'category': 'Education',
    'author': 'Instituto Raimon Gaja',
    'license': 'LGPL-3',
    'depends': [
        'mail',
        'website_slides',
        'website_slides_survey',
        'survey',
        'isep_gradebook',
    ],
    'data': [
        'security/irg_oral_case_security.xml',
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'data/ir_cron.xml',
        'views/slide_slide_views.xml',
        'views/survey_user_input_views.xml',
        'views/oral_case_job_views.xml',
        'views/confirm_grade_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_oral_case/static/src/css/oral_case_player.css',
            'irg_oral_case/static/src/js/oral_case_logic.js',
            'irg_oral_case/static/src/js/oral_case_player.js',
        ],
    },
    'installable': True,
    'application': False,
}
