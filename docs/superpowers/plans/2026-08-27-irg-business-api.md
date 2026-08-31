# irg_business_api Implementation Plan

> **For agentic workers:** Execute in the worktree `feat/irg-business-api`. Follow AGENTS.md: TDD, independent review, validation, documentation. Merge to `Dev_iRG` only after gates pass.

**Goal:** Installable Odoo 16 facade so Lisa can run closed academic reads and unpublished slide/section writes.

**Architecture:** Command model `irg.api.operation` with server-owned state, allowlisted services, no HTTP, no changes to existing addons.

**Tech Stack:** Odoo 16, OpenEduCat, website_slides, iRG extra addons.

---

See `missions/irg-business-api/plan.md` for classification, acceptance and test commands.
