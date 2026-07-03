{
    'name': 'ISEP Admission from Student Field',
    'version': '16.0.1.0.6',
    'category': 'Sales',
    'summary': 'Use existing student_id field from sale_order to create admissions',
    'description': """
        Este módulo modifica la lógica de creación de admisiones para usar el campo existente 'student_id'
        (definido en irg_sale_order_extended) en lugar de usar siempre el titular de la factura.
        
        Si el campo 'student_id' (Alumno) está informado en el pedido, la admisión se creará a su nombre.
        Si está vacío, se usará el cliente del pedido (partner_id).
    """,
    'author': 'ISEP',
    'depends': [
        'sale',
        'isep_openeducat_sale',
        'isep_sale_order_admissions',
        'isep_elearning_custom',  # IMPORTANTE: para que nuestro override de submit_form se aplique después
        'irg_sale_order_extended',
        'irg_admission_gender_fix',
    ],
    'data': [
        'views/sale_order_line_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
