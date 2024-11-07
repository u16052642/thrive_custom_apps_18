# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import api, fields, models, _
from thrive.exceptions import ValidationError


class EquipmentSubcontract(models.Model):
    _name = 'equipment.subcontract'
    _description = "Equipment Subcontract"
    _rec_name = 'seq'

    seq = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    name = fields.Char(string="Title")
    equipment_id = fields.Many2one('product.product', string="Equipment", domain="[('is_equipment','=',True)]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    cost_type = fields.Selection([('depreciation_cost', 'Depreciation Cost'),
                                  ('investment_cost', 'Investment/Interest Cost'),
                                  ('tax', 'Tax'),
                                  ('rent', 'Rent'),
                                  ('other', 'Other')], string="Type ", default='rent')
    cost = fields.Monetary(string="Estimation Cost")
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    job_type_id = fields.Many2one('job.type', string="Work Type")
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    stage = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done')], default='draft')
    po_bill = fields.Selection([('bill', 'Bill'), ('purchase_order', 'Purchase Order')], string="Type", default='bill')
    ra_bill_ids = fields.One2many('equip.contract.line', 'contract_id', string="Ra Bills")
    completion_date = fields.Date(string="Completion Date", compute="compute_completion_date")

    # Calculation
    qty = fields.Integer(string="Qty.", default=1)
    remain_qty = fields.Integer(string="Remaining Qty")
    total_cost = fields.Monetary(string="Total Cost")
    remaining_amount = fields.Monetary(string="Remaining Amount")
    progress = fields.Float(string="Complete Billing", compute="_compute_payment_progress")
    tax_id = fields.Many2one('account.tax', string='Tax')

    # Project Details
    job_order_id = fields.Many2one('job.order', string="Work Order")
    phase_id = fields.Many2one(related="job_order_id.job_sheet_id", string="Project Phase(WBS)", store=True)
    project_id = fields.Many2one(related='job_order_id.project_id', string="Sub Project", store=True)
    task_id = fields.Many2one(related="job_order_id.task_id", string="Task", store=True)

    # Department
    department_id = fields.Many2one(related="job_order_id.department_id", string="Department", store=True)
    manager_ids = fields.Many2many('res.users', store=True, string="Manager")
    user_id = fields.Many2one(related="job_order_id.user_id", string="Responsible")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('seq', _('New')) == _('New'):
                vals['seq'] = self.env['ir.sequence'].next_by_code('equip.sub') or _('New')
        res = super(EquipmentSubcontract, self).create(vals_list)
        return res

    def action_in_progress(self):
        self.stage = 'in_progress'

    def action_state_done(self):
        self.stage = 'done'

    @api.constrains('ra_bill_ids', 'qty')
    def _check_ra_bill_qty(self):
        qty = 0
        for record in self.ra_bill_ids:
            if record.qc_status != 'reject':
                qty = qty + record.qty
        if qty > self.qty:
            raise ValidationError(_("Quantity should be less than total qty."))

    @api.depends('total_cost', 'remaining_amount')
    def _compute_payment_progress(self):
        for rec in self:
            progress = 0.0
            if rec.total_cost and rec.remaining_amount:
                progress = (rec.remaining_amount * 100) / rec.total_cost
            rec.progress = 100 - progress

    @api.depends('stage', 'ra_bill_ids')
    def compute_completion_date(self):
        for rec in self:
            date = None
            if rec.stage == "done":
                dates = rec.ra_bill_ids.mapped('date')
                if dates:
                    date = dates[-1]
            rec.completion_date = date


