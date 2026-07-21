import ast
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from psycopg2 import errors

from odoo import SUPERUSER_ID, api, sql_db
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.addons.irg_forum_notice_global_seen.models import (
    forum_notice_seen as global_seen_model_module,
)


def _json_payload(case, route, params):
    response = case.url_open(
        route,
        data=json.dumps({
            'jsonrpc': '2.0',
            'method': 'call',
            'params': params,
            'id': 1,
        }),
        headers={'Content-Type': 'application/json'},
    )
    return response.json()


def _json_call(case, route, params):
    payload = _json_payload(case, route, params)
    case.assertNotIn('error', payload)
    return payload['result']


@tagged('post_install', '-at_install')
class TestForumNoticeGlobalSeen(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_group = cls.env.ref('base.group_user')
        portal_group = cls.env.ref('base.group_portal')
        system_group = cls.env.ref('base.group_system')
        cls.user_a = cls.env['res.users'].create({
            'name': 'Global Seen A',
            'login': 'global-seen-a@example.test',
            'groups_id': [(6, 0, user_group.ids)],
        })
        cls.user_b = cls.env['res.users'].create({
            'name': 'Global Seen B',
            'login': 'global-seen-b@example.test',
            'groups_id': [(6, 0, user_group.ids)],
        })
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Global Seen Portal',
            'login': 'global-seen-portal@example.test',
            'groups_id': [(6, 0, portal_group.ids)],
        })
        cls.system_user = cls.env['res.users'].create({
            'name': 'Global Seen System',
            'login': 'global-seen-system@example.test',
            'groups_id': [(6, 0, (user_group | system_group).ids)],
        })
        cls.course_a = cls.env['op.course'].create({
            'name': 'Seen Course A',
            'code': 'SEEN-A',
        })
        cls.course_b = cls.env['op.course'].create({
            'name': 'Seen Course B',
            'code': 'SEEN-B',
        })
        cls.forum = cls.env['forum.forum'].create({'name': 'Global Seen Forum'})
        cls.post = cls.env['forum.post'].sudo().create({
            'name': 'Aviso global seen',
            'forum_id': cls.forum.id,
            'content': 'Global seen test',
        })

    def setUp(self):
        super().setUp()
        if (
            self._testMethodName != 'test_global_seen_model_is_registered'
            and 'irg.forum.notice.global.seen' not in self.env.registry.models
        ):
            self.skipTest('global seen model is not registered yet')

    def _legacy_values(self, user=None, course=None):
        return {
            'user_id': (user or self.user_a).id,
            'course_id': (course or self.course_a).id,
            'post_id': self.post.id,
        }

    def test_global_seen_model_is_registered(self):
        self.assertTrue(
            'irg.forum.notice.global.seen' in self.env.registry.models,
            'irg.forum.notice.global.seen is absent from the registry',
        )

    def test_frontend_replacement_asset_contract(self):
        module_root = Path(__file__).resolve().parents[1]
        manifest = ast.literal_eval(
            (module_root / '__manifest__.py').read_text(encoding='utf-8')
        )
        frontend_assets = manifest.get('assets', {}).get(
            'web.assets_frontend', []
        )
        parent_asset = (
            'remove',
            'irg_forum_notice_popup/static/src/js/forum_notice_popup.js',
        )
        replacement_asset = (
            'irg_forum_notice_global_seen/static/src/js/'
            'forum_notice_popup.js'
        )
        self.assertEqual(frontend_assets.count(parent_asset), 1)
        self.assertEqual(frontend_assets.count(replacement_asset), 1)
        self.assertLess(
            frontend_assets.index(parent_asset),
            frontend_assets.index(replacement_asset),
        )

        replacement_path = (
            module_root / 'static' / 'src' / 'js' /
            'forum_notice_popup.js'
        )
        self.assertTrue(replacement_path.is_file())
        source = replacement_path.read_text(encoding='utf-8')
        for contract in (
            'const suppressedNoticeIds = new Set();',
            'const markSeenRequests = new Map();',
            'if (!markSeenRequests.has(noticeId))',
            'if (!result || !result.ok)',
            'wrapper.dataset.noticeId = String(notice.id);',
        ):
            self.assertIn(contract, source)

        mark_seen = source[
            source.index('function markSeen('):
            source.index('function shouldRunPopupCheck(')
        ]
        self.assertIn('if (!noticeId)', mark_seen)
        self.assertNotIn('if (!courseId || !noticeId)', mark_seen)

        dismiss = source[
            source.index('async function dismissPopup('):
            source.index('function renderPopup(')
        ]
        self.assertLess(
            dismiss.index('suppressedNoticeIds.add(noticeId)'),
            dismiss.index('await markSeen(noticeId, courseId)'),
        )
        self.assertLess(
            dismiss.index('await markSeen(noticeId, courseId)'),
            dismiss.index('wrapper.remove()'),
        )
        dismiss_finally = dismiss.index('} finally {')
        self.assertLess(
            dismiss.index('await markSeen(noticeId, courseId)'),
            dismiss_finally,
        )
        self.assertLess(dismiss_finally, dismiss.index('wrapper.remove()'))

        open_handler = source[
            source.index("openBtn.addEventListener('click'"):
            source.index('\n    }\n}', source.index(
                "openBtn.addEventListener('click'"
            ))
        ]
        for contract in (
            'event.preventDefault()',
            'await markSeen(notice.id, courseId)',
            'window.location.assign(openBtn.href)',
        ):
            self.assertIn(contract, open_handler)
        self.assertLess(
            open_handler.index('event.preventDefault()'),
            open_handler.index('await markSeen(notice.id, courseId)'),
        )
        self.assertLess(
            open_handler.index('await markSeen(notice.id, courseId)'),
            open_handler.index('window.location.assign(openBtn.href)'),
        )
        open_finally = open_handler.index('} finally {')
        self.assertLess(
            open_handler.index('await markSeen(notice.id, courseId)'),
            open_finally,
        )
        self.assertLess(
            open_finally,
            open_handler.index('window.location.assign(openBtn.href)'),
        )

    def test_frontend_renders_untrusted_notice_content_safely(self):
        module_root = Path(__file__).resolve().parents[1]
        source = (
            module_root / 'static' / 'src' / 'js' /
            'forum_notice_popup.js'
        ).read_text(encoding='utf-8')
        render_popup = source[
            source.index('function renderPopup('):
            source.index('async function initForumNoticePopup(')
        ]

        skeleton_start = render_popup.index('wrapper.innerHTML = `')
        skeleton_end = render_popup.index('`;', skeleton_start)
        static_skeleton = render_popup[skeleton_start:skeleton_end]
        malicious_payload = {
            'title': '<img src=x onerror=alert(1)>',
            'forum_name': '</div><script>alert(2)</script>',
            'preview': '<svg onload=alert(3)>',
            'url': 'javascript:alert(4)',
        }

        self.assertNotIn('${', static_skeleton)
        for field_name in malicious_payload:
            self.assertNotIn('notice.%s' % field_name, static_skeleton)

        for assignment in (
            "titleNode.textContent = notice.title || 'Nuevo aviso';",
            'metaNode.textContent = `Foro: ${notice.forum_name}`;',
            'previewNode.textContent = notice.preview;',
        ):
            self.assertIn(assignment, render_popup)

        safe_url = source[
            source.index('function getSafeNoticeUrl('):
            source.index('function renderPopup(')
        ]
        for contract in (
            'new URL(value, window.location.origin)',
            "['http:', 'https:'].includes(url.protocol)",
            'url.origin !== window.location.origin',
        ):
            self.assertIn(contract, safe_url)
        self.assertIn('const safeUrl = getSafeNoticeUrl(notice.url);', render_popup)
        self.assertIn('openBtn.href = safeUrl;', render_popup)
        self.assertNotIn('href="${notice.url}', render_popup)

    def test_mark_seen_is_idempotent_per_user_and_post(self):
        Seen = self.env['irg.forum.notice.global.seen']
        first = Seen._irg_mark_seen(self.user_a.id, self.post.id)
        second = Seen._irg_mark_seen(self.user_a.id, self.post.id)
        self.assertEqual(first, second)
        self.assertEqual(Seen.search_count([
            ('user_id', '=', self.user_a.id),
            ('post_id', '=', self.post.id),
        ]), 1)

    def test_non_unique_integrity_errors_are_not_swallowed(self):
        Seen = self.env['irg.forum.notice.global.seen']
        missing_user_id = 2147483647
        self.assertFalse(self.env['res.users'].sudo().browse(missing_user_id).exists())
        with self.env.cr.savepoint():
            with self.assertRaises(errors.ForeignKeyViolation):
                Seen._irg_mark_seen(missing_user_id, self.post.id)

    def test_seen_state_is_independent_per_user(self):
        Seen = self.env['irg.forum.notice.global.seen']
        Seen._irg_mark_seen(self.user_a.id, self.post.id)
        self.assertTrue(Seen._irg_is_seen(self.user_a.id, self.post.id))
        self.assertFalse(Seen._irg_is_seen(self.user_b.id, self.post.id))

    def test_legacy_seen_in_any_course_counts_as_seen(self):
        self.env['irg.forum.notice.seen'].sudo().create({
            'user_id': self.user_a.id,
            'course_id': self.course_a.id,
            'post_id': self.post.id,
        })
        Seen = self.env['irg.forum.notice.global.seen']
        self.assertTrue(Seen._irg_is_seen(self.user_a.id, self.post.id))
        self.assertEqual(Seen.search_count([]), 0)

    def test_legacy_rows_for_two_courses_do_not_require_two_dismissals(self):
        Legacy = self.env['irg.forum.notice.seen'].sudo()
        for course in (self.course_a, self.course_b):
            Legacy.create({
                'user_id': self.user_a.id,
                'course_id': course.id,
                'post_id': self.post.id,
            })
        self.assertTrue(
            self.env['irg.forum.notice.global.seen']._irg_is_seen(
                self.user_a.id, self.post.id
            )
        )

    def test_global_model_direct_create_is_system_only(self):
        values = {'user_id': self.user_a.id, 'post_id': self.post.id}
        Seen = self.env['irg.forum.notice.global.seen']
        for user in (self.user_a, self.portal_user):
            with self.assertRaises(AccessError):
                Seen.with_user(user).create(values)
        created = Seen.with_user(self.system_user).create(values)
        self.assertEqual(created.user_id, self.user_a)

    def test_legacy_reads_are_owner_scoped(self):
        Legacy = self.env['irg.forum.notice.seen'].sudo()
        own_internal = Legacy.create(self._legacy_values(self.user_a))
        other_internal = Legacy.create(self._legacy_values(self.user_b))
        own_portal = Legacy.create(self._legacy_values(self.portal_user))

        internal_rows = Legacy.with_user(self.user_a).search([
            ('id', 'in', (own_internal | other_internal | own_portal).ids),
        ])
        portal_rows = Legacy.with_user(self.portal_user).search([
            ('id', 'in', (own_internal | other_internal | own_portal).ids),
        ])
        self.assertEqual(internal_rows, own_internal)
        self.assertEqual(portal_rows, own_portal)

    def test_internal_and_portal_cannot_create_legacy_rows(self):
        Legacy = self.env['irg.forum.notice.seen']
        for user in (self.user_a, self.portal_user):
            with self.assertRaises(AccessError):
                Legacy.with_user(user).create(self._legacy_values(user))

    def test_internal_and_portal_cannot_mutate_owned_legacy_rows(self):
        Legacy = self.env['irg.forum.notice.seen'].sudo()
        for user in (self.user_a, self.portal_user):
            row = Legacy.create(self._legacy_values(user))
            with self.assertRaises(AccessError):
                row.with_user(user).write({'seen_at': False})
            with self.assertRaises(AccessError):
                row.with_user(user).write({'user_id': self.user_b.id})
            with self.assertRaises(AccessError):
                row.with_user(user).unlink()
            self.assertTrue(row.exists())
            self.assertEqual(row.user_id, user)

    def test_trusted_sudo_and_system_can_mutate_legacy_rows(self):
        Legacy = self.env['irg.forum.notice.seen']
        sudo_row = Legacy.sudo().create(self._legacy_values(self.user_a))
        sudo_row.write({'user_id': self.user_b.id})
        self.assertEqual(sudo_row.user_id, self.user_b)

        system_row = Legacy.with_user(self.system_user).create(
            self._legacy_values(self.system_user, self.course_b)
        )
        system_row.write({'user_id': self.portal_user.id})
        self.assertEqual(system_row.user_id, self.portal_user)
        system_row.unlink()
        self.assertFalse(system_row.exists())


