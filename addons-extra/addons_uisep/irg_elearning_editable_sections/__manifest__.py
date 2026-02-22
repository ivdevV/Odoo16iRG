{
    'name': 'iRG eLearning Editable Sections',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Secciones editables, elementos hijos y herencia de límites en eLearning',
    'author': 'iRG',
    'depends': [
        'website_slides',
        'irg_batch_slide_restrictions',
        'irg_elearning_scheduled',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/slide_channel_view.xml',
        'views/slide_slide_view.xml',
        'views/slide_slide_search_view.xml',
        'views/website_slides_section_visibility.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
