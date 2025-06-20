{
    'name': "Isep - Elearning Custom",
    'summary': """
        Personalizaciones de Isep para Elearning""",
    'description': """
        Personalizaciones de Isep para Elearning""",
    'author': "HFoc - Hans Franco Olivos Cerna",
    'website': "https://universidadisep.com",
    'category': 'Openeducat',
    'version': '16.0.1',
    'depends': ['website_slides','isep_openeducat_custom','openeducat_core','openeducat_admission','openeducat_core_enterprise','openeducat_admission_enterprise'],
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/op_admission_welcome.xml',        
        'views/op_admission_email.xml',        
        'views/op_subject.xml',
        'views/slide_channel.xml',        
        'views/op_admission_elearning_wizard.xml',
        'views/slide_channel_partner.xml',
        'views/op_admission.xml',
        'views/op_admission_register.xml',
        'views/op_course.xml',
        
    ],    
    'installable': True,
    'application': False,
}
