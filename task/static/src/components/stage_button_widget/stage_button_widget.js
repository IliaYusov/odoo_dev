/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component, useState, onWillUpdateProps } = owl;

class StageButtonWidget extends Component {
    setup() {
        super.setup(...arguments);

        this.rpc = useService("rpc");
        this.actionService = useService("action");

        this.state = useState({
            value_json: JSON.parse(this.props.value),
        });

        this.model = this.env.model.root.resModel

        onWillUpdateProps(nextProps => {
            if (nextProps.value !== this.props.value) {
                this.state.value_json = JSON.parse(nextProps.value);
            }
        });
    }
    _fetchUpdateProps() {
        this.rpc('/web/dataset/call_kw', {
            model: this.model,
            method: 'read',
            args: [[this.env.model.root.data['id']], ['stage_routes']],
            kwargs: {},
        }).then((result) => {
            this.state.value_json = JSON.parse(result[0]['stage_routes']);

            this.env.model.load({ resId: this.env.model.root.data.id });
        });
    };

    async _onButtonClick(routeId) {
        await this.env.model.root.save({
                noReload: true,
                stayInEdition: true,
                useSaveErrorDialog: true,
            });

        if (this.env.model.root.data['id']) {
            return this.rpc('/web/dataset/call_kw', {
                model: this.model,
                method: 'action_move_task_along_route',
                args: [this.env.model.root.data['id'], routeId],
                kwargs: {},
            }).then((action_data) => {
                if (action_data) {
                    this.actionService.doAction(
                        action_data, {
                            onClose: () => {
                                this._fetchUpdateProps();
                            },
                        }
                    )
                } else {
                    this._fetchUpdateProps();
                }
            })
    };
}}
StageButtonWidget.template = 'task.stage_button_widget'

registry.category('fields').add('stage_button_widget', StageButtonWidget);
