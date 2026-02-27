odoo.define('irg_op_session_default_month.portal_timetable_month_default', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');

    require('openeducat_timetable_enterprise.portal_timetable');

    if (!publicWidget.registry.PortalTimeTableWidget) {
        return;
    }

    publicWidget.registry.PortalTimeTableWidget.include({
        InitKendo: async function () {
            var today = new Date();
            var date = today.getFullYear() + '/' + (today.getMonth() + 1) + '/' + today.getDate();
            var stud_id = $(".stud_id_timetable_parent").attr('id');
            var timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

            ajax.jsonRpc("/get-timetable/data", 'call', {
                stud_id: stud_id,
                current_timezone: timezone,
            }).then(function (data) {
                var kendoData = new kendo.data.SchedulerDataSource({ data: data });

                $('#timetable_portal_kendo').kendoScheduler({
                    date: new Date(date),
                    editable: {
                        confirmation: false,
                        create: false,
                        destroy: false,
                        move: false,
                        editRecurringMode: "series",
                        resize: false,
                        template: $("#editor").html(),
                    },
                    majorTimeHeaderTemplate: kendo.template("<strong>#=kendo.toString(date, 'HH:mm')#</strong>"),
                    edit: function (e) {
                        e.container.find(".k-scheduler-update").hide();
                    },
                    views: [
                        {
                            type: "day",
                            eventTemplate: $("#event-template").html(),
                            dateHeaderTemplate: "<span class='k-link k-nav-day'>#=kendo.toString(date, 'ddd dd/M')#</span>",
                        },
                        {
                            type: "week",
                            eventTemplate: $("#event-template").html(),
                            dateHeaderTemplate: "<span class='k-link k-nav-day'>#=kendo.toString(date, 'ddd dd/M')#</span>",
                        },
                        {
                            type: "month",
                            selected: true,
                        },
                        {
                            type: "agenda",
                            eventTemplate: $("#day-event-template").html(),
                        },
                    ],
                    dataSource: kendoData,
                });
            });
        },
    });
});
