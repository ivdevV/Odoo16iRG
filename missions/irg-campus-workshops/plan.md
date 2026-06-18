# Plan - Misión irg-campus-workshops (Actualizado)

Implementación de un módulo personalizado de Odoo 16 para crear una sección de "Talleres" en el portal de `/campus`, añadir la tarjeta "iRG Empower" con redirección y auto-inscripción automática, y restringir la visibilidad de la sección para estudiantes matriculados únicamente en diplomados.

## 1. Alcance y Descomposición
- **Módulo Odoo 16 personalizado**: `irg_campus_workshops` en `addons-extra/extrairg/`.
- **Estructura básica**:
  - `__init__.py`
  - `__manifest__.py` (añadida dependencia a `irg_course_portal_tiles_diplomado_hide`).
  - `views/user_profile_content_workshops.xml`
- **Controlador Python**: `controllers/main.py` y `controllers/__init__.py`.
- **Restricción de Visibilidad (QWeb)**:
  - Obtener las admisiones finalizadas (`state='done'`) del estudiante.
  - Utilizar el método helper `.is_diplomado()` (de `irg_course_portal_tiles_diplomado_hide`) para evaluar si todas las admisiones del alumno pertenecen a cursos de tipo diplomado.
  - Envolver la sección de "Talleres" en un bloque condicional `<t t-if="not only_diplomado">`.
- **Activos Estáticos**: Imagen del logo en `static/src/img/irg_empower_logo.jpg`.
- **Pruebas**:
  - Test en `tests/test_workshops.py` para verificar:
    1. Carga correcta de la vista.
    2. Auto-inscripción en el controlador.
    3. Ocultamiento de la sección en QWeb cuando el alumno está matriculado únicamente en cursos diplomados.

## 2. Clasificación de Complejidad
- **Tier**: `standard`
- **Justificación**: Añade lógica condicional QWeb dependiente de un método heredado de otro módulo personalizado del proyecto.
- **Modelos Asignados**:
  - Todos los roles asignados al modelo Gemini 3.5 Flash (actual).

## 3. Propuesta de Cambios

### [Componente: irg_campus_workshops]

#### [MODIFY] [__manifest__.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_workshops/__manifest__.py)
Añadir dependencia `'irg_course_portal_tiles_diplomado_hide'`.

#### [MODIFY] [user_profile_content_workshops.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_workshops/views/user_profile_content_workshops.xml)
Implementar la evaluación de admisiones y la condicional de visibilidad `not only_diplomado`.

#### [MODIFY] [test_workshops.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_workshops/tests/test_workshops.py)
Añadir caso de prueba que valide la visibilidad condicional basada en admisiones diplomados vs. másteres.

## 4. Plan de Verificación

### Pruebas Automatizadas
- Ejecutar tests locales de Odoo:
  `docker compose -f docker-compose.local.yml run --rm odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_campus_workshops --test-enable --stop-after-init`

### Verificación Manual
- Crear un alumno inscrito únicamente en diplomados y comprobar que no visualiza la sección "Talleres".
- Crear un alumno inscrito en un máster y comprobar que sí la visualiza.
