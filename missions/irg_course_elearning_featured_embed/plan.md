# Mission: irg_course_elearning_featured_embed

## Scope

Allow the course-level eLearning featured block to include raw embed code, such as iframe snippets, without relying on the sanitized HTML editor field.

## Complexity

Tier: `standard`

Justification:

- Adds one field to `op.course`, backend view exposure, frontend rendering and test coverage.
- Uses controlled backend configuration and QWeb `Markup` rendering for embed snippets.
- No authentication, deployment secrets, migrations, concurrency or destructive operations are involved.

## Plan

1. Add `irg_featured_section_embed_code` as a plain text field on `op.course`.
2. Show it in the `Destacado eLearning` tab as a code textarea below the standard HTML content.
3. Return it from `slide.channel.irg_get_featured_section_values()` wrapped as `Markup` only after reading from the backend field.
4. Render it below the formatted body in the eLearning featured block.
5. Extend tests to verify iframe/embed code is preserved.
6. Validate Python compile, XML parse and Odoo update/tests in Docker local.

## Acceptance Criteria

- Admins can paste iframe/embed HTML into a dedicated code field.
- The frontend renders the embed snippet in the featured block.
- Existing title/body/button behavior remains unchanged.
- Validation evidence is stored in `verification.json`.
