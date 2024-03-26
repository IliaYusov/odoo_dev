/** @odoo-module **/

import "@mail/components/attachment_viewer/attachment_viewer";
import { getMessagingComponent } from "@mail/utils/messaging_component";

const { Component, useEffect, useRef, useState } = owl;

export class DmsAttachmentViewer extends Component {
    setup() {
        this.root = useRef("root");
        this.state = useState({
            topOffset: 0,
        });
        this.previewState = useState(this.env.documentsView.previewStore);

        const onKeydown = this.onIframeKeydown.bind(this);
        useEffect(
            (iframe) => {
                if (!iframe) {
                    return;
                }
                const onLoad = () => {
                    if (!iframe.contentDocument) {
                        return;
                    }
                    iframe.contentDocument.addEventListener("keydown", onKeydown);
                };
                iframe.addEventListener("load", onLoad);
                return () => {
                    iframe.removeEventListener("load", onLoad);
                };
            },
            () => [this.root.el && this.root.el.querySelector("iframe")]
        );
        useEffect(
            (el) => {
                if (!el) {
                    return;
                }
                this.state.topOffset = el.scrollTop;
                const scrollHandler = () => {
                    this.state.topOffset = el.scrollTop;
                };
                el.addEventListener("scroll", scrollHandler);
                return () => {
                    el.removeEventListener("scroll", scrollHandler);
                };
            },
            () => [this.parentRoot.el]
        );
    }

    get parentRoot() {
        return this.props.parentRoot;
    }

    onGlobalKeydown(ev) {
        const cancelledKeys = ["ArrowUp", "ArrowDown"];
        if (cancelledKeys.includes(ev.key)) {
            ev.stopPropagation();
        }
    }

    onIframeKeydown(ev) {
        if (ev.key === "Escape") {
            this.previewState.documentList.delete();
        }
    }
}
DmsAttachmentViewer.components = {
    AttachmentViewer: getMessagingComponent("AttachmentViewer"),
};
DmsAttachmentViewer.template = "dms.DocumentAttachmentViewer";
