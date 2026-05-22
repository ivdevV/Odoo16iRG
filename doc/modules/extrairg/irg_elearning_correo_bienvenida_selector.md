# irg_elearning_correo_bienvenida_selector

**Categoría:** OpenEduCat
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `isep_elearning_custom`, `isep_student_migration`, `isep_sale_order_admissions`

---

## ¿Qué hace este módulo?

Este módulo se encarga de seleccionar automáticamente la plantilla de correo de bienvenida correspondiente para las admisiones de alumnos según la modalidad asignada al lote (grupo). Específicamente, gestiona el envío de correos utilizando plantillas personalizadas para la modalidad Online.

### Salvaguarda para Fecha de Inicio de Clases (`date_start_class`)

Se ha incorporado una salvaguarda crítica antes del envío del correo de bienvenida para admisiones asociadas a lotes de modalidad Online:
* **Problema:** Si el campo `date_start_class` (Fecha de inicio de clases) en el lote (`op.batch`) está vacío, las plantillas de correo se envían con marcadores de posición vacíos o incompletos (por ejemplo, mostrando "Fecha" en blanco en el cuerpo del correo).
* **Solución/Salvaguarda:** El módulo intercepta el proceso de envío de correos de bienvenida de admisiones Online y verifica si `date_start_class` está vacío. De ser así, lo autopuebla de manera automática con el valor del campo `start_date` (Fecha de inicio del lote) del mismo registro de lote.

### Criterio de Emparejamiento de Modalidad Online

El módulo utiliza un flujo ordenado para determinar si un lote corresponde a la modalidad Online:
1. **Verificación Directa por Nombre de Modalidad:** Evalúa si la modalidad asociada al lote (`batch_id.modality_id.name`) contiene la cadena `"online"` (búsqueda insensible a mayúsculas y minúsculas).
2. **Mecanismo de Respaldo (Fallback):** En caso de no detectarse por el campo anterior, se evalúa si la subcadena `"ONL"` está presente en el código (`batch_id.code`) o en el nombre (`batch_id.name`) del lote (búsqueda insensible a mayúsculas y minúsculas).

---

## Funcionalidades principales

* **Validaciones previas al envío:** Garantiza que el aplicante disponga de un tutor asignado (`tutor_id`), un grupo/lote asignado (`batch_id`) y que el lote posea la fecha de inicio (`start_date`) configurada.
* **Salvaguarda de integridad de datos:** Rellena `date_start_class` en `op.batch` utilizando `start_date` antes del envío del correo si está vacío.
* **Selección y envío de plantilla:** Utiliza la plantilla específica para modalidad Online (`irg_elearning_correo_bienvenida_selector.email_op_admission_confirm_online`).
* **Gestión de contraseñas de bienvenida:** Aplica un contexto seguro que controla si se debe incluir o no el bloque de contraseña (`welcome_show_password`), evitando volver a enviar contraseñas en texto claro si el correo ya fue enviado con anterioridad.

---

## Modelos

| Modelo | Tipo | Campos / Métodos principales | Descripción |
| :--- | :--- | :--- | :--- |
| `op.admission` | Herencia | `send_mail()`, `_welcome_password_context()`, `_fix_welcome_password_placeholder()` | Intercepta el flujo de envío del correo de bienvenida para aplicar las validaciones, la salvaguarda de fecha, la selección de plantilla Online y la lógica de seguridad para contraseñas de bienvenida. |

---

## Pruebas y Test Suite

El módulo cuenta con una suite de pruebas automatizadas que se encuentra en la siguiente ruta:
* [test_welcome_mail.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/addons_uisep/irg_elearning_correo_bienvenida_selector/tests/test_welcome_mail.py)

La suite de pruebas valida la salvaguarda a través de 2 casos de prueba unitarios:

1. **`test_send_mail_online_modality_auto_populates_date_start_class` (Caso de Prueba 1):**
   * **Objetivo:** Validar que para un lote configurado con una modalidad que contenga "Online Modality" (pero sin el código "ONL"), si el campo `date_start_class` está vacío, el proceso de envío del correo de bienvenida lo autopueble automáticamente con el valor del campo `start_date`.
   * **Verificación:** Se comprueba que `date_start_class` pase de estar vacío a coincidir con `start_date` y que el correo de admisión sea marcado como enviado con éxito (`email_send_ok = True`).

2. **`test_send_mail_online_code_auto_populates_date_start_class` (Caso de Prueba 2):**
   * **Objetivo:** Validar la lógica de respaldo (fallback) cuando el lote contiene `"ONL"` en su código pero no tiene la modalidad explícita establecida, y el campo `date_start_class` ha sido limpiado manualmente en base de datos.
   * **Verificación:** Confirma que la salvaguarda actúa correctamente autopoblando `date_start_class` con `start_date` en el lote y permitiendo que el correo se envíe de manera satisfactoria.

---

## Instalación / Actualización

Ejecute los siguientes comandos en su contenedor de Odoo local para instalar o actualizar el módulo:

```bash
# Instalar el módulo
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -i irg_elearning_correo_bienvenida_selector \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar el módulo
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -u irg_elearning_correo_bienvenida_selector \
    --stop-after-init --db_host=pgodoo_latest
```
