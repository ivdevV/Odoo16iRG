# Spec — irg-practice-agreement-specific (internacional)

## Problema

En la solicitud de prácticas del alumno hay que crear un **convenio
específico** (anexo al marco) con el centro asignado. Hay dos tipos;
esta entrega implementa solo el **Específico Internacional**.

## Solución

Módulo nuevo `addons-extra/extrairg/irg_practice_agreement_specific`
(depende de `irg_practice_agreement_types`; no modifica módulos previos):

1. Botón **Crear Convenio** en `practice.request` abre un wizard de radio.
   En esta entrega la única opción es Específico Internacional.
2. Reutiliza `practice.agreement` con `agreement_type=especifico_internacional`,
   `practice_request_id` y una copia de alumno, máster, documento, fechas,
   días/horario, horas, tutor y dirección del centro asignado.
3. Firma triple: iRG precargada; dos enlaces públicos (email alumno y email
   centro). `completed` solo cuando existen ambas firmas.
4. PDF/portal con cláusulas del ejemplo (genéricas, sin INMIRA). QUINTA:
   RC de iRG solo en España. Anexo I de normativa. Tres columnas de firma.
5. Campo opcional `student_proposed_activities`; si está vacío, no se pinta
   ese bloque.

## Flujo

Solicitud (centro asignado) → wizard → borrador → Enviar por email
(dos correos) → cada parte firma su enlace → PDF adjunto al convenio,
a la solicitud y al centro.

## Criterios de aceptación

1. El formulario de `practice.request` tiene **Crear Convenio** y abre el wizard.
2. El wizard exige centro asignado y crea un específico internacional con
   datos copiados de la solicitud.
3. El HTML/PDF contiene «fuera de España» / seguros y **no** contiene INMIRA.
4. Solo la firma del centro no completa el convenio; ambas sí.
5. URLs de alumno y centro son distintas.
6. Tests del módulo en verde.

## Fuera de alcance

- Específico nacional (cuando llegue el ejemplo).
- Tercer lugar de prácticas distinto del centro asignado.
- Odoo Sign / `email_specific_agreement` legado.
