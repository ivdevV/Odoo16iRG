# Descarga de Diplomados en el Portal del Alumno (Odoo 16)

Este documento describe detalladamente los patrones técnicos empleados para implementar el aislamiento y descarga segura de diplomas de posgrado y diplomados desde el portal web del estudiante, garantizando modularidad, legibilidad y robustez académica.

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
            
            # Buscar estudiantes del partner
            students = request.env['op.student'].sudo().search([
                ('partner_id', '=', partner.id)
            ])
            
            # Recuperar diplomados del histórico
            diplomados_raw = request.env['irg.diplomado.registry'].sudo().search([
                ('student_id', 'in', students.ids),
            ], order='id desc')
            
            # Procesar lógica de libreta y descarga
            diplomados_data = []
            for d in diplomados_raw:
                gradebook = request.env['app.gradebook.student'].sudo().search([
                    ('student_id', '=', d.student_id.id),
                    ('course_id', '=', d.course_id.id),
                ], limit=1)
                
                final_grade = gradebook.total_final if gradebook else 0.0
                can_download = final_grade > 7.0
                
                diplomados_data.append({
                    'record': d,
                    'final_grade': final_grade,
                    'can_download': can_download,
                })
                
            # Exponer los datos en el contexto de QWeb sin sobreescribir el resto
            response.qcontext['diplomados_data'] = diplomados_data
            
        return response
```

### Ventajas de este patrón:
- **Preservación de Rutas:** Se conserva la ruta original `/campus/certificates` sin necesidad de duplicarla o colisionar con otros controladores.
- **Acumulación de Contexto:** Al usar `super()`, la respuesta original (con los certificados que ya listaba el módulo base) se genera primero, y luego simplemente inyectamos la clave `diplomados_data` en el `qcontext`.

---

## 2. Patrón de Exclusión y Filtrado por Controladores en Formularios

Para evitar la solicitud y tramitación de tasas de certificados para cursos que son diplomados (ya que estos se expiden de manera gratuita mediante el histórico), se debe excluir e invalidar este flujo tanto en el frontend como en el backend.

El endpoint `/campus/certificates/new` gestiona tanto la presentación del formulario (método `GET`) como el procesamiento del envío de la solicitud (método `POST`).

### A. Filtrado en la Carga del Formulario (GET)
Cuando se carga el formulario, el controlador intercepta la lista de libretas de calificaciones disponibles (`gradebooks`) que se pasarán al combo de selección en QWeb. Se realiza un filtrado mediante el método `.filtered()` del RecordSet para eliminar aquellas correspondientes a diplomados:

```python
    @http.route(
        '/campus/certificates/new',
        type='http',
        auth='user',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def certificate_new(self, **post):
        # 1. Ejecutar comportamiento padre (que generará qcontext o procesará el POST)
        # Si es POST, primero procesamos la validación de seguridad de datos enviados
        ...
```

El filtrado en Odoo 16 se hace después del `super()`, modificando la variable `gradebooks` en el `qcontext`:

```python
        response = super(IrgCampusDiplomadosPortal, self).certificate_new(**post)

        if hasattr(response, 'qcontext') and 'gradebooks' in response.qcontext:
            gradebooks = response.qcontext['gradebooks']
            # Excluir las libretas académicas de diplomados
            response.qcontext['gradebooks'] = gradebooks.filtered(lambda gb: not gb.course_id.is_diplomado())

        return response
```

### B. Validación y Sanitización del Envío (POST)
Si un usuario intenta saltarse la validación visual del frontend y envía directamente una solicitud POST con el ID de una libreta de diplomado, el backend debe interceptarlo **antes** de delegar al controlador padre. 

Al cambiar el `gradebook_id` enviado a `'0'`, el controlador original del módulo base no encontrará una libreta válida y rechazará la solicitud de forma nativa devolviendo un error del formulario ("Selecciona la libreta"):

```python
        if request.httprequest.method == 'POST':
            gradebook_id = int(post.get('gradebook_id', 0) or 0)
            if gradebook_id:
                gradebook = request.env['app.gradebook.student'].sudo().browse(gradebook_id)
                # Si la libreta pertenece a un diplomado, invalidamos la solicitud
                if gradebook.exists() and gradebook.course_id.is_diplomado():
                    post['gradebook_id'] = '0'  # Provoca fallo nativo por libreta no seleccionada
```

---

## 3. Patrón de Inyección de Pestañas y Paneles Independientes mediante XPath

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
        <!-- Listado específico de diplomados -->
        <t t-if="not diplomados_data">
            ...
        </t>
        <t t-else="">
            ...
        </t>
    </div>
</xpath>
```

---

## 4. Validación del Rendimiento Académico para Proteger Descargas

La validación del rendimiento del estudiante no debe recaer de manera única en la UI (ocultando el botón). Es imperativo implementar una doble capa de validación directamente en el endpoint de descarga para evitar peticiones malintencionadas o accesos directos por URL.

### Lógica de Control y Protección del Endpoint
Cuando el usuario llama a `/campus/certificates/download/diplomado/<int:diplomado_id>`, el controlador valida el rendimiento académico en la base de datos contra el modelo de libreta de calificaciones `app.gradebook.student`:

```python
# 1. Control de seguridad y pertenencia
partner = request.env.user.partner_id
diplomado = request.env['irg.diplomado.registry'].sudo().browse(diplomado_id)

if not diplomado.exists() or diplomado.student_id.partner_id.id != partner.id:
    return request.redirect('/campus/certificates')

# 2. Validación de rendimiento académico
gradebook = request.env['app.gradebook.student'].sudo().search([
    ('student_id', '=', diplomado.student_id.id),
    ('course_id', '=', diplomado.course_id.id),
], limit=1)

# El criterio estricto exige que la nota final sea superior a 7.0
if not gradebook or gradebook.total_final <= 7.0:
    return request.redirect('/campus/certificates?error=grade_too_low')

# 3. Envío del archivo
# (Si no existe el binario adjunto, se genera dinámicamente)
if not diplomado.attachment_id or not diplomado.attachment_id.datas:
    diplomado.action_reprint()

data = io.BytesIO(base64.standard_b64decode(diplomado.attachment_id.datas))
filename = diplomado.attachment_id.name or "diplomado.pdf"
return http.send_file(data, filename=filename, as_attachment=True)
```

### Reglas del Criterio Académico:
- **Origen de la Calificación:** La nota final se lee del campo `total_final` en el modelo `app.gradebook.student` correspondiente al estudiante y curso del diplomado.
- **Límite Estricto:** La calificación final debe ser **estrictamente mayor a 7.0** (`gradebook.total_final > 7.0`). Si la nota es menor o igual, la descarga se bloquea de forma inmediata a nivel de backend.
- **Redirección Segura:** El bloqueo redirige a la lista de certificados del portal agregando el query parameter `error=grade_too_low`, activando la alerta visual del frontend.
