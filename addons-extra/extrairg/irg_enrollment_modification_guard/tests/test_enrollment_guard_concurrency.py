"""Real two-connection scenarios; invoked by the mission Odoo-shell wrapper.

Use only the disposable database prepared by prepare_red.py.
"""

def run(env):
    import json
    import threading
    import time
    from unittest.mock import patch
    from psycopg2.errors import SerializationFailure
    from odoo import api, SUPERUSER_ID
    from odoo.exceptions import UserError

    registry = env.registry
    ids = json.loads(env['ir.config_parameter'].sudo().get_param('irg_guard_test_fixtures'))
    source = env['irg.enrollment.change'].browse(ids['race'])
    enrollment_id = source.student_course_id.id
    student_id = source.student_id.id
    order_id = source.sale_order_id.id
    env.cr.rollback()
    created = []

    def setup(modality=False):
        with registry.cursor() as cr:
            e = api.Environment(cr, SUPERUSER_ID, {})
            e['op.student.course'].browse(enrollment_id).write({'batch_id': ids['batch_a']})
            order = e['sale.order'].browse(order_id)
            order.payment_mode_id = ids['pay_a']
            order.order_line.unlink()
            e['sale.order.line'].create({'order_id': order.id, 'product_id': ids['product'],
                                         'product_uom_qty': 1, 'price_unit': 10,
                                         'x_studio_modalidad': 'Online'})
            request = e['irg.enrollment.change'].create({
                'student_id': student_id, 'student_course_id': enrollment_id,
                'sale_order_id': order_id, 'change_batch': True,
                'dest_batch_id': ids['batch_b'], 'change_payment': True,
                'dest_payment_mode_id': ids['pay_b'], 'change_modality': modality,
                'dest_modality': 'Homeclass' if modality else False,
            })
            created.append(request.id)
            cr.commit()
            return request.id


    def retry(request_id):
        with registry.cursor() as cr:
            e = api.Environment(cr, SUPERUSER_ID, {})
            request = e['irg.enrollment.change'].browse(request_id)
            action = request.action_approve_academic()
            assert action['tag'] == 'display_notification'
            assert request.irg_guard_blocked
            assert request.state == 'submitted'
            cr.commit()


    def stale_approval(case):
        request_id = setup(modality=case in ['insert', 'insert_default', 'unlink', 'move', 'modality'])
        with registry.cursor() as first, registry.cursor() as second:
            a = api.Environment(first, SUPERUSER_ID, {})
            b = api.Environment(second, SUPERUSER_ID, {})
            request = a['irg.enrollment.change'].browse(request_id)
            request.read(['state'])  # establish a snapshot BEFORE transaction B
            first.execute('SHOW transaction_isolation')
            assert first.fetchone()[0] == 'repeatable read'
            order = b['sale.order'].browse(order_id)
            if case == 'enrollment':
                b['op.student.course'].browse(enrollment_id).batch_id = ids['batch_c']
            elif case == 'payment':
                order.payment_mode_id = ids['pay_b']
            elif case == 'insert':
                order.order_line.copy({'order_id': order_id})
            elif case == 'insert_default':
                default_domain = [
                    ('field_id', '=', b['ir.model.fields']._get('sale.order.line', 'order_id').id),
                    ('user_id', '=', SUPERUSER_ID),
                    ('company_id', '=', False), ('condition', '=', False),
                ]
                assert not b['ir.default'].search(default_domain), 'Unexpected existing test-user default'
                b['ir.default'].set('sale.order.line', 'order_id', order_id,
                                    user_id=SUPERUSER_ID)
                line = b['sale.order.line'].create({
                    'name': 'Guard ir.default section', 'display_type': 'line_section'})
                assert line.order_id.id == order_id
                # Remove only this temporary user default before committing.
                b['ir.default'].search(default_domain).unlink()
            elif case == 'unlink':
                order.order_line.unlink()
            elif case == 'modality':
                order.order_line.x_studio_modalidad = 'Presencial'
            elif case == 'move':
                # A different fixture order; restore it during final cleanup.
                destination = b['irg.enrollment.change'].browse(ids['modality']).sale_order_id
                order.order_line.order_id = destination
            second.commit()
            try:
                request.action_approve_academic()
            except SerializationFailure:
                first.rollback()
            else:
                raise AssertionError(case + ': stale snapshot did not propagate SerializationFailure')
        retry(request_id)
        with registry.cursor() as cr:
            e = api.Environment(cr, SUPERUSER_ID, {})
            assert e['op.student.course'].browse(enrollment_id).batch_id.id == (
                ids['batch_c'] if case == 'enrollment' else ids['batch_a'])
        print('PASS two connections stale approval:', case)


    def double_action(action):
        request_id = setup()
        if action == 'action_retry_pdf':
            with registry.cursor() as cr:
                e = api.Environment(cr, SUPERUSER_ID, {})
                request = e['irg.enrollment.change'].browse(request_id)
                request.action_approve_academic()
                Document = type(e['irg.enrollment.change.document'])
                with patch.object(Document, 'build_pdf_bytes', side_effect=UserError('Test converter failure')):
                    request.action_approve_finance()
                assert request.pdf_pending
                cr.commit()
        ready = threading.Event()
        release = threading.Event()
        outcomes = []
        RequestClass = type(env['irg.enrollment.change'])
        original = RequestClass._guard_lock_request

        def lock_then_pause(self):
            result = original(self)
            if threading.current_thread().name == 'guard-winner':
                ready.set()
                assert release.wait(15), 'release timeout'
            return result

        def worker(winner):
            try:
                with registry.cursor() as cr:
                    e = api.Environment(cr, SUPERUSER_ID, {})
                    request = e['irg.enrollment.change'].browse(request_id)
                    request.read(['state'])
                    Document = type(e['irg.enrollment.change.document'])
                    with patch.object(Document, 'build_pdf_bytes', return_value=b'%PDF-1.4\n%%EOF'):
                        getattr(request, action)()
                    cr.commit()
                    outcomes.append('committed')
            except SerializationFailure:
                outcomes.append('serialization')
            except Exception as error:
                outcomes.append(repr(error))

        with patch.object(RequestClass, '_guard_lock_request', lock_then_pause):
            first = threading.Thread(target=worker, args=(True,), name='guard-winner')
            second = threading.Thread(target=worker, args=(False,), name='guard-loser')
            first.start()
            assert ready.wait(15)
            second.start()
            # Assert real blocking with PostgreSQL, rather than relying on a sleep.
            blocked = False
            for _ in range(100):
                with registry.cursor() as probe:
                    probe.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'SELECT id FROM %irg_enrollment_change%'")
                    blocked = probe.fetchone()[0] > 0
                if blocked:
                    break
                time.sleep(0.02)
            release.set()
            first.join(20)
            second.join(20)
            assert not first.is_alive() and not second.is_alive()
            assert blocked, 'second action never waited on PostgreSQL lock'
        assert sorted(outcomes) == ['committed', 'serialization'], outcomes
        with registry.cursor() as cr:
            e = api.Environment(cr, SUPERUSER_ID, {})
            request = e['irg.enrollment.change'].browse(request_id)
            with cr.savepoint():
                try:
                    getattr(request, action)()
                except UserError:
                    pass
                else:
                    raise AssertionError('retry duplicated transition')
            expected_state = {'action_refuse': 'refused', 'action_retry_pdf': 'done',
                              'action_approve_academic': 'academic_approved'}[action]
            assert request.state == expected_state
            if action == 'action_retry_pdf':
                assert not request.pdf_pending
                assert len(e['ir.attachment'].search([('res_model', '=', request._name),
                           ('res_id', '=', request.id), ('name', '=', 'final.pdf')])) == 1
            if action == 'action_approve_academic':
                assert e['op.student.course'].browse(enrollment_id).batch_id.id == ids['batch_b']
                assert len(request.message_ids.filtered(lambda m: 'Pendiente de visto' in (m.body or ''))) == 1
        print('PASS threads + PostgreSQL lock + fresh retry:', action)


    def writer_during_approval():
        request_id = setup(modality=True)
        ready = threading.Event()
        release = threading.Event()
        outcomes = []
        RequestClass = type(env['irg.enrollment.change'])
        original = RequestClass._guard_compare

        def compare_then_pause(self, phase):
            original(self, phase)
            if threading.current_thread().name == 'guard-fenced-approval':
                ready.set()
                assert release.wait(15), 'release timeout'

        def approve():
            try:
                with registry.cursor() as cr:
                    e = api.Environment(cr, SUPERUSER_ID, {})
                    e['irg.enrollment.change'].browse(request_id).action_approve_academic()
                    cr.commit()
                    outcomes.append('approval committed')
            except Exception as error:
                outcomes.append(repr(error))

        def edit():
            try:
                with registry.cursor() as cr:
                    e = api.Environment(cr, SUPERUSER_ID, {})
                    lines = e['sale.order'].browse(order_id).order_line
                    lines.write({'x_studio_modalidad': 'Presencial'})
                    cr.commit()
                    outcomes.append('writer committed stale')
            except SerializationFailure:
                outcomes.append('writer serialization')
            except Exception as error:
                outcomes.append(repr(error))

        with patch.object(RequestClass, '_guard_compare', compare_then_pause):
            first = threading.Thread(target=approve, name='guard-fenced-approval')
            second = threading.Thread(target=edit, name='guard-fenced-writer')
            first.start()
            assert ready.wait(15)
            second.start()
            blocked = False
            for _ in range(100):
                with registry.cursor() as probe:
                    probe.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND wait_event_type='Lock' AND query LIKE 'UPDATE sale_order SET id = id%'")
                    blocked = probe.fetchone()[0] > 0
                if blocked:
                    break
                time.sleep(0.02)
            release.set()
            first.join(20)
            second.join(20)
            assert not first.is_alive() and not second.is_alive()
            assert blocked, 'line writer did not wait on approval fence'
        assert sorted(outcomes) == ['approval committed', 'writer serialization'], outcomes
        with registry.cursor() as cr:
            e = api.Environment(cr, SUPERUSER_ID, {})
            order = e['sale.order'].browse(order_id)
            assert set(order.order_line.mapped('x_studio_modalidad')) == {'Homeclass'}
            order.order_line.write({'x_studio_modalidad': 'Presencial'})
            cr.commit()
        with registry.cursor() as cr:
            e = api.Environment(cr, SUPERUSER_ID, {})
            request = e['irg.enrollment.change'].browse(request_id)
            action = request.action_approve_finance()
            assert action['tag'] == 'display_notification'
            assert request.state == 'academic_approved'
            assert request.student_course_id.batch_id.id == ids['batch_b']
            assert request.sale_order_id.payment_mode_id.id == ids['pay_a']
            assert set(request.sale_order_id.order_line.mapped('x_studio_modalidad')) == {'Presencial'}
            cr.commit()
        print('PASS concurrent line writer waits on approval fence; fresh edit survives and blocks finance')

    try:
        for case in ['enrollment', 'payment', 'insert', 'insert_default', 'unlink', 'modality', 'move']:
            stale_approval(case)
        for action in ['action_approve_academic', 'action_refuse', 'action_retry_pdf']:
            double_action(action)
        writer_during_approval()
    finally:
        # Disposable fixtures restored even when a concurrency assertion fails.
        with registry.cursor() as cr:
            e = api.Environment(cr, SUPERUSER_ID, {})
            e['irg.enrollment.change'].browse(created).unlink()
            e['op.student.course'].browse(enrollment_id).batch_id = ids['batch_a']
            order = e['sale.order'].browse(order_id)
            order.payment_mode_id = ids['pay_a']
            order.order_line.unlink()
            e['sale.order.line'].create({'order_id': order_id, 'product_id': ids['product'],
                                         'product_uom_qty': 1, 'price_unit': 10,
                                         'x_studio_modalidad': 'Online'})
            other = e['irg.enrollment.change'].browse(ids['modality']).sale_order_id
            if len(other.order_line) > 1:
                other.order_line.sorted('id')[1:].unlink()
            cr.commit()
        print('CLEANUP concurrent requests removed; enrollment, order and lines restored')
    print('PASS concurrency integration complete')
