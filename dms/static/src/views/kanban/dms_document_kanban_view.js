/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { DocumentKanbanRenderer } from "./dms_document_kanban_renderer";
import { DocumentKanbanController } from "./dms_document_kanban_controller";
import { DocumentSearchModel } from "../search/dms_search_model";

import { FileDropZone, FileUpload } from "../helper/dms_document_upload";

patch(DocumentKanbanRenderer.prototype, "document_kanban_renderer_zone", FileDropZone);
patch(DocumentKanbanController.prototype, "document_kanban_controller_upload", FileUpload);
DocumentKanbanRenderer.template = "dms.KanbanRenderer";

export const DocumentKanbanView = {
    ...kanbanView,
    buttonTemplate: "dms.KanbanButtons",
    SearchModel: DocumentSearchModel,
    Controller: DocumentKanbanController,
    Renderer: DocumentKanbanRenderer
};

registry.category("views").add("document_kanban", DocumentKanbanView);
