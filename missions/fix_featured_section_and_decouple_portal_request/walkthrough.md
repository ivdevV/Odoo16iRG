# Walkthrough of Changes

## Overview
We have resolved the `AccessError` on contents of `op.subject` for e-learning featured sections, decoupled `irg_diplomado_portal_request` from `irg_campus_certificates_portal` dependency, relocated both portal tiles to "Herramientas del curso", and fixed a payment-related validation block in the tests.

## Changes Made

### 1. Slide Channel AccessError Fix
- Modified [slide_channel.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_course_elearning_featured_section/models/slide_channel.py):
  `subjects = self.sudo().op_subject_ids` instead of `self.op_subject_ids.sudo()`. This resolves the `AccessError` on `op.subject` for portal students.

### 2. Decoupling and Relocation of Tiles
- Manifest Update: Removed the dependency of `'irg_campus_certificates_portal'` from [__manifest__.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_diplomado_portal_request/__manifest__.py).
- View Target updates: Relocated both "Diploma del Diplomado" and "Certificados y Diplomas" tiles to the tools row using `//h5[contains(text(), 'Herramientas del curso')]/following-sibling::div[hasclass('row')]` XPath target in [course_portal_tiles.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_diplomado_portal_request/views/course_portal_tiles.xml) and [campus_dashboard_override.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_certificates_portal/views/campus_dashboard_override.xml).
- Added check in certificates tile to hide it on diplomado courses dynamically.

### 3. Exclude Request Invoices from Academic Debt
- Modified [irg_certificate_request.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_academic_request_history/models/irg_certificate_request.py):
  `_get_academic_invoices` was updated to filter out and exclude invoices created for certificate requests. Unpaid optional certificate request invoices no longer count as academic debt to block students from requesting other documents.

## Verification & Tests
- Automated tests run and passed:
  - `irg_campus_certificates_portal`: 8 tests, 0 failed, 0 errors.
  - `irg_diplomado_portal_request`: 3 tests, 0 failed, 0 errors.