class EquipContractLine(models.Model):
    _name = 'equip.contract.line'
    _description = "Equip Contract Line"
    _rec_name = 'remark'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    contract_id = fields.Many2one('equipment.subcontract', string="Subcontract", ondelete='cascade')
    percentage = fields.Float(string="Percentage", tracking=True, compute="_compute_percentage")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    amount = fields.Monetary(tracking=True, string="Amount", compute="_compute_percentage_amount")
    date = fields.Date(string="Date", default=fields.Date.today(), tracking=True)
    remark = fields.Char(string="Remark", tracking=True)
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    bill_id = fields.Many2one('account.move', string="Bill")
    payment_state = fields.Selection(related="bill_id.payment_state", string="Payment State", tracking=True)
    state = fields.Selection(related="purchase_order_id.state", string="State", tracking=True)
    po_bill = fields.Selection(related="contract_id.po_bill")
    qty = fields.Integer(string="Qty")
    retention_percentage = fields.Float(string="Retention(%)")
    retention_amount = fields.Monetary(string="Retention Amount", compute="compute_retention_amount")
    final_amount = fields.Monetary(string="Total Amount", compute="_compute_final_amount")

    # QC Check
    qc_user_id = fields.Many2one('res.users', string="QC Responsible", tracking=True)
    qc_status = fields.Selection(
        [('draft', 'Draft'),
         ('request', 'Department Approval'),
         ('approve', 'Approve'),
         ('reject', 'Reject')], default='draft', string="Quality Check Status", tracking=True)
    reject_reason = fields.Text(string="Reject Reason", tracking=True)

    def unlink(self):
        for rec in self:
            if rec.qc_status != 'draft':
                raise ValidationError(_("You can't delete until Quality Check status is in Draft"))
            else:
                return super(EquipContractLine, self).unlink()

    @api.constrains('qty')
    def _check_ra_bill_qty(self):
        ra_bill_ids = self.env['equip.contract.line'].search([('contract_id', '=', self.contract_id.id)])
        qty = 0
        for record in ra_bill_ids:
            if record.qc_status != 'reject':
                qty = qty + record.qty
        if qty > self.contract_id.qty:
            raise ValidationError(_("Quantity should be less than total qty."))

    @api.depends('contract_id', 'qty', 'contract_id.tax_id')
    def _compute_percentage_amount(self):
        for rec in self:
            amount = 0.0
            if rec.qty and rec.contract_id:
                amount = (rec.contract_id.cost + (rec.contract_id.tax_id.amount * rec.contract_id.cost / 100)) * rec.qty
            rec.amount = amount

    @api.depends('qty', 'retention_amount')
    def _compute_final_amount(self):
        for rec in self:
            total = 0.0
            if rec.amount:
                total = rec.amount - rec.retention_amount
            rec.final_amount = total

    @api.depends('amount', 'retention_percentage')
    def compute_retention_amount(self):
        for rec in self:
            retention_amount = 0.0
            if rec.retention_percentage:
                retention_amount = rec.amount * rec.retention_percentage / 100
            rec.retention_amount = retention_amount

    @api.depends('contract_id', 'amount')
    def _compute_percentage(self):
        for rec in self:
            percentage = 0.0
            if rec.contract_id and rec.amount > 0:
                percentage = (100 * rec.amount) / rec.contract_id.total_cost
            rec.percentage = percentage

    def action_quality_check(self):
        self.qc_status = 'request'

    def action_quality_check_approve(self):
        self.qc_status = 'approve'
        self.qc_user_id = self.env.user.id

    def action_quality_check_reject(self):
        self.qc_status = 'reject'
        self.qc_user_id = self.env.user.id

    def action_reset_to_draft(self):
        self.qc_status = 'draft'

    def action_create_ra_bill(self):
        if self.po_bill == 'bill':
            record = {
                'product_id': self.contract_id.equipment_id.id,
                'name': self.contract_id.name,
                'quantity': 1,
                'price_unit': self.final_amount,
                'tax_ids': False
            }
            invoice_lines = [(0, 0, record)]
            data = {
                'partner_id': self.contract_id.vendor_id.id,
                'invoice_date': self.date,
                'invoice_line_ids': invoice_lines,
                'move_type': 'in_invoice',
                'equipment_subcontract_id': self.contract_id.id,
                'job_order_id': self.contract_id.job_order_id.id,
                'purchase_order': 'equipment'
            }
            invoice_id = self.env['account.move'].sudo().create(data)
            self.bill_id = invoice_id.id
            remaining_amount = self.contract_id.remaining_amount
            self.contract_id.remaining_amount = remaining_amount - self.amount
            qty = self.contract_id.remain_qty
            self.contract_id.remain_qty = qty - self.qty
        elif self.po_bill == 'purchase_order':
            purchase_record = {
                'product_id': self.contract_id.equipment_id.id,
                'name': self.contract_id.name,
                'product_qty': 1,
                'price_unit': self.final_amount,
            }
            purchase_lines = [(0, 0, purchase_record)]
            purchase_data = {
                'partner_id': self.contract_id.vendor_id.id,
                'order_line': purchase_lines,
                'job_order_id': self.contract_id.job_order_id.id,
                'equipment_subcontract_id': self.contract_id.id,
                'purchase_order': 'equipment'
            }
            purchase_order_id = self.env['purchase.order'].create(purchase_data)
            self.purchase_order_id = purchase_order_id.id
            remaining_amount = self.contract_id.remaining_amount
            self.contract_id.remaining_amount = remaining_amount - self.amount
            qty = self.contract_id.remain_qty
            self.contract_id.remain_qty = qty - self.qty


