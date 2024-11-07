# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, api, models, _
from thrive.exceptions import ValidationError


class JobCosting(models.Model):
    _name = 'job.costing'
    _description = "Job Costing"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string="Title")
    create_date = fields.Date(string="Start Date", default=fields.Date.today())
    close_date = fields.Date(string="End Date")
    status = fields.Selection([('draft', 'Draft'), ('waiting_approval', 'Waiting Approval'), ('approved', 'Approved'),
                               ('in_progress', 'In Progress'), ('complete', 'Complete'), ('cancel', 'Cancel'),
                               ('reject', 'Reject')], default='draft', tracking=True)

    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user and self.env.user.id or False,
                                     string="Created By")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    site_id = fields.Many2one('tk.construction.site', string="Project")
    project_id = fields.Many2one('tk.construction.project', string="Sub Project")
    activity_id = fields.Many2one('job.type', string="Work Type")

    # Department
    department_id = fields.Many2one('construction.department', string="Department")
    manager_ids = fields.Many2many('res.users', string="Manager")
    user_id = fields.Many2one('res.users', string="Responsible")

    # One2 many
    work_order_ids = fields.One2many('job.order', 'job_sheet_id')
    cost_material_ids = fields.One2many('cost.material.line', 'job_costing_id')
    cost_equipment_ids = fields.One2many('cost.equipment.line', 'job_costing_id')
    cost_labour_ids = fields.One2many('cost.labour.line', 'job_costing_id')
    cost_overhead_ids = fields.One2many('cost.overhead.line', 'job_costing_id')

    # Total
    material_total_cost = fields.Monetary(string="Total Material Cost", compute="_compute_total")
    equipment_total_cost = fields.Monetary(string="Total Equipment Cost", compute="_compute_total")
    labour_total_cost = fields.Monetary(string="Total Labour Cost", compute="_compute_total")
    overhead_total_cost = fields.Monetary(string="Total Overhead Cost", compute="_compute_total")
    material_actual_cost = fields.Monetary(string="Actual Material Cost", compute="_compute_total")
    equipment_actual_cost = fields.Monetary(string="Actual Equipment Cost", compute="_compute_total")
    labour_actual_cost = fields.Monetary(string="Actual Labour Cost", compute="_compute_total")
    overhead_actual_cost = fields.Monetary(string="Actual Overhead Cost", compute="_compute_total")

    # Count
    job_order_count = fields.Integer(string="Jon Order", compute="_compute_count")
    mrq_count = fields.Integer(string="MRQ Order", compute="_compute_count")

    # Budget Qty.
    sub_work_type_ids = fields.Many2many('job.sub.category')

    # Create, Write, Unlink, Constrain
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New') and vals.get('project_id'):
                project_id = self.env['tk.construction.project'].browse(vals.get('project_id'))
                vals['name'] = str(project_id.code) + "/" + (
                        self.env['ir.sequence'].next_by_code('job.costing') or _('New'))
        res = super(JobCosting, self).create(vals_list)
        return res

    def name_get(self):
        data = []
        for rec in self:
            data.append((rec.id, '%s - %s' % (rec.name, rec.title)))
        return data

    # Onchange
    @api.onchange('project_id')
    def _onchange_project_info(self):
        for rec in self:
            rec.project_id = rec.project_id.id
            rec.department_id = rec.project_id.department_id.id
            rec.manager_ids = rec.project_id.manager_ids.ids
            rec.user_id = rec.project_id.user_id.id

    # Compute
    @api.depends('cost_material_ids', 'cost_equipment_ids', 'cost_labour_ids', 'cost_overhead_ids')
    def _compute_total(self):
        material, equipment, labour, overhead = 0.0, 0.0, 0.0, 0.0
        material_actual_cost = self.env['order.material.line'].search(
            [('job_sheet_id', '=', self.id), ('state', '=', 'complete')]).mapped(
            'total_price')
        equipment_actual_cost = self.env['order.equipment.line'].search(
            [('job_sheet_id', '=', self.id), ('state', '=', 'complete')]).mapped(
            'total_cost')
        labour_actual_cost = self.env['order.labour.line'].search(
            [('job_sheet_id', '=', self.id), ('state', '=', 'complete')]).mapped(
            'sub_total')
        overhead_actual_cost = self.env['order.overhead.line'].search(
            [('job_sheet_id', '=', self.id), ('state', '=', 'complete')]).mapped(
            'sub_total')
        for rec in self:
            for data in rec.cost_material_ids:
                material = material + data.total_cost
            for data in rec.cost_equipment_ids:
                equipment = equipment + data.total_cost
            for data in rec.cost_labour_ids:
                labour = labour + data.sub_total
            for data in rec.cost_overhead_ids:
                overhead = overhead + data.sub_total
            rec.material_total_cost = material
            rec.equipment_total_cost = equipment
            rec.labour_total_cost = labour
            rec.overhead_total_cost = overhead
            rec.material_actual_cost = sum(material_actual_cost)
            rec.equipment_actual_cost = sum(equipment_actual_cost)
            rec.labour_actual_cost = sum(labour_actual_cost)
            rec.overhead_actual_cost = sum(overhead_actual_cost)

    def _compute_count(self):
        for rec in self:
            rec.job_order_count = self.env['job.order'].search_count([('job_sheet_id', '=', rec.id)])
            rec.mrq_count = self.env['material.requisition'].search_count([('job_sheet_id', '=', rec.id)])

    # Smart Button
    def action_view_job_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order'),
            'res_model': 'job.order',
            'domain': [('job_sheet_id', '=', self.id)],
            'context': {'create': False},
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_mrq(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Material Requisition'),
            'res_model': 'material.requisition',
            'domain': [('job_sheet_id', '=', self.id)],
            'context': {'default_job_sheet_id': self.id},
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_department_approval(self):
        self.status = 'waiting_approval'

    def action_approve_phase(self):
        self.status = 'approved'

    def action_reject_phase(self):
        self.status = 'reject'

    def action_in_progress(self):
        self.status = 'in_progress'

    def action_reset_to_draft(self):
        self.status = 'draft'

    def action_cancel_phase(self):
        self.status = 'cancel'

    def action_complete_phase(self):
        is_complete_work_order = True
        for data in self.work_order_ids:
            if data.state != 'complete':
                is_complete_work_order = False
                break
        if not is_complete_work_order:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': "Please complete all work orders related to this phase.",
                    'sticky': False,
                }
            }
            return message

        if is_complete_work_order:
            self.status = 'complete'

    def action_create_work_order(self):
        material_line = []
        equipment_line = []
        labour_line = []
        overhead_line = []
        ctx = {
            'default_site_id': self.site_id.id,
            'default_project_id': self.project_id.id,
            'default_start_date': self.create_date,
            'default_end_date': self.close_date,
            'default_work_type_id': self.activity_id.id,
            'default_job_sheet_id': self.id,
            'default_department_id': self.department_id.id,
            'default_manager_ids': self.manager_ids.ids,
            'default_user_id': self.user_id.id
        }
        for data in self.cost_material_ids:
            material_line.append((0, 0, {
                'sub_category_id': data.sub_category_id.id,
                'material_id': data.material_id.id,
                'name': data.name,
                'qty': data.forcast_qty,
                'remain_qty': data.forcast_qty,
                'phase_forcast_qty': data.forcast_qty,
                'tax_id': data.tax_id.id,
                'price': data.cost
            }))
        for data in self.cost_equipment_ids:
            equipment_line.append((0, 0, {
                'sub_category_id': data.sub_category_id.id,
                'equipment_id': data.equipment_id.id,
                'cost_type': data.cost_type,
                'desc': data.name,
                'qty': data.forcast_qty,
                'cost': data.cost,
                'phase_forcast_qty': data.forcast_qty,
                'tax_id': data.tax_id.id,
            }))
        for data in self.cost_labour_ids:
            labour_line.append((0, 0, {
                'sub_category_id': data.sub_category_id.id,
                'product_id': data.product_id.id,
                'name': data.name,
                'hours': data.forcast_qty,
                'cost': data.cost,
                'phase_forcast_qty': data.forcast_qty,
                'tax_id': data.tax_id.id,
            }))
        for data in self.cost_overhead_ids:
            overhead_line.append((0, 0, {
                'sub_category_id': data.sub_category_id.id,
                'product_id': data.product_id.id,
                'name': data.name,
                'qty': data.forcast_qty,
                'cost': data.cost,
                'phase_forcast_qty': data.forcast_qty,
                'tax_id': data.tax_id.id,
            }))
        ctx['default_material_order_ids'] = material_line
        ctx['default_equipment_order_ids'] = equipment_line
        ctx['default_labour_order_ids'] = labour_line
        ctx['default_overhead_order_ids'] = overhead_line
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order'),
            'res_model': 'job.order',
            'context': ctx,
            'view_mode': 'form',
            'target': 'new'
        }


