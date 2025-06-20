{
    'name': "Isep - Openeducat Sale Custom",
    'summary': """
        Personalizaciones de Isep para Openeducat""",
    'description': """
        Personalizaciones de Isep para Openeducat""",
    'author': "Hans Franco Olivos Cerna",
    'website': "https://universidadisep.com",
    'category': 'sale',
    'version': '16.0.1',
    'depends': ['openeducat_core','sale','openeducat_admission','openeducat_admission_enterprise','website_slides'],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'data': [
        'views/sale_order_line.xml',
        'views/op_admission.xml',
        'views/product_template.xml',
        'views/sale_order_line_views.xml',
        'views/slide_channel.xml',
    ],
    'installable': True,
    'application': False,
}
