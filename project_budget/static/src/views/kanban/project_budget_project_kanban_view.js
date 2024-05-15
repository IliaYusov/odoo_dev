/** @odoo-module **/

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { ProjectKanbanRenderer } from "./project_budget_project_kanban_renderer";

export const ProjectKanbanView = {
    ...kanbanView,
    Controller: class extends kanbanView.Controller {},
    Renderer: ProjectKanbanRenderer,
};

registry.category("views").add("project_kanban", ProjectKanbanView);
