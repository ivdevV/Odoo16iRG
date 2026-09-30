# Changelog — irg-gradebook-elearning-exam-qty

## 16.0.1.0.0

- Nuevo módulo `irg_gradebook_elearning_exam_qty`.
- `exam.qty` de cada línea de libreta sale del recuento de exámenes publicados
  en el canal e-learning de esa asignatura, filtrado por
  `slide.allowed_batch_ids` y el lote de la libreta.
- No hay entero en `op.batch`. Una libreta puede exigir N distintos por
  asignatura.
- Libreta `done` no se recalcula. N = 0 deja el qty de la plantilla.
- No se editan `isep_gradebook` ni `irg_batch_slide_restrictions`.
