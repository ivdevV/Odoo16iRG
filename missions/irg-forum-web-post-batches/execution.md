# Ejecución

- Rama: `feat/irg-forum-web-post-batches` desde `Dev_iRG` (`fec6149f3`).
- La imagen `odoo16irg:16.0-local` no se pudo construir: apt devolvió 404 de paquetes de Debian 11. Las pruebas corrieron con la imagen oficial `odoo:16.0` y Postgres de `docker-compose.local.yml`.
- Base desechable: `test_irg_web_post_batches`.
- Resultado final: 8 tests, 0 failed, 0 errors.
- Review independiente: aprobada, sin bloqueos. Se añadió después un filtro para aceptar el contexto de lotes solo si es lista o tupla.
- TestSprite no se ejecutó: no hay runtime de campus en el puerto 8069 y la imagen local no compiló.
