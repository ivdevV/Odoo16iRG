# Referencia Técnica: irg_certificate_partial

Este documento provee la especificación técnica completa y de referencia para el módulo `irg_certificate_partial`.

---

## Ficha Técnica

| Propiedad | Valor |
| --- | --- |
| **Nombre Técnico** | `irg_certificate_partial` |
| **Categoría** | Academic / Website |
| **Versión** | `16.0.1.0.0` |
| **Licencia** | LGPL-3 |
| **Instalable** | Sí |
| **Aplicación** | No |
| **Autor** | iRG |

### Dependencias

El módulo interactúa y depende de los siguientes componentes del sistema:
- `irg_gradebook_certificates` (Módulo base de gestión de solicitudes de certificados)
- `irg_campus_certificates_portal` (Interfaz unificada de certificados en el portal)

---

## Descripción General

El módulo `irg_certificate_partial` implementa la lógica específica para la generación de los **Certificados de Notas Parciales** (`gradebook_partial`). A diferencia del certificado completo (que exige cerrar la libreta con estado `done`), el certificado parcial se puede solicitar y generar mientras el alumno está cursando el programa académico (`state == 'in_progress'`).

### Características principales:
- **Estado Académico Flexible:** Se puede emitir con libretas activas.
- **Formateo de Notas Pendientes:** Si una asignatura obligatoria no tiene exámenes calificados (o su cantidad de calificaciones registradas es inferior al número de exámenes mínimos configurados en la libreta), se muestra el texto `"PENDIENTE"` en lugar de la nota numérica `0.0`.
- **Cálculo de la Nota Media:** La Nota Media final reflejada en el certificado se calcula de forma dinámica y justa, promediando única y exclusivamente aquellas asignaturas que dispongan de calificaciones completas (los valores float) y excluyendo los registros marcados como `"PENDIENTE"`. Si todas las asignaturas obligatorias están pendientes, la Nota Media final se reporta como `"PENDIENTE"`.

---

## Diseño Técnico

### 1. Modelos (`models/irg_certificate_request.py`)

Hereda el modelo base `irg.certificate.request` para modularizar la lógica de rellenado:

* **Carga de Plantilla (`_get_template_path`):**
  - Si el tipo de documento es `gradebook_partial`, localiza y utiliza de forma compartida las plantillas oficiales de notas del módulo `irg_gradebook_certificates` (`Plantilla-certificado-notas-dpto.docx` o `Plantilla-certificado-notas-raimon.docx` según el firmante) mediante `get_module_resource`. Esto previene duplicar archivos y simplifica el mantenimiento.

* **Reemplazo Dinámico (`_fill_template`):**
  - Sobrescribe la lógica de llenado del documento Word.
  - Itera sobre las asignaturas de tipo obligatorio (`compulsory`).
  - Obtiene el número total de exámenes requeridos (`qty` de tipo `exam` definido en las líneas de la plantilla de libreta).
  - Compara contra los resultados registrados del estudiante:
    - Si la lista de resultados de tipo `exam` está vacía o el número de resultados es inferior al requerido, la nota se establece como `"PENDIENTE"`.
    - De lo contrario, se formatea la nota real a dos decimales y se añade al grupo para promediar.
  - Genera dinámicamente la tabla XML del documento docx reemplazando los textos de código, nombre y nota.
  - Sobrescribe la celda del pie de tabla ("Nota Media") para mostrar el promedio dinámico calculado o `"PENDIENTE"` si corresponde.

---

## Suite de Pruebas Automatizadas

El módulo incluye un set de pruebas en `tests/test_partial.py`:
- `test_01_partial_gradebook_fill_template`: Crea un estudiante con dos asignaturas obligatorias. Una completa (2/2 exámenes calificados) y otra incompleta (1/2 exámenes). Valida que se genere el certificado parcial, que la asignatura completa tenga su nota numérica, la incompleta aparezca como "PENDIENTE", y la nota media final sea igual a la nota de la asignatura completa.
- `test_02_partial_gradebook_all_pending_fill_template`: Comprueba el comportamiento del módulo en casos límites donde todas las asignaturas obligatorias están pendientes. Valida que el certificado se cree correctamente y que la nota media final se imprima como "PENDIENTE".

---

## Instalación y Pruebas Locales

```bash
# Instalar y ejecutar tests
docker exec -it odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_certificate_partial --test-enable --stop-after-init
```
