/** @odoo-module **/

import session from "web.session";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { WorkplaceEmployeeDashboard } from "@workplace_employee/components/workplace_employee_dashboard/workplace_employee_dashboard";

const { useState, onWillStart } = owl;

var rpc = require('web.rpc');

patch(WorkplaceEmployeeDashboard.prototype, "workplace_employee_project_budget.WorkplaceEmployeeProjectBudgetDashboard", {
    setup() {
        this._super(...arguments);
        this.state.projectInfo = null;
    },

    async _fetchData() {
        await this._super(...arguments);
        this.is_project_budget_user = await session.user_has_group("project_budget.project_budget_users") || await session.user_has_group("project_budget.project_budget_admin");
        if (this.is_project_budget_user) {
            await this._fetchProjectInfoData();
        }
    },

    async _fetchProjectInfoData() {
        this.state.projectInfo = await this.orm.call(
            "project_budget.projects",
            "retrieve_dashboard",
            [],
            {
                context: session.user_context
            }
        );
    },

    openOverdueProjectReport() {
        this.action.doAction({
            name: _t("Overdue Projects"),
            type: "ir.actions.act_window",
            res_model: "project.budget.project.overdue.report",
            view_mode: "tree,form",
            views: [[false, "tree"], [false, "form"]],
            context: {
                ...session.context
            },
            target: "current"
        });
    },

    createProject() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "project_budget.projects",
            view_mode: "form",
            views: [[false, "form"]],
            context: {
                ...session.context
            },
            target: "current"
        });
    },

    viewProject(projectId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "project_budget.projects",
            res_id: parseInt(projectId),
            view_mode: "form",
            views: [[false, "form"]],
            context: {
                ...session.context
            },
            target: "current"
        });
    },

    viewStep(stepId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "project_budget.steps",
            res_id: parseInt(stepId),
            view_mode: "form",
            views: [[false, "form"]],
            context: {
                ...session.context
            },
            target: "current"
        });
    }
})
