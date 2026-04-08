odoo.define('irg_timetable_irg_api.main', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');

    // Load the base widget so we can override it
    require('openeducat_timetable_enterprise.portal_timetable');

    // Guard: base widget must exist
    if (!publicWidget.registry.PortalTimeTableWidget) {
        return;
    }

    function escHtml(v) {
        return String(v == null ? '' : v)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function showError(root, msg) {
        root.innerHTML =
            '<div class="irg-api-error">' +
                '<span class="irg-api-error-icon">⚠️</span>' +
                '<span>' + escHtml(msg) + '</span>' +
            '</div>';
    }

    function buildIframe(baseUrl, lote) {
        var embedUrl = baseUrl + '/embed/' + encodeURIComponent(lote);
        return '<iframe class="irg-api-iframe" ' +
                'src="' + escHtml(embedUrl) + '" ' +
                'title="Calendario de clases" ' +
                'allow="fullscreen" ' +
                'loading="lazy">' +
            '</iframe>';
    }

    publicWidget.registry.PortalTimeTableWidget.include({

        /**
         * Prevent the base widget from loading Kendo JS/CSS (~2 MB).
         */
        willStart: function () {
            this.jsLibs = [];
            this.cssLibs = [];
            return this._super.apply(this, arguments);
        },

        /**
         * Override the base entry point — mount an iframe to /embed/:lote
         * instead of initialising the Kendo scheduler.
         */
        setLocaleKendo: async function () {
            await this._irgApiInit();
            return true;
        },

        _irgApiInit: async function () {
            var root = document.getElementById('irg-api-calendar-root');
            if (!root) { return; }

            // Show spinner while resolving lote
            root.innerHTML =
                '<div class="irg-api-loading">' +
                    '<span class="irg-api-spinner"></span>Cargando calendario\u2026' +
                '</div>';

            // Extract course_id from the URL: /campus/course/{course_id}
            var courseId = null;
            var urlMatch = window.location.pathname.match(/\/campus\/course\/(\d+)/);
            if (urlMatch) {
                courseId = parseInt(urlMatch[1], 10);
            }

            var loteInfo;
            try {
                loteInfo = await ajax.jsonRpc('/irg-timetable/lote', 'call', {
                    course_id: courseId || undefined,
                });
            } catch (err) {
                showError(root,
                    'No se pudo determinar tu grupo. Por favor, contacta con soporte.');
                return;
            }

            if (!loteInfo || loteInfo.error === 'no_batch' || !loteInfo.lote) {
                showError(root,
                    'No se encontr\u00f3 un grupo (lote) asignado a tu cuenta. ' +
                    'Si acabas de matricularte, espera unos minutos y recarga la p\u00e1gina.');
                return;
            }

            var baseUrl = (loteInfo.base_url || 'https://calendario.institutoraimongaja.com')
                .replace(/\/$/, '');

            root.innerHTML = buildIframe(baseUrl, loteInfo.lote);
        },
    });
});