@tagged('post_install', '-at_install')
class TestForumNoticeGlobalSeenHttp(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        internal_group = cls.env.ref('base.group_user')
        portal_group = cls.env.ref('base.group_portal')
        system_group = cls.env.ref('base.group_system')
        password = 'global-seen-test'
        cls.system_user = cls.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Global Seen HTTP System',
            'login': 'global-seen-http-system@example.test',
            'password': password,
            'groups_id': [(
                6, 0, (internal_group | system_group).ids,
            )],
        })
        cls.internal_user = cls.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Global Seen HTTP Internal',
            'login': 'global-seen-http-internal@example.test',
            'password': password,
            'groups_id': [(6, 0, internal_group.ids)],
        })
        cls.portal_user = cls.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Global Seen HTTP Portal',
            'login': 'global-seen-http-portal@example.test',
            'password': password,
            'groups_id': [(6, 0, portal_group.ids)],
        })
        cls.target_user = cls.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Global Seen HTTP Target',
            'login': 'global-seen-http-target@example.test',
            'password': password,
            'groups_id': [(6, 0, internal_group.ids)],
        })
        cls.courseless_student_user = cls.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Global Seen HTTP Courseless Student',
            'login': 'global-seen-http-courseless@example.test',
            'password': password,
            'groups_id': [(6, 0, internal_group.ids)],
        })
        cls.courseless_student = cls.env['op.student'].sudo().create({
            'first_name': 'Global Seen',
            'last_name': 'Courseless Student',
            'partner_id': cls.courseless_student_user.partner_id.id,
            'user_id': cls.courseless_student_user.id,
        })
        cls.course = cls.env['op.course'].create({
            'name': 'Global Seen HTTP Course',
            'code': 'GS-HTTP-A',
        })
        cls.other_course = cls.env['op.course'].create({
            'name': 'Global Seen HTTP Other Course',
            'code': 'GS-HTTP-B',
        })
        cls.forum = cls.env['forum.forum'].create({
            'name': 'Global Seen HTTP Forum',
            'visibility_course_ids': [(
                6, 0, (cls.course | cls.other_course).ids,
            )],
        })
        cls.post = cls.env['forum.post'].sudo().create({
            'name': 'Aviso global seen HTTP',
            'forum_id': cls.forum.id,
            'content': 'Global seen HTTP test',
        })
        cls.restricted_post = cls.post

    def _legacy_values(self, user, course):
        return {
            'user_id': user.id,
            'course_id': course.id,
            'post_id': self.post.id,
        }

    def _seen_state(self, users):
        user_ids = users.ids
        state = {}
        for model_name in (
            'irg.forum.notice.seen',
            'irg.forum.notice.global.seen',
        ):
            Model = self.env[model_name].sudo()
            self.env.invalidate_all()
            rows = Model.search(
                [('user_id', 'in', user_ids)], order='id'
            )
            state[model_name] = {
                'counts': {
                    user.id: Model.search_count([
                        ('user_id', '=', user.id),
                    ])
                    for user in users
                },
                'rows': tuple(
                    (
                        row.id,
                        row.user_id.id,
                        row.post_id.id,
                        row.seen_at,
                    )
                    for row in rows
                ),
            }
        return state

    def _assert_orm_denied_without_state_change(self, users, operation):
        before = self._seen_state(users)
        with self.assertRaises(AccessError):
            operation()
        self.assertEqual(self._seen_state(users), before)

    def _assert_rpc_denied_without_state_change(
        self, users, model_name, method_name, args, kwargs=None
    ):
        before = self._seen_state(users)
        payload = _json_payload(
            self,
            '/web/dataset/call_kw/%s/%s' % (model_name, method_name),
            {
                'model': model_name,
                'method': method_name,
                'args': args,
                'kwargs': kwargs or {},
            },
        )
        self.assertIn('error', payload)
        self.assertEqual(self._seen_state(users), before)

    def _assert_actor_security_boundaries(self, actor):
        users = actor | self.target_user
        Legacy = self.env['irg.forum.notice.seen']
        Global = self.env['irg.forum.notice.global.seen']

        self._assert_orm_denied_without_state_change(
            users,
            lambda: Legacy.with_user(actor).create(
                self._legacy_values(self.target_user, self.course)
            ),
        )
        self._assert_orm_denied_without_state_change(
            users,
            lambda: Legacy.with_user(actor).create(
                self._legacy_values(actor, self.course)
            ),
        )
        own_legacy = Legacy.sudo().create(
            self._legacy_values(actor, self.course)
        )
        other_legacy = Legacy.sudo().create(
            self._legacy_values(self.target_user, self.course)
        )
        self._assert_orm_denied_without_state_change(
            users,
            lambda: other_legacy.with_user(actor).write({'seen_at': False}),
        )
        self._assert_orm_denied_without_state_change(
            users,
            lambda: other_legacy.with_user(actor).unlink(),
        )
        self._assert_orm_denied_without_state_change(
            users,
            lambda: own_legacy.with_user(actor).write({'seen_at': False}),
        )
        self._assert_orm_denied_without_state_change(
            users,
            lambda: own_legacy.with_user(actor).write({
                'user_id': self.target_user.id,
            }),
        )
        self._assert_orm_denied_without_state_change(
            users,
            lambda: own_legacy.with_user(actor).unlink(),
        )

        self._assert_orm_denied_without_state_change(
            users,
            lambda: Global.with_user(actor).create({
                'user_id': self.target_user.id,
                'post_id': self.post.id,
            }),
        )
        other_global = Global.sudo().create({
            'user_id': self.target_user.id,
            'post_id': self.post.id,
        })
        self._assert_orm_denied_without_state_change(
            users,
            lambda: other_global.with_user(actor).write({'seen_at': False}),
        )

        self.authenticate(actor.login, 'global-seen-test')
        self._assert_rpc_denied_without_state_change(
            users,
            'irg.forum.notice.seen',
            'create',
            [self._legacy_values(self.target_user, self.other_course)],
        )
        rpc_own_legacy = Legacy.sudo().create(
            self._legacy_values(actor, self.other_course)
        )
        rpc_other_legacy = Legacy.sudo().create(
            self._legacy_values(self.target_user, self.other_course)
        )
        for row, method_name, args in (
            (rpc_other_legacy, 'write', [[rpc_other_legacy.id], {
                'seen_at': False,
            }]),
            (rpc_other_legacy, 'unlink', [[rpc_other_legacy.id]]),
            (rpc_own_legacy, 'write', [[rpc_own_legacy.id], {
                'seen_at': False,
            }]),
            (rpc_own_legacy, 'write', [[rpc_own_legacy.id], {
                'user_id': self.target_user.id,
            }]),
            (rpc_own_legacy, 'unlink', [[rpc_own_legacy.id]]),
        ):
            self._assert_rpc_denied_without_state_change(
                users,
                'irg.forum.notice.seen',
                method_name,
                args,
            )

        other_global.sudo().unlink()
        self._assert_rpc_denied_without_state_change(
            users,
            'irg.forum.notice.global.seen',
            'create',
            [{
                'user_id': self.target_user.id,
                'post_id': self.post.id,
            }],
        )
        rpc_other_global = Global.sudo().create({
            'user_id': self.target_user.id,
            'post_id': self.post.id,
        })
        self._assert_rpc_denied_without_state_change(
            users,
            'irg.forum.notice.global.seen',
            'write',
            [[rpc_other_global.id], {'seen_at': False}],
        )
        for private_method in ('_irg_is_seen', '_irg_mark_seen'):
            self._assert_rpc_denied_without_state_change(
                users,
                'irg.forum.notice.global.seen',
                private_method,
                [actor.id, self.post.id],
            )

    def test_browser_dismiss_persists_before_next_poll(self):
        code = """
            const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const waitFor = async (selector, timeoutMs = 10000) => {
                const deadline = Date.now() + timeoutMs;
                while (Date.now() < deadline) {
                    const node = document.querySelector(selector);
                    if (node) return node;
                    await sleep(100);
                }
                throw new Error(`Missing ${selector}`);
            };
            const rpc = async (route, params = {}) => {
                const response = await fetch(route, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        jsonrpc: '2.0', method: 'call', params, id: 1,
                    }),
                });
                const payload = await response.json();
                if (payload.error) throw new Error(JSON.stringify(payload.error));
                return payload.result;
            };

            const popup = await waitFor('.irg-forum-popup-wrap');
            const noticeId = Number(popup.dataset.noticeId);
            if (!noticeId) throw new Error('Popup has no data-notice-id');
            popup.querySelector('.irg-forum-popup-dismiss').click();
            await sleep(4000);
            const result = await rpc('/campus/forum_notice_popup');
            if (result.notice && result.notice.id === noticeId) {
                throw new Error('Dismissed notice was returned by the next poll');
            }
            console.log('test successful');
        """
        self.browser_js(
            '/', code, login=self.system_user.login, timeout=60
        )

    def test_mark_seen_without_course_id(self):
        self.authenticate(self.system_user.login, 'global-seen-test')
        result = _json_call(self, '/campus/forum_notice_popup_seen', {
            'notice_id': self.post.id,
        })
        self.assertEqual(result, {'ok': True})
        self.assertTrue(
            self.env['irg.forum.notice.global.seen'].sudo().search([
                ('user_id', '=', self.system_user.id),
                ('post_id', '=', self.post.id),
            ])
        )

    def test_concurrent_transactions_recover_unique_race(self):
        Seen = self.env['irg.forum.notice.global.seen'].sudo()
        with sql_db.db_connect(self.env.cr.dbname).cursor() as setup_cursor:
            setup_cursor.execute(
                """
                INSERT INTO forum_forum (
                    name, mode, default_order, create_uid, write_uid,
                    create_date, write_date
                ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (
                    json.dumps({
                        'en_US':
                        'Global Seen Committed Concurrency Forum',
                    }),
                    'questions',
                    'activity',
                    SUPERUSER_ID,
                    SUPERUSER_ID,
                ),
            )
            concurrent_forum_id = setup_cursor.fetchone()[0]
            setup_cursor.execute(
                """
                INSERT INTO forum_post (
                    forum_id, name, content, create_uid, write_uid,
                    create_date, write_date
                ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (
                    concurrent_forum_id,
                    'Global Seen Committed Concurrency Notice',
                    'Committed fixture for independent transactions',
                    SUPERUSER_ID,
                    SUPERUSER_ID,
                ),
            )
            concurrent_post_id = setup_cursor.fetchone()[0]
            setup_cursor.commit()
        domain = [
            ('user_id', '=', SUPERUSER_ID),
            ('post_id', '=', concurrent_post_id),
        ]
        self.assertFalse(Seen.search(domain))
        initial_search_barrier = threading.Barrier(2)
        initial_search_count = 0
        count_lock = threading.Lock()
        worker_context = threading.local()
        winner_committed = threading.Event()
        model_class = type(Seen)
        original_search = model_class.search

        def synchronized_search(recordset, search_domain, *args, **kwargs):
            nonlocal initial_search_count
            result = original_search(
                recordset, search_domain, *args, **kwargs
            )
            if (
                recordset._name == 'irg.forum.notice.global.seen'
                and search_domain == domain
                and kwargs.get('limit') == 1
                and not result
            ):
                with count_lock:
                    initial_search_count += 1
                initial_search_barrier.wait(timeout=10)
                recordset.env.cr.commit()
                if worker_context.index == 1:
                    if not winner_committed.wait(timeout=10):
                        raise AssertionError(
                            'winning transaction did not commit in time'
                        )
            return result

        def mark(worker_index):
            worker_context.index = worker_index
            with sql_db.db_connect(self.env.cr.dbname).cursor() as cursor:
                thread_env = api.Environment(
                    cursor, SUPERUSER_ID, {}
                )
                seen = thread_env[
                    'irg.forum.notice.global.seen'
                ]._irg_mark_seen(SUPERUSER_ID, concurrent_post_id)
                seen_id = seen.id
                cursor.commit()
                if worker_index == 0:
                    winner_committed.set()
                return seen_id

        try:
            with patch.object(
                model_class, 'search', synchronized_search
            ), patch.object(
                global_seen_model_module._logger,
                'debug',
                wraps=global_seen_model_module._logger.debug,
            ) as debug_log:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    results = list(executor.map(mark, range(2)))

            self.assertEqual(initial_search_count, 2)
            self.assertEqual(results[0], results[1])
            with sql_db.db_connect(
                self.env.cr.dbname
            ).cursor() as assertion_cursor:
                assertion_cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM irg_forum_notice_global_seen
                    WHERE user_id = %s AND post_id = %s
                    """,
                    (SUPERUSER_ID, concurrent_post_id),
                )
                self.assertEqual(assertion_cursor.fetchone()[0], 1)
            self.assertTrue(any(
                'concurrent duplicate ignored' in str(call)
                for call in debug_log.call_args_list
            ))
        finally:
            with sql_db.db_connect(
                self.env.cr.dbname
            ).cursor() as cleanup_cursor:
                cleanup_cursor.execute(
                    """
                    DELETE FROM irg_forum_notice_global_seen
                    WHERE user_id = %s AND post_id = %s
                    """,
                    (SUPERUSER_ID, concurrent_post_id),
                )
                cleanup_cursor.execute(
                    'DELETE FROM forum_post WHERE id = %s',
                    (concurrent_post_id,),
                )
                cleanup_cursor.execute(
                    'DELETE FROM forum_forum WHERE id = %s',
                    (concurrent_forum_id,),
                )
                cleanup_cursor.commit()

        self.assertFalse(user.sudo().forum_effective_course_ids)
        self.assertFalse(self.env['op.student.course'].sudo().search([
            ('student_id', '=', self.courseless_student.id),
        ]))
        self.assertFalse(self.env['op.admission'].sudo().search([
            '|',
            ('student_id', '=', self.courseless_student.id),
            ('partner_id', '=', user.partner_id.id),
        ]))

        self.post.sudo().write({'active': False})
        unrestricted_forum = self.env['forum.forum'].sudo().create({
            'name': 'Global Seen HTTP Courseless Student Forum',
        })
        unrestricted_post = self.env['forum.post'].sudo().create({
            'name': 'Aviso global seen courseless student',
            'forum_id': unrestricted_forum.id,
            'content': 'Visible to a linked student without a course',
        })
        self.assertTrue(unrestricted_post._is_visible_for_user(user))

        self.authenticate(user.login, 'global-seen-test')
        discovered = _json_call(self, '/campus/forum_notice_popup', {})
        self.assertEqual(discovered['notice']['id'], unrestricted_post.id)
        marked = _json_call(self, '/campus/forum_notice_popup_seen', {
            'notice_id': unrestricted_post.id,
        })
        self.assertEqual(marked, {'ok': True})
        self.assertEqual(
            self.env['irg.forum.notice.global.seen'].sudo().search_count([
                ('user_id', '=', user.id),
                ('post_id', '=', unrestricted_post.id),
            ]),
            1,
        )
        suppressed = _json_call(self, '/campus/forum_notice_popup', {})
        self.assertTrue(
            not suppressed['notice']
            or suppressed['notice']['id'] != unrestricted_post.id
        )

    def test_course_mark_seen_route_uses_global_state(self):
        self.authenticate(self.system_user.login, 'global-seen-test')
        result = _json_call(
            self,
            '/campus/course/%s/forum_notice_popup_seen' % self.course.id,
            {'notice_id': self.post.id},
        )
        self.assertEqual(result, {'ok': True})
        self.assertTrue(
            self.env['irg.forum.notice.global.seen'].sudo().search([
                ('user_id', '=', self.system_user.id),
                ('post_id', '=', self.post.id),
            ])
        )

    def test_same_post_is_suppressed_after_seen_from_any_course(self):
        self.env['irg.forum.notice.global.seen'].sudo()._irg_mark_seen(
            self.system_user.id, self.post.id
        )
        self.authenticate(self.system_user.login, 'global-seen-test')
        for course in (self.course, self.other_course):
            result = _json_call(
                self,
                '/campus/course/%s/forum_notice_popup' % course.id,
                {},
            )
            self.assertTrue(
                not result['notice'] or result['notice']['id'] != self.post.id
            )

    def test_any_campus_discovery_uses_global_state(self):
        self.env['irg.forum.notice.global.seen'].sudo()._irg_mark_seen(
            self.system_user.id, self.post.id
        )
        self.authenticate(self.system_user.login, 'global-seen-test')
        result = _json_call(self, '/campus/forum_notice_popup', {})
        self.assertTrue(
            not result['notice'] or result['notice']['id'] != self.post.id
        )

    def test_any_campus_suppresses_seen_post_without_course_context(self):
        self.assertFalse(
            self.system_user.sudo().forum_effective_course_ids,
            'regression fixture unexpectedly has an effective course',
        )
        self.post.sudo().write({'active': False})
        unrestricted_forum = self.env['forum.forum'].create({
            'name': 'Global Seen HTTP Unrestricted Forum',
        })
        unrestricted_post = self.env['forum.post'].sudo().create({
            'name': 'Aviso global seen without course',
            'forum_id': unrestricted_forum.id,
            'content': 'Visible notice without course context',
        })
        self.authenticate(self.system_user.login, 'global-seen-test')
        before_seen = _json_call(self, '/campus/forum_notice_popup', {})
        self.assertEqual(before_seen['notice']['id'], unrestricted_post.id)

        self.env['irg.forum.notice.global.seen'].sudo()._irg_mark_seen(
            self.system_user.id, unrestricted_post.id
        )
        after_seen = _json_call(self, '/campus/forum_notice_popup', {})
        self.assertTrue(
            not after_seen['notice']
            or after_seen['notice']['id'] != unrestricted_post.id
        )

    def test_internal_user_without_visibility_cannot_mark_post(self):
        self.authenticate(self.internal_user.login, 'global-seen-test')
        result = _json_call(self, '/campus/forum_notice_popup_seen', {
            'notice_id': self.restricted_post.id,
        })
        self.assertEqual(result, {'ok': False})
        self.assertFalse(
            self.env['irg.forum.notice.global.seen'].sudo().search([
                ('user_id', '=', self.internal_user.id),
                ('post_id', '=', self.restricted_post.id),
            ])
        )

    def test_portal_user_without_visibility_cannot_mark_post(self):
        self.authenticate(self.portal_user.login, 'global-seen-test')
        result = _json_call(self, '/campus/forum_notice_popup_seen', {
            'notice_id': self.restricted_post.id,
        })
        self.assertEqual(result, {'ok': False})
        self.assertFalse(
            self.env['irg.forum.notice.global.seen'].sudo().search([
                ('user_id', '=', self.portal_user.id),
                ('post_id', '=', self.restricted_post.id),
            ])
        )

    def test_public_invalid_and_missing_posts_are_rejected(self):
        users = self.system_user
        before = self._seen_state(users)
        self.authenticate(None, None)
        public_payload = _json_payload(
            self,
            '/campus/forum_notice_popup_seen',
            {'notice_id': self.post.id},
        )
        self.assertIn('error', public_payload)
        self.assertEqual(self._seen_state(users), before)

        self.authenticate(self.system_user.login, 'global-seen-test')
        for notice_id in ('not-an-id', 0, 999999999):
            result = _json_call(
                self,
                '/campus/forum_notice_popup_seen',
                {'notice_id': notice_id},
            )
            self.assertEqual(result, {'ok': False})
            self.assertEqual(self._seen_state(users), before)

    def test_internal_orm_and_rpc_security_boundaries(self):
        self._assert_actor_security_boundaries(self.internal_user)

    def test_portal_orm_and_rpc_security_boundaries(self):
        self._assert_actor_security_boundaries(self.portal_user)

    def test_trusted_sudo_and_system_legacy_controls_remain_available(self):
        Legacy = self.env['irg.forum.notice.seen']
        sudo_row = Legacy.sudo().create(
            self._legacy_values(self.internal_user, self.course)
        )
        sudo_row.write({'user_id': self.portal_user.id})
        self.assertEqual(sudo_row.user_id, self.portal_user)

        system_row = Legacy.with_user(self.system_user).create(
            self._legacy_values(self.system_user, self.other_course)
        )
        system_row.write({'user_id': self.target_user.id})
        self.assertEqual(system_row.user_id, self.target_user)
        system_row.unlink()
        self.assertFalse(system_row.exists())
