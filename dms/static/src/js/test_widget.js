/** @odoo-module **/
import { Many2ManyBinaryField } from "@web/views/fields/many2many_binary/many2many_binary_field";
import { patch } from "@web/core/utils/patch";

patch(Many2ManyBinaryField.prototype, '/advanced_many2many_binary/static/src/js/many2many_binary_field.js', {
    getUrl(id) {
        const file = "/web/content/" + id;
        return "/web/static/lib/pdfjs/web/viewer.html?file=" + file;
    },
})
