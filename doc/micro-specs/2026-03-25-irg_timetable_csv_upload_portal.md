# Micro-spec: Portal Web de Upload de Calendarios (irg_timetable_csv_upload_portal)

**Fecha:** 2026-03-25  
**Módulo:** `irg_timetable_csv_upload_portal`  
**Versión:** 16.0.1.0.0  
**Responsable:** Equipo Desarrollo iRG

---

## 1. Título Corto
**Upload seguro de CSV de calendarios en `/campus` con interfaz de gestor**

---

## 2. Resumen Objetivo
Agregar un botón/tarjeta en la página del portal `/campus` que permita a gestores y administradores subir el archivo CSV consolidado (`Calendario_Global_iRG.csv`) sin acceder a la terminal ni Odoo backend. La interfaz validará el archivo y disparará la importación automáticamente.

---

## 3. Motivo / Justificación
- **Usabilidad:** No todos los usuarios gestores pueden acceder a la terminal o paneles de Odoo.
- **Seguridad:** Restringir a roles específicos (gestor/admin de web).
- **Automatización:** Integrar el flujo de upload con el cron existente sin fricción.
- **No es override:** Es una extensión funcional; usamos un módulo nuevo con herencia ligera.

---

## 4. Alcance Exacto

### Modelos
- **Nuevo:** `irg.timetable.csv.upload` — registro del archivo subido (archivo, usuario, timestamp, estado)
- **No modificar:** modelos existentes (`irg.timetable.import.log`, etc.)

### Vistas / Templates
- **Nueva ruta HTTP:** `GET/POST /campus/csv-upload` (portal web)
- **Nueva template QWeb:** mostrar formulario de upload + estado último
- **Nueva tarjeta/botón:** en la página `/campus` (vista existente heredada con xpath)

### Seguridad
- **Grupo requerido:** `website.group_website_publisher` (gestores de sitio) O `base.group_erp_manager` (admins Odoo)
- **ACL:** permitir crear/leer registros solo a gestores
- **Validación:** archivo debe ser CSV, <10MB, con columnas esperadas

### Assets
- Ninguno especial (formulario simple con Bootstrap del sitio web)

---

## 5. Diseño Técnico

### Estructura de Carpetas
```
addons-extra/extrairg/irg_timetable_csv_upload_portal/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   └── csv_upload.py         # Modelo irg.timetable.csv.upload
├── controllers/
│   ├── __init__.py
│   └── portal.py             # Controlador HTTP /campus/csv-upload
├── views/
│   ├── csv_upload_views.py
│   └── portal_upload_template.xml   # Template QWeb
├── security/
│   └── ir.model.access.csv
└── static/
    └── (sin assets específicos)
```

### Modelo: `irg.timetable.csv.upload` {#modelo}

```python
class IrgTimetableCSVUpload(models.Model):
    _name = 'irg.timetable.csv.upload'
    _description = 'Upload de CSV de Calendarios'
    _order = 'upload_date desc'

    # Campos
    name = CharField  # nombre del archivo original
    upload_date = DatetimeField  # timestamp del upload
    uploaded_by = Many2oneField('res.users')  # usuario que subió
    file_content = BinaryField  # contenido del CSV
    file_path = CharField  # ruta donde se guardó (opcional)
    state = Selection  # 'pending', 'processing', 'done', 'error'
    error_message = TextField  # si hay error
    import_log_id = Many2oneField('irg.timetable.import.log')  # referencia al log después de importar
```

### Controlador HTTP {#controller}

**Ruta: `/campus/csv-upload`**

```python
class TimetableCSVUploadController(http.Controller):
    
    @http.route('/campus/csv-upload', auth='user', website=True)
    def upload_page(self, **kwargs):
        """Página de upload — solo si el usuario es gestor/admin"""
        # _check_access() — lanza HTTP 403 si no tiene permisos
        # render template con form
        
    @http.route('/campus/csv-upload/action', auth='user', website=True, methods=['POST'], csrf=True)
    def upload_action(self, **kwargs):
        """Procesa el upload"""
        # _check_access()
        # validar CSV: tamaño, columnas, encoding
        # crear registro irg.timetable.csv.upload
        # mover archivo a watch_dir
        # disparar cron manualmente (opcional) o dejar que cron lo procese
        # redirigir a upload_page con mensaje
```

### Template QWeb {#template}

**Ubicación:** `views/portal_upload_template.xml`

```xml
<t t-extend="website.layout">
    <xpath expr="//div[@class='oe_structure']">
        <div class="container mt-5">
            <h1>Actualizar Calendarios Académicos</h1>
            
            <!-- Formulario de upload -->
            <form method="POST" action="/campus/csv-upload/action" enctype="multipart/form-data">
                <input type="hidden" name="csrf_token" value="..."/>
                
                <div class="form-group">
                    <label for="csv_file">Selecciona el archivo CSV:</label>
                    <input type="file" name="csv_file" accept=".csv" required/>
                </div>
                
                <button type="submit" class="btn btn-primary">Subir y Actualizar</button>
            </form>
            
            <!-- Historial de uploads (últimos 5) -->
            <hr/>
            <h3>Historial de uploads</h3>
            <table class="table">
                <tr>
                    <th>Archivo</th>
                    <th>Usuario</th>
                    <th>Fecha</th>
                    <th>Estado</th>
                </tr>
                <tr t-foreach="uploads" t-as="upload">
                    <td><t t-out="upload.name"/></td>
                    <td><t t-out="upload.uploaded_by.name"/></td>
                    <td><t t-out="upload.upload_date"/></td>
                    <td>
                        <span t-if="upload.state == 'done'" class="badge badge-success">✓ OK</span>
                        <span t-elif="upload.state == 'error'" class="badge badge-danger">✗ Error</span>
                        <span t-else="" class="badge badge-warning">⏳ Procesando</span>
                    </td>
                </tr>
            </table>
        </div>
    </xpath>
</t>
```

