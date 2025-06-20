{
    'name': "Isep - Sale subscription custom",
    'summary': """
        Sale subscription custom""",
    'description': """
        Sale subscription custom""",
    'author': "Hans Franco Olivos Cerna",
    'website': "https://universidadisep.com",
    'category': 'sale',
    'version': '16.0.1',
    'depends': ['sale_subscription','sales_team'],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/sale_order.xml',
    ],
    'installable': True,
    'application': False,
}
