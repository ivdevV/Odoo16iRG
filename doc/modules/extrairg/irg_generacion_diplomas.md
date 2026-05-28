# irg_generacion_diplomas

**Categoría:** extrairg  
**Versión:** 16.0.2.0.0  
**Licencia:** AGPL-3  
**Instalable:** Sí  
**Autor:** ISEP / iRG  
**Depende de:** `openeducat_core`, `web`, `website`  

---

## ¿Qué hace este módulo?

Permite generar diplomas físicos y digitales para los alumnos directamente desde la ficha del estudiante o a través del portal de alumnos. En la versión 16.0.2.0.0, el motor de generación ha sido migrado de ReportLab a plantillas de Word (`.docx`) dinámicas y compilación mediante LibreOffice, mejorando significativamente la flexibilidad del diseño y manteniendo la generación automatizada de códigos QR y números de registro.

## Dependencias de Sistema y Python

- **Librerías Python**: `qrcode`, `python-docx` (declarada en el manifiesto como `docx`), `reportlab`.
- **Sistema**: Requiere que `libreoffice` (o `soffice`) esté instalado en el sistema/contenedor para realizar la conversión de documentos Word a PDF en modo headless.
  - **Búsqueda del Ejecutable**: El módulo busca el ejecutable de forma automática y secuencial:
    1. A través del parámetro del sistema de Odoo: `irg.libreoffice.path` (ruta absoluta configurable en los Parámetros del Sistema en modo técnico).
    2. Buscando `'libreoffice'` en el `PATH` del sistema (`shutil.which`).
    3. Buscando `'soffice'` en el `PATH` del sistema (común en macOS o instalaciones de desarrollo en host).
    4. Evaluando rutas absolutas predeterminadas comunes para Linux, macOS y Windows (ej. `/usr/bin/libreoffice`, `/Applications/LibreOffice.app/Contents/MacOS/soffice`, etc.).
  - Si no lo encuentra, lanza un `UserError` indicando los pasos para instalarlo o configurarlo en los parámetros del sistema.

## Funcionalidades principales

- **Generación mediante Plantillas Word**: Carga dinámica de plantillas DOCX ubicadas en `static/` del módulo:
  - Digital: `Plantilla Diplomas iRG Digital final.docx`
  - Físico: `Plantilla Diploma fisico.docx`
- **Inyección de Código QR Dinámico**:
  - En la plantilla digital, se reemplaza la etiqueta de texto `<<Imagen_QR>>` insertando la imagen del QR de forma inline.
  - En la plantilla física, se localiza la relación de imagen placeholder (`blip` drawing) en los runs del documento y se sobreescriben directamente sus bytes en el paquete zip del docx (`related_parts`), preservando de forma exacta la maquetación.
- **Limpieza de Temporales y Seguridad**: Toda la generación intermedia de códigos QR (PNG), archivos `.docx` modificados y archivos `.pdf` se realiza bajo un bloque `try...finally` general en `/tmp/`, garantizando que todos los archivos temporales se eliminen incondicionalmente tras su procesamiento.

## Modelos y Componentes

| Modelo / Reporte | Tipo | Función |
|------------------|------|---------|
| `irg.diploma.wizard` | Wizard | Permite seleccionar el alumno, tipo de diploma y curso para su generación desde el backend. |
| `report.irg_generacion_diplomas.diploma_pdf` | Reporte Abstracto | Contiene el método `generate_diploma_pdf(self, data, diploma_type='digital')` que constituye el motor central de generación. |

### Variables de Reemplazo en Plantillas

#### Plantilla Digital
- `<<Mastercat>>` -> Nombre del curso en Catalán.
- `<<Master>>` -> Nombre del curso en Castellano.
- `NombreAlumno>>` -> Nombre del estudiante (búsqueda flexible para evitar interferencias de formato en Word).
- `<<fechacat>>` -> Fecha en Catalán.
- `<<fecha>>` -> Fecha en Castellano.
- `<<registro>>` -> Número de Registro del Diploma.
- `<<Imagen_QR>>` -> Código QR insertado inline.

#### Plantilla Física
- `<<NombreCursoCat>>` -> Nombre del curso en Catalán.
- `<<NombreCurso>>` -> Nombre del curso en Castellano.
- `<<NombreAlumno>>` -> Nombre del estudiante.
- `<<FechaExpedidoCat>>` -> Fecha en Catalán.
- `<<FechaExpedido>>` -> Fecha en Castellano.
- `IRG-2026-0126` -> Número de Registro del Diploma.
- Placeholder de Imagen -> Código QR inyectado por manipulación binaria de la relación de la imagen.

## Instalación / Actualización

Dado que se han añadido dependencias y nuevas plantillas estáticas, se debe actualizar el módulo:

```bash
# Actualizar en contenedor local
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_generacion_diplomas --stop-after-init
```

## Historial de Cambios (Changelog)

### v16.0.2.0.0
- **Migración de Motor**: Se sustituyó ReportLab por `python-docx` y LibreOffice headless.
- **Plantillas DOCX**: Incorporación de `Plantilla Diplomas iRG Digital final.docx` y `Plantilla Diploma fisico.docx`.
- **Inyección de Imagen QR**: Implementación de inyección nativa en Word (para digital) y manipulación a nivel de bytes de relaciones blip en XML de Word (para físico).
- **Seguridad**: Bloque `try...finally` estricto con eliminación garantizada de temporales en `/tmp/` para prevenir fugas de datos y sobrellenado del disco.
