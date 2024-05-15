/** @odoo-module **/

import { registry } from "@web/core/registry"
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";

const { Component, useState, onWillStart } = owl;

export class WorkplaceEmployeeDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.session = session;
        this.state = useState({
            employeeInfo: null,
        });

        onWillStart(this.onWillStart);
    }

    async onWillStart() {
        await this._fetchData();
    }

    async _fetchData() {
        await this._fetchEmployeeInfoData()
    }

    async _fetchEmployeeInfoData() {
        this.state.employeeInfo = await this.orm.call(
            "hr.employee",
            "get_user_employee_info",
            [],
            {
                context: session.user_context
            }
        );
    }

    async openProfile() {
        const actionDescription = await this.orm.call("res.users", "action_get", [], {
            context: { from_workplace: true },
        });
        actionDescription.res_id = session.user_id[0];
        this.action.doAction(actionDescription);
    }
}

WorkplaceEmployeeDashboard.components = {
};
WorkplaceEmployeeDashboard.template = "EmployeeDashboard";

registry.category("actions").add("workplace_employee_dashboard", WorkplaceEmployeeDashboard)
