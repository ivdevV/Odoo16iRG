# Mission: irg_course_elearning_featured_section

## Scope

Implement a new Odoo 16 custom module that lets administrators configure one global featured eLearning block on `op.course` and render it at the beginning of every related eLearning subject channel.

## Complexity

Tier: `standard`

Justification:

- New module under `addons-extra/extrairg/`.
- Affects a small set of files: models, backend views, frontend QWeb, tests and documentation.
- Logic is bounded to resolving the related `op.course` from a `slide.channel` using existing `op_subject_ids` / `op.course.subject_ids` relationships.
- No authentication, deployment secrets, concurrency, destructive operations or data migrations are involved.

## Plan

1. Add module skeleton `irg_course_elearning_featured_section`.
2. Extend `op.course` with fields for featured block enablement, title, body, optional URL and optional button label.
3. Extend `slide.channel` with helper methods to resolve the related course and featured values.
4. Extend the `op.course` form view to configure the featured block once per course.
5. Extend `website_slides.course_slides_list` to render the block before the normal eLearning content list.
6. Add focused tests for course resolution and featured data exposure.
7. Validate with compile checks, XML parse and Odoo module update/tests in `docker-compose.local.yml`.

## Model Routing

- Orchestrator / Plan: high reasoning model.
- Implementation: standard coding model.
- Validation: standard tester model or direct local validation.
- Documentation: lightweight documentation update.

## Acceptance Criteria

- A featured block can be configured in `op.course`.
- Any `slide.channel` linked to a subject of that course renders the same block in eLearning.
- Empty/disabled featured configuration renders nothing.
- No existing modules are modified.
- `verification.json` status is `passed` with evidence.
