# -*- coding: utf-8 -*-
{
    'name': 'IRG - Fecha de nacimiento: fuente única',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'La fecha de nacimiento del alumno pasa a ser la del contacto; se elimina la fabricación de 01/01/2000.',
    'description': """
        La fecha de nacimiento vivía duplicada en dos columnas independientes,
        res.partner.birth_date y op.student.birth_date, sincronizadas solo por
        copias sueltas repartidas por cuatro módulos. Cuando alguna de esas copias
        no encontraba valor, escribía un 01/01/2000 inventado.

        Este módulo:
        - Convierte op.student.birth_date en related almacenado de
          partner_id.birth_date. Como op.admission.birth_date ya es related al
          mismo sitio, los tres pasan a ser EL MISMO dato y divergir se vuelve
          imposible por construcción.
        - Relaja el required de op.admission.birth_date, que era la razón por la
          que el código inventaba fechas para poder guardar.
        - Añade un filtro para localizar a los alumnos sin fecha real.

        El pre_init_hook rescata, antes de la conversión, los casos en que la fecha
        buena solo estaba en la ficha del alumno.
    """,
    'author': 'IRG',
    'website': 'https://www.irg.edu.es',
    'depends': [
        'openeducat_core',
        'openeducat_admission',
        'isep_record_request',
        'isep_openeducat_custom',
    ],
    'data': [
        'views/op_student_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
}
