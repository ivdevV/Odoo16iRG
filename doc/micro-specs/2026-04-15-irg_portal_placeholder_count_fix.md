# IRG Portal Placeholder Count Fix

## 1. Título corto
Corrección de errores de JS en badges de contador del portal.

## 2. Resumen objetivo
Prevenir el error `Cannot set properties of null (setting 'textContent')` cuando el portal renderiza badges de contador con `data-placeholder_count` sin que el valor correspondiente exista en el contexto.

## 3. Motivo / justificación
El error se reproduce al acceder como alumno y también desde la vista de alumno en backend. El portal usa placeholders dinámicos para badges como `quotation_count`, `order_count`, `documents_quantity` y `documents_count`; cuando el controlador no devuelve esos valores, el JS del portal intenta actualizar un elemento inexistente.

## 4. Alcance exacto
- Override del controlador `portal.CustomerPortal`.
- Se añade lógica para rellenar valores por defecto en `_prepare_home_portal_values`.
- No se modifican vistas ni assets nativos.

## 5. Diseño técnico
- Nuevo módulo `addons-extra/extrairg/irg_portal_placeholder_count_fix`.
- Hereda el controlador `portal.CustomerPortal` y extiende su método `_prepare_home_portal_values`.
- Añade valores por defecto `0` para los placeholders conocidos que usan `data-placeholder_count`.

## 6. Dependencias
- `portal`

## 7. Compatibilidad / migración
- Compatible con Odoo 16.
- No altera datos existentes.
- Se puede desinstalar sin impacto funcional salvo que se pierda el fallback de contador.

## 8. Casos de prueba / criterios de aceptación
- `CustomerPortal._prepare_home_portal_values` retorna `documents_quantity`, `documents_count`, `quotation_count` y `order_count` con valor `0` si no existen.
- No se rompe el renderizado normal de portal cuando esos valores sí están presentes.
- El error JS reportado deja de aparecer en los menús de portal y en la vista de alumno.

## 9. Rollback plan
- Desinstalar el módulo `irg_portal_placeholder_count_fix`.
- Verificar que el portal vuelve al comportamiento previo.

## 10. Estimación y responsable
- Estimación: 1 hora.
- Responsable: Equipo IRG / desarrollador actual.
