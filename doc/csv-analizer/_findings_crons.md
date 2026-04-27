# Findings: Acciones Planificadas (ir.cron) — 2026-04-27

Análisis del servidor de producción Odoo 16 IRG/ISEP.

Fuente: `doc/csv-analizer/Acciones planificadas (ir.cron).xlsx`


## Resumen

| Métrica | Valor |
|---|---|
| Total acciones analizadas | **122** |
| Activas | **84** |
| Inactivas | **38** |
| Custom IRG/ISEP (alta confianza) | **37** |
| Custom IRG/ISEP (media confianza) | **2** |
| OCA / Terceros | **29** |
| Nativo Odoo | **54** |
| No identificadas | **0** |

## Mapa completo

| # | Nombre de la acción | Activo | Modelo | Intervalo | Origen | Módulo | Categoría | Fichero XML | Confianza |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Automated ppc maturity Scheduler | ✅ | Affiliate Visit Model | 1 Meses | 📦 oca | affiliate_management | addons-extend | .../affiliate_management/data/automated_scheduler_action.xml | alta |
| 2 | Ludificación: consolidación del seguimiento de karma | ✅ | Seguimiento de cambios de karma | 1 Meses | 🏠 nativo_odoo | gamification |  | — | media |
| 3 | Calcular Promedios Académicos cuatrimestre | ✅ | Gradebook Summary | 1 Semanas | 🔧 custom | isep_gradebook | addons_uisep | ...dons_uisep/isep_gradebook/data/cron_admission_summary.xml | alta |
| 4 | Hoja de asistencia: semanal | ✅ | Hoja de asistencia | 1 Semanas | 🏠 nativo_odoo | hr_attendance |  | — | media |
| 5 | Venta de suscripción: Actualizar KPI | ✅ | Pedido de venta | 1 Semanas | 🏠 nativo_odoo | sale_subscription |  | — | media |
| 6 | Cerrado automatico Ticket ChatGPT | ✅ | Tíquet de servicio de asistencia | 7 Días | 🔧 custom | connect_chatgpt | addons_uisep | ...a/addons_uisep/connect_chatgpt/data/cron_close_ticket.xml | alta |
| 7 | Marca de necesitamos documentos | ✅ | Curso abierto | 1 Meses | 🔧 custom | Automation_student_documents_email | addons_uisep | ...ation_student_documents_email/data/complate_documents.xml | alta |
| 8 | Deshabilitar snippets no utilizados | ✅ | Sitio web | 1 Semanas | 🏠 nativo_odoo | website |  | — | media |
| 9 | Generar lista de verificación | ✅ | Practice Request | 1 Días | 🔧 custom | isep_practices_2 | addons_uisep | addons-extra/addons_uisep/isep_practices_2/data/cron.xml | alta |
| 10 | Enviar Solicitud de firma | ✅ | Practice Request | 1 Días | 🔧 custom | isep_practices_2 | addons_uisep | addons-extra/addons_uisep/isep_practices_2/data/cron.xml | alta |
| 11 | Enviar Solicitar Aprobado-En Proceso | ✅ | Practice Request | 1 Días | 🔧 custom | isep_practices_2 | addons_uisep | addons-extra/addons_uisep/isep_practices_2/data/cron.xml | alta |
| 12 | Auto-verificar usuarios sin karma | ✅ | Usuario | 1 Días | 🔧 custom | irg_auto_verify_user | addons_uisep | addons-extra/addons_uisep/irg_auto_verify_user/data/cron.xml | alta |
| 13 | Recordatorio materiales | ✅ | Recordatorio materiales | 1 Días | 📦 oca | openeducat_core | terceros | — | media |
| 14 | Knowledge Content Sync | ✅ | Curso | 1 Días | 🔧 custom | knowledge_slides | addons_uisep | ...extra/addons_uisep/knowledge_slides/data/ir_cron_data.xml | alta |
| 15 | Marcar los Mandatos de débitos directo SEPA como Expirados | ✅ | Un mandato bancario genérico | 1 Días | 🏠 nativo_odoo | account |  | — | media |
| 16 | Actualización del estado de la orden | ✅ | Orden SEPA | 1 Días | 🏠 nativo_odoo | account |  | — | media |
| 17 | Envío de correo de link de pago automático a facturas, Recordatorio | ✅ | Asiento contable | 3 Días | 🔧 custom | isep_cron_send_mail_time | addons_uisep | ...ep/isep_cron_send_mail_time/data/cron_sale_order_link.xml | alta |
| 18 | Convertir slide a txt | ✅ | Content txt of Slide.Slide | 1 Días | 🔧 custom | isep_public_content_slides | addons_uisep | ...ns_uisep/isep_public_content_slides/data/ir_cron_data.xml | alta |
| 19 | Vaciado automático de la cola de trabajos | ✅ | Cola de trabajos | 1 Días | 📦 oca | queue_job | terceros | — | media |
| 20 | Auto-generate date ranges | ✅ | Tipo de rango de fechas | 1 Días | 📦 oca | date_range | addons-extend | addons-extra/addons-extend/date_range/data/ir_cron_data.xml | alta |
| 21 | Actualizar Estado de Grupo/duracion de Admisiones | ✅ | Admisión | 1 Días | 🔧 custom | isep_openeducat_custom | addons_uisep | ...s_uisep/isep_openeducat_custom/data/ir_cron_admission.xml | alta |
| 22 | Datos para llamadas HelpDesk | ✅ | DataMasterCall | 1 Días | 🔧 custom | isep_data_call | addons_uisep | ...extra/addons_uisep/isep_data_call/data/cron_data_call.xml | alta |
| 23 | Envío de link de registro de tarjeta | ✅ | Pedido de venta | 1 Días | 🔧 custom | isep_form_card_link | addons_uisep | ...tra/addons_uisep/isep_form_card_link/data/cron_action.xml | alta |
| 24 | Datos para Make | ✅ | DataMasterMake | 1 Días | 🔧 custom | isep_data_master_make | addons_uisep | ...ddons_uisep/isep_data_master_make/data/cron_data_make.xml | alta |
| 25 | Reciclado de datos: limpiar registros | ✅ | Modelo de reciclado | 1 Días | 🏠 nativo_odoo | data_recycle |  | — | media |
| 26 | Proyecto: crear tareas recurrentes | ✅ | Recurrencia de tareas | 1 Días | 🏠 nativo_odoo | project |  | — | media |
| 27 | Courses Content slide to txt | ✅ | Curso abierto | 1 Días | 🏠 nativo_odoo | website_slides |  | — | media |
| 28 | Hoja de asistencia: diariamente | ✅ | Hoja de asistencia | 1 Días | 🏠 nativo_odoo | hr_attendance |  | — | media |
| 29 | Hoja de asistencia si la sesión: diariamente | ✅ | Hoja de asistencia | 1 Días | 🏠 nativo_odoo | hr_attendance |  | — | media |
| 30 | Kpi mail cron | ✅ | Dashboard Ninja items | 1 Días | 🔧 custom | ks_dashboard_ninja | addons_uisep | ...tra/addons_uisep/ks_dashboard_ninja/data/ks_mail_cron.xml | alta |
| 31 | Account Report Followup; Execute followup | ✅ | Contacto | 1 Días | 📦 oca | account_followup | ent_addons | addons-extra/ent_addons/account_followup/data/cron.xml | alta |
| 32 | Cuenta: contabilice borradores de entradas con auto_post habilitado y la fecha contable hasta día de hoy | ✅ | Asiento contable | 1 Días | 🏠 nativo_odoo | account |  | — | media |
| 33 | Fusión de datos: registros limpios | ✅ | Grupo de deduplicación | 1 Días | 🏠 nativo_odoo | data_merge |  | — | media |
| 34 | Fusión de datos: encontrar registros duplicados | ✅ | Modelo de deduplicación | 1 Días | 🏠 nativo_odoo | data_merge |  | — | media |
| 35 | Hoja de asistencia: mensual | ✅ | Hoja de asistencia | 1 Meses | 🏠 nativo_odoo | hr_attendance |  | — | media |
| 36 | Auto Enroll Students | ✅ | Admisión | 1 Días | 🔧 custom | isep_elearning_custom | addons_uisep | ...p/isep_elearning_custom/data/cron_batch_slide_channel.xml | alta |
| 37 | Cancelar automatico Ticket ChatGPT | ✅ | Tíquet de servicio de asistencia | 1 Días | 🔧 custom | connect_chatgpt | addons_uisep | ...a/addons_uisep/connect_chatgpt/data/cron_close_ticket.xml | alta |
| 38 | Automated invoice Scheduler | ✅ | Affiliate Visit Model | 1 Días | 📦 oca | affiliate_management | addons-extend | .../affiliate_management/data/automated_scheduler_action.xml | alta |
| 39 | Expense OCR: Validate Expenses | ✅ | Gasto | 1 Días | 📦 oca | hr_expense_extract | ent_addons | addons-extra/ent_addons/hr_expense_extract/data/crons.xml | alta |
| 40 | Expense OCR: Parse Expenses | ✅ | Gasto | 1 Días | 📦 oca | hr_expense_extract | ent_addons | addons-extra/ent_addons/hr_expense_extract/data/crons.xml | alta |
| 41 | OCR de gastos: Actualizar todos los estados | ✅ | Gasto | 1 Días | 🏠 nativo_odoo | hr_expense |  | — | media |
| 42 | Parte de hora: Recordatorio mediante correo electrónico para empleados | ✅ | Compañías | 1 Días | 📦 oca | l10n_es_vat_prorate | localizacion_espanola | — | media |
| 43 | Parte de horas: Recordatorio mediante correo electrónico para responsables | ✅ | Compañías | 1 Días | 📦 oca | l10n_es_vat_prorate | localizacion_espanola | — | media |
| 44 | Cuenta: sincronizar diario en línea | ✅ | Diario | 12 Horas | 🏠 nativo_odoo | account |  | — | media |
| 45 | Transferencias automáticas de cuenta: realizar transferencias | ✅ | Modelo de transferencia de cuenta | 1 Días | 🏠 nativo_odoo | account |  | — | media |
| 46 | Recordatorio de compra | ✅ | Pedido de compra | 1 Días | 🏠 nativo_odoo | purchase |  | — | media |
| 47 | Recruitment OCR: Validate CV | ✅ | Candidato | 1 Días | 📦 oca | hr_recruitment_extract | ent_addons | ...a/ent_addons/hr_recruitment_extract/data/ir_cron_data.xml | alta |
| 48 | Recruitment OCR: Parse CV | ✅ | Candidato | 1 Días | 📦 oca | hr_recruitment_extract | ent_addons | ...a/ent_addons/hr_recruitment_extract/data/ir_cron_data.xml | alta |
| 49 | Recruitment OCR: Update All Status | ✅ | Candidato | 1 Días | 📦 oca | hr_recruitment_extract | ent_addons | ...a/ent_addons/hr_recruitment_extract/data/ir_cron_data.xml | alta |
| 50 | Moneda: actualizar tasa | ✅ | Compañías | 1 Días | 📦 oca | l10n_es_vat_prorate | localizacion_espanola | — | media |
| 51 | Invoice OCR: Validate Invoices | ✅ | Asiento contable | 1 Días | 📦 oca | account_invoice_extract | ent_addons | ...s-extra/ent_addons/account_invoice_extract/data/crons.xml | alta |
| 52 | Invoice OCR: Parse Invoices | ✅ | Asiento contable | 1 Días | 📦 oca | account_invoice_extract | ent_addons | ...s-extra/ent_addons/account_invoice_extract/data/crons.xml | alta |
| 53 | Try to reconcile automatically your statement lines | ✅ | Línea de extracto bancario | 1 Días | 📦 oca | account_accountant | ent_addons | addons-extra/ent_addons/account_accountant/data/ir_cron.xml | alta |
| 54 | Visitante del sitio web: eliminar visitantes inactivos | ✅ | Visitante del sitio web | 1 Días | 🏠 nativo_odoo | website |  | — | media |
| 55 | Generar entradas de trabajo faltantes | ✅ | Contrato del empleado | 1 Días | 🏠 nativo_odoo | hr_work_entry |  | — | media |
| 56 | Ausencias acumuladas: actualiza la cantidad de ausencias | ✅ | Asignación de ausencias | 1 Días | 🔧 custom | isep_crm_asig | addons_uisep | — | media |
| 57 | Contrato de RR. HH.: actualizar estado | ✅ | Contrato del empleado | 1 Días | 🏠 nativo_odoo | hr_contract |  | — | media |
| 58 | Valoración: ejecutar la valoración de los empleados | ✅ | Compañías | 1 Días | 📦 oca | l10n_es_vat_prorate | localizacion_espanola | — | media |
| 59 | Google Calendar: sincronización | ✅ | Usuario | 12 Horas | 🏠 nativo_odoo | google_calendar |  | — | media |
| 60 | Empleado de RR. HH.: comprobar la validez del permiso de trabajo | ✅ | Empleado | 1 Días | 🏠 nativo_odoo | hr |  | — | media |
| 61 | Ludificación: comprobación de metas del desafío | ✅ | Desafío de ludificación | 1 Días | 🏠 nativo_odoo | gamification |  | — | media |
| 62 | Calendario: recordatorio de evento | ✅ | Gestor de alertas del calendario | 1 Días | 🏠 nativo_odoo | calendar |  | — | media |
| 63 | Usuarios: notificar usuarios no registrados | ✅ | Usuario | 1 Días | 🏠 nativo_odoo | base |  | — | media |
| 64 | Notificación: eliminar notificaciones con más de 6 meses de antigüedad | ✅ | Notificaciones de mensajes | 1 Días | 🏠 nativo_odoo | mail |  | — | media |
| 65 | Base: limpieza automática de datos internos | ✅ | Limpieza automática | 1 Días | 🏠 nativo_odoo | base |  | — | media |
| 66 | Análisis y calificación / Envío a Libreta | ✅ | Entrada de usuario de la encuesta | 6 Horas | 🔧 custom | dv_slide_channel_custom_inh | addons_uisep | ..._slide_channel_custom_inh/data/cron_auto_send_library.xml | alta |
| 67 | Vacío de informes temporales | ✅ | Instancia de informe MIS | 4 Horas | 📦 oca | mis_builder | terceros | — | media |
| 68 | Norma de acción básica: revisar y ejecutar | ✅ | Acción automatizada | 144 Minutos | 🏠 nativo_odoo | base_automation |  | — | media |
| 69 | Outlook: sincronización | ✅ | Usuario | 12 Horas | 🏠 nativo_odoo | microsoft_calendar |  | — | media |
| 70 | Calificacion automatica ChatGPT IA certificaciones | ✅ | Entrada de usuario de la encuesta | 5 Horas | 🔧 custom | dv_slide_channel_custom | addons_uisep | ...uisep/dv_slide_channel_custom/data/cron_auto_score_ia.xml | alta |
| 71 | Actualización | ✅ | Ajustes de configuración | 55 Minutos | 📦 oca | nomina_cfdi_ee | addons-mx | — | media |
| 72 | Enviar Link de  Firma a Compras Website  | ✅ | Pedido de venta | 1 Días | 🔧 custom | isep_website_sale_custom | addons_uisep | ...uisep/isep_website_sale_custom/data/automated_actions.xml | media |
| 73 | Social: hacer las publicaciones programadas | ✅ | Publicar en redes sociales | 1 Horas | 🏠 nativo_odoo | social |  | — | media |
| 74 | CRM: enriquecer leads (IAP) | ✅ | Lead/Oportunidad | 1 Horas | 🏠 nativo_odoo | crm |  | — | media |
| 75 | Crono Asignación de leads | ✅ | Lead/Oportunidad | 15 Minutos | 🔧 custom | isep_crm_asiguser | addons_uisep | ...xtra/addons_uisep/isep_crm_asiguser/data/crono_assign.xml | alta |
| 76 | Fetch Facebook Leads | ✅ | Lead/Oportunidad | 30 Minutos | 🔧 custom | crm_meta_leads | addons_uisep | addons-extra/addons_uisep/crm_meta_leads/data/ir_cron.xml | alta |
| 77 | pago: transacciones posprocesadas | ✅ | Transacción de pago | 10 Minutos | 🏠 nativo_odoo | payment |  | — | media |
| 78 | SMS: administrador de la cola de SMS | ✅ | SMS salientes | 1 Horas | 🏠 nativo_odoo | sms |  | — | media |
| 79 | Autocompletar contacto: sincronización con la base de datos remota | ✅ | Sincronización para autocompletar un contacto | 60 Minutos | 🏠 nativo_odoo | partner_autocomplete |  | — | media |
| 80 | Penalization Appointment Check | ✅ | Evento de calendario | 15 Minutos | 🔧 custom | isep_appointments | addons_uisep | addons-extra/addons_uisep/isep_appointments/data/ir_cron.xml | alta |
| 81 | Notificación: enviar notificaciones de mensajes programados | ✅ | Mensajes programados | 1 Horas | 🏠 nativo_odoo | mail |  | — | media |
| 82 | [Security User Roles] Activate/Block Users for Roles | ✅ | User Role | 1 Horas | 🔧 custom | security_user_roles | addons_uisep | addons-extra/addons_uisep/security_user_roles/data/cron.xml | alta |
| 83 | Correo: servicio de Fetchmail | ✅ | Servidor de correo de entrada | 5 Minutos | 📦 oca | nomina_cfdi_ee | addons-mx | — | media |
| 84 | Recolector de basura de trabajos | ✅ | Cola de trabajos | 5 Minutos | 📦 oca | queue_job | terceros | — | media |
| 85 | Recordatorios de vencimiento de facturas | ❌ | Asiento contable | 1 Días | 🔧 custom | isep_invoice_due_reminders | addons_uisep | ...tra/addons_uisep/isep_invoice_due_reminders/data/cron.xml | alta |
| 86 | Envío de correo de link de pago automático por tiempo - Recordatorio | ❌ | Asiento contable | 1 Días | 🔧 custom | isep_cron_send_mail_time | addons_uisep | ...ep/isep_cron_send_mail_time/data/cron_sale_order_link.xml | alta |
| 87 | Venta de suscripción: generar facturas y pagos recurrentes Actualizado | ❌ | Pedido de venta | 1 Días | 🔧 custom | isep_sale_order_cron_payment | addons_uisep | ..._order_cron_payment/data/cron_sale_order_link_payment.xml | alta |
| 88 | Venta de suscripción: Envío de correo de link de pago automático | ❌ | Asiento contable | 1 Días | 🔧 custom | isep_sale_order_cron_payment | addons_uisep | ..._order_cron_payment/data/cron_sale_order_link_payment.xml | alta |
| 89 | Depuración de datos: registros de depuración | ❌ | Modelo de depuración | 1 Días | 🏠 nativo_odoo | base_setup |  | — | media |
| 90 | [NUEVO] Suscripciones: Cobro sobre factura pendiente Segmentada | ❌ | Transacción de pago | 1 Días | 🔧 custom | isep_payment_cron_extend | addons_uisep | ...extra/addons_uisep/isep_payment_cron_extend/data/cron.xml | alta |
| 91 | [Pago] Limpiar registros antiguos de reintentos | ❌ | PaymentRetryLog | 1 Días | 🔧 custom | isep_payment_cron_extend | addons_uisep | ...extra/addons_uisep/isep_payment_cron_extend/data/cron.xml | alta |
| 92 | Nómina: Actualizar datos | ❌ | Recibo de nómina | 1 Meses | 📦 oca | nomina_cfdi_ee | addons-mx | — | media |
| 93 | Nómina: Generar PDFs | ❌ | Recibo de nómina | 1 Meses | 📦 oca | nomina_cfdi_ee | addons-mx | — | media |
| 94 | Marketing automatizado: sincronizar participantes | ❌ | Campaña de marketing | 12 Horas | 🏠 nativo_odoo | mass_mailing |  | — | media |
| 95 | Marketing automatizado: ejecutar actividades | ❌ | Campaña de marketing | 1 Horas | 🏠 nativo_odoo | mass_mailing |  | — | media |
| 96 | Crear Resúmenes de Calificaciones Cuatrimestre | ❌ | Admisión | 1 Días | 🔧 custom | isep_gradebook | addons_uisep | ...dons_uisep/isep_gradebook/data/cron_admission_summary.xml | alta |
| 97 | Generar links de pago para facturas (futuro 3 meses) | ❌ | Asiento contable | 1 Días | 🔧 custom | isep_sale_order_cron_payment | addons_uisep | ..._order_cron_payment/data/cron_sale_order_link_payment.xml | alta |
| 98 | Generar Facturas desde Cronograma de Suscripción | ❌ | Pedido de venta | 1 Días | 🔧 custom | isep_sale_order_cron_payment | addons_uisep | ..._order_cron_payment/data/cron_sale_order_link_payment.xml | alta |
| 99 | Transacciones de pago erroneas correo | ❌ | Transacción de pago | 1 Semanas | 🔧 custom | isep_payment_cron | addons_uisep | addons-extra/addons_uisep/isep_payment_cron/data/cron.xml | alta |
| 100 | Suscripciones: Cobro sobre factura pendiente | ❌ | Transacción de pago | 1 Días | 🔧 custom | isep_payment_cron | addons_uisep | addons-extra/addons_uisep/isep_payment_cron/data/cron.xml | alta |
| 101 | Documentos solicitados por correo | ❌ | Contacto | 1 Meses | 🔧 custom | Automation_student_documents_email | addons_uisep | ...mation_student_documents_email/data/autosend_template.xml | alta |
| 102 | Proyecto: Enviar calificación | ❌ | Proyecto | 1 Días | 🏠 nativo_odoo | project_rating |  | — | media |
| 103 | Suscripción de venta: Vencimiento de suscripciones | ❌ | Pedido de venta | 1 Semanas | 🏠 nativo_odoo | sale_subscription |  | — | media |
| 104 | Correos electrónicos del resumen | ❌ | Resumen | 1 Días | 🏠 nativo_odoo | digest |  | — | media |
| 105 | Suscripción de venta: Generar pagos y facturas recurrentes | ❌ | Pedido de venta | 1 Días | 🏠 nativo_odoo | sale_subscription |  | — | media |
| 106 | Factura de tarifas cron | ❌ | Detalles de las tarifas de los estudiantes | 1 Días | 📦 oca | openeducat_admission_enterprise | terceros | — | media |
| 107 | Actualizar conteo de facturas vencidas | ❌ | Pedido de venta | 1 Días | 🔧 custom | isep_sale_order_account_count | addons_uisep | ...ep/isep_sale_order_account_count/data/sale_order_cron.xml | alta |
| 108 | OCR de facturas: Actualizar todos los estados | ❌ | Asiento contable | 1 Días | 🏠 nativo_odoo | account |  | — | media |
| 109 | Marketing por correo: fila del proceso | ❌ | Correo masivo | 1 Días | 🏠 nativo_odoo | mass_mailing |  | — | media |
| 110 | Comercio electrónico: envíe un correo electrónico a los clientes sobre su cesta abandonada | ❌ | Sitio web | 1 Horas | 🏠 nativo_odoo | website_sale |  | — | media |
| 111 | Evento: planificador de correo | ❌ | Envío automático de correos de eventos | 1 Horas | 🏠 nativo_odoo | event |  | — | media |
| 112 | Correo postal: procesar cartas en la cola | ❌ | Carta de correo postal | 1 Horas | 📦 oca | l10n_co_edi_jorels | addons-co | — | media |
| 113 | Correo: gerente de la cola de correo electrónico | ❌ | Correos electrónicos salientes | 1 Horas | 🏠 nativo_odoo | mail |  | — | media |
| 114 | Gestión de activos: generar activos | ❌ | Calcular amortizaciones | 1 Días | 📦 oca | nomina_cfdi_ee | addons-mx | — | media |
| 115 | Limpiar automáticamente los auditlogs | ❌ | Auditlog - Borrar registros antiguos | 1 Días | 📦 oca | auditlog | addons-extend | — | media |
| 116 | Tíquet de asistencia: Cerrar tíquets automáticamente | ❌ | Equipo de servicio de asistencia | 1 Días | 🏠 nativo_odoo | helpdesk |  | — | media |
| 117 | Generar Embbedings masivos Elearning ChatGPT | ❌ | Diapositivas | 1 Meses | 🔧 custom | connect_chatgpt | addons_uisep | ...a/addons_uisep/connect_chatgpt/data/cron_close_ticket.xml | alta |
| 118 | facturación automática: envío de factura lista | ❌ | Transacción de pago | 1 Días | 🏠 nativo_odoo | account |  | — | media |
| 119 | EDI: Ejecutar operaciones del servicio web | ❌ | Documento electrónico para un account.move | 1 Días | 📦 oca | edi_account_oca | edi-framework | — | media |
| 120 | Marketing por correo: prueba A/B | ❌ | Campaña UTM | 1 Días | 🏠 nativo_odoo | mass_mailing |  | — | media |
| 121 | CRM: Asignación de lead | ❌ | Equipo de ventas | 1 None | 🏠 nativo_odoo | hr_holidays |  | — | media |
| 122 | Puntuación predictiva de leads: volver a calcular las probabilidades automatizadas | ❌ | Lead/Oportunidad | 1 Días | 🏠 nativo_odoo | crm_lead_scoring |  | — | media |

