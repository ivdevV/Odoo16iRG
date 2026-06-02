# Micro-Spec: irg_welcome_diplomado_template_selector

## Objetivo

Crear un modulo nuevo en `addons-extra/extrairg/` para rutear los correos de bienvenida de admisiones de Diplomados a una plantilla editable especifica, sin modificar modulos existentes.

## Alcance

- Anadir `welcome_template_diplomado_id` a `auto.admission.required`.
- Mostrar la plantilla de Diplomados junto a las plantillas de bienvenida existentes.
- Heredar `op.admission.send_mail()` para conservar el comportamiento de `irg_sale_manual_confirmation_wizard` cuando `manual_wizard_enabled` esta activo.
- Detectar Diplomados cuando el codigo de lote empieza por `DI` o cuando la categoria del curso/producto empieza por `DI`.
- Resolver plantilla de Diplomados en este orden: configuracion, plantilla copiada del modulo, plantilla por defecto existente.
- Crear una copia editable de `isep_elearning_custom.email_op_admission_confirm` en `post_init_hook` con external id propio, sin sobrescribirla en actualizaciones, y asignarla en la configuracion si no hay plantilla de Diplomados definida.
- Anadir pruebas `TransactionCase` para helpers de deteccion y resolucion de plantilla.

## Fuera De Alcance

- No modificar `irg_elearning_correo_bienvenida_selector` ni `irg_sale_manual_confirmation_wizard`.
- No cambiar el formato de codigos de lote ni la logica del wizard de confirmacion.
- No sobrescribir plantillas editadas por usuarios.

## Validacion Esperada

- Carga del modulo en Odoo 16.
- Tests del modulo con `--test-enable`.
- Verificacion de que la plantilla copiada existe y es editable desde UI.
