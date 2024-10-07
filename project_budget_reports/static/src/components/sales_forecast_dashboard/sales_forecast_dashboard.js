/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { sprintf } from "@web/core/utils/strings";

import { registry } from "@web/core/registry"
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { FinancialIndicator } from "../financial_indicator/financial_indicator";
import { FinancialIndicatorGraph } from "../financial_indicator_graph/financial_indicator_graph";
import { Layout } from "@web/search/layout";

const { Component, useState, useRef, onWillStart } = owl;
const { DateTime } = luxon;

export class SalesForecastDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.session = session;
        this.state = useState({
            options: {},
            data: [],
        });

        onWillStart(async () => {
            await this.loadOptions();
            await this.getDashboardData();
        })
    }

    async loadOptions(previous_options=null) {
        this.state.options = await this.orm.call(
            "project.budget.report.sales.forecast",
            "get_options",
            [previous_options],
            {
                context: session.user_context
            }
        );
        this.periodFilter = this.initPeriodFilters();
    }

    async getDashboardData() {
        this.state.data = await this.orm.call(
            "project.budget.report.sales.forecast",
            "retrieve_dashboard",
            [this.state.options],
            {
                context: session.user_context
            }
        );
    }

    periodFilters() {
        return [
//            {"name": _t("Month"), "period": "month"},
//            {"name": _t("Quarter"), "period": "quarter"},
            { "name": _t("Year"), "period": "year" }
        ];
    }

    initPeriodFilters() {
        const filters = {
            "month": 0,
            "quarter": 0,
            "year": 0,
        };
        filters[this.state.options.date.period_type] = this.state.options.date.period;
        return filters;
    }

    selectPreviousPeriod(periodType) {
        this._changePeriod(periodType, -1);
    }

    selectNextPeriod(periodType) {
        this._changePeriod(periodType, 1);
    }

    _changePeriod(periodType, increment) {
        this.periodFilter[periodType] = this.periodFilter[periodType] + increment;
        this.updateOption("date.period", this.periodFilter[periodType]);
        this.applyFilters();
    }

    displayPeriod(periodType) {
        const dateTo = DateTime.now();

        switch (periodType) {
            case "month":
                return this._displayMonth(dateTo);
            case "quarter":
                return this._displayQuarter(dateTo);
            case "year":
                return this._displayYear(dateTo);
            default:
                throw new Error(`Invalid period type in displayPeriod(): ${ periodType }`);
        }
    }

    _displayMonth(dateTo) {
        return dateTo.plus({ months: this.periodFilter.month }).toFormat("MMMM yyyy");
    }

    _displayQuarter(dateTo) {
        dateTo = dateTo.plus({ months: this.periodFilter.quarter * 3 });

        return `Q${dateTo.quarter} ${dateTo.year}`;
    }

    _displayYear(dateTo) {
        return dateTo.plus({ years: this.periodFilter.year }).toFormat("yyyy");
    }

    async applyFilters() {
        await this.loadOptions(this.state.options);
        await this.getDashboardData();
    }

    roundingUnitName(roundingUnit) {
        return sprintf(_t("In %s"), this.state.options["rounding_unit_names"][roundingUnit]);
    }

    async filterRoundingUnit(rounding) {
        await this.updateOption("rounding_unit", rounding);

        this.state.data = await this.orm.call(
            "project.budget.report.sales.forecast",
            "format_data_values",
            [
                this.state.options,
                this.state.data
            ]
        );
    }

    async updateOption(optionPath, optionValue) {
        await this._updateOption("update", optionPath, optionValue);
    }

    async _updateOption(operationType, optionPath, optionValue=null) {
        const optionKeys = optionPath.split(".");

        let currentOptionKey = null;
        let option = this.state.options;

        while (optionKeys.length > 1) {
            currentOptionKey = optionKeys.shift();
            option = option[currentOptionKey];

            if (option  === undefined)
                throw new Error(`Invalid option key in _updateOption(): ${ currentOptionKey } (${ optionPath })`);
        }

        switch (operationType) {
            case "update":
                option[optionKeys[0]] = optionValue;
                break;
            case "delete":
                delete option[optionKeys[0]];
                break;
            default:
                throw new Error(`Invalid operation type in _updateOption(): ${ operationType }`);
        }
    }

    async exportXlsx() {

        const action = await this.orm.call(
            "project.budget.report.sales.forecast.excel",
            "generate_xlsx_report",
            [this.state.data, this.state.options]
        );

        const result = await this.action.doAction(action);
    }
}

SalesForecastDashboard.template = "project_budget_reports.SalesForecastDashboard";
SalesForecastDashboard.components = {
    Dropdown,
    DropdownItem,
    FinancialIndicator,
    FinancialIndicatorGraph,
    Layout
};

registry.category("actions").add("sales_forecast_dashboard", SalesForecastDashboard)
