/** @odoo-module **/

import { loadJS } from "@web/core/assets"
import { registry } from "@web/core/registry"

import { Component, onWillStart, useEffect, useRef } from "@odoo/owl";

export class FinancialIndicatorGraph extends Component {
    setup() {
        this.chart = null;
        this.chartRef = useRef("chartRef");
        onWillStart(async () => {
            await loadJS("/project_budget_reports/static/lib/Chart/chart.umd.js")
        })

        useEffect(() => {
            this.renderChart();
            return () => {
                if (this.chart) {
                    this.chart.destroy();
                }
            };
        });
    }

    renderChart() {
        if (this.chart) {
            this.chart.destroy();
        }

        const innerBarText = {
            id: "innerBarText",
            afterDatasetsDraw(chart, args, pluginOptions) {
                const { ctx, data, chartArea: { left }, scales: { x, y } } = chart;
                ctx.save();
                data.datasets[0].data.forEach((dataPoint, index) => {
                    const amount = dataPoint === undefined ? 0 : dataPoint
                    ctx.font = "bolder 12px sans-serif";
                    ctx.fillStyle = "gray";
                    ctx.fillText(`${amount}`, left + 10, y.getPixelForValue(index));
                });
            }
        };

        this.chart = new Chart(this.chartRef.el,
        {
            type: this.props.type,
            data: {
                labels: [
                    this.props.name
                ],
                datasets: [
                    {
                        axis: 'y',
                        label: 'Fact',
                        data: [this.props.value]
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                },
                scales: {
                    x: {
                        display: false,
                        grid: {
                            display: false
                        },
                        max: this.props.max
                    },
                    y: {
                        display: false
                    }
                }
            },
            plugins: [ innerBarText ]
        });
    }
}

FinancialIndicatorGraph.template = "project_budget.FinancialIndicatorGraph"
