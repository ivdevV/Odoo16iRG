{
    'name': 'IRG Download Button Removal Fix',
    'version': '16.0.1.0.0',
    'summary': 'Removes the custom download button from eLearning slides',
    'category': 'Website/eLearning',
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'depends': [
        'website_slides',
        'website_slides_customizations', 
    ],
    'data': [
        'views/slide_remove_download.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OEEL-1',
}