class LabourSubcontract(models.Model):
    _name = 'labour.subcontract'
    _description = "Labour Sub Contract"
    _rec_name = 'seq'

    seq = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    name = fields.Char(string="Title")
    product_id = fields.Many2one('product.product', string="Product", domain="[('is_labour','=',True)]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    cost = fields.Monetary(string="Cost / Hour")
    po_bill = fields.Selection([('bill', 'Bill'), ('purchase_order', 'Purchase Order')], string="Type",
                               default='bill')
    stage = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done')],
                             default='draft')
    vendor_id = fields.Many2one('res.partner', string="Contractor")
    job_type_id = fields.Many2one('job.type', string="Work Type")
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    ra_bill_ids = fields.One2many('labour.contract.line', 'contract_id', string="Ra Bills")
    completion_date = fields.Date(string="Completion Date", compute="compute_completion_date")

    # Project Details
    job_order_id = fields.Many2one('job.order', string="Work Order")
    phase_id = fields.Many2one(related="job_order_id.job_sheet_id", string="Project Phase(WBS)", store=True)
    project_id = fields.Many2one(related='job_order_id.project_id', string="Sub Project", store=True)
    task_id = fields.Many2one(related="job_order_id.task_id", string="Task", store=True)

    # Department
    department_id = fields.Many2one(related="job_order_id.department_id", string="Department", store=True)
    manager_ids = fields.Many2many('res.users', store=True, string="Manager")
    user_id = fields.Many2one(related="job_order_id.user_id", string="Responsible")

    # Calculation
    hours = fields.Float(string="Hours")
    remain_hours = fields.Float(string="Remaining Hours")
    total_cost = fields.Monetary(string="Total Cost")
    remaining_amount = fields.Monetary(string="Remaining Amount")
    progress = fields.Float(string="Completed Billing", compute="_compute_payment_progress")
    tax_id = fields.Many2one('account.tax', string='Tax')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('seq', _('New')) == _('New'):
                vals['seq'] = self.env['ir.sequence'].next_by_code('labour.sub') or _('New')
        res = super(LabourSubcontract, self).create(vals_list)
        return res

    def action_in_progress(self):
        self.stage = 'in_progress'

    def action_state_done(self):
        self.stage = 'done'

    @api.constrains('ra_bill_ids', 'hours')
    def _check_ra_bill_hours(self):
        hours = 0
        for record in self.ra_bill_ids:
            if record.qc_status != 'reject':
                hours = hours + record.hours
        if hours > self.hours:
            raise ValidationError(_("Hours should be less than total hours"))

    @api.depends('total_cost', 'remaining_amount')
    def _compute_payment_progress(self):
        for rec in self:
            progress = 0.0
            if rec.total_cost and rec.remaining_amount:
                progress = (rec.remaining_amount * 100) / rec.total_cost
            rec.progress = 100 - progress

    @api.depends('stage', 'ra_bill_ids')
    def compute_completion_date(self):
        for rec in self:
            date = None
            if rec.stage == "done":
                dates = rec.ra_bill_ids.mapped('date')
                if dates:
                    date = dates[-1]
            rec.completion_date = date


