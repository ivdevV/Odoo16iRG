odoo.define('irg_profile_batch_fix.timetable_batch_filter', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    // Esperar a que el módulo base registre el widget antes de extenderlo
    require('irg_timetable_portal_overhaul_v2.portal_timetable_overhaul_v2');

    if (!publicWidget.registry.PortalTimeTableWidget) {
        return;
    }

    /*
     * Extiende el widget del calendario (irg_timetable_portal_overhaul_v2)
     * para leer el parámetro batch_id de la URL y enviarlo al endpoint
     * /get-timetable/data. Esto limita las sesiones devueltas al batch
     * del alumno para el curso actual, en vez de devolver todos sus batches.
     */
    publicWidget.registry.PortalTimeTableWidget.include({
        InitKendo: async function () {
            var self = this;
            var ajax = require('web.ajax');
            var stud_id = $('.stud_id_timetable_parent').attr('id');
            var timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

            var urlParams = new URLSearchParams(window.location.search);
            var rawBatchId = urlParams.get('batch_id');
            var batchId = rawBatchId ? parseInt(rawBatchId, 10) : false;

            ajax.jsonRpc('/get-timetable/data', 'call', {
                stud_id: stud_id,
                current_timezone: timezone,
                batch_id: batchId,
            }).then(function (rows) {
                self._irgRenderOverhaul(rows || []);
            });
        },
    });
});
