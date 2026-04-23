# irg_interactive_content

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `website_slides`, `website`, `web`

---

## ¿Qué hace este módulo?

Extiende las diapositivas de eLearning (`slide.slide`) para soportar contenido interactivo generado por IA. Permite mostrar diagramas Mermaid, flashcards, contenido HTML interactivo y quizzes de opción múltiple directamente en las diapositivas del curso.

Dependencias externas Python: `requests` (para llamadas a la API de IA).

## Funcionalidades principales

- Nuevo tipo de contenido "interactivo" en las slides.
- Soporte para diagramas Mermaid (flowcharts, secuencias, etc.).
- Flashcards con frente/reverso para repaso.
- Quizzes de opción múltiple integrados en el contenido.
- Cargador JavaScript asíncrono para el contenido interactivo.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `slide.slide` | Herencia | Tipo interactivo, datos de contenido |

## Vistas y UI

- `views/slide_view.xml` — tipo de slide interactivo en el backend.
- JS: `static/src/js/interactive_loader.js`.
- CSS: `static/src/css/interactive_content.css`.

## Notas técnicas

- Requiere `security/ir.model.access.csv`.
- Dependencia Python `requests` debe estar instalada en el contenedor.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_interactive_content \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_interactive_content \
    --stop-after-init --db_host=pgodoo_latest
```
