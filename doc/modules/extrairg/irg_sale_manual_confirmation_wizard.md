# irg_sale_manual_confirmation_wizard

**Categoría:** Sales (Ventas)
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** Instituto Raimon Gaja
**Depende de:** `sale`, `isep_openeducat_sale`, `irg_openeducat_sale_lote_custom`, `irg_elearning_correo_bienvenida_selector`, `isep_sale_order_admissions`, `isep_admission_from_student_field`, `irg_admission_class_start_date`

---

## ¿Qué hace este módulo?

Este módulo gestiona la confirmación manual y e-commerce de presupuestos/pedidos de venta de forma controlada y segura, asegurando la consistencia de las fechas de admisión, y proporcionando salvaguardas para la creación de usuarios de portal, soporte y ruteo de correos de bienvenida según modalidad.

---

## Funcionalidades principales

### 1. Wizard de Pre-Confirmación Manual
* Proporciona el botón "Confirmar (validar fechas)" en los presupuestos de venta (`sale.order`), permitiendo al gestor revisar y corregir la fecha de inicio (`admission_date`) antes de la confirmación definitiva.
* Muestra avisos si la fecha seleccionada no pertenece al mes actual o si es una modalidad presencial/híbrida (HC/PRS) y el día es superior al día 7.

### 2. Ruteo de Correo de Bienvenida Post-Confirmación
* Ejecuta la lógica personalizada de ruteo de plantillas de correo de bienvenida de admisión:
  - Si el código de lote contiene `"ONL"` (y no corresponde a un diplomado) -> plantilla de bienvenida Online.
  - En otros casos -> plantilla por defecto (HomeClass).
* Las plantillas son configurables globalmente en el singleton de configuración `auto.admission.required`.

### 3. Salvaguarda de Creación y Vinculación de Usuario Portal (`_ensure_portal_user`)
* **Problema:** En el flujo de automatrícula o confirmación, si el alumno ya existe o fue pre-creado antes de la validación de la admisión (a través del campo `student_id` asignado a la admisión), el método de enrolado estándar de OpenEduCat omite el bloque de creación del usuario portal (`res.users`), dejando al alumno sin credenciales de acceso.
* **Solución/Salvaguarda:** Antes de procesar el registro del alumno (`enroll_student`), el módulo ejecuta de forma automática el método `_ensure_portal_user()`, garantizando que cada estudiante procesado disponga de un usuario portal activo y debidamente vinculado:
  1. **Si el estudiante ya tiene usuario:** Asegura que disponga del grupo de portal `base.group_portal` (siempre que no sea un usuario interno).
  2. **Si el partner tiene usuario pero el estudiante no está vinculado:** Vincula el campo `user_id` del estudiante con el usuario del partner.
  3. **Si no hay usuario pero existe la cuenta de correo (login) asignada a otro partner:** Vincula al estudiante con el usuario existente y actualiza los registros de estudiante y admisión para apuntar a dicho partner, evitando colisiones de login y duplicidad de contactos.
  4. **Si no existe usuario en el sistema:** Crea un nuevo usuario portal (`base.group_portal` e `is_student=True`) asociado al partner.
  5. **Sincronización de datos:** Actualiza la ficha del partner con los datos básicos de contacto (email, teléfono, móvil) de la admisión si estuviesen vacíos.

### 4. Soporte y Ruteo de Diplomados
El módulo incorpora un sistema de detección y procesamiento robusto de **Diplomados** (identificados mediante una estrategia multi-factor):
*   **Criterio de Identificación:** Se clasifica una línea como Diplomado si se cumple cualquiera de las siguientes condiciones:
    - La categoría del producto tiene un código que comienza por `'DI'` (insensible a mayúsculas/minúsculas).
    - La categoría del producto tiene un nombre que contiene la palabra `'DIPLOMADO'` (por ejemplo, "Diplomados Universitarios").
    - El nombre del producto contiene la palabra `'DIPLOMADO'`.
