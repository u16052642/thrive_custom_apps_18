/** @thrive-module **/

import {View} from '@web/views/view';

import { evaluateExpr } from '@web/core/py_js/py';
import { parseXML } from "@web/core/utils/xml";
import { nbsp } from "@web/core/utils/strings";
import { registry } from '@web/core/registry';
import { deepCopy, pick } from '@web/core/utils/objects';
import { extractLayoutComponents } from '@web/search/layout';
import { WithSearch } from '@web/search/with_search/with_search';
import { computeViewClassName } from "@web/views/utils";

import {
    Component,
    markRaw,
    onWillUpdateProps,
    onWillStart,
    toRaw,
    useSubEnv,
    reactive,
} from "@thrive/owl";
const viewRegistry = registry.category('views');
const CALLBACK_RECORDER_NAMES = [
    "__beforeLeave__",
    "__getGlobalState__",
    "__getLocalState__",
    "__getContext__",
    "__getOrderBy__",
];
const STANDARD_PROPS = [
    "resModel",
    "resId",
    "type",

    "arch",
    "fields",
    "relatedModels",
    "viewId",
    "actionMenus",
    "loadActionMenus",

    "searchViewArch",
    "searchViewFields",
    "searchViewId",
    "irFilters",
    "loadIrFilters",

    "comparison",
    "context",
    "domain",
    "groupBy",
    "orderBy",

    "useSampleModel",
    "noContentHelp",
    "className",

    "display",
    "globalState",

    "activateFavorite",
    "dynamicFilters",
    "hideCustomGroupBy",
    "searchMenuTypes",

    ...CALLBACK_RECORDER_NAMES,

    // LEGACY: remove this later (clean when mappings old state <-> new state are established)
    "searchPanel",
    "searchModel",
];
const ACTIONS = ["create", "delete", "edit", "group_create", "group_delete", "group_edit"];
export class SplitViewForm extends View {

    setup() {
        super.setup()
    }

