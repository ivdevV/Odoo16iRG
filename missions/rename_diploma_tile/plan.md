# Misión: Renombrar "Diploma del Diplomado" a "Diploma Campus Internacional"

## Alcance y Objetivos
1. Modificar el texto "Diploma del Diplomado" por "Diploma Campus Internacional" en el portal de alumnos de Odoo (en el tile de herramientas de curso del diplomado y en la página de solicitud correspondiente).
2. Actualizar las aserciones de pruebas automatizadas en `test_portal.py` para validar el nuevo texto "Diploma Campus Internacional".
3. Actualizar la documentación técnica del módulo `irg_diplomado_portal_request.md` para reflejar este cambio.

## Clasificación de Complejidad
- **Clasificación:** `standard`
- **Justificación:** Afecta a 3 archivos fuente en el módulo custom `irg_diplomado_portal_request` (vistas XML y un archivo de tests Python) y a 1 archivo de documentación. No hay lógica nueva, borrado de datos o cambios arquitectónicos.

## Modelos Elegidos para cada Fase
- **Plan:** Orquestador (Gemini 3.5 Flash)
- **Implementación:** Codificador (Gemini 3.5 Flash)
- **Validación:** Testeador (Gemini 3.5 Flash)
- **Documentación:** Documentador (Gemini 3.5 Flash)

## Tareas Propuestas
1. Crear el directorio de misión `missions/rename_diploma_tile/`.
2. Modificar el texto en `addons-extra/extrairg/irg_diplomado_portal_request/views/course_portal_tiles.xml`.
3. Modificar el texto en `addons-extra/extrairg/irg_diplomado_portal_request/views/portal_templates.xml`.
4. Modificar el test en `addons-extra/extrairg/irg_diplomado_portal_request/tests/test_portal.py`.
5. Ejecutar la validación con pruebas de Odoo a nivel local.
6. Actualizar `doc/modules/extrairg/irg_diplomado_portal_request.md`.
7. Crear `verification.json` con el resultado y registrar el proceso en `execution.log`.
