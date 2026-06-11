# irg_sale_manual_confirmation_wizard

**Categoría:** Sales (Ventas)
**Versión:** 16.0.1.4.0
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
* Muestra en una vista previa (`detected_registers_preview`) el nombre del registro de admisión detectado para cada curso de la orden o indica si se creará uno nuevo en función del período de inicio calculado.


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
*   **Formato de Lote Mensual:** Generan lotes mensuales con una estructura de código específica, por ejemplo: `'DIIAHC2606'` (para un Diplomado con código de curso `'IA'` que inicia en Junio de 2026). Si la categoría no tiene un código definido pero coincide con la regla de nombre de Diplomados, se autogenera la inicial del lote como `'DI'`.
*   **Forzado de Plantilla de Correo:** Al ser detectados como modalidad `'HC'`, siempre utilizan la plantilla de correo de bienvenida por defecto (HomeClass), previniendo que se aplique la plantilla online de admisión por error.

### 5. Autocompletado de Fecha de Inicio de Clases
*   Al confirmar un pedido de venta (ya sea mediante confirmación manual a través del wizard o por e-commerce), el módulo sincroniza la fecha de inicio de la línea de producto (`start_date_enroller` en `sale.order.line`) con la fecha de inicio de clases (`irg_class_start_date`) de la admisión (`op.admission`) generada.

### 6. Exclusión de Líneas de Descuento (Precios Negativos)
*   **Problema:** En presupuestos con productos de descuento (como `Descuento Máster` o `Dcto. Diplomado`), estos productos pueden marcarse como programas académicos o tener nombres que coincidan con los criterios de detección, provocando que Odoo intente tratarlos como líneas de programa académico principales, asignándoles lotes o generando admisiones independientes.
*   **Solución:** Se implementa un filtro explícito en la detección de líneas académicas (`_is_academic_line`). Si una línea tiene un precio unitario negativo (`price_unit < 0`) o un subtotal negativo (`price_subtotal < 0`), se descarta automáticamente de la lógica de confirmación y asignación de lotes, evitando errores y previniendo que los productos de descuento sean interpretados erróneamente como programas formativos reales.

### 7. Búsqueda Inteligente y Salvaguarda de Fechas en Registros
*   **Reutilización por variación de formato de período:** El método `_find_or_create_register` incorpora una búsqueda robusta que asocia períodos con y sin ceros a la izquierda (ej. `'2026-02'` frente a `'2026-2'`), garantizando que se reutilicen los registros de admisión existentes para el mismo curso y período, independientemente de variaciones sintácticas menores en el formato del período.
*   **Salvaguarda para períodos vencidos:** Si se confirma una admisión para un período cuya fecha límite de registro (`gat_date_max_register`) ya ha expirado respecto a la fecha actual (`today > end_date`), el sistema pre-crea automáticamente el registro de admisión forzando tanto la fecha de inicio (`start_date`) como la fecha de fin (`end_date`) al último día del período correspondiente (`end_date`). Esto previene fallos por restricciones de validación temporal y permite procesar admisiones históricas de forma segura.

### 8. Comportamiento de la Confirmación Nativa para España (es_ES)
*   **Anulación de automatrícula automática:** Cuando se confirma un presupuesto de venta de manera nativa (por ejemplo, desde el botón nativo de Odoo "Confirmar" o por flujo e-commerce) y el idioma del curso asociado es español de España (`es_ES`), el sistema **no realiza la matriculación automática** ni envía el correo de bienvenida.
*   **Estado Borrador:** En su lugar, el registro de admisión (`op.admission`) correspondiente se crea y permanece en estado **Borrador** (`draft`), permitiendo su posterior revisión y procesamiento manual por el equipo gestor.
*   **Proceso Exclusivo del Asistente:** La matriculación definitiva (paso a estado `done` y el envío automático de correos de bienvenida) es un **proceso exclusivo** del Asistente de Confirmación Manual (`irg.manual.confirmation.wizard`). Al procesar la confirmación a través de este wizard, se fuerza la promoción de estados y el envío del email a través del contexto (`irg_manual_wizard_passed=True`).

---

## Modelos Modificados

| Modelo | Archivo | Tipo | Campos / Métodos principales | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `op.admission` | [op_admission.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/models/op_admission.py) | Herencia | `enroll_student()`, `_ensure_portal_user()`, `send_mail()`, `submit_form()`, `get_student_vals()` | Incorpora la salvaguarda de creación de usuarios portal, gestiona el ruteo del correo de bienvenida (forzando plantillas default para diplomados) y asegura la persistencia de fechas de nacimiento y admisión. |
| `sale.order` | [sale_order.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/models/sale_order.py) | Herencia | `_is_academic_line()`, `_get_line_modality()`, `_create_or_get_admission()`, `_find_or_create_register()`, `auto_ad_active()` | Permite identificar la modalidad de una línea y añade compatibilidad con diplomados. Propaga el precio a `fees`, sincroniza `start_date_enroller` con `irg_class_start_date`. Excluye líneas con precio negativo (descuentos). Implementa la búsqueda robusta de registros por variación de formato de período y la salvaguarda de fecha de inicio/fin en períodos vencidos. Desactiva la matriculación automática para España (`es_ES`). |
| `irg.manual.confirmation.wizard` | [manual_confirmation_wizard.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/wizards/manual_confirmation_wizard.py) | Nuevo Wizard | `detected_registers_preview`, `_get_line_period()`, `_find_matching_register()`, `_is_academic_line()`, `default_get()`, `_compute_preview()`, `_build_preview()`, `_detect_line_modalidad()`, `_build_line_batch_code_preview()`, `action_confirm()` | Interfaz gráfica y lógica de validación de pre-confirmación que calcula la modalidad detectada, el lote correspondiente (soportando mensual trimestral y diplomados), y los registros de admisión pre-existentes/nuevos, ignorando líneas de descuento con precios negativos. |

