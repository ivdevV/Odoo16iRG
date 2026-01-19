{
    'name': 'IRG Admissions by Student',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Create admissions using student_id if available',
    'description': """
        This module overrides the admission creation logic to prioritize the 'student_id' field
        on the Sale Order. If 'student_id' is set, the admission is created for that student.
        Otherwise, it defaults to the 'partner_id' (Customer).
        
        Also adds 'Student' column to Sale Order Lines view.
    """,
    'author': 'ISEP',
    'depends': [
        'sale',
        'isep_openeducat_sale',
        'irg_sale_order_extended', 
    ],
    'data': [
        'views/sale_order_line_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