    async loadView(props) {
        // determine view type
        let descr = viewRegistry.get(props.type);
        const type = descr.type;

        // determine views for which descriptions should be obtained
        let { viewId, searchViewId } = props;

        const views = deepCopy(props.views || this.env.config.views);
        const view = views.find((v) => v[1] === type) || [];
        if (view.length) {
            view[0] = viewId !== undefined ? viewId : view[0];
            viewId = view[0];
        } else {
            view.push(viewId || false, type);
            views.push(view); // viewId will remain undefined if not specified and loadView=false
        }

        const searchView = views.find((v) => v[1] === "search");
        if (searchView) {
            searchView[0] = searchViewId !== undefined ? searchViewId : searchView[0];
            searchViewId = searchView[0];
        } else if (searchViewId !== undefined) {
            views.push([searchViewId, "search"]);
        }
        // searchViewId will remains undefined if loadSearchView=false

        // prepare view description
        const { context, resModel, resId, loadActionMenus, loadIrFilters } = props;
        let {
            arch,
            fields,
            relatedModels,
            searchViewArch,
            searchViewFields,
            irFilters,
            actionMenus,
        } = props;

        const loadView = !arch || (!actionMenus && loadActionMenus);
        const loadSearchView =
            (searchViewId !== undefined && !searchViewArch) || (!irFilters && loadIrFilters);

        let viewDescription = { viewId, resModel, resId, type };
        let searchViewDescription;
        if (loadView || loadSearchView) {
            // view description (or search view description if required) is incomplete
            // a loadViews is done to complete the missing information
            const result = await this.viewService.loadViews(
                { context, resModel, resId, views },
                { actionId: this.env.config.actionId, loadActionMenus, loadIrFilters }
            );
            // Note: if props.views is different from views, the cached descriptions
            // will certainly not be reused! (but for the standard flow this will work as
            // before)
            viewDescription = result.views[type];
            searchViewDescription = result.views.search;
            if (loadSearchView) {
                searchViewId = searchViewId || searchViewDescription.id;
                if (!searchViewArch) {
                    searchViewArch = searchViewDescription.arch;
                    searchViewFields = result.fields;
                }
                if (!irFilters) {
                    irFilters = searchViewDescription.irFilters;
                }
            }
            this.env.config.views = views;
            fields = fields || markRaw(result.fields);
            relatedModels = relatedModels || markRaw(result.relatedModels);
        }

        if (!arch) {
            arch = viewDescription.arch;
        }
        if (!actionMenus) {
            actionMenus = viewDescription.actionMenus;
        }

        const archXmlDoc = parseXML(arch.replace(/&amp;nbsp;/g, nbsp));
        for (const action of ACTIONS) {
            if (action in this.props.context && !this.props.context[action]) {
                archXmlDoc.setAttribute(action, "0");
            }
        }

        let subType = archXmlDoc.getAttribute("js_class");
        const bannerRoute = archXmlDoc.getAttribute("banner_route");
        const sample = archXmlDoc.getAttribute("sample");
        const className = computeViewClassName(type, archXmlDoc, [
            "o_view_controller",
            ...(props.className || "").split(" "),
        ]);

        // determine ViewClass to instantiate (if not already done)
        if (subType) {
            if (viewRegistry.contains(subType)) {
                descr = viewRegistry.get(subType);
            } else {
                subType = null;
            }
        }

        Object.assign(this.env.config, {
            viewArch: archXmlDoc,
            viewId: viewDescription.id,
            viewType: type,
            viewSubType: subType,
            bannerRoute,
            noBreadcrumbs: false,
            ...extractLayoutComponents(descr),
        });
        const info = {
            actionMenus,
            mode: props.display.mode,
            irFilters,
            searchViewArch,
            searchViewFields,
            searchViewId,
        };

        // prepare the view props
        const viewProps = {
            info,
            arch: archXmlDoc,
            fields,
            relatedModels,
            resModel,
            resId,
            useSampleModel: false,
            className,
        };
        if (viewDescription.custom_view_id) {
            // for dashboard
            viewProps.info.customViewId = viewDescription.custom_view_id;
        }
        if (props.globalState) {
            viewProps.globalState = props.globalState;
        }

        if ("useSampleModel" in props) {
            viewProps.useSampleModel = props.useSampleModel;
        } else if (sample) {
            viewProps.useSampleModel = evaluateBooleanExpr(sample);
        }

        for (const key in props) {
            if (!STANDARD_PROPS.includes(key)) {
                viewProps[key] = props[key];
            }
        }

        const { noContentHelp } = props;
        if (noContentHelp) {
            viewProps.info.noContentHelp = noContentHelp;
        }

        const searchMenuTypes =
            props.searchMenuTypes || descr.searchMenuTypes || this.constructor.searchMenuTypes;
        viewProps.searchMenuTypes = searchMenuTypes;

        const finalProps = descr.props ? descr.props(viewProps, descr, this.env.config) : viewProps;
        // prepare the WithSearch component props
        this.Controller = this.env.config.Controller || descr.Controller;
        this.componentProps = finalProps;
        this.withSearchProps = {
            ...toRaw(props),
            hideCustomGroupBy: props.hideCustomGroupBy || descr.hideCustomGroupBy,
            searchMenuTypes,
            SearchModel: descr.SearchModel,
        };

        if (searchViewId !== undefined) {
            this.withSearchProps.searchViewId = searchViewId;
        }
        if (searchViewArch) {
            this.withSearchProps.searchViewArch = searchViewArch;
            this.withSearchProps.searchViewFields = searchViewFields;
        }
        if (irFilters) {
            this.withSearchProps.irFilters = irFilters;
        }

        if (descr.display) {
            // FIXME: there's something inelegant here: display might come from
            // the View's defaultProps, in which case, modifying it in place
            // would have unwanted effects.
            const viewDisplay = deepCopy(descr.display);
            const display = { ...this.withSearchProps.display };
            for (const key in viewDisplay) {
                if (typeof display[key] === "object") {
                    Object.assign(display[key], viewDisplay[key]);
                } else if (!(key in display) || display[key]) {
                    display[key] = viewDisplay[key];
                }
            }
            this.withSearchProps.display = display;
        }

        for (const key in this.withSearchProps) {
            if (!(key in WithSearch.props)) {
                delete this.withSearchProps[key];
            }
        }
    }

    onWillUpdateProps(nextProps) {
        const oldProps = pick(this.props, "arch", "type", "resModel" ,"resId");
        const newProps = pick(nextProps, "arch", "type", "resModel", "resId");
        if (JSON.stringify(oldProps) !== JSON.stringify(newProps)) {
            return this.loadView(nextProps);
        }
        // we assume that nextProps can only vary in the search keys:
        // comparison, context, domain, groupBy, orderBy
        const { comparison, context, domain, groupBy, orderBy } = nextProps;
        Object.assign(this.withSearchProps, { comparison, context, domain, groupBy, orderBy });
    }
    
}

SplitViewForm.defaultProps = {
    type: 'form',
}