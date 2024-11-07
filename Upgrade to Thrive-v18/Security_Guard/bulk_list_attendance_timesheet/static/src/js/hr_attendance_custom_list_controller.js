/** @thrive-module */
import {ListController} from "@web/views/list/list_controller";
import {registry} from '@web/core/registry';
import {listView} from "@web/views/list/list_view";
import {useService} from "@web/core/utils/hooks";


export class PlanningSLotListCustomController extends ListController {
    setup() {
        super.setup();
        this.orm = useService('orm');
    }

    async onclickToDayAttendance() {
        const action = await this.orm.call('hr.attendance', 'action_view_today_attendance', [])
        this.actionService.doAction(action);
    }
}

registry.category("views").add("hr_attendance_custom", {
    ...listView,
    Controller: PlanningSLotListCustomController,
    buttonTemplate: "bulk_list_attendance_timesheet.TodayAttendanceButton",
});
