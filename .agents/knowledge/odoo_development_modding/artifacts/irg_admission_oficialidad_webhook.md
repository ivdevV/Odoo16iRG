# Aprendizajes: webhook de oficialidad de admisiones

## Contexto

El módulo `irg_admission_oficialidad_webhook` envía desde Odoo 16 a n8n una
serialización dinámica de `op.admission`, `op.student` y `res.partner`. El destino
final es un Google Sheet gestionado fuera de Odoo.

## Decisiones reutilizables

### Serialización completa no significa exportar secretos

Cuando un contrato pide iterar `record._fields`, hay que conservar la extensibilidad
sin convertir el webhook en un exfiltrador de credenciales. La solución adoptada:

- incluir escalares, fechas y relaciones simples de forma dinámica;
- excluir binarios/imágenes y chatter/actividad/acceso;
- excluir nombres normalizados que contengan patrones de secreto (`token`,
  `secret`, `password`, `passwd`, `apikey`, `privatekey`, `credential`);
- capturar por campo los computes/related defectuosos para omitir solo ese campo.

Esta es una decisión de seguridad deliberada aunque el requisito funcional hable de
“serialización completa”. El filtro por nombre es defensa en profundidad: se debe
seguir revisando la PII y ampliar patrones cuando aparezcan convenciones nuevas.

### SSRF, DNS rebinding y pinning

Validar únicamente el esquema o resolver DNS y después dejar que `urllib` resuelva
otra vez mantiene una ventana TOCTOU. El patrón robusto usado aquí es:

1. aceptar solo HTTPS sin credenciales ni fragmento;
2. resolver todas las direcciones y rechazar el destino si alguna no es global;
3. deshabilitar proxies ambientales y redirecciones;
4. conectar el socket a la IP ya validada;
5. conservar el hostname original para SNI y validación del certificado TLS;
6. limitar timeout y lectura del cuerpo remoto.

No debe aplicarse pinning global ni monkey-patching de DNS/socket. El handler y la
conexión deben ser por petición para no afectar a otros procesos Odoo.

### Autorización en servidor

`groups` en botones/acciones y dominios de campos solo protegen la interfaz. Los
métodos `default_get`, `action_send` y el servicio deben comprobar el grupo servidor,
el `active_model`, la pertenencia de los registros y las ACL/reglas reales. El
destino n8n también debe validar el Bearer token del lado servidor antes de procesar
el JSON; ocultar una URL o un botón nunca es autenticación.

Limitar `sudo()` a la lectura de `ir.config_parameter`. No usarlo para leer o marcar
admisiones porque el usuario debe conservar sus permisos y reglas de registro.

### PII y trazabilidad

La serialización dinámica amplía automáticamente el payload cuando otros módulos
añaden campos. Esto obliga a revisión periódica, minimización en n8n, retención
definida en n8n/Sheets/logs/backups y prohibición de registrar payloads reales. Una
fecha local tras 2xx ofrece trazabilidad mínima, no historial de entregas ni
idempotencia.

## Gotchas del worktree con Docker local

`docker-compose.local.yml` está configurado alrededor del checkout principal y sus
volúmenes no apuntan automáticamente a un worktree de Git. Copiar el addon al
checkout original contamina el workspace y puede validar código distinto al diff.

Para esta misión se reutilizaron la imagen, red, configuración y base de datos del
compose local, pero se lanzó un contenedor efímero con el `addons-extra` del worktree
montado en solo lectura. Las comprobaciones deben confirmar dentro del contenedor
qué ruta del módulo se importó. Los logs Odoo pueden incluir warnings ajenos de los
centenares de addons instalados; el criterio fiable es el resumen del módulo, el
conteo de tests y el código de salida.

Los artefactos `*.log` están ignorados globalmente en este repositorio. Cuando una
misión exige evidencia versionada, deben añadirse explícitamente con `git add -f`,
sin incluir secretos ni payloads de producción.

## Evidencia de referencia

- `missions/oficialidad-webhook/verification.json`: estado `passed`.
- `missions/oficialidad-webhook/artifacts/runtime-summary.log`: 21 tests, 0 fallos,
  0 errores y vistas/modelos runtime correctos.
- `missions/oficialidad-webhook/artifacts/static-validation.log`: AST, XML,
  manifest, ACL, contrato del servicio y diff correctos.
