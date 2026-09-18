# irg_gradebook_elearning_exam_qty

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí (instalación explícita; `auto_install` False)
**Autor:** iRG
**Depende de:** `isep_gradebook`, `irg_batch_slide_restrictions`

---

## ¿Qué hace este módulo?

Sustituye la cantidad de exámenes exigida en cada línea de libreta
(`exam.qty`) por el recuento de exámenes publicados en el canal e-learning de
**esa asignatura** cuyo requisito de lote (`slide.allowed_batch_ids`) cumple el
lote de la libreta.

No hay un entero en `op.batch`. Una misma libreta puede exigir 3 exámenes en
una asignatura y 2 en otra. El texto `AVG Exámenes => [n de N]` y el cierre
`state_to_done` usan ese N.

## Funcionalidades principales

- Hereda `app.gradebook.subject` y redefine `_get_gradebook_info`.
- Llama a `super()` (pesos y qty de plantilla).
- Si la libreta no está `done` y N > 0, escribe `gradebook['exam']['qty'] = N`.
- N = surveys únicos tipo `exam`, slides publicados, no secciones.
- `allowed_batch_ids` vacío: cuenta para todos los lotes.
- `allowed_batch_ids` con valores: cuenta solo si
  `gradebook_student_id.batch_id` está en la lista.
- No filtra por `scheduled_date`.
- N = 0 (sin canal o sin exámenes Odoo): deja el qty de la plantilla.
- Libreta `done`: no sustituye.

## Modelos

| Modelo | Tipo | Campos / comportamiento |
|--------|------|-------------------------|
| `app.gradebook.subject` | Herencia | `_irg_slide_allows_gradebook_batch`, `_irg_elearning_exam_qty`, override `_get_gradebook_info` |

No crea modelos nuevos ni vistas.

## Tests

`tests/test_elearning_exam_qty.py`, etiquetados `post_install` y `-at_install`.

- Un examen sin requisito de lote → N=1.
- Misma libreta: 3 y 2 por asignatura.
- Examen restringido a lote nuevo: el lote viejo sigue en 1.
- `scheduled_date` futura sigue contando.
- No publicado, assignment o `survey_id` duplicado no inflan N.
- Sin canal: qty de plantilla.
- Cierre exige el N detectado.
- Libreta `done` no sustituye tras un examen nuevo.

## Limitaciones

- Hay que instalar el módulo en cada entorno; no se autoinstala.
- Al publicar un examen extra en un canal compartido, hay que rellenar
  `allowed_batch_ids` con los lotes nuevos. Si queda vacío, las libretas
  `in_progress` antiguas pasarían a exigirlo.
- Moodle/HomeClass sin slides de examen Odoo: fallback a la plantilla. El
  wizard Moodle (`qty == 1`) no se cambia.
- `info_exam` es computed stored: el cierre lee N en vivo; el texto `[n de N]`
  se refresca al recomputar promedios.
- No usar `is_user_allowed_by_batch` para este recuento (usuario ORM ≠ alumno).

## Instalación / Actualización

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d <dbname> \
  -i irg_gradebook_elearning_exam_qty \
  --stop-after-init --http-port=8099
```
