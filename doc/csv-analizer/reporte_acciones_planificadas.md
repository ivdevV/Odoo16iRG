# Reporte: Acciones Planificadas (ir.cron) — Odoo 16 IRG/ISEP

**Fecha de análisis:** 27 de abril de 2026
**Fuente de datos:** `doc/csv-analizer/Acciones planificadas (ir.cron).xlsx`
**Base:** Servidor de producción Odoo 16 IRG/ISEP

---

## Resumen ejecutivo

Se analizaron **122 acciones planificadas** (`ir.cron`) activas en el servidor de producción.
De ellas, **84 están activas** y **38 inactivas**.

| Categoría | Cantidad | % del total |
|---|---|---|
| 🔧 Custom IRG/ISEP | **39** | 32.0% |
| 📦 OCA / Terceros | **29** | 23.8% |
| 🏠 Nativo Odoo | **54** | 44.3% |
| ❓ No identificadas | **0** | 0.0% |
| **TOTAL** | **122** | 100% |

> **Confianza de clasificación:**
> - Alta (match exacto en XML): 49 acciones
> - Media (match parcial/heurística): 73 acciones
> - Baja (suposición): 0 acciones

---

## 1. Acciones Custom IRG/ISEP

**39 acciones** son propias del proyecto IRG/ISEP.
- Confianza alta (match en XML): 37
- Confianza media (match parcial): 2

### 1.1 Por módulo

