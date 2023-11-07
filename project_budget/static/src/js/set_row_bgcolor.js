odoo.define('project_budget.tree_color', function (require) {
    'use strict';
    var ListRenderer = require('web.ListRenderer');
    ListRenderer.include({
        _renderRow: function (record, index) {
            var $row = this._super.apply(this, arguments);
            var color = record.data.color;
            if (color) {
                $row.css('background-color', color);
            }
            return $row;
        },
    });
});