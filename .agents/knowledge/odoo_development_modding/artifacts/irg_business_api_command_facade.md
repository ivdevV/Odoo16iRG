# Fachada de comandos Odoo: write cerrado y apply interno

## Contexto

Un modelo de comandos (`irg.api.operation`) es la única superficie RPC para un agente. El cliente puede hacer `create`, `write` y pasar `context` arbitrario. Cualquier atajo interno visible por RPC se convierte en forja de `state` o de snapshots.

## Gotcha: no usar flags de contexto como guarda

`write()` no puede fiarse de `self.env.context.get('irg_api_internal')`. El cliente RPC envía ese contexto. El patrón validado:

```python
def write(self, vals):
    raise AccessError(_('API operation fields cannot be written directly.'))

def _irg_internal_write(self, vals):
    return super(IrgApiOperation, self).write(vals)
```

`super().write()` no reentra en el override. `create()` también usa `super().create()` y luego `_irg_internal_write` para campos de servidor.

## Gotcha: `self.env.sudo()` no existe

En Odoo 16 el sudo del environment es `self.sudo().env`, no `self.env.sudo()`. Lo segundo levanta `AttributeError` en runtime.

## Gotcha: `write_date` a segundo no sirve para optimistic lock

Entre preview y apply, comparar solo `write_date` del objetivo pierde condiciones de carrera en el mismo segundo. El patrón usado compara campos de negocio (nombre, `is_published`, secuencia) además del bloqueo `SELECT … FOR UPDATE` de la fila de operación.

## Patrón de ciclo

Lectura: `create` → resultado en snapshot → `verified`.
Escritura: `create` → `preview` → `action_approve` (o meta `irg_approve_operation` en el mismo create, para no anidar aprobaciones).
Apply: re-check de grupo y propietario → `FOR UPDATE` → savepoint → allowlist ORM → verificar → `verified`.