## Acciones no identificadas

_Ninguna acción sin identificar._

## Custom IRG/ISEP — detalle

| Nombre de la acción | Módulo | Categoría | Fichero XML | Confianza |
|---|---|---|---|---|
| Calcular Promedios Académicos cuatrimestre | isep_gradebook | addons_uisep | ...s-extra/addons_uisep/isep_gradebook/data/cron_admission_summary.xml | alta |
| Cerrado automatico Ticket ChatGPT | connect_chatgpt | addons_uisep | addons-extra/addons_uisep/connect_chatgpt/data/cron_close_ticket.xml | alta |
| Marca de necesitamos documentos | Automation_student_documents_email | addons_uisep | ...isep/Automation_student_documents_email/data/complate_documents.xml | alta |
| Generar lista de verificación | isep_practices_2 | addons_uisep | addons-extra/addons_uisep/isep_practices_2/data/cron.xml | alta |
| Enviar Solicitud de firma | isep_practices_2 | addons_uisep | addons-extra/addons_uisep/isep_practices_2/data/cron.xml | alta |
| Enviar Solicitar Aprobado-En Proceso | isep_practices_2 | addons_uisep | addons-extra/addons_uisep/isep_practices_2/data/cron.xml | alta |
| Auto-verificar usuarios sin karma | irg_auto_verify_user | addons_uisep | addons-extra/addons_uisep/irg_auto_verify_user/data/cron.xml | alta |
| Knowledge Content Sync | knowledge_slides | addons_uisep | addons-extra/addons_uisep/knowledge_slides/data/ir_cron_data.xml | alta |
| Envío de correo de link de pago automático a facturas, Recordatorio | isep_cron_send_mail_time | addons_uisep | ...addons_uisep/isep_cron_send_mail_time/data/cron_sale_order_link.xml | alta |
| Convertir slide a txt | isep_public_content_slides | addons_uisep | ...extra/addons_uisep/isep_public_content_slides/data/ir_cron_data.xml | alta |
| Actualizar Estado de Grupo/duracion de Admisiones | isep_openeducat_custom | addons_uisep | ...xtra/addons_uisep/isep_openeducat_custom/data/ir_cron_admission.xml | alta |
| Datos para llamadas HelpDesk | isep_data_call | addons_uisep | addons-extra/addons_uisep/isep_data_call/data/cron_data_call.xml | alta |
| Envío de link de registro de tarjeta | isep_form_card_link | addons_uisep | addons-extra/addons_uisep/isep_form_card_link/data/cron_action.xml | alta |
| Datos para Make | isep_data_master_make | addons_uisep | ...ns-extra/addons_uisep/isep_data_master_make/data/cron_data_make.xml | alta |
| Kpi mail cron | ks_dashboard_ninja | addons_uisep | addons-extra/addons_uisep/ks_dashboard_ninja/data/ks_mail_cron.xml | alta |
| Auto Enroll Students | isep_elearning_custom | addons_uisep | ...ddons_uisep/isep_elearning_custom/data/cron_batch_slide_channel.xml | alta |
| Cancelar automatico Ticket ChatGPT | connect_chatgpt | addons_uisep | addons-extra/addons_uisep/connect_chatgpt/data/cron_close_ticket.xml | alta |
| Ausencias acumuladas: actualiza la cantidad de ausencias | isep_crm_asig | addons_uisep | — | media |
| Análisis y calificación / Envío a Libreta | dv_slide_channel_custom_inh | addons_uisep | ...s_uisep/dv_slide_channel_custom_inh/data/cron_auto_send_library.xml | alta |
| Calificacion automatica ChatGPT IA certificaciones | dv_slide_channel_custom | addons_uisep | ...ra/addons_uisep/dv_slide_channel_custom/data/cron_auto_score_ia.xml | alta |
| Enviar Link de  Firma a Compras Website  | isep_website_sale_custom | addons_uisep | ...ra/addons_uisep/isep_website_sale_custom/data/automated_actions.xml | media |
| Crono Asignación de leads | isep_crm_asiguser | addons_uisep | addons-extra/addons_uisep/isep_crm_asiguser/data/crono_assign.xml | alta |
| Fetch Facebook Leads | crm_meta_leads | addons_uisep | addons-extra/addons_uisep/crm_meta_leads/data/ir_cron.xml | alta |
| Penalization Appointment Check | isep_appointments | addons_uisep | addons-extra/addons_uisep/isep_appointments/data/ir_cron.xml | alta |
| [Security User Roles] Activate/Block Users for Roles | security_user_roles | addons_uisep | addons-extra/addons_uisep/security_user_roles/data/cron.xml | alta |
| Recordatorios de vencimiento de facturas | isep_invoice_due_reminders | addons_uisep | addons-extra/addons_uisep/isep_invoice_due_reminders/data/cron.xml | alta |
| Envío de correo de link de pago automático por tiempo - Recordatorio | isep_cron_send_mail_time | addons_uisep | ...addons_uisep/isep_cron_send_mail_time/data/cron_sale_order_link.xml | alta |
| Venta de suscripción: generar facturas y pagos recurrentes Actualizado | isep_sale_order_cron_payment | addons_uisep | .../isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml | alta |
| Venta de suscripción: Envío de correo de link de pago automático | isep_sale_order_cron_payment | addons_uisep | .../isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml | alta |
| [NUEVO] Suscripciones: Cobro sobre factura pendiente Segmentada | isep_payment_cron_extend | addons_uisep | addons-extra/addons_uisep/isep_payment_cron_extend/data/cron.xml | alta |
| [Pago] Limpiar registros antiguos de reintentos | isep_payment_cron_extend | addons_uisep | addons-extra/addons_uisep/isep_payment_cron_extend/data/cron.xml | alta |
| Crear Resúmenes de Calificaciones Cuatrimestre | isep_gradebook | addons_uisep | ...s-extra/addons_uisep/isep_gradebook/data/cron_admission_summary.xml | alta |
| Generar links de pago para facturas (futuro 3 meses) | isep_sale_order_cron_payment | addons_uisep | .../isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml | alta |
| Generar Facturas desde Cronograma de Suscripción | isep_sale_order_cron_payment | addons_uisep | .../isep_sale_order_cron_payment/data/cron_sale_order_link_payment.xml | alta |
| Transacciones de pago erroneas correo | isep_payment_cron | addons_uisep | addons-extra/addons_uisep/isep_payment_cron/data/cron.xml | alta |
| Suscripciones: Cobro sobre factura pendiente | isep_payment_cron | addons_uisep | addons-extra/addons_uisep/isep_payment_cron/data/cron.xml | alta |
| Documentos solicitados por correo | Automation_student_documents_email | addons_uisep | ...uisep/Automation_student_documents_email/data/autosend_template.xml | alta |
| Actualizar conteo de facturas vencidas | isep_sale_order_account_count | addons_uisep | ...addons_uisep/isep_sale_order_account_count/data/sale_order_cron.xml | alta |
| Generar Embbedings masivos Elearning ChatGPT | connect_chatgpt | addons_uisep | addons-extra/addons_uisep/connect_chatgpt/data/cron_close_ticket.xml | alta |

