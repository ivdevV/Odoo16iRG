# Descarga de Diplomados en el Portal del Alumno (Odoo 16)

Este documento describe detalladamente los patrones técnicos empleados para implementar la descarga segura de diplomas de posgrado y diplomados desde el portal web del estudiante, garantizando modularidad, legibilidad y robustez académica.

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

## 2. Patrón de Inyección de Subsecciones en Vistas mediante XPath en Odoo 16

Para extender y modificar las plantillas QWeb del portal sin alterar el código original del módulo padre, se utiliza herencia XML (`inherit_id`) e inyección mediante expresiones XPath.

### Inyección de la Tabla de Diplomados
La plantilla hereda de `irg_campus_certificates_portal.portal_certificate_list_override` e inyecta la subsección usando `position="inside"` en el contenedor correspondiente:

```xml
<template id="portal_certificate_list_diplomados_override" inherit_id="irg_campus_certificates_portal.portal_certificate_list_override">
    
    <!-- 1. Alerta de error por nota insuficiente -->
    <xpath expr="//t[@t-if=&quot;request.params.get('error') == 'no_pdf'&quot;]" position="before">
        <t t-if="request.params.get('error') == 'grade_too_low'">
            <div class="alert alert-danger alert-dismissible fade show border-start border-4 border-danger shadow-sm mb-4" role="alert">
                <i class="fa fa-times-circle me-2 text-danger"/>
                <strong>Calificación insuficiente:</strong> No cumples con los requisitos académicos de calificación final mínima (7.0) para poder imprimir este diploma.
            </div>
        </t>
    </xpath>

    <!-- 2. Contenido de la subsección dentro de la pestaña de diplomas -->
    <xpath expr="//div[@id='diplomas-pane']" position="inside">
        <t t-if="diplomados_data">
            <div class="mt-5 pt-4 border-top">
                <h4 class="h5 mb-0 text-primary fw-bold">Diplomas de Posgrados y Diplomados</h4>
                <!-- Renderizado de la tabla con t-foreach="diplomados_data" t-as="d" -->
                ...
            </div>
        </t>
    </xpath>
</template>
```

### Elementos Clave de Diseño:
- **Control Condicional de Botones:** En base a `d['can_download']`, la interfaz renderiza condicionalmente el botón de descarga (`<a>` con la ruta de descarga) o un elemento badge que indica que el diploma está "Bloqueado" junto a un icono de candado (`<i class="fa fa-lock"/>`).
- **Formateo Numérico:** Calificaciones formateadas de manera uniforme mediante `<t t-out="'%.2f' % d['final_grade']"/>` con colores dinámicos según el estado de la descarga (`text-success` si cumple, `text-danger` si no).

---

## 3. Validación del Rendimiento Académico para Proteger Descargas

La validación del rendimiento del estudiante no debe recaer de manera única en la UI (ocultando el botón). Es imperativo implementar una doble capa de validación directamente en el backend (dentro del endpoint de descarga) para evitar peticiones malintencionadas o accesos directos por URL.

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
