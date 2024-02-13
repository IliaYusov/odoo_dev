/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { getDefaultConfig } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { Domain } from "@web/core/domain";
import { Card } from "./card/card";
import { PieChart } from "./pie_chart/pie_chart";
import { BarChart } from "./bar_chart/bar_chart";

const { Component, useSubEnv, onWillStart, useState } = owl;

class ProjectBudgetDashboard extends Component {
    setup() {

        // The useSubEnv below can be deleted if you're > 16.0
        useSubEnv({
            config: {
                ...getDefaultConfig(),
                ...this.env.config,
            },
        });

        this.state = useState({
            period: 'Y',
            type: 'summary',
            year: new Date().getFullYear(),
            office: false,
            allowed_companies: false,
        });

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
            console.log(this)
            if (this.props.action.context.office) {
                this.state.office = this.props.action.context.office;
            }
            if (this.props.action.context.period) {
                this.state.period = this.props.action.context.period;
            }
            if (this.props.action.context.type) {
                this.state.type = this.props.action.context.type;
            }
            if (this.props.action.context.year) {
                this.state.year = this.props.action.context.year;
            }
            this.state.allowed_companies = require('web.session').user_context.allowed_company_ids
        });
    }

    async getQuotations(){
    }

    async onChangePeriod(){
        this.props.action.context.period = this.state.period
    }

    async onChangeType(){
        this.props.action.context.type = this.state.type
    }

    async onChangeYear(){
        this.props.action.context.year = this.state.year
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

//    openCompanyDashboard(title, domain) {
//        this.action.doAction({
//            type: "ir.actions.client",
//            name: "Project Budget Dashboard",
//            tag: "project_budget.dashboard",
//            target: "main",
//            context: {
//            'office': false,
//            'type': this.state.type,
//            'period': this.state.period,
//            'year': this.state.year,
//            },
//        });
//    }

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

ProjectBudgetDashboard.components = { Layout, Card, PieChart, BarChart };
ProjectBudgetDashboard.template = "project_budget.dashboard_template";

registry.category("actions").add("project_budget.dashboard", ProjectBudgetDashboard);