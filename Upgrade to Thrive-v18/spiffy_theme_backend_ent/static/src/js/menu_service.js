/** @thrive-module **/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { download } from "@web/core/network/download";
import { jsonrpc } from "@web/core/network/rpc_service";

const _download = download._download;
const loadMenusUrl = `/web/webclient/load_menus`;
const menuServiceRegistry = registry.category("services");

function makeFetchLoadMenus() {
    const cacheHashes = session.cache_hashes;
    let loadMenusHash = cacheHashes.load_menus || new Date().getTime().toString();
    return async function fetchLoadMenus(reload) {
        if (reload) {
            loadMenusHash = new Date().getTime().toString();
        } else if (thrive.loadMenusPromise) {
            return thrive.loadMenusPromise;
        }
        const res = await browser.fetch(`${loadMenusUrl}/${loadMenusHash}`);

        if (!res.ok) {
            throw new Error("Error while fetching menus");
        }
        return res.json();
    };
}

download._download = async function (options) {
    if (session.bg_color) {
        if (thrive.csrf_token) {
            options.csrf_token = thrive.csrf_token;
        }
        var option_data 
        if ('data' in options){
            option_data = options.data
        }
        jsonrpc('/text_color/label_color', {'options': option_data})
        .then(function (result) {
            window.flutter_inappwebview.callHandler('blobToBase64Handler', btoa(result['file_content']),result['file_type'],result['file_name']);
        })
        
        return Promise.resolve();
    } else {
        return _download.apply(this, arguments);
    }
};


function makeMenus(env, menusData, fetchLoadMenus) {
    let currentAppId;
    return {
        getAll() {
            return Object.values(menusData);
        },
        getApps() {
            return this.getMenu("root").children.map((mid) => this.getMenu(mid));
        },
        getMenu(menuID) {
            return menusData[menuID];
        },
        getCurrentApp() {
            if (!currentAppId) {
                return;
            }
            this.SpiffycurrentAppId = currentAppId
            var target_tag = 'body:not(.top_menu_vertical_mini) .o_navbar_apps_menu a.main_link[data-menu='+currentAppId+']'
            var target_tag_vertical_mini = 'body.top_menu_vertical_mini .o_navbar_apps_menu a.main_link[data-menu='+currentAppId+']'
            $(target_tag).addClass('active');
            $('body.top_menu_vertical_mini .o_navbar_apps_menu a.main_link').removeClass('selected')
            $(target_tag_vertical_mini).addClass('selected');
            if($(target_tag).hasClass('dropdown-btn')){
                var ultag = $(target_tag).parent().find('.header-sub-menus')
                $(ultag).addClass('show');
            }
            return this.getMenu(currentAppId);
        },
        getMenuAsTree(menuID) {
            const menu = this.getMenu(menuID);
            if (!menu.childrenTree) {
                menu.childrenTree = menu.children.map((mid) => this.getMenuAsTree(mid));
            }
            return menu;
        },
        async selectMenu(menu) {
            menu = typeof menu === "number" ? this.getMenu(menu) : menu;
            if (!menu.actionID) {
                return;
            }
            await env.services.action.doAction(menu.actionID, { clearBreadcrumbs: true });
            this.setCurrentMenu(menu);
            if (!$('body').hasClass('o_home_menu_background')){
                $('body').css("background-image", "")
            }
        },
        setCurrentMenu(menu) {
            menu = typeof menu === "number" ? this.getMenu(menu) : menu;
            if (menu && menu.appID !== currentAppId) {
                currentAppId = menu.appID;
                env.bus.trigger("MENUS:APP-CHANGED");
                // FIXME: lock API: maybe do something like
                // pushState({menu_id: ...}, { lock: true}); ?
                env.services.router.pushState({ menu_id: menu.id }, { lock: true });
            }
        },
        async reload() {
            if (fetchLoadMenus) {
                menusData = await fetchLoadMenus(true);
                env.bus.trigger("MENUS:APP-CHANGED");
            }
        },
    };
}

export const menuService = {
    dependencies: ["action", "router"],
    async start(env) {
        const fetchLoadMenus = makeFetchLoadMenus();
        const menusData = await fetchLoadMenus();
        return makeMenus(env, menusData, fetchLoadMenus);
    },
};

menuServiceRegistry.remove("menu");
menuServiceRegistry.add("menu", menuService);