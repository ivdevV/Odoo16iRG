# IRG Diploma Gradebook Presential Detection

## Propósito y causa confirmada

`irg_diploma_gradebook_presential_detection` corrige la identificación del
módulo presencial que participa en la ponderación global 50/50 de los
Diplomados.

El log de beta confirmó que el motor autoritativo y la plantilla correcta sí
estaban activos, pero la libreta 719 conservaba el promedio simple porque la
guarda estructural encontraba cero candidatos:

```text
Authoritative Diploma 50/50 skipped for gradebook 719:
found 0 presential subject candidates.
```

La causa estaba en el detector heredado. Este elegía
`op_subject_id.name or line.name`, de modo que, si el nombre interno de
`op.subject` existía, nunca comprobaba el nombre almacenado y visible de la
línea `app.gradebook.subject`. Además, su expresión regular exigía que
`Modulo presencial` estuviera prácticamente al final del texto. Por eso una
línea visible como `AD003983 - Modulo presencial` podía no reconocerse si el
nombre interno era distinto, y tampoco se aceptaban sufijos descriptivos como
`- Certificacion` o `- Convocatoria 2`.

Al no existir exactamente un candidato, el cálculo 50/50 actuaba de forma
segura: registraba la advertencia, devolvía `False` y conservaba la media
heredada `9,78`.

## Arquitectura

Es un addon puente de herencia. No modifica addons existentes, no crea modelos,
campos, vistas, ACL ni datos. Extiende `app.gradebook.student` y sobrescribe
únicamente `_is_presential_module_subject()`.

El detector nuevo:

1. obtiene por separado `gradebook_subject.op_subject_id.name` y
   `gradebook_subject.name`;
2. normaliza ambos textos mediante el helper heredado `_normalize_text()`, por
   lo que ignora mayúsculas, tildes y espacios redundantes;
3. busca la frase completa `modulo presencial` en cualquiera de los dos
   nombres; y
4. usa límites de palabra para no confundirla con textos como
   `Modulo presencialidad`, `Supermodulo presencial` o
   `Modulo semi presencial`.

Se conserva sin cambios el contrato autoritativo: la fórmula especial solo se
aplica cuando la plantilla tiene `final_calculation_mode = diploma_50_50`, hay
exactamente un presencial obligatorio y existe al menos un módulo ordinario
obligatorio no exento. Dos candidatos siguen produciendo el fallback seguro.

## Dependencia

El manifest depende directamente de:

- `irg_diploma_gradebook_template_authoritative`.

Esto garantiza que el override del detector se cargue después del motor que
aplica el 50/50. La dependencia incorpora transitivamente la plantilla, la
compatibilidad NLEX/EX y los demás addons puente de esta funcionalidad. No se
deben desinstalar mientras este addon esté instalado.

## Instalación y uso en beta

1. Desplegar el código del addon en el servidor beta y reiniciar todos los
   procesos/workers de Odoo para que Python cargue la nueva clase.
2. Actualizar la lista de aplicaciones en modo desarrollador.
3. Quitar el filtro `Aplicaciones` si oculta addons técnicos.
4. Buscar e instalar `IRG Diploma Gradebook Presential Detection`.
5. Confirmar que la libreta usa
   `Diplomado - Solo examen - Ponderación 50/50`.
6. Para una libreta histórica que ya tenía esa plantilla, seleccionar una
   plantilla estándar, guardar, volver a seleccionar la plantilla 50/50 y
   guardar. Esto fuerza la invalidación y el recálculo de `total_final` y
   `avg_score`.

No es necesario renombrar la asignatura ni modificar datos de beta. Después de
la instalación, el log ya no debe mostrar `found 0 presential subject
candidates` para una libreta con una única línea cuyo nombre interno o visible
contenga la frase completa `Módulo presencial`.

## Resultado esperado

Para el caso diagnosticado:

```text
presencial = 8,44
ordinarios = 10, 10, 10, 10, 10, 10
resultado  = 8,44 * 0,50 + 10 * 0,50 = 9,22
```

El valor `9,78` es la media simple heredada de las siete notas y solo debe
permanecer si las guardas estructurales impiden aplicar el modo especial.

## Pruebas y evidencia

La validación se ejecutó con `docker-compose.local.yml` en la base aislada
`test_irg_diploma_presential_detection_20260716`, creada a partir de
`test_irg_diploma_authoritative_v2_20260715`. Odoo cargó 232 módulos e instaló
el addon como versión `16.0.1.0.0`.

Las cinco pruebas `TransactionCase` post-install comprobaron:

- detección con prefijos y sufijos alrededor de `Módulo presencial`;
- uso de `app.gradebook.subject.name` cuando `op.subject.name` es distinto;
- resultado `9,22` para seis notas `10` y presencial `8,44` tanto en
  `total_final` como en `avg_score`;
- rechazo de frases parciales; y
- fallback seguro cuando existen dos candidatos presenciales.

Resultado: 5 pruebas superadas, 0 fallos y 0 errores; 638 consultas en 0,69
segundos. También pasaron `compileall`, parseo del manifest, cadena de imports,
dependencia declarada, `git diff --check` y revisión de espacios. El proceso
Odoo finalizó con código 0 y `verification.json` quedó en estado `passed`.

## Limitaciones conocidas

- Este addon solo mejora la detección del módulo presencial; no cambia la
  fórmula, los pesos ni el funcionamiento de plantillas estándar.
- Requiere que el nombre interno o el visible contenga la frase completa
  `Módulo presencial`. No infiere el tipo a partir de códigos u otros campos.
- El modo especial exige exactamente un presencial obligatorio. Cero o dos o
  más candidatos conservan deliberadamente el cálculo heredado.
- No realiza migraciones ni recálculos masivos. Una libreta histórica puede
  requerir volver a guardar `gradebook_id` después de instalar el addon.
- Si se renombra únicamente el texto almacenado de la línea, el grafo de
  dependencias previo puede no invalidar los campos finales; cambiar y guardar
  la plantilla fuerza el recálculo.
- Depende de los contratos internos `_normalize_text()`,
  `_is_presential_module_subject()` y `_get_diploma_weighting_values()` de la
  cadena de addons de ponderación.

## Changelog

### 16.0.1.0.0 — 2026-07-16

- Corregida la causa de `found 0 presential subject candidates` observada en
  beta.
- Añadida comprobación independiente del nombre interno y el nombre visible de
  cada línea.
- Permitidos prefijos y sufijos conservando límites de palabra estrictos.
- Preservadas las guardas estructurales, exenciones NLEX/EX y el fallback
  seguro.
- Añadidas cinco pruebas de regresión e integración.
