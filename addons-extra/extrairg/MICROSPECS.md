Microspecs — Spec-Driven Development (light)

Objetivo
- Definir un proceso ligero para elaborar planes de desarrollo (microspecs) para módulos Odoo.

Regla de ubicación
- Todos los nuevos módulos Odoo se crearán en `addons-extra/extrairg`.

Proceso (light)
1. Propósito breve: 1-2 frases que expliquen el objetivo del módulo.
2. Alcance mínimo (MVP): lista corta de funcionalidades imprescindibles.
3. Entregables:
   - Archivos: `__manifest__.py`, `__init__.py`, `models/`, `views/`.
   - Opcional pero recomendado: `security/ir.model.access.csv`, `README.md`, `tests/`, `data/`.
4. Dependencias: enumerar módulos Odoo que debe declarar `depends` en el manifest.
5. Interfaces: vistas, reportes, controladores web públicos, assets.
6. Criterios de aceptación (QA): casos de uso mínimos y pasos de verificación.
7. Tareas de implementación: dividir en subtareas técnicas (modelos, vistas, seguridad, tests).
8. Lanzamiento: pasos para instalar/actualizar el módulo en el entorno (reinicio, actualizar módulo).

Notas prácticas
- Nombre del módulo: usar prefijo `irg_` para módulos locales.
- Estructura: colocar Python en `models/` y JS/CSS en `static/`.
- Manifest: incluir `data` y `demo` necesarios; mantener `installable: True`.
- Seguridad: siempre añadir `ir.model.access.csv` si se crean modelos nuevos.

Uso
- Crear este archivo al empezar un nuevo módulo y enlazarlo desde la issue/ticket correspondiente.
