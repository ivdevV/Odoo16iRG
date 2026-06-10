# irg_student_reset_password

**Categoría:** extrairg  
**Versión:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Sí  
**Autor:** iRG  
**Dependencias:** `openeducat_core`, `isep_update_pass_user_ext`

---

## Propósito / ¿Qué hace este módulo?

Este módulo añade una pestaña llamada **"Restablecer contraseña"** en la vista de formulario del estudiante (`op.student`). Su principal objetivo es permitir que los usuarios con roles de Back Office (por ejemplo, el personal de 'Académica') puedan restablecer la contraseña de un estudiante y visualizar la nueva contraseña generada mediante un asistente emergente (wizard). 

Esto evita que el personal de Back Office dependa del departamento de TI o de administradores del sistema con permisos completos de Odoo para realizar cambios rutinarios de contraseñas de alumnos.

---

## Funcionalidades principales

- **Pestaña en Ficha de Estudiante:** Añade la pestaña "Restablecer contraseña" al formulario de estudiantes (`op.student`), visible exclusivamente para los miembros del grupo Back Office (`openeducat_core.group_op_back_office`).
- **Validaciones y Mensajes Dinámicos en la Interfaz:**
  - Si el estudiante **tiene un usuario vinculado**, se muestra una alerta de advertencia destacando las consecuencias del cambio (que se generará una contraseña nueva y el acceso actual dejará de funcionar) junto con el botón para realizar la acción.
  - Si el estudiante **no tiene un usuario vinculado**, se muestra un aviso indicando que la opción de restablecer contraseña no está habilitada.
- **Acceso Elevado Seguro (Sudo):** La lógica del módulo eleva privilegios de forma controlada (`sudo()`) para llamar al método de generación de contraseña de `res.users`, eludiendo las restricciones nativas de escritura de contraseñas de Odoo que suele tener el personal administrativo.
- **Visualización de Credenciales:** Abre un wizard emergente (`isep.generate.password.wizard`) para mostrarle al administrador la contraseña generada, facilitando su copia y comunicación directa al estudiante.

---

## Modelos y Métodos

El módulo hereda el modelo de estudiante de OpenEduCat para inyectarle la lógica del negocio:

| Modelo | Tipo de herencia | Métodos / Campos principales |
| :--- | :--- | :--- |
| `op.student` | `_inherit = 'op.student'` | **Métodos:**<br>• `action_generate_password()`: Verifica que el estudiante tenga un `user_id` vinculado. Si existe, ejecuta `self.user_id.sudo().action_generate_password()` para delegar la generación segura al módulo `isep_update_pass_user_ext`. Si no existe, lanza un error de usuario (`UserError`). |

---

## Vistas y UI

El módulo hereda la vista nativa de formulario de estudiantes de OpenEduCat:

- **Vista heredada:** `openeducat_core.view_op_student_form` (ID de registro: `view_op_student_form_inherit_reset_password`).
- **Cambios realizados:** Se inserta un `<page name="reset_password">` al final del elemento `<notebook>`.
- **Estructura de la pestaña:**
  - Alerta de advertencia (`alert-warning`) y botón de confirmación condicionados a `attrs="{'invisible': [('user_id', '=', False)]}"`.
  - Alerta informativa (`alert-info`) condicionada a `attrs="{'invisible': [('user_id', '!=', False)]}"`.
  - Botón "Generar y actualizar contraseña" (`action_generate_password`) que despliega una confirmación nativa de javascript antes de realizar el cambio irreversible.

---

## Seguridad

El módulo define la configuración de acceso necesaria para la manipulación del wizard desde el Back Office:

- **Acceso de Modelo (`security/ir.model.access.csv`):**
  - Concede permisos completos (Lectura, Escritura, Creación, Eliminación) sobre el modelo `isep_update_pass_user_ext.model_isep_generate_password_wizard` al grupo `openeducat_core.group_op_back_office`.
  - ID de la regla: `access_isep_generate_password_wizard_back_office`.

---

## Tests

El módulo incluye un conjunto de pruebas unitarias para garantizar el correcto funcionamiento de las validaciones y procesos.

- **Ubicación:** `tests/test_reset_password.py`
- **Casos de prueba:**
  1. `test_01_action_generate_password_success`: Verifica que se genera correctamente una contraseña para un estudiante con usuario Odoo asignado, validando la creación y datos del wizard de retorno.
  2. `test_02_action_generate_password_no_user_fails`: Verifica que se lanza correctamente una excepción de tipo `UserError` si se intenta regenerar la contraseña para un estudiante sin un usuario vinculado.
- **Ejecución de las pruebas:**
  ```bash
  odoo -c /etc/odoo/odoo.conf -d <dbname> --test-enable --test-tags=post_install,-at_install -i irg_student_reset_password --stop-after-init
  ```

---

## Instrucciones de Instalación / Actualización

### Instalación
Para instalar el módulo por primera vez, ejecute el siguiente comando:
```bash
odoo -c /etc/odoo/odoo.conf -d <dbname> -i irg_student_reset_password --stop-after-init
```

### Actualización
Para aplicar actualizaciones en el módulo, ejecute el siguiente comando:
```bash
odoo -c /etc/odoo/odoo.conf -d <dbname> -u irg_student_reset_password --stop-after-init
```

---

## Rollback

Dado que este módulo no crea nuevos modelos de datos persistentes (las tablas de la base de datos no sufren alteraciones ni se agregan nuevos campos de base de datos en `op.student`), el proceso de rollback es seguro y directo:

1. Desinstalar el módulo `irg_student_reset_password` desde la lista de aplicaciones de la interfaz de Odoo (o con el comando de desinstalación pertinente).
2. Opcionalmente, retirar el módulo del repositorio de código si se desea eliminar toda traza.
3. Actualizar la lista de aplicaciones y el sistema. El comportamiento volverá a su estado nativo sin pérdida ni alteración de datos de los estudiantes o usuarios.

---

## Limitaciones conocidas

- **Usuario Vinculado Requerido:** El estudiante debe tener obligatoriamente una cuenta de usuario de Odoo vinculada a su ficha (`user_id`). Si no existe dicha vinculación, la pestaña mostrará un mensaje informando que no es posible realizar el restablecimiento.

---

## Changelog

- **2026-06-10** - Documentación inicial y creación del módulo `irg_student_reset_password`.
