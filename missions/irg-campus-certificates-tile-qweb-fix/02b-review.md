# Review de código — irg-campus-certificates-tile-qweb-fix

Fecha: 2026-09-04
Revisor: agente `reviewer` (distinto del codificador)
Alcance: **solo código funcional** del módulo nuevo `irg_campus_certificates_tile_qweb_fix`.
No se han revisado `plan.md`, `01-plan.md`, `execution.md`, `verification.json`, changelog ni knowledge.
No se ha editado ningún archivo de código.

## Archivos revisados

| Archivo | Estado |
| --- | --- |
| `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/__manifest__.py` | revisado |
| `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/__init__.py` | revisado |
| `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/views/campus_dashboard_override.xml` | revisado |
| `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/tests/__init__.py` | revisado |
| `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/tests/test_qweb_guard.py` | revisado |

Contexto de solo lectura consultado: `irg_campus_certificates_portal/views/campus_dashboard_override.xml`,
`irg_course_portal_tiles_diplomado_hide/{models/op_course.py,views,__manifest__.py}`,
`irg_diplomado_portal_request/models/op_course.py`,
`irg_course_portal_tiles/views/irg_course_portal_tiles_views.xml`.

## Verificación de los criterios de la spec

1. **El `t-if` combinado no usa `hasattr`.** Cumple. El xpath
   `//div[@name='certificates_and_diplomas']` con `position="attributes"` reemplaza por completo el
   atributo `t-if`; no lo compone ni lo concatena con el original, de modo que `hasattr` desaparece de
   la arquitectura combinada.
2. **Usa `course_id.is_diplomado()`.** Cumple. El valor nuevo es exactamente
   `not course_id.is_diplomado()`.
3. **Renderizar la expresión con `ir.qweb` no lanza `TypeError`.** Cumple por construcción:
   `is_diplomado()` es un método de `op.course` invocado sobre un recordset, patrón que `safe_eval`
   sí admite, y no queda ninguna llamada a builtins ausentes. La comprobación empírica corresponde al
   validador.
4. **Máster muestra el tile; diplomado (`DI…`) lo oculta.** Cumple.
   `is_diplomado()` (en `irg_course_portal_tiles_diplomado_hide`) devuelve `True` cuando `code`
   empieza por `DI` (case-insensitive), y `False` para un curso sin `course_type_id` ni productos con
   marcas de diplomado.
5. **No se edita `irg_campus_certificates_portal`.** Cumple. `git status` muestra únicamente
   `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/` como directorio no rastreado; el
   módulo original conserva intacto su `t-if` con `hasattr`. La regla de oro (arreglar por herencia,
   no editar módulos existentes) se respeta.

## Arquitectura

Correcta y alineada con las convenciones del repositorio.

- **Punto de herencia.** Heredar de `irg_campus_certificates_portal.user_profile_content_details_certificates_tile`
  (una vista de extensión, no la raíz) es la elección adecuada: garantiza por relación padre-hijo que
  el spec del fix se aplique **después** de que el padre haya insertado el `<div>`, y ata el arreglo al
  módulo defectuoso mediante la dependencia. El repositorio ya usa este mecanismo con éxito en
  `irg_profile_batch_fix` y `irg_online_subject_opening`, que heredan vistas de extensión y hacen xpath
  sobre la arquitectura combinada.
- **Unicidad del xpath.** `certificates_and_diplomas` es un nombre único en todo `addons-extra`; el tile
  hermano de `irg_diplomado_portal_request` se llama `diplomado_diploma_request`, así que no hay colisión.
  Si el nodo dejara de existir, la instalación fallaría de forma ruidosa, que es el comportamiento deseado.
- **Equivalencia semántica.** `is_diplomado()` e `irg_is_diplomado()` implementan exactamente la misma
  lógica (código `DI`, `course_type_id`, nombres y categorías de `product_template_id`/`_ids`). El cambio
  preserva el comportamiento pretendido por el módulo original sin desviación funcional.
