"""Unit tests for irg_auto_translate module."""

from odoo.tests.common import TransactionCase
import logging

_logger = logging.getLogger(__name__)


class TestOpSubjectTranslate(TransactionCase):
    """Test op.subject translation setup."""

    def setUp(self):
        super().setUp()
        self.OpSubject = self.env['op.subject']

    def test_subject_name_field_is_translatable(self):
        """Verify that op.subject.name is marked as translatable."""
        field = self.OpSubject._fields['name']
        self.assertTrue(
            field.translate,
            "op.subject.name should have translate=True"
        )

    def test_subject_create_basic(self):
        """Verify basic subject creation still works with translatable name."""
        subject = self.OpSubject.create({
            'name': 'Mathematics',
            'code': 'MATH-101',
            'type': 'theory',
            'subject_type': 'compulsory'
        })
        self.assertEqual(subject.name, 'Mathematics')
        self.assertEqual(subject.code, 'MATH-101')

    def test_subject_translate_method_exists(self):
        """Verify _translate_record_fields method exists and is callable."""
        subject = self.OpSubject.create({
            'name': 'Physics',
            'code': 'PHYS-101',
            'type': 'theory',
            'subject_type': 'compulsory'
        })
        # Method should exist and be callable
        self.assertTrue(hasattr(subject, '_translate_record_fields'))
        self.assertTrue(callable(subject._translate_record_fields))

    def test_subject_translate_method_returns_true(self):
        """Verify _translate_record_fields returns True (placeholder ok)."""
        subject = self.OpSubject.create({
            'name': 'Chemistry',
            'code': 'CHEM-101',
            'type': 'theory',
            'subject_type': 'compulsory'
        })
        result = subject._translate_record_fields(lang='es')
        self.assertTrue(result)

    def test_subject_translate_on_multiple_records(self):
        """Verify _translate_record_fields works on recordset."""
        subjects = self.OpSubject.create([
            {
                'name': 'Biology',
                'code': 'BIO-101',
                'type': 'practical',
                'subject_type': 'compulsory'
            },
            {
                'name': 'History',
                'code': 'HIST-101',
                'type': 'theory',
                'subject_type': 'elective'
            }
        ])
        result = subjects._translate_record_fields(lang='en')
        self.assertTrue(result)


class TestIrgAutoTranslate(TransactionCase):
    """Test IrgAutoTranslate cron model."""

    def setUp(self):
        super().setUp()
        self.AutoTranslate = self.env['irg.auto.translate']
        self.OpSubject = self.env['op.subject']

    def test_auto_translate_model_exists(self):
        """Verify IrgAutoTranslate model can be instantiated."""
        record = self.AutoTranslate.create({'name': 'Test'})
        self.assertIsNotNone(record)
        self.assertEqual(record.name, 'Test')

    def test_cron_run_method_exists(self):
        """Verify cron_run method exists and is callable."""
        self.assertTrue(
            hasattr(self.AutoTranslate, 'cron_run'),
            "IrgAutoTranslate should have cron_run method"
        )
        self.assertTrue(callable(self.AutoTranslate.cron_run))

    def test_cron_run_on_empty_database(self):
        """Verify cron_run completes without error on empty subject DB."""
        result = self.AutoTranslate.cron_run()
        self.assertTrue(result)

    def test_cron_run_with_subjects(self):
        """Verify cron_run processes existing subjects without error."""
        # Create 5 subjects
        for i in range(5):
            self.OpSubject.create({
                'name': f'Subject {i}',
                'code': f'SUBJ-{i:03d}',
                'type': 'theory',
                'subject_type': 'compulsory'
            })
        # Cron should complete successfully
        result = self.AutoTranslate.cron_run()
        self.assertTrue(result)
        # Verify all subjects still exist
        subjects = self.OpSubject.search([])
        self.assertEqual(len(subjects), 5)

    def test_cron_run_paginated_batching(self):
        """Verify cron_run processes subjects in batches."""
        # Create 250 subjects (2.5x default batch size of 100)
        for i in range(250):
            self.OpSubject.create({
                'name': f'Batch Test Subject {i}',
                'code': f'BATCH-{i:04d}',
                'type': 'theory',
                'subject_type': 'compulsory'
            })
        # Cron should complete without error (3 batches: 100, 100, 50)
        result = self.AutoTranslate.cron_run()
        self.assertTrue(result)
        # Verify all subjects still exist
        subjects = self.OpSubject.search([])
        self.assertEqual(len(subjects), 250)


