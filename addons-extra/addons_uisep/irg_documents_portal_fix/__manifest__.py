# -*- coding: utf-8 -*-
{
    'name': 'IRG Documents Portal Fix',
    'version': '16.0.1.0.0',
    'summary': 'Corrige el error de contador duplicado en el portal de documentos',
    'description': """
        Este módulo corrige el error:
        "Cannot set properties of null (setting 'textContent')"
        
        El problema ocurre porque hay dos módulos que definen contadores
        con nombres diferentes para la sección de documentos:
        - isep_record_request: usa 'documents_quantity'
        - isep_documents_portal: usa 'documents_count'
        
        Este módulo oculta la entrada duplicada de isep_record_request
        para evitar el conflicto.
    """,
    'author': 'IRG',
    'category': 'Website',
    'depends': [
        'portal',
        'isep_record_request',
        'isep_documents_portal',
    ],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
