from thrive import api, fields, models, _
from thrive.exceptions import ValidationError


class ProjectWBS(models.TransientModel):
    _name = 'project.wbs'
    _description = "Sub Project WBS"

    name = fields.Char(string="Title")
    work_type_ids = fields.Many2many('job.type', string="Work Type Jobs", compute="compute_work_type_ids")
    activity_id = fields.Many2one('job.type', string="Work Type", domain="[('id','in',work_type_ids)]")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    sub_project_id = fields.Many2one('tk.construction.project', string="Sub Project")
    project_start_date = fields.Date(related="sub_project_id.start_date", store=True)
    project_end_date = fields.Date(related="sub_project_id.end_date", store=True)

    @api.model
    def default_get(self, fields):
        res = super(ProjectWBS, self).default_get(fields)
        active_id = self._context.get('active_id')
        res['sub_project_id'] = active_id
        return res

    def action_create_project_phase(self):
        active_id = self._context.get('active_id')
        sub_project_id = self.env['tk.construction.project'].browse(active_id)
        phase_id = self.env['job.costing'].create({
            'title': self.name,
            'activity_id': self.activity_id.id,
            'create_date': self.start_date,
            'close_date': self.end_date,
            'site_id': sub_project_id.construction_site_id.id,
            'project_id': sub_project_id.id,
            'department_id': sub_project_id.department_id.id,
            'manager_ids': sub_project_id.manager_ids.ids,
            'user_id': sub_project_id.user_id.id
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Project Phase(WBS)'),
            'res_model': 'job.costing',
            'res_id': phase_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    @api.constrains('project_start_date', 'project_end_date', 'start_date')
    def _check_wbs_start_date(self):
        for record in self:
            if record.project_start_date and record.project_end_date:
                if not record.project_start_date <= record.start_date <= record.project_end_date:
                    raise ValidationError("Invalid start date. Must be within sub project start and end dates.")

    @api.constrains('start_date', 'project_end_date', 'end_date')
    def _check_wbs_end_date(self):
        for record in self:
            if record.start_date and record.project_end_date:
                if not record.project_end_date >= record.end_date > record.start_date:
                    raise ValidationError(
                        "Invalid end date. Must be within start date and sub project end date.")

    @api.depends('activity_id', 'sub_project_id')
    def compute_work_type_ids(self):
        ids = self.sub_project_id.boq_budget_ids.mapped('activity_id').mapped('id')
        self.work_type_ids = ids