| Módulo | Categoría | Nº crons | Activos | Acciones |
|---|---|---|---|---|
| `isep_sale_order_cron_payment` | addons_uisep | 4 | 0/4 | Venta de suscripción: generar facturas y, Venta de suscripción: Envío de correo de, Generar links de pago para facturas (fut (+1 más) |
| `connect_chatgpt` | addons_uisep | 3 | 2/3 | Cerrado automatico Ticket ChatGPT, Cancelar automatico Ticket ChatGPT, Generar Embbedings masivos Elearning Cha |
| `isep_practices_2` | addons_uisep | 3 | 3/3 | Generar lista de verificación, Enviar Solicitud de firma, Enviar Solicitar Aprobado-En Proceso |
| `isep_gradebook` | addons_uisep | 2 | 1/2 | Calcular Promedios Académicos cuatrimest, Crear Resúmenes de Calificaciones Cuatri |
| `Automation_student_documents_email` | addons_uisep | 2 | 1/2 | Marca de necesitamos documentos, Documentos solicitados por correo |
| `isep_cron_send_mail_time` | addons_uisep | 2 | 1/2 | Envío de correo de link de pago automáti, Envío de correo de link de pago automáti |
| `isep_payment_cron_extend` | addons_uisep | 2 | 0/2 | [NUEVO] Suscripciones: Cobro sobre factu, [Pago] Limpiar registros antiguos de rei |
| `isep_payment_cron` | addons_uisep | 2 | 0/2 | Transacciones de pago erroneas correo, Suscripciones: Cobro sobre factura pendi |
| `irg_auto_verify_user` | addons_uisep | 1 | 1/1 | Auto-verificar usuarios sin karma |
| `knowledge_slides` | addons_uisep | 1 | 1/1 | Knowledge Content Sync |
| `isep_public_content_slides` | addons_uisep | 1 | 1/1 | Convertir slide a txt |
| `isep_openeducat_custom` | addons_uisep | 1 | 1/1 | Actualizar Estado de Grupo/duracion de A |
| `isep_data_call` | addons_uisep | 1 | 1/1 | Datos para llamadas HelpDesk |
| `isep_form_card_link` | addons_uisep | 1 | 1/1 | Envío de link de registro de tarjeta |
| `isep_data_master_make` | addons_uisep | 1 | 1/1 | Datos para Make |
| `ks_dashboard_ninja` | addons_uisep | 1 | 1/1 | Kpi mail cron |
| `isep_elearning_custom` | addons_uisep | 1 | 1/1 | Auto Enroll Students |
| `isep_crm_asig` | addons_uisep | 1 | 1/1 | Ausencias acumuladas: actualiza la canti |
| `dv_slide_channel_custom_inh` | addons_uisep | 1 | 1/1 | Análisis y calificación / Envío a Libret |
| `dv_slide_channel_custom` | addons_uisep | 1 | 1/1 | Calificacion automatica ChatGPT IA certi |
| `isep_website_sale_custom` | addons_uisep | 1 | 1/1 | Enviar Link de  Firma a Compras Website  |
| `isep_crm_asiguser` | addons_uisep | 1 | 1/1 | Crono Asignación de leads |
| `crm_meta_leads` | addons_uisep | 1 | 1/1 | Fetch Facebook Leads |
| `isep_appointments` | addons_uisep | 1 | 1/1 | Penalization Appointment Check |
| `security_user_roles` | addons_uisep | 1 | 1/1 | [Security User Roles] Activate/Block Use |
| `isep_invoice_due_reminders` | addons_uisep | 1 | 0/1 | Recordatorios de vencimiento de facturas |
| `isep_sale_order_account_count` | addons_uisep | 1 | 0/1 | Actualizar conteo de facturas vencidas |

### 1.2 Detalle completo

| # | Nombre de la acción | Activo | Intervalo | Siguiente ejecución | Módulo | Fichero XML | Confianza |
|---|---|---|---|---|---|---|---|
| 1 | Calcular Promedios Académicos cuatrimestre | ✅ | 1 Semanas | 2026-04-29 05:01 | `isep_gradebook` | `.../isep_gradebook/data/cron_admission_summary.xml` | alta |
| 2 | Cerrado automatico Ticket ChatGPT | ✅ | 7 Días | 2026-04-28 18:47 | `connect_chatgpt` | `.../connect_chatgpt/data/cron_close_ticket.xml` | alta |
| 3 | Marca de necesitamos documentos | ✅ | 1 Meses | 2026-04-28 18:47 | `Automation_student_documents_email` | `.../Automation_student_documents_email/data/complate_documents.xml` | alta |
| 4 | Generar lista de verificación | ✅ | 1 Días | 2026-04-28 10:41 | `isep_practices_2` | `addons-extra/addons_uisep/isep_practices_2/data/cron.xml` | alta |
| 5 | Enviar Solicitud de firma | ✅ | 1 Días | 2026-04-28 10:41 | `isep_practices_2` | `addons-extra/addons_uisep/isep_practices_2/data/cron.xml` | alta |
| 6 | Enviar Solicitar Aprobado-En Proceso | ✅ | 1 Días | 2026-04-28 10:41 | `isep_practices_2` | `addons-extra/addons_uisep/isep_practices_2/data/cron.xml` | alta |
| 7 | Auto-verificar usuarios sin karma | ✅ | 1 Días | 2026-04-28 10:32 | `irg_auto_verify_user` | `addons-extra/addons_uisep/irg_auto_verify_user/data/cron.xml` | alta |
| 8 | Knowledge Content Sync | ✅ | 1 Días | 2026-04-28 08:00 | `knowledge_slides` | `addons-extra/addons_uisep/knowledge_slides/data/ir_cron_data.xml` | alta |
| 9 | Envío de correo de link de pago automático a facturas, Recordatorio | ✅ | 3 Días | 2026-04-28 07:00 | `isep_cron_send_mail_time` | `.../isep_cron_send_mail_time/data/cron_sale_order_link.xml` | alta |
| 10 | Convertir slide a txt | ✅ | 1 Días | 2026-04-28 07:00 | `isep_public_content_slides` | `.../isep_public_content_slides/data/ir_cron_data.xml` | alta |
| 11 | Actualizar Estado de Grupo/duracion de Admisiones | ✅ | 1 Días | 2026-04-28 06:00 | `isep_openeducat_custom` | `.../isep_openeducat_custom/data/ir_cron_admission.xml` | alta |
| 12 | Datos para llamadas HelpDesk | ✅ | 1 Días | 2026-04-28 05:08 | `isep_data_call` | `addons-extra/addons_uisep/isep_data_call/data/cron_data_call.xml` | alta |
| 13 | Envío de link de registro de tarjeta | ✅ | 1 Días | 2026-04-28 05:08 | `isep_form_card_link` | `.../isep_form_card_link/data/cron_action.xml` | alta |
| 14 | Datos para Make | ✅ | 1 Días | 2026-04-28 05:06 | `isep_data_master_make` | `.../isep_data_master_make/data/cron_data_make.xml` | alta |
| 15 | Kpi mail cron | ✅ | 1 Días | 2026-04-28 04:46 | `ks_dashboard_ninja` | `.../ks_dashboard_ninja/data/ks_mail_cron.xml` | alta |
| 16 | Auto Enroll Students | ✅ | 1 Días | 2026-04-27 20:49 | `isep_elearning_custom` | `.../isep_elearning_custom/data/cron_batch_slide_channel.xml` | alta |
| 17 | Cancelar automatico Ticket ChatGPT | ✅ | 1 Días | 2026-04-27 18:47 | `connect_chatgpt` | `.../connect_chatgpt/data/cron_close_ticket.xml` | alta |
| 18 | Ausencias acumuladas: actualiza la cantidad de ausencias | ✅ | 1 Días | 2026-04-27 18:42 | `isep_crm_asig` | `—` | media |
| 19 | Análisis y calificación / Envío a Libreta | ✅ | 6 Horas | 2026-04-27 16:36 | `dv_slide_channel_custom_inh` | `.../dv_slide_channel_custom_inh/data/cron_auto_send_library.xml` | alta |
| 20 | Calificacion automatica ChatGPT IA certificaciones | ✅ | 5 Horas | 2026-04-27 12:47 | `dv_slide_channel_custom` | `.../dv_slide_channel_custom/data/cron_auto_score_ia.xml` | alta |
| 21 | Enviar Link de  Firma a Compras Website  | ✅ | 1 Días | 2026-04-27 12:19 | `isep_website_sale_custom` | `.../isep_website_sale_custom/data/automated_actions.xml` | media |
| 22 | Crono Asignación de leads | ✅ | 15 Minutos | 2026-04-27 11:44 | `isep_crm_asiguser` | `addons-extra/addons_uisep/isep_crm_asiguser/data/crono_assign.xml` | alta |
| 23 | Fetch Facebook Leads | ✅ | 30 Minutos | 2026-04-27 11:43 | `crm_meta_leads` | `addons-extra/addons_uisep/crm_meta_leads/data/ir_cron.xml` | alta |
| 24 | Penalization Appointment Check | ✅ | 15 Minutos | 2026-04-27 11:41 | `isep_appointments` | `addons-extra/addons_uisep/isep_appointments/data/ir_cron.xml` | alta |
| 25 | [Security User Roles] Activate/Block Users for Roles | ✅ | 1 Horas | 2026-04-27 11:41 | `security_user_roles` | `addons-extra/addons_uisep/security_user_roles/data/cron.xml` | alta |
| 26 | Recordatorios de vencimiento de facturas | ❌ | 1 Días | 2026-03-27 09:38 | `isep_invoice_due_reminders` | `.../isep_invoice_due_reminders/data/cron.xml` | alta |
| 27 | Envío de correo de link de pago automático por tiempo - Recordatorio | ❌ | 1 Días | 2026-03-10 10:43 | `isep_cron_send_mail_time` | `.../isep_cron_send_mail_time/data/cron_sale_order_link.xml` | alta |
| 28 | Venta de suscripción: generar facturas y pagos recurrentes Actualizado | ❌ | 1 Días | 2026-03-10 10:43 | `isep_sale_order_cron_payment` | `.../isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml` | alta |
| 29 | Venta de suscripción: Envío de correo de link de pago automático | ❌ | 1 Días | 2026-03-10 10:43 | `isep_sale_order_cron_payment` | `.../isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml` | alta |
| 30 | [NUEVO] Suscripciones: Cobro sobre factura pendiente Segmentada | ❌ | 1 Días | 2026-03-03 15:26 | `isep_payment_cron_extend` | `addons-extra/addons_uisep/isep_payment_cron_extend/data/cron.xml` | alta |
| 31 | [Pago] Limpiar registros antiguos de reintentos | ❌ | 1 Días | 2026-03-03 15:26 | `isep_payment_cron_extend` | `addons-extra/addons_uisep/isep_payment_cron_extend/data/cron.xml` | alta |
| 32 | Crear Resúmenes de Calificaciones Cuatrimestre | ❌ | 1 Días | 2025-10-02 05:01 | `isep_gradebook` | `.../isep_gradebook/data/cron_admission_summary.xml` | alta |
| 33 | Generar links de pago para facturas (futuro 3 meses) | ❌ | 1 Días | 2025-10-01 04:52 | `isep_sale_order_cron_payment` | `.../isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml` | alta |
| 34 | Generar Facturas desde Cronograma de Suscripción | ❌ | 1 Días | 2025-10-01 04:52 | `isep_sale_order_cron_payment` | `.../isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml` | alta |
| 35 | Transacciones de pago erroneas correo | ❌ | 1 Semanas | 2025-10-01 04:45 | `isep_payment_cron` | `addons-extra/addons_uisep/isep_payment_cron/data/cron.xml` | alta |
| 36 | Suscripciones: Cobro sobre factura pendiente | ❌ | 1 Días | 2025-09-30 10:54 | `isep_payment_cron` | `addons-extra/addons_uisep/isep_payment_cron/data/cron.xml` | alta |
| 37 | Documentos solicitados por correo | ❌ | 1 Meses | 2025-05-28 18:47 | `Automation_student_documents_email` | `.../Automation_student_documents_email/data/autosend_template.xml` | alta |
| 38 | Actualizar conteo de facturas vencidas | ❌ | 1 Días | 2025-05-07 18:46 | `isep_sale_order_account_count` | `.../isep_sale_order_account_count/data/sale_order_cron.xml` | alta |
| 39 | Generar Embbedings masivos Elearning ChatGPT | ❌ | 1 Meses | 2025-01-28 17:47 | `connect_chatgpt` | `.../connect_chatgpt/data/cron_close_ticket.xml` | alta |

---

## 2. Acciones OCA / Terceros

**29 acciones** provienen de módulos OCA o de proveedores externos.

| # | Nombre de la acción | Activo | Modelo | Intervalo | Módulo | Categoría | Confianza |
|---|---|---|---|---|---|---|---|
| 1 | Automated ppc maturity Scheduler | ✅ | Affiliate Visit Model | 1 Meses | `affiliate_management` | addons-extend | alta |
| 2 | Recordatorio materiales | ✅ | Recordatorio materiales | 1 Días | `openeducat_core` | terceros | media |
| 3 | Vaciado automático de la cola de trabajos | ✅ | Cola de trabajos | 1 Días | `queue_job` | terceros | media |
| 4 | Auto-generate date ranges | ✅ | Tipo de rango de fechas | 1 Días | `date_range` | addons-extend | alta |
| 5 | Account Report Followup; Execute followup | ✅ | Contacto | 1 Días | `account_followup` | ent_addons | alta |
| 6 | Automated invoice Scheduler | ✅ | Affiliate Visit Model | 1 Días | `affiliate_management` | addons-extend | alta |
| 7 | Expense OCR: Validate Expenses | ✅ | Gasto | 1 Días | `hr_expense_extract` | ent_addons | alta |
| 8 | Expense OCR: Parse Expenses | ✅ | Gasto | 1 Días | `hr_expense_extract` | ent_addons | alta |
| 9 | Parte de hora: Recordatorio mediante correo electrónico para empleados | ✅ | Compañías | 1 Días | `l10n_es_vat_prorate` | localizacion_espanola | media |
| 10 | Parte de horas: Recordatorio mediante correo electrónico para responsables | ✅ | Compañías | 1 Días | `l10n_es_vat_prorate` | localizacion_espanola | media |
| 11 | Recruitment OCR: Validate CV | ✅ | Candidato | 1 Días | `hr_recruitment_extract` | ent_addons | alta |
| 12 | Recruitment OCR: Parse CV | ✅ | Candidato | 1 Días | `hr_recruitment_extract` | ent_addons | alta |
| 13 | Recruitment OCR: Update All Status | ✅ | Candidato | 1 Días | `hr_recruitment_extract` | ent_addons | alta |
| 14 | Moneda: actualizar tasa | ✅ | Compañías | 1 Días | `l10n_es_vat_prorate` | localizacion_espanola | media |
| 15 | Invoice OCR: Validate Invoices | ✅ | Asiento contable | 1 Días | `account_invoice_extract` | ent_addons | alta |
| 16 | Invoice OCR: Parse Invoices | ✅ | Asiento contable | 1 Días | `account_invoice_extract` | ent_addons | alta |
| 17 | Try to reconcile automatically your statement lines | ✅ | Línea de extracto bancario | 1 Días | `account_accountant` | ent_addons | alta |
| 18 | Valoración: ejecutar la valoración de los empleados | ✅ | Compañías | 1 Días | `l10n_es_vat_prorate` | localizacion_espanola | media |
| 19 | Vacío de informes temporales | ✅ | Instancia de informe MIS | 4 Horas | `mis_builder` | terceros | media |
| 20 | Actualización | ✅ | Ajustes de configuración | 55 Minutos | `nomina_cfdi_ee` | addons-mx | media |
| 21 | Correo: servicio de Fetchmail | ✅ | Servidor de correo de entrada | 5 Minutos | `nomina_cfdi_ee` | addons-mx | media |
| 22 | Recolector de basura de trabajos | ✅ | Cola de trabajos | 5 Minutos | `queue_job` | terceros | media |
| 23 | Nómina: Actualizar datos | ❌ | Recibo de nómina | 1 Meses | `nomina_cfdi_ee` | addons-mx | media |
| 24 | Nómina: Generar PDFs | ❌ | Recibo de nómina | 1 Meses | `nomina_cfdi_ee` | addons-mx | media |
| 25 | Factura de tarifas cron | ❌ | Detalles de las tarifas de los estudiantes | 1 Días | `openeducat_admission_enterprise` | terceros | media |
| 26 | Correo postal: procesar cartas en la cola | ❌ | Carta de correo postal | 1 Horas | `l10n_co_edi_jorels` | addons-co | media |
| 27 | Gestión de activos: generar activos | ❌ | Calcular amortizaciones | 1 Días | `nomina_cfdi_ee` | addons-mx | media |
| 28 | Limpiar automáticamente los auditlogs | ❌ | Auditlog - Borrar registros antiguos | 1 Días | `auditlog` | addons-extend | media |
| 29 | EDI: Ejecutar operaciones del servicio web | ❌ | Documento electrónico para un account.move | 1 Días | `edi_account_oca` | edi-framework | media |

---

## 3. Acciones Nativas Odoo

**54 acciones** corresponden a módulos nativos de Odoo 16.

### 3.1 Por módulo Odoo

| Módulo Odoo | Nº crons |
|---|---|
| `account` | 7 |
| `hr_attendance` | 4 |
| `mass_mailing` | 4 |
| `sale_subscription` | 3 |
| `mail` | 3 |
| `gamification` | 2 |
| `website` | 2 |
| `data_merge` | 2 |
| `base` | 2 |
| `data_recycle` | 1 |
| `project` | 1 |
| `website_slides` | 1 |
| `hr_expense` | 1 |
| `purchase` | 1 |
| `hr_work_entry` | 1 |
| `hr_contract` | 1 |
| `google_calendar` | 1 |
| `hr` | 1 |
| `calendar` | 1 |
| `base_automation` | 1 |
| `microsoft_calendar` | 1 |
| `social` | 1 |
| `crm` | 1 |
| `payment` | 1 |
| `sms` | 1 |
| `partner_autocomplete` | 1 |
| `base_setup` | 1 |
| `project_rating` | 1 |
| `digest` | 1 |
| `website_sale` | 1 |
| `event` | 1 |
| `helpdesk` | 1 |
| `hr_holidays` | 1 |
| `crm_lead_scoring` | 1 |

### 3.2 Detalle completo

| # | Nombre de la acción | Activo | Modelo | Intervalo | Módulo Odoo |
|---|---|---|---|---|---|
| 1 | Ludificación: consolidación del seguimiento de karma | ✅ | Seguimiento de cambios de karma | 1 Meses | `gamification` |
| 2 | Hoja de asistencia: semanal | ✅ | Hoja de asistencia | 1 Semanas | `hr_attendance` |
| 3 | Venta de suscripción: Actualizar KPI | ✅ | Pedido de venta | 1 Semanas | `sale_subscription` |
| 4 | Deshabilitar snippets no utilizados | ✅ | Sitio web | 1 Semanas | `website` |
| 5 | Marcar los Mandatos de débitos directo SEPA como Expirados | ✅ | Un mandato bancario genérico | 1 Días | `account` |
| 6 | Actualización del estado de la orden | ✅ | Orden SEPA | 1 Días | `account` |
| 7 | Reciclado de datos: limpiar registros | ✅ | Modelo de reciclado | 1 Días | `data_recycle` |
| 8 | Proyecto: crear tareas recurrentes | ✅ | Recurrencia de tareas | 1 Días | `project` |
| 9 | Courses Content slide to txt | ✅ | Curso abierto | 1 Días | `website_slides` |
| 10 | Hoja de asistencia: diariamente | ✅ | Hoja de asistencia | 1 Días | `hr_attendance` |
| 11 | Hoja de asistencia si la sesión: diariamente | ✅ | Hoja de asistencia | 1 Días | `hr_attendance` |
| 12 | Cuenta: contabilice borradores de entradas con auto_post habilitado y la fecha contable hasta día de hoy | ✅ | Asiento contable | 1 Días | `account` |
| 13 | Fusión de datos: registros limpios | ✅ | Grupo de deduplicación | 1 Días | `data_merge` |
| 14 | Fusión de datos: encontrar registros duplicados | ✅ | Modelo de deduplicación | 1 Días | `data_merge` |
| 15 | Hoja de asistencia: mensual | ✅ | Hoja de asistencia | 1 Meses | `hr_attendance` |
| 16 | OCR de gastos: Actualizar todos los estados | ✅ | Gasto | 1 Días | `hr_expense` |
| 17 | Cuenta: sincronizar diario en línea | ✅ | Diario | 12 Horas | `account` |
| 18 | Transferencias automáticas de cuenta: realizar transferencias | ✅ | Modelo de transferencia de cuenta | 1 Días | `account` |
| 19 | Recordatorio de compra | ✅ | Pedido de compra | 1 Días | `purchase` |
| 20 | Visitante del sitio web: eliminar visitantes inactivos | ✅ | Visitante del sitio web | 1 Días | `website` |
| 21 | Generar entradas de trabajo faltantes | ✅ | Contrato del empleado | 1 Días | `hr_work_entry` |
| 22 | Contrato de RR. HH.: actualizar estado | ✅ | Contrato del empleado | 1 Días | `hr_contract` |
| 23 | Google Calendar: sincronización | ✅ | Usuario | 12 Horas | `google_calendar` |
| 24 | Empleado de RR. HH.: comprobar la validez del permiso de trabajo | ✅ | Empleado | 1 Días | `hr` |
| 25 | Ludificación: comprobación de metas del desafío | ✅ | Desafío de ludificación | 1 Días | `gamification` |
| 26 | Calendario: recordatorio de evento | ✅ | Gestor de alertas del calendario | 1 Días | `calendar` |
| 27 | Usuarios: notificar usuarios no registrados | ✅ | Usuario | 1 Días | `base` |
| 28 | Notificación: eliminar notificaciones con más de 6 meses de antigüedad | ✅ | Notificaciones de mensajes | 1 Días | `mail` |
| 29 | Base: limpieza automática de datos internos | ✅ | Limpieza automática | 1 Días | `base` |
| 30 | Norma de acción básica: revisar y ejecutar | ✅ | Acción automatizada | 144 Minutos | `base_automation` |
| 31 | Outlook: sincronización | ✅ | Usuario | 12 Horas | `microsoft_calendar` |
| 32 | Social: hacer las publicaciones programadas | ✅ | Publicar en redes sociales | 1 Horas | `social` |
| 33 | CRM: enriquecer leads (IAP) | ✅ | Lead/Oportunidad | 1 Horas | `crm` |
| 34 | pago: transacciones posprocesadas | ✅ | Transacción de pago | 10 Minutos | `payment` |
| 35 | SMS: administrador de la cola de SMS | ✅ | SMS salientes | 1 Horas | `sms` |
| 36 | Autocompletar contacto: sincronización con la base de datos remota | ✅ | Sincronización para autocompletar un contacto | 60 Minutos | `partner_autocomplete` |
| 37 | Notificación: enviar notificaciones de mensajes programados | ✅ | Mensajes programados | 1 Horas | `mail` |
| 38 | Depuración de datos: registros de depuración | ❌ | Modelo de depuración | 1 Días | `base_setup` |
| 39 | Marketing automatizado: sincronizar participantes | ❌ | Campaña de marketing | 12 Horas | `mass_mailing` |
| 40 | Marketing automatizado: ejecutar actividades | ❌ | Campaña de marketing | 1 Horas | `mass_mailing` |
| 41 | Proyecto: Enviar calificación | ❌ | Proyecto | 1 Días | `project_rating` |
| 42 | Suscripción de venta: Vencimiento de suscripciones | ❌ | Pedido de venta | 1 Semanas | `sale_subscription` |
| 43 | Correos electrónicos del resumen | ❌ | Resumen | 1 Días | `digest` |
| 44 | Suscripción de venta: Generar pagos y facturas recurrentes | ❌ | Pedido de venta | 1 Días | `sale_subscription` |
| 45 | OCR de facturas: Actualizar todos los estados | ❌ | Asiento contable | 1 Días | `account` |
| 46 | Marketing por correo: fila del proceso | ❌ | Correo masivo | 1 Días | `mass_mailing` |
| 47 | Comercio electrónico: envíe un correo electrónico a los clientes sobre su cesta abandonada | ❌ | Sitio web | 1 Horas | `website_sale` |
| 48 | Evento: planificador de correo | ❌ | Envío automático de correos de eventos | 1 Horas | `event` |
| 49 | Correo: gerente de la cola de correo electrónico | ❌ | Correos electrónicos salientes | 1 Horas | `mail` |
| 50 | Tíquet de asistencia: Cerrar tíquets automáticamente | ❌ | Equipo de servicio de asistencia | 1 Días | `helpdesk` |
| 51 | facturación automática: envío de factura lista | ❌ | Transacción de pago | 1 Días | `account` |
| 52 | Marketing por correo: prueba A/B | ❌ | Campaña UTM | 1 Días | `mass_mailing` |
| 53 | CRM: Asignación de lead | ❌ | Equipo de ventas | 1 None | `hr_holidays` |
| 54 | Puntuación predictiva de leads: volver a calcular las probabilidades automatizadas | ❌ | Lead/Oportunidad | 1 Días | `crm_lead_scoring` |

---

## 4. Áreas funcionales de los crons custom

Los módulos custom cubren las siguientes áreas funcionales:

| Área funcional | Módulos implicados |
|---|---|
| **Pagos y suscripciones** | `isep_sale_order_cron_payment`, `isep_payment_cron`, `isep_payment_cron_extend`, `isep_cron_send_mail_time`, `isep_form_card_link`, `isep_invoice_due_reminders` |
| **Académico / Gradebook** | `isep_gradebook`, `isep_openeducat_custom`, `irg_auto_verify_user` |
| **Prácticas** | `isep_practices_2` |
| **eLearning / Contenido** | `isep_public_content_slides`, `knowledge_slides`, `isep_elearning_custom`, `dv_slide_channel_custom`, `dv_slide_channel_custom_inh` |
| **ChatGPT / IA** | `connect_chatgpt` (3 crons: cerrado, cancelado, embeddings) |
| **CRM / Leads** | `isep_crm_asiguser`, `isep_crm_asig`, `crm_meta_leads` |
| **Datos e integraciones** | `isep_data_call`, `isep_data_master_make` |
| **Documentos estudiantes** | `Automation_student_documents_email` |
| **Misc** | `ks_dashboard_ninja`, `security_user_roles`, `isep_appointments`, `isep_sale_order_account_count`, `isep_website_sale_custom` |

---

## 5. Acciones inactivas — análisis

Hay **38 acciones inactivas**. Detalle:

| # | Nombre de la acción | Origen | Módulo | Intervalo |
|---|---|---|---|---|
| 1 | Recordatorios de vencimiento de facturas | 🔧 custom | `isep_invoice_due_reminders` | 1 Días |
| 2 | Envío de correo de link de pago automático por tiempo - Recordatorio | 🔧 custom | `isep_cron_send_mail_time` | 1 Días |
| 3 | Venta de suscripción: generar facturas y pagos recurrentes Actualizado | 🔧 custom | `isep_sale_order_cron_payment` | 1 Días |
| 4 | Venta de suscripción: Envío de correo de link de pago automático | 🔧 custom | `isep_sale_order_cron_payment` | 1 Días |
| 5 | Depuración de datos: registros de depuración | 🏠 nativo_odoo | `base_setup` | 1 Días |
| 6 | [NUEVO] Suscripciones: Cobro sobre factura pendiente Segmentada | 🔧 custom | `isep_payment_cron_extend` | 1 Días |
| 7 | [Pago] Limpiar registros antiguos de reintentos | 🔧 custom | `isep_payment_cron_extend` | 1 Días |
| 8 | Nómina: Actualizar datos | 📦 oca | `nomina_cfdi_ee` | 1 Meses |
| 9 | Nómina: Generar PDFs | 📦 oca | `nomina_cfdi_ee` | 1 Meses |
| 10 | Marketing automatizado: sincronizar participantes | 🏠 nativo_odoo | `mass_mailing` | 12 Horas |
| 11 | Marketing automatizado: ejecutar actividades | 🏠 nativo_odoo | `mass_mailing` | 1 Horas |
| 12 | Crear Resúmenes de Calificaciones Cuatrimestre | 🔧 custom | `isep_gradebook` | 1 Días |
| 13 | Generar links de pago para facturas (futuro 3 meses) | 🔧 custom | `isep_sale_order_cron_payment` | 1 Días |
| 14 | Generar Facturas desde Cronograma de Suscripción | 🔧 custom | `isep_sale_order_cron_payment` | 1 Días |
| 15 | Transacciones de pago erroneas correo | 🔧 custom | `isep_payment_cron` | 1 Semanas |
| 16 | Suscripciones: Cobro sobre factura pendiente | 🔧 custom | `isep_payment_cron` | 1 Días |
| 17 | Documentos solicitados por correo | 🔧 custom | `Automation_student_documents_email` | 1 Meses |
| 18 | Proyecto: Enviar calificación | 🏠 nativo_odoo | `project_rating` | 1 Días |
| 19 | Suscripción de venta: Vencimiento de suscripciones | 🏠 nativo_odoo | `sale_subscription` | 1 Semanas |
| 20 | Correos electrónicos del resumen | 🏠 nativo_odoo | `digest` | 1 Días |
| 21 | Suscripción de venta: Generar pagos y facturas recurrentes | 🏠 nativo_odoo | `sale_subscription` | 1 Días |
| 22 | Factura de tarifas cron | 📦 oca | `openeducat_admission_enterprise` | 1 Días |
| 23 | Actualizar conteo de facturas vencidas | 🔧 custom | `isep_sale_order_account_count` | 1 Días |
| 24 | OCR de facturas: Actualizar todos los estados | 🏠 nativo_odoo | `account` | 1 Días |
| 25 | Marketing por correo: fila del proceso | 🏠 nativo_odoo | `mass_mailing` | 1 Días |
| 26 | Comercio electrónico: envíe un correo electrónico a los clientes sobre su cesta abandonada | 🏠 nativo_odoo | `website_sale` | 1 Horas |
| 27 | Evento: planificador de correo | 🏠 nativo_odoo | `event` | 1 Horas |
| 28 | Correo postal: procesar cartas en la cola | 📦 oca | `l10n_co_edi_jorels` | 1 Horas |
| 29 | Correo: gerente de la cola de correo electrónico | 🏠 nativo_odoo | `mail` | 1 Horas |
| 30 | Gestión de activos: generar activos | 📦 oca | `nomina_cfdi_ee` | 1 Días |
| 31 | Limpiar automáticamente los auditlogs | 📦 oca | `auditlog` | 1 Días |
| 32 | Tíquet de asistencia: Cerrar tíquets automáticamente | 🏠 nativo_odoo | `helpdesk` | 1 Días |
| 33 | Generar Embbedings masivos Elearning ChatGPT | 🔧 custom | `connect_chatgpt` | 1 Meses |
| 34 | facturación automática: envío de factura lista | 🏠 nativo_odoo | `account` | 1 Días |
| 35 | EDI: Ejecutar operaciones del servicio web | 📦 oca | `edi_account_oca` | 1 Días |
| 36 | Marketing por correo: prueba A/B | 🏠 nativo_odoo | `mass_mailing` | 1 Días |
| 37 | CRM: Asignación de lead | 🏠 nativo_odoo | `hr_holidays` | 1 None |
| 38 | Puntuación predictiva de leads: volver a calcular las probabilidades automatizadas | 🏠 nativo_odoo | `crm_lead_scoring` | 1 Días |

---

## 6. Notas metodológicas

Este reporte fue generado mediante análisis automático del codebase usando tres estrategias:

| Estrategia | Descripción | Confianza resultante |
|---|---|---|
| **A — Match exacto XML** | Búsqueda del nombre de la acción en registros `<record model="ir.cron">` de todos los XML de `addons-extra/` | Alta |
| **A2 — Match parcial XML** | Búsqueda de subcadena del nombre en el índice XML de crons | Media |
| **B — Match por modelo Python** | Extracción de palabras clave del campo `Modelo` y búsqueda en `_name` de ficheros Python | Media |
| **C — Heurística nativa Odoo** | Clasificación por palabras clave conocidas de módulos nativos Odoo 16 | Media |
| **C2 — Heurística OCA/Terceros** | Clasificación por palabras clave de módulos OCA/terceros conocidos | Media |

> **Nota:** Las clasificaciones con confianza *media* deben verificarse manualmente, especialmente
> las que apuntan a `l10n_es_vat_prorate` o `nomina_cfdi_ee` que pueden ser falsos positivos
> de la estrategia B (matching por palabras clave del modelo).

---

*Generado automáticamente por el agente `odoo16_cron_analyzer` — Odoo 16 IRG/ISEP*
