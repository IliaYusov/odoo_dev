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
            self.render_tasks_graph();
//            self.render_team_ticket_count_graph();
//            self.render_projects_ticket_graph();
//            self.render_billed_task_team_graph();
//            self.render_team_ticket_done_graph();

        },
        render_tasks_graph: function () {
            var self = this
            var ctx = self.$(".task_done");
            rpc.query({
                model: "task.task",
                method: "get_done_tasks_pie",
            }).then(function (arrays) {
                var data = {
                    labels: ["Done", 'In Progress'],
                    datasets: [{
                        label: "",
                        data: arrays,
                        backgroundColor: [
                            "#665191",
                            "#ff7c43"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#2f4b7c"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
//                var options = {
//                    responsive: true,
//                    title: false,
//                    legend: {
//                        display: true,
//                        position: "right",
//                        labels: {
//                            fontColor: "#333",
//                            fontSize: 16
//                        }
//                    },
//                    scales: {
//                        yAxes: [{
//                            gridLines: {
//                                color: "rgba(0, 0, 0, 0)",
//                                display: false,
//                            },
//                            ticks: {
//                                min: 0,
//                                display: false,
//                            }
//                        }]
//                    }
//                };

                //create Chart class object
                var chart = new Chart(ctx, {
                    type: "doughnut",
                    data: data
//                    options: options
                });
            });
        },
//        render_team_ticket_count_graph: function () {
//            var self = this
//            var ctx = self.$(".team_ticket_count");
//            rpc.query({
//                model: "help.ticket",
//                method: "get_team_ticket_count_pie",
//            }).then(function (arrays) {
//                var data = {
//                    labels: arrays[1],
//                    datasets: [{
//                        label: "",
//                        data: arrays[0],
//                        backgroundColor: [
//                            'rgba(255, 99, 132, 0.2)',
//                            'rgba(255, 159, 64, 0.2)',
//                            'rgba(255, 205, 86, 0.2)',
//                            'rgba(75, 192, 192, 0.2)',
//                            'rgba(54, 162, 235, 0.2)',
//                            'rgba(153, 102, 255, 0.2)',
//                            'rgba(201, 203, 207, 0.2)'
//                        ],
//                        borderColor: ['rgb(255, 99, 132)',
//                            'rgb(255, 159, 64)',
//                            'rgb(255, 205, 86)',
//                            'rgb(75, 192, 192)',
//                            'rgb(54, 162, 235)',
//                            'rgb(153, 102, 255)',
//                            'rgb(201, 203, 207)'
//                        ],
//                        borderWidth: 1
//                    },]
//                };
//
//                //options
//                var options = {
//                    responsive: true,
//                    title: false,
//                    maintainAspectRatio: true,
//                    legend: {
//                        display: false //This will do the task
//                    },
//                    scales: {
//                        yAxes: [{
//                            display: true,
//                            ticks: {
//                                beginAtZero: true,
//                                steps: 10,
//                                stepValue: 5,
//                                // max: 100
//                            }
//                        }]
//                    }
//                };
//
//                //create Chart class object
//                var chart = new Chart(ctx, {
//                    type: "bar",
//                    data: data,
//                    options: options
//                });
//            });
//        },
//
//        render_projects_ticket_graph: function () {
//            var self = this
//            var ctx = self.$(".projects_ticket");
//            rpc.query({
//                model: "help.ticket",
//                method: "get_project_ticket_count",
//            }).then(function (arrays) {
//                var data = {
//                    labels: arrays[1],
//                    datasets: [{
//                        label: "",
//                        data: arrays[0],
//                        backgroundColor: [
//                            "rgba(175,180,255,0.75)",
//                            "rgba(133,208,255,0.9)",
//                            "rgba(113,255,221,0.79)",
//                            "rgba(255,187,95,0.77)",
//                            "#2c7fb8",
//                            "#fa9fb5",
//                            "#2f4b7c",
//                        ],
//                        borderColor: [
//                            "#003f5c",
//                            "#2f4b7c",
//                            "#f95d6a",
//                            "#665191",
//                            "#d45087",
//                            "#ff7c43",
//                            "#ffa600",
//                            "#a05195",
//                            "#6d5c16"
//                        ],
//                        borderWidth: 1
//                    },]
//                };
//
//                  //options
//                var options = {
//                    responsive: true,
//                    title: false,
//                    maintainAspectRatio: true,
//                    legend: {
//                        display: false //This will do the task
//                    },
//                    scales: {
//                        yAxes: [{
//                            display: true,
//                            ticks: {
//                                beginAtZero: true,
//                                steps: 10,
//                                stepValue: 5,
//                                // max: 100
//                            }
//                        }]
//                    }
//                };
//
//                //create Chart class object
//                var chart = new Chart(ctx, {
//                    type: "bar",
//                    data: data,
//                    options: options
//                });
//            });
//        },
//        render_billed_task_team_graph: function () {
//            var self = this
//            var ctx = self.$(".billed_team");
//            rpc.query({
//                model: "help.ticket",
//                method: "get_billed_task_team_chart",
//            }).then(function (arrays) {
//                var data = {
//                    labels: arrays[1],
//                    datasets: [{
//                        label: "",
//                        data: arrays[0],
//                        backgroundColor: [
//                            "#a07fcd",
//                            "#fea84c",
//                            "#2cb8b1",
//                            "#fa9fb5",
//                            "#2f4b7c",
//                            "#2c7fb8"
//                        ],
//                        borderColor: [
//                            "#4fc9ff",
//                            "#2f4b7c",
//                            "#f95d6a",
//                            "#665191",
//                            "#d45087",
//                            "#ff7c43",
//                            "#ffa600",
//                            "#a05195",
//                            "#6d5c16"
//                        ],
//                        borderWidth: 1
//                    },]
//                };
//
//                //options
//                var options = {
//                    responsive: true,
//                    title: false,
//                    legend: {
//                        display: true,
//                        position: "right",
//                        labels: {
//                            fontColor: "#333",
//                            fontSize: 16
//                        }
//                    },
//                    scales: {
//                        yAxes: [{
//                            gridLines: {
//                                color: "rgba(0, 0, 0, 0)",
//                                display: false,
//                            },
//                            ticks: {
//                                min: 0,
//                                display: false,
//                            }
//                        }]
//                    }
//                };
//
//                //create Chart class object
//                var chart = new Chart(ctx, {
//                    type: "polarArea",
//                    data: data,
//                    options: options
//                });
//            });
//        },
//        render_team_ticket_done_graph: function () {
//            var self = this
//            var ctx = self.$(".team_ticket_done");
//            rpc.query({
//                model: "help.ticket",
//                method: "get_team_ticket_done_pie",
//            }).then(function (arrays) {
//                var data = {
//                    labels: arrays[1],
//                    datasets: [{
//                        fill: false,
//                        label: "",
//                        data: arrays[0],
//                        backgroundColor:[
//                            "#b7c1ff",
//                            "#6159ff",
//                            "#c79bff",
//                            "#0095b2"
//                        ],
//                        borderColor:
//                            'rgba(54,162,235,0.49)'
//                        ,
//                        borderWidth: 2
//                    },]
//                };
//
//                //options
//                var options = {
//                    responsive: true,
//                    title: false,
//                    maintainAspectRatio: true,
//                    legend: {
//                        display: false //This will do the task
//                    },
//                    scales: {
//                        yAxes: [{
//                            display: true,
//                            ticks: {
//                                beginAtZero: true,
//                                steps: 10,
//                                stepValue: 5,
//                                // max: 100
//                            }
//                        }]
//                    }
//                };
//
//                //create Chart class object
//                var chart = new Chart(ctx, {
//                    type: "line",
//                    data: data,
//                    options: options
//                });
//            });
//        },

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
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['to_do', 'assigned', 'in_progress']],
                    ['user_ids', 'in', require('web.session').user_id],
                    ['date_deadline', '>', new Date()]
                ],
                context: { default_state: 'to_do' },
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
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'not in', ['done', 'cancel']],
                    ['user_ids', 'in', require('web.session').user_id]
                    ['date_deadline', '<', new Date()]
                ],
                context: {create: false},
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
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['to_do', 'assigned', 'in_progress']],
                    ['write_uid', '=', require('web.session').user_id]
                    ['date_deadline', '>', new Date()]
                ],
                context: { default_state: 'to_do' },
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
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'not in', ['done', 'cancel']],
                    ['write_uid', '=', require('web.session').user_id]
                    ['date_deadline', '<', new Date()]
                ],
                context: {create: false},
                target: 'current'
            });
        }
    });

    core.action_registry.add("document_flow_dashboard", DashBoard);
    return DashBoard;
});
