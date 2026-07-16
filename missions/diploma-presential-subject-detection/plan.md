# Plan: detección robusta del módulo presencial

## Objetivo

Corregir el fallback 9,78 confirmado por el log de beta cuando el motor 50/50
informa `found 0 presential subject candidates` para la libreta 719.

## Evidencia

- El addon autoritativo está instalado y ejecutándose.
- El template tiene `final_calculation_mode = diploma_50_50`.
- El log confirma que la única guarda que falla es la identificación del
  módulo presencial.
- La vista muestra `AD003983 - Modulo presencial`, pero el helper actual usa
  `op_subject_id.name or line.name`; si el primer valor existe, nunca contrasta
  el nombre visible almacenado.
- El patrón heredado también exige una posición final demasiado estricta.

## Alcance

1. Crear un addon puente nuevo bajo `addons-extra/extrairg/`, sin modificar
   addons existentes.
2. Depender de `irg_diploma_gradebook_template_authoritative` para cargarse al
   final de la cadena.
3. Sobrescribir únicamente `_is_presential_module_subject()`.
4. Normalizar y comprobar por separado `op_subject_id.name` y `line.name`.
5. Reconocer la frase completa `modulo presencial` con límites de palabra,
   independientemente de prefijos/sufijos descriptivos.
6. Conservar la regla de exactamente un presencial y todas las demás guardas
   del cálculo autoritativo.

## Fuera de alcance

- Cambiar pesos, notas o templates estándar.
- Migrar o renombrar asignaturas existentes.
- Modificar datos de beta.
- Commit o push sin autorización explícita posterior.

## Complejidad y routing

- **Tier:** `complex`.
- **Justificación:** addon nuevo con más de cinco archivos y compatibilidad
  cross-module, aunque la lógica sea pequeña y localizada.
- **Implementación:** subagente codificador.
- **Validación:** subagente independiente con Docker local y
  `verification.json` obligatorio.
- **Documentación:** subagente después de validación `passed`.
- **Security Advisor:** no aplica.

## Criterios de aceptación

- Variantes con prefijo o sufijo alrededor de `Módulo presencial` se detectan.
- Si el nombre interno no coincide pero `line.name` visible sí, se detecta.
- Seis notas 10 y presencial 8,44 producen 9,22.
- Textos que no contienen la frase completa no se detectan.
- Dos candidatos continúan provocando fallback seguro.

## Conocimiento aplicado

- El log de beta sustituye la hipótesis por evidencia: el motor sí corre y la
  guarda de candidatos presenciales devuelve cero.
- Los campos computados almacenados pueden mostrar un texto histórico distinto
  del Many2one actual si sus dependencias no incluyen subcampos relacionados.
