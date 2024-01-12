/** @odoo-module */

import { loadJS } from "@web/core/assets";
import { getColor } from "@web/views/graph/colors";
import { useService } from "@web/core/utils/hooks"

const { Component, onWillStart, useRef, onMounted, useEffect, onWillUnmount } = owl;

export class PieChart extends Component {
    setup() {
        this.canvasRef = useRef("canvas");

        this.data = this.props.data[this.props.type][this.props.period][0];
        this.color = this.props.data[this.props.type][this.props.period][1];
        this.labels = this.props.data[this.props.type][this.props.period][2];

        onWillStart(() => {
            return loadJS(["/web/static/lib/Chart/Chart.js"]);
        });

        onMounted(() => {
            this.renderChart();
        });

        useEffect(() => {
            this.renderChart()
        }, () => [this.props.period, this.props.type]
           );

        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });

        this.actionService = useService("action")
    }

    renderChart() {
        if (this.chart) {
            this.chart.destroy();
        }
        this.chart = new Chart(this.canvasRef.el, {
            type: "doughnut",
            data: {
                labels: this.labels,
                datasets: [
                    {
                        label: this.props.label,
                        data: this.data,
                        backgroundColor: this.color,
                    },
                ],
            },
            options: {
                onClick: (e) => {
                    this.actionService.doAction({
                        type: "ir.actions.act_window",
                        name: this.props.title,
                        res_model: "project_budget.projects",
                        views: [
                            [false, "list"],
                            [false, "form"],
                        ],
                    })
                },

                legend: {
                    display: false,
                    labels: {
                        fontColor: 'rgb(255, 99, 132)'
                    }
                },

                tooltips: {
                    enabled: false,
                }
            }
        });
    }
}

PieChart.template = "project_budget.PieChart";
