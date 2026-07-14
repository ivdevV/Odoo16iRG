# Changelog

Todos los cambios relevantes de `irg_admission_oficialidad_webhook` se documentan
en este archivo.

## 16.0.1.0.0 — 2026-07-14

### Añadido

- Botón **Oficialidad** en el registro de admisión y wizard modal con selección de
  admisiones.
- Envío JSON a n8n con contexto de Odoo/registro y serialización dinámica de
  admisión, estudiante y contacto.
- Parámetros de sistema para URL, Bearer token y timeout.
- Campo de trazabilidad `oficialidad_sent_date`, actualizado solo tras HTTP 2xx.
- Suite Odoo de 21 pruebas `post_install`.

### Seguridad

- Acceso restringido al grupo administrador de admisiones y validaciones repetidas
  en servidor.
- Exclusión de binarios, campos técnicos y nombres compatibles con secretos, pese a
  que el payload funcional serializa todos los campos de negocio soportados.
- URL HTTPS con rechazo de redes no globales, redirecciones y proxies del entorno.
- Pinning de la conexión a la IP validada con SNI/certificado del hostname original
  para mitigar SSRF, DNS rebinding y la ventana DNS TOCTOU.
- Respuestas acotadas y errores sin información interna o cuerpos remotos.

### Validación

- Instalación/actualización correcta sobre Odoo 16 en `test_irg_db` mediante
  `docker-compose.local.yml`.
- Resultado: 21 tests, 0 fallos y 0 errores; validación estática y comprobaciones de
  vistas/modelos runtime superadas.
