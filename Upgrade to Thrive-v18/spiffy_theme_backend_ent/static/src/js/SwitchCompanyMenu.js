/** @thrive-module **/

import { patch } from "@web/core/utils/patch";
import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";
import { registry } from "@web/core/registry";

patch(SwitchCompanyMenu.prototype, {
    setup() {
        super.setup();
        // this.isDebug = config.isDebug();
        // this.isAssets = config.isDebug("assets");
        // this.isTests = config.isDebug("tests");
        this.isDebug = Boolean(thrive.debug);
        this.isAssets = thrive.debug.includes("assets");
        this.isTests = thrive.debug.includes("tests");
    },
});

// show company menu even if company is count is 1 
const systrayItemSwitchCompanyMenu = {
    Component: SwitchCompanyMenu,
    isDisplayed(env) {
        const { allowedCompanies } = env.services.company;
        return Object.keys(allowedCompanies).length > 0;
    },
};

registry.category("systray").add("SwitchCompanyMenu", systrayItemSwitchCompanyMenu, { sequence: 1, force: true });