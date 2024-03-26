/** @odoo-module */

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";

import { DocumentKanbanRecord } from "./dms_document_kanban_record";
import { DocumentAttachmentViewer } from "../helper/dms_attachment_viewer";

export class DocumentKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup();
    }
}

DocumentKanbanRenderer.components = {
    ...KanbanRenderer.components,
    KanbanRecord: DocumentKanbanRecord,
    DocumentAttachmentViewer
};
