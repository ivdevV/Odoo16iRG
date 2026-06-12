# irg_openeducat_sale_online_quarterly

**Categoría:** Sales / OpenEduCat
**Versión:** 16.0.1.1.0
**Autor:** Instituto Raimon Gaja
**Depende de:** `irg_openeducat_sale_lote_custom`, `isep_openeducat_sale`

---

## ¿Qué hace este módulo?

Este módulo gestiona la creación y asignación de convocatorias (lotes `op.batch`) de tipo trimestral de forma exclusiva para los cursos en modalidad **Online (ONL)**. 

HC (HomeClass), PRS (Presencial) y GE (General) no se ven afectados por este módulo y continúan con su flujo de facturación mensual regular controlado por `irg_openeducat_sale_lote_custom`.

---

## Configuración y Activación

Para activar el flujo trimestral online, se debe marcar el campo **Convocatoria Trimestral Online** en la configuración general de Odoo (**auto.admission.required** -> `quarterly_online_enabled`). 

Si este parámetro está inactivo, el módulo delega 100% en el comportamiento mensual estándar del módulo base.

---

## Lógica del Código Trimestral

Cuando el flujo está activo y el curso es modalidad Online:
1. El sistema mapea el mes de la fecha efectiva de admisión a una letra/número de trimestre:
   - **Enero - Marzo** -> Trimestre `1`
   - **Abril - Junio** -> Trimestre `2`
   - **Julio - Septiembre** -> Trimestre `3`
   - **Octubre - Diciembre** -> Trimestre `4`
2. El código del lote se construye usando la estructura:
   ```text
   <categoría><código_curso>ONL<año><trimestre>
   ```
   *Ejemplo:* `MPSCONL263` para un máster propio de Sexología (`SC`) en julio de 2026.

---

## Reglas de Normalización de Códigos

Este módulo incorpora las mismas reglas de robustez de `irg_openeducat_sale_lote_custom`:
- **Normalización de Masters (MO/MP)**: Si el producto pertenece a la categoría Máster (código inicia con `M` y no es `MB`, o nombre contiene "master"), se normaliza el prefijo de categoría a `MO` si el nombre de curso o producto contiene la palabra "oficial", o `MP` en caso contrario.
- **Limpieza de código de curso duplicado**: Si el prefijo de categoría empieza por `M` y el código del curso también empieza por `M` (caso `MSC`), se limpia la primera letra del curso (quedando `SC`) para evitar códigos duplicados como `MOMSC...`.
- **Prevención de creación en borrador**: Respeta el contexto `irg_no_create_batch` para no forzar la creación de nuevos lotes en la base de datos si la admisión permanece en estado borrador.

---

## Changelog

### 2026-06-12 (16.0.1.1.0)

- **Normalización de categoría de Masters**: Alineación con la lógica de categorías `MO`/`MP` basada en la palabra "oficial" en los nombres de cursos/productos.
- **Limpieza de duplicidad de M en curso**: Eliminación automática de la `M` redundante de los códigos de curso (ej. `MSC` -> `SC`) al construir lotes trimestrales online.
- **Evitar creación de lotes en borrador**: Soporte para retornar un recordset de lote vacío si `irg_no_create_batch` está en el contexto y el lote no existe.

### 2026-06-02 (16.0.1.0.0)

- Versión inicial del módulo que implementa el mapeo trimestral (1-4) para cursos en modalidad Online (ONL).
