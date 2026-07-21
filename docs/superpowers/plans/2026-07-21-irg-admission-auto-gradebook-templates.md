# Auto gradebook templates on enrollment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After auto-creating a student gradebook on enroll, assign `gradebook_id` from the course when set, otherwise from canonical diplomado/master templates.

**Architecture:** Bridge addon `irg_admission_auto_gradebook_templates` overrides `op.admission.enroll_student`, calls `super()`, then fills empty `app.gradebook.student.gradebook_id` using course template or type-based canons. Depends on editable-template so writes survive recompute.

**Tech Stack:** Odoo 16, `isep_gradebook`, IRG admission auto-gradebook and diploma template addons, TransactionCase + unittest.mock patch of OpenEduCat enroll.

---

### Task 1: Scaffold module + failing tests

**Files:**
- Create: `addons-extra/extrairg/irg_admission_auto_gradebook_templates/__init__.py`
- Create: `addons-extra/extrairg/irg_admission_auto_gradebook_templates/__manifest__.py`
- Create: `addons-extra/extrairg/irg_admission_auto_gradebook_templates/models/__init__.py`
- Create: `addons-extra/extrairg/irg_admission_auto_gradebook_templates/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_admission_auto_gradebook_templates/tests/test_auto_gradebook_templates.py`

- [ ] **Step 1: Write failing tests** covering course template precedence, diplomado canon, master canon (type + name), other empty, no subject force-write.
- [ ] **Step 2: Run tests expecting FAIL** (missing behavior / empty gradebook_id).

### Task 2: Data + enrollment override

**Files:**
- Create: `addons-extra/extrairg/irg_admission_auto_gradebook_templates/data/gradebook_template_data.xml`
- Create: `addons-extra/extrairg/irg_admission_auto_gradebook_templates/models/op_admission.py`

- [ ] **Step 1: Add Solo Examen XML data** (exam 100%).
- [ ] **Step 2: Implement template resolution + `enroll_student` post-hook**.
- [ ] **Step 3: Run tests expecting PASS**.

### Task 3: Mission artifacts + verify

**Files:**
- Create: `missions/irg-admission-auto-gradebook-templates/plan.md` (link to this plan)
- Create: `missions/irg-admission-auto-gradebook-templates/execution.md`
- Update: verification evidence under mission when docker suite runs

- [ ] **Step 1: Record commands and results in execution.md**
- [ ] **Step 2: Emit verification.json after independent validation**
