odoo.define('irg_timetable_lote_batch_fix.main', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');

    // Cargar el módulo base para asegurar que _irgApiInit ya existe antes
    // de sobreescribirlo.
    require('irg_timetable_irg_api.main');

    if (!publicWidget.registry.PortalTimeTableWidget) {
        return;
    }

    publicWidget.registry.PortalTimeTableWidget.include({

        /**
         * Override de _irgApiInit que añade soporte para ?batch_id=X en la URL.
         *
         * Cuando /student/timetable/?batch_id=X (u otra página) incluye batch_id
         * en la query string, lo pasamos directamente al endpoint
         * /irg-timetable/lote para que devuelva el nombre del lote correcto,
         * en vez de resolver por enrollment running (que puede ser incorrecto
         * para alumnos matriculados en más de un programa).
         *
         * Si no hay batch_id en la URL, delega al comportamiento original.
         */
        _irgApiInit: async function () {
            var urlParams = new URLSearchParams(window.location.search);
            var rawBatchId = urlParams.get('batch_id');
            var batchId = rawBatchId ? parseInt(rawBatchId, 10) : 0;

            // Sin batch_id en la URL → comportamiento original del compañero
            if (!batchId) {
                return this._super.apply(this, arguments);
            }

            var root = document.getElementById('irg-api-calendar-root');
            if (!root) {
                return this._super.apply(this, arguments);
            }

            root.innerHTML =
                '<div class="irg-api-loading">' +
                    '<span class="irg-api-spinner"></span>Cargando calendario\u2026' +
                '</div>';

            var loteInfo;
            try {
                loteInfo = await ajax.jsonRpc('/irg-timetable/lote', 'call', {
                    batch_id: batchId,
                });
            } catch (err) {
                // Si falla la llamada con batch_id, intentamos el flujo original
                return this._super.apply(this, arguments);
            }

            // Si el servidor no pudo resolver el batch, intentamos el flujo original
            if (!loteInfo || loteInfo.error || !loteInfo.lote) {
                return this._super.apply(this, arguments);
            }

            var baseUrl = (loteInfo.base_url || 'https://calendario.institutoraimongaja.com')
                .replace(/\/$/, '');
            var embedUrl = baseUrl + '/embed/' + encodeURIComponent(loteInfo.lote);

            root.innerHTML =
                '<iframe class="irg-api-iframe" ' +
                    'src="' + embedUrl + '" ' +
                    'title="Calendario de clases" ' +
                    'allow="fullscreen" ' +
                    'loading="lazy">' +
                '</iframe>';
        },
    });
});
