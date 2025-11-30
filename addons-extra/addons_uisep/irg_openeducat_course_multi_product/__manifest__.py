{
    'name': 'OpenEducat Course Multi Product',
    'version': '16.0.1.0.0',
    'category': 'OpenEducat',
    'summary': 'Allow multiple products per course',
    'description': """
        This module allows associating multiple products with a single OpenEducat course.
        It replaces the single product_template_id with a many2many relationship.
    """,
    'author': 'Antigravity',
    'depends': [
        'openeducat_core',
        'isep_openeducat_sale',
    ],
    'data': [
        'views/op_course.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
