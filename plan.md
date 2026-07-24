# Plan: Módulo irg_hide_portal_servicios

## Alcance y Clasificación
- **Nivel de Misión**: `light` (Creación de un nuevo módulo ligero `irg_hide_portal_servicios` en `addons-extra/extrairg/`).
- **Capacidad Requerida**: Standard (Estructura de módulo Odoo 16, vistas XML de portal e inheritance).

## Criterios de Aceptación
1. **Creación del Módulo**: Crear la carpeta `addons-extra/extrairg/irg_hide_portal_servicios` con la estructura estándar de Odoo (`__manifest__.py`, `__init__.py`, `views/portal_templates.xml`).
2. **Dependencias**: Depender de `isep_openeducat_reports` y `portal`.
3. **Ocultamiento de Servicios Adicionales**: Sobreescribir el template `isep_openeducat_reports.portal_my_home_servicios_menu` mediante `xpath` con `position="replace"` para eliminar la entrada "Servicios adicionales" del portal (`/my/home`).
4. **Comprobación de Sintaxis/Validación**: Verificar la correcta sintaxis del manifest y vistas XML.

## Matriz de Roles
- **Orquestador**: Planificación y control del ciclo de vida.
- **Codificador**: Creación de los archivos del módulo Odoo.
- **Revisor**: Revisión del código diff y sintaxis XML.
- **Validador**: Verificación de validez XML y coherencia manifest.
- **Documentador**: Actualización de `execution.md` y `CHANGELOG.md`.

## Fases del Ciclo de Vida
1. **Plan**: `plan.md` y `execution.md` registrados.
2. **Implementación**: Creación de `__manifest__.py`, `__init__.py`, `views/portal_templates.xml`.
3. **Review de Código**: Inspección de diffs y verificación del alcance exacto.
4. **Validación**: Ejecución de check de sintaxis XML y generación de `verification.json`.
5. **Documentación**: Registrar cambios en `execution.md` y `CHANGELOG.md`.
