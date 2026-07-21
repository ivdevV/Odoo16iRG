import http.cookiejar
import json
import re
import urllib.request


base = 'http://127.0.0.1:18069'
database = 'test_irg_forum_global_seen'
password = 'evidence-validator'


def new_client():
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )


def call(client, route, params):
    data = json.dumps({
        'jsonrpc': '2.0', 'method': 'call', 'params': params, 'id': 1,
    }).encode()
    request = urllib.request.Request(
        base + route, data=data, headers={'Content-Type': 'application/json'}
    )
    with client.open(request, timeout=30) as response:
        payload = json.loads(response.read().decode())
    if 'error' in payload:
        raise AssertionError((route, payload['error']))
    return payload['result']


def login(name):
    client = new_client()
    result = call(client, '/web/session/authenticate', {
        'db': database, 'login': name, 'password': password,
    })
    assert result['uid']
    return client


def rpc(client, model, method, args, kwargs=None):
    return call(client, f'/web/dataset/call_kw/{model}/{method}', {
        'model': model,
        'method': method,
        'args': args,
        'kwargs': kwargs or {},
    })


system = login('evidence-second@example.test')
course_a, course_b = 46, 47
multicourse = 71
post_ids = {'multi': 17, 'excluded': 18, 'courseless': 19}

courseless = login('evidence-courseless@example.test')
result = call(courseless, '/campus/forum_notice_popup', {})
assert result['notice']['id'] == post_ids['courseless']
assert call(courseless, '/campus/forum_notice_popup_seen', {
    'notice_id': post_ids['courseless'],
}) == {'ok': True}
result = call(courseless, '/campus/forum_notice_popup', {})
assert not result['notice'] or result['notice']['id'] != post_ids['courseless']
print('courseless_once: PASS')

result = call(system, '/campus/forum_notice_popup', {})
assert result['notice']['id'] == post_ids['courseless']
assert call(system, '/campus/forum_notice_popup_seen', {
    'notice_id': post_ids['courseless'],
}) == {'ok': True}
print('independent_users: PASS')

rpc(system, 'forum.post', 'write', [[post_ids['courseless']], {'active': False}])
rpc(system, 'forum.post', 'write', [[post_ids['multi']], {'active': True}])
multi = login('evidence-multi@example.test')
route_a = f'/campus/course/{course_a}/forum_notice_popup'
route_b = f'/campus/course/{course_b}/forum_notice_popup'
assert call(multi, route_a, {})['notice']['id'] == post_ids['multi']
assert call(
    multi,
    f'/campus/course/{course_a}/forum_notice_popup_seen',
    {'notice_id': post_ids['multi']},
) == {'ok': True}
for route in (route_a, route_b):
    result = call(multi, route, {})
    assert not result['notice'] or result['notice']['id'] != post_ids['multi']
print('multicourse_single_dismissal: PASS')

global_ids = rpc(system, 'irg.forum.notice.global.seen', 'search', [[
    ('user_id', '=', multicourse), ('post_id', '=', post_ids['multi']),
]])
assert len(global_ids) == 1
rpc(system, 'irg.forum.notice.global.seen', 'unlink', [global_ids])
rpc(system, 'irg.forum.notice.seen', 'create', [{
    'user_id': multicourse,
    'course_id': course_a,
    'post_id': post_ids['multi'],
}])
assert rpc(system, 'irg.forum.notice.global.seen', 'search_count', [[
    ('user_id', '=', multicourse), ('post_id', '=', post_ids['multi']),
]]) == 0
result = call(multi, route_b, {})
assert not result['notice'] or result['notice']['id'] != post_ids['multi']
print('legacy_cross_course: PASS')

rpc(system, 'forum.post', 'write', [[post_ids['multi']], {'active': False}])
rpc(system, 'forum.post', 'write', [[post_ids['excluded']], {'active': True}])
for route in ('/campus/forum_notice_popup', route_a):
    result = call(multi, route, {})
    assert not result['notice'] or result['notice']['id'] != post_ids['excluded']
assert call(multi, '/campus/forum_notice_popup_seen', {
    'notice_id': post_ids['excluded'],
}) == {'ok': False}
assert rpc(system, 'irg.forum.notice.global.seen', 'search_count', [[
    ('user_id', '=', multicourse), ('post_id', '=', post_ids['excluded']),
]]) == 0
print('batch_exclusion: PASS')

with system.open(base + '/?debug=assets', timeout=30) as response:
    page = response.read().decode()
    assert response.status == 200
urls = sorted(set(re.findall(
    r'(?:src|href)=[\"\']([^\"\']*/web/assets/debug/[^\"\']+)[\"\']',
    page,
)))
texts = []
for url in urls:
    with system.open(base + url, timeout=30) as response:
        assert response.status == 200
        texts.append(response.read().decode())
bundle = '\n'.join(texts)
counts = {
    'replacement': bundle.count(
        '/irg_forum_notice_global_seen/static/src/js/forum_notice_popup.js'
    ),
    'parent_popup': bundle.count(
        '/irg_forum_notice_popup/static/src/js/forum_notice_popup.js'
    ),
    'share_override': bundle.count(
        '/irg_forum_notice_popup/static/src/js/forum_share_override.js'
    ),
    'parent_scss': bundle.count(
        '/irg_forum_notice_popup/static/src/scss/forum_notice_popup.scss'
    ),
}
assert counts == {
    'replacement': 1,
    'parent_popup': 0,
    'share_override': 1,
    'parent_scss': 1,
}
print('live_assets: PASS ' + json.dumps(counts, sort_keys=True))
print(f'live_asset_urls_fetched={len(urls)}')
