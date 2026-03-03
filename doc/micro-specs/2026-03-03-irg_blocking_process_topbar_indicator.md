# 2026-03-03 — IRG Blocking Process Topbar Indicator

## 1) Título corto
Indicador en barra superior de procesos bloqueantes

## 2) Resumen objetivo
Mostrar en la barra superior de backend (`/web`) un punto en vivo:
- rojo cuando hay proceso bloqueante,
- verde cuando no hay bloqueo.

## 3) Motivo / justificación
Las actualizaciones de módulos se ven bloqueadas por procesos concurrentes. Se requiere visibilidad inmediata para operadores sin modificar core de Odoo.

## 4) Alcance exacto
- Módulo: `irg_isep_cron_update_guard`.
- Backend assets (`web.assets_backend`): JS + XML + SCSS para systray.
- Endpoint JSON autenticado para consultar estado de bloqueo.
- Sin cambios en core ni módulos nativos.

## 5) Diseño técnico
- Systray OWL en top bar vía `registry.category("systray")`.
- Polling cada 2s al endpoint `/irg/blocking_process/status`.
- Criterios de bloqueo iniciales:
  - módulos en `to install|to upgrade|to remove`,
  - queries activas tipo módulo/cron en `pg_stat_activity`,
  - queries largas activas (>20s).

## 6) Dependencias
`web`, `isep_appointments`, `isep_payment_cron`, `isep_payment_cron_extend`.

## 7) Backwards-compatibility / migración
Compatible con Odoo 16. Sin migraciones de datos.

## 8) Casos de prueba / criterios de aceptación
1. En `/web`, aparece punto en la barra superior.
2. Si hay bloqueo detectado, el punto está rojo.
3. Cuando no hay bloqueo, el punto cambia a verde en el siguiente ciclo de polling (máx. ~2s).
4. Si falla endpoint, el indicador queda en estado conservador (rojo).

## 9) Rollback plan
- Revertir commit del feature o desinstalar módulo `irg_isep_cron_update_guard`.
- Actualizar módulo sin este asset en despliegue siguiente.

## 10) Estimación y responsable
Estimación: 2–3 horas (implementación + QA).
Responsable: Equipo iRG / Copilot.
