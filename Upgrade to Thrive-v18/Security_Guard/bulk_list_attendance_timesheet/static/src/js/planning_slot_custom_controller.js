/** @thrive-module */
import {ListController} from "@web/views/list/list_controller";
import {registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";

export class PlanningSLotListCustomController extends ListController {
    setup() {
        super.setup();
        this.orm = useService('orm');
    }

    async onclickToDayShift() {
        const action = await this.orm.call('planning.slot', 'action_view_today_shift', [])
        this.actionService.doAction(action);
    }
}

const planning_tree = registry.category("views").get("planning_tree");
Object.assign(planning_tree, {
    Controller: PlanningSLotListCustomController,
    buttonTemplate: "bulk_list_attendance_timesheet.ListView.Buttons",
});