class CostMaterialLine(models.Model):
    _name = 'cost.material.line'
    _description = 'Construction Job Cost Material Line'

    material_id = fields.Many2one('product.product', string="Material", domain="[('is_material','=',True)]")
    name = fields.Char(string="Description")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    qty = fields.Integer(string="Qty.", default=1)
    cost = fields.Float(string="Cost")
    total_cost = fields.Monetary(string="Total Cost", compute="_compute_total_cost", store=True)
    uom_id = fields.Many2one(related="material_id.uom_po_id", string="Unit of Measure")
    job_costing_id = fields.Many2one('job.costing', string="Job Costing")
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    tax_id = fields.Many2one('account.tax', string="Taxes")
    budget_qty = fields.Float(string="Budget Qty.", compute="compute_budget_qty", store=True)
    boq_per_qty = fields.Float(string="Per BOQ RA. Qty.")
    total_remain_boq_qty = fields.Float(string="Total Remain BOQ Qty")
    forcast_qty = fields.Float(string="Forcast Qty.", compute="compute_forcast_qty")
    used_qty = fields.Float(string="Used Qty.")
    used_budget_qty = fields.Float(string="Used Budget Qty.")
    remain_qty = fields.Float(string="Remain Qty.", compute="compute_remain_qty")

    @api.onchange('material_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.material_id.name
            rec.cost = rec.material_id.standard_price

    @api.depends('material_id', 'qty', 'cost', 'tax_id')
    def _compute_total_cost(self):
        for rec in self:
            total_cost = 0.0
            tax_amount = 0.0
            if rec.material_id:
                total_cost = rec.qty * rec.cost
            if rec.tax_id:
                tax_amount = rec.tax_id.amount * (rec.qty * rec.cost) / 100
                total_cost = tax_amount + total_cost
            rec.total_cost = total_cost

    @api.depends('boq_per_qty', 'qty')
    def compute_budget_qty(self):
        for rec in self:
            budget_qty = 0
            if rec.boq_per_qty > 0:
                budget_qty = rec.qty / rec.boq_per_qty
            rec.budget_qty = budget_qty

    @api.depends('qty',
                 'job_costing_id.activity_id',
                 'material_id',
                 'sub_category_id',
                 'job_costing_id.work_order_ids.material_order_ids.qty')
    def compute_forcast_qty(self):
        for rec in self:
            forcast_qty = 0.0
            for record in rec.job_costing_id.work_order_ids:
                for data in record.material_order_ids:
                    if data.material_id.id == rec.material_id.id and data.sub_category_id.id == rec.sub_category_id.id:
                        forcast_qty = forcast_qty + data.qty
            rec.forcast_qty = rec.qty - forcast_qty

    @api.depends('job_costing_id.work_order_ids.material_order_ids.qty', 'job_costing_id.work_order_ids.state', 'qty')
    def compute_remain_qty(self):
        for rec in self:
            remain_qty = 0.0
            for record in rec.job_costing_id.work_order_ids:
                if record.state == 'complete':
                    for data in record.material_order_ids:
                        if data.material_id.id == rec.material_id.id and data.sub_category_id.id == rec.sub_category_id.id:
                            remain_qty = remain_qty + data.qty
            rec.remain_qty = rec.qty - remain_qty


class CostEquipmentLine(models.Model):
    _name = 'cost.equipment.line'
    _description = 'Construction Job Cost Equipment Line'

    equipment_id = fields.Many2one('product.product', string="Equipment", domain="[('is_equipment','=',True)]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    cost_type = fields.Selection(
        [('depreciation_cost', 'Depreciation Cost'), ('investment_cost', 'Investment/Interest Cost'),
         ('tax', 'Tax'), ('rent', 'Rent'), ('other', 'Other')], string="Type", default='rent')
    name = fields.Char(string='Description')
    qty = fields.Integer(string="Qty.", default=1)
    cost = fields.Monetary(string="Estimation Cost")
    total_cost = fields.Monetary(string="Total Cost", compute="_compute_total_cost", store=True)
    job_costing_id = fields.Many2one('job.costing', string="Job Costing")
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    tax_id = fields.Many2one('account.tax', string="Taxes")
    budget_qty = fields.Float(string="Budget Qty.", compute="compute_budget_qty", store=True)
    boq_per_qty = fields.Float(string="Per BOQ RA. Qty.")
    total_remain_boq_qty = fields.Float(string="Total Remain BOQ Qty")
    forcast_qty = fields.Float(string="Forcast Qty.", compute="compute_forcast_qty")
    used_qty = fields.Float(string="Used Qty.")
    used_budget_qty = fields.Float(string="Used Budget Qty.")
    remain_qty = fields.Float(string="Remain Qty.", compute="compute_remain_qty")

    @api.depends('equipment_id', 'qty', 'cost', 'tax_id')
    def _compute_total_cost(self):
        for rec in self:
            total_cost = 0.0
            if rec.equipment_id:
                total_cost = rec.qty * rec.cost
            if rec.tax_id:
                tax_amount = rec.tax_id.amount * (rec.qty * rec.cost) / 100
                total_cost = tax_amount + total_cost
            rec.total_cost = total_cost

    @api.onchange('equipment_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.equipment_id.name
            rec.cost = rec.equipment_id.standard_price

    @api.depends('boq_per_qty', 'qty')
    def compute_budget_qty(self):
        for rec in self:
            budget_qty = 0
            if rec.boq_per_qty > 0:
                budget_qty = rec.qty / rec.boq_per_qty
            rec.budget_qty = budget_qty

    @api.depends('qty',
                 'job_costing_id.activity_id',
                 'equipment_id',
                 'sub_category_id',
                 'job_costing_id.work_order_ids.equipment_order_ids.qty')
    def compute_forcast_qty(self):
        for rec in self:
            forcast_qty = 0.0
            for record in rec.job_costing_id.work_order_ids:
                for data in record.equipment_order_ids:
                    if data.equipment_id.id == rec.equipment_id.id and data.sub_category_id.id == rec.sub_category_id.id:
                        forcast_qty = forcast_qty + data.qty
            rec.forcast_qty = rec.qty - forcast_qty

    @api.depends('job_costing_id.work_order_ids.equipment_order_ids.qty', 'job_costing_id.work_order_ids.state', 'qty')
    def compute_remain_qty(self):
        for rec in self:
            remain_qty = 0.0
            for record in rec.job_costing_id.work_order_ids:
                if record.state == 'complete':
                    for data in record.equipment_order_ids:
                        if data.equipment_id.id == rec.equipment_id.id and data.sub_category_id.id == rec.sub_category_id.id:
                            remain_qty = remain_qty + data.qty
            rec.remain_qty = rec.qty - remain_qty


class CostLabourLine(models.Model):
    _name = 'cost.labour.line'
    _description = "Cost Labour Line"

    job_costing_id = fields.Many2one('job.costing', string="Job Costing")
    product_id = fields.Many2one('product.product', string="Product", domain="[('is_labour','=',True)]")
    name = fields.Char(string="Description")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    hours = fields.Float(string="Hours")
    remain_hours = fields.Float(string="Remaining Hours")
    cost = fields.Monetary(string="Cost / Hour")
    sub_total = fields.Monetary(string="Sub Total", compute="_compute_total_cost", store=True)
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    tax_id = fields.Many2one('account.tax', string="Taxes")
    budget_qty = fields.Float(string="Budget Qty.", compute="compute_budget_qty", store=True)
    boq_per_qty = fields.Float(string="Per BOQ RA. Qty.")
    total_remain_boq_qty = fields.Float(string="Total Remain BOQ Qty")
    forcast_qty = fields.Float(string="Forcast Hours", compute="compute_forcast_qty")
    used_qty = fields.Float(string="Used Qty.")
    used_budget_qty = fields.Float(string="Used Budget Qty.")
    remain_qty = fields.Float(string="Remain Hours", compute="compute_remain_qty")

    @api.onchange('product_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.product_id.name
            rec.cost = rec.product_id.standard_price

    @api.depends('product_id', 'hours', 'cost', 'tax_id')
    def _compute_total_cost(self):
        for rec in self:
            total_cost = 0.0
            if rec.product_id:
                total_cost = rec.hours * rec.cost
            if rec.tax_id:
                tax_amount = rec.tax_id.amount * (rec.hours * rec.cost) / 100
                total_cost = tax_amount + total_cost
            rec.sub_total = total_cost

    @api.depends('boq_per_qty', 'hours')
    def compute_budget_qty(self):
        for rec in self:
            budget_qty = 0
            if rec.boq_per_qty > 0:
                budget_qty = rec.hours / rec.boq_per_qty
            rec.budget_qty = budget_qty

    @api.depends('hours',
                 'job_costing_id.activity_id',
                 'product_id',
                 'sub_category_id',
                 'job_costing_id.work_order_ids.labour_order_ids.hours')
    def compute_forcast_qty(self):
        for rec in self:
            forcast_qty = 0.0
            for record in rec.job_costing_id.work_order_ids:
                for data in record.labour_order_ids:
                    if data.product_id.id == rec.product_id.id and data.sub_category_id.id == rec.sub_category_id.id:
                        forcast_qty = forcast_qty + data.hours
            rec.forcast_qty = rec.hours - forcast_qty

    @api.depends('job_costing_id.work_order_ids.labour_order_ids.hours', 'job_costing_id.work_order_ids.state', 'hours')
    def compute_remain_qty(self):
        for rec in self:
            remain_qty = 0.0
            for record in rec.job_costing_id.work_order_ids:
                if record.state == 'complete':
                    for data in record.labour_order_ids:
                        if data.product_id.id == rec.product_id.id and data.sub_category_id.id == rec.sub_category_id.id:
                            remain_qty = remain_qty + data.hours
            rec.remain_qty = rec.hours - remain_qty


class CostOverheadLine(models.Model):
    _name = 'cost.overhead.line'
    _description = "Cost Overhead Line"

    job_costing_id = fields.Many2one('job.costing', string="Job Costing")
    product_id = fields.Many2one('product.product', string="Product", domain="[('is_overhead','=',True)]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    name = fields.Char(string="Description")
    qty = fields.Integer(string="Qty.", default=1)
    uom_id = fields.Many2one(related="product_id.uom_po_id", string="UOM")
    cost = fields.Monetary(string="Cost / Unit")
    sub_total = fields.Monetary(string="Sub Total", compute="_compute_total_cost", store=True)
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    tax_id = fields.Many2one('account.tax', string="Taxes")
    budget_qty = fields.Float(string="Budget Qty.", compute="compute_budget_qty", store=True)
    boq_per_qty = fields.Float(string="Per BOQ RA. Qty.")
    total_remain_boq_qty = fields.Float(string="Total Remain BOQ Qty")
    forcast_qty = fields.Float(string="Forcast Qty.", compute="compute_forcast_qty")
    used_qty = fields.Float(string="Used Qty.")
    used_budget_qty = fields.Float(string="Used Budget Qty.")
    remain_qty = fields.Float(string="Remain Qty.", compute="compute_remain_qty")

    @api.depends('product_id', 'qty', 'cost', 'tax_id')
    def _compute_total_cost(self):
        for rec in self:
            total_cost = 0.0
            if rec.product_id:
                total_cost = rec.qty * rec.cost
            if rec.tax_id:
                tax_amount = rec.tax_id.amount * (rec.qty * rec.cost) / 100
                total_cost = tax_amount + total_cost
            rec.sub_total = total_cost

    @api.onchange('product_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.product_id.name
            rec.cost = rec.product_id.standard_price

    @api.depends('boq_per_qty', 'qty')
    def compute_budget_qty(self):
        for rec in self:
            budget_qty = 0
            if rec.boq_per_qty > 0:
                budget_qty = rec.qty / rec.boq_per_qty
            rec.budget_qty = budget_qty

    @api.depends('qty',
                 'job_costing_id.activity_id',
                 'product_id',
                 'sub_category_id',
                 'job_costing_id.work_order_ids.overhead_order_ids.qty')
    def compute_forcast_qty(self):
        for rec in self:
            forcast_qty = 0.0
            for record in rec.job_costing_id.work_order_ids:
                for data in record.overhead_order_ids:
                    if data.product_id.id == rec.product_id.id and data.sub_category_id.id == rec.sub_category_id.id:
                        forcast_qty = forcast_qty + data.qty
            rec.forcast_qty = rec.qty - forcast_qty

    @api.depends('job_costing_id.work_order_ids.overhead_order_ids.qty', 'job_costing_id.work_order_ids.state', 'qty')
    def compute_remain_qty(self):
        for rec in self:
            remain_qty = 0.0
            for record in rec.job_costing_id.work_order_ids:
                if record.state == 'complete':
                    for data in record.overhead_order_ids:
                        if data.product_id.id == rec.product_id.id and data.sub_category_id.id == rec.sub_category_id.id:
                            remain_qty = remain_qty + data.qty
            rec.remain_qty = rec.qty - remain_qty
