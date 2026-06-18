# Changelog - 18 de Junio de 2026

## Proyecto: Sección de Talleres en el Campus Virtual (`irg-campus-workshops`)

Este registro de cambios detalla la creación e implementación del módulo personalizado para añadir una sección de talleres en el portal `/campus` y presentar la tarjeta con redirección y logotipo de "iRG Empower" en Odoo 16.

---

### [16.0.1.0.0] - 2026-06-18

### Añadido
- **Nuevo módulo `irg_campus_workshops`**: Creado para encapsular la adición de la sección "Talleres" en el portal de campus de forma aislada e independiente (siguiendo las reglas de no modificar directamente módulos base ni preexistentes).
- **Logotipo de iRG Empower**:
  - Incorporada la imagen oficial `irg_empower_logo.jpg` en los activos estáticos del módulo (`static/src/img/`).
- **Vista Heredada QWeb (`views/user_profile_content_workshops.xml`)**:
  - Extensión de la plantilla de diseño del portal `isep_website_custom_design.custom_user_profile_content_design`.
  - Inyección de la nueva sección **Talleres** con un título estilizado de cabecera (`h5`).
  - Tarjeta de enlace ("cuadrado") interactiva para **iRG Empower** con redirección segura a `https://app.institutoraimongaja.com/slides/irg-empower-261` en una pestaña nueva (`target="_blank"`).
- **Estilos CSS Modernos y Hover Micro-Animations**:
  - Definidos estilos locales (`.irg-workshop-card`) con transiciones fluidas de transformación y sombra (`box-shadow`) para proporcionar un efecto de elevación táctil e interactivo de alta calidad en dispositivos de escritorio.
  - Diseño responsivo compatible con dispositivos móviles, adaptándose a cuadrículas de 1 a 4 columnas.
- **Tests de Integración y Carga de Vistas (`tests/test_workshops.py`)**:
  - Suite de pruebas de Odoo que verifica la carga exitosa de la vista heredada.
  - Comprobación de que el XML final renderizado incluye el título "Talleres", el enlace de redirección a iRG Empower y la imagen del logotipo.

### Documentación
- Registro de la misión y el plan de ejecución en `missions/irg-campus-workshops/`.
- Persistencia de aprendizajes y guías de desarrollo web para herencias complejas en el portal en `.agents/knowledge/odoo_development_modding/artifacts/irg_course_elearning_featured_section.md` (o archivo temático de portal).
