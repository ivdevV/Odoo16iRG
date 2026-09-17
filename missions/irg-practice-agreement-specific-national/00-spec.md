# Spec — específico nacional en irg_practice_agreement_specific

## Excepción (autorizada; no crear un módulo nuevo)

La regla de oro del desarrollo iRG es **no editar módulos existentes** y
añadir funcionalidad con un módulo nuevo por herencia.

Esta misión es una **excepción explícita, acotada y de un solo uso**,
autorizada por el usuario: el Convenio Específico Nacional se añade
**dentro de** `irg_practice_agreement_specific` (versión 16.0.1.1.0).
Motivo: no tiene sentido un módulo nuevo solo para una variante del
mismo wizard, la misma doble firma y el mismo informe PDF.

Esta excepción **no** autoriza tocar `irg_practice_agreement_sign`,
`irg_practice_agreement_types` ni ningún otro módulo. No sienta
precedente para futuras features.

## Problema

El wizard de la solicitud solo ofrece Específico Internacional. Falta el
**Específico Nacional**, con plantilla genérica del ejemplo (sin nombres
de centro/alumno) y seguros a cargo de iRG.

## Solución

En el mismo módulo:

1. Radio del wizard: Internacional y Nacional.
2. `agreement_type=especifico_nacional` usa el mismo flujo de doble firma.
3. QWeb nacional: QUINTA = RC, accidentes y asistencia sanitaria a cargo
   de iRG (sin «fuera de España»). Normativa con ley 26/2015.
4. Python y QWeb tratan `especifico_nacional` como específico (doble firma
   + plantilla nacional), no como marco.

## Criterios de aceptación

1. El wizard permite crear nacional e internacional.
2. HTML nacional contiene seguros a cargo de iRG y ley 26/2015; no
   contiene «fuera de España», Encuentro ni Miroslava.
3. HTML internacional sigue conteniendo «fuera de España».
4. Solo la firma del centro no completa un nacional; ambas sí.
5. Tests del módulo en verde.
