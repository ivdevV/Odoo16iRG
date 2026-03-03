# 2026-03-03 — IRG ISEP Cron Update Guard

## 1) Título corto
IRG guard de cron para actualización de módulos

## 2) Resumen objetivo
Evitar bloqueos durante actualización/instalación de módulos en Odoo 16.
Se añade un guard que salta cron críticos de ISEP cuando hay módulos en estado de operación.

## 3) Motivo / justificación
Se detectó bloqueo frecuente de actualizaciones por ejecución simultánea de acciones programadas de alta frecuencia.
Se implementa como módulo extra `irg_` para no tocar módulos nativos ni código de terceros.

## 4) Alcance exacto
- Modelos:
  - `calendar.event` (`_create_penalization`)
  - `payment.transaction` (`_cron_recurring_payment_sale_order`, `_process_invoice_batch`)
- Sin cambios en vistas, assets o reports.

## 5) Diseño técnico
- Nuevo módulo: `addons-extra/extrairg/irg_isep_cron_update_guard`.
- Mixin abstracto: `irg.module.operation.guard.mixin`.
- Regla: si existe `ir.module.module` en `to install|to upgrade|to remove`, se hace early-return en cron.
- Herencia por `_inherit` y `super()`; sin monkey-patching.

## 6) Dependencias
`isep_appointments`, `isep_payment_cron`, `isep_payment_cron_extend`.

## 7) Backwards-compatibility / migración
Compatible con Odoo 16.
Sin migración de datos.
Comportamiento normal de cron se mantiene cuando no hay operación de módulos.

## 8) Casos de prueba / criterios de aceptación
1. Con módulos en operación (`to upgrade`), los métodos cron objetivo no ejecutan lógica pesada.
2. Sin módulos en operación, los métodos cron ejecutan flujo normal vía `super()`.
3. Instalación del módulo no modifica ni requiere cambios en `addons_uisep`.

## 9) Rollback plan
- Desinstalar módulo:
  - `odoo -u base -d <db> --stop-after-init` (si se usa pipeline, revert por commit)
- Revertir commit del módulo `irg_isep_cron_update_guard`.

## 10) Estimación y responsable
Estimación: 1–2 horas (implementación + validación en staging).
Responsable: Equipo iRG / Copilot.
