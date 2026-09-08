# IRG Practice Agreement Types

En el practice center, **Crear Convenio** abre un wizard para elegir
**Marco Nacional** o **Marco Internacional**. El nacional reutiliza la
plantilla de `irg_practice_agreement_sign`. El internacional añade la
cláusula 4.3 de seguros (RC de iRG solo en España; fuera, a cargo del
estudiante) y separa confidencialidad y protección de datos.

## Uso

1. Instalar `irg_practice_agreement_types` (depende de
   `irg_practice_agreement_sign`).
2. Abrir un centro de prácticas → **Crear Convenio**.
3. Elegir el tipo y **Crear**. Se abre el convenio en borrador.
4. Enviar por email y firmar como hasta ahora. El PDF y el portal usan
   el texto del tipo elegido.

Los convenios ya existentes se tratan como nacional. El tipo no se puede
cambiar una vez enviado o firmado.

Los convenios específicos del alumno están en
`irg_practice_agreement_specific` (esta entrega: internacional).

## Pruebas

```bash
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d <db> -u irg_practice_agreement_types \
  --test-enable --test-tags /irg_practice_agreement_types \
  --stop-after-init --http-port=8099 --log-level=test
```
