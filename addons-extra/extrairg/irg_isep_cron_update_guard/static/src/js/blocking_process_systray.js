/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillStart, onWillUnmount, useState } from "@odoo/owl";

class IrgBlockingProcessSystray extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            blocking: false,
            title: "No blocking process",
        });
        this.intervalId = null;

        onWillStart(async () => {
            await this._refreshStatus();
        });

        onMounted(() => {
            this.intervalId = setInterval(() => this._refreshStatus(), 2000);
        });

        onWillUnmount(() => {
            if (this.intervalId) {
                clearInterval(this.intervalId);
            }
        });
    }

    async _refreshStatus() {
        try {
            const result = await this.rpc("/irg/blocking_process/status", {});
            this.state.blocking = !!result.blocking;
            this.state.title = result.blocking
                ? `Blocking process running (${(result.sources || []).join(", ")})`
                : "No blocking process";
        } catch (_error) {
            this.state.blocking = true;
            this.state.title = "Status unavailable";
        }
    }

    get dotClass() {
        return this.state.blocking ? "o_irg_blocking_dot is-red" : "o_irg_blocking_dot is-green";
    }
}

IrgBlockingProcessSystray.template = "irg_isep_cron_update_guard.BlockingProcessSystray";

registry.category("systray").add("irg_blocking_process_systray", { Component: IrgBlockingProcessSystray }, { sequence: 20 });