- **Eliminación del guard defensivo.** El `hasattr` existía porque `irg_is_diplomado()` solo está
  disponible si `irg_diplomado_portal_request` está instalado. Al depender explícitamente de
  `irg_course_portal_tiles_diplomado_hide`, el método está siempre garantizado y el guard sobra: la
  dependencia dura sustituye correctamente a una comprobación en runtime. Buena decisión.
- **Coherencia con las tiles hermanas.** `irg_course_portal_tiles_diplomado_hide` ya aplica
  `not course_id.is_diplomado()` a las tiles de Prácticas y TFM en la misma `<div class="row">`. El fix
  unifica el criterio en lugar de introducir un tercer mecanismo.
- **Dependencias.** Mínimas y ambas necesarias: una aporta la vista a heredar y la otra el método.
  No se arrastra `irg_diplomado_portal_request`, que ya no hace falta. Correcto.

## Hallazgos

### BLOQUEANTE

Ninguno.

### MENOR

1. **`auto_install: True` no aplica el arreglo si falta una dependencia.**
   `addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/__manifest__.py`
   `auto_install` solo dispara cuando **todas** las dependencias ya están instaladas. Si en beta
   `irg_course_portal_tiles_diplomado_hide` no estuviera instalado, el módulo no entraría y
   `/campus/course/<id>` seguiría en 500 sin ninguna señal de error. El riesgo es bajo, porque
   `irg_campus_workshops` e `irg_campus_diplomados_portal` ya dependen de ese módulo, pero es una
   suposición que conviene confirmar y no inferir.
   *Corrección:* el validador debe verificar en el runtime local (y quien despliegue, en beta) que
   `irg_course_portal_tiles_diplomado_hide` figura como `installed` antes de dar por aplicado el fix; si
   no lo estuviera, instalar el módulo del fix explícitamente en vez de confiar en `auto_install`.
   Es además el único módulo de `extrairg` con `auto_install: True`, así que la desviación merece quedar
   registrada aunque la spec la justifique.

2. **El test interpola el `t-if` en XML sin escapar.**
   `tests/test_qweb_guard.py`, `_render_guard` (líneas 25-36)
   `'<span t-if="%s">shown</span>' % t_if` rompería con `XMLSyntaxError` si un override futuro
   introdujera `"`, `<` o `&` en la expresión, y el fallo sería opaco en lugar de informativo.
   *Corrección:* construir el nodo con `lxml` y `set('t-if', t_if)`, o envolver con
   `xml.sax.saxutils.quoteattr`.

3. **La vista no documenta la causa del arreglo.**
   `views/campus_dashboard_override.xml`
   Sin un comentario, el siguiente lector no sabe por qué existe este módulo y podría "simplificarlo"
   reintroduciendo `hasattr`. Otros módulos-parche del repositorio (`irg_profile_batch_fix`,
   `irg_op_subject_visibility`, `irg_subject_slide_fix`) sí llevan una cabecera explicativa.
   *Corrección:* añadir un comentario XML de una o dos líneas indicando que `hasattr` no está en
   `_BUILTINS` de `safe_eval` en Odoo 16 y que por eso se sustituye por `is_diplomado()`.

### NIT

4. **`priority="99"` no tiene efecto hoy.** `views/campus_dashboard_override.xml`. La vista es la única
   hija de su padre, así que la prioridad no ordena nada. Es defensiva y del todo inocua; si se conserva,
   basta una nota que explique la intención.

5. **`'lang': self.env.user.lang or 'en_US'` es irrelevante para el caso probado.**
   `tests/test_qweb_guard.py`, líneas 48 y 58. El campo existe en `op.course` (lo usan otros tests del
   repositorio), pero `is_diplomado()` no lo consulta, así que solo añade ruido al fixture.

6. **Falta el atributo `name` en la plantilla.** `views/campus_dashboard_override.xml`. Odoo lo deriva
   del `id`; es únicamente cuestión de legibilidad en la lista de vistas.

