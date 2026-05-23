# Changelog: 2026-05-22 — Corrección de Error 403 (AccessError) en Portal para `irg_course_convocatorias_v2`

## Resumen de Cambios

Se ha implementado una corrección de seguridad para resolver el error de acceso `403 Forbidden` (`AccessError`) que afectaba a los estudiantes y usuarios del portal cuando intentaban cargar los canales de eLearning. 

El error se originaba debido a que la interfaz del portal evaluaba reglas de visibilidad y pertenencia ejecutando consultas directas sobre modelos de OpenEduCat (`op.course`, `op.batch`, `op.admission`). Dado que los usuarios con rol Portal no disponen de reglas de acceso de lectura (ACLs) para dichos modelos internos, Odoo bloqueaba la solicitud arrojando una excepción de seguridad.

La resolución implementa una elevación de privilegios controlada mediante `.sudo()` para verificar exclusivamente las condiciones de inscripción y modalidad del estudiante, sin exponer información sensible.

---

## Detalle de Cambios

### Módulo `irg_course_convocatorias_v2`

#### 1. Lógica de Negocio (`models/slide_channel.py`)
* **`_irg_get_related_courses()`**:
  - Modificado para inicializar y buscar registros del modelo `op.course` con elevación de privilegios (`self = self.sudo()` y `self.env['op.course'].sudo()`).
* **`_irg_is_partner_online_student_for_channel()`**:
  - Modificado para realizar consultas de coincidencia y lectura sobre admisiones (`op.admission`) y lotes (`op.batch`) bajo contexto `sudo()`.
* **`_irg_is_online_student_for_channel()`**:
  - Modificado para llamar al método de verificación de partner usando la instancia del canal con privilegios elevados (`self.sudo()`).

#### 2. Pruebas de Regresión (`tests/test_bootstrap_online_v2.py`)
* Se añadió el test unitario **`test_portal_user_access_check`**:
  - Simula la ejecución de consultas y llamadas a métodos bajo un usuario real perteneciente al grupo Portal (`base.group_portal`).
  - Valida que la llamada a `_irg_is_online_student_for_channel()` se ejecute de forma íntegra y retorne el valor correcto, sin arrojar ningún error de tipo `AccessError` (403).

---

## Validación y Pruebas

Los cambios han sido verificados satisfactoriamente en el entorno de desarrollo local mediante la suite de tests automatizada de Odoo:

* **Entorno:** Contenedor Docker de desarrollo local (`odoo16irg_local`) contra la base de datos `test_irg_db`.
* **Comando ejecutado:**
  ```bash
  python3 odoo-bin -c /etc/odoo/odoo.conf -d test_irg_db -i irg_course_convocatorias_v2 --test-enable
  ```
* **Resultado del test suite:**
  - **Pruebas ejecutadas:** 10
  - **Pruebas fallidas:** 0
  - **Errores:** 0
  - **Estado:** EXITOSO (`SUCCESS`)
