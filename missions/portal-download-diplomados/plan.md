# Misión: portal-download-diplomados (Revisado - Visibilidad Contextual)

## Alcance y Descomposición
El objetivo es permitir que los alumnos soliciten gratis la expedición de sus diplomados (`irg.diplomado.request`) desde el campus si su calificación final es > 7.0, y descargarlos una vez emitidos.
Además, si el campus se abre en el contexto de un curso de tipo diplomado (`course_id` en URL), se ocultarán las demás pestañas y el botón de "+ Nueva Solicitud".

1. **Nuevo Modelo de Solicitudes**:
   - `irg.diplomado.request` para registrar las peticiones del campus.
   - Asociación automática en `irg.diplomado.registry` cuando se expide el diploma.

2. **Aislamiento y Visibilidad Contextual**:
   - Añadir pestaña "Mis Diplomados".
   - Si se detecta `course_id` de tipo diplomado en el request, fijar `only_diplomados = True`.
   - Ocultar las otras pestañas y paneles, y activar "Mis Diplomados" por defecto.
   - Ocultar el botón superior de solicitudes tradicionales.

3. **Complejidad y Routing**:
   - **Clasificación**: `standard` (afecta a un nuevo módulo extendiendo dos módulos existentes sin comprometer la seguridad general).
   - **Modelo sugerido**: Modelo intermedio / fuerte de código.

4. **Tareas de Implementación**:
   - Definir modelos y archivos de datos.
   - Modificar controlador `controllers/portal.py` y plantilla `views/portal_templates.xml`.
   - Modificar tests unitarios en `tests/test_portal.py`.

5. **Validación**:
   - Ejecutar suite de pruebas de `irg_campus_diplomados_portal`.
