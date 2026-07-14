import json
import urllib.error
import urllib.request
from http.cookiejar import CookieJar


BASE = "http://127.0.0.1:8069"
DB = "test_irg_db"
LOGIN_OPERATOR = "validation.campus.operator@example.test"
LOGIN_FACULTY = "validation.campus.faculty@example.test"
LOGIN_PORTAL = "validation.campus.portal@example.test"
PASSWORD = "ValidationCampus-2026!"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def new_session(follow_redirects=True):
    cookiejar = CookieJar()
    handlers = [urllib.request.HTTPCookieProcessor(cookiejar)]
    if not follow_redirects:
        handlers.append(NoRedirect())
    opener = urllib.request.build_opener(*handlers)
    opener.cookiejar = cookiejar
    return opener


def rpc(session, path, params):
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(
            {"jsonrpc": "2.0", "method": "call", "params": params, "id": 1}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with session.open(request, timeout=30) as response:
        return json.load(response)


def authenticate(login):
    session = new_session()
    payload = rpc(
        session,
        "/web/session/authenticate",
        {"db": DB, "login": login, "password": PASSWORD},
    )
    return session, payload


operator, operator_auth = authenticate(LOGIN_OPERATOR)
assert operator_auth.get("result", {}).get("uid"), operator_auth

portal, portal_auth = authenticate(LOGIN_PORTAL)
portal_uid = portal_auth.get("result", {}).get("uid")
assert portal_uid, portal_auth
with portal.open(BASE + "/my/home", timeout=30) as response:
    before_status = response.status
assert before_status == 200, before_status

search = rpc(
    operator,
    "/web/dataset/call_kw",
    {
        "model": "op.student",
        "method": "search_read",
        "args": [[("user_id.login", "=", LOGIN_PORTAL)]],
        "kwargs": {"fields": ["id", "irg_campus_blocked"], "limit": 1},
    },
)
student = search.get("result", [])[0]
student_id = student["id"]

faculty, faculty_auth = authenticate(LOGIN_FACULTY)
assert faculty_auth.get("result", {}).get("uid"), faculty_auth
faculty_denied = rpc(
    faculty,
    "/web/dataset/call_kw",
    {
        "model": "op.student",
        "method": "action_block_campus_access",
        "args": [[student_id]],
        "kwargs": {},
    },
)
faculty_error_name = faculty_denied.get("error", {}).get("data", {}).get("name")
assert faculty_error_name == "odoo.exceptions.AccessError", faculty_denied

active_after_faculty_denial = rpc(
    operator,
    "/web/dataset/call_kw",
    {
        "model": "res.users",
        "method": "search_read",
        "args": [[("id", "=", portal_uid)]],
        "kwargs": {
            "context": {"active_test": False},
            "fields": ["active"],
            "limit": 1,
        },
    },
)
target_after_faculty_denial = active_after_faculty_denial.get("result", [])[0]
assert target_after_faculty_denial["active"] is True, active_after_faculty_denial

blocked = rpc(
    operator,
    "/web/dataset/call_kw",
    {
        "model": "op.student",
        "method": "action_block_campus_access",
        "args": [[student_id]],
        "kwargs": {},
    },
)
assert "error" not in blocked, blocked

portal_no_redirect = new_session(follow_redirects=False)
for cookie in portal.cookiejar:
    portal_no_redirect.cookiejar.set_cookie(cookie)
try:
    portal_no_redirect.open(BASE + "/my/home", timeout=30)
    raise AssertionError("blocked existing session unexpectedly received a success response")
except urllib.error.HTTPError as response:
    next_status = response.code
    next_location = response.headers.get("Location")
assert next_status in (302, 303), (next_status, next_location)
assert "/web/login" in next_location, next_location

blocked_session, blocked_auth = authenticate(LOGIN_PORTAL)
assert not blocked_auth.get("result", {}).get("uid"), blocked_auth

unblocked = rpc(
    operator,
    "/web/dataset/call_kw",
    {
        "model": "op.student",
        "method": "action_unblock_campus_access",
        "args": [[student_id]],
        "kwargs": {},
    },
)
assert "error" not in unblocked, unblocked

restored_session, restored_auth = authenticate(LOGIN_PORTAL)
restored_uid = restored_auth.get("result", {}).get("uid")
assert restored_uid == portal_uid, restored_auth
with restored_session.open(BASE + "/my/home", timeout=30) as response:
    restored_status = response.status
assert restored_status == 200, restored_status

result = {
    "active_auth_uid": portal_uid,
    "active_portal_status": before_status,
    "faculty_denial_error": faculty_error_name,
    "target_active_after_faculty_denial": target_after_faculty_denial["active"],
    "blocked_existing_session_next_request_status": next_status,
    "blocked_existing_session_location": next_location,
    "blocked_new_auth_uid": blocked_auth.get("result", {}).get("uid"),
    "restored_auth_uid": restored_uid,
    "restored_portal_status": restored_status,
    "redis_session_deletion_asserted": False,
}
print(json.dumps(result, indent=2, sort_keys=True))
