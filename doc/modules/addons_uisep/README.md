# Módulos: addons_uisep

Carpeta principal de módulos del ecosistema ISEP (Universidad/Escuela Superior de Ingeniería de Proyectos). Contiene los módulos base del proyecto desarrollados por y para ISEP, incluyendo el flujo académico completo (admisiones, eLearning, libretas, prácticas), el flujo comercial (suscripciones, pagos, firma electrónica), y los módulos auxiliares del sistema.

Los módulos con prefijo `irg_` son overrides o fixes desarrollados por el equipo iRG sobre los módulos base ISEP. Los módulos con prefijo `isep_` son los módulos core del proyecto. El resto son módulos de terceros o integraciones.

---

## Módulos core ISEP (documentación detallada disponible)

| Módulo | Descripción | Documentación |
|--------|-------------|---------------|
| isep_sale_subscription_extension | Choreographer del calendario de pagos | [Ver doc](./isep_sale_subscription_extension.md) |
| isep_sale_subscription_custom | Base del sistema de pago a plazos | [Ver doc](./isep_sale_subscription_custom.md) |
| isep_sale_order_cron_payment | Cron de facturación anticipada | [Ver doc](./isep_sale_order_cron_payment.md) |
| isep_payment_cron | Cobros recurrentes tokenizados Stripe | [Ver doc](./isep_payment_cron.md) |
| isep_website_sale_custom | Checkout personalizado con campos del alumno | [Ver doc](./isep_website_sale_custom.md) |
| isep_website_sale_monthly_price | Precio mensual en la tienda | [Ver doc](./isep_website_sale_monthly_price.md) |
| isep_openeducat_sale | Auto-creación de admisión desde pedido | [Ver doc](./isep_openeducat_sale.md) |
| isep_openeducat_custom | Personalización base de OpenEduCat | [Ver doc](./isep_openeducat_custom.md) |
| isep_elearning_custom | Personalizaciones del eLearning | [Ver doc](./isep_elearning_custom.md) |
| isep_website_custom | Campus virtual del alumno (base) | [Ver doc](./isep_website_custom.md) |
| isep_website_custom_design | Capa de diseño del campus | [Ver doc](./isep_website_custom_design.md) |
| isep_gradebook | Sistema de libretas de calificaciones | [Ver doc](./isep_gradebook.md) |
| isep_survey | Encuestas/exámenes académicos | [Ver doc](./isep_survey.md) |
| isep_sign_sale | Firma electrónica del contrato de matrícula | [Ver doc](./isep_sign_sale.md) |
| isep_practices | Prácticas externas v1 | [Ver doc](./isep_practices.md) |
| isep_practices_2 | Prácticas externas v2 (con crons y GeoNames) | [Ver doc](./isep_practices_2.md) |
| isep_op_session | Wizard de planificación masiva de sesiones | [Ver doc](./isep_op_session.md) |
| isep_academic_management | Hub de gestión académica / secretaría | [Ver doc](./isep_academic_management.md) |
| payment_flywire | Proveedor de pagos Flywire (internacionales) | [Ver doc](./payment_flywire.md) |

---

## Índice completo de módulos

