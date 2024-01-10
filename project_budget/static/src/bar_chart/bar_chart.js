/** @odoo-module */

import { loadJS } from "@web/core/assets";
import { getColor } from "@web/views/graph/colors";

const { Component, onWillStart, useRef, onMounted, onWillUnmount } = owl;

export class BarChart extends Component {
    setup() {
        this.canvasRef = useRef("canvas");

        this.labels = this.props.data[0];
        this.data = this.props.data[1];
        this.color = this.props.data[2];

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
                legend: {
                    display: false,
                    labels: {
                        fontColor: 'rgb(255, 99, 132)'
                    }
                },
                tooltips: {
                    enabled: false,
                },
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
