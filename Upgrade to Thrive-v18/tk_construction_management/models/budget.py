from thrive import api, fields, models, _


class SubProjectBudget(models.Model):
    _name = 'sub.project.budget'
    _description = "Sub Project Budget"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Title")
    progress = fields.Float(string="Budget Utilization(%)",
                            compute="compute_used_budget")
    total_budget_amount = fields.Monetary(
        string="Total Budget Amount", compute="compute_used_budget")
    utilization_amount = fields.Monetary(
        string="Budget Utilization", compute="compute_used_budget")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    site_id = fields.Many2one('tk.construction.site', string="Project")
    sub_project_id = fields.Many2one(
        'tk.construction.project', string="Sub Project")
    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user and self.env.user.id or False,
                                     string="Responsible")
    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    status = fields.Selection([('draft', 'Draft'), ('waiting_approval', 'Waiting Approval'), ('approved', 'Approved'),
                               ('in_progress', 'In Progress'), ('complete',
                                                                'Complete'), ('cancel', 'Cancel'),
                               ('reject', 'Reject')], default='draft')
    budget_count = fields.Integer(
        string="Budget Line Count", compute="compute_count")
    reject_reason = fields.Text(string="Reject Reason")
    budget_line_ids = fields.One2many(
        'project.budget', 'sub_project_budget_id')

    def compute_count(self):
        for rec in self:
            rec.budget_count = self.env['project.budget'].search_count(
                [('sub_project_budget_id', '=', rec.id)])

    def action_view_budget_line(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Budget'),
            'res_model': 'project.budget',
            'domain': [('sub_project_budget_id', '=', self.id)],
            'context': {'default_sub_project_budget_id': self.id},
            'view_mode': 'tree,kanban,form',
            'target': 'current'
        }

    def action_department_approval(self):
        self.status = 'waiting_approval'

    def action_approve_budget(self):
        self.status = 'approved'

    def action_reject_budget(self):
        self.status = 'reject'

    def action_complete_budget(self):
        self.status = 'complete'

    def action_cancel_budget(self):
        self.status = 'cancel'

    def action_reset_draft_budget(self):
        self.status = 'draft'

    @api.depends('budget_line_ids', 'budget_line_ids.budget', 'budget_line_ids.remaining_budget')
    def compute_used_budget(self):
        for rec in self:
            utilize_budget = 0.0
            total_budget_amount = 0.0
            remaining_budget_amount = 0.0
            for data in rec.budget_line_ids:
                total_budget_amount = total_budget_amount + data.budget
                remaining_budget_amount = remaining_budget_amount + data.remaining_budget
            utilize_budget = 100 - (
                (remaining_budget_amount * 100 / total_budget_amount) if total_budget_amount > 0 else 100)
            rec.progress = round(utilize_budget, 1)
            rec.total_budget_amount = total_budget_amount
            rec.utilization_amount = total_budget_amount - remaining_budget_amount


