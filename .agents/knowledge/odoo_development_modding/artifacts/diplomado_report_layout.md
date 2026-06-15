# Patrón de Diseño: Generación de PDFs a Sangre Completa (Full Bleed) con ReportLab

**Fecha:** 2026-06-15  
**Módulo de Referencia:** `addons-extra/extrairg/irg_generacion_diplomados`  
**Tecnología Recomendada:** ReportLab (Python)  

---

## El Problema: Inestabilidad de wkhtmltopdf en Full Bleed

En Odoo, el motor predeterminado para generar reportes en PDF es `wkhtmltopdf` (QWeb). Aunque funciona bien para informes estructurados tradicionales (facturas, listados), presenta graves deficiencias cuando se requiere un diseño a **sangre completa (Full Bleed)** sin márgenes, como en diplomas o certificados:

1. **Escala Asimétrica de la Impresora Simulada:** `wkhtmltopdf` simula una cola de impresión. Para ajustar el HTML al formato físico de la hoja, a menudo aplica una escala (como `1.08` o similar) o márgenes ocultos. Esto genera un renderizado deformado o distorsiones de aspecto en imágenes y fuentes vectoriales.
2. **Doble Anidamiento y Márgenes Forzados:** Los layouts base de Odoo (`web.basic_layout` u otros) inyectan divs intermedios como `.article` o `.page` con clases CSS de Bootstrap. Intentar forzar la anulación de estos márgenes vía CSS (`margin: 0 !important`) suele fallar de forma intermitente según la versión de Odoo y de wkhtmltopdf instalada.
3. **Imágenes Rotas por Resolución de URLs:** `wkhtmltopdf` se ejecuta como un proceso externo. Para renderizar imágenes en el HTML (`/web/image` o rutas de módulo locales), necesita resolver la URL mediante HTTP contra el propio servidor de Odoo. Si la variable `web.base.url` de los parámetros del sistema no está correctamente configurada, o existen problemas con la resolución DNS local (muy común en entornos Docker y Kubernetes), las firmas y logotipos aparecerán rotos (con un icono de imagen vacía) en el PDF final.
4. **Páginas en Blanco Extras:** Al intentar extender una imagen al 100% de la altura de la página (ej. `210mm` para un A4), los pequeños desvíos de redondeo de píxeles hacen que el motor detecte un desbordamiento de flujo y genere una página en blanco adicional no deseada.

---

## La Solución Definitiva: ReportLab en Python

La solución robusta y profesional consiste en prescindir de QWeb y maquetar directamente en memoria utilizando **ReportLab**. Este motor de dibujo vectorial en Python nos da un control absoluto sobre el lienzo del PDF.

### Ventajas de ReportLab:
- **Cero dependencias del motor del cliente:** Se compila en el servidor y genera un PDF exacto.
- **Acceso Directo al Disco Local:** Las imágenes y firmas se cargan directamente desde la ruta del disco del servidor (usando `modules.get_module_resource`), garantizando un 100% de disponibilidad de imágenes y evitando consultas DNS/HTTP externas.
- **Precisión Milimétrica Nativa:** El canvas de ReportLab permite posicionar y dibujar de forma vectorial en unidades físicas (`mm`, `inch`, `cm`, `points`).
- **Control Físico de Páginas:** La creación y separación de páginas se hace de forma imperativa con `c.showPage()`, asegurando que no se generen páginas adicionales por desbordamiento.

---

## Estructura del Patrón

### 1. Modelo de Reporte ReportLab
Se crea un modelo abstracto que encapsula el dibujo vectorial sobre el canvas de ReportLab:

```python
import io
import os
from odoo import models, api, modules
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

class MiReportePDF(models.AbstractModel):
    _name = 'report.mi_modulo.mi_reporte_pdf'
    _description = 'Generador de Reportes ReportLab'

    def _get_image_path(self, image_name):
        return modules.get_module_resource('mi_modulo', 'static/src/img', image_name)

    @api.model
    def generate_pdf(self, data):
        buffer = io.BytesIO()
        page_size = landscape(A4)  # O A4 simple
        page_width, page_height = page_size
        c = canvas.Canvas(buffer, pagesize=page_size)

        # PAGINA 1: Anverso
        # Fondo Full Bleed (si el tipo es digital, cargamos imagen)
        bg_path = self._get_image_path('background.jpg')
        if bg_path and os.path.exists(bg_path):
            c.drawImage(bg_path, 0, 0, width=page_width, height=page_height)

        # Dibujo de Textos
        c.setFont('Helvetica-Bold', 29)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(page_width / 2.0, page_height - 79 * mm, data.get('student_name', ''))

        # Textos con auto-wrap (Paragraph con estilos enriquecidos)
        style = ParagraphStyle('TextoLargo', fontName='Helvetica', fontSize=13, alignment=1)
        p = Paragraph("Texto con <b>negritas</b> y auto-wrap.", style)
        p.wrapOn(c, 257 * mm, 40 * mm)
        p.drawOn(c, 20 * mm, page_height - 106 * mm)

        # PAGINA 2: Reverso (Salto de página explícito)
        c.showPage()
        
        # Dibujo del reverso...
        # ...

        # Guardar y retornar
        c.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content
```

### 2. Flujo del Wizard / Emisor
El asistente invoca al modelo de ReportLab, guarda el PDF binario como un archivo adjunto (`ir.attachment`) asociado al registro correspondiente y devuelve una redirección directa para su descarga.

```python
import base64
from odoo import models, api

class MiWizard(models.TransientModel):
    _name = 'mi.wizard'

    def action_print(self):
        self.ensure_one()
        
        # 1. Preparar datos
        data = {
            'student_name': self.student_name,
            # ...
        }
        
        # 2. Generar el binario mediante ReportLab
        pdf_content = self.env['report.mi_modulo.mi_reporte_pdf'].generate_pdf(data)
        
        # 3. Guardar en adjuntos
        attachment = self.env['ir.attachment'].create({
            'name': f"Reporte_{self.student_name}.pdf",
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'mi.registro.historico',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        
        # 4. Retornar acción act_url para descarga directa (mismo comportamiento que diplomas normales)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
```

## Conclusiones / Buenas Prácticas
1. **Utilizar siempre `Paragraph` para textos largos:** Las funciones `drawString` o `drawCentredString` no soportan saltos de línea ni auto-wrap. Si el contenido dinámico puede ser largo, es obligatorio envolverlo en un `Paragraph`.
2. **Definir el tamaño de envoltura (`wrapOn`) antes de pintar (`drawOn`):** En ReportLab, un `Paragraph` requiere que se calcule su tamaño y área de dibujo llamando primero a `p.wrapOn(canvas, width, height)` antes de pintar sobre la coordenada con `p.drawOn(canvas, x, y)`.
3. **Mapear coordenadas y origen:** En ReportLab, el origen `(0,0)` del canvas está en la esquina inferior izquierda. Por consistencia de legibilidad de arriba-abajo, es una buena práctica restar las coordenadas verticales a la altura máxima (`page_height - Y * mm`).
