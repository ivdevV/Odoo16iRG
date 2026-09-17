# Spec — irg-practice-agreement-types (marcos)

## Problema

El practice center solo puede crear un **Convenio Marco Nacional** (módulo
`irg_practice_agreement_sign`). Hay que poder elegir tipo al crear, y añadir
el **Convenio Marco Internacional**, con el mismo flujo de firma y un texto
legal distinto. Los convenios específicos (nacional/internacional) van en la
solicitud del alumno y quedan fuera de esta entrega.

## Solución

Módulo nuevo `addons-extra/extrairg/irg_practice_agreement_types` (sin
modificar `irg_practice_agreement_sign`):

1. Botón **Crear Convenio** en el practice center abre un wizard de radio:
   Marco Nacional / Marco Internacional.
2. Campo `agreement_type` en `practice.agreement`. Los registros existentes
   y el `action_create_agreement` original se tratan como nacional.
3. PDF y portal reutilizan la cáscara nacional (logo, REUNIDOS, MANIFIESTAN,
   firmas). El cuerpo de cláusulas del internacional añade 4.3 seguros,
   vigencia/resolución ampliadas y confidencialidad + protección de datos
   separadas. No se incluye INMIRA ni datos de un centro concreto.
4. La plantilla QWeb nacional existente no se reescribe: se oculta cuando el
   tipo es internacional y se inserta el bloque nuevo.

## Criterios de aceptación

1. El botón del practice center se llama **Crear Convenio** y abre un wizard
   TransientModel con radio Nacional / Internacional.
2. Crear desde el wizard persiste `agreement_type` y abre el formulario del
   convenio.
3. Un convenio nacional (incluido uno creado por el método original) genera
   PDF/portal **sin** la cláusula 4.3 de seguros LATAM.
4. Un convenio internacional genera PDF/portal **con** 4.3 (RC iRG solo en
   España; resto a cargo del estudiante) y **sin** la palabra INMIRA.
5. Email, token, canvas de firma y adjunto al centro siguen el módulo base.
6. Suite de tests del módulo en verde.

## Fuera de alcance

- Convenio Específico Nacional e Internacional.
- Botón o wizard en solicitudes de alumno.
- Reescritura de la plantilla nacional.
- Texto de intermediario / centro de prácticas distinto del firmante.
