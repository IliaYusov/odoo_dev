/** @odoo-module */

import { SearchModel } from "@web/search/search_model";
import {useBus, useService} from "@web/core/utils/hooks";
import rpc from "web.rpc";
import {_t} from "web.core";

const {useRef, useEffect, useState} = owl;

export const FileDropZone = {
    setup() {
        this._super();
        this.dragState = useState({
            showDragZone: false,
        });
        this.root = useRef("root");
        this.rpc = useService("rpc");

        useEffect(
            (el) => {
                if (!el) {
                    return;
                }
                const highlight = this.highlight.bind(this);
                const unhighlight = this.unhighlight.bind(this);
                const drop = this.onDrop.bind(this);
                el.addEventListener("dragover", highlight);
                el.addEventListener("dragleave", unhighlight);
                el.addEventListener("drop", drop);
                return () => {
                    el.removeEventListener("dragover", highlight);
                    el.removeEventListener("dragleave", unhighlight);
                    el.removeEventListener("drop", drop);
                };
            },

            () => [document.querySelector(".o_content")]
        );
    },

    highlight(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.dragState.showDragZone = true;
    },

    unhighlight(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.dragState.showDragZone = false;
    },

    async onDrop(ev) {
        ev.preventDefault();
        await this.env.bus.trigger("change_file_input", {
            files: ev.dataTransfer.files
        });
    },
};

export const FileUpload = {
    setup() {
        this._super();
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.http = useService("http");
        this.fileInput = useRef("fileInput");
        this.root = useRef("root");

        this.rpc = useService("rpc");

        useBus(this.env.bus, "change_file_input", async (ev) => {
            this.fileInput.el.files = ev.detail.files;
            await this.onChangeFileInput();
        });
    },

    uploadDocument() {
        this.fileInput.el.click();
    },

    async onChangeFileInput() {
        const controllerID = this.actionService.currentController.jsId;

        if (!this.env.searchModel.getSelectedDirectoryId()) {
            this.actionService.restore(controllerID);
            return this.notification.add(
                this.env._t("You must select a directory first"),
                {
                    type: "danger",
                }
            );
        }

        const ctx = this.props.context;
        let res_model = ctx.default_res_model ? ctx.default_res_model : "dms.document";
        let res_id = ctx.default_res_model ? ctx.default_res_id : 0;

        const params = {
            csrf_token: odoo.csrf_token,
            ufile: [...this.fileInput.el.files],
            directory_id: this.env.searchModel.getSelectedDirectoryId(),
            res_model: res_model,
            res_id: res_id
        };

        const fileData = await this.http.post(
            "/dms/upload_attachment",
            params,
            "text"
        );
        const attachments = JSON.parse(fileData);
        if (attachments.error) {
            throw new Error(attachments.error);
        }
        this.notification.add(
            attachments.success ? attachments.success : this.env._t("All files uploaded"),
            {
                type: "success",
            }
        );
        this.actionService.restore(controllerID);
    }
};
