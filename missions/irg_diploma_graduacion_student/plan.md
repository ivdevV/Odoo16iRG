# Misión: Generación de Diploma de Graduación desde Vista de Estudiante (ReportLab A3)

## Alcance
Rediseñar el módulo personalizado `irg_diploma_graduacion_student` para generar el diploma de graduación en formato **A3 horizontal (landscape)** utilizando **ReportLab** en Python directamente. Esto reemplaza el flujo anterior basado en DOCX y LibreOffice, que producía descuadres en cuadros de texto y fuentes, garantizando un resultado vectorial exacto y alineado según la maquetación provista en el PDF del cliente.

## Clasificación de Complejidad
- **Tier:** `standard`
- **Justificación:** Cambio de la tecnología de renderizado de LibreOffice/DOCX a ReportLab. Involucra programar la clase AbstractModel de ReportLab para posicionar coordenadas A3, usar fuentes TTF vectoriales, dibujar las columnas de catalán/castellano, y procesar las imágenes de firma y logotipos sin dependencias externas del sistema.

## Modelos Asignados
- **Orquestador (Plan):** Gemini 3.5 Flash (actual)
- **Codificador (Implementación):** Gama estándar
- **Testeador (Validación):** Gama estándar / intermedio
- **Documentador (Documentación):** Gama ligera/barata

## Cambios de Diseño y Coordenadas A3 Landscape
* Tamaño de página: `landscape(A3)` (420mm x 297mm).
* Textos de cabecera: "Diploma de Graduación" y "Diploma de Graduació" en azul y centrados arriba.
* Dos columnas para los títulos del curso (Máster en Catalán izquierda, Máster en Castellano derecha).
* Nombre del Alumno centrado en el medio (en azul grande).
* Textos descriptivos en dos columnas (Catalán izquierda, Castellano derecha).
* Fechas y firmas en dos columnas en la parte inferior, con firmas digitalizadas de Raimon Gaja y Fermín Carrillo.

## Descomposición de Tareas
1. **Fase de Plan:**
   - Actualizar el plan de misión (`plan.md`).
   - Crear el plan de implementación (`implementation_plan.md`) con la nueva arquitectura ReportLab y esperar aprobación.
2. **Fase de Implementación:**
   - Copiar las firmas (`firma_raimon.png`, `firmaferminv2.jpg`) al directorio `static/src/img/` del módulo.
   - Crear `reports/diploma_pdf_report.py` con el motor ReportLab para el dibujo en A3 landscape.
   - Modificar el wizard `wizard/diploma_graduacion_wizard.py` para invocar al generador ReportLab y quitar la lógica de python-docx/LibreOffice.
   - Ajustar el manifest para incluir el nuevo archivo de reporte.
3. **Fase de Validación:**
   - Ejecutar pruebas automatizadas en `docker-compose.local.yml`.
   - Generar `verification.json`.
4. **Fase de Documentación:**
   - Actualizar el Changelog y walkthrough de cara al usuario.
