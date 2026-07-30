# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBirthDateSingleSource(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Alumno Prueba',
            'email': 'alumno.prueba@test.com',
            'birth_date': '1990-05-17',
        })
        self.student = self.env['op.student'].create({
            'partner_id': self.partner.id,
            'first_name': 'Alumno',
            'last_name': 'Prueba',
            'gender': 'm',
        })

    # ------------------------------------------------------------------
    # Vinculación
    # ------------------------------------------------------------------
    def test_01_student_reads_partner_date(self):
        """El alumno no tiene fecha propia: lee la del contacto."""
        self.assertEqual(str(self.student.birth_date), '1990-05-17')

    def test_02_writing_on_partner_updates_student(self):
        self.partner.write({'birth_date': '1985-03-02'})
        self.student.invalidate_recordset()
        self.assertEqual(str(self.student.birth_date), '1985-03-02')

    def test_03_writing_on_student_updates_partner(self):
        """Editar en la ficha del alumno escribe en el contacto.

        Es la mitad que faltaba: antes eran dos columnas y editar una dejaba la
        otra con el valor viejo.
        """
        self.student.write({'birth_date': '1979-11-30'})
        self.partner.invalidate_recordset()
        self.assertEqual(str(self.partner.birth_date), '1979-11-30')

    def test_04_cannot_diverge(self):
        """No hay forma de dejarlas distintas: es el mismo dato."""
        self.student.write({'birth_date': '1992-01-08'})
        self.partner.write({'birth_date': '1992-01-08'})
        self.student.invalidate_recordset()
        self.partner.invalidate_recordset()
        self.assertEqual(self.student.birth_date, self.partner.birth_date)

    def test_05_stored_column_is_kept_in_sync(self):
        """`store=True` es obligatorio: hay informes que leen la columna por SQL."""
        self.partner.write({'birth_date': '1988-06-06'})
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT birth_date FROM op_student WHERE id = %s", (self.student.id,))
        stored = self.env.cr.fetchone()[0]
        self.assertEqual(str(stored), '1988-06-06')

    # ------------------------------------------------------------------
    # Nunca inventar
    # ------------------------------------------------------------------
    def test_06_empty_birth_date_is_allowed(self):
        """Sin fecha se puede guardar: es lo que evita que el código la fabrique."""
        partner = self.env['res.partner'].create({'name': 'Sin Fecha'})
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'Sin',
            'last_name': 'Fecha',
            'gender': 'm',
        })
        self.assertFalse(student.birth_date)

    def test_07_empty_date_does_not_crash_the_constraint(self):
        """El constraint del core hace `birth_date > today` y con False da TypeError."""
        partner = self.env['res.partner'].create({'name': 'Sin Fecha 2'})
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'Sin',
            'last_name': 'Fecha2',
            'gender': 'm',
        })
        # No debe lanzar nada.
        student._check_birthdate()
        self.assertFalse(student.birth_date)

    def test_08_future_date_is_still_rejected(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.partner.write({'birth_date': '2099-01-01'})
            self.student.invalidate_recordset()
            self.student._check_birthdate()

    # ------------------------------------------------------------------
    # Detección de huecos
    # ------------------------------------------------------------------
    def test_09_real_date_is_not_flagged(self):
        self.assertFalse(self.student.irg_birth_date_missing)

    def test_10_fabricated_date_is_flagged(self):
        self.partner.write({'birth_date': '2000-01-01'})
        self.student.invalidate_recordset()
        self.assertTrue(
            self.student.irg_birth_date_missing,
            "El 01/01/2000 que fabricaba el código antiguo debe contar como hueco")

    def test_11_creation_date_pattern_is_flagged(self):
        """El otro patrón corrupto: la fecha de creación del registro como nacimiento."""
        self.partner.write({'birth_date': '2026-06-22'})
        self.student.invalidate_recordset()
        self.assertTrue(self.student.irg_birth_date_missing)

    def test_12_missing_date_is_flagged(self):
        partner = self.env['res.partner'].create({'name': 'Vacio'})
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'Va',
            'last_name': 'Cio',
            'gender': 'm',
        })
        self.assertTrue(student.irg_birth_date_missing)

    def test_13_search_filter_finds_the_gaps(self):
        bad_partner = self.env['res.partner'].create({
            'name': 'Fabricado', 'birth_date': '2000-01-01'})
        bad_student = self.env['op.student'].create({
            'partner_id': bad_partner.id,
            'first_name': 'Fab', 'last_name': 'Ricado', 'gender': 'm',
        })
        found = self.env['op.student'].search([('irg_birth_date_missing', '=', True)])
        self.assertIn(bad_student, found)
        self.assertNotIn(self.student, found)

    def test_14_search_filter_negated(self):
        found = self.env['op.student'].search([('irg_birth_date_missing', '=', False)])
        self.assertIn(self.student, found)

    # ------------------------------------------------------------------
    # Edición desde la admisión
    # ------------------------------------------------------------------
    def test_15_admission_field_is_editable_and_optional(self):
        """La admisión debe poder editar la fecha, y no exigirla.

        `required` era la causa raíz de las fechas inventadas. `readonly` impedía
        corregir el dato desde la propia admisión salvo en estado 'done'; ahora que
        hay fuente única, escribir ahí actualiza el contacto y es seguro.
        """
        field = self.env['op.admission']._fields['birth_date']
        self.assertFalse(field.required, "No debe ser obligatoria: si no hay dato, se deja vacía")
        self.assertFalse(field.readonly, "Debe poder editarse desde la ficha de admisión")
        self.assertEqual(field.related, 'partner_id.birth_date')
        self.assertFalse(field.store, "Sigue sin columna propia: lee siempre del contacto")