class LabourContractLine(models.Model):
    _name = 'labour.contract.line'
    _description = "Labour Contract Line"
    _rec_name = 'remark'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    contract_id = fields.Many2one('labour.subcontract', string="Labour Subcontract", ondelete='cascade')
    percentage = fields.Float(string="Percentage", tracking=True, compute="_compute_percentage")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    amount = fields.Monetary(tracking=True, string="Amount", compute="_compute_percentage_amount")
    date = fields.Date(string="Date", default=fields.Date.today(), tracking=True)
    remark = fields.Char(string="Remark", tracking=True)
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    bill_id = fields.Many2one('account.move', string="Bill")
    payment_state = fields.Selection(related="bill_id.payment_state", string="Payment State", tracking=True)
    state = fields.Selection(related="purchase_order_id.state", string="State", tracking=True)
    po_bill = fields.Selection(related="contract_id.po_bill")
    hours = fields.Float(string="Hours")
    retention_percentage = fields.Float(string="Retention(%)")
    retention_amount = fields.Monetary(string="Retention Amount", compute="compute_retention_amount")
    final_amount = fields.Monetary(string="Total Amount", compute="_compute_final_amount")

    # QC Check
    qc_user_id = fields.Many2one('res.users', string="QC Responsible", tracking=True)
    qc_status = fields.Selection([('draft', 'Draft'),
                                  ('request', 'Department Approval'),
                                  ('approve', 'Approve'),
                                  ('reject', 'Reject')],
                                 default='draft', string="Quality Check Status", tracking=True)
    reject_reason = fields.Text(string="Reject Reason", tracking=True)

    def unlink(self):
        for rec in self:
            if rec.qc_status != 'draft':
                raise ValidationError(_("You can't delete until Quality Check status is in Draft"))
            else:
                return super(LabourContractLine, self).unlink()

    @api.constrains('hours')
    def _check_ra_bill_hours(self):
        ra_bill_ids = self.env['labour.contract.line'].search([('contract_id', '=', self.contract_id.id)])
        hours = 0
        for record in ra_bill_ids:
            if record.qc_status != 'reject':
                hours = hours + record.hours
        if hours > self.contract_id.hours:
            raise ValidationError(_("Hours should be less than total hours"))

    @api.depends('contract_id', 'hours', 'contract_id.tax_id')
    def _compute_percentage_amount(self):
        for rec in self:
            amount = 0.0
            if rec.hours and rec.contract_id:
                amount = (rec.contract_id.cost + (
                        rec.contract_id.tax_id.amount * rec.contract_id.cost / 100)) * rec.hours
            rec.amount = amount

    @api.depends('hours', 'retention_amount')
    def _compute_final_amount(self):
        for rec in self:
            total = 0.0
            if rec.amount:
                total = rec.amount - rec.retention_amount
            rec.final_amount = total

    @api.depends('amount', 'retention_percentage')
    def compute_retention_amount(self):
        for rec in self:
            retention_amount = 0.0
            retention_amount = rec.amount * rec.retention_percentage / 100
            rec.retention_amount = retention_amount

    @api.depends('contract_id', 'amount')
    def _compute_percentage(self):
        for rec in self:
            percentage = 0.0
            if rec.contract_id and rec.amount > 0:
                percentage = (100 * rec.amount) / rec.contract_id.total_cost
            rec.percentage = percentage

    def action_quality_check(self):
        self.qc_status = 'request'

    def action_quality_check_approve(self):
        self.qc_status = 'approve'
        self.qc_user_id = self.env.user.id

    def action_quality_check_reject(self):
        self.qc_status = 'reject'
        self.qc_user_id = self.env.user.id

    def action_reset_to_draft(self):
        self.qc_status = 'draft'

    def action_create_ra_bill(self):
        if self.po_bill == 'bill':
            record = {
                'product_id': self.contract_id.product_id.id,
                'name': self.contract_id.name,
                'quantity': 1,
                'price_unit': self.final_amount,
                'tax_ids': False
            }
            invoice_lines = [(0, 0, record)]
            data = {
                'partner_id': self.contract_id.vendor_id.id,
                'invoice_date': self.date,
                'invoice_line_ids': invoice_lines,
                'move_type': 'in_invoice',
                'labour_subcontract_id': self.contract_id.id,
                'job_order_id': self.contract_id.job_order_id.id,
                'purchase_order': 'equipment'
            }
            invoice_id = self.env['account.move'].sudo().create(data)
            remaining_amount = self.contract_id.remaining_amount
            self.contract_id.remaining_amount = remaining_amount - self.amount
            self.bill_id = invoice_id.id
            qty = self.contract_id.remain_hours
            self.contract_id.remain_hours = qty - self.hours
        elif self.po_bill == 'purchase_order':
            purchase_record = {
                'product_id': self.contract_id.product_id.id,
                'name': self.contract_id.name
                ,
                'product_qty': 1,
                'price_unit': self.final_amount,
            }
            purchase_lines = [(0, 0, purchase_record)]
            purchase_data = {
                'partner_id': self.contract_id.vendor_id.id,
                'order_line': purchase_lines,
                'job_order_id': self.contract_id.job_order_id.id,
                'labour_subcontract_id': self.contract_id.id,
                'purchase_order': 'equipment'
            }
            purchase_order_id = self.env['purchase.order'].create(purchase_data)
            self.purchase_order_id = purchase_order_id.id
            remaining_amount = self.contract_id.remaining_amount
            self.contract_id.remaining_amount = remaining_amount - self.amount
            qty = self.contract_id.remain_hours
            self.contract_id.remain_hours = qty - self.hours


