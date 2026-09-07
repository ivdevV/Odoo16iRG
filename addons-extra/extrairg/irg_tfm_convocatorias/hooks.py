from odoo.exceptions import ValidationError


def pre_init_hook(cr):
    """Reject an unsafe install before Odoo adds the thesis unique constraint."""
    cr.execute("""
        SELECT 1
          FROM ir_model_fields
         WHERE model = 'op.student.course'
           AND name = 'completion_proc'
         LIMIT 1
    """)
    if not cr.fetchone():
        raise ValidationError(
            'IRG TFM Convocatorias requires op.student.course.completion_proc. '
            'Install the module that provisions it before installing this addon.'
        )

    cr.execute("""
        SELECT course_id, count(*)
          FROM tesis_model
         GROUP BY course_id
        HAVING count(*) > 1
         LIMIT 1
    """)
    duplicate = cr.fetchone()
    if duplicate:
        raise ValidationError(
            'IRG TFM Convocatorias cannot install: tesis.model has multiple '
            'records for op.student.course id %s. Resolve duplicates manually; '
            'this addon never deletes or merges historical records.' % duplicate[0]
        )
