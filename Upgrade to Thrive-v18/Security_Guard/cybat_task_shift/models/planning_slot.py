from datetime import datetime, timedelta

import pytz

from thrive import models, fields, api
from thrive.exceptions import ValidationError


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    task_shift_id = fields.Many2one('project.task.shift.rate')
    attendance_check_in = fields.Datetime(default=fields.datetime.now(), copy=False)
    attendance_check_out = fields.Datetime(default=fields.datetime.now(), copy=False)
    attendance_id = fields.Many2one('hr.attendance', copy=False)
    overtime_request_id = fields.Many2one('overtime.request',copy=False)
    timesheet_id = fields.Many2one('account.analytic.line',copy=False)
    project_id = fields.Many2one('project.project')

    def create_attendance(self):
        if self.attendance_id:
            raise ValidationError('Attendance Already Exists!')
        if not self.attendance_check_in:
            raise ValidationError('Please Input Clock In!')
        if self.attendance_check_in < self.start_datetime:
            raise ValidationError('You Can Not Check in Before Schedule Datetime')
        if self.attendance_check_in > self.end_datetime:
            raise ValidationError('You Can Not Check in After Schedule Datetime')
        # if self.attendance_check_out > self.end_datetime:
        #     raise ValidationError('You Can Not Check Out After Schedule Datetime End')
        attendance_id = self.env['hr.attendance'].create({
            'employee_id': self.resource_id.employee_id.id,
            'check_in': self.attendance_check_in,
            # 'check_out': self.attendance_check_out,
            'project_id': self.project_id.id,
            'task_shift_id': self.task_shift_id.id
        })
        self.attendance_id = attendance_id.id

    def update_attendance_checkout(self):
        if self.attendance_id:
            if not self.attendance_id.check_out:
                self.attendance_id.check_out = self.attendance_check_out
            else:
                raise ValidationError('Attendance Check Out Already Marked')
        else:
            raise ValidationError('Please Check In Attendance')

    def create_timesheet(self):
        if self.timesheet_id:
            raise ValidationError('Timesheet Already Exist')
        if not self.project_id:
            raise ValidationError('Please Select Project')
        difference = self.attendance_check_out - self.attendance_check_in
        total_seconds = difference.total_seconds()
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60
        unit_amount = total_seconds / 3600
        timesheet_id = self.env['account.analytic.line'].create({
            'project_id': self.project_id.id,
            'task_shift_id': self.task_shift_id.id,
            'rate_per_hour': self.task_shift_id.shift_rate,
            'date': self.attendance_check_in.date(),
            'unit_amount': self.allocated_hours,
            'employee_id': self.resource_id.employee_id.id,
        })
        self.timesheet_id = timesheet_id.id
        if unit_amount > self.allocated_hours:
            overtime = unit_amount -self.allocated_hours
            end_date = self.attendance_check_out + timedelta(hours=overtime)
            overtime_id = self.env['overtime.request'].create({
                'employee_id': self.resource_id.employee_id.id,
                'start_date': self.attendance_check_out,
                'end_date': end_date,
                'include_in_payroll': True
            })
            self.overtime_request_id = overtime_id.id


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    project_ids = fields.Many2many('project.project')


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    project_id = fields.Many2one('project.project')
    task_shift_id = fields.Many2one('project.task.shift.rate')
