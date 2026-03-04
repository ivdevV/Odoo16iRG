# 2026-03-04 — IRG eLearning Styles Rework

## 1) Título corto
Rework visual moderno para páginas de eLearning

## 2) Resumen objetivo
Aplicar una mejora visual de alto impacto en las páginas de curso de eLearning (cabecera, breadcrumb, sidebar y listado de contenidos) mediante herencia QWeb y estilos frontend, sin modificar módulos base o existentes.

## 3) Motivo / justificación
La interfaz actual funciona correctamente, pero necesita una estética más moderna y atractiva para mejorar la percepción de calidad y la experiencia de navegación del estudiante.

## 4) Alcance exacto
- Módulo nuevo: `irg_elearning_styles_rework`.
- Ubicación: `addons-extra/extrairg/`.
- Herencias QWeb sobre:
  - `website_slides.course_nav`
  - `website_slides.course_sidebar`
  - `openeducat_lms.course_detail`
- Estilos SCSS en `web.assets_frontend` enfocados a curso eLearning.
- Sin cambios en modelos Python ni lógica de negocio.

## 5) Diseño técnico
- Añadir clases de enganche (`irg-elearning-*`, `irg-lms-*`) vía `xpath` para aplicar estilos con bajo acoplamiento.
- SCSS basado en variables de tema/Bootstrap de Odoo (`$primary`, `$border-color`, `$white`, `$black`, etc.).
- Mantener responsividad en breakpoints principales.

## 6) Dependencias
- `website_slides`
- `website`
- `openeducat_lms`
- `openeducat_lms_website`

## 7) Backwards-compatibility / migración
Compatible con Odoo 16. No requiere migración de datos ni scripts de upgrade.

## 8) Casos de prueba / criterios de aceptación
1. Al instalar el módulo, el curso eLearning muestra cabecera más moderna (gradiente y mejor contraste).
2. El breadcrumb aparece con estilo tipo cápsula.
3. El sidebar de curso se visualiza como tarjeta moderna.
4. El listado de secciones/contenidos presenta estilo de cards con hover y estado activo.
5. No se altera la funcionalidad de navegación, inscripción o progreso.

## 9) Rollback plan
- Desinstalar `irg_elearning_styles_rework` o revertir commit.
- Actualizar assets para limpiar caché de frontend.

## 10) Estimación y responsable
Estimación: 2–4 horas (implementación + validación visual).
Responsable: Equipo iRG / Copilot.