class ProjectBudget(models.Model):
    _name = 'project.budget'
    _description = "Project Budget"
    _rec_name = 'job_type_id'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    sub_project_budget_id = fields.Many2one(
        'sub.project.budget', string="Sub Project Budget")
    project_id = fields.Many2one(
        related="sub_project_budget_id.sub_project_id", string="Project")
    site_id = fields.Many2one(
        related="project_id.construction_site_id", string="Site")
    job_type_id = fields.Many2one('job.type', string="Work Type")
    sub_category_ids = fields.Many2many(
        related="job_type_id.sub_category_ids", string="Sub Categories")
    sub_category_id = fields.Many2one(
        'job.sub.category', string="Work Sub Type", domain="[('id','in',sub_category_ids)]")
    boq_qty = fields.Float(string="BOQ Qty")
    additional_qty = fields.Float(string="Add. Qty", help="Additional Qty")
    total_qty = fields.Float(string="Total Qty.", compute="compute_total_qty")
    rate_analysis_id = fields.Many2one('rate.analysis', string="Rate Analysis")
    price_per_qty = fields.Monetary(
        string="Price / Qty", compute="compute_rate_analysis_info", store=True)
    untaxed_amount = fields.Monetary(
        string="Untaxed Amount", compute="compute_rate_analysis_info", store=True)
    tax_amount = fields.Monetary(
        string="Tax Amount", compute="compute_rate_analysis_info", store=True)
    budget = fields.Monetary(string="Total Budget Amount",
                             compute="compute_rate_analysis_info", store=True)
    # Spent
    material_spent = fields.Monetary(
        string="Material Spent", compute="_compute_budget_calculation")
    equipment_spent = fields.Monetary(
        string="Equipment Spent", compute="_compute_budget_calculation")
    labour_spent = fields.Monetary(
        string="Labour Spent", compute="_compute_budget_calculation")
    overhead_spent = fields.Monetary(
        string="Overhead Spent", compute="_compute_budget_calculation")
    remaining_budget = fields.Monetary(
        string="Remaining Budget", compute="_compute_budget_calculation")

    # Spent in Percentage
    total_spent = fields.Float(
        string="Utilization(%)", compute="_compute_budget_calculation")
    boq_used_qty = fields.Float(
        string="Used Qty", compute="_compute_budget_calculation")

    @api.depends('boq_qty', 'additional_qty')
    def compute_total_qty(self):
        for rec in self:
            rec.total_qty = rec.boq_qty + rec.additional_qty

    @api.depends('rate_analysis_id', 'rate_analysis_id.total_amount', 'rate_analysis_id.untaxed_amount',
                 'rate_analysis_id.tax_amount', 'total_qty')
    def compute_rate_analysis_info(self):
        for rec in self:
            untaxed_amount = 0.0
            tax_amount = 0.0
            price_per_qty = 0.0
            budget = 0.0
            if rec.rate_analysis_id:
                price_per_qty = rec.rate_analysis_id.total_amount
                untaxed_amount = rec.rate_analysis_id.untaxed_amount
                tax_amount = rec.rate_analysis_id.tax_amount
                budget = rec.total_qty * price_per_qty
            rec.untaxed_amount = untaxed_amount
            rec.tax_amount = tax_amount
            rec.price_per_qty = price_per_qty
            rec.budget = budget

    @api.depends('project_id', 'sub_category_id', 'job_type_id', 'budget', 'total_qty')
    def _compute_budget_calculation(self):
        for rec in self:
            budget_phase_ids = self.env['job.costing'].search(
                [('project_id', '=', rec.project_id.id), ('activity_id', '=', rec.job_type_id.id)]).mapped('id')
            domain = [('project_id', '=', rec.project_id.id), ('work_type_id', '=', rec.job_type_id.id),
                      ('sub_category_id', '=',
                       rec.sub_category_id.id), ('state', '=', 'complete'),
                      ('job_sheet_id', 'in', budget_phase_ids)]
            material_spent = sum(self.env['order.material.line'].search(
                domain).mapped('total_price'))
            equipment_spent = sum(self.env['order.equipment.line'].search(
                domain).mapped('total_cost'))
            labour_spent = sum(self.env['order.labour.line'].search(
                domain).mapped('sub_total'))
            overhead_spent = sum(self.env['order.overhead.line'].search(
                domain).mapped('sub_total'))
            remaining_budget = rec.budget - \
                (material_spent + equipment_spent + labour_spent + overhead_spent)
            total_spent = 100 - \
                ((remaining_budget * 100 / rec.budget) if rec.budget > 0 else 100)
            boq_used_qty = rec.total_qty - (
                (remaining_budget * rec.total_qty / rec.budget) if rec.budget > 0 else rec.total_qty)
            rec.equipment_spent = equipment_spent
            rec.labour_spent = labour_spent
            rec.overhead_spent = overhead_spent
            rec.material_spent = material_spent
            rec.remaining_budget = remaining_budget
            rec.total_spent = round(total_spent, 1)
            rec.boq_used_qty = boq_used_qty

    def action_view_material_budget(self):
        budget_phase_ids = self.env['job.costing'].search(
            [('project_id', '=', self.project_id.id), ('activity_id', '=', self.job_type_id.id)]).mapped('id')
        domain = [('project_id', '=', self.project_id.id), ('work_type_id', '=', self.job_type_id.id),
                  ('sub_category_id', '=',
                   self.sub_category_id.id), ('state', '=', 'complete'),
                  ('job_sheet_id', 'in', budget_phase_ids)]
        ids = self.env['order.material.line'].search(domain).mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Material'),
            'res_model': 'order.material.line',
            'domain': [('id', 'in', ids)],
            'context': {'create': False},
            'view_mode': 'tree',
            'target': 'current'
        }

    def action_view_equipment_budget(self):
        budget_phase_ids = self.env['job.costing'].search(
            [('project_id', '=', self.project_id.id), ('activity_id', '=', self.job_type_id.id)]).mapped('id')
        domain = [('project_id', '=', self.project_id.id), ('work_type_id', '=', self.job_type_id.id),
                  ('sub_category_id', '=',
                   self.sub_category_id.id), ('state', '=', 'complete'),
                  ('job_sheet_id', 'in', budget_phase_ids)]
        ids = self.env['order.equipment.line'].search(domain).mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Equipment'),
            'res_model': 'order.equipment.line',
            'domain': [('id', 'in', ids)],
            'context': {'create': False},
            'view_mode': 'tree',
            'target': 'current'
        }

    def action_view_labour_budget(self):
        budget_phase_ids = self.env['job.costing'].search(
            [('project_id', '=', self.project_id.id), ('activity_id', '=', self.job_type_id.id)]).mapped('id')
        domain = [('project_id', '=', self.project_id.id), ('work_type_id', '=', self.job_type_id.id),
                  ('sub_category_id', '=',
                   self.sub_category_id.id), ('state', '=', 'complete'),
                  ('job_sheet_id', 'in', budget_phase_ids)]
        ids = self.env['order.labour.line'].search(domain).mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Labour'),
            'res_model': 'order.labour.line',
            'domain': [('id', 'in', ids)],
            'context': {'create': False},
            'view_mode': 'tree',
            'target': 'current'
        }

    def action_view_overhead_budget(self):
        budget_phase_ids = self.env['job.costing'].search(
            [('project_id', '=', self.project_id.id), ('activity_id', '=', self.job_type_id.id)]).mapped('id')
        domain = [('project_id', '=', self.project_id.id), ('work_type_id', '=', self.job_type_id.id),
                  ('sub_category_id', '=',
                   self.sub_category_id.id), ('state', '=', 'complete'),
                  ('job_sheet_id', 'in', budget_phase_ids)]
        ids = self.env['order.overhead.line'].search(domain).mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Overhead'),
            'res_model': 'order.overhead.line',
            'domain': [('id', 'in', ids)],
            'context': {'create': False},
            'view_mode': 'tree',
            'target': 'current'
        }