*   **Mapeo de Curso Fallback:** Si un producto no está vinculado formalmente a un curso (`op.course`) en la base de datos, el wizard intenta recuperarlo a través del campo `course_id` del presupuesto/pedido de venta (`sale.order`) como fallback, evitando que la previsualización se rompa.
*   **Detección de Modalidad:** Son clasificados de forma forzada bajo la modalidad HomeClass (`'HC'`), independientemente de otros atributos.
*   **Formato de Lote Mensual:** Generan lotes mensuales con una estructura de código específica, por ejemplo: `'DIAHC2606'` (para un Diplomado con código de curso `'IA'` que inicia en Junio de 2026). Si la categoría no tiene un código definido pero coincide con la regla de nombre de Diplomados, se autogenera la inicial del lote como `'D'`.
*   **Forzado de Plantilla de Correo:** Al ser detectados como modalidad `'HC'`, siempre utilizan la plantilla de correo de bienvenida por defecto (HomeClass), previniendo que se aplique la plantilla online de admisión por error.

### 5. Autocompletado de Fecha de Inicio de Clases
*   Al confirmar un pedido de venta (ya sea mediante confirmación manual a través del wizard o por e-commerce), el módulo sincroniza la fecha de inicio de la línea de producto (`start_date_enroller` en `sale.order.line`) con la fecha de inicio de clases (`irg_class_start_date`) de la admisión (`op.admission`) generada.

---

## Modelos Modificados

| Modelo | Tipo | Campos / Métodos principales | Descripción |
| :--- | :--- | :--- | :--- |
| `op.admission` | Herencia | `enroll_student()`, `_ensure_portal_user()`, `send_mail()`, `submit_form()`, `get_student_vals()` | Incorpora la salvaguarda de creación de usuarios portal, gestiona el ruteo del correo de bienvenida (forzando plantillas default para diplomados) y asegura la persistencia de fechas de nacimiento y admisión. |
| `sale.order` | Herencia | `_get_line_modality()`, `_create_or_get_admission()` | Permite identificar la modalidad de una línea y añade compatibilidad con diplomados (forzando 'HC' para categorías con código que empieza por 'DI'). Además, propaga el precio de la línea a `fees`, la fecha de admisión y sincroniza la fecha de inicio de la línea (`start_date_enroller`) con la fecha de inicio de clases (`irg_class_start_date`) en la admisión. |
| `irg.manual.confirmation.wizard` | Nuevo Modelo (Wizard) | `default_get()`, `_compute_preview()`, `_build_preview()`, `_detect_line_modalidad()`, `_build_line_batch_code_preview()`, `action_confirm()` | Interfaz gráfica y lógica de validación de pre-confirmación que calcula la modalidad detectada y el lote correspondiente (soportando mensual trimestral y diplomados). |

---

## Pruebas y Test Suite

El módulo dispone de dos suites de pruebas unitarias/de integración automatizadas:

1.  **Salvaguardas de Portal Users (`test_portal_user.py`):**
    *   [test_portal_user.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/tests/test_portal_user.py)
    *   **`test_enroll_student_creates_portal_user_if_missing`:** Comprueba la creación de un nuevo usuario de portal para alumnos sin credenciales.
    *   **`test_enroll_student_links_existing_portal_user`:** Comprueba la vinculación sin duplicidad con usuarios de portal preexistentes en el partner.
    *   **`test_enroll_student_handles_duplicate_login`:** Comprueba la resolución de conflictos en colisiones de email/login vinculando al partner adecuado.

2.  **Soporte de Diplomados (`test_diplomados_wizard.py`):**
    *   [test_diplomados_wizard.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/scratch/test_diplomados_wizard.py)
    *   **Caso de Validación de Asistente:** Crea una categoría temporal con código `'DI'` y un producto/curso con código `'IA'` que inicia en Junio de 2026. Valida que el asistente de confirmación manual detecta correctamente la modalidad como `'HC'` y genera la vista previa de lote `'DIAHC2606'` de forma exitosa.

3.  **Sincronización de Fecha de Inicio de Clases (`test_class_start_date.py`):**
    *   [test_class_start_date.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/scratch/test_class_start_date.py)
    *   **Caso de Validación de Sincronización:** Crea un presupuesto de venta con una línea académica que tiene asignada una fecha en `start_date_enroller`. Al confirmar la orden, valida que la admisión generada o recuperada contenga dicho valor exacto en el campo `irg_class_start_date` en la base de datos local.

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
