# Ejecución: irg-moroso-banner

## 2026-10-19 — Plan

- Spec aceptada: `docs/superpowers/specs/2026-10-19-irg-moroso-banner-design.md`.
- Jev de la petición original: clase efectiva `full`, sin Security Advisor.
- Tier `complex`. Capacidad: la de esta sesión.
- El checkout principal es el que monta `docker-compose.local.yml` en `/mnt/extra-addons`. No se abre worktree.
- Publicación no autorizada.

## Registro de fases

### 2026-10-19 — Implementación/TDD

- RED en `test_irg_moroso_banner` con el módulo instalable y sin la regla: 1 fallo y 13 errores. El fallo es la cinta ausente; los errores son `irg_is_moroso` y `_irg_recompute_moroso` inexistentes. Evidencia: `artifacts/tdd-red.txt`.
- GREEN: `-u irg_moroso_banner --test-enable --test-tags /irg_moroso_banner`. Resultado: 0 failed, 0 errors of 14 tests. Evidencia: `artifacts/tdd-green.txt`.
- El borrado de una factura publicada pasa antes por SQL a borrador porque Odoo no deja borrar apuntes de un asiento publicado. El gancho de `unlink` es el que quita el marcador.
- No se instala el módulo en la base que sirve el puerto 8069: el `post_init_hook` clasificaría contactos reales.
- Review bloqueó el pago: `payment_state` no pasa por `write()`. RED: `artifacts/tdd-payment-red.txt` (`irg_is_moroso` seguía verdadero). Se enganchó `account.partial.reconcile` create/unlink. Review posterior: bloqueo levantado.
- GREEN final, con el caso de desconciliar: 0 failed, 0 errors of 15 tests. Evidencia: `artifacts/tdd-green.txt`.
