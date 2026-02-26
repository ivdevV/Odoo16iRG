Title: irg_course_portal_tiles — Course-level portal tiles (Calendar, Prácticas, TFM)
Date: 2026-02-26
Author: iRG (automation)

Summary
-------
Add course-level quick tiles (Calendar, Prácticas) to the course profile page and a TFM link under `/campus/course/<id>/tfm`.

Motivation
----------
Previously the tiles were added directly into `isep_website_custom` which violates SPECIFICATIONS.md. This micro-spec defines a small `irg_` module implementing the same UI changes via an inherit+xpath.

Scope
-----
- Create module `irg_course_portal_tiles` under `addons-extra/extrairg/`.
- Add a QWeb template inherit to insert the course-level tiles on the course profile page.
- No new models or server-side logic required.

Files changed
------------
- `addons-extra/extrairg/irg_course_portal_tiles/__manifest__.py`
- `addons-extra/extrairg/irg_course_portal_tiles/views/irg_course_portal_tiles_views.xml`

Acceptance criteria
-------------------
- The course profile page shows the three tiles when module installed.
- No direct edits remain in `isep_website_custom`.
- Module is prefixed with `irg_` and lives in `addons-extra/extrairg/`.

Rollout
-------
Install the module and verify the portal course page under `/campus/course/<id>` displays the tiles.
