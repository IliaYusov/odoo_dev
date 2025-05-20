/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { LicenseDashBoard } from '@license_mngmnt/views/dashboard/license_license_dashboard';

export class LicenseDashBoardRenderer extends ListRenderer {};

LicenseDashBoardRenderer.template = 'license_mngmnt.LicenseListView';
LicenseDashBoardRenderer.components= Object.assign({}, ListRenderer.components, {LicenseDashBoard})

export const LicenseDashBoardListView = {
    ...listView,
    Renderer: LicenseDashBoardRenderer,
};

registry.category("views").add("license_dashboard_list", LicenseDashBoardListView);
