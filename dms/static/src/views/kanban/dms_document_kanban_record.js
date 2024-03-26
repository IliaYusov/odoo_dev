/** @odoo-module **/

import {KanbanRecord} from "@web/views/kanban/kanban_record";
import {useService} from "@web/core/utils/hooks";

export class DocumentKanbanRecord extends KanbanRecord {
    setup() {
        super.setup();
        this.messaging = useService("messaging");
        this.dialog = useService("dialog");
    }

    isViewable() {
        return (
            [
                "image/bmp",
                "image/gif",
                "image/jpeg",
                "image/png",
                "image/svg+xml",
                "image/tiff",
                "image/x-icon",
                "application/javascript",
                "application/json",
                "text/css",
                "text/html",
                "text/plain",
                "application/pdf",
                "application/pdf;base64",
                "audio/mpeg",
                "video/x-matroska",
                "video/mp4",
                "video/webm",
            ].includes(this.props.record.data.mimetype)
        );
    };

    onGlobalClick(ev) {
        const self = this;

        if (ev.target.closest(".o_kanban_previewer")) {
            this.messaging.get().then((messaging) => {
                if (this.isViewable()) {
                    const attachmentList = messaging.models.AttachmentList.insert({
                        selectedAttachment: messaging.models.Attachment.insert({
                            id: self.props.record.data.attachment_id[0],
                            filename: self.props.record.data.name,
                            name: self.props.record.data.name,
                            mimetype: self.props.record.data.mimetype,
                            model_name: self.props.record.resModel
                        }),
                    });
                    this.dialog = messaging.models.Dialog.insert({
                        attachmentListOwnerAsAttachmentView: attachmentList,
                    });
                }
            });
            return;
        }
        return super.onGlobalClick(...arguments);
    };
}
