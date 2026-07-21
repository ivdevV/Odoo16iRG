# Forum Notice Global Seen Pattern

## Course-independent identity

When a forum notice can be discovered through more than one course, persist
seen state by `(user_id, post_id)`, not by discovery context.  Keep the course
only as an input to candidate discovery.  Compatibility checks for a legacy
course-scoped table must also query by user and post only.

## Server boundary

Expose authenticated controller routes, not generic-RPC model services.  Make
technical services private and perform post existence and
`_is_visible_for_user(request.env.user)` checks before any `sudo()` lookup or
write.  `sudo()` may be used only for the technical state operation; it must
not decide visibility.

If a legacy seen model remains installed, preserve read compatibility but add
owner-scoped record rules and a server-side create/write/unlink guard.  UI or
ACL controls alone do not prevent an owner from reassigning or mutating a row
through ORM/RPC.

## Frontend replacement gotcha

Replacing a parent asset requires one `remove` entry before the replacement in
the same bundle; verify the resolved `?debug=assets` output.  Polling popups
need a per-post session suppression set plus one in-flight persistence promise
per post.  Suppress before awaiting persistence, and await the same promise
before closing or navigation.  Client suppression is not durable: on a failed
request, redisplay after a full reload is expected.

Treat all notice payload strings as untrusted. Keep the popup skeleton static,
assign title/forum/preview with `textContent`, and create a navigation element
only after parsing the URL and requiring same-origin HTTP(S).

## Concurrent insert recovery

Catch PostgreSQL `UniqueViolation` specifically around the unique insert
savepoint. Catching the broader `IntegrityError` can hide foreign-key or other
integrity failures. A deterministic race regression should synchronize two
independent initial reads, let one transaction commit the unique row, then
force the second through the conflicting insert and verify both recovery and
the single surviving row.
