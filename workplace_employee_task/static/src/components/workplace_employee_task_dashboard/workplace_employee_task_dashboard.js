/** @odoo-module **/

import { session } from '@web/session';
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { WorkplaceEmployeeDashboard } from "@workplace_employee/components/workplace_employee_dashboard/workplace_employee_dashboard";

const { useState, onWillStart } = owl;

var rpc = require('web.rpc');

patch(WorkplaceEmployeeDashboard.prototype, "workplace_employee_task.WorkplaceEmployeeTaskDashboard", {
    setup() {
        this._super(...arguments);
        this.state.taskInfo = null;
    },

    async _fetchData() {
        await this._super(...arguments);
        await this._fetchEmployeeTaskInfoData();
    },

    async _fetchEmployeeTaskInfoData() {
        this.state.taskInfo = await this.orm.call(
            "task.task",
            "get_tasks_count",
            [],
            {
                context: session.user_context
            }
        );
    },

    viewMyTasksToDo() {
        this.action.doAction({
            name: _t("Assigned To Me"),
            type: "ir.actions.act_window",
            res_model: "task.task",
            view_mode: "kanban,tree,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [
                ["is_closed", "=", false],
                "|", ["user_ids", "=", session.user_id], ["user_ids", "in", this.state.employeeInfo.replaceable_ids],
                ["date_deadline", ">=", new Date()]
            ],
            context: {
                ...session.context
            },
            target: "current"
        });
    },

    viewMyTasksOverdue() {
        this.action.doAction({
            name: _t("Overdue"),
            type: "ir.actions.act_window",
            res_model: "task.task",
            view_mode: "kanban,tree,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [
                ["is_closed", "=", false],
                "|", ["user_ids", "=", session.user_id], ["user_ids", "in", this.state.employeeInfo.replaceable_ids],
                ["date_deadline", "<", new Date()]
            ],
            context: {
                ...session.context
            },
            target: "current"
        });
    },

    viewByMeTasksToDo() {
        this.action.doAction({
            name: _t("Created By Me"),
            type: "ir.actions.act_window",
            res_model: "task.task",
            view_mode: "kanban,tree,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [
                ["is_closed", "=", false],
                ["author_id", "=", session.user_id],
                ["date_deadline", ">=", new Date()]
            ],
            context: {
                ...session.context
            },
            target: 'current'
        });
    },

    viewByMeTasksOverdue() {
        this.action.doAction({
            name: _t("Created By Me Overdue"),
            type: "ir.actions.act_window",
            res_model: "task.task",
            view_mode: "kanban,tree,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [
                ["is_closed", "=", false],
                ["author_id", "=", session.user_id],
                ["date_deadline", "<", new Date()]
            ],
            context: {
                ...session.context
            },
            target: 'current'
        });
    },

    viewGroupTasksToDo() {
        rpc.query({
            model: "workflow.group.executors",
            method: "search",
            args: [[["member_ids", "in", session.user_id]], []]
        }).then(groups => {
            this.action.doAction({
                name: _t("Assigned To Group"),
                type: "ir.actions.act_window",
                res_model: "task.task",
                view_mode: "kanban,tree,form",
                views: [[false, "kanban"], [false, "list"], [false, "form"]],
                domain: [
                    ["is_closed", "=", false],
                    ["date_deadline", ">=", new Date()],
                    ["user_ids", "=", false],
                    ["group_executors_id", "in", groups]
                ],
                target: "current"
            });
        })
    },

    viewGroupTasksOverdue() {
        rpc.query({
            model: "workflow.group.executors",
            method: "search",
            args: [[["member_ids", "in", session.user_id]], []]
        }).then(groups => {
            this.action.doAction({
                name: _t("Group Overdue"),
                type: "ir.actions.act_window",
                res_model: "task.task",
                view_mode: "kanban,tree,form",
                views: [[false, "kanban"], [false, "list"], [false, "form"]],
                domain: [
                    ["is_closed", "=", false],
                    ["date_deadline", "<", new Date()],
                    ["user_ids", "=", false],
                    ["group_executors_id", "in", groups]
                ],
                target: "current"
            });
        })
    },

    viewSubordinatesTasksToDo() {
        this.action.doAction({
            name: _t("Tasks Of Subordinates"),
            type: "ir.actions.act_window",
            res_model: "task.task",
            view_mode: "kanban,tree,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [
                ["is_closed", "=", false],
                ["user_ids", "in", this.state.employeeInfo.subordinate_ids],
                ["date_deadline", ">=", new Date()]
            ],
            context: {
                ...session.context
            },
            target: "current"
        });
    },

    viewSubordinatesTasksOverdue() {
        this.action.doAction({
            name: _t("Overdue Tasks Of Subordinates"),
            type: "ir.actions.act_window",
            res_model: "task.task",
            view_mode: "kanban,tree,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [
                ["is_closed", "=", false],
                ["user_ids", "in", this.state.employeeInfo.subordinate_ids],
                ["date_deadline", "<", new Date()]
            ],
            context: {
                ...session.context
            },
            target: "current"
        });
    }
})
