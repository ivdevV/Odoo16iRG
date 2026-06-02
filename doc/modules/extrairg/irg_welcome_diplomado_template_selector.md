# irg_welcome_diplomado_template_selector

**Categoria:** Education
**Version:** 16.0.1.0.1
**Licencia:** LGPL-3
**Instalable:** Si
**Autor:** Instituto Raimon Gaja
**Depende de:** `irg_sale_manual_confirmation_wizard`

## Que Hace

Anade un ruteo especifico para correos de bienvenida de Diplomados sin modificar los modulos existentes de bienvenida ni de confirmacion manual.

Cuando `manual_wizard_enabled` esta activo en `auto.admission.required`, las admisiones cuyo lote empieza por `DI` o cuyo curso/producto pertenece a una categoria con codigo `DI*` usan una plantilla de bienvenida propia para Diplomados.

## Configuracion

El modulo anade el campo `Plantilla bienvenida Diplomados` en el formulario de `auto.admission.required`, junto a las plantillas Online y por defecto.

La plantilla se resuelve en este orden:

1. `welcome_template_diplomado_id` configurada en UI.
2. Copia editable creada por el modulo con XML ID `irg_welcome_diplomado_template_selector.email_op_admission_confirm_diplomado`.
3. Plantilla por defecto `isep_elearning_custom.email_op_admission_confirm`.

## Plantilla Copiada

En la instalacion o actualizacion del modulo, `action_irg_ensure_diplomado_welcome_template()` copia `isep_elearning_custom.email_op_admission_confirm` y crea una plantilla llamada `Bienvenida admision Diplomados`.

Si `welcome_template_diplomado_id` esta vacio, el hook asigna automaticamente esa copia a la configuracion global para que sea visible y editable desde la interfaz.

La copia no se sobrescribe en actualizaciones si ya existe su external id, por lo que los cambios hechos desde la UI se conservan.

## Modelos Modificados

| Modelo | Tipo | Cambios |
| --- | --- | --- |
| `auto.admission.required` | Herencia | Campo `welcome_template_diplomado_id` |
| `op.admission` | Herencia | Helpers de deteccion DI, resolucion de plantilla y override de `send_mail()` |

## Pruebas

Incluye `TransactionCase` en `tests/test_welcome_diplomado_template_selector.py` para validar:

1. Deteccion por codigo de lote que empieza por `DI`.
2. Deteccion por categoria con codigo `DI*`.
3. Prioridad de la plantilla configurada en UI.
4. Fallback a la plantilla copiada o a la plantilla por defecto.

## Changelog

- 16.0.1.0.1: Asegura la creacion/asignacion de la plantilla de Diplomados tambien en actualizaciones del modulo.
- 16.0.1.0.0: Modulo inicial para ruteo de plantilla de bienvenida de Diplomados, con copia editable de la plantilla por defecto y asignacion automatica en configuracion si esta vacia.
