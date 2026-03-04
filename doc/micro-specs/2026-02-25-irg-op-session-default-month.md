# Micro-spec — IRG OpenEduCat Timetable Default Month

## ID
2026-02-25-irg-op-session-default-month

## Objetivo
Cambiar la vista predeterminada del horario en portal OpenEduCat de `week` a `month`, sin modificar módulos existentes y mediante herencia/override desde un módulo nuevo.

## Alcance
- Módulo nuevo: `addons-extra/extrairg/irg_op_session_default_month`
- Override frontend del widget `openeducat_timetable_enterprise.portal_timetable` para seleccionar `month` por defecto.

## Fuera de alcance
- Cambios en modelo `op.session` backend.
- Cambios de filtros de búsqueda (`Week`/`Month`) en vistas backend.
- Reescritura completa del scheduler Kendo.

## Dependencias
- `openeducat_timetable_enterprise`

## Interfaces afectadas
- `web.assets_frontend`
- Widget portal `PortalTimeTableWidget` (método `InitKendo`).

## Criterios de aceptación
1. Al abrir el horario portal, la vista inicial seleccionada es `month`.
2. Las vistas `day`, `week` y `agenda` continúan disponibles.
3. Instalación/actualización del módulo sin errores XML/JS.

## Plan de implementación
1. Crear módulo `irg_op_session_default_month` en `addons-extra/extrairg/`.
2. Declarar dependencia y asset JS en `__manifest__.py`.
3. Incluir override JS mínimo del método `InitKendo`.
4. Validar sintaxis de manifest/JS y preparar despliegue con `-u`.

## Riesgos y mitigación
- **Riesgo:** Cambios upstream en `openeducat_timetable_enterprise` rompan el include.
- **Mitigación:** Override acotado a un método y verificación funcional post-upgrade.