---

## Pruebas y Test Suite

El módulo dispone de varias suites de pruebas unitarias/de integración automatizadas:

1.  **Salvaguardas de Portal Users (`test_portal_user.py`):**
    *   [test_portal_user.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/tests/test_portal_user.py)
    *   **`test_enroll_student_creates_portal_user_if_missing`:** Comprueba la creación de un nuevo usuario de portal para alumnos sin credenciales.
    *   **`test_enroll_student_links_existing_portal_user`:** Comprueba la vinculación sin duplicidad con usuarios de portal preexistentes en el partner.
    *   **`test_enroll_student_handles_duplicate_login`:** Comprueba la resolución de conflictos en colisiones de email/login vinculando al partner adecuado.

2.  **Soporte de Diplomados (`test_diplomados_wizard.py`):**
    *   [test_diplomados_wizard.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/scratch/test_diplomados_wizard.py)
    *   **Caso de Validación de Asistente:** Crea una categoría temporal con código `'DI'` y un producto/curso con código `'IA'` que inicia en Junio de 2026. Valida que el asistente de confirmación manual detecta correctamente la modalidad como `'HC'` y genera la vista previa de lote `'DIIAHC2606'` de forma exitosa.

3.  **Sincronización de Fecha de Inicio de Clases (`test_class_start_date.py`):**
    *   [test_class_start_date.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/scratch/test_class_start_date.py)
    *   **Caso de Validación de Sincronización:** Crea un presupuesto de venta con una línea académica que tiene asignada una fecha en `start_date_enroller`. Al confirmar la orden, valida que la admisión generada o recuperada contenga dicho valor exacto en el campo `irg_class_start_date` en la base de datos local.

4.  **Búsqueda de Registros y Salvaguarda de Fechas (`test_register_date_validation.py`):**
    *   [test_register_date_validation.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_sale_manual_confirmation_wizard/tests/test_register_date_validation.py)
    *   **`test_search_matches_alternative_period_format`:** Verifica que la consulta encuentre registros que coincidan con formatos alternativos de período (por ejemplo, buscar `'2026-02'` encuentra el registro guardado como `'2026-2'` y viceversa).
    *   **`test_date_safeguard_for_past_periods`:** Valida que al crear un registro de admisión para un período cuya fecha límite ya ha expirado, no se produzca ningún error y se asigne de forma segura la fecha de finalización (`end_date`) tanto a `start_date` como a `end_date` del registro.
    *   **`test_wizard_shows_detected_register_name`:** Valida que el campo calculado en el wizard `detected_registers_preview` liste correctamente los nombres de los registros de admisión emparejados para las líneas del pedido, o bien indique si se creará uno nuevo.
    *   **`test_es_ES_academic_confirmation_routing`:** Verifica que al confirmar un presupuesto con un curso en idioma `es_ES`: (A) de forma nativa (sin el contexto del asistente manual), se crea la admisión pero permanece en estado borrador (`draft` o `application`) y no se envía el email de bienvenida; (B) mediante el asistente de confirmación manual, se fuerza la promoción de estados a `done` (matriculado) y el envío del correo electrónico.

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

---

## Changelog

*   **16.0.1.4.0**: Anulación del proceso de automatrícula automática desde el botón de confirmar nativo para España (es_ES), manteniendo la creación de la admisión en estado borrador (draft) y haciendo que la matriculación y envío de correos sea un proceso exclusivo del asistente de confirmación manual.
*   **16.0.1.3.0**: Adición del campo computado `detected_registers_preview` al wizard de confirmación manual, que lista de forma amigable los registros de admisión que se asignarán o pre-crearán al confirmar la orden de venta. Implementación de helpers para resolución robusta de períodos de inicio y emparejado de registros, y agregado del caso de prueba correspondiente.
*   **16.0.1.2.0**: Implementación de lógica inteligente de búsqueda y reutilización de registros de admisión con variantes de formato en el período (ej. ceros a la izquierda), así como una salvaguarda de seguridad para pre-crear registros de admisión en períodos vencidos forzando las fechas al límite del período para evitar fallas por restricciones de validación temporal. Adición de la suite de pruebas unitarias correspondiente.
*   **16.0.1.1.0**: Exclusión de líneas con precios negativos (`price_unit < 0` o `price_subtotal < 0`) en la detección de líneas académicas para ignorar los productos de tipo descuento (por ejemplo, `Descuento Máster` o `Dcto. Diplomado`) y evitar que sean tratados como programas académicos independientes.
*   **16.0.1.0.0**: Versión inicial con el wizard de pre-confirmación manual, routing de correos de bienvenida post-confirmación y salvaguardas de creación de usuario portal.
