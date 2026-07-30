# -*- coding: utf-8 -*-
"""Migración previa a convertir ``op.student.birth_date`` en related almacenado.

Orden de los acontecimientos, que es lo delicado:

1. Este hook corre **antes** de que Odoo cargue el modelo con el campo ya
   convertido en ``related='partner_id.birth_date'``.
2. En cuanto el campo pasa a ser related almacenado, Odoo **recalcula las 978
   filas** copiando el valor del contacto sobre el alumno.

Ese recálculo arregla solo los casos en que el contacto tiene la fecha buena y el
alumno la tiene corrupta. Pero **destruiría** el caso contrario: alumno con fecha
buena y contacto con basura. Por eso hay que rescatar esos primero, aquí, mientras
el alumno sigue siendo la fuente.
"""
import logging

_logger = logging.getLogger(__name__)

#: Valor centinela que los fallbacks del wizard escribían cuando no había fecha.
FABRICATED_DATE = '2000-01-01'

#: Por debajo de este año consideramos la fecha plausible. Las fechas corruptas
#: conocidas son la propia fecha de creación del registro (2026) y el 2000-01-01.
PLAUSIBLE_BEFORE = '2020-01-01'


def _is_garbage_sql(alias):
    """Fragmento SQL: la fecha de `alias` es basura conocida, no un dato real."""
    return (
        f"({alias}.birth_date IS NULL"
        f" OR {alias}.birth_date = DATE '{FABRICATED_DATE}'"
        f" OR {alias}.birth_date >= DATE '{PLAUSIBLE_BEFORE}'"
        f" OR {alias}.birth_date = {alias}.create_date::date)"
    )


def pre_init_hook(cr):
    """Sube al contacto la fecha buena que solo existe en el alumno."""
    cr.execute(
        f"""
        UPDATE res_partner p
           SET birth_date = s.birth_date
          FROM op_student s
         WHERE s.partner_id = p.id
           AND NOT {_is_garbage_sql('s')}
           AND {_is_garbage_sql('p')}
        """
    )
    rescued = cr.rowcount
    _logger.info(
        "IRG birth_date: %s contactos recuperados desde la ficha del alumno antes "
        "de convertir el campo en related.", rescued)

    # Diagnóstico: cuántos quedan sin fecha real en ninguno de los dos lados.
    cr.execute(
        f"""
        SELECT count(*)
          FROM op_student s
          LEFT JOIN res_partner p ON p.id = s.partner_id
         WHERE {_is_garbage_sql('s')} AND {_is_garbage_sql('p')}
        """
    )
    lost = cr.fetchone()[0]
    if lost:
        _logger.warning(
            "IRG birth_date: %s alumnos sin fecha de nacimiento recuperable en Odoo. "
            "Hay que pedirla de nuevo; el filtro 'Sin fecha de nacimiento' del listado "
            "de alumnos los lista.", lost)


def post_init_hook(cr, registry):
    """Alinea la columna del alumno con la del contacto.

    Hace falta porque **Odoo no recalcula una columna preexistente** al convertir el
    campo en related almacenado: solo computa las filas cuyo valor es NULL. Como
    ``op_student.birth_date`` ya existía con datos, las divergencias antiguas
    sobrevivirían indefinidamente a la instalación, y la columna almacenada —que
    leen varios informes por SQL crudo— seguiría mintiendo.

    Se ejecuta después del ``pre_init_hook``, así que a estas alturas el contacto ya
    tiene el mejor valor disponible de los dos y puede mandar sin perder nada.
    """
    cr.execute(
        """
        UPDATE op_student s
           SET birth_date = p.birth_date
          FROM res_partner p
         WHERE p.id = s.partner_id
           AND s.birth_date IS DISTINCT FROM p.birth_date
        """
    )
    _logger.info(
        "IRG birth_date: %s fichas de alumno alineadas con la fecha del contacto.",
        cr.rowcount)
