from thrive import models, fields, api, _
from thrive.exceptions import UserError


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    planning_slot_ids = fields.One2many('planning.slot', 'attendance_id')
    planning_slot_id = fields.Many2one('planning.slot', compute='_compute_planning_slot_id')
    # timesheet_id = fields.Many2one('account.analytic.line')

    @api.depends('planning_slot_ids')
    def _compute_planning_slot_id(self):
        for r in self:
            r.planning_slot_id = r.planning_slot_ids[:1]

    @api.model
    def action_view_today_attendance(self):
        action = self.env['ir.actions.act_window']._for_xml_id('hr_attendance.hr_attendance_action')
        action['context'] = {
            'search_default_filter_today_attendance': 1
        }
        action['view_mode'] = 'tree,form'
        return action

    # def action_bulk_create_timesheet(self):
    #     for r in self:
    #         if not r.planning_slot_id:
    #             raise UserError(
    #                 _('No planning slot in the attendance record: %s, please check in attendance first') % r)
    #     self.planning_slot_id.action_bulk_create_timesheet()
    #     return self._action_client_notify(message="Success")
