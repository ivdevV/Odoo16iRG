# Módulos: localizacion_espanola

Carpeta con los módulos OCA (Odoo Community Association) de **localización española** para Odoo 16. Contiene los módulos del repositorio `l10n-spain` de OCA: impuestos AEAT, facturae, TicketBAI, SII, libro de IVA, validación de NIF y otras adaptaciones legales para el mercado español.

Todos son módulos de terceros (OCA) y no deben modificarse directamente.

---

## Índice de módulos

### Módulos AEAT (Declaraciones Fiscales)

| Módulo | Descripción |
|--------|-------------|
| l10n_es_aeat | Base de módulos AEAT |
| l10n_es_aeat_mod111 | Modelo 111 — Retenciones IRPF trabajo/actividades |
| l10n_es_aeat_mod115 | Modelo 115 — Retenciones IRPF arrendamientos |
| l10n_es_aeat_mod123 | Modelo 123 — Retenciones IRPF dividendos |
| l10n_es_aeat_mod130 | Modelo 130 — IRPF actividades empresariales |
| l10n_es_aeat_mod190 | Modelo 190 — Resumen anual retenciones |
| l10n_es_aeat_mod216 | Modelo 216 — IRNR retenciones |
| l10n_es_aeat_mod296 | Modelo 296 — IRNR resumen anual |
| l10n_es_aeat_mod303 | Modelo 303 — Declaración periódica IVA |
| l10n_es_aeat_mod303_oss | Modelo 303 — OSS (One Stop Shop) |
| l10n_es_aeat_mod303_vat_prorate | Modelo 303 — Prorrata de IVA |
| l10n_es_aeat_mod347 | Modelo 347 — Operaciones con terceros |
| l10n_es_aeat_mod347_igic | Modelo 347 — IGIC (Canarias) |
| l10n_es_aeat_mod349 | Modelo 349 — Operaciones intracomunitarias |
| l10n_es_aeat_mod369 | Modelo 369 — IVA OSS |
| l10n_es_aeat_mod390 | Modelo 390 — Resumen anual IVA |
| l10n_es_aeat_partner_check | Verificación de NIF en declaraciones AEAT |

### Módulos SII (Suministro Inmediato de Información)

| Módulo | Descripción |
|--------|-------------|
| l10n_es_aeat_sii_oca | SII — Suministro Inmediato de Información (base OCA) |
| l10n_es_aeat_sii_force_type | SII — Forzar tipo de operación |
| l10n_es_aeat_sii_invoice_summary | SII — Resumen de facturas |
| l10n_es_aeat_sii_match | SII — Cotejo de datos |
| l10n_es_aeat_sii_oss | SII — OSS |
| l10n_es_aeat_sii_taxfree | SII — Operaciones exentas |
| l10n_es_dua_sii | SII — DUA (Declaración de Valor en Aduana) |
| l10n_es_irnr_sii | SII — IRNR |
| l10n_es_pos_sii | SII — TPV (Punto de Venta) |

### Módulos de Facturación Electrónica

| Módulo | Descripción |
|--------|-------------|
| l10n_es_facturae | Factura electrónica (FacturaE) |
| l10n_es_facturae_face | FacturaE para FACe (Administración Pública) |
| l10n_es_verifactu_oca | Verifactu (nuevo sistema de verificación de facturas) |
| l10n_es_verifactu_oca_oss | Verifactu con OSS |

### Módulos de Libro de IVA

| Módulo | Descripción |
|--------|-------------|
| l10n_es_vat_book | Libro de registro de IVA |
| l10n_es_vat_book_igic | Libro de IVA para IGIC |
| l10n_es_vat_book_invoice_summary | Resumen de facturas en libro de IVA |
| l10n_es_vat_book_oss | Libro de IVA con OSS |
| l10n_es_vat_prorate | Prorrata de IVA |

### TicketBAI (País Vasco y Navarra)

| Módulo | Descripción |
|--------|-------------|
| l10n_es_ticketbai | TicketBAI base |
| l10n_es_ticketbai_api | API de TicketBAI |
| l10n_es_ticketbai_api_batuz | API TicketBAI Batuz (Bizkaia) |
| l10n_es_ticketbai_batuz | TicketBAI Batuz |

### Módulos de Partners y Localización

| Módulo | Descripción |
|--------|-------------|
| l10n_es_partner | Validación de NIF/CIF de partners españoles |
| l10n_es_partner_mercantil | Datos del Registro Mercantil |
| l10n_es_toponyms | Topónimos de España (municipios, provincias) |
| l10n_es_location_nuts | Codificación NUTS para España |

### Módulos de Pagos y Banca

| Módulo | Descripción |
|--------|-------------|
| l10n_es_account_banking_sepa_fsdd | SEPA adeudo directo (FSDD) |
| l10n_es_account_statement_import_n43 | Importación extractos bancarios N43 |
| l10n_es_payment_order_confirming_aef | Confirming AEF |
| l10n_es_payment_order_confirming_sabadell | Confirming Banco Sabadell |
| payment_redsys | Pasarela de pago Redsys (TPV bancario) |

### Módulos de Impuestos Especiales

| Módulo | Descripción |
|--------|-------------|
| l10n_es_igic | IGIC (Impuesto General Indirecto Canario) |
| l10n_es_irnr | IRNR (Impuesto sobre la Renta de No Residentes) |
| l10n_es_atc | ATC (Administración Tributaria de Canarias) |
| l10n_es_atc_mod415 | Modelo 415 (Canarias) |
| l10n_es_atc_mod420 | Modelo 420 (Canarias) |
| l10n_es_dua | DUA (Declaración de Valor en Aduana) |

### Módulos Contables

| Módulo | Descripción |
|--------|-------------|
| l10n_es_account_asset | Activos fijos para España |
| l10n_es_mis_report | MIS Report para España |
| l10n_es_intrastat_report | Declaración Intrastat |
| l10n_es_sigaus_account | SIGAUS (gestión aceites) — contabilidad |
| l10n_es_sigaus_purchase | SIGAUS — compras |
| l10n_es_sigaus_sale | SIGAUS — ventas |
| l10n_es_sigaus_stock_picking_report_valued | SIGAUS — albaranes valorados |

### TPV (Punto de Venta)

| Módulo | Descripción |
|--------|-------------|
| l10n_es_pos | TPV para España |
| l10n_es_pos_by_device | TPV por dispositivo |

### Otros

| Módulo | Descripción |
|--------|-------------|
| delivery_gls_asm | Transportista GLS/ASM para España |
