/** @odoo-module **/

import {Field} from '@web/views/fields/field';
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const { Component, onWillStart, onWillRender, useState } = owl;

export class ProcessingWidget extends Field {
    async setup() {
        super.setup();

        this.rpc = useService('rpc');
        this.orm = useService('orm');
        this.actionService = useService("action");

        this.jsonStringify = JSON.stringify;

        this.state = useState({'process_id': null});
        this.lastParent = null;

        onWillStart(this.handleComponentUpdate.bind(this));
        onWillRender(this.handleComponentUpdate.bind(this));
    }

    /**
     * Called on start and on render
     */
    async handleComponentUpdate() {
        this.process = this.props.record.data;
        this.state.process_id = this.process.id;
        const forceReload = this.lastRecord !== this.props.record;
        this.lastRecord = this.props.record;
        await this.fetchProcessData(this.state.process_id, forceReload);
    }

    async fetchProcessData(processId, force = false) {
        if (!processId) {
            this.sub_processes = [];
            if (this.view_process_id) {
                this.render(true);
            }
            this.view_process_id = null;
        } else if (processId !== this.view_process_id || force) {
            this.view_process_id = processId;
            var processData = await this.rpc(
                '/document_flow/get_process_chart',
                {
                    process_id: processId,
                    context: Component.env.session.user_context,
                }
            );
            if (Object.keys(processData).length === 0) {
                processData = {
                    sub_processes: [],
                }
            }
            this.sub_processes = processData.sub_processes;
            this.self = processData.self;
            this.render(true);
        }
    }
}

ProcessingWidget.template = 'document_flow.processing_widget'

registry.category('fields').add('processing_widget', ProcessingWidget);
