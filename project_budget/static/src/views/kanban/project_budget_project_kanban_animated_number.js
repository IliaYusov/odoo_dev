/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { formatFloat } from "@web/views/fields/formatters";
import { session } from "@web/session";
import { KanbanAnimatedNumber } from "@web/views/kanban/kanban_animated_number";

import { Component } from "@odoo/owl";

export class ProjectKanbanAnimatedNumber extends KanbanAnimatedNumber {
    formattedValue(value) {
        return formatFloat(value);
    }
}

ProjectKanbanAnimatedNumber.template = "project_budget.ProjectKanbanAnimatedNumber";
