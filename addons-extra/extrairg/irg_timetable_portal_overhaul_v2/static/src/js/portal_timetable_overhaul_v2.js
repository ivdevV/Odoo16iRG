odoo.define('irg_timetable_portal_overhaul_v2.portal_timetable_overhaul_v2', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');

    require('openeducat_timetable_enterprise.portal_timetable');

    if (!publicWidget.registry.PortalTimeTableWidget) {
        return;
    }

    function parseDate(rawValue) {
        if (!rawValue) {
            return null;
        }
        if (rawValue instanceof Date) {
            return rawValue;
        }
        var text = String(rawValue).trim();
        if (!text) {
            return null;
        }
        if (text.indexOf('T') === -1) {
            text = text.replace(' ', 'T');
        }
        var parsed = new Date(text);
        if (!isNaN(parsed.getTime())) {
            return parsed;
        }
        parsed = new Date(text + 'Z');
        if (!isNaN(parsed.getTime())) {
            return parsed;
        }
        return null;
    }

    function formatTime(dateObj) {
        if (!dateObj) {
            return '';
        }
        return dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function formatTimeInZone(dateObj, timeZone) {
        if (!dateObj) {
            return '';
        }
        return new Intl.DateTimeFormat('es-ES', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: timeZone,
        }).format(dateObj);
    }

    function formatDateInZone(dateObj, timeZone) {
        if (!dateObj) {
            return '';
        }
        return new Intl.DateTimeFormat('es-ES', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            timeZone: timeZone,
        }).format(dateObj);
    }

    function formatDayNameInZone(dateObj, timeZone) {
        if (!dateObj) {
            return '-';
        }
        return new Intl.DateTimeFormat('en-US', {
            weekday: 'long',
            timeZone: timeZone,
        }).format(dateObj);
    }

    function buildTimezoneOptions(browserTimezone) {
        var options = [
            { value: browserTimezone || 'UTC', label: 'Mi zona (' + (browserTimezone || 'UTC') + ')' },
            { value: 'Europe/Madrid', label: 'Campus (Europe/Madrid)' },
            { value: 'UTC', label: 'UTC' },

            { value: 'America/Mexico_City', label: 'México (CDMX)' },
            { value: 'America/Guatemala', label: 'Guatemala' },
            { value: 'America/El_Salvador', label: 'El Salvador' },
            { value: 'America/Tegucigalpa', label: 'Honduras' },
            { value: 'America/Managua', label: 'Nicaragua' },
            { value: 'America/Costa_Rica', label: 'Costa Rica' },
            { value: 'America/Panama', label: 'Panamá' },
            { value: 'America/Havana', label: 'Cuba (La Habana)' },
            { value: 'America/Santo_Domingo', label: 'República Dominicana' },
            { value: 'America/Puerto_Rico', label: 'Puerto Rico' },

            { value: 'America/Bogota', label: 'Colombia' },
            { value: 'America/Lima', label: 'Perú' },
            { value: 'America/Guayaquil', label: 'Ecuador (Guayaquil)' },
            { value: 'America/La_Paz', label: 'Bolivia' },
            { value: 'America/Caracas', label: 'Venezuela' },
            { value: 'America/Asuncion', label: 'Paraguay' },
            { value: 'America/Santiago', label: 'Chile (Santiago)' },
            { value: 'America/Argentina/Buenos_Aires', label: 'Argentina (Buenos Aires)' },
            { value: 'America/Montevideo', label: 'Uruguay (Montevideo)' },
        ];
        var seen = {};
        return options.filter(function (item) {
            if (seen[item.value]) {
                return false;
            }
            seen[item.value] = true;
            return true;
        });
    }

    function sameDay(a, b) {
        return a && b &&
            a.getFullYear() === b.getFullYear() &&
            a.getMonth() === b.getMonth() &&
            a.getDate() === b.getDate();
    }

    function escapeHtml(value) {
        var source = value === undefined || value === null ? '' : String(value);
        return source
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    publicWidget.registry.PortalTimeTableWidget.include({
        setLocaleKendo: async function () {
            this.InitKendo();
            return true;
        },

        InitKendo: async function () {
            var self = this;
            var stud_id = $('.stud_id_timetable_parent').attr('id');
            var timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

            ajax.jsonRpc('/get-timetable/data', 'call', {
                stud_id: stud_id,
                current_timezone: timezone,
            }).then(function (rows) {
                self._irgRenderOverhaul(rows || []);
            });
        },

        _irgRenderOverhaul: function (rows) {
            var root = document.getElementById('irg_timetable_overhaul_root');
            if (!root) {
                return;
            }

            var events = rows.map(function (item, index) {
                var start = parseDate(item.start);
                var end = parseDate(item.end) || start;
                return {
                    id: index + 1,
                    title: item.title || 'Clase',
                    faculty: item.faculty || '-',
                    course: item.course || '-',
                    batch: item.batch || '-',
                    day: item.day || '-',
                    lesson: item.lesson || '',
                    start: start,
                    end: end,
                    time_url_metting: item.time_url_metting || '',
                    time_url_recoding: item.time_url_recoding || '',
                };
            }).filter(function (item) {
                return item.start;
            });

            var state = {
                currentDate: new Date(),
                selectedDate: new Date(),
                selectedEvent: null,
            };

            var browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
            var timezoneOptions = buildTimezoneOptions(browserTimezone);
            var monthNames = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
            var dayNames = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

            var getWeekStart = function (date) {
                var copy = new Date(date.getFullYear(), date.getMonth(), date.getDate());
                var day = copy.getDay();
                var diff = day === 0 ? -6 : 1 - day;
                copy.setDate(copy.getDate() + diff);
                return copy;
            };

            var getEventsByDate = function (date) {
                return events
                    .filter(function (eventItem) {
                        return sameDay(eventItem.start, date);
                    })
                    .sort(function (a, b) {
                        return a.start - b.start;
                    });
            };

            var buildCell = function (date, currentMonth, activeTimezone) {
                var inMonth = date.getMonth() === currentMonth;
                var isToday = sameDay(date, new Date());
                var isSelected = sameDay(date, state.selectedDate);
                var items = getEventsByDate(date);

                var maxItems = 3;
                var shown = items.slice(0, maxItems);
                var more = items.length - shown.length;

                var eventHtml = shown.map(function (ev) {
                    return '<button class="irg-oh-event" data-event-id="' + ev.id + '">' +
                        '<span class="irg-oh-event-time">' + formatTimeInZone(ev.start, activeTimezone) + '</span>' +
                        '<span class="irg-oh-event-title">' + escapeHtml(ev.title) + '</span>' +
                        '</button>';
                }).join('');

                if (more > 0) {
                    eventHtml += '<div class="irg-oh-more">+' + more + ' más</div>';
                }

                return '<div class="irg-oh-cell' +
                    (inMonth ? '' : ' is-muted') +
                    (isToday ? ' is-today' : '') +
                    (isSelected ? ' is-selected' : '') +
                    '" data-date="' + date.toISOString() + '">' +
                    '<div class="irg-oh-cell-head">' + date.getDate() + '</div>' +
                    '<div class="irg-oh-cell-events">' + eventHtml + '</div>' +
                    '</div>';
            };

            var render = function () {
                var activeTimezone = state.displayTimezone || browserTimezone || 'UTC';
                var monthStart = new Date(state.currentDate.getFullYear(), state.currentDate.getMonth(), 1);
                var gridStart = getWeekStart(monthStart);
                var cursor = new Date(gridStart);

                var cells = '';
                for (var i = 0; i < 42; i++) {
                    cells += buildCell(cursor, state.currentDate.getMonth(), activeTimezone);
                    cursor.setDate(cursor.getDate() + 1);
                }

                var selectedEvents = getEventsByDate(state.selectedDate);
                var agendaHtml = selectedEvents.length ? selectedEvents.map(function (ev) {
                    return '<button class="irg-oh-agenda-item" data-event-id="' + ev.id + '">' +
                        '<div class="irg-oh-agenda-time">' + formatTimeInZone(ev.start, activeTimezone) + ' - ' + formatTimeInZone(ev.end, activeTimezone) + '</div>' +
                        '<div class="irg-oh-agenda-title">' + escapeHtml(ev.title) + '</div>' +
                        '<div class="irg-oh-agenda-meta">' + escapeHtml(ev.course) + ' · ' + escapeHtml(ev.faculty) + '</div>' +
                    '</button>';
                }).join('') : '<div class="irg-oh-empty">Sin clases para este día</div>';

                var selected = state.selectedEvent;
                var detailHtml = selected ?
                    '<div class="irg-oh-detail-card">' +
                        '<h4>' + escapeHtml(selected.title) + '</h4>' +
                        '<p><strong>Hora:</strong> ' + formatTimeInZone(selected.start, activeTimezone) + ' - ' + formatTimeInZone(selected.end, activeTimezone) + '</p>' +
                        '<p><strong>Docente:</strong> ' + escapeHtml(selected.faculty) + '</p>' +
                        '<p><strong>Curso:</strong> ' + escapeHtml(selected.course) + '</p>' +
                        '<p><strong>Lote:</strong> ' + escapeHtml(selected.batch) + '</p>' +
                        '<p><strong>Día:</strong> ' + escapeHtml(formatDayNameInZone(selected.start, activeTimezone)) + '</p>' +
                        '<p><strong>Zona horaria:</strong> ' + escapeHtml(activeTimezone) + '</p>' +
                        '<div class="irg-oh-detail-notes">' + escapeHtml(selected.lesson || '-') + '</div>' +
                        (selected.time_url_metting ? '<a class="irg-oh-link" target="_blank" href="' + escapeHtml(selected.time_url_metting) + '">Acceso en vivo</a>' : '') +
                        (selected.time_url_recoding ? '<a class="irg-oh-link" target="_blank" href="' + escapeHtml(selected.time_url_recoding) + '">Grabación</a>' : '') +
                    '</div>' :
                    '<div class="irg-oh-empty">Selecciona una clase para ver detalle</div>';

                root.innerHTML =
                    '<div class="irg-oh-shell">' +
                        '<div class="irg-oh-topbar">' +
                            '<div class="irg-oh-nav">' +
                                '<button class="irg-oh-btn" data-action="prev">◀</button>' +
                                '<button class="irg-oh-btn" data-action="today">Hoy</button>' +
                                '<button class="irg-oh-btn" data-action="next">▶</button>' +
                            '</div>' +
                            '<div class="irg-oh-tools">' +
                                '<label for="irg-oh-tz-select" class="irg-oh-tools-label">Hora en:</label>' +
                                '<select id="irg-oh-tz-select" class="irg-oh-timezone-select">' +
                                    timezoneOptions.map(function (option) {
                                        return '<option value="' + escapeHtml(option.value) + '"' + (option.value === activeTimezone ? ' selected="selected"' : '') + '>' + escapeHtml(option.label) + '</option>';
                                    }).join('') +
                                '</select>' +
                            '</div>' +
                            '<div class="irg-oh-title">' + monthNames[state.currentDate.getMonth()] + ' ' + state.currentDate.getFullYear() + '</div>' +
                        '</div>' +
                        '<div class="irg-oh-layout">' +
                            '<div class="irg-oh-main">' +
                                '<div class="irg-oh-weekdays">' + dayNames.map(function (name) { return '<div>' + name + '</div>'; }).join('') + '</div>' +
                                '<div class="irg-oh-grid">' + cells + '</div>' +
                            '</div>' +
                            '<aside class="irg-oh-sidebar">' +
                                '<div class="irg-oh-sidebar-card">' +
                                    '<h3>Agenda · ' + formatDateInZone(state.selectedDate, activeTimezone) + '</h3>' +
                                    '<div class="irg-oh-timezone-note">Zona: ' + escapeHtml(activeTimezone) + '</div>' +
                                    '<div class="irg-oh-agenda">' + agendaHtml + '</div>' +
                                '</div>' +
                                '<div class="irg-oh-sidebar-card">' +
                                    '<h3>Detalle</h3>' + detailHtml +
                                '</div>' +
                            '</aside>' +
                        '</div>' +
                    '</div>';

                root.querySelectorAll('[data-action="prev"]').forEach(function (btn) {
                    btn.addEventListener('click', function () {
                        state.currentDate.setMonth(state.currentDate.getMonth() - 1);
                        render();
                    });
                });
                root.querySelectorAll('[data-action="next"]').forEach(function (btn) {
                    btn.addEventListener('click', function () {
                        state.currentDate.setMonth(state.currentDate.getMonth() + 1);
                        render();
                    });
                });
                root.querySelectorAll('[data-action="today"]').forEach(function (btn) {
                    btn.addEventListener('click', function () {
                        state.currentDate = new Date();
                        state.selectedDate = new Date();
                        render();
                    });
                });

                var timezoneSelect = root.querySelector('.irg-oh-timezone-select');
                if (timezoneSelect) {
                    timezoneSelect.addEventListener('change', function () {
                        state.displayTimezone = timezoneSelect.value || browserTimezone || 'UTC';
                        render();
                    });
                }

                root.querySelectorAll('.irg-oh-cell').forEach(function (cell) {
                    cell.addEventListener('click', function () {
                        var raw = cell.getAttribute('data-date');
                        state.selectedDate = new Date(raw);
                        state.selectedEvent = null;
                        render();
                    });
                });

                root.querySelectorAll('[data-event-id]').forEach(function (node) {
                    node.addEventListener('click', function (event) {
                        event.stopPropagation();
                        var id = parseInt(node.getAttribute('data-event-id'), 10);
                        state.selectedEvent = events.find(function (eventItem) {
                            return eventItem.id === id;
                        }) || null;
                        if (state.selectedEvent) {
                            state.selectedDate = new Date(state.selectedEvent.start);
                        }
                        render();
                    });
                });
            };

            state.selectedEvent = events.length ? events[0] : null;
            state.displayTimezone = browserTimezone;
            if (state.selectedEvent) {
                state.selectedDate = new Date(state.selectedEvent.start);
                state.currentDate = new Date(state.selectedEvent.start);
            }
            render();
        },
    });
});
