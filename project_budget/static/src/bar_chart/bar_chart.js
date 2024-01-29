/** @odoo-module */

import { loadJS } from "@web/core/assets";
import { getColor } from "@web/views/graph/colors";
import { useService } from "@web/core/utils/hooks"
import { Domain } from "@web/core/domain";

const { Component, onWillStart, useRef, onMounted, onWillUnmount } = owl;

export class BarChart extends Component {
    setup() {
        this.canvasRef = useRef("canvas");

//        this.labels = this.props.data[0];
//        this.data = this.props.data[1];
//        this.color = this.props.data[2];

        this.data = this.props.data[this.props.type][this.props.period][1];
        this.color = this.props.data[this.props.type][this.props.period][2];
        this.labels = this.props.data[this.props.type][this.props.period][0];

        onWillStart(() => {
            return loadJS(["/web/static/lib/Chart/Chart.js"]);
        });

        onMounted(() => {
            this.renderChart();
        });

        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });
        this.actionService = useService("action")
    }

    onPieClick(ev, chartElem) {
        if (chartElem[0]) {
            const clickedIndex = chartElem[0]._index;
            const kam = this.labels[clickedIndex];
            this.actionService.doAction({
                type: "ir.actions.act_window",
                name: kam,
                res_model: "project_budget.projects",
                domain: new Domain("[('project_manager_id.name','=','" + kam + "'),('budget_state', '=', 'work')]").toList(),
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
            })
        }
    }

    renderChart() {
        if (this.chart) {
            this.chart.destroy();
        }
        this.chart = new Chart(this.canvasRef.el, {
            type: "horizontalBar",
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
                onClick: this.onPieClick.bind(this),
                legend: {
                    display: false,
                    labels: {
                        fontColor: 'rgb(255, 99, 132)'
                    }
                },
//                tooltips: {
//                    enabled: false,
//                },
                scales: {
                    xAxes: [{
                        ticks: {
                            max: 140,
                            min: 0,
                            stepSize: 20,
                            beginAtZero: true,
                        }
                    }]
                },
            }

        });
    }
}

BarChart.template = "project_budget.BarChart";
