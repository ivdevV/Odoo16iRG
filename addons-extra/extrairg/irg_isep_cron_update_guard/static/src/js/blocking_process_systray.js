/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillStart, onWillUnmount, useState } from "@odoo/owl";

const YELLOW_TRANSITION_MS = 20000;

class IrgBlockingProcessSystray extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            blocking: false,
            title: "No blocking process",
            dotStatus: "green", // green | yellow | red
        });
        this.intervalId = null;
        this.yellowTimerId = null;
        this.lastServerBlocking = false;

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
            if (this.yellowTimerId) {
                clearTimeout(this.yellowTimerId);
            }
        });
    }

    _setRed(title) {
        if (this.yellowTimerId) {
            clearTimeout(this.yellowTimerId);
            this.yellowTimerId = null;
        }
        this.state.dotStatus = "red";
        this.state.blocking = true;
        this.state.title = title;
    }

    _startYellowTransition() {
        if (this.state.dotStatus === "yellow") {
            return;
        }
        if (this.yellowTimerId) {
            clearTimeout(this.yellowTimerId);
        }

        this.state.dotStatus = "yellow";
        this.state.blocking = false;
        this.state.title = "Blocking process ended, waiting 20s before green status";

        this.yellowTimerId = setTimeout(() => {
            this.yellowTimerId = null;
            // Only switch to green if server is still non-blocking.
            if (!this.lastServerBlocking) {
                this.state.dotStatus = "green";
                this.state.blocking = false;
                this.state.title = "No blocking process";
            }
        }, YELLOW_TRANSITION_MS);
    }

    async _refreshStatus() {
        try {
            const result = await this.rpc("/irg/blocking_process/status", {});
            const isBlocking = !!result.blocking;
            this.lastServerBlocking = isBlocking;

            if (isBlocking) {
                const title = `Blocking process running (${(result.sources || []).join(", ")})`;
                this._setRed(title);
                return;
            }

            // Mandatory transition: red -> yellow(10s) -> green
            if (this.state.dotStatus === "red") {
                this._startYellowTransition();
                return;
            }

            // Keep current non-red state if no new blocking process.
            if (!this.yellowTimerId) {
                this.state.dotStatus = "green";
                this.state.blocking = false;
                this.state.title = "No blocking process";
            }
        } catch (_error) {
            this.lastServerBlocking = true;
            this._setRed("Status unavailable");
        }
    }

    get dotClass() {
        if (this.state.dotStatus === "red") {
            return "o_irg_blocking_dot is-red";
        }
        if (this.state.dotStatus === "yellow") {
            return "o_irg_blocking_dot is-yellow";
        }
        return "o_irg_blocking_dot is-green";
    }
}

IrgBlockingProcessSystray.template = "irg_isep_cron_update_guard.BlockingProcessSystray";

registry.category("systray").add("irg_blocking_process_systray", { Component: IrgBlockingProcessSystray }, { sequence: 20 });
