# Misión: Corrección de tamaño del vídeo embebido y visibilidad de sección destacada para estudiantes

## Alcance y Objetivos
1. Solucionar el problema de que el reproductor de video embebido (iframe) se muestre muy pequeño o deformado. Aplicaremos estilos CSS responsivos con una relación de aspecto de 16:9 y un ancho máximo de 800px.
2. Solucionar el problema de que los usuarios tipo portal (estudiantes) no visualicen la sección destacada en los canales de eLearning clonados para la modalidad online (ya que los clones carecen de asignaturas directas en el campo `op_subject_ids`). Implementaremos un fallback para redirigir la búsqueda al canal HomeClass principal.

## Clasificación de Complejidad
- **Clasificación:** `standard`
- **Justificación:** Afecta a 3 archivos del módulo `irg_course_elearning_featured_section` (modelo, estilos, y pruebas unitarias). No involucra cambios en datos críticos ni modificaciones de esquema de la base de datos.

## Modelos Elegidos para cada Fase
- **Plan:** Orquestador (Gemini 3.5 Flash)
- **Implementación:** Codificador (Gemini 3.5 Flash)
- **Validación:** Testeador (Gemini 3.5 Flash)
- **Documentación:** Documentador (Gemini 3.5 Flash)

## Tareas Propuestas
1. Modificar `irg_get_featured_course` en `slide_channel.py` para usar `irg_homeclass_channel_id` como fallback si el canal actual es un clon online.
2. Modificar `featured_section.scss` para hacer que el iframe embebido escale al 100% de ancho del contenedor con un límite de 800px y mantenga una proporción 16:9 limpia.
3. Añadir pruebas en `test_featured_section.py` que verifiquen el correcto funcionamiento del fallback de canales clonados y el acceso sin errores para usuarios tipo portal.
