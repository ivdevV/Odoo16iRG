# Módulos: addons-extend

Carpeta con módulos OCA y de terceros que complementan el stack base de Odoo 16 para ISEP/IRG. Incluye módulos de banca/SEPA, WhatsApp, integraciones EDI, geolocalización, gestión de colas (Queue Job), helpdesk y otros módulos de soporte.

Todos son módulos de terceros y no deben modificarse directamente.

---

## Grupos funcionales

### Banca y Pagos (OCA)

| Módulo | Descripción |
|--------|-------------|
| account_banking_mandate | Mandatos bancarios (base para SEPA) |
| account_banking_pain_base | Base PAIN (ISO 20022) |
| account_banking_sepa_direct_debit | Adeudo directo SEPA (SDD) |
| account_payment_mode | Modos de pago |
| account_payment_order | Órdenes de pago batch |
| account_payment_partner | Modo de pago por partner |
| account_payment_sale | Modo de pago en ventas |
| base_bank_from_iban | Banco desde IBAN |
| account_due_list | Lista de deudas |
| account_invoice_refund_link | Enlace factura/abono |
| account_tax_balance | Balance de IVA |
| account_financial_report | Informes financieros OCA |
| account_fiscal_position_partner_type | Posición fiscal por tipo de partner |
| account_statement_base | Base de extractos bancarios |
| account_statement_import_base | Base de importación de extractos |
| account_statement_import_file | Importación de extractos desde archivo |

### WhatsApp

| Módulo | Descripción |
|--------|-------------|
| whatsapp_connector | Conector base WhatsApp |
| whatsapp_connector_bot | Bot de WhatsApp |
| whatsapp_connector_chatter | Chatter integrado con WhatsApp |
| whatsapp_connector_crm | WhatsApp en CRM |
| whatsapp_connector_facebook | WhatsApp con Facebook |
| whatsapp_connector_inherited | Herencia del conector WhatsApp |
| whatsapp_connector_mass | Envíos masivos WhatsApp |
| whatsapp_connector_pack | Pack de WhatsApp |
| whatsapp_connector_sale | WhatsApp en ventas |

### EDI y Gestión de Colas

| Módulo | Descripción |
|--------|-------------|
| base_edi | Base EDI |
| component | Componentes (base para Queue Job) |
| component_event | Eventos de componentes |
| queue_job | Gestión de colas de trabajo asíncrono |

### Geolocalización

| Módulo | Descripción |
|--------|-------------|
| base_location | Ubicaciones (ciudad, zip, estado) |
| base_location_geonames_import | Importación de GeoNames |
| base_location_nuts | Codificación NUTS |
| base_iso3166 | ISO 3166 (países, regiones) |

### Intrastat y Comercio Exterior

| Módulo | Descripción |
|--------|-------------|
| intrastat_base | Base de Intrastat |
| intrastat_product | Intrastat de productos |
| l10n_eu_oss_oca | IVA OSS (UE) |
| product_harmonized_system | Sistema Armonizado de productos |

### Reporting

| Módulo | Descripción |
|--------|-------------|
| report_xlsx | Informes XLSX |
| report_xlsx_helper | Helpers XLSX |
| mis_builder | MIS Builder (informes financieros) |
| stock_picking_report_valued | Albarán valorado |

### Helpdesk

| Módulo | Descripción |
|--------|-------------|
| sh_all_in_one_helpdesk | Helpdesk all-in-one (SynconHub) |
| sh_all_in_one_helpdesk_custom | Personalización del helpdesk |

### Otros

| Módulo | Descripción |
|--------|-------------|
| access_restriction_by_ip | Restricción de acceso por IP |
| affiliate_management | Gestión de afiliados |
| auditlog | Log de auditoría de cambios |
| date_range | Rangos de fechas |
| delivery_package_number | Número de paquete de entrega |
| delivery_state | Estado de entrega |
| hr_biometric_machine_zk | Máquina biométrica ZKTeco |
| mail_smtp_imap_by_company | SMTP/IMAP por empresa |
| mail_smtp_imap_by_company_helpdesk | SMTP/IMAP helpdesk por empresa |
| plaid_sync | Sincronización con Plaid (banca) |
| planning_extends | Extensión de planificación |
| res_users_schedules | Horarios de usuarios |
| server_action_mass_edit | Edición masiva con acciones de servidor |
| sh_login_as_other_user | Iniciar sesión como otro usuario |
| wk_redis_session | Sesiones con Redis |
| wk_wizard_messages | Mensajes de wizard |
