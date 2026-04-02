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

    // ─── Pure helpers -────────────────────────────────────────────────────────

    function escHtml(v) {
        return String(v == null ? '' : v)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * Parse "DD/MM/YYYY" → Date (local midnight).
     * Returns null on failure.
     */
    function parseDMY(str) {
        if (!str) { return null; }
        var parts = str.split('/');
        if (parts.length !== 3) { return null; }
        var d = parseInt(parts[0], 10);
        var m = parseInt(parts[1], 10) - 1;
        var y = parseInt(parts[2], 10);
        var dt = new Date(y, m, d);
        return isNaN(dt.getTime()) ? null : dt;
    }

    /** True if two Date objects refer to the same calendar day. */
    function sameDay(a, b) {
        return a && b &&
            a.getFullYear() === b.getFullYear() &&
            a.getMonth()    === b.getMonth()    &&
            a.getDate()     === b.getDate();
    }

    /** First Monday ≤ the given date (ISO week — Monday first). */
    function weekStart(date) {
        var d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        var dow = d.getDay(); // 0=Sun
        d.setDate(d.getDate() - (dow === 0 ? 6 : dow - 1));
        return d;
    }

    /**
     * Format HH:MM (Spain, Europe/Madrid) to a target timezone.
     * @param {string} hhmm  "16:00"
     * @param {Date}   baseDate  The clase's date (to anchor DST calculation)
     * @param {string} tz   target IANA zone
     * @returns {string}  localized HH:MM
     */
    function convertTime(hhmm, baseDate, tz) {
        if (!hhmm || !baseDate) { return hhmm || ''; }
        var parts = hhmm.split(':');
        var h = parseInt(parts[0], 10);
        var m = parseInt(parts[1], 10);
        // Build a UTC Date from the Spain local time
        var madridOffset = getMadridOffset(baseDate, h);
        var utcMs = Date.UTC(
            baseDate.getFullYear(), baseDate.getMonth(), baseDate.getDate(),
            h - madridOffset, m, 0
        );
        var utcDate = new Date(utcMs);
        try {
            return new Intl.DateTimeFormat('es-ES', {
                hour: '2-digit', minute: '2-digit', hour12: false, timeZone: tz,
            }).format(utcDate);
        } catch (e) {
            return hhmm;
        }
    }

    /**
     * Approximate Spain (Europe/Madrid) UTC offset in hours for a given date+hour.
     * CET = UTC+1, CEST = UTC+2 (last Sun of March → last Sun of October).
     */
    function getMadridOffset(date, hour) {
        var y = date.getFullYear();
        // Last Sunday of March
        var lastSunMar = new Date(y, 2, 31); // March 31
        lastSunMar.setDate(31 - lastSunMar.getDay());
        // Last Sunday of October
        var lastSunOct = new Date(y, 9, 31); // October 31
        lastSunOct.setDate(31 - lastSunOct.getDay());

        var d = new Date(date.getFullYear(), date.getMonth(), date.getDate(), hour);
        if (d >= lastSunMar && d < lastSunOct) {
            return 2; // CEST
        }
        return 1; // CET
    }

    var MONTH_LONG = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
    ];
    var MONTH_SHORT = [
        'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
    ];
    var DAY_HEADERS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

    // ─── Google Meet links per master (NFD-normalized, lowercase) ─────────
    var MEET_LINKS = {
        'psicologia clinica y de la salud':               'https://meet.google.com/dwi-wykx-ftw',
        'sexologia clinica y terapia de parejas':         'https://meet.google.com/kof-qphm-nvt',
        'neuropsicologia clinica basada en la evidencia': 'https://meet.google.com/kmm-iagm-gwi',
        'psicologia clinica infantojuvenil':              'https://meet.google.com/ruy-mdjo-mfo',
        'neurologopedia':                                'https://meet.google.com/ybe-xmxu-pnm',
        'neurodesarrollo y dano cerebral adquirido':      'https://meet.google.com/bmq-yert-vib',
    };

    /** Strip accents and lowercase for fuzzy master→meet matching. */
    function normalizeMaster(s) {
        return (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .toLowerCase().replace(/^master\s+(en\s+)?/i, '').trim();
    }

    function getMeetLink(masterName) {
        var key = normalizeMaster(masterName);
        // Try direct match first, then substring
        if (MEET_LINKS[key]) { return MEET_LINKS[key]; }
        var keys = Object.keys(MEET_LINKS);
        for (var i = 0; i < keys.length; i++) {
            if (key.indexOf(keys[i]) !== -1 || keys[i].indexOf(key) !== -1) {
                return MEET_LINKS[keys[i]];
            }
        }
        return null;
    }

    var TZ_OPTIONS = [
        { value: 'Europe/Madrid',            label: 'España (Madrid)' },
        { value: 'America/Mexico_City',      label: 'México (CDMX)' },
        { value: 'America/Guatemala',        label: 'Guatemala' },
        { value: 'America/El_Salvador',      label: 'El Salvador' },
        { value: 'America/Tegucigalpa',      label: 'Honduras' },
        { value: 'America/Managua',          label: 'Nicaragua' },
        { value: 'America/Costa_Rica',       label: 'Costa Rica' },
        { value: 'America/Panama',           label: 'Panamá' },
        { value: 'America/Havana',           label: 'Cuba' },
        { value: 'America/Santo_Domingo',    label: 'República Dominicana' },
        { value: 'America/Puerto_Rico',      label: 'Puerto Rico' },
        { value: 'America/Bogota',           label: 'Colombia' },
        { value: 'America/Lima',             label: 'Perú' },
        { value: 'America/Guayaquil',        label: 'Ecuador' },
        { value: 'America/La_Paz',           label: 'Bolivia' },
        { value: 'America/Caracas',          label: 'Venezuela' },
        { value: 'America/Asuncion',         label: 'Paraguay' },
        { value: 'America/Santiago',         label: 'Chile' },
        { value: 'America/Argentina/Buenos_Aires', label: 'Argentina' },
        { value: 'America/Montevideo',       label: 'Uruguay' },
        { value: 'UTC',                      label: 'UTC' },
    ];

    function buildTzOptions(current) {
        var browser = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
        var extra = { value: browser, label: 'Mi zona (' + browser + ')' };
        // prepend browser tz if not already in the list
        var found = TZ_OPTIONS.some(function (o) { return o.value === browser; });
        var opts = found ? TZ_OPTIONS : [extra].concat(TZ_OPTIONS);
        return opts.map(function (o) {
            return '<option value="' + escHtml(o.value) + '"' +
                (o.value === current ? ' selected' : '') + '>' +
                escHtml(o.label) + '</option>';
        }).join('');
    }

    // ─── Try to extract end-hour from horario string ─────────────────────────
    // e.g. "16:00–21:00h (hora España)"  → "21:00"
    function parseEndHour(horario) {
        if (!horario) { return null; }
        var m = horario.match(/[–\-]\s*(\d{1,2}:\d{2})/);
        return m ? m[1] : null;
    }

    // ─── Build date→classes index ─────────────────────────────────────────────
    function buildIndex(clases) {
        var idx = {};
        clases.forEach(function (c) {
            if (!c._date) { return; }
            var key = c._date.toDateString();
            if (!idx[key]) { idx[key] = []; }
            idx[key].push(c);
        });
        return idx;
    }

    // ─── Main render function ─────────────────────────────────────────────────

    function renderCalendar(root, apiData) {
        var lote    = apiData.lote    || '';
        var master  = apiData.master  || '';
        var horario = apiData.horario || '';
        var endHour = parseEndHour(horario);
        var meetUrl = getMeetLink(master);

        // Parse dates once
        var clases = (apiData.clases || []).map(function (c) {
            return Object.assign({}, c, { _date: parseDMY(c.fecha) });
        }).filter(function (c) { return c._date; });

        // Sort ascending
        clases.sort(function (a, b) { return a._date - b._date; });

        var idx = buildIndex(clases);

        // Initial state: navigate to first future class (or today if past)
        var today = new Date();
        var future = clases.find(function (c) { return c._date >= today; });
        var state = {
            month: future ? new Date(future._date.getFullYear(), future._date.getMonth(), 1)
                          : new Date(today.getFullYear(), today.getMonth(), 1),
            tz: 'Europe/Madrid',
            selDay: null,
        };

        function render() {
            var tz = state.tz;
            var month = state.month;
            var mIdx = month.getMonth();
            var yr   = month.getFullYear();

            // Build 42-cell grid
            var gridStart = weekStart(month);
            var cells = '';
            for (var i = 0; i < 42; i++) {
                var cell = new Date(
                    gridStart.getFullYear(),
                    gridStart.getMonth(),
                    gridStart.getDate() + i
                );
                var key     = cell.toDateString();
                var hasCls  = !!idx[key];
                var isMuted = cell.getMonth() !== mIdx;
                var isToday = sameDay(cell, today);
                var isSel   = state.selDay && sameDay(cell, state.selDay);

                var cls = 'irg-api-cell';
                if (isMuted) { cls += ' muted'; }
                if (hasCls)  { cls += ' hascls'; }
                if (isToday) { cls += ' today'; }
                if (isSel)   { cls += ' sel'; }

                // Build tooltip text for days with classes
                var cellEvts = idx[key] || [];
                var tooltipAttr = '';
                if (cellEvts.length) {
                    tooltipAttr = ' data-cls-count="' + cellEvts.length + '"';
                }

                cells += '<div class="' + cls + '" data-date="' + cell.toISOString() + '"' + tooltipAttr + '>' +
                    '<span class="irg-api-dn">' + cell.getDate() + '</span>' +
                    (hasCls && !isMuted
                        ? '<span class="irg-api-cell-label">' + escHtml(cellEvts[0].asignatura).substring(0, 16) +
                          (cellEvts[0].asignatura.length > 16 ? '…' : '') + '</span>'
                        : '') +
                    '</div>';
            }

            // Classes for selected day or entire month
            var listClases = state.selDay
                ? (idx[state.selDay.toDateString()] || [])
                : clases.filter(function (c) {
                    return c._date.getMonth() === mIdx && c._date.getFullYear() === yr;
                });

            var listTitle = state.selDay
                ? (listClases.length
                    ? 'CLASES · ' + listClases[0]._date.getDate() + ' ' +
                      MONTH_SHORT[listClases[0]._date.getMonth()].toUpperCase() + ' ' +
                      listClases[0]._date.getFullYear()
                    : 'SIN CLASES EN ESTE DÍA')
                : 'CLASES EN ' + MONTH_LONG[mIdx].toUpperCase();

            var listHtml = listClases.length ? listClases.map(function (c) {
                var startDisp = (tz === 'Europe/Madrid') ? c.hora
                    : convertTime(c.hora, c._date, tz);
                var endDisp   = endHour
                    ? ((tz === 'Europe/Madrid') ? endHour
                        : convertTime(endHour, c._date, tz))
                    : '';
                var timeRange = endDisp ? startDisp + '–' + endDisp + 'h hora española'
                                        : startDisp + 'h hora española';
                if (tz !== 'Europe/Madrid') {
                    timeRange = startDisp + (endDisp ? '–' + endDisp : '') + 'h (' + tz + ')';
                }

                return '<div class="irg-api-cls-item">' +
                    '<div class="irg-api-cls-date">' +
                        '<span class="irg-api-cls-day">' + c._date.getDate() + '</span>' +
                        '<span class="irg-api-cls-mon">' +
                            MONTH_SHORT[c._date.getMonth()] + '</span>' +
                    '</div>' +
                    '<div class="irg-api-cls-info">' +
                        '<div class="irg-api-cls-title">' + escHtml(c.asignatura) + '</div>' +
                        (c.docente
                            ? '<div class="irg-api-cls-doc">Prof. ' + escHtml(c.docente) + '</div>'
                            : '') +
                        '<div class="irg-api-cls-time">' + escHtml(timeRange) + '</div>' +
                        (c.bloqueAsignaturas
                            ? '<div class="irg-api-cls-bloque">' + escHtml(c.bloqueAsignaturas) + '</div>'
                            : '') +
                        (meetUrl
                            ? '<a class="irg-api-meet-link" href="' + escHtml(meetUrl) + '" target="_blank" rel="noopener noreferrer">' +
                              '<span class="irg-api-meet-icon">🎥</span> Unirse a la clase</a>'
                            : '') +
                    '</div>' +
                    '</div>';
            }).join('') : '<div class="irg-api-empty">Sin clases en este período</div>';

            // Timezone note suffix
            var tzNote = (tz !== 'Europe/Madrid')
                ? ' <span class="irg-api-tz-note">(convertido a ' + escHtml(tz) + ')</span>'
                : '';

            root.innerHTML =
                '<div class="irg-api-wrap">' +
                    '<div class="irg-api-header">' +
                        '<div class="irg-api-logo">' +
                            '<span class="irg-api-brand">iRG</span>' +
                        '</div>' +
                        '<div class="irg-api-header-text">' +
                            '<div class="irg-api-master">' + escHtml(master) + '</div>' +
                            '<div class="irg-api-meta">Grupo: ' + escHtml(lote) +
                                (horario ? ' · ' + escHtml(horario) : '') +
                            '</div>' +
                        '</div>' +
                        (meetUrl
                            ? '<a class="irg-api-header-meet" href="' + escHtml(meetUrl) + '" target="_blank" rel="noopener noreferrer">' +
                              '<span class="irg-api-meet-icon">🎥</span> Unirse a la clase</a>'
                            : '') +
                    '</div>' +

                    '<div class="irg-api-tz-row">' +
                        '<span class="irg-api-tz-icon">🕐</span>' +
                        '<span class="irg-api-tz-label">Zona horaria:</span>' +
                        '<select class="irg-api-tz-sel">' + buildTzOptions(tz) + '</select>' +
                    '</div>' +

                    '<div class="irg-api-cal">' +
                        '<div class="irg-api-nav">' +
                            '<button class="irg-api-nav-btn" data-dir="-1">&#8249;</button>' +
                            '<span class="irg-api-nav-title">' +
                                MONTH_LONG[mIdx] + ' ' + yr + '</span>' +
                            '<button class="irg-api-nav-btn" data-dir="1">&#8250;</button>' +
                        '</div>' +
                        '<div class="irg-api-dow">' +
                            DAY_HEADERS.map(function (d) {
                                return '<div>' + d + '</div>';
                            }).join('') +
                        '</div>' +
                        '<div class="irg-api-grid">' + cells + '</div>' +
                        '<div class="irg-api-legend">' +
                            '<span class="irg-api-leg-dot has"></span> Día con clase' +
                            '&nbsp;&nbsp;' +
                            '<span class="irg-api-leg-dot tod"></span> Hoy' +
                        '</div>' +
                    '</div>' +

                    // Popup (hidden until a cell with classes is clicked)
                    '<div class="irg-api-popup" style="display:none"></div>' +

                    '<div class="irg-api-cls-section">' +
                        '<div class="irg-api-cls-title-row">' +
                            escHtml(listTitle) + tzNote +
                        '</div>' +
                        '<div class="irg-api-cls-list">' + listHtml + '</div>' +
                    '</div>' +
                '</div>';

            // ── Event listeners (re-attached each render) ──────────────────

            root.querySelector('.irg-api-tz-sel').addEventListener('change', function (e) {
                state.tz = e.target.value || 'Europe/Madrid';
                render();
            });

            root.querySelectorAll('.irg-api-nav-btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    var dir = parseInt(btn.getAttribute('data-dir'), 10);
                    state.month = new Date(
                        state.month.getFullYear(),
                        state.month.getMonth() + dir,
                        1
                    );
                    state.selDay = null;
                    render();
                });
            });

            root.querySelectorAll('.irg-api-cell').forEach(function (cell) {
                cell.addEventListener('click', function (e) {
                    e.stopPropagation();
                    var raw = cell.getAttribute('data-date');
                    var clicked = new Date(raw);
                    // Navigate to the cell's month if it belongs to another month
                    if (clicked.getMonth() !== mIdx || clicked.getFullYear() !== yr) {
                        state.month = new Date(
                            clicked.getFullYear(), clicked.getMonth(), 1
                        );
                        state.selDay = clicked;
                        render();
                        return;
                    }
                    // Toggle selection
                    if (state.selDay && sameDay(state.selDay, clicked)) {
                        state.selDay = null;
                    } else {
                        state.selDay = clicked;
                    }

                    // Show popup if day has classes
                    var dayClases = idx[clicked.toDateString()] || [];
                    var popup = root.querySelector('.irg-api-popup');
                    if (dayClases.length && popup) {
                        var pStartDisp = (tz === 'Europe/Madrid') ? dayClases[0].hora
                            : convertTime(dayClases[0].hora, dayClases[0]._date, tz);
                        var pEndDisp = endHour
                            ? ((tz === 'Europe/Madrid') ? endHour
                                : convertTime(endHour, dayClases[0]._date, tz))
                            : '';
                        var pTimeRange = pStartDisp + (pEndDisp ? ' - ' + pEndDisp : '') + ' hora española';
                        if (tz !== 'Europe/Madrid') {
                            pTimeRange = pStartDisp + (pEndDisp ? ' - ' + pEndDisp : '') + ' (' + tz + ')';
                        }

                        popup.innerHTML =
                            '<div class="irg-api-popup-inner">' +
                                '<button class="irg-api-popup-close">&times;</button>' +
                                '<div class="irg-api-popup-date">' +
                                    '<span class="irg-api-popup-dn">' + clicked.getDate() + '</span> ' +
                                    String(clicked.getDate()).padStart(2, '0') + '/' +
                                    String(clicked.getMonth() + 1).padStart(2, '0') + '/' +
                                    clicked.getFullYear() +
                                '</div>' +
                                dayClases.map(function (pc) {
                                    var pcStart = (tz === 'Europe/Madrid') ? pc.hora
                                        : convertTime(pc.hora, pc._date, tz);
                                    var pcEnd = endHour
                                        ? ((tz === 'Europe/Madrid') ? endHour
                                            : convertTime(endHour, pc._date, tz))
                                        : '';
                                    var pcTime = pcStart + ':00' + (pcEnd ? ' - ' + pcEnd + ':00' : '') + ' hora española';
                                    if (tz !== 'Europe/Madrid') {
                                        pcTime = pcStart + (pcEnd ? ' - ' + pcEnd : '') + ' (' + tz + ')';
                                    }
                                    return '<div class="irg-api-popup-cls">' +
                                        '<div class="irg-api-popup-title">' + escHtml(pc.asignatura) + '</div>' +
                                        (pc.docente
                                            ? '<div class="irg-api-popup-doc">Prof. ' + escHtml(pc.docente) + '</div>'
                                            : '') +
                                        '<div class="irg-api-popup-time">' + escHtml(pcTime) + '</div>' +
                                        (meetUrl
                                            ? '<a class="irg-api-popup-meet" href="' + escHtml(meetUrl) + '" target="_blank" rel="noopener noreferrer">' +
                                              '<span class="irg-api-meet-icon">🎥</span> Unirse a la clase</a>'
                                            : '') +
                                    '</div>';
                                }).join('') +
                            '</div>';
                        popup.style.display = '';

                        // Position popup near the cell
                        var cellRect = cell.getBoundingClientRect();
                        var rootRect = root.getBoundingClientRect();
                        popup.style.position = 'absolute';
                        popup.style.top = (cellRect.bottom - rootRect.top + 6) + 'px';
                        popup.style.left = Math.max(0, Math.min(
                            cellRect.left - rootRect.left - 60,
                            rootRect.width - 280
                        )) + 'px';

                        popup.querySelector('.irg-api-popup-close').addEventListener('click', function (ev) {
                            ev.stopPropagation();
                            popup.style.display = 'none';
                        });
                    } else if (popup) {
                        popup.style.display = 'none';
                    }

                    // Re-render grid + class list (but NOT inside the popup flow)
                    // Save popup state before render
                    var popupHtml = popup ? popup.innerHTML : '';
                    var popupDisplay = popup ? popup.style.display : 'none';
                    var popupTop = popup ? popup.style.top : '';
                    var popupLeft = popup ? popup.style.left : '';

                    render();

                    // Restore popup after render
                    var newPopup = root.querySelector('.irg-api-popup');
                    if (newPopup && popupDisplay !== 'none') {
                        newPopup.innerHTML = popupHtml;
                        newPopup.style.display = popupDisplay;
                        newPopup.style.position = 'absolute';
                        newPopup.style.top = popupTop;
                        newPopup.style.left = popupLeft;
                        var closeBtn = newPopup.querySelector('.irg-api-popup-close');
                        if (closeBtn) {
                            closeBtn.addEventListener('click', function (ev) {
                                ev.stopPropagation();
                                newPopup.style.display = 'none';
                            });
                        }
                    }
                });
            });
        } // end render()

        // Close popup when clicking outside (registered once, outside render)
        document.addEventListener('click', function (e) {
            var popup = root.querySelector('.irg-api-popup');
            if (popup && popup.style.display !== 'none' &&
                !popup.contains(e.target) &&
                !e.target.closest('.irg-api-cell')) {
                popup.style.display = 'none';
            }
        });

        render();
    }

    // ─── Show error inside the root div ──────────────────────────────────────

    function showError(root, msg) {
        root.innerHTML =
            '<div class="irg-api-error">' +
                '<span class="irg-api-error-icon">⚠️</span>' +
                '<span>' + escHtml(msg) + '</span>' +
            '</div>';
    }

    // ─── Widget override ──────────────────────────────────────────────────────

    publicWidget.registry.PortalTimeTableWidget.include({

        /**
         * Prevent the base widget from loading Kendo JS/CSS (~2 MB).
         * We shadow the prototype's jsLibs/cssLibs with empty arrays
         * before _super calls loadLibs().
         */
        willStart: function () {
            this.jsLibs = [];
            this.cssLibs = [];
            return this._super.apply(this, arguments);
        },

        /**
         * Override the base entry point so the Kendo/op.session path is never
         * executed. We mount our own calendar instead.
         */
        setLocaleKendo: async function () {
            await this._irgApiInit();
            return true;
        },

        _irgApiInit: async function () {
            var root = document.getElementById('irg-api-calendar-root');
            if (!root) {
                // New module's div wasn't found — bail out silently.
                return;
            }

            // Show spinner
            root.innerHTML =
                '<div class="irg-api-loading">' +
                    '<span class="irg-api-spinner"></span>Cargando calendario…' +
                '</div>';

            // 1. Resolve lote via Odoo controller
            var studId = (document.querySelector('.stud_id_timetable_parent') || {}).id || null;
            var loteInfo;
            try {
                loteInfo = await ajax.jsonRpc('/irg-timetable/lote', 'call', {
                    stud_id: studId || undefined,
                });
            } catch (err) {
                showError(root,
                    'No se pudo determinar tu grupo. Por favor, contacta con soporte.');
                return;
            }

            if (!loteInfo || loteInfo.error === 'no_batch' || !loteInfo.lote) {
                showError(root,
                    'No se encontró un grupo (lote) asignado a tu cuenta. ' +
                    'Si acabas de matricularte, espera unos minutos y recarga la página.');
                return;
            }

            var baseUrl = (loteInfo.base_url || 'https://calendario.institutoraimongaja.com').replace(/\/$/, '');
            var lote    = loteInfo.lote;
            var apiUrl  = baseUrl + '/api/calendario/' + encodeURIComponent(lote);

            // 2. Fetch from external IRG API
            var controller = new AbortController();
            var timeoutId  = setTimeout(function () { controller.abort(); }, 30000);
            var apiData;
            try {
                var resp = await fetch(apiUrl, { signal: controller.signal });
                clearTimeout(timeoutId);
                if (resp.status === 404) {
                    showError(root,
                        'El grupo "' + lote + '" no se encontró en el calendario. ' +
                        'Contacta con tu coordinador académico.');
                    return;
                }
                if (!resp.ok) {
                    showError(root,
                        'Error al obtener el calendario (HTTP ' + resp.status + '). ' +
                        'Inténtalo de nuevo más tarde.');
                    return;
                }
                apiData = await resp.json();
            } catch (fetchErr) {
                clearTimeout(timeoutId);
                if (fetchErr.name === 'AbortError') {
                    showError(root,
                        'El servidor de calendarios tardó demasiado en responder. ' +
                        'Recarga la página para intentarlo de nuevo.');
                } else {
                    showError(root,
                        'No se pudo conectar con el servidor de calendarios. ' +
                        'Comprueba tu conexión a internet.');
                }
                return;
            }

            // 3. Render
            renderCalendar(root, apiData);
        },
    });
});
