# IRG Forum Notice Global Seen

`irg_forum_notice_global_seen` makes a forum notice visible at most once to
each authenticated user.  It extends `irg_forum_notice_popup`; install the
parent addon first, then install this addon.

## Install

From the repository root, select the intended database and install the addon:

```bash
irg_forum_seen_db=<database>
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d "$irg_forum_seen_db" \
  -i irg_forum_notice_global_seen --stop-after-init
```

## Update

After deploying a newer version, update the installed addon in the selected
database:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local \
  odoo -c /etc/odoo/odoo.conf -d "$irg_forum_seen_db" \
  -u irg_forum_notice_global_seen --stop-after-init
```

Restart or otherwise reload the frontend assets after updating so the
replacement popup script is served.

## Seen semantics and compatibility

The authoritative identity is `(user_id, post_id)`.  A course may be used to
discover a notice, but never identifies whether it has been seen.  Therefore,
the same post discovered through two courses is dismissed once, while two
different users can each see it once.

Existing `irg.forum.notice.seen` rows remain read-only compatibility data.  A
legacy row for the same user and post suppresses the notice regardless of the
legacy row's course.  This addon does not migrate, modify, or delete legacy
records.

## Visibility and security

The JSON routes require an authenticated, non-public user.  Before a route
looks up or writes technical seen state with `sudo()`, it checks that the post
exists and is visible to the requesting user.  The existing forum, course,
batch and exclusion controls remain the source of truth; in particular, a
batch exclusion prevents discovery and marking.

The new global-seen model has direct ACL access only for system administrators.
Its `_irg_is_seen` and `_irg_mark_seen` services are private and are called by
trusted server code, not generic RPC.  Legacy rows are record-rule scoped to
their owner for internal and portal users, and their create/write/unlink
operations are blocked outside trusted sudo or system-administrator paths.

## Test in an isolated worktree

When working from an isolated worktree, include the mission overlay so the
ephemeral Odoo process mounts that worktree's `addons-extra` directory rather
than changing the shared service:

```bash
docker compose \
  -f /Users/ivrogo/Workspace/Proyectos\ iRG/Odoo16iRG/docker-compose.local.yml \
  -f missions/irg_forum_notice_global_seen/docker-compose.worktree.yml \
  run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_forum_global_seen \
  -i irg_forum_notice_global_seen --test-enable \
  --test-tags /irg_forum_notice_global_seen --stop-after-init --log-level=test
```

The browser end-to-end test may be skipped when the image lacks both the
`websocket-client` Python module and a Chrome/Chromium executable.  The
frontend still suppresses a notice while its persistence request is in flight,
but if that request fails the notice can appear again after a full page reload;
the browser does not treat client-side suppression as authoritative.

Notice titles, forum names and previews are rendered as text, never interpolated
HTML. The “Ver aviso” link is created only for same-origin HTTP(S) URLs;
malformed, cross-origin and non-HTTP(S) values do not produce a navigation link.
