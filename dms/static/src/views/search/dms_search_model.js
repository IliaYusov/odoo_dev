/** @odoo-module **/

import { SearchModel } from "@web/search/search_model";
import { browser } from "@web/core/browser/browser";

const isDirectoryCategory = (s) => s.type === "category" && s.fieldName === "directory_id";

export class DocumentSearchModel extends SearchModel {
    getSelectedDirectoryId() {
        const { activeValueId } = this.getSections(isDirectoryCategory)[0];
        return activeValueId;
    }
}
