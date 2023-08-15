/** @odoo-module */

import {Field} from '@web/views/fields/field';
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
//import { onEmployeeSubRedirect } from './hooks';

const { Component, onWillStart, onWillRender, useState } = owl;

function useUniquePopover() {
    const popover = usePopover();
    let remove = null;
    return Object.assign(Object.create(popover), {
        add(target, component, props, options) {
            if (remove) {
                remove();
            }
            remove = popover.add(target, component, props, options);
            return () => {
                remove();
                remove = null;
            };
        },
    });
}

class ProcessingChartPopover extends Component {
    async setup() {
        super.setup();

        this.rpc = useService('rpc');
        this.orm = useService('orm');
        this.actionService = useService("action");
//        this._onEmployeeSubRedirect = onEmployeeSubRedirect();
    }

    /**
     * Redirect to the employee form view.
     *
     * @private
     * @param {MouseEvent} event
     * @returns {Promise} action loaded
     */
//    async _onEmployeeRedirect(employeeId) {
//        const action = await this.orm.call('hr.employee', 'get_formview_action', [employeeId]);
//        this.actionService.doAction(action);
//    }
}
ProcessingChartPopover.template = 'document_flow.processing_popover';

export class ProcessingChart extends Field {
    async setup() {
        super.setup();

        this.rpc = useService('rpc');
        this.orm = useService('orm');
        this.actionService = useService("action");
        this.popover = useUniquePopover();

        this.jsonStringify = JSON.stringify;

        this.state = useState({'process_id': null});
        this.lastParent = null;
//        this._onEmployeeSubRedirect = onEmployeeSubRedirect();

        onWillStart(this.handleComponentUpdate.bind(this));
        onWillRender(this.handleComponentUpdate.bind(this));
    }

    /**
     * Called on start and on render
     */
    async handleComponentUpdate() {
        this.process = this.props.record.data;
        this.state.process_id = this.process.id;
        const main_process = this.process.parent_id || this.process.process_parent_id;
        const forceReload = this.lastRecord !== this.props.record || this.lastParent != main_process;
        this.lastParent = main_process;
        this.lastRecord = this.props.record;
        await this.fetchProcessData(this.state.process_id, forceReload);
    }

    async fetchProcessData(processId, force = false) {
        if (!processId) {
            this.main_processes = [];
            this.sub_processes = [];
            if (this.view_process_id) {
                this.render(true);
            }
            this.view_process_id = null;
        } else if (processId !== this.view_process_id || force) {
            this.view_process_id = processId;
            var processData = await this.rpc(
                '/document_flow/get_processing_chart',
                {
                    process_id: processId,
                    context: Component.env.session.user_context,
                }
            );
            if (Object.keys(processData).length === 0) {
                processData = {
                    main_processes: [],
                    sub_processes: [],
                }
            }
            this.main_processes = processData.main_processes;
            this.sub_processes = processData.sub_processes;
//            this.managers_more = processData.managers_more;
            this.self = processData.self;
            this.render(true);
        }
    }

    _onOpenPopover(event, process) {
        this.popover.add(
            event.currentTarget,
            this.constructor.components.Popover,
            {process},
            {closeOnClickAway: true}
        );
    }

    /**
     * Redirect to the employee form view.
     *
     * @private
     * @param {MouseEvent} event
     * @returns {Promise} action loaded
     */
//    async _onEmployeeRedirect(employeeId) {
//        const action = await this.orm.call('hr.employee', 'get_formview_action', [employeeId]);
//        this.actionService.doAction(action);
//    }

//    async _onEmployeeMoreManager(managerId) {
//        await this.fetchEmployeeData(managerId);
//        this.state.employee_id = managerId;
//    }
}

ProcessingChart.components = {
    Popover: ProcessingChartPopover,
};

ProcessingChart.template = 'document_flow.processing_chart';

registry.category("fields").add("processing_chart", ProcessingChart);