## OCA / Terceros — detalle

| Nombre de la acción | Módulo | Categoría | Fichero XML | Confianza |
|---|---|---|---|---|
| Automated ppc maturity Scheduler | affiliate_management | addons-extend | ...ons-extend/affiliate_management/data/automated_scheduler_action.xml | alta |
| Recordatorio materiales | openeducat_core | terceros | — | media |
| Vaciado automático de la cola de trabajos | queue_job | terceros | — | media |
| Auto-generate date ranges | date_range | addons-extend | addons-extra/addons-extend/date_range/data/ir_cron_data.xml | alta |
| Account Report Followup; Execute followup | account_followup | ent_addons | addons-extra/ent_addons/account_followup/data/cron.xml | alta |
| Automated invoice Scheduler | affiliate_management | addons-extend | ...ons-extend/affiliate_management/data/automated_scheduler_action.xml | alta |
| Expense OCR: Validate Expenses | hr_expense_extract | ent_addons | addons-extra/ent_addons/hr_expense_extract/data/crons.xml | alta |
| Expense OCR: Parse Expenses | hr_expense_extract | ent_addons | addons-extra/ent_addons/hr_expense_extract/data/crons.xml | alta |
| Parte de hora: Recordatorio mediante correo electrónico para empleados | l10n_es_vat_prorate | localizacion_espanola | — | media |
| Parte de horas: Recordatorio mediante correo electrónico para responsables | l10n_es_vat_prorate | localizacion_espanola | — | media |
| Recruitment OCR: Validate CV | hr_recruitment_extract | ent_addons | addons-extra/ent_addons/hr_recruitment_extract/data/ir_cron_data.xml | alta |
| Recruitment OCR: Parse CV | hr_recruitment_extract | ent_addons | addons-extra/ent_addons/hr_recruitment_extract/data/ir_cron_data.xml | alta |
| Recruitment OCR: Update All Status | hr_recruitment_extract | ent_addons | addons-extra/ent_addons/hr_recruitment_extract/data/ir_cron_data.xml | alta |
| Moneda: actualizar tasa | l10n_es_vat_prorate | localizacion_espanola | — | media |
| Invoice OCR: Validate Invoices | account_invoice_extract | ent_addons | addons-extra/ent_addons/account_invoice_extract/data/crons.xml | alta |
| Invoice OCR: Parse Invoices | account_invoice_extract | ent_addons | addons-extra/ent_addons/account_invoice_extract/data/crons.xml | alta |
| Try to reconcile automatically your statement lines | account_accountant | ent_addons | addons-extra/ent_addons/account_accountant/data/ir_cron.xml | alta |
| Valoración: ejecutar la valoración de los empleados | l10n_es_vat_prorate | localizacion_espanola | — | media |
| Vacío de informes temporales | mis_builder | terceros | — | media |
| Actualización | nomina_cfdi_ee | addons-mx | — | media |
| Correo: servicio de Fetchmail | nomina_cfdi_ee | addons-mx | — | media |
| Recolector de basura de trabajos | queue_job | terceros | — | media |
| Nómina: Actualizar datos | nomina_cfdi_ee | addons-mx | — | media |
| Nómina: Generar PDFs | nomina_cfdi_ee | addons-mx | — | media |
| Factura de tarifas cron | openeducat_admission_enterprise | terceros | — | media |
| Correo postal: procesar cartas en la cola | l10n_co_edi_jorels | addons-co | — | media |
| Gestión de activos: generar activos | nomina_cfdi_ee | addons-mx | — | media |
| Limpiar automáticamente los auditlogs | auditlog | addons-extend | — | media |
| EDI: Ejecutar operaciones del servicio web | edi_account_oca | edi-framework | — | media |

