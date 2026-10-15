# Practice slide restrictions — online clone modality resolution

> **For agentic workers:** `missions/irg-practice-slide-online-clone-modality/plan.md` is the canonical mission plan. This file mirrors the implementation steps.

**Goal:** On online clone channels (`irg_homeclass_channel_id` set), resolve enrollment courses from the master channel so modality-tagged sections become visible.

**Architecture:** Soft-check `irg_homeclass_channel_id` inside `_irg_courses_for_channel`; no new module, no hard dependency on convocatorias.

**Tech stack:** Odoo 16, `irg_practice_slide_restrictions`, docker-compose.local.yml.

---

### Task 1: RED — failing test for clone resolution

**Files:**
- Modify: `addons-extra/extrairg/irg_practice_slide_restrictions/tests/test_practice_slide_restrictions.py`

Steps: write test that builds master+subject+enrollment+modality, online clone without subjects, section with required type on clone; assert allow for matching and block without. Run until RED. Then implement.

### Task 2: GREEN — resolve via master

**Files:**
- Modify: `addons-extra/extrairg/irg_practice_slide_restrictions/models/slide_slide.py`
- Modify: `__manifest__.py` version bump

### Task 3: Docs

Update module doc and knowledge gotcha.
