# Misión: Generación de Diploma de Graduación desde Vista de Estudiante (OpenEduCat)

## Alcance
Crear un módulo personalizado en Odoo 16 (`irg_diploma_graduacion_student`) que permita generar un diploma de graduación en PDF para un estudiante desde su vista en OpenEduCat (`op.student`).
La maquetación se basará en una plantilla `.docx` proporcionada por el usuario, que se procesará mediante `python-docx` y se convertirá a PDF (siguiendo el patrón existente en el proyecto para otros certificados/diplomas).

## Clasificación de Complejidad
- **Tier:** `standard`
- **Justificación:** Requiere la creación de un nuevo módulo en `addons-extra/extrairg/irg_diploma_graduacion_student`, heredar el modelo `op.student`, añadir un botón de acción en la vista de estudiante, programar la lógica del controlador/wizard para procesar la plantilla `.docx` con marcadores dinámicos de campos del estudiante (nombre, curso, fecha, etc.) y realizar la conversión a PDF mediante el servidor de LibreOffice, así como definir las reglas de seguridad ACL correspondientes.

## Modelos Asignados
- **Orquestador (Plan):** Gemini 3.5 Flash (actual)
- **Codificador (Implementación):** Gama estándar
- **Testeador (Validación):** Gama estándar / intermedio
- **Documentador (Documentación):** Gama ligera/barata

## Ruta del Documento Origen (.docx)
El archivo `.docx` original con la maquetación se almacenará en:
`missions/irg_diploma_graduacion_student/artifacts/diploma_graduacion_maquetacion.docx` (o nombre similar provisto).

## Descomposición de Tareas
1. **Fase de Plan:**
   - Crear el plan de misión (`plan.md`).
   - Crear el plan de implementación (`implementation_plan.md`) detallando la estructura del módulo, modelos y vistas a heredar, y variables esperadas en el `.docx`.
   - Esperar aprobación del usuario tras recibir el `.docx`.
2. **Fase de Implementación:**
   - Crear el esqueleto del módulo `irg_diploma_graduacion_student`.
   - Implementar la herencia en `op.student` para agregar el botón de impresión del diploma.
   - Implementar el método python que lee la plantilla `.docx`, realiza los reemplazos de texto dinámicos (nombre del alumno, diplomado, fecha de graduación, etc.) y llama a la conversión a PDF.
   - Definir seguridad y accesos.
3. **Fase de Validación:**
   - Probar la generación localmente con `docker-compose.local.yml`.
   - Generar `verification.json`.
4. **Fase de Documentación:**
   - Escribir manual de uso, dependencias del sistema y el archivo de cambios (Changelog).
