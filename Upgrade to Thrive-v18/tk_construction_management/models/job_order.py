# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, api, models, _


class JobOrder(models.Model):
    _name = 'job.order'
    _description = "Work Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sequence', required=True,
                       readonly=True, default=lambda self: _('New'))
    title = fields.Char(string="Title")
    stage = fields.Selection([('draft', 'Draft'),
                              ('waiting_approval', 'Waiting for approval'),
                              ('approved', 'Approved'),
                              ('complete', 'Complete'),
                              ('cancel', 'Cancel')], default='draft', tracking=True)
    is_user = fields.Boolean(compute="_compute_user_role")
    is_material_requisition = fields.Boolean(compute="compute_material_req")

    # Project Details
    site_id = fields.Many2one('tk.construction.site', string="Project")
    project_id = fields.Many2one(
        'tk.construction.project', string="Sub Project")
    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    warehouse_id = fields.Many2one(
        related="project_id.warehouse_id", string="Warehouse")

    # Other Details
    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user and self.env.user.id or False,
                                     string="Created By")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    # Work Type
    work_type_id = fields.Many2one('job.type', string="Work Type")
    job_sheet_id = fields.Many2one(
        'job.costing', string="Project Phase(WBS)", domain="[('project_id','=',project_id)]")

    # Department
    department_id = fields.Many2one(
        'construction.department', string="Department")
    manager_ids = fields.Many2many('res.users', string="Manager")
    user_id = fields.Many2one('res.users', string="Responsible")

    # Material
    material_req_id = fields.Many2one(
        'material.requisition', string="Material Request")
    state = fields.Selection([('draft', 'Draft'),
                              ('material_request', 'Material Request'),
                              ('material_arrive', 'Material Arrived'),
                              ('in_progress', 'In Progress'),
                              ('complete', 'Complete'),
                              ('cancel', 'Cancel')], default='draft')

    # Task Details
    project_project_id = fields.Many2one(
        related="project_id.project_id", string="Project ")
    task_name = fields.Char(string="Task Title")
    task_desc = fields.Text(string="Description")
    assignees_ids = fields.Many2many('res.users', 'construction_assign_dep_rel', 'assign_id', 'dep_id',
                                     string="Assignees")
    task_id = fields.Many2one('project.task', string="Task")

    # One2 many
    material_order_ids = fields.One2many('order.material.line', 'job_order_id')
    equipment_order_ids = fields.One2many(
        'order.equipment.line', 'job_order_id')
    labour_order_ids = fields.One2many('order.labour.line', 'job_order_id')
    overhead_order_ids = fields.One2many('order.overhead.line', 'job_order_id')

    # Total
    equipment_total_cost = fields.Monetary(
        string="Equipment Cost", compute="_compute_total")
    labour_total_cost = fields.Monetary(
        string="Labour Cost", compute="_compute_total")
    overhead_total_cost = fields.Monetary(
        string="Overhead Cost", compute="_compute_total")

    # Consume Order and Subcontract
    consume_order_ids = fields.One2many('material.consume', 'job_order_id')
    equipment_contract_ids = fields.One2many(
        'equipment.subcontract', 'job_order_id')
    labour_contract_ids = fields.One2many('labour.subcontract', 'job_order_id')
    overhead_contract_ids = fields.One2many(
        'overhead.subcontract', 'job_order_id')

    # Count
    po_count = fields.Integer(string="Purchase Count",
                              compute="_compute_count")
    equip_po_count = fields.Integer(
        string="Purchase Equip Count", compute="_compute_count")
    labour_po_count = fields.Integer(
        string="Purchase Labour Count", compute="_compute_count")
    overhead_po_count = fields.Integer(
        string="Purchase Overhead Count", compute="_compute_count")
    bill_count = fields.Integer(string="Bill Count", compute="_compute_count")
    delivery_count = fields.Integer(
        string="Delivery Count", compute="_compute_count")
    equip_contract_count = fields.Integer(
        string="Equipment Contract Count", compute="_compute_count")
    labour_contract_count = fields.Integer(
        string="Labour Contract Count", compute="_compute_count")
    overhead_contract_count = fields.Integer(
        string="Overhead Contract Count", compute="_compute_count")
    material_consume_count = fields.Integer(
        string="Material Consume Count", compute="_compute_count")

    # Create, Write, Unlink, Constrain
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New') and vals.get('project_id'):
                project_id = self.env['tk.construction.project'].browse(
                    vals.get('project_id'))
                vals['name'] = str(project_id.code) + "/" + (
                    self.env['ir.sequence'].next_by_code('job.order') or _('New'))
        res = super(JobOrder, self).create(vals_list)
        for rec in res:
            data = {
                'name': rec.task_name,
                'description': rec.task_desc,
                'user_ids': [(6, 0, rec.assignees_ids.ids)],
                'job_order_id': rec.id,
                'con_project_id': rec.project_id.id,
                'date_deadline': rec.end_date
            }
            task_id = self.env['project.task'].sudo().create(data)
            task_id.project_id = rec.project_id.project_id.id
            rec.task_id = task_id.id
        return res

    def name_get(self):
        data = []
        for rec in self:
            data.append((rec.id, '%s - %s' % (rec.name, rec.title)))
        return data

    # Compute
    def _compute_count(self):
        for rec in self:
            rec.po_count = self.env['purchase.order'].search_count(
                [('job_order_id', '=', rec.id)])
            rec.equip_po_count = self.env['purchase.order'].search_count(
                [('job_order_id', '=', rec.id), ('purchase_order', '=', 'equipment')])
            rec.labour_po_count = self.env['purchase.order'].search_count(
                [('job_order_id', '=', rec.id), ('purchase_order', '=', 'labour')])
            rec.overhead_po_count = self.env['purchase.order'].search_count(
                [('job_order_id', '=', rec.id), ('purchase_order', '=', 'overhead')])
            rec.bill_count = self.env['account.move'].search_count(
                [('job_order_id', '=', rec.id)])
            rec.delivery_count = self.env['stock.picking'].search_count(
                [('consume_order_id', '=', rec.id)])
            rec.equip_contract_count = self.env['equipment.subcontract'].search_count(
                [('job_order_id', '=', rec.id)])
            rec.labour_contract_count = self.env['labour.subcontract'].search_count(
                [('job_order_id', '=', rec.id)])
            rec.overhead_contract_count = self.env['overhead.subcontract'].search_count(
                [('job_order_id', '=', rec.id)])
            rec.material_consume_count = self.env['material.consume'].search_count(
                [('job_order_id', '=', rec.id)])

    def _compute_user_role(self):
        if self.env.user.has_group('tk_construction_management.advance_construction_user'):
            self.is_user = True
        else:
            self.is_user = False

    @api.depends('material_order_ids')
    def compute_material_req(self):
        for rec in self:
            material_req = False
            for data in rec.material_order_ids:
                if data.qty != 0:
                    material_req = True
                    break
            rec.is_material_requisition = material_req

    @api.depends('material_order_ids', 'equipment_order_ids', 'labour_order_ids', 'overhead_order_ids')
    def _compute_total(self):
        equipment, labour, overhead = 0, 0, 0
        for rec in self:
            for data in rec.equipment_order_ids:
                equipment = equipment + data.total_cost
            for data in rec.labour_order_ids:
                labour = labour + data.sub_total
            for data in rec.overhead_order_ids:
                overhead = overhead + data.sub_total
            rec.equipment_total_cost = equipment
            rec.labour_total_cost = labour
            rec.overhead_total_cost = overhead

    # Smart Button
    def action_view_purchase_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_model': 'purchase.order',
            'domain': [('job_order_id', '=', self.id)],
            'context': {
                'default_job_order_id': self.id,
                'group_by': 'purchase_order'
            },
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_bills(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bills'),
            'res_model': 'account.move',
            'domain': [('job_order_id', '=', self.id)],
            'context': {
                'default_job_order_id': self.id
            },
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_delivery_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery Order'),
            'res_model': 'stock.picking',
            'domain': [('consume_order_id', '=', self.id)],
            'context': {
                'default_': self.id
            },
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_purchase_order_equipment(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Equipment PO'),
            'res_model': 'purchase.order',
            'domain': [('job_order_id', '=', self.id), ('purchase_order', '=', 'equipment')],
            'context': {
                'default_job_order_id': self.id,
                'purchase_order': 'equipment'
            },
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_contract_equipment(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Equipment Contract'),
            'res_model': 'equipment.subcontract',
            'domain': [('job_order_id', '=', self.id)],
            'context': {
                'create': False,
            },
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_contract_labour(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Labour Contract'),
            'res_model': 'labour.subcontract',
            'domain': [('job_order_id', '=', self.id)],
            'context': {
                'create': False,
            },
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_contract_overhead(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Overhead Contract'),
            'res_model': 'overhead.subcontract',
            'domain': [('job_order_id', '=', self.id)],
            'context': {
                'create': False,
            },
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_material_consume_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Consume Orders'),
            'res_model': 'material.consume',
            'domain': [('job_order_id', '=', self.id)],
            'context': {
                'create': False,
            },
            'view_mode': 'tree,form',
            'target': 'current'
        }

    # Button
    def action_request_material(self):
        if not self.material_order_ids:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('Add Material'),
                    'message': "Add Material to Create Material Request",
                    'sticky': False,
                }
            }
            return message
        material_request_id = self.env['material.requisition'].create({
            'title': self.title,
            'company_id': self.company_id.id,
            'desc': self.task_desc,
            'project_id': self.project_id.id,
            'department_id': self.department_id.id,
            'manager_ids': self.manager_ids.ids,
            'user_id': self.user_id.id,
            'work_order_id': self.id,
            'work_type_id': self.work_type_id.id,
            'site_id': self.site_id.id
        })
        for data in self.material_order_ids:
            record = {
                'material_id': data.material_id.id,
                'name': data.name,
                'qty': data.qty,
                'warehouse_id': self.warehouse_id.id,
                'material_req_id': material_request_id.id,
                'sub_category_id': data.sub_category_id.id,
                'job_sheet_id': self.job_sheet_id.id,
            }
            req_line_id = self.env['material.requisition.line'].create(record)
            data.material_req_line_id = req_line_id.id
        self.material_req_id = material_request_id.id
        self.state = 'material_request'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Material Request'),
            'res_model': 'material.requisition',
            'res_id': material_request_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def action_create_equipment_subcontract(self):
        for rec in self.equipment_order_ids:
            if not rec.equip_sub_contract_id:
                data = {
                    'name': rec.desc,
                    'equipment_id': rec.equipment_id.id,
                    'cost_type': rec.cost_type,
                    'qty': rec.qty,
                    'remain_qty': rec.qty,
                    'cost': rec.cost,
                    'total_cost': rec.total_cost,
                    'vendor_id': rec.vendor_id.id,
                    'job_type_id': self.work_type_id.id,
                    'sub_category_id': rec.sub_category_id.id,
                    'job_order_id': self.id,
                    'remaining_amount': rec.total_cost,
                    'manager_ids': self.manager_ids.ids,
                    'tax_id': rec.tax_id.id
                }
                equip_line_id = self.env['equipment.subcontract'].create(data)
                rec.equip_sub_contract_id = equip_line_id.id

    def action_create_labour_subcontract(self):
        for rec in self.labour_order_ids:
            if not rec.labour_sub_contract_id:
                data = {
                    'name': rec.name,
                    'product_id': rec.product_id.id,
                    'hours': rec.hours,
                    'remain_hours': rec.hours,
                    'cost': rec.cost,
                    'total_cost': rec.sub_total,
                    'vendor_id': rec.vendor_id.id,
                    'job_type_id': self.work_type_id.id,
                    'sub_category_id': rec.sub_category_id.id,
                    'job_order_id': self.id,
                    'remaining_amount': rec.sub_total,
                    'manager_ids': self.manager_ids.ids,
                    'tax_id': rec.tax_id.id
                }
                labour_line_id = self.env['labour.subcontract'].create(data)
                rec.labour_sub_contract_id = labour_line_id.id

    def action_create_overhead_subcontract(self):
        for rec in self.overhead_order_ids:
            if not rec.overhead_sub_contract_id:
                data = {
                    'name': rec.name,
                    'product_id': rec.product_id.id,
                    'qty': rec.qty,
                    'remain_qty': rec.qty,
                    'cost': rec.cost,
                    'total_cost': rec.sub_total,
                    'vendor_id': rec.vendor_id.id,
                    'job_type_id': self.work_type_id.id,
                    'sub_category_id': rec.sub_category_id.id,
                    'job_order_id': self.id,
                    'remaining_amount': rec.sub_total,
                    'manager_ids': self.manager_ids.ids,
                    'tax_id': rec.tax_id.id
                }
                overhead_line_id = self.env['overhead.subcontract'].create(
                    data)
                rec.overhead_sub_contract_id = overhead_line_id.id

    def action_create_material_consume_order(self):
        remain_qty = False
        for rec in self.material_order_ids:
            if not rec.remain_qty == 0:
                remain_qty = True
                break
        if remain_qty:
            consume_order_id = self.env['material.consume'].create({
                'job_order_id': self.id,
                'manager_ids': self.manager_ids.ids,
                'warehouse_id': self.warehouse_id.id
            })
            for rec in self.material_order_ids:
                if rec.remain_qty > 0:
                    self.env['material.consume.line'].create({
                        'material_id': rec.material_id.id,
                        'name': rec.name,
                        'qty': rec.remain_qty,
                        'material_consume_id': consume_order_id.id,
                        'material_line_id': rec.id
                    })
            return {
                'type': 'ir.actions.act_window',
                'name': _('Material Consume Order'),
                'res_model': 'material.consume',
                'res_id': consume_order_id.id,
                'view_mode': 'form',
                'target': 'new'
            }
        if not remain_qty:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': "No Material consumption orders found !",
                    'sticky': False,
                }
            }
            return message

    def action_department_approval(self):
        self.stage = 'waiting_approval'

    def action_department_approval_approved(self):
        self.stage = 'approved'

    def action_department_approval_reject(self):
        self.stage = 'cancel'

    def action_draft_order(self):
        self.stage = 'draft'

    def action_cancel_order(self):
        self.stage = 'cancel'

    def action_in_progress(self):
        self.state = 'in_progress'

    def action_reset_draft(self):
        self.state = 'draft'

    def action_complete_work_order(self):
        material = True
        equipment = True
        labour = True
        overhead = True
        for data in self.equipment_contract_ids:
            if data.stage != 'done':
                equipment = False
                break
        for data in self.labour_contract_ids:
            if data.stage != 'done':
                labour = False
                break
        for data in self.overhead_contract_ids:
            if data.stage != 'done':
                overhead = False
                break
        for data in self.consume_order_ids:
            if data.qc_status != 'approve':
                material = False
                break
        if not material or not equipment or not labour or not overhead:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': _(
                        "Please Complete Consume Order / Equipment Subcontract / Labour Subcontract / Overhead Subcontract to complete work order"),
                    'sticky': False,
                }
            }
            return message
        self.state = 'complete'


