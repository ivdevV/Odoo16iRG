# -*- coding: utf-8 -*-
{
    'name': 'IRG Course eLearning Featured Section',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Show a course-level featured block across related eLearning subjects',
    'description': """
        Adds a single featured eLearning block to OpenEduCat courses and
        displays it at the top of every linked website_slides subject channel.
    """,
    'author': 'iRG',
    'website': '',
    'depends': [
        'website_slides',
        'openeducat_core',
        'isep_elearning_custom',
    ],
    'data': [
        'views/op_course_views.xml',
        'views/website_slides_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_course_elearning_featured_section/static/src/scss/featured_section.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
