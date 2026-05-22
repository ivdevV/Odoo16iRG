# irg_sale_manual_confirmation_wizard

**Categoría:** Sales (Ventas)
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** Instituto Raimon Gaja
**Depende de:** `sale`, `isep_openeducat_sale`, `irg_openeducat_sale_lote_custom`, `irg_elearning_correo_bienvenida_selector`, `isep_sale_order_admissions`, `isep_admission_from_student_field`

---

## ¿Qué hace este módulo?

Este módulo gestiona la confirmación manual y e-commerce de presupuestos/pedidos de venta de forma controlada y segura, asegurando la consistencia de las fechas de admisión, y proporcionando salvaguardas para la creación de usuarios de portal y ruteo de correos de bienvenida según modalidad.

---

## Funcionalidades principales

### 1. Wizard de Pre-Confirmación Manual
* Proporciona el botón "Confirmar (validar fechas)" en los presupuestos de venta (`sale.order`), permitiendo al gestor revisar y corregir la fecha de inicio (`admission_date`) antes de la confirmación definitiva.
* Muestra avisos si la fecha seleccionada no pertenece al mes actual o si es una modalidad presencial/híbrida (HC/PRS) y el día es superior al día 7.

### 2. Ruteo de Correo de Bienvenida Post-Confirmación
* Ejecuta la lógica personalizada de ruteo de plantillas de correo de bienvenida de admisión:
  - Si el código de lote contiene `"ONL"` -> plantilla de bienvenida Online.
  - En otros casos -> plantilla por defecto.
* Las plantillas son configurables globalmente en el singleton de configuración `auto.admission.required`.

### 3. Salvaguarda de Creación y Vinculación de Usuario Portal (`_ensure_portal_user`)
* **Problema:** En el flujo de automatrícula o confirmación, si el alumno ya existe o fue pre-creado antes de la validación de la admisión (a través del campo `student_id` asignado a la admisión), el método de enrolado estándar de OpenEduCat omite el bloque de creación del usuario portal (`res.users`), dejando al alumno sin credenciales de acceso.
* **Solución/Salvaguarda:** Antes de procesar el registro del alumno (`enroll_student`), el módulo ejecuta de forma automática el método `_ensure_portal_user()`, garantizando que cada estudiante procesado disponga de un usuario portal activo y debidamente vinculado:
  1. **Si el estudiante ya tiene usuario:** Asegura que disponga del grupo de portal `base.group_portal` (siempre que no sea un usuario interno).
  2. **Si el partner tiene usuario pero el estudiante no está vinculado:** Vincula el campo `user_id` del estudiante con el usuario del partner.
  3. **Si no hay usuario pero existe la cuenta de correo (login) asignada a otro partner:** Vincula al estudiante con el usuario existente y actualiza los registros de estudiante y admisión para apuntar a dicho partner, evitando colisiones de login y duplicidad de contactos.
  4. **Si no existe usuario en el sistema:** Crea un nuevo usuario portal (`base.group_portal` e `is_student=True`) asociado al partner.
  5. **Sincronización de datos:** Actualiza la ficha del partner con los datos básicos de contacto (email, teléfono, móvil) de la admisión si estuviesen vacíos.

---

## Modelos Modificados

| Modelo | Tipo | Campos / Métodos principales | Descripción |
| :--- | :--- | :--- | :--- |
| `op.admission` | Herencia | `enroll_student()`, `_ensure_portal_user()`, `send_mail()`, `submit_form()`, `get_student_vals()` | Incorpora la salvaguarda de creación de usuarios portal antes de procesar el enrolado, gestiona el routing del correo de bienvenida y asegura la persistencia de las fechas de nacimiento y admisión. |

---

## Pruebas y Test Suite

El módulo dispone de una suite de pruebas unitarias automatizadas que se encuentra en la siguiente ruta:
* [test_portal_user.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/tests/test_portal_user.py)

La suite de pruebas valida la salvaguarda cubriendo 3 casos principales:

1. **`test_enroll_student_creates_portal_user_if_missing`:**
   - **Objetivo:** Comprobar que si se ejecuta el proceso de enrolado con un alumno pre-creado que carece de usuario (`user_id = False`), se le crea automáticamente un usuario de portal con el login correspondiente y se vincula correctamente.

2. **`test_enroll_student_links_existing_portal_user`:**
   - **Objetivo:** Comprobar que si el partner del alumno ya posee un usuario registrado en el sistema pero el alumno no estaba formalmente vinculado a él, el proceso de enrolado vincula al alumno con dicho usuario preexistente sin intentar duplicarlo.

3. **`test_enroll_student_handles_duplicate_login`:**
   - **Objetivo:** Validar el comportamiento ante colisiones de login. Si ya existe un usuario registrado con el email del aplicante vinculado a otro partner, el módulo reasigna el partner de la admisión y del estudiante al del usuario existente para mantener consistencia y evitar fallos por restricción única de login en Odoo.

---

## Instalación / Actualización

Ejecute los siguientes comandos en su contenedor de Odoo local para instalar o actualizar el módulo:

```bash
# Instalar el módulo
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -i irg_sale_manual_confirmation_wizard \
    --stop-after-init

# Actualizar el módulo
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -u irg_sale_manual_confirmation_wizard \
    --stop-after-init
```