class OverheadSubcontract(models.Model):
    _name = 'overhead.subcontract'
    _description = "Overhead Subcontract"
    _rec_name = 'seq'

    seq = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    name = fields.Char(string="Title")
    product_id = fields.Many2one('product.product', string="Product", domain="[('is_overhead','=',True)]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    uom_id = fields.Many2one(related="product_id.uom_po_id", string="Unit of Measure")
    cost = fields.Monetary(string="Cost / Unit")
    po_bill = fields.Selection([('bill', 'Bill'), ('purchase_order', 'Purchase Order')], string="Type", default='bill')
    stage = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done')], default='draft')
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    job_type_id = fields.Many2one('job.type', string="Work Type")
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    ra_bill_ids = fields.One2many('overhead.contract.line', 'contract_id', string="Ra Bills")
    completion_date = fields.Date(string="Completion Date", compute="compute_completion_date")

    # Project Details
    job_order_id = fields.Many2one('job.order', string="Work Order")
    phase_id = fields.Many2one(related="job_order_id.job_sheet_id", string="Project Phase(WBS)", store=True)
    project_id = fields.Many2one(related='job_order_id.project_id', string="Sub Project", store=True)
    task_id = fields.Many2one(related="job_order_id.task_id", string="Task", store=True)
    # Department
    department_id = fields.Many2one(related="job_order_id.department_id", string="Department", store=True)
    manager_ids = fields.Many2many('res.users', store=True, string="Manager")
    user_id = fields.Many2one(related="job_order_id.user_id", string="Responsible")

    # Calculation
    qty = fields.Integer(string="Qty.", default=1)
    remain_qty = fields.Integer(string="Remaining Qty")
    total_cost = fields.Monetary(string="Total Cost")
    remaining_amount = fields.Monetary(string="Remaining Amount")
    progress = fields.Float(string="Completed Billing", compute="_compute_payment_progress")
    tax_id = fields.Many2one('account.tax', string='Tax')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('seq', _('New')) == _('New'):
                vals['seq'] = self.env['ir.sequence'].next_by_code('overhead.sub') or _('New')
        res = super(OverheadSubcontract, self).create(vals_list)
        return res

    def action_in_progress(self):
        self.stage = 'in_progress'

    def action_state_done(self):
        self.stage = 'done'

    @api.constrains('ra_bill_ids', 'qty')
    def _check_ra_bill_qty(self):
        qty = 0
        for record in self.ra_bill_ids:
            if record.qc_status != 'reject':
                qty = qty + record.qty
        if qty > self.qty:
            raise ValidationError(_("Quantity should be less than total qty."))

    @api.depends('total_cost', 'remaining_amount')
    def _compute_payment_progress(self):
        for rec in self:
            progress = 0.0
            if rec.total_cost and rec.remaining_amount:
                progress = (rec.remaining_amount * 100) / rec.total_cost
            rec.progress = 100 - progress

    @api.depends('stage', 'ra_bill_ids')
    def compute_completion_date(self):
        for rec in self:
            date = None
            if rec.stage == "done":
                dates = rec.ra_bill_ids.mapped('date')
                if dates:
                    date = dates[-1]
            rec.completion_date = date


class OverheadContractLine(models.Model):
    _name = 'overhead.contract.line'
    _description = "Overhead Contract Line"
    _rec_name = 'remark'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    contract_id = fields.Many2one('overhead.subcontract', string="Overhead Subcontract", ondelete='cascade')
    percentage = fields.Float(string="Percentage", tracking=True, compute="_compute_percentage")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    amount = fields.Monetary(tracking=True, string="Amount", compute="_compute_percentage_amount")
    date = fields.Date(string="Date", default=fields.Date.today(), tracking=True)
    remark = fields.Char(string="Remark", tracking=True)
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    bill_id = fields.Many2one('account.move', string="Bill")
    payment_state = fields.Selection(related="bill_id.payment_state", string="Payment State", tracking=True)
    state = fields.Selection(related="purchase_order_id.state", string="State", tracking=True)
    po_bill = fields.Selection(related="contract_id.po_bill")
    qty = fields.Integer(string="Qty")
    retention_percentage = fields.Float(string="Retention(%)")
    retention_amount = fields.Monetary(string="Retention Amount", compute="compute_retention_amount")
    final_amount = fields.Monetary(string="Total Amount", compute="_compute_final_amount")

    # QC Check
    qc_user_id = fields.Many2one('res.users', string="QC Responsible", tracking=True)
    qc_status = fields.Selection([('draft', 'Draft'),
                                  ('request', 'Department Approval'),
                                  ('approve', 'Approve'),
                                  ('reject', 'Reject')], default='draft', string="Quality Check Status", tracking=True)
    reject_reason = fields.Text(string="Reject Reason", tracking=True)

    def unlink(self):
        for rec in self:
            if rec.qc_status != 'draft':
                raise ValidationError(_("You can't delete until Quality Check status is in Draft"))
            else:
                return super(OverheadContractLine, self).unlink()

    @api.constrains('qty')
    def _check_ra_bill_qty(self):
        ra_bill_ids = self.env['overhead.contract.line'].search([('contract_id', '=', self.contract_id.id)])
        qty = 0
        for record in ra_bill_ids:
            if record.qc_status != 'reject':
                qty = qty + record.qty
        if qty > self.contract_id.qty:
            raise ValidationError(_("Quantity should be less than total qty."))

    @api.depends('contract_id', 'qty', 'contract_id.tax_id')
    def _compute_percentage_amount(self):
        for rec in self:
            amount = 0.0
            if rec.qty and rec.contract_id:
                amount = (rec.contract_id.cost + (rec.contract_id.tax_id.amount * rec.contract_id.cost / 100)) * rec.qty
            rec.amount = amount

    @api.depends('qty', 'retention_amount')
    def _compute_final_amount(self):
        for rec in self:
            total = 0.0
            if rec.amount:
                total = rec.amount - rec.retention_amount
            rec.final_amount = total

    @api.depends('amount', 'retention_percentage')
    def compute_retention_amount(self):
        for rec in self:
            retention_amount = 0.0
            if rec.retention_percentage:
                retention_amount = rec.amount * rec.retention_percentage / 100
            rec.retention_amount = retention_amount

    @api.depends('contract_id', 'amount')
    def _compute_percentage(self):
        for rec in self:
            percentage = 0.0
            if rec.contract_id and rec.amount > 0:
                percentage = (100 * rec.amount) / rec.contract_id.total_cost
            rec.percentage = percentage

    def action_quality_check(self):
        self.qc_status = 'request'

    def action_quality_check_approve(self):
        self.qc_status = 'approve'
        self.qc_user_id = self.env.user.id

    def action_quality_check_reject(self):
        self.qc_status = 'reject'
        self.qc_user_id = self.env.user.id

    def action_reset_to_draft(self):
        self.qc_status = 'draft'

    def action_create_ra_bill(self):
        if self.po_bill == 'bill':
            record = {
                'product_id': self.contract_id.product_id.id,
                'name': self.contract_id.name,
                'quantity': 1,
                'price_unit': self.final_amount,
                'tax_ids': False
            }
            invoice_lines = [(0, 0, record)]
            data = {
                'partner_id': self.contract_id.vendor_id.id,
                'invoice_date': self.date,
                'invoice_line_ids': invoice_lines,
                'move_type': 'in_invoice',
                'overhead_subcontract_id': self.contract_id.id,
                'job_order_id': self.contract_id.job_order_id.id,
                'purchase_order': 'overhead'
            }
            invoice_id = self.env['account.move'].sudo().create(data)
            remaining_amount = self.contract_id.remaining_amount
            self.contract_id.remaining_amount = remaining_amount - self.amount
            self.bill_id = invoice_id.id
            qty = self.contract_id.remain_qty
            self.contract_id.remain_qty = qty - self.qty
        elif self.po_bill == 'purchase_order':
            purchase_record = {
                'product_id': self.contract_id.product_id.id,
                'name': self.contract_id.name
                ,
                'product_qty': 1,
                'price_unit': self.final_amount,
            }
            purchase_lines = [(0, 0, purchase_record)]
            purchase_data = {
                'partner_id': self.contract_id.vendor_id.id,
                'order_line': purchase_lines,
                'job_order_id': self.contract_id.job_order_id.id,
                'overhead_subcontract_id': self.contract_id.id,
                'purchase_order': 'overhead'
            }
            purchase_order_id = self.env['purchase.order'].create(
                purchase_data)
            self.purchase_order_id = purchase_order_id.id
            remaining_amount = self.contract_id.remaining_amount
            self.contract_id.remaining_amount = remaining_amount - self.amount
            qty = self.contract_id.remain_qty
            self.contract_id.remain_qty = qty - self.qty


class MaterialConsume(models.Model):
    _name = 'material.consume'
    _description = "Material Consume Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'seq'

    seq = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    date = fields.Date(string="Date", default=fields.Date.today())
    remark = fields.Char(string="Remark")

    warehouse_id = fields.Many2one('stock.warehouse')
    consume_order_id = fields.Many2one('stock.picking', string="Consume Order")
    state = fields.Selection(related="consume_order_id.state", string="Status")
    consume_order_ids = fields.One2many('material.consume.line', 'material_consume_id', string="Material Consume")

    # Project Details
    job_order_id = fields.Many2one('job.order', string="Work Order")
    phase_id = fields.Many2one(related="job_order_id.job_sheet_id", string="Project Phase(WBS)", store=True)
    project_id = fields.Many2one(related='job_order_id.project_id', string="Sub Project", store=True)
    task_id = fields.Many2one(related="job_order_id.task_id", string="Task", store=True)
    # Department
    department_id = fields.Many2one(related="job_order_id.department_id", string="Department", store=True)
    manager_ids = fields.Many2many('res.users', store=True, string="Manager")
    user_id = fields.Many2one(related="job_order_id.user_id", string="Responsible", store=True)

    # Quality Check
    qc_user_id = fields.Many2one('res.users', string="QC Responsible", tracking=True)
    qc_status = fields.Selection([('draft', 'Draft'), ('request', 'Department Approval'), ('approve', 'Approve'),
                                  ('reject', 'Reject'), ('cancel', 'Cancel')], default='draft',
                                 string="Quality Check Status", tracking=True)
    reject_reason = fields.Text(string="Reject Reason", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('seq', _('New')) == _('New'):
                vals['seq'] = self.env['ir.sequence'].next_by_code('material.consume') or _('New')
        res = super(MaterialConsume, self).create(vals_list)
        return res

    def unlink(self):
        if self.qc_status != 'draft':
            raise ValidationError(_("You can't delete until Quality Check status is in Draft"))
        else:
            return super(MaterialConsume, self).unlink()

    @api.constrains('consume_order_ids')
    def _check_material_line_qty(self):
        for rec in self.consume_order_ids:
            if rec.qty > rec.material_line_id.remain_qty:
                raise ValidationError(_("Qty should be less than remain Qty."))

    def action_quality_check(self):
        self.qc_status = 'request'

    def action_quality_check_approve(self):
        self.qc_status = 'approve'
        self.qc_user_id = self.env.user.id

    def action_quality_check_reject(self):
        self.qc_status = 'reject'
        self.qc_user_id = self.env.user.id

    def action_reset_to_draft(self):
        self.qc_status = 'draft'

    def action_cancel_consume_order(self):
        self.qc_status = 'cancel'

    def action_create_consume_order(self):
        dest_location_id = False
        if self.warehouse_id.consume_stock_location_id:
            dest_location_id = self.warehouse_id.consume_stock_location_id
        else:
            dest_location_id = self.env['stock.location'].create(
                {'name': "Consume Location/" + str(self.warehouse_id.name), 'usage': 'production'})
            self.warehouse_id.consume_stock_location_id = dest_location_id.id
        lines = []
        for rec in self.consume_order_ids:
            lines.append((0, 0, {
                'product_id': rec.material_id.id,
                'product_uom_qty': rec.qty,
                'product_uom': rec.uom_id.id,
                'location_id': self.warehouse_id.lot_stock_id.id,
                'location_dest_id': dest_location_id.id,
                'name': rec.name
            }))
        source_id = self.warehouse_id.lot_stock_id
        stock_picking_type_id = self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing'), ('warehouse_id', '=', self.warehouse_id.id)], limit=1)
        delivery_record = {
            'picking_type_id': stock_picking_type_id.id,
            'location_id': source_id.id,
            'location_dest_id': dest_location_id.id,
            'move_ids_without_package': lines,
            'consume_order_id': self.job_order_id.id,
            'material_consume_id': self.id,
            'move_type': 'one'
        }
        delivery_id = self.env['stock.picking'].create(delivery_record)
        self.consume_order_id = delivery_id.id
        for rec in self.consume_order_ids:
            remain_qty = rec.material_line_id.remain_qty
            usage_qty = rec.material_line_id.usage_qty
            rec.material_line_id.remain_qty = remain_qty - rec.qty
            rec.material_line_id.usage_qty = usage_qty + rec.qty
        return {
            'type': 'ir.actions.act_window',
            'name': _('Consume Order'),
            'res_model': 'stock.picking',
            'res_id': delivery_id.id,
            'view_mode': 'form',
            'target': 'current'
        }


class MaterialConsumeLine(models.Model):
    _name = 'material.consume.line'
    _description = "Material Consume Line"

    material_id = fields.Many2one('product.product', string="Material", domain="[('is_material','=',True)]")
    uom_id = fields.Many2one(related="material_id.uom_id", string="UOM")
    name = fields.Char(string="Description")
    qty = fields.Integer(string="Qty")
    material_consume_id = fields.Many2one('material.consume', string="Material Consume")
    qc_status = fields.Selection(related="material_consume_id.qc_status")
    material_line_id = fields.Many2one('order.material.line')
