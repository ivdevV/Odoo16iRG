# Módulos: extrairg

Carpeta principal de desarrollo propio del proyecto IRG/ISEP. Contiene todos los módulos con prefijo `irg_` creados para personalizar y extender Odoo 16 según las necesidades del negocio educativo, así como conectores de terceros comerciales instalados en el entorno.

Los módulos cubren áreas funcionales clave:
- **Foro académico** — notificaciones, karma, visibilidad por lote.
- **Campus / Portal del alumno** — diseño, calendario, asignaturas, prácticas.
- **Comercial / Suscripciones** — checkout, financiación, Stripe, facturas.
- **Calificaciones / Admisiones** — libretas, diplomas, admisión por alumno.
- **CRM** — extensiones, GCLID, deduplicación.
- **Encuestas / eLearning** — auto-puntuación, recalificación, importación TXT.
- **Conectores externos** — Looker Studio, Moodle, Mauit.

---

## Índice de módulos

| Módulo | Descripción | Modelos afectados | Estado |
|--------|-------------|-------------------|--------|
| [irg_forum_batch_visibility](./irg_forum_batch_visibility.md) | Visibilidad del foro por lote/promoción | `website.forum` | Instalable |
| [irg_forum_disable_karma](./irg_forum_disable_karma.md) | Desactiva requisitos de karma en el foro | `website.forum` | Instalable |
| [irg_forum_email_notify](./irg_forum_email_notify.md) | Notificaciones email del foro por lote | `forum.post` | Instalable |
| [irg_forum_followers_post_notify](./irg_forum_followers_post_notify.md) | Notifica a seguidores de posts del foro | `forum.post` | Instalable |
| [irg_forum_notice_popup](./irg_forum_notice_popup.md) | Avisos popup en el foro por lote | `irg.forum.notice` (nuevo) | Instalable |
| [irg_forum_post_comments_limit](./irg_forum_post_comments_limit.md) | Limita el número de comentarios en posts | `forum.post` | Instalable |
| [irg_forum_web_editor_save_guard](./irg_forum_web_editor_save_guard.md) | Guarda JS para el editor del foro | — | Instalable |
| [irg_campus_course_forum](./irg_campus_course_forum.md) | Sección de foro en el perfil del campus | `op.student` | Instalable |
| [irg_website_theme](./irg_website_theme.md) | Tema visual central del sitio web | — | Instalable |
| [irg_timetable_portal_modern_ui](./irg_timetable_portal_modern_ui.md) | UI moderna de calendario en el portal | — | Instalable |
| [irg_timetable_portal_overhaul_v2](./irg_timetable_portal_overhaul_v2.md) | Overhaul estructural v2 del calendario | — | Instalable |
| [irg_timetable_irg_api](./irg_timetable_irg_api.md) | Calendario del portal consumiendo API IRG | — | Instalable |
| [irg_timetable_csv_import](./irg_timetable_csv_import.md) | Importación CSV de sesiones con cron | `irg.timetable.program.map`, `irg.timetable.import.log` (nuevos) | Instalable |
| [irg_timetable_csv_upload_portal](./irg_timetable_csv_upload_portal.md) | Portal web de carga de CSV | `irg.timetable.csv.upload` (nuevo) | Instalable |
| [irg_timetable_lote_batch_fix](./irg_timetable_lote_batch_fix.md) | Fix JS para parámetro batch_id en URL | — | Instalable |
| [irg_timetable_pdf_export](./irg_timetable_pdf_export.md) | Exportación PDF del calendario académico | — | Instalable |
| [irg_timetable_subject_prefix](./irg_timetable_subject_prefix.md) | Prefijo de código de asignatura en títulos | — | Instalable |
| [irg_timetable_session_title_endpoint](./irg_timetable_session_title_endpoint.md) | Integración para títulos de sesión | — | Instalable |
| [irg_op_session_class_title](./irg_op_session_class_title.md) | Nombre del aula en las tarjetas de sesión | `op.session` | Instalable |
| [irg_op_session_default_month](./irg_op_session_default_month.md) | Vista mensual por defecto en el portal | — | Instalable |
| [irg_sale_subscription_esp](./irg_sale_subscription_esp.md) | Override español de suscripción/financiación | `sale.order`, `sale.subscription` | Instalable |
| [irg_payment_stripe_recurring](./irg_payment_stripe_recurring.md) | Pagos recurrentes con Stripe | `payment.token`, `sale.order` | Instalable |
| [irg_subscription_esp_single_invoice](./irg_subscription_esp_single_invoice.md) | Estrategia de factura única de suscripción | `irg.subscription.adjustment`, `irg.stripe.event` (nuevos) | Instalable |
| [irg_website_sale_custom](./irg_website_sale_custom.md) | Personalizaciones del checkout (versión IRG) | `sale.order` | Instalable |
| [irg_website_checkout_fixes](./irg_website_checkout_fixes.md) | Fixes visuales del checkout | — | Instalable |
| [irg_checkout_financing_sign_sync](./irg_checkout_financing_sign_sync.md) | Sincronización financiación con documentos Sign | `sale.order`, `sign.request` | Instalable |
| [irg_website_sale_monthly_price](./irg_website_sale_monthly_price.md) | Precio mensual en tienda (versión IRG) | `product.template` | Instalable |
| [irg_website_sale_monthly_default_combo](./irg_website_sale_monthly_default_combo.md) | Alinea precio mensual con combo por defecto | `product.template` | Instalable |
| [irg_gradebook_certificates](./irg_gradebook_certificates.md) | Solicitud y generación de certificados de notas | `irg.certificate.request` (nuevo) | Instalable |
| [irg_gradebook_autoload_subjects](./irg_gradebook_autoload_subjects.md) | Auto-carga asignaturas al crear libreta | `app.gradebook.student` | Instalable |
| [irg_gradebook_clear_subjects](./irg_gradebook_clear_subjects.md) | Botón para borrar todas las asignaturas de la libreta | `app.gradebook.student` | Instalable |
| [irg_gradebook_exam_as_final](./irg_gradebook_exam_as_final.md) | Nota del examen como nota final | `app.gradebook.subject` | Instalable |
| [irg_admission_auto_gradebook](./irg_admission_auto_gradebook.md) | Auto-crea libreta al matricular alumno | `op.admission`, `op.course` | Instalable |
| [irg_quiz_auto_scoring](./irg_quiz_auto_scoring.md) | Auto-puntuación de cuestionarios y sync con libreta | `survey.user_input` | Instalable |
| [irg_survey_regrade_attempts](./irg_survey_regrade_attempts.md) | Recalificación de intentos de examen | `survey.user_input` | Instalable |
| [irg_survey_second_attempt_fix](./irg_survey_second_attempt_fix.md) | Segundo intento, nota y libreta correcta | `survey.survey`, `survey.user_input` | Instalable |
| [irg_survey_txt_import_feedback](./irg_survey_txt_import_feedback.md) | Importación de preguntas desde TXT | `irg.survey.txt.import.wizard` (nuevo) | Instalable |
| [irg_elearning_styles_rework](./irg_elearning_styles_rework.md) | Rework visual del eLearning | — | Instalable |
| [irg_exam_score_100](./irg_exam_score_100.md) | Campo de compatibilidad escala 100 en surveys | `survey.survey` | Instalable |
| [irg_op_student_admission_editable](./irg_op_student_admission_editable.md) | Popup de admisión editable en ficha del alumno | `op.student`, `op.admission` | Instalable |
| [irg_admissions_by_student](./irg_admissions_by_student.md) | Crea admisiones usando student_id | `sale.order` | Instalable |
| [irg_admission_birthdate_edit](./irg_admission_birthdate_edit.md) | Hace editable birth_date en op.admission | `op.admission` | Instalable |
| [irg_admission_register_export](./irg_admission_register_export.md) | Exportación de admisiones a CSV/XLSX | `irg.admission.export.wizard` (nuevo) | Instalable |
| [irg_auto_translate](./irg_auto_translate.md) | Auto-traducción de cursos y asignaturas con DeepL/Google | `op.course`, `op.subject` | Instalable |
| [irg_course_portal_tiles](./irg_course_portal_tiles.md) | Tiles de acceso rápido en el campus | — | Instalable |
| [irg_crm_extensions](./irg_crm_extensions.md) | Comercial anterior y fecha de reactivación en leads | `crm.lead` | Instalable |
| [irg_crm_gclid](./irg_crm_gclid.md) | Campo GCLID de Google Ads en leads | `crm.lead` | Instalable |
| [irg_crm_lead_dedup](./irg_crm_lead_dedup.md) | Cron de deduplicación de leads por email/teléfono | `crm.lead` | Instalable |
| [irg_custom_discount](./irg_custom_discount.md) | Programas de descuento con fórmulas Python | `irg.discount.program`, `irg.discount.table`, `irg.discount.exception` (nuevos) | Instalable |
| [irg_generacion_diplomas](./irg_generacion_diplomas.md) | Generación de diplomas con QR y número de registro | `irg.diploma.wizard` (nuevo) | Instalable |
| [irg_google_calendar_sync_session_dedupe](./irg_google_calendar_sync_session_dedupe.md) | Evita duplicados en sync con Google Calendar | `op.session` | Instalable |
| [irg_identification_types](./irg_identification_types.md) | Restringe tipos de identificación a DNI/Pasaporte/Doc. | `l10n_latam.identification.type` | Instalable |
| [irg_interactive_content](./irg_interactive_content.md) | Contenido interactivo IA en slides de eLearning | `slide.slide` | Instalable |
| [irg_invoice_payments_sort](./irg_invoice_payments_sort.md) | Ordena pagos de factura por fecha ascendente | `account.move` | Instalable |
| [irg_isep_cron_update_guard](./irg_isep_cron_update_guard.md) | Pausa crons pesados durante actualizaciones | — | Instalable |
| [irg_language_nav](./irg_language_nav.md) | Selector de idioma con ES/EN primero | — | Instalable |
| [irg_op_course_modality](./irg_op_course_modality.md) | Modalidades múltiples de impartición en cursos | `op.course`, `irg.course.modality` | Instalable |
| [irg_op_course_subjects_manage](./irg_op_course_subjects_manage.md) | Gestión de asignaturas desde el formulario del curso | `op.course` | Instalable |
| [irg_op_subject_multi_course](./irg_op_subject_multi_course.md) | Asignatura vinculable a múltiples cursos | `op.subject` | Instalable |
| [irg_op_subject_visibility](./irg_op_subject_visibility.md) | Visibilidad de asignatura por lote | `op.subject`, `slide.channel` | Instalable |
| [irg_portal_placeholder_safe](./irg_portal_placeholder_safe.md) | Valores por defecto para placeholders del portal | — | Instalable |
| [irg_practicas_fix](./irg_practicas_fix.md) | user_id relacionado con el alumno en prácticas | Modelo prácticas | Instalable |
| [irg_practice_center_restrict](./irg_practice_center_restrict.md) | Oculta centros de prácticas al alumno | — | Instalable |
| [irg_profile_batch_fix](./irg_profile_batch_fix.md) | Fix nombre de programa y filtro de calendario por lote | — | Instalable |
| [irg_sign_position_fix](./irg_sign_position_fix.md) | Ajusta posición del bloque de firma en matrícula | `sign.template` | Instalable |
| [irg_sign_reposition](./irg_sign_reposition.md) | Lógica alternativa de reposición de firma | `sign.template`, `sign.item` | Instalable |
| [irg_student_scholarship_documents](./irg_student_scholarship_documents.md) | Gestión de documentación de becas de alumnos | `irg.scholarship.document` (nuevo), `res.partner`, `op.scholarship.type` | Instalable |
| [irg_subject_fix](./irg_subject_fix.md) | Fix de filtrado de asignaturas por lote activo | — | Instalable |
| [irg_web_editor_fix](./irg_web_editor_fix.md) | Guarda JS en OdooEditor para el foro | — | Instalable |
| [looker_connector](./looker_connector.md) | Conector Odoo → Google Looker Studio | — | Instalable |
| [looker_sql_connector](./looker_sql_connector.md) | Conector SQL para Looker Studio | — | Instalable |
| [mauit_roles](./mauit_roles.md) | Roles personalizados para Mauit | — | Instalable |
| [odoo_moodle_connector](./odoo_moodle_connector.md) | Sincronización Odoo ↔ Moodle | — | Instalable |