| Módulo | Descripción resumida | Estado |
|--------|----------------------|--------|
| Automation_student_documents_email | Automatización de envío de documentos a alumnos | Instalable |
| ak_odoo_teams_integration | Integración con Microsoft Teams | Instalable |
| base_automation_webhook | Webhooks para automatizaciones | Instalable |
| chatgpt_base | Base de integración con ChatGPT | Instalable |
| connect_chatgpt | Conector ChatGPT para Odoo | Instalable |
| crm_meta_leads | Leads desde Meta (Facebook/Instagram Ads) | Instalable |
| dec_document | Gestión de documentos DEC | Instalable |
| dependencies_start | Módulo de gestión de dependencias de inicio | Instalable |
| document_processing_with_ai | Procesamiento de documentos con IA | Instalable |
| dv_data_migration | Migración de datos DV | Instalable |
| dv_migration_code | Código de migración DV | Instalable |
| dv_slide_channel_custom | Personalización de canales de slides DV | Instalable |
| dv_slide_channel_custom_inh | Herencia de personalización de canales DV | Instalable |
| elearning_student_ui | UI del alumno en eLearning | Instalable |
| fanlab_odoo_rapport | Reporting FanLab para Odoo | Instalable |
| get_gradebook | Obtención de datos de libreta | Instalable |
| hide_menu_user | Ocultación de menús para usuarios | Instalable |
| irg_auto_verify_user | Auto-verificación de usuarios nuevos | Instalable |
| irg_batch_slide_restrictions | Restricciones de slides por lote | Instalable |
| irg_documents_portal_fix | Fix del portal de documentos | Instalable |
| irg_download_button_removal_fix | Fix eliminación del botón de descarga | Instalable |
| irg_elearning_correo_bienvenida_selector | Selector de correo de bienvenida eLearning | Instalable |
| irg_elearning_editable_sections | Secciones editables en eLearning | Instalable |
| irg_elearning_prerequisites | Prerrequisitos de cursos eLearning | Instalable |
| irg_elearning_restrictions | Restricciones de acceso al eLearning | Instalable |
| irg_elearning_scheduled | eLearning programado | Instalable |
| irg_end_date_fix | Fix de fecha de fin | Instalable |
| irg_google_calendar_sync | Sincronización con Google Calendar | Instalable |
| irg_modalidad_fix | Fix de modalidad de estudio | Instalable |
| irg_openeducat_course_multi_product | Curso vinculado a múltiples productos | Instalable |
| irg_openeducat_sale_lote_custom | Creación de lote personalizada | Instalable |
| irg_pedido_matricula_fix | Fix del pedido de matrícula | Instalable |
| irg_phone_prefix_fix | Fix del prefijo de teléfono | Instalable |
| irg_practicas_fix | Fix de user_id en prácticas | Instalable |
| irg_private_phone_fix | Fix del teléfono privado | Instalable |
| irg_subject_slide_fix | Fix de relación asignatura-slide | Instalable |
| [isep_academic_management](./isep_academic_management.md) | Hub de gestión académica | Instalable |
| isep_account_move_field_static | Campo estático en asientos contables | Instalable |
| isep_account_payment_draft | Pagos en borrador | Instalable |
| isep_account_reports_custom | Informes contables personalizados | Instalable |
| isep_admission_csv_export | Exportación de admisiones a CSV | Instalable |
| isep_admission_from_student_field | Admisión desde campo de alumno | Instalable |
| isep_appointment_payment | Pago para citas/reuniones | Instalable |
| isep_appointments | Gestión de citas | Instalable |
| isep_auth_signup_email | Email de alta de cuenta de alumno | Instalable |
| isep_batch_csv_export | Exportación de lotes a CSV | Instalable |
| isep_bunny_elearning | Integración con Bunny.net para vídeos | Instalable |
| isep_conciliar_estractos | Conciliación de extractos bancarios | Instalable |
| isep_content_interactive | Contenido interactivo (base) | Instalable |
| isep_content_interactive_ext | Extensión de contenido interactivo | Instalable |
| isep_content_interactive_survey | Contenido interactivo con surveys | Instalable |
| isep_control_escolar | Control escolar (matrícula y bajas) | Instalable |
| isep_crm_asig | Asignación de CRM | Instalable |
| isep_crm_asiguser | Asignación de usuario en CRM | Instalable |
| isep_crm_lead_checklist | Checklist de leads en CRM | Instalable |
| isep_cron_send_mail_time | Cron de envío de email en tiempo programado | Instalable |
| isep_custom_ecommerce | Ecommerce personalizado ISEP | Instalable |
| isep_custom_planning | Planificación personalizada | Instalable |
| isep_data_call | Llamadas de datos | Instalable |
| isep_data_master_make | Creación de datos maestros | Instalable |
| isep_documents_portal | Portal de documentos del alumno | Instalable |
| isep_ecommerce_fix | Fixes del ecommerce | Instalable |
| [isep_elearning_custom](./isep_elearning_custom.md) | Personalizaciones del eLearning | Instalable |
| isep_employee_server | Servidor de empleados | Instalable |
| isep_external_video | Vídeos externos en eLearning | Instalable |
| isep_form_card_link | Enlace de tarjeta de formulario | Instalable |
| isep_form_data | Datos de formulario de matrícula | Instalable |
| isep_google_ads | Integración con Google Ads | Instalable |
| isep_gpt_slide_translate | Traducción de slides con GPT | Instalable |
| [isep_gradebook](./isep_gradebook.md) | Libretas de calificaciones | Instalable |
| isep_invoice_due_reminders | Recordatorios de vencimiento de facturas | Instalable |
| isep_mautic_sincrono | Sincronización con Mautic | Instalable |
| isep_notice_view_kanban | Vista kanban de avisos | Instalable |
| isep_op_academic_year | Año académico en OpenEduCat | Instalable |
| [isep_op_session](./isep_op_session.md) | Wizard de sesiones masivas | Instalable |
| isep_op_subject_ext_id | ID externo de asignatura | Instalable |
| [isep_openeducat_custom](./isep_openeducat_custom.md) | Personalización base de OpenEduCat | Instalable |
| isep_openeducat_reports | Informes de OpenEduCat | Instalable |
| [isep_openeducat_sale](./isep_openeducat_sale.md) | Auto-admisión desde pedido de venta | Instalable |
| isep_openeducat_sale_ext | Extensión de ventas OpenEduCat | Instalable |
| isep_openeducat_sale_lote | Creación de lote desde venta | Instalable |
| isep_order_number_admission | Número de pedido en la admisión | Instalable |
| isep_partner_summary_make | Resumen de partner | Instalable |
| [isep_payment_cron](./isep_payment_cron.md) | Cron de cobros tokenizados | Instalable |
| isep_payment_cron_extend | Extensión del cron de cobros | Instalable |
| isep_payment_recurring | Pagos recurrentes base | Instalable |
| isep_portal_certificate_mail | Email de certificados desde el portal | Instalable |
| [isep_practices](./isep_practices.md) | Prácticas externas v1 | Instalable |
| [isep_practices_2](./isep_practices_2.md) | Prácticas externas v2 | Instalable |
| isep_private_phone | Teléfono privado del alumno | Instalable |
| isep_program_sepyc | Programa SEPYC | Instalable |
| isep_public_content_slides | Contenido público en slides | Instalable |
| isep_record_request | Solicitudes de documentos | Instalable |
| isep_record_request_endpoint | Endpoint de documentos | Instalable |
| isep_record_request_extended | Extensión de solicitudes de documentos | Instalable |
| isep_reports_others | Otros informes ISEP | Instalable |
| isep_res_partner_custom | Partner personalizado ISEP | Instalable |
| isep_restrict_portal_modules | Restricción de módulos en el portal | Instalable |
| isep_sale_order_account_count | Contador de facturas en el pedido | Instalable |
| isep_sale_order_admissions | Admisiones desde el pedido de venta | Instalable |
| [isep_sale_order_cron_payment](./isep_sale_order_cron_payment.md) | Cron de facturación anticipada | Instalable |
| isep_sale_order_note | Nota del pedido de venta | Instalable |
| isep_sale_pricelist | Tarifa de precios ISEP | Instalable |
| [isep_sale_subscription_custom](./isep_sale_subscription_custom.md) | Base del pago a plazos | Instalable |
| [isep_sale_subscription_extension](./isep_sale_subscription_extension.md) | Choreographer de pagos/suscripciones | Instalable |
| isep_scorm_elearning | SCORM en eLearning | Instalable |
| isep_share_link_purchase | Enlace de compra compartido | Instalable |
| isep_sign_custom | Firma electrónica personalizada | Instalable |
| [isep_sign_sale](./isep_sign_sale.md) | Firma del contrato de matrícula | Instalable |
| isep_sign_sale_ext | Extensión de firma en ventas | Instalable |
| isep_slide_article_custom | Artículos personalizados en slides | Instalable |
| isep_student_access | Control de acceso del alumno | Instalable |
| isep_student_credential | Credenciales del alumno | Instalable |
| isep_student_filter | Filtros de alumnos | Instalable |
| isep_student_migration | Migración de alumnos | Instalable |
| isep_subject_precedence | Precedencias de asignaturas | Instalable |
| [isep_survey](./isep_survey.md) | Encuestas/exámenes académicos | Instalable |
| isep_survey_attachment | Adjuntos en encuestas | Instalable |
| isep_survey_input_view | Vista de respuestas de encuesta | Instalable |
| isep_survey_question_result | Resultados de preguntas de encuesta | Instalable |
| isep_tag_custom | Etiquetas personalizadas | Instalable |
| isep_tesis_model | Modelo de tesis/TFM | Instalable |
| isep_time_link_url | URL de enlace temporal | Instalable |
| isep_titulation_custom | Titulación personalizada | Instalable |
| isep_typeform_custom | Typeform personalizado | Instalable |
| isep_update_pass_user | Actualización de contraseña de usuario | Instalable |
| isep_update_pass_user_ext | Extensión actualización de contraseña | Instalable |
| isep_upload_forum | Subida de archivos al foro | Instalable |
| [isep_website_custom](./isep_website_custom.md) | Campus virtual del alumno (base) | Instalable |
| [isep_website_custom_design](./isep_website_custom_design.md) | Diseño del campus | Instalable |
| isep_website_custom_inh | Herencia del campus virtual | Instalable |
| isep_website_rule_user | Reglas de usuario en el sitio web | Instalable |
| [isep_website_sale_custom](./isep_website_sale_custom.md) | Checkout personalizado | Instalable |
| [isep_website_sale_monthly_price](./isep_website_sale_monthly_price.md) | Precio mensual en tienda | Instalable |
| jh_customizations_affiliate | Personalizaciones de afiliados JH | Instalable |
| knowledge_slides | Knowledge en slides | Instalable |
| ks_dashboard_ninja | Dashboard Ninja (tercero) | Instalable |
| loyalty_program_user | Programa de fidelización por usuario | Instalable |
| mk_typeform | Typeform MK | Instalable |
| payment_active | Proveedor de pago activo | Instalable |
| [payment_flywire](./payment_flywire.md) | Proveedor Flywire (pagos internacionales) | Instalable |
| payment_flywire_logs | Logs de transacciones Flywire | Instalable |
| payment_flywire_recurring | Pagos recurrentes Flywire | Instalable |
| report_certificate_others | Informes de otros certificados | Instalable |
| security_user_roles | Roles de seguridad de usuarios | Instalable |
| theme_silon | Tema visual Silon del sitio web | Instalable |
| uisep_payroll | Nóminas UISEP | Instalable |
| website_slides_customizations | Personalizaciones de website slides | Instalable |
| website_whatsapp | Integración WhatsApp en el sitio web | Instalable |
