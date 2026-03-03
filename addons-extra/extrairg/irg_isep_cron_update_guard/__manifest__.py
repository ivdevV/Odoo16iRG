{
    "name": "IRG ISEP Cron Update Guard",
    "version": "16.0.1.0.0",
    "summary": "Skip heavy ISEP cron jobs while module operations are in progress",
    "category": "Technical",
    "author": "iRG",
    "license": "LGPL-3",
    "depends": [
        "web",
        "isep_appointments",
        "isep_payment_cron",
        "isep_payment_cron_extend"
    ],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "irg_isep_cron_update_guard/static/src/js/blocking_process_systray.js",
            "irg_isep_cron_update_guard/static/src/xml/blocking_process_systray.xml",
            "irg_isep_cron_update_guard/static/src/scss/blocking_process_systray.scss"
        ]
    },
    "installable": True,
    "application": False
}
