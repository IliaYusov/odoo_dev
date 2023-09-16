odoo.define("project_budget_dashboard.ProjectBudgetDashboard", function (require) {
    "use strict";

    const AbstractAction = require("web.AbstractAction");
    const core = require("web.core");
    const rpc = require("web.rpc");
    var ajax = require("web.ajax");
    const _t = core._t;
    const QWeb = core.qweb;
    const DashBoard = AbstractAction.extend({
        template: "ProjectBudgetDashboard",
        events: {
            "click .canceled": "canceled_projects",
            "click .potential": "potential_projects",
            "click .opportunity": "opportunity_projects",
            "click .reserve": "reserve_projects",
            "click .commitment": "commitment_projects",
            "click .execution": "execution_projects",
            "click .done": "done_projects"
        },
        init: function (parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['ProjectBudgetDashboard'];
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
        },

        render_dashboards: function () {
            var self = this;
            var templates = ['ProjectDashboard'];
            _.each(templates, function (template) {
                self.$('.o_pb_dashboard').append(QWeb.render(template, {widget: self}));
            });

            rpc.query({
                model: "project_budget.projects",
                method: "get_projects",
                args: [require('web.session').user_context.allowed_company_ids]
            }).then(function (result) {
                $("#canceled_count").append("<span class='stat-digit'>" + result.canceled_count + "</span>");
                $("#canceled_revenue").append("<span class='stat-digit'>" + result.canceled_revenue + "</span>");
                $("#canceled_cost").append("<span class='stat-digit'>" + result.canceled_cost + "</span>");
                $("#canceled_margin").append("<span class='stat-digit'>" + result.canceled_margin + "</span>");
                $("#potential_count").append("<span class='stat-digit'>" + result.potential_count + "</span>");
                $("#potential_revenue").append("<span class='stat-digit'>" + result.potential_revenue + "</span>");
                $("#potential_cost").append("<span class='stat-digit'>" + result.potential_cost + "</span>");
                $("#potential_margin").append("<span class='stat-digit'>" + result.potential_margin + "</span>");
                $("#opportunity_count").append("<span class='stat-digit'>" + result.opportunity_count + "</span>");
                $("#opportunity_revenue").append("<span class='stat-digit'>" + result.opportunity_revenue + "</span>");
                $("#opportunity_cost").append("<span class='stat-digit'>" + result.opportunity_cost + "</span>");
                $("#opportunity_margin").append("<span class='stat-digit'>" + result.opportunity_margin + "</span>");
                $("#reserve_count").append("<span class='stat-digit'>" + result.reserve_count + "</span>");
                $("#reserve_revenue").append("<span class='stat-digit'>" + result.reserve_revenue + "</span>");
                $("#reserve_cost").append("<span class='stat-digit'>" + result.reserve_cost + "</span>");
                $("#reserve_margin").append("<span class='stat-digit'>" + result.reserve_margin + "</span>");
                $("#commitment_count").append("<span class='stat-digit'>" + result.commitment_count + "</span>");
                $("#commitment_revenue").append("<span class='stat-digit'>" + result.commitment_revenue + "</span>");
                $("#commitment_cost").append("<span class='stat-digit'>" + result.commitment_cost + "</span>");
                $("#commitment_margin").append("<span class='stat-digit'>" + result.commitment_margin + "</span>");
                $("#execution_count").append("<span class='stat-digit'>" + result.execution_count + "</span>");
                $("#execution_revenue").append("<span class='stat-digit'>" + result.execution_revenue + "</span>");
                $("#execution_cost").append("<span class='stat-digit'>" + result.execution_cost + "</span>");
                $("#execution_margin").append("<span class='stat-digit'>" + result.execution_margin + "</span>");
                $("#done_count").append("<span class='stat-digit'>" + result.done_count + "</span>");
                $("#done_revenue").append("<span class='stat-digit'>" + result.done_revenue + "</span>");
                $("#done_cost").append("<span class='stat-digit'>" + result.done_cost + "</span>");
                $("#done_margin").append("<span class='stat-digit'>" + result.done_margin + "</span>");
            });
        },

        canceled_projects: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t('Canceled'),
                type: 'ir.actions.act_window',
                res_model: 'project_budget.projects',
                view_mode: 'tree,form,pivot',
                views: [[false, 'list'], [false, 'form'], [false, 'pivot']],
                domain: [
                    ['budget_state', '=', 'work'],
                    ['estimated_probability_id.code', '=', '0']
                ],
                target: 'current'
            });
        },
        potential_projects: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t('Potential'),
                type: 'ir.actions.act_window',
                res_model: 'project_budget.projects',
                view_mode: 'tree,form,pivot',
                views: [[false, 'list'], [false, 'form'], [false, 'pivot']],
                domain: [
                    ['budget_state', '=', 'work'],
                    ['estimated_probability_id.code', '=', '1']
                ],
                target: 'current'
            });
        },
        opportunity_projects: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t('Opportunity'),
                type: 'ir.actions.act_window',
                res_model: 'project_budget.projects',
                view_mode: 'tree,form,pivot',
                views: [[false, 'list'], [false, 'form'], [false, 'pivot']],
                domain: [
                    ['budget_state', '=', 'work'],
                    ['estimated_probability_id.code', '=', '2']
                ],
                target: 'current'
            });
        },
        reserve_projects: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t('Reserve'),
                type: 'ir.actions.act_window',
                res_model: 'project_budget.projects',
                view_mode: 'tree,form,pivot',
                views: [[false, 'list'], [false, 'form'], [false, 'pivot']],
                domain: [
                    ['budget_state', '=', 'work'],
                    ['estimated_probability_id.code', '=', '3']
                ],
                target: 'current'
            });
        },
        commitment_projects: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t('Commitment'),
                type: 'ir.actions.act_window',
                res_model: 'project_budget.projects',
                view_mode: 'tree,form,pivot',
                views: [[false, 'list'], [false, 'form'], [false, 'pivot']],
                domain: [
                    ['budget_state', '=', 'work'],
                    ['estimated_probability_id.code', '=', '4']
                ],
                target: 'current'
            });
        },
        execution_projects: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t('Execution'),
                type: 'ir.actions.act_window',
                res_model: 'project_budget.projects',
                view_mode: 'tree,form,pivot',
                views: [[false, 'list'], [false, 'form'], [false, 'pivot']],
                domain: [
                    ['budget_state', '=', 'work'],
                    ['estimated_probability_id.code', '=', '5']
                ],
                target: 'current'
            });
        },
        done_projects: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t('Done'),
                type: 'ir.actions.act_window',
                res_model: 'project_budget.projects',
                view_mode: 'tree,form,pivot',
                views: [[false, 'list'], [false, 'form'], [false, 'pivot']],
                domain: [
                    ['budget_state', '=', 'work'],
                    ['estimated_probability_id.code', '=', '6']
                ],
                target: 'current'
            });
        }
    });

    core.action_registry.add("project_budget_dashboard", DashBoard);
    return DashBoard;
});
