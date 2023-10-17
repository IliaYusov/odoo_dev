/** @odoo-module */

const { Component } = owl;

export class Card extends Component {}

Card.template = "project_budget.Card";
Card.props = {
    slots: {
        type: Object,
        shape: {
            default: Object,
            title: { type: Object, optional: true },
        },
    },
    className: {
        type: String,
        optional: true,
    },
};