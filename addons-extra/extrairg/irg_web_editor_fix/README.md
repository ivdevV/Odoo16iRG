# IRG Web Editor Fix

## Purpose
Prevent frontend crashes in the Odoo WYSIWYG editor when saving forum message edits and the selection anchor node does not expose the expected raw command method.

## What this module changes
- Adds a defensive patch on `OdooEditor._applyRawCommand`.
- Validates method availability on the selection anchor node.
- Applies a fallback on the parent element for text nodes.
- Returns safely when no valid target method exists.

## Scope
- Frontend only (`web_editor.assets_wysiwyg`).
- No database schema changes.
- No server-side business logic changes.

## Dependencies
- `web_editor`
- `website_forum`

## Installation / Update
1. Update apps list.
2. Upgrade module:
   - `odoo -u irg_web_editor_fix -d <yourdb> --stop-after-init`

## Rollback
- Uninstall `irg_web_editor_fix`, or revert the deployment commit and upgrade modules.
