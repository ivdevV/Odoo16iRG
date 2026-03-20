{
    'name': 'IRG Phone Prefix Fix',
    'version': '16.0.2.0.0',
    'summary': 'Preserva el dígito "1" en números mexicanos +521... y evita asteriscos en el widget',
    'description': """
IRG Phone Prefix Fix
====================

Problema raíz
-------------
Google libphonenumber (usada por Odoo) trata +521XXXXXXXXXX como equivalente a
+52XXXXXXXXXX. El "1" era prefijo de larga distancia dentro de México, eliminado
por la IFT en 2020. La librería lo silencia sin error: el dígito simplemente desaparece.

Además, el widget JS "phone" en la vista del formulario hace su propio reformateo
en el navegador, por lo que incluso si Python devuelve el número correcto, el widget
puede volver a eliminar el "1" al enfocar/desenfocar el campo.

Soluciones implementadas
------------------------
1. Override Python de _phone_format en res.partner:
   Detecta si el usuario introdujo +521... y restaura el "1" tras la normalización.

2. Override XML de la vista del formulario de contacto:
   Cambia widget="phone" a widget="char" en los campos phone y mobile,
   eliminando el reformateo JS en el navegador.

Sobre los asteriscos (*****):
   fields.Char nunca genera asteriscos por sí solo. Solo aparecen si:
   a) Una vista XML tiene password="True" en el campo.
   b) El campo tiene groups="..." restringiendo el acceso de lectura.
   c) Un módulo enterprise de privacidad/anonimización hashea el valor en BD.
   Este módulo NO incluye password="True" en ninguna vista.
    """,
    'author': 'IRG',
    'depends': ['base', 'phone_validation'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
