odoo.define("document_flow_dashboard.dashboard_view", function (require) {
    "use strict";

    const AbstractAction = require("web.AbstractAction");
    const core = require("web.core");
    const rpc = require("web.rpc");
    var ajax = require("web.ajax");
    const _t = core._t;
    const QWeb = core.qweb;
    const DashBoard = AbstractAction.extend({
        template: "DocumentFlowDashboard",
        events: {
            "click .my_to_do_tasks": "my_tasks_to_do",
            "click .my_overdue_tasks": "my_tasks_overdue",
            "click .by_me_to_do_tasks": "by_me_tasks_to_do",
            "click .by_me_overdue_tasks": "by_me_tasks_overdue",
        },
        init: function (parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['DocumentFlowDashboard'];
        },
        start: function () {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.render_dashboards();
                self.render_graphs();
                self.$el.parent().addClass('oe_background_grey');
            });

        },
        render_graphs: function () {
            var self = this;
//            self.render_tasks_graph();
//            self.render_team_ticket_count_graph();
//            self.render_projects_ticket_graph();
//            self.render_billed_task_team_graph();
//            self.render_team_ticket_done_graph();

        },

        render_dashboards: function () {
            var self = this;
            var templates = ['DashBoardDocumentFlow'];
            _.each(templates, function (template) {
                self.$('.document_flow_dashboard_main').append(QWeb.render(template, {widget: self}));
            });

            rpc.query({
                model: "task.task",
                method: "get_tasks_count",
                args: [],
            })
                .then(function (result) {
                    $("#my_to_do_count").append("<span class='stat-digit'>" + result.my_to_do_count + "</span>");
                    $("#my_overdue_count").append("<span class='stat-digit'>" + result.my_overdue_count + "</span>");
                    $("#by_me_to_do_count").append("<span class='stat-digit'>" + result.by_me_to_do_count + "</span>");
                    $("#by_me_overdue_count").append("<span class='stat-digit'>" + result.by_me_overdue_count + "</span>");

                    ajax.jsonRpc("/document_flow/tasks", "call", {}).then(function (values) {
                        $('.pending_tasks').append(values);
                    });

                });
        },

        my_tasks_to_do: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t("Assigned To Me"),
                type: 'ir.actions.act_window',
                res_model: 'task.task',
                view_mode: 'kanban,tree,form',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                domain: [
                    ['parent_ref_type', 'like', 'document_flow.%'],
                    ['is_closed', '=', false],
                    ['user_id', 'in', require('web.session').user_id],
                    ['date_deadline', '>=', new Date()]
                ],
                context: {'default_parent_ref_type': 'document_flow.%'},
                target: 'current'
            });
        },

        my_tasks_overdue: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t("Overdue"),
                type: 'ir.actions.act_window',
                res_model: 'task.task',
                view_mode: 'kanban,tree,form',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                domain: [
                    ['parent_ref_type', 'like', 'document_flow.%'],
                    ['is_closed', '=', false],
                    ['user_id', 'in', require('web.session').user_id],
                    ['date_deadline', '<', new Date()]
                ],
                context: {'default_parent_ref_type': 'document_flow.%'},
                target: 'current'
            });
        },

        by_me_tasks_to_do: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t("Created By Me"),
                type: 'ir.actions.act_window',
                res_model: 'task.task',
                view_mode: 'kanban,tree,form',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                domain: [
                    ['parent_ref_type', 'like', 'document_flow.%'],
                    ['is_closed', '=', false],
                    ['author_id', 'in', require('web.session').user_id],
                    ['date_deadline', '>=', new Date()]
                ],
                context: {'default_parent_ref_type': 'document_flow.%'},
                target: 'current'
            });
        },

        by_me_tasks_overdue: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t("Created By Me Overdue"),
                type: 'ir.actions.act_window',
                res_model: 'task.task',
                view_mode: 'kanban,tree,form',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                domain: [
                    ['parent_ref_type', 'like', 'document_flow.%'],
                    ['is_closed', '=', false],
                    ['author_id', 'in', require('web.session').user_id],
                    ['date_deadline', '<', new Date()]
                ],
                context: {'default_parent_ref_type': 'document_flow.%'},
                target: 'current'
            });
        }
    });

    core.action_registry.add("document_flow_dashboard", DashBoard);
    return DashBoard;
});
