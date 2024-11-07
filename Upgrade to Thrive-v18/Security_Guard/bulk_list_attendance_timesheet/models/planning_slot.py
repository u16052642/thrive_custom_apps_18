from datetime import timedelta

from thrive import models, api, _
from thrive.exceptions import ValidationError


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    def _bulk_create_attendance(self):
        if self.attendance_id:
            raise ValidationError('Attendance Already Exists!')
        # if not self.attendance_check_in:
        #     raise ValidationError('Please Input Clock In!')
        # if self.attendance_check_in < self.start_datetime:
        #     raise ValidationError('You Can Not Check in Before Schedule Datetime')
        # if self.attendance_check_in > self.end_datetime:
        #     raise ValidationError('You Can Not Check in After Schedule Datetime')
        # if self.attendance_check_out > self.end_datetime:
        #     raise ValidationError('You Can Not Check Out After Schedule Datetime End')
        attendance_id = self.env['hr.attendance'].create({
            'employee_id': self.resource_id.employee_id.id,
            'check_in': self.start_datetime,
            # 'check_out': self.attendance_check_out,
            'project_id': self.project_id.id,
            'task_shift_id': self.task_shift_id.id,
        })
        self.attendance_id = attendance_id.id

    def _bulk_update_attendance_checkout(self):
        if self.attendance_id:
            if not self.attendance_id.check_out:
                self.attendance_id.check_out = self.end_datetime
            else:
                raise ValidationError('Attendance Check Out Already Marked')
        else:
            raise ValidationError('Please Check In Attendance')

    def action_bulk_checkin(self):
        for r in self:
            r._bulk_create_attendance()
        return self._action_client_notify(message="Success")

    def action_bulk_checkout(self):
        for r in self:
            r._bulk_update_attendance_checkout()
        return self._action_client_notify(message="Success")

    def action_bulk_create_timesheet(self):
        for r in self:
            r._bulk_create_timesheet()
        return self._action_client_notify(message="Success")

    def _bulk_create_timesheet(self):
        if self.timesheet_id:
            raise ValidationError('Timesheet Already Exist')
        if not self.project_id:
            raise ValidationError('Please Select Project')
        if not self.attendance_id:
            self.create_attendance()

        difference = self.attendance_id.check_in - self.attendance_id.check_out
        total_seconds = difference.total_seconds()
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60
        unit_amount = total_seconds / 3600
        timesheet_id = self.env['account.analytic.line'].create({
            'project_id': self.project_id.id,
            'task_shift_id': self.task_shift_id.id,
            'rate_per_hour': self.task_shift_id.shift_rate,
            'date': self.attendance_id.check_in.date(),
            'unit_amount': self.attendance_id.worked_hours,
            'employee_id': self.resource_id.employee_id.id,
        })
        self.timesheet_id = timesheet_id.id
        if unit_amount > self.allocated_hours:
            overtime = unit_amount -self.allocated_hours
            end_date = self.attendance_id.check_out + timedelta(hours=overtime)
            overtime_id = self.env['overtime.request'].create({
                'employee_id': self.resource_id.employee_id.id,
                'start_date': self.attendance_id.check_out,
                'end_date': end_date,
                'include_in_payroll': True
            })
            self.overtime_request_id = overtime_id.id

    @api.model
    def action_view_today_shift(self):
        action = self.env['ir.actions.act_window']._for_xml_id('bulk_list_attendance_timesheet.planning_slot_action_filter_today_shift')
        action['context'] = {
            'search_default_group_by_project': 1,
            'search_default_group_by_role': True,
            'search_default_filter_today_shift': 1,
        }
        return action