## Nativo Odoo — detalle

| Nombre de la acción | Módulo Odoo | Confianza |
|---|---|---|
| Ludificación: consolidación del seguimiento de karma | gamification | media |
| Hoja de asistencia: semanal | hr_attendance | media |
| Venta de suscripción: Actualizar KPI | sale_subscription | media |
| Deshabilitar snippets no utilizados | website | media |
| Marcar los Mandatos de débitos directo SEPA como Expirados | account | media |
| Actualización del estado de la orden | account | media |
| Reciclado de datos: limpiar registros | data_recycle | media |
| Proyecto: crear tareas recurrentes | project | media |
| Courses Content slide to txt | website_slides | media |
| Hoja de asistencia: diariamente | hr_attendance | media |
| Hoja de asistencia si la sesión: diariamente | hr_attendance | media |
| Cuenta: contabilice borradores de entradas con auto_post habilitado y la fecha contable hasta día de hoy | account | media |
| Fusión de datos: registros limpios | data_merge | media |
| Fusión de datos: encontrar registros duplicados | data_merge | media |
| Hoja de asistencia: mensual | hr_attendance | media |
| OCR de gastos: Actualizar todos los estados | hr_expense | media |
| Cuenta: sincronizar diario en línea | account | media |
| Transferencias automáticas de cuenta: realizar transferencias | account | media |
| Recordatorio de compra | purchase | media |
| Visitante del sitio web: eliminar visitantes inactivos | website | media |
| Generar entradas de trabajo faltantes | hr_work_entry | media |
| Contrato de RR. HH.: actualizar estado | hr_contract | media |
| Google Calendar: sincronización | google_calendar | media |
| Empleado de RR. HH.: comprobar la validez del permiso de trabajo | hr | media |
| Ludificación: comprobación de metas del desafío | gamification | media |
| Calendario: recordatorio de evento | calendar | media |
| Usuarios: notificar usuarios no registrados | base | media |
| Notificación: eliminar notificaciones con más de 6 meses de antigüedad | mail | media |
| Base: limpieza automática de datos internos | base | media |
| Norma de acción básica: revisar y ejecutar | base_automation | media |
| Outlook: sincronización | microsoft_calendar | media |
| Social: hacer las publicaciones programadas | social | media |
| CRM: enriquecer leads (IAP) | crm | media |
| pago: transacciones posprocesadas | payment | media |
| SMS: administrador de la cola de SMS | sms | media |
| Autocompletar contacto: sincronización con la base de datos remota | partner_autocomplete | media |
| Notificación: enviar notificaciones de mensajes programados | mail | media |
| Depuración de datos: registros de depuración | base_setup | media |
| Marketing automatizado: sincronizar participantes | mass_mailing | media |
| Marketing automatizado: ejecutar actividades | mass_mailing | media |
| Proyecto: Enviar calificación | project_rating | media |
| Suscripción de venta: Vencimiento de suscripciones | sale_subscription | media |
| Correos electrónicos del resumen | digest | media |
| Suscripción de venta: Generar pagos y facturas recurrentes | sale_subscription | media |
| OCR de facturas: Actualizar todos los estados | account | media |
| Marketing por correo: fila del proceso | mass_mailing | media |
| Comercio electrónico: envíe un correo electrónico a los clientes sobre su cesta abandonada | website_sale | media |
| Evento: planificador de correo | event | media |
| Correo: gerente de la cola de correo electrónico | mail | media |
| Tíquet de asistencia: Cerrar tíquets automáticamente | helpdesk | media |
| facturación automática: envío de factura lista | account | media |
| Marketing por correo: prueba A/B | mass_mailing | media |
| CRM: Asignación de lead | hr_holidays | media |
| Puntuación predictiva de leads: volver a calcular las probabilidades automatizadas | crm_lead_scoring | media |