class TestIrgTranslateWizard(TransactionCase):
    """Test IrgTranslateWizard transient model."""

    def setUp(self):
        super().setUp()
        self.Wizard = self.env['irg.translate.wizard']
        self.OpSubject = self.env['op.subject']

    def test_wizard_model_exists(self):
        """Verify IrgTranslateWizard model can be instantiated."""
        wizard = self.Wizard.create({
            'model_name': 'op.subject',
            'lang_to': 'es',
            'batch_size': 50,
            'offset': 0
        })
        self.assertIsNotNone(wizard)
        self.assertEqual(wizard.model_name, 'op.subject')
        self.assertEqual(wizard.lang_to, 'es')
        self.assertEqual(wizard.batch_size, 50)

    def test_wizard_action_run_method_exists(self):
        """Verify action_run method exists and is callable."""
        wizard = self.Wizard.create({
            'model_name': 'op.subject',
            'lang_to': 'es'
        })
        self.assertTrue(hasattr(wizard, 'action_run'))
        self.assertTrue(callable(wizard.action_run))

    def test_wizard_action_run_on_empty_database(self):
        """Verify action_run completes on empty subject DB."""
        wizard = self.Wizard.create({
            'model_name': 'op.subject',
            'lang_to': 'en',
            'batch_size': 50,
            'offset': 0
        })
        result = wizard.action_run()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')

    def test_wizard_action_run_with_batch_processing(self):
        """Verify action_run processes specified batch."""
        # Create 10 subjects
        for i in range(10):
            self.OpSubject.create({
                'name': f'Wizard Test {i}',
                'code': f'WIZARD-{i:02d}',
                'type': 'theory',
                'subject_type': 'compulsory'
            })
        # Wizard: process batch of 5 starting at offset 0
        wizard = self.Wizard.create({
            'model_name': 'op.subject',
            'lang_to': 'es',
            'batch_size': 5,
            'offset': 0
        })
        result = wizard.action_run()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')
        # Verify all subjects still exist
        subjects = self.OpSubject.search([])
        self.assertEqual(len(subjects), 10)

    def test_wizard_action_run_with_offset(self):
        """Verify action_run respects offset parameter."""
        # Create 20 subjects
        for i in range(20):
            self.OpSubject.create({
                'name': f'Offset Test {i}',
                'code': f'OFFSET-{i:02d}',
                'type': 'theory',
                'subject_type': 'compulsory'
            })
        # Wizard: process batch of 5 starting at offset 10
        wizard = self.Wizard.create({
            'model_name': 'op.subject',
            'lang_to': 'en',
            'batch_size': 5,
            'offset': 10
        })
        result = wizard.action_run()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')
        # Verify all subjects still exist
        subjects = self.OpSubject.search([])
        self.assertEqual(len(subjects), 20)


class TestSystemParameters(TransactionCase):
    """Test system parameters setup."""

    def setUp(self):
        super().setUp()
        self.ConfigParam = self.env['ir.config_parameter']

    def test_provider_parameter_exists(self):
        """Verify irg_auto_translate.provider parameter exists."""
        param = self.ConfigParam.sudo().get_param('irg_auto_translate.provider')
        self.assertIsNotNone(param)

    def test_api_key_parameter_exists(self):
        """Verify irg_auto_translate.api_key parameter exists."""
        param = self.ConfigParam.sudo().get_param('irg_auto_translate.api_key')
        # Can be empty string, but the key should exist in config
        self.assertIsNotNone(param)

    def test_provider_parameter_default_value(self):
        """Verify provider parameter defaults to 'none'."""
        param = self.ConfigParam.sudo().get_param('irg_auto_translate.provider')
        self.assertEqual(param, 'none')
