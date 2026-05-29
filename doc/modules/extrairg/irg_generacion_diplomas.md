# irg_generacion_diplomas

**Categoría:** extrairg
**Versión:** 16.0.1.0.1
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** ISEP / iRG
**Depende de:** `openeducat_core`, `web`, `website`

---

## ¿Qué hace este módulo?

Permite generar diplomas físicos y digitales para los alumnos directamente desde la ficha del estudiante. Soporta nombres de cursos en catalán, genera automáticamente un código QR y un número de registro para cada diploma, y tiene diseño adaptado para nombres de cursos largos.

Dependencias externas Python: `qrcode`, `reportlab`.

## Funcionalidades principales

- Wizard de generación de diplomas desde `op.student`.
- Soporte para diplomas físicos y digitales.
- Gestión de nombres de cursos en catalán.
- Generación automática de QR y número de registro.
- Plantilla de diseño adaptada para cursos con nombres largos.
- Página de verificación de diploma en el sitio web.
- Secuencia numérica para los diplomas.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.diploma.wizard` (nuevo) | Nuevo | Alumno, tipo, curso en catalán |

## Vistas y UI

- `views/op_course_views.xml` — campo de nombre en catalán en el formulario de curso.
- `wizard/diploma_wizard_views.xml` — wizard de generación.
- `views/op_student_views.xml` — botón de diploma en la ficha del alumno.
- `views/diploma_verify_templates.xml` — página de verificación web.

## Notas técnicas

- Dependencias externas: `pip install qrcode reportlab` en el contenedor.
- Requiere `security/ir.model.access.csv`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_generacion_diplomas \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_generacion_diplomas \
    --stop-after-init --db_host=pgodoo_latest
```

## Historial de Cambios

### Versión 16.0.1.0.1 (V2.3)
- **Mejora Estética del Layout**: Se ajustó la posición de renderizado vertical de los nombres de los másteres en el PDF de ReportLab. Se modificó el desplazamiento vertical de `y -= sp(28)` a `y -= sp(38)` en la línea 215 del generador. Esto añade un espaciado visual (aire) de 10 puntos respecto a la cabecera superior. Las posiciones de los elementos subsiguientes se calculan dinámicamente de forma relativa a este desplazamiento, manteniendo la cohesión y previniendo solapamientos en todo el diploma.

