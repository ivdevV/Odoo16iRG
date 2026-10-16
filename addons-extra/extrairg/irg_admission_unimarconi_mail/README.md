# irg_admission_unimarconi_mail

Botón **Enviar matrícula Unimarconi** en la ficha de `op.admission`.

Aparece cuando el código del lote, sin espacios iniciales y en mayúsculas,
empieza por `MO`. Abre el compositor de Odoo con la plantilla
`Admisión: matrícula Unimarconi`. El botón del correo abre
https://oficialidad.institutoraimongaja.com.

El formulario cumplimentado no se guarda en este módulo. La aplicación de
oficialidad lo envía y `irg_student_oficialidad_webhook` lo archiva como
`matricula-unimarconi`.

## Dependencias

`openeducat_admission`, `mail`.

## Pruebas

    docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
      -c /etc/odoo/odoo.conf -d test_irg_unimarconi_mail \
      -u irg_admission_unimarconi_mail --test-enable \
      --test-tags=/irg_admission_unimarconi_mail --stop-after-init \
      --http-port=8099 --log-level=test
