odoo.define('form_style_adjustment.FormView', function (require) {
"use strict";

var FormRenderer = require('web.FormRenderer');


FormRenderer.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------
    /**
     * @private
     * @param {Object} node
     * @returns {jQueryElement}
     */
    _renderTagSheet: function (node) {
        var $sheet = this._super.apply(this, arguments);
        if (node.attrs.style) {
            $sheet.attr('style', node.attrs.style);
        }
        return $sheet;
    },
});

});
