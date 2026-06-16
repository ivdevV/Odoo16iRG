# Descarga de Diplomados en el Portal del Alumno (Odoo 16)

Este documento describe detalladamente los patrones técnicos empleados para implementar el aislamiento, solicitud gratuita y descarga segura de diplomas de posgrado y diplomados desde el portal web del estudiante, garantizando modularidad, legibilidad y robustez académica.

---

## 1. Patrón de Herencia Limpia de Controladores del Portal

En Odoo 16, la extensión de rutas de controladores existentes debe realizarse heredando de la clase del controlador original y sobrescribiendo sus métodos. Esto evita redefiniciones de rutas en conflicto y permite acumular lógica de diferentes módulos de manera limpia.

### Implementación Técnica
El controlador `IrgCampusDiplomadosPortal` hereda de `IrgCampusCertificatesPortal` (del módulo base de certificados):

```python
from odoo import http
from odoo.http import request
from odoo.addons.irg_campus_certificates_portal.controllers.portal import IrgCampusCertificatesPortal

class IrgCampusDiplomadosPortal(IrgCampusCertificatesPortal):

    @http.route(
        '/campus/certificates',
        type='http',
        auth='user',
        website=True,
        methods=['GET'],
    )
    def certificate_list(self, **kw):
        # 1. Ejecutar el comportamiento original del padre
        response = super(IrgCampusDiplomadosPortal, self).certificate_list(**kw)
        
        # 2. Inyectar datos específicos si la respuesta es un render QWeb
        if hasattr(response, 'qcontext'):
            partner = request.env.user.partner_id
            
            # Buscar estudiantes del partner y diplomados del histórico
            ...
```

---

## 2. Patrón de Herencia Contextual y Visibilidad Dinámica por Parámetros (Query Params)

Para mantener una navegación enfocada e impedir que el usuario navegue fuera del alcance de su programa actual cuando es redirigido desde el curso de un diplomado, se aplica una visibilidad condicional en la interfaz web de Odoo basada en parámetros de URL.

### A. Lógica en el Controlador (Backend)
El controlador lee el parámetro `course_id` de los argumentos HTTP de tipo GET (`**kw`). Si este existe y corresponde a un diplomado, activa la bandera `only_diplomados = True` y filtra estrictamente los datos que se mostrarán en la vista, eliminando información de otros programas:

```python
        course_id = kw.get('course_id')
        only_diplomados = False
        if course_id:
            try:
                course = request.env['op.course'].sudo().browse(int(course_id))
                if course.exists() and course.is_diplomado():
                    only_diplomados = True
                    # Filtrar datos exclusivamente para este curso
                    diplomados_data = [d for d in diplomados_data if d['record'].course_id.id == course.id]
                    solicitudes_tramite = solicitudes_tramite.filtered(lambda r: r.course_id.id == course.id)
                    disponibles_solicitar = [gb for gb in disponibles_solicitar if gb.course_id.id == course.id]
            except Exception:
                pass
                
        response.qcontext.update({
            'diplomados_data': diplomados_data,
            'solicitudes_tramite': solicitudes_tramite,
            'disponibles_solicitar': disponibles_solicitar,
            'only_diplomados': only_diplomados,
        })
```

### B. Ocultamiento de la Interfaz en QWeb (Frontend)
En la plantilla XML se envuelven las pestañas comunes ("Mis Diplomas", "Actas TFM/TFG", "Solicitudes") y el botón superior "+ Nueva Solicitud" con condicionales QWeb que evalúan la bandera inyectada:

```xml
<!-- Ocultamiento dinámico del botón superior de Nueva Solicitud -->
<xpath expr="//a[contains(@href, '/campus/certificates/new')]" position="replace">
    <t t-if="not only_diplomados">
        <a href="/campus/certificates/new" class="btn btn-primary">
            <i class="fa fa-plus me-1"/> Nueva Solicitud
        </a>
    </t>
</xpath>
```
Este patrón evita el "ruido visual" y guía al estudiante de forma contextual en el flujo de su diplomado específico.

---

## 3. Patrón de Vinculación Automatizada y Reactiva de Estados

Cuando un administrador del centro educativo emite o registra el diploma oficial en el backend (creando un registro en `irg.diplomado.registry`), el sistema debe actualizar de forma reactiva el estado de cualquier solicitud de trámite web pendiente que haya hecho el alumno en el portal.

### Implementación en el Modelo (Backend)
Se extiende la creación del modelo de registro (`irg.diplomado.registry`) mediante herencia clásica de Odoo para interceptar el método `create`:

```python
class IrgDiplomadoRegistry(models.Model):
    _inherit = 'irg.diplomado.registry'

    @api.model
    def create(self, vals):
        # 1. Crear el registro original en el histórico
        record = super(IrgDiplomadoRegistry, self).create(vals)
        
        # 2. Buscar si el estudiante tenía una solicitud activa para este curso en el portal
        solicitud = self.env['irg.diplomado.request'].sudo().search([
            ('student_id', '=', record.student_id.id),
            ('course_id', '=', record.course_id.id),
            ('state', '=', 'requested')
        ], limit=1)
        
        # 3. Vincular de manera automatizada y reactiva
        if solicitud:
            solicitud.write({
                'diplomado_registry_id': record.id,
                'state': 'processed' # Cambia de "Solicitado" a "Procesado"
            })
            
        return record
```

### Ventajas del Patrón:
- **Desacoplamiento:** El módulo de expedición base no conoce la existencia del portal de solicitudes; la reactividad e integración se inyectan limpiamente en el módulo del portal.
- **Sincronización Inmediata:** La interfaz del portal del alumno se actualiza de inmediato para reflejar el estado "Procesado", moviendo el registro de "Expediciones en Trámite" a "Títulos Emitidos" para habilitar la descarga del PDF.

---

## 4. Patrón de Exclusión y Filtrado por Controladores en Formularios

Para evitar la solicitud y tramitación de tasas de certificados para cursos que son diplomados (ya que estos se expiden de manera gratuita mediante el histórico), se debe excluir e invalidar este flujo tanto en el frontend como en el backend.

### A. Filtrado en la Carga del Formulario (GET)
Cuando se carga el formulario, el controlador intercepta la lista de libretas de calificaciones disponibles (`gradebooks`) que se pasarán al combo de selección en QWeb. Se realiza un filtrado mediante el método `.filtered()` del RecordSet para eliminar aquellas correspondientes a diplomados:

```python
        response = super(IrgCampusDiplomadosPortal, self).certificate_new(**post)

        if hasattr(response, 'qcontext') and 'gradebooks' in response.qcontext:
            gradebooks = response.qcontext['gradebooks']
            response.qcontext['gradebooks'] = gradebooks.filtered(lambda gb: not gb.course_id.is_diplomado())

        return response
```

### B. Validación y Sanitización del Envío (POST)
Si un usuario intenta saltarse la validación visual del frontend y envía directamente una solicitud POST con el ID de una libreta de diplomado, el backend debe interceptarlo **antes** de delegar al controlador padre. Al cambiar el `gradebook_id` enviado a `'0'`, el controlador original del módulo base no encontrará una libreta válida y rechazará la solicitud de forma nativa devolviendo un error del formulario ("Selecciona la libreta"):

```python
        if request.httprequest.method == 'POST':
            gradebook_id = int(post.get('gradebook_id', 0) or 0)
            if gradebook_id:
                gradebook = request.env['app.gradebook.student'].sudo().browse(gradebook_id)
                if gradebook.exists() and gradebook.course_id.is_diplomado():
                    post['gradebook_id'] = '0'  # Provoca fallo nativo por libreta no seleccionada
```

---

## 5. Patrón de Inyección de Pestañas y Paneles Independientes mediante XPath

En lugar de incrustar contenidos adicionales dentro de la misma sección de certificados de pago (lo cual genera confusión), se inyecta una pestaña (`nav-item`) y un panel (`tab-pane`) independientes dentro del contenedor principal del portal.

### Implementación en QWeb
```xml
<!-- Inyectar la pestaña en la lista de tabs -->
<xpath expr="//button[@id='diplomas-tab']/parent::li" position="after">
    <li class="nav-item" role="presentation">
        <button class="nav-link py-3 fw-bold border-0 rounded-0" id="diplomados-tab" data-bs-toggle="tab" data-bs-target="#diplomados-pane" type="button" role="tab" aria-controls="diplomados-pane" aria-selected="false">
            <i class="fa fa-certificate me-2 text-primary"/>Mis Diplomados
        </button>
    </li>
</xpath>

<!-- Inyectar el panel de la pestaña justo después del panel original -->
<xpath expr="//div[@id='diplomas-pane']" position="after">
    <div class="tab-pane fade" id="diplomados-pane" role="tabpanel" aria-labelledby="diplomados-tab">
        <!-- Listado específico de diplomados con tres subsecciones: Emitidos, Disponibles para Solicitar y En Trámite -->
        ...
    </div>
</xpath>
```
