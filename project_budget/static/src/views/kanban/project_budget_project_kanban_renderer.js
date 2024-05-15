/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { ProjectKanbanAnimatedNumber } from "./project_budget_project_kanban_animated_number";

const { onWillStart } = owl;

export class ProjectKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup();
    }
}

ProjectKanbanRenderer.components = {
    ...KanbanRenderer.components,
    KanbanAnimatedNumber: ProjectKanbanAnimatedNumber,
};

ProjectKanbanRenderer.template = "project_budget.ProjectKanbanRenderer";
