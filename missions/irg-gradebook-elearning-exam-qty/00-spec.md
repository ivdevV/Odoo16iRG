# Spec — irg-gradebook-elearning-exam-qty

Fuente canónica:
`docs/superpowers/specs/2026-09-18-irg-gradebook-elearning-exam-qty-design.md`

Módulo nuevo `irg_gradebook_elearning_exam_qty` que, en cada línea de libreta,
sustituye `exam.qty` por el recuento de exámenes del canal e-learning de **esa
asignatura** cuyo requisito de lote (`slide.allowed_batch_ids`) cumple el lote
de la libreta. No hay entero en `op.batch`. Una libreta puede exigir 3 en una
asignatura y 2 en otra.
