# Misión: portal-download-diplomados (Revisado - Aislamiento Completo)

## Alcance y Descomposición
El objetivo es permitir que los alumnos descarguen diplomados (`irg.diplomado.registry`) directamente (sin flujos de pago) desde el campus si su calificación final es > 7.0. Esto se hará de forma completamente aislada de los diplomas y solicitudes de máster.

1. **Aislamiento en Vistas**:
   - Crear una pestaña exclusiva llamada **"Mis Diplomados"** al mismo nivel que "Mis Diplomas" y "Actas TFM/TFG".
   - No mostrar los diplomados en la pestaña original de "Mis Diplomas".

2. **Aislamiento en Solicitudes (Sin Pago)**:
   - Sobrescribir `certificate_new` en el controlador para filtrar y **excluir** todas las libretas académicas de cursos de diplomado en el formulario de solicitud tradicional `/campus/certificates/new`. Así el alumno no podrá solicitar su pago en Stripe por error.

3. **Complejidad y Routing**:
   - **Clasificación**: `standard` (afecta a un nuevo módulo extendiendo dos módulos existentes sin comprometer la seguridad general).
   - **Modelo sugerido**: Modelo intermedio / fuerte de código.

4. **Tareas de Implementación**:
   - Modificar controlador `controllers/portal.py`.
   - Modificar la plantilla `views/portal_templates.xml`.
   - Modificar tests unitarios en `tests/test_portal.py`.

5. **Validación**:
   - Ejecutar suite de pruebas de `irg_campus_diplomados_portal`.
