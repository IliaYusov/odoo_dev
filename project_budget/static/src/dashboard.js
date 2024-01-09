/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { getDefaultConfig } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { Domain } from "@web/core/domain";
import { Card } from "./card/card";
import { PieChart } from "./pie_chart/pie_chart";
import { Counter } from "./counter/counter";
import { TodoList } from "./todo_list/todo_list";

const { Component, useSubEnv, onWillStart } = owl;

class ProjectBudgetDashboard extends Component {
    setup() {

        // The useSubEnv below can be deleted if you're > 16.0
        useSubEnv({
            config: {
                ...getDefaultConfig(),
                ...this.env.config,
            },
        });

        this.todo = { id: 3, description: "buy milk", done: false };

        this.display = {
            controlPanel: { "top-right": false, "bottom-right": false },
        };

        this.action = useService("action");
        this.project_budget_service = useService("project_budget_service");

        this.keyToString = {
            contracting_total_plan: "Contracting Total Plan",
        };
        onWillStart(async () => {
            this.statistics = await this.project_budget_service.loadStatistics();
        });
    }

    openCustomerView() {
        this.action.doAction("base.action_partner_form");
    }

    openOrders(title, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: "project_budget.projects",
            domain: new Domain(domain).toList(),
            views: [
                [false, "list"],
                [false, "form"],
            ],
        });
    }
    openLast7DaysOrders() {
        const domain =
            "[('create_date','>=', (context_today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d'))]";
        this.openOrders("Last 7 days orders", domain);
    }

    openLast7DaysCancelledOrders() {
        const domain =
            "[('specification_state','=', 'cancel')]";
        this.openOrders("Cancelled orders", domain);
    }
}

ProjectBudgetDashboard.components = { Layout, Card, Counter, TodoList, PieChart };
ProjectBudgetDashboard.template = "project_budget.clientaction";

registry.category("actions").add("project_budget.dashboard", ProjectBudgetDashboard);