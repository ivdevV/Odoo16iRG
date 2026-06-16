# Misión: portal-download-diplomados (Revisado)

## Alcance y Descomposición
El objetivo es permitir que los alumnos descarguen diplomados (`irg.diplomado.registry`) desde el campus si su calificación final es > 7.0, a través de la creación de un nuevo módulo exclusivo (`irg_campus_diplomados_portal`) para evitar conflictos con el flujo de másteres/grados.

1. **Creación del Módulo**:
   - Estructura básica de `irg_campus_diplomados_portal`.
   - Manifest especificando dependencias de `irg_campus_certificates_portal`, `irg_generacion_diplomados` e `isep_gradebook`.

2. **Complejidad y Routing**:
   - **Clasificación**: `standard` (afecta a un nuevo módulo extendiendo dos módulos existentes sin comprometer la seguridad general).
   - **Modelo sugerido**: Modelo intermedio / fuerte de código.

3. **Tareas de Implementación**:
   - Escribir `__manifest__.py`, `__init__.py`, y la inicialización de controladores y vistas.
   - Implementar controlador heredado `IrgCampusDiplomadosPortal` en `controllers/portal.py`.
   - Modificar la plantilla `portal_templates.xml` inyectando la sección de posgrados y diplomados mediante XPath.
   - Crear un archivo de tests automatizados `tests/test_portal.py` y registrarlo en `tests/__init__.py`.

4. **Validación**:
   - Instalar el módulo en base de datos.
   - Ejecutar suite de pruebas de `irg_campus_diplomados_portal`.