### Tarjeta en `/campus` {#tarjeta}

**Ubicación:** heredar la vista `website.portal_my_home` con xpath

```xml
<record id="view_portal_csv_upload_card" model="ir.ui.view">
    <field name="name">Portal CSV Upload Card</field>
    <field name="model">ir.ui.view</field>
    <field name="inherit_id" ref="website.portal_my_home"/>
    <field name="arch" type="xml">
        
        <!-- Agregar tarjeta de upload al final de las aplicaciones -->
        <xpath expr="//div[@class='row']" position="inside">
            <t t-if="user.has_group('website.group_website_publisher') or user.has_group('base.group_erp_manager')">
                <div class="col-md-4 mb-3">
                    <a href="/campus/csv-upload" class="card h-100 text-decoration-none">
                        <div class="card-body text-center">
                            <i class="fa fa-upload fa-3x text-primary mb-3"/>
                            <h5 class="card-title">Actualizar Calendarios</h5>
                            <p class="card-text">Subir archivo CSV con fechas de sesiones</p>
                        </div>
                    </a>
                </div>
            </t>
        </xpath>
        
    </field>
</record>
```

---

## 6. Dependencias

**`__manifest__.py`:**
```python
{
    'name': 'Upload Web Calendarios',
    'version': '16.0.1.0.0',
    'depends': [
        'website',
        'web',
        'irg_timetable_csv_import',  # importar del módulo principal
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/csv_upload_views.xml',
        'views/portal_upload_template.xml',
    ],
    'installable': True,
    'license': 'OPL-1',
}
```

---

## 7. Backwards-Compatibility / Migración
- **No afecta** datos existentes ni workflows
- **Módulo nuevo:** puede instalarse sin efectos secundarios
- **Rollback:** desinstalar módulo; la tarjeta desaparece automáticamente

---

## 8. Casos de Prueba / Criterios de Aceptación

| # | Caso | Esperado |
|---|------|----------|
| 1 | Usuario no autenticado accede `/campus/csv-upload` | Redirigir a login |
| 2 | Usuario normal (sin permisos) accede `/campus/csv-upload` | Mostrar 403 Forbidden |
| 3 | Usuario gestor accede `/campus/csv-upload` | Mostrar formulario |
| 4 | Usuario admin accede `/campus/csv-upload` | Mostrar formulario |
| 5 | Subir CSV válido | Archivo se mueve a watch_dir; mensaje "OK" |
| 6 | Subir archivo que no es CSV | Mostrar error "Archivo debe ser .csv" |
| 7 | Subir CSV > 10MB | Mostrar error "Archivo muy grande" |
| 8 | Subir CSV sin columnas requeridas | Mostrar error "Columnas faltantes" |
| 9 | Tarjeta visible para gestor en `/campus` | Tarjeta aparece (icono upload + texto) |
| 10 | Tarjeta invisible para usuario normal | Tarjeta NO aparece |
| 11 | Historial muestra últimos 5 uploads | Lista correcta de archivos |
| 12 | Click en historial → detalles de error (si error) | Detalle visible |

---

## 9. Rollback Plan

```bash
# En docker
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
  -d odoo16_production \
  -u irg_timetable_csv_upload_portal \
  --uninstall-before-remove \
  --db_host=pgodoo_latest

# O manualmente en Odoo: Aplicaciones > Módulos > Desinstalar
```

---

## 10. Estimación y Responsable

| Aspecto | Duración |
|--------|----------|
| **Implementación** | ~2 horas |
| **Testing** | ~1 hora |
| **Total** | ~3 horas |

**Responsable:** Equipo Desarrollo iRG

---

## Notas Técnicas

### Validación de CSV
```python
# En el controlador, validar:
- Tamaño < 10MB
- Extensión == .csv
- Encoding UTF-8 válido
- Columnas requeridas presentes: "Máster/Programa", "Fecha", "Nombre Asignatura", "Docente"
- No vacío
```

### Integración con cron existente
- El archivo subido se copia directo a `watch_dir`
- El cron existente `irg_timetable_csv_import.cron_process_csv_directory` lo procesa automáticamente cada 6 horas
- O el controlador puede llamar a `cron_process_csv_directory()` manualmente (opcional)

### Seguridad CSRF
- Usar `@http.route(..., csrf=True)` en POST
- Token `csrf_token` en form oculto

### Encoding
- Aceptar solo UTF-8 o UTF-8-SIG (con BOM)
- No Latin-1 ni otros

---

## Cambios Posteriores Planeados

Ninguno identificado en este momento.
