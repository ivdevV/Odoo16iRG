# Spec — específico HomeClass síncronas

## Excepción (autorizada; no crear un módulo nuevo)

Misma excepción ya usada para el nacional: el HomeClass síncronas se
añade **dentro de** `irg_practice_agreement_specific` (versión
16.0.1.2.0). Comparte wizard, doble firma e informe. No se tocan
`irg_practice_agreement_sign` ni `irg_practice_agreement_types`.

## Problema

El wizard solo ofrece Internacional y Nacional. Falta el **Convenio
Específico HomeClass Síncronas**, genérico a partir del PDF de ejemplo
(sin nombres de alumno, tutor ni centro).

## Solución

1. Radio del wizard: Internacional, Nacional, HomeClass Síncronas.
2. `agreement_type=especifico_homeclass_sincronas` usa el mismo flujo de
   doble firma.
3. QWeb HomeClass:
   - PRIMERA: fechas, horas, modalidad sincrónica online en tiempo real.
     Sin dirección física.
   - SEGUNDA: tutor + supervisión virtual sincrónica.
   - TERCERA: puntualidad en sesiones sincrónicas, plataforma, no grabar,
     confidencialidad digital.
   - CUARTA: tareas online + difusión del centro, talleres a usuarios y
     guías psicoeducativas (genéricas). Actividades propuestas solo si
     hay texto.
   - Sin QUINTA.
   - SEXTA: rescisión.
   - SÉPTIMA: no remuneradas; el centro puede cobrar a pacientes
     (gratuita / bonificada / estándar); el alumno no cobra.
   - Normativa con ley 26/2015 y Zoom.
4. Python y QWeb tratan el tipo como específico, no como marco.

## Criterios de aceptación

1. El wizard crea las tres variantes.
2. HTML HomeClass contiene modalidad sincrónica, no grabar, cobro a
   pacientes y ley 26/2015; no contiene QUINTA «a cargo de iRG»,
   «fuera de España», FUPPEMM, Luz Mary ni Área de Psicología.
3. HTML internacional sigue conteniendo «fuera de España».
4. Solo la firma del centro no completa un HomeClass; ambas sí.
5. Tests del módulo en verde.
