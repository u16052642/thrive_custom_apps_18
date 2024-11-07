# -*- coding: utf-8 -*-
from datetime import datetime, time

import pytz

from thrive import models, fields, api, _
from thrive.exceptions import ValidationError


class TaskShift(models.Model):
    _name = 'task.shift'

    name = fields.Char()
    shift_rate = fields.Float()


class ProjectTaskShiftRate(models.Model):
    _name = 'project.task.shift.rate'
    _rec_name = 'task_shift_id'

    task_shift_id = fields.Many2one('task.shift')
    hr_work_entry_type = fields.Many2one('hr.work.entry.type', required=True)
    shift_rate = fields.Float()

    project_id = fields.Many2one('project.project')

    @api.onchange('task_shift_id')
    def update_shift_rate(self):
        for rec in self:
            rec.shift_rate = rec.task_shift_id.shift_rate


class Project(models.Model):
    _inherit = 'project.project'

    project_task_shift_ids = fields.One2many('project.task.shift.rate', 'project_id')


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    task_shift_id = fields.Many2one('project.task.shift.rate')
    rate_per_hour = fields.Float(string='Rate Per Hour')
    total_earn = fields.Float(string='Total Earn', compute='calculate_total_earn')

    @api.onchange('task_shift_id')
    def update_rate_per_hour(self):
        for rec in self:
            rec.rate_per_hour = rec.task_shift_id.shift_rate

    @api.depends('unit_amount', 'rate_per_hour')
    def calculate_total_earn(self):
        for rec in self:
            rec.total_earn = rec.rate_per_hour * rec.unit_amount

    @api.model
    def create(self, vals):
        # a = self.check_attendace_and_schedule(vals)
        res = super().create(vals)
        return res

    def write(self, vals):
        # if vals.get('employee_id') or vals.get('date'):
        #     a = self.check_attendace_and_schedule_write(vals)
        # if vals.get('unit_amount'):
        #     a = self.check_attendace_and_schedule_write(vals)
        res = super().write(vals)
        return res

    def check_attendace_and_schedule(self, vals):
        if vals.get('employee_id'):
            employee_id = vals.get('employee_id')
        else:
            employee_id = self.employee_id.id
        if vals.get('date'):
            task_date = vals.get('date')
            date_obj = datetime.strptime(str(task_date), "%Y-%m-%d")
        else:
            task_date = self.date
            date_obj = datetime.strptime(str(task_date), "%Y-%m-%d")
        date_obj_a = date_obj.date()
        slots = self.env['planning.slot'].search([('resource_id', '=', employee_id)])
        tasks = self.env['account.analytic.line'].search([('date', '=', date_obj_a), ('employee_id', '=', employee_id)])
        hr_attendances = self.env['hr.attendance'].search([('employee_id', '=', employee_id)])
        that_date_task_hours = sum(tasks.mapped('unit_amount'))
        user_tz = pytz.timezone(self.env.get('tz') or self.env.user.tz)
        pak_time = pytz.utc.localize(date_obj).astimezone(user_tz)

        start_date_slots = slots.filtered(
            lambda x: pytz.utc.localize(x.start_datetime).astimezone(user_tz).day == date_obj.day and pytz.utc.localize(
                x.start_datetime).astimezone(user_tz).month == date_obj.month and pytz.utc.localize(
                x.start_datetime).astimezone(user_tz).year == date_obj.year)
        end_date_slots = slots.filtered(
            lambda x: pytz.utc.localize(x.end_datetime).astimezone(user_tz).day == date_obj.day and pytz.utc.localize(
                x.end_datetime).astimezone(user_tz).month == date_obj.month and pytz.utc.localize(
                x.end_datetime).astimezone(user_tz).year == date_obj.year)
        common_elements = list(set(start_date_slots).intersection(set(end_date_slots)))
        start_date_slots = [x for x in start_date_slots if x not in common_elements]
        end_date_slots = [x for x in end_date_slots if x not in common_elements]

        start_date_attendance = hr_attendances.filtered(
            lambda x: pytz.utc.localize(x.check_in).astimezone(user_tz).day == date_obj.day and pytz.utc.localize(
                x.check_in).astimezone(user_tz).month == date_obj.month and pytz.utc.localize(x.check_in).astimezone(
                user_tz).year == date_obj.year)
        end_date_attendance = hr_attendances.filtered(
            lambda x: pytz.utc.localize(x.check_out).astimezone(user_tz).day == date_obj.day and pytz.utc.localize(
                x.check_out).astimezone(user_tz).month == date_obj.month and pytz.utc.localize(x.check_out).astimezone(
                user_tz).year == date_obj.year)
        common_date_attendance = list(set(start_date_attendance).intersection(set(end_date_attendance)))
        start_date_attendance = [x for x in start_date_attendance if x not in common_date_attendance]
        end_date_attendance = [x for x in end_date_attendance if x not in common_date_attendance]
        this_task_time = 0
        allocated_hours = 0
        total_attedance_hours = 0
        if vals.get('unit_amount'):
            this_task_time = vals.get('unit_amount')
            if end_date_slots:
                for y in end_date_slots:
                    end_time = pytz.utc.localize(y.end_datetime).astimezone(user_tz)
                    midnight = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
                    difference = end_time - midnight
                    allocated_hours += difference.total_seconds() / 3600
            if start_date_slots:
                for x in start_date_slots:
                    start_time = pytz.utc.localize(x.start_datetime).astimezone(user_tz)
                    mid_night = start_time.replace(hour=23, minute=59, second=59, microsecond=59)
                    difference = mid_night - start_time
                    allocated_hours += difference.total_seconds() / 3600
            if common_elements:
                for z in common_elements:
                    allocated_hours += z.allocated_hours

            if end_date_attendance:
                for att in end_date_attendance:
                    end_time = pytz.utc.localize(att.check_out).astimezone(user_tz)
                    midnight = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
                    difference = end_time - midnight
                    total_attedance_hours += difference.total_seconds() / 3600
            if start_date_attendance:
                for atta in start_date_attendance:
                    start_time = pytz.utc.localize(atta.check_in).astimezone(user_tz)
                    mid_night = start_time.replace(hour=23, minute=59, second=59, microsecond=59)
                    difference = mid_night - start_time
                    total_attedance_hours += difference.total_seconds() / 3600
            if common_date_attendance:
                for a in common_date_attendance:
                    total_attedance_hours += a.worked_hours

        if round(allocated_hours, 2) < (that_date_task_hours + this_task_time):
            raise ValidationError('Task Hours Greater Than Schedule Allocated Hours.')

        if round(total_attedance_hours, 2) < (that_date_task_hours + this_task_time):
            raise ValidationError('Resource Attendance Worked Hours Are Less Than Task Hours.')

    def check_attendace_and_schedule_write(self, vals):
        if vals.get('employee_id'):
            employee_id = vals.get('employee_id')
        else:
            employee_id = self.employee_id.id
        if vals.get('date'):
            task_date = vals.get('date')
            date_obj = datetime.strptime(str(task_date), "%Y-%m-%d")
        else:
            task_date = self.date
            date_obj = datetime.strptime(str(task_date), "%Y-%m-%d")
        date_obj_a = date_obj.date()
        slots = self.env['planning.slot'].search([('resource_id', '=', employee_id)])
        tasks = self.env['account.analytic.line'].search([('date', '=', date_obj_a), ('employee_id', '=', employee_id)])
        hr_attendances = self.env['hr.attendance'].search([('employee_id', '=', employee_id)])
        that_date_task_hours = sum(tasks.mapped('unit_amount'))
        user_tz = pytz.timezone(self.env.get('tz') or self.env.user.tz)
        pak_time = pytz.utc.localize(date_obj).astimezone(user_tz)

        start_date_slots = slots.filtered(
            lambda x: pytz.utc.localize(x.start_datetime).astimezone(user_tz).day == date_obj.day and pytz.utc.localize(
                x.start_datetime).astimezone(user_tz).month == date_obj.month and pytz.utc.localize(
                x.start_datetime).astimezone(user_tz).year == date_obj.year)
        end_date_slots = slots.filtered(
            lambda x: pytz.utc.localize(x.end_datetime).astimezone(user_tz).day == date_obj.day and pytz.utc.localize(
                x.end_datetime).astimezone(user_tz).month == date_obj.month and pytz.utc.localize(
                x.end_datetime).astimezone(user_tz).year == date_obj.year)
        common_elements = list(set(start_date_slots).intersection(set(end_date_slots)))
        start_date_slots = [x for x in start_date_slots if x not in common_elements]
        end_date_slots = [x for x in end_date_slots if x not in common_elements]

        if not start_date_slots and not end_date_slots and not common_elements:
            raise ValidationError('Schedule Allocated Hours Not Found.')

        start_date_attendance = hr_attendances.filtered(
            lambda x: pytz.utc.localize(x.check_in).astimezone(user_tz).day == date_obj.day and pytz.utc.localize(
                x.check_in).astimezone(user_tz).month == date_obj.month and pytz.utc.localize(x.check_in).astimezone(
                user_tz).year == date_obj.year)
        end_date_attendance = hr_attendances.filtered(
            lambda x: pytz.utc.localize(x.check_out).astimezone(user_tz).day == date_obj.day and pytz.utc.localize(
                x.check_out).astimezone(user_tz).month == date_obj.month and pytz.utc.localize(x.check_out).astimezone(
                user_tz).year == date_obj.year)
        common_date_attendance = list(set(start_date_attendance).intersection(set(end_date_attendance)))
        start_date_attendance = [x for x in start_date_attendance if x not in common_date_attendance]
        end_date_attendance = [x for x in end_date_attendance if x not in common_date_attendance]
        this_task_time = 0
        allocated_hours = 0
        total_attedance_hours = 0
        previous_task_hours = 0
        if vals.get('unit_amount'):
            this_task_time = vals.get('unit_amount')
            previous_task_hours = self.unit_amount
        else:
            this_task_time = self.unit_amount
        if end_date_slots:
            for y in end_date_slots:
                end_time = pytz.utc.localize(y.end_datetime).astimezone(user_tz)
                midnight = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
                difference = end_time - midnight
                allocated_hours += difference.total_seconds() / 3600
        if start_date_slots:
            for x in start_date_slots:
                start_time = pytz.utc.localize(x.start_datetime).astimezone(user_tz)
                mid_night = start_time.replace(hour=23, minute=59, second=59, microsecond=59)
                difference = mid_night - start_time
                allocated_hours += difference.total_seconds() / 3600
        if common_elements:
            for z in common_elements:
                allocated_hours += z.allocated_hours

        if end_date_attendance:
            for att in end_date_attendance:
                end_time = pytz.utc.localize(att.check_out).astimezone(user_tz)
                midnight = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
                difference = end_time - midnight
                total_attedance_hours += difference.total_seconds() / 3600
        if start_date_attendance:
            for atta in start_date_attendance:
                start_time = pytz.utc.localize(atta.check_in).astimezone(user_tz)
                mid_night = start_time.replace(hour=23, minute=59, second=59, microsecond=59)
                difference = mid_night - start_time
                total_attedance_hours += difference.total_seconds() / 3600
        if common_date_attendance:
            for a in common_date_attendance:
                total_attedance_hours += a.worked_hours

        if round(allocated_hours, 2) < (that_date_task_hours + this_task_time - previous_task_hours):
            raise ValidationError('Task Hours Greater Than Schedule Allocated Hours.')

        if round(total_attedance_hours, 2) < (that_date_task_hours + this_task_time - previous_task_hours):
            raise ValidationError('Resource Attendance Worked Hours Are Less Than Task Hours.')


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    shift_id = fields.Many2one('project.task.shift.rate')

    # @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'contract_id.wage', 'payslip_id.sum_worked_hours')
    # def _compute_amount(self):
    #     for worked_days in self:
    #         if worked_days.shift_id:
    #             worked_days.amount = worked_days.shift_id.shift_rate * worked_days.number_of_hours
    #             continue
    #         if worked_days.code == 'OVERTIME':
    #             worked_days.amount = worked_days.number_of_hours * self.payslip_id.contract_id.overtime_rate

    @api.depends('is_paid', 'is_credit_time', 'number_of_hours', 'payslip_id', 'contract_id.wage','payslip_id.sum_worked_hours')
    def _compute_amount(self):
        for worked_days in self:
            if worked_days.contract_id.employee_id.is_security_guard:
                if worked_days.shift_id:
                    worked_days.amount = worked_days.shift_id.shift_rate * worked_days.number_of_hours
                    continue
                if worked_days.code == 'OVERTIME':
                    worked_days.amount = worked_days.number_of_hours * self.payslip_id.contract_id.overtime_rate
            else:

                if worked_days.payslip_id.edited or worked_days.payslip_id.state not in ['draft', 'verify']:
                    continue
                if not worked_days.contract_id or worked_days.code == 'OUT' or worked_days.is_credit_time:
                    worked_days.amount = 0
                    continue
                if worked_days.payslip_id.wage_type == "hourly":
                    worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
                else:
                    worked_days.amount = worked_days.payslip_id.contract_id.contract_wage * worked_days.number_of_hours / (
                            worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0

    # @api.depends('work_entry_type_id', 'number_of_days', 'number_of_hours', 'payslip_id')
    # def _compute_name(self):
    #     to_check_public_holiday = {
    #         res[0]: res[1]
    #         for res in self.env['resource.calendar.leaves']._read_group(
    #             [
    #                 ('resource_id', '=', False),
    #                 ('work_entry_type_id', 'in', self.mapped('work_entry_type_id').ids),
    #                 ('date_from', '<=', max(self.payslip_id.mapped('date_to'))),
    #                 ('date_to', '>=', min(self.payslip_id.mapped('date_from'))),
    #             ],
    #             ['work_entry_type_id'],
    #             ['id:recordset']
    #         )
    #     }
    #     for worked_days in self:
    #         public_holidays = to_check_public_holiday.get(worked_days.work_entry_type_id, '')
    #         holidays = public_holidays and public_holidays.filtered(lambda p:
    #                                                                 (
    #                                                                         p.calendar_id.id == worked_days.payslip_id.contract_id.resource_calendar_id.id or not p.calendar_id.id)
    #                                                                 and p.date_from.date() <= worked_days.payslip_id.date_to
    #                                                                 and p.date_to.date() >= worked_days.payslip_id.date_from
    #                                                                 and p.company_id == worked_days.payslip_id.company_id)
    #         half_day = worked_days._is_half_day()
    #         if holidays:
    #             name = (', '.join(holidays.mapped('name')))
    #         else:
    #             name = worked_days.work_entry_type_id.name
    #         worked_days.name = name + (_(' (Half-Day)') if half_day else '')
    #         if worked_days.shift_id:
    #             worked_days.name = name + (_(' '+str(worked_days.shift_id.task_shift_id.name)))



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_security_guard = fields.Boolean()


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_worked_day_lines_values(self, domain=None):
        res = super()._get_worked_day_lines_values(domain=domain)
        if not self.employee_id.is_security_guard:
            return res
        timesheets = self.env['account.analytic.line'].search(
            [('employee_id', '=', self.employee_id.id), ('date', '>=', self.date_from), ('date', '<=', self.date_to)])
        shifts = timesheets.mapped('task_shift_id')
        seq = 1
        work_entry_type = self.env['hr.work.entry.type'].search([('code', '=', 'TIME100')], limit=1)
        if shifts:
            for shift in shifts:
                work_entry = timesheets.filtered(lambda x: x.task_shift_id.id == shift.id)
                task_of_day = len(work_entry.mapped('date'))
                hours_sum = sum([y.unit_amount for y in work_entry])
                res.append({
                    'sequence': seq,
                    'work_entry_type_id': shift.hr_work_entry_type.id if shift.hr_work_entry_type else work_entry_type.id,
                    'number_of_days': task_of_day,
                    'number_of_hours': hours_sum,
                    'shift_id': shift.id,
                    'name': str(shift.task_shift_id.name),
                    'code': shift.hr_work_entry_type.code if shift.task_shift_id else work_entry_type.code,
                    'payslip_id': self.id
                })
                seq += 1
        return res