7. **Riesgo preexistente, no introducido aquí:** `is_diplomado()` llama a `ensure_one()`, de modo que un
   `course_id` vacío provocaría un `ValueError`. No es una regresión: las tiles de Prácticas y TFM del
   mismo bloque ya evalúan idéntica expresión, y `course_id` es siempre un curso único en el ámbito de
   `/campus/course/<id>`. Se deja constancia, sin acción requerida.

## Calidad y antipatrones

- Sin duplicación de lógica: el fix no reimplementa la detección de diplomado, reutiliza el método
  existente.
- Sin código muerto: `__init__.py` está vacío porque el módulo no aporta Python, y `tests/` no se declara
  en `data`, que es lo correcto (Odoo importa `<módulo>.tests` de forma autónoma).
- Manifiesto completo y coherente con el del módulo padre: `version`, `license`, `author`, `category`,
  `summary`, `installable`, `application`.
- Sin `t-raw`, sin f-strings en QWeb, sin `sudo()` innecesarios, sin lógica en la vista más allá de la
  condición.

## Tests

Los tests son proporcionados y atacan el punto correcto.

- `_certificates_tile_t_if` valida sobre `get_combined_arch()` de la raíz real
  (`isep_website_custom.user_profile_content_details`), que es la integración que de verdad importa; un
  test contra `arch_db` del módulo no habría detectado un fallo de aplicación del xpath. Acertado.
- Se asegura la unicidad del nodo antes de leer el `t-if`, evitando falsos positivos si otro módulo
  duplicara el tile.
- `test_combined_t_if_does_not_use_hasattr` cubre los criterios 1 y 2.
- Los dos tests de render pasan por `ir.qweb._render` de verdad, así que un `TypeError` de `safe_eval`
  haría fallar la prueba: cubren el criterio 3.
- Los fixtures son deterministas para el criterio 4: `MTQG01` no activa ninguna rama de `is_diplomado()`
  y `DIQG01` activa la del prefijo `DI`.
- `@tagged('post_install', '-at_install')` es la elección correcta, ya que la arquitectura combinada solo
  está completa tras instalar todos los módulos.
- Limitación aceptada: se prueba la expresión extraída, no la página completa. Es un compromiso razonable
  y la cobertura de la página renderizada queda en el gate E2E declarado para esta misión.

## Seguridad

Sin observaciones. El cambio es exclusivamente declarativo sobre una plantilla QWeb: no añade
controladores, rutas, campos, ACLs ni reglas de registro; no introduce `sudo()`, entradas de usuario,
consultas construidas por concatenación ni secretos; no toca autenticación, concurrencia, migraciones ni
borrado de datos. `is_diplomado()` es de solo lectura. No procede activar al Security Advisor.

Se deja constancia de que ocultar un tile es una decisión de presentación y no un control de acceso; el
control de la ruta `/campus/certificates` vive en el controlador de `irg_campus_certificates_portal`, que
no se modifica y queda fuera de este alcance. El fix preserva exactamente el comportamiento pretendido,
por lo que no hay regresión de seguridad.

## Zonas sensibles

No se detecta ningún `PROJECT.md` en la raíz del repositorio; se ha aplicado como política vigente
`AGENTS.md`. Sus restricciones relevantes se cumplen: no se edita ningún módulo existente, el arreglo se
entrega como módulo `irg_` nuevo por herencia y no se toca configuración de despliegue, credenciales ni
`docker-compose*.yml`.

## Conclusión

No hay observaciones bloqueantes abiertas. Los cinco criterios de la spec se cumplen, la arquitectura es
la correcta para el problema y el alcance es exactamente el necesario. Las tres observaciones MENOR son
mejoras de robustez y despliegue que no impiden avanzar; la número 1 debe quedar cubierta como
comprobación explícita durante la Validación.

REVIEW PASS
