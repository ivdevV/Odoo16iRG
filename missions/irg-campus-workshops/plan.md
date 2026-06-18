# Plan - Misión irg-campus-workshops

Implementación de un módulo personalizado de Odoo 16 para crear una sección de "Talleres" en el portal de `/campus` y añadir la tarjeta "iRG Empower" con redirección y el logo correspondiente.

## 1. Alcance y Descomposición
- **Módulo Odoo 16 personalizado**: `irg_campus_workshops` en `addons-extra/extrairg/`.
- **Estructura básica**: `__init__.py`, `__manifest__.py`, `views/user_profile_content_workshops.xml`.
- **Activos Estáticos**: Copiar la imagen del logo `media__1781776099101.jpg` a `irg_campus_workshops/static/src/img/irg_empower_logo.jpg`.
- **Plantilla QWeb**: Extender `isep_website_custom_design.custom_user_profile_content_design` usando xpath para inyectar la sección de "Talleres" con el card de iRG Empower.
- **Redirección**: Enlace hacia `https://app.institutoraimongaja.com/slides/irg-empower-261` con comportamiento responsivo y efectos visuales de alta calidad (hover scale, sombreado dinámico).
- **Pruebas**: Test de validación XML en `tests/test_workshops.py` para asegurar que el heredado sea válido y contenga la sección de talleres y la tarjeta.

## 2. Clasificación de Complejidad
- **Tier**: `standard`
- **Justificación**: Afecta a un solo módulo nuevo (creación de 4 archivos más la imagen), utiliza herencia básica de vistas web, no altera la base de datos ni afecta a seguridad, autenticación o concurrencia.
- **Modelos Asignados**:
  - **Plan**: Gemini 3.5 Flash (actual)
  - **Implementación (Codificador)**: Gemini 3.5 Flash (actual)
  - **Validación (Testeador)**: Gemini 3.5 Flash (actual)
  - **Documentación (Documentador)**: Gemini 3.5 Flash (actual)

## 3. Proposed Changes

### [Componente: irg_campus_workshops]
Nuevo módulo de Odoo en `addons-extra/extrairg/irg_campus_workshops`.

#### [NEW] [__init__.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_workshops/__init__.py)
Inicializador vacío del módulo.

#### [NEW] [__manifest__.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_workshops/__manifest__.py)
Manifiesto de Odoo con dependencias de diseño y rutas de vistas.

#### [NEW] [user_profile_content_workshops.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_workshops/views/user_profile_content_workshops.xml)
Vista heredada para añadir la sección "Talleres" y el card "iRG Empower" con estilos premium integrados.

#### [NEW] [irg_empower_logo.jpg](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_workshops/static/src/img/irg_empower_logo.jpg)
Imagen del logo copiada desde los recursos del chat.

#### [NEW] [__init__.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_workshops/tests/__init__.py)
Inicializador de tests.

#### [NEW] [test_workshops.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_campus_workshops/tests/test_workshops.py)
Tests automatizados para verificar la carga correcta de la vista heredada y la existencia del card.

## 4. Plan de Verificación

### Pruebas Automatizadas
- Ejecutar tests de Odoo para el módulo:
  `docker compose -f docker-compose.local.yml run --rm odoo odoo -c /etc/odoo/odoo.conf -i irg_campus_workshops --test-enable --stop-after-init`

### Verificación Manual
- Visualización de la sección en `/campus` una vez desplegado en el entorno local.
- Comprobación del redireccionamiento al hacer clic en el card de iRG Empower.
- Inspección de la visualización responsiva en dispositivos móviles.