class OrderMaterialLine(models.Model):
    _name = 'order.material.line'
    _description = "Job order material line"

    material_id = fields.Many2one(
        'product.product', string="Material", domain="[('is_material','=',True)]")
    name = fields.Char(string="Description")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    qty = fields.Integer(string="Qty.", default=1)
    remain_qty = fields.Integer(string="Remain Qty.", default=1)
    usage_qty = fields.Integer(string="Used Qty.")
    uom_id = fields.Many2one(related="material_id.uom_po_id", string="UOM")
    job_order_id = fields.Many2one('job.order', string="Work Order")
    sub_category_id = fields.Many2one(
        'job.sub.category', string="Work Sub Type")
    price = fields.Monetary(string="Price")
    total_price = fields.Monetary(
        string="Total Price", compute="_compute_total_price")
    material_req_line_id = fields.Many2one('material.requisition.line')
    phase_forcast_qty = fields.Float()
    tax_id = fields.Many2one('account.tax', string="Taxes")

    # Budget Field
    job_sheet_id = fields.Many2one(
        related="job_order_id.job_sheet_id", store=True)
    project_id = fields.Many2one(related="job_order_id.project_id", store=True)
    work_type_id = fields.Many2one(
        related="job_order_id.work_type_id", store=True)
    state = fields.Selection(related="job_order_id.state", store=True)

    @api.onchange('material_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.material_id.name
            rec.price = rec.material_id.standard_price

    @api.depends('qty', 'price', 'tax_id')
    def _compute_total_price(self):
        for rec in self:
            total = 0.0
            if rec.qty and rec.price:
                total = rec.qty * rec.price
            if rec.tax_id:
                tax_amount = rec.tax_id.amount * total / 100
                total = tax_amount + total
            rec.total_price = total

    @api.onchange('qty')
    def _onchange_remain_qty(self):
        for rec in self:
            rec.remain_qty = rec.qty

    @api.depends('warehouse_id', 'material_id')
    def _compute_forcast_qty(self):
        for rec in self:
            qty = 0.0
            if rec.material_id:
                qty = rec.material_id.with_context(
                    warehouse=rec.warehouse_id.id).virtual_available
            rec.forcast_qty = qty


class OrderEquipmentLine(models.Model):
    _name = 'order.equipment.line'
    _description = 'Construction Work Order Equipment Line'

    equipment_id = fields.Many2one(
        'product.product', string="Equipment", domain="[('is_equipment','=',True)]")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    cost_type = fields.Selection(
        [('depreciation_cost', 'Depreciation Cost'), ('investment_cost', 'Investment/Interest Cost'),
         ('tax', 'Tax'), ('rent', 'Rent'), ('other', 'Other')], string="Type", default='rent')
    desc = fields.Text(string='Description')
    qty = fields.Integer(string="Qty.", default=1)
    cost = fields.Monetary(string="Estimation Cost")
    total_cost = fields.Monetary(
        string="Total Cost", compute="_compute_total_cost", store=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    job_order_id = fields.Many2one('job.order', string="Work Order")
    purchase_order_id = fields.Many2one(
        'purchase.order', string="Purchase Order")
    is_po_create = fields.Boolean()
    sub_category_id = fields.Many2one(
        'job.sub.category', string="Work Sub Type")

    equip_sub_contract_id = fields.Many2one(
        'equipment.subcontract', string="Equip Subcontract")
    phase_forcast_qty = fields.Float()
    tax_id = fields.Many2one('account.tax', string="Taxes")

    # Budget Field
    job_sheet_id = fields.Many2one(
        related="job_order_id.job_sheet_id", store=True)
    project_id = fields.Many2one(related="job_order_id.project_id", store=True)
    work_type_id = fields.Many2one(
        related="job_order_id.work_type_id", store=True)
    state = fields.Selection(related="job_order_id.state", store=True)

    @api.depends('qty', 'cost', 'tax_id')
    def _compute_total_cost(self):
        for rec in self:
            total = 0.0
            if rec.cost and rec.qty:
                total = rec.cost * rec.qty
            if rec.tax_id:
                tax_amount = rec.tax_id.amount * total / 100
                total = tax_amount + total
            rec.total_cost = total

    @api.onchange('equipment_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.desc = rec.equipment_id.name
            rec.cost = rec.equipment_id.standard_price


class OrderLabourLine(models.Model):
    _name = 'order.labour.line'
    _description = "Work Order Labour Line"

    job_order_id = fields.Many2one('job.order', string="Work Order")
    product_id = fields.Many2one(
        'product.product', string="Product", domain="[('is_labour','=',True)]")
    name = fields.Char(string="Description")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    hours = fields.Float(string="Hours")
    remain_hours = fields.Float(
        related='labour_sub_contract_id.remain_hours', string="Remain Hours")
    cost = fields.Monetary(string="Cost / Hour")
    sub_total = fields.Monetary(
        string="Sub Total", compute="_compute_sub_total", store=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    is_bill_created = fields.Boolean()
    purchase_order_id = fields.Many2one(
        'purchase.order', string="Purchase Order")
    sub_category_id = fields.Many2one(
        'job.sub.category', string="Work Sub Type")
    labour_sub_contract_id = fields.Many2one(
        'labour.subcontract', string="Subcontract")
    phase_forcast_qty = fields.Float()
    tax_id = fields.Many2one('account.tax', string="Taxes")

    # Budget Field
    job_sheet_id = fields.Many2one(
        related="job_order_id.job_sheet_id", store=True)
    project_id = fields.Many2one(related="job_order_id.project_id", store=True)
    work_type_id = fields.Many2one(
        related="job_order_id.work_type_id", store=True)
    state = fields.Selection(related="job_order_id.state", store=True)

    @api.onchange('product_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.product_id.name
            rec.cost = rec.product_id.standard_price

    @api.depends('cost', 'hours', 'tax_id')
    def _compute_sub_total(self):
        for rec in self:
            total = 0.0
            if rec.cost and rec.hours:
                total = rec.cost * rec.hours
            if rec.tax_id:
                tax_amount = rec.tax_id.amount * total / 100
                total = tax_amount + total
            rec.sub_total = total


class OrderOverheadLine(models.Model):
    _name = 'order.overhead.line'
    _description = "Work Order Overhead Line"

    job_order_id = fields.Many2one('job.order', string="Work Order")
    product_id = fields.Many2one(
        'product.product', string="Product", domain="[('is_overhead','=',True)]")
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    name = fields.Char(string="Description")
    qty = fields.Integer(string="Qty.", default=1)
    uom_id = fields.Many2one(
        related="product_id.uom_po_id", string="Unit of Measure")
    cost = fields.Monetary(string="Cost / Unit")
    sub_total = fields.Monetary(
        string="Sub Total", compute="_compute_sub_total", store=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    is_bill_created = fields.Boolean()
    purchase_order_id = fields.Many2one(
        'purchase.order', string="Purchase Order")
    sub_category_id = fields.Many2one(
        'job.sub.category', string="Work Sub Type")
    overhead_sub_contract_id = fields.Many2one(
        'overhead.subcontract', string="Subcontract")
    phase_forcast_qty = fields.Float()
    tax_id = fields.Many2one('account.tax', string="Taxes")

    # Budget Field
    job_sheet_id = fields.Many2one(
        related="job_order_id.job_sheet_id", store=True)
    project_id = fields.Many2one(related="job_order_id.project_id", store=True)
    work_type_id = fields.Many2one(
        related="job_order_id.work_type_id", store=True)
    state = fields.Selection(related="job_order_id.state", store=True)

    @api.depends('cost', 'qty', 'tax_id')
    def _compute_sub_total(self):
        for rec in self:
            total = 0.0
            if rec.cost and rec.qty:
                total = rec.cost * rec.qty
            if rec.tax_id:
                tax_amount = rec.tax_id.amount * total / 100
                total = tax_amount + total
            rec.sub_total = total

    @api.onchange('product_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.product_id.name
            rec.cost = rec.product_id.standard_price
