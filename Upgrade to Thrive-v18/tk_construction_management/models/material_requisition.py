# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, api, models, _
from thrive.exceptions import ValidationError


class MaterialRequisition(models.Model):
    _name = 'material.requisition'
    _description = "Material Requisition"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string="Title", tracking=True)

    reject_reason = fields.Text(string="Reject Reason")
    allow_resubmit = fields.Boolean(string="Allow Resubmit", tracking=True)
    po_created = fields.Boolean()
    delivery_ready = fields.Boolean(compute="_compute_delivery_ready")
    line_added = fields.Boolean()
    stage = fields.Selection(
        [('draft', 'Draft'),
         ('department_approval', 'Waiting Department Approval'),
         ('approve', 'In Progress'),
         ('ready_delivery', 'Ready for Delivery'),
         ('reject', 'Reject'),
         ('internal_transfer', 'Internal Transfer'),
         ('material_arrived', 'Material Arrived'),
         ('cancel', 'Cancel')], default='draft', tracking=True)
    desc = fields.Text(string="Description")

    # Project Details
    site_id = fields.Many2one('tk.construction.site', string="Project")
    project_id = fields.Many2one('tk.construction.project', string="Sub Project", tracking=True)
    warehouse_id = fields.Many2one(related="project_id.warehouse_id", string="Warehouse")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)

    # Other Details
    date = fields.Datetime(string="Date", default=fields.Datetime.now())
    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user and self.env.user.id or False,
                                     string="Created By")

    # Department Details
    department_id = fields.Many2one('construction.department', string="Department", tracking=True)
    manager_ids = fields.Many2many('res.users', string="Manager")
    user_id = fields.Many2one('res.users', string="Responsible User ")

    # Work Type & Job Sheet and Phase
    work_type_id = fields.Many2one('job.type', string="Work Type")
    work_order_id = fields.Many2one('job.order', string="Work Order")
    job_sheet_id = fields.Many2one(related="work_order_id.job_sheet_id", store=True)

    internal_transfer_id = fields.Many2one('internal.transfer', string="Transfer Ref.")

    # Back Order
    is_back_order = fields.Boolean(tracking=True)
    is_any_back_order = fields.Boolean(compute="_compute_any_back_order")
    back_order_id = fields.Many2one('material.requisition', string="Back Order", tracking=True)
    material_req_ref = fields.Char(string="Material Requisition Ref.", tracking=True)

    # One 2 Many
    material_line_ids = fields.One2many('material.requisition.line', 'material_req_id')
    material_purchase_ids = fields.One2many('material.purchase.line', 'material_req_id')
    material_transfer_ids = fields.One2many('material.transfer.line', 'material_req_id')

    # compute
    po_count = fields.Integer(string="Purchase Order Count", compute="_compute_count")
    bill_count = fields.Integer(string="Bill Count", compute="_compute_count")
    delivery_count = fields.Integer(string="Delivery Count", compute="_compute_count")

    # Create, Write, Unlink, Constrain
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('material.req') or _('New')
        res = super(MaterialRequisition, self).create(vals_list)
        return res

    def name_get(self):
        data = []
        for rec in self:
            data.append((rec.id, '%s - %s' % (rec.name, rec.title)))
        return data

    # Compute
    def _compute_count(self):
        for rec in self:
            rec.po_count = self.env['purchase.order'].search_count([('material_req_id', '=', rec.id)])
            rec.bill_count = self.env['account.move'].search_count([('material_req_id', '=', rec.id)])
            po = self.material_purchase_ids.mapped('purchase_order_id').mapped('name')
            ids = self.env['stock.picking'].search([('origin', 'in', po), ('code', '=', 'incoming')]).mapped('id')
            rec.delivery_count = self.env['stock.picking'].search_count([('id', 'in', ids)])

    def _compute_delivery_ready(self):
        if self.material_purchase_ids:
            incomplete = False
            for rec in self.material_purchase_ids:
                if not rec.status == 'complete':
                    incomplete = True
                    break
            if not incomplete:
                self.delivery_ready = True
            else:
                self.delivery_ready = False
        else:
            self.delivery_ready = True

    @api.depends('material_line_ids')
    def _compute_any_back_order(self):
        back_order = False
        for rec in self.material_line_ids:
            if rec.operation_type == 'back_order':
                back_order = True
                break
        if back_order:
            self.is_any_back_order = True
        else:
            self.is_any_back_order = False

    # Onchange
    @api.onchange('department_id', 'manager_ids')
    def _onchange_department_manager(self):
        ids = []
        for rec in self:
            if rec.department_id:
                ids = rec.department_id.manager_ids.ids
        return {'domain': {'manager_ids': [('id', 'in', ids)]}}

    @api.onchange('department_id', 'manager_ids', 'user_id')
    def _onchange_department_responsible(self):
        ids = []
        for rec in self:
            if rec.department_id:
                ids = rec.department_id.user_ids.ids
        return {'domain': {'user_id': [('id', 'in', ids)]}}

    # Smart Button
    def action_view_purchase_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_model': 'purchase.order',
            'domain': [('material_req_id', '=', self.id)],
            'context': {
                'default_material_req_id': self.id
            },
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_bills(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bills'),
            'res_model': 'account.move',
            'domain': [('material_req_id', '=', self.id)],
            'context': {
                'default_material_req_id': self.id
            },
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_delivery_order(self):
        po = self.material_purchase_ids.mapped('purchase_order_id').mapped('name')
        ids = self.env['stock.picking'].search([('origin', 'in', po)]).mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery Orders'),
            'res_model': 'stock.picking',
            'domain': [('id', 'in', ids), ('code', '=', 'incoming')],
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    # Button
    def action_department_approval(self):
        user_id = self.env.user.id
        msg = "<ul><li>Request for Department Approval of <strong>" + str(
            self.name) + "</strong>" + " On <strong>" + str(
            fields.Datetime.now()) + "</strong></li></ul>"
        self.message_post(body=msg, partner_ids=[user_id])
        self.stage = 'department_approval'

    def action_approve_requisition(self):
        material_arrives = True
        for rec in self.material_line_ids:
            if not (rec.forcast_qty >= rec.qty):
                material_arrives = False
        if material_arrives:
            self.stage = 'material_arrived'
            self.work_order_id.state = 'material_arrive'
        else:
            for rec in self.material_line_ids:
                if rec.forcast_qty >= rec.qty:
                    rec.is_created = True
            ready = True
            for rec in self.material_line_ids:
                if not rec.is_created:
                    ready = False
            if not ready:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'info',
                        'message': "Please Validate Lines to Approve Order",
                        'sticky': False,
                    }
                }
                return message
            self.stage = 'approve'
        user_id = self.env.user.id
        msg = "<ul><li>Approval request of <strong>" + str(self.name) + "</strong> has been approved On <strong>" + str(
            fields.Datetime.now()) + "</strong></li></ul>"
        self.message_post(body=msg, partner_ids=[user_id])

    def action_draft_requisition(self):
        self.stage = 'draft'
        self.allow_resubmit = False

    def action_ready_delivery(self):
        delivery_warehouse = False
        for rec in self.material_transfer_ids:
            if not rec.delivery_warehouse_id:
                delivery_warehouse = True
                break
        if delivery_warehouse:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('Warehouse Missing'),
                    'message': "Please Select Warehouse in Internal Transfer",
                    'sticky': False,
                }
            }
            return message
        if not self.material_purchase_ids:
            self.line_added = True
        if not self.line_added:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('Add lines'),
                    'message': "Please add purchase order line to internal transfer",
                    'sticky': False,
                }
            }
            return message
        if not self.material_transfer_ids:
            self.stage = 'material_arrived'
            self.work_order_id.state = 'material_arrive'
            return {
                'type': 'ir.actions.act_window',
                'name': _('Work Order'),
                'res_model': 'job.order',
                'res_id': self.work_order_id.id,
                'view_mode': 'form',
                'target': 'current'
            }
        else:
            self.stage = 'ready_delivery'

    def action_create_purchase_order(self):
        ready = True
        for rec in self.material_purchase_ids:
            if not rec.vendor_id:
                ready = False
        if not ready:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': ('Vendor or Warehouse Missing !'),
                    'message': "Please Select Warehouse or Vendor in Material Purchase",
                    'sticky': False,
                }
            }
            return message
        price_check = True
        for rec in self.material_purchase_ids:
            if not rec.price > 0:
                price_check = False
        if not price_check:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': ('Invalid Product Price !'),
                    'message': "Price must greater than zero to create Purchase Order.",
                    'sticky': False,
                }
            }
            return message
        vendor_count = self.material_purchase_ids.mapped('vendor_id').mapped('id')
        warehouse_count = self.material_purchase_ids.mapped('purchase_warehouse_id').mapped('id')
        for warehouse in warehouse_count:
            for data in vendor_count:
                lines = []
                create_po_ids = []
                for rec in self.material_purchase_ids:
                    if rec.purchase_warehouse_id.id == warehouse and not rec.purchase_order_id and rec.vendor_id.id == data:
                        lines.append((0, 0, {
                            'product_id': rec.product_id.id,
                            'name': rec.name,
                            'product_qty': rec.qty,
                            'product_uom': rec.uom_id.id,
                            'price_unit': rec.price,
                        }))
                        create_po_ids.append(rec.id)
                        rec.product_id.last_po_price = rec.price
                stock_picking_type_id = self.env['stock.picking.type'].search(
                    [('code', '=', 'incoming'), ('warehouse_id', '=', warehouse)], limit=1)
                if lines and stock_picking_type_id:
                    record = {
                        'partner_id': data,
                        'order_line': lines,
                        'material_req_id': self.id,
                        'picking_type_id': stock_picking_type_id.id
                    }
                    purchase_order_id = self.env['purchase.order'].create(record)
                    for rec in create_po_ids:
                        materia_po_line = self.env['material.purchase.line'].browse(rec)
                        materia_po_line.purchase_order_id = purchase_order_id.id
        self.po_created = True

    def action_create_back_order(self):
        ready = True
        for rec in self.material_line_ids:
            if not rec.is_created:
                ready = False
        if not ready:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': "Please Validate Lines to Create Back Order",
                    'sticky': False,
                }
            }
            return message
        mrq = {
            'title': self.title,
            'project_id': self.project_id.id,
            'warehouse_id': self.warehouse_id.id,
            'department_id': self.department_id.id,
            'manager_ids': self.manager_ids.ids,
            'user_id': self.user_id.id,
            'company_id': self.company_id.id,
            'job_sheet_id': self.job_sheet_id.id,
            'stage': 'approve',
            'is_back_order': True,
            'work_type_id': self.work_type_id.id,
            'work_order_id': self.work_order_id.id,
            'job_sheet_id': self.job_sheet_id.id,
            'site_id': self.site_id.id,
            'material_req_ref': self.name
        }
        mrq_id = self.env['material.requisition'].create(mrq)
        self.back_order_id = mrq_id.id
        for data in self.material_line_ids:
            if data.operation_type == 'back_order':
                record = {
                    'product_id': data.material_id.id,
                    'name': data.name,
                    'qty': data.back_order_qty,
                    'price': data.material_id.last_po_price if data.material_id.last_po_price != 0 else data.material_id.standard_price,
                    'purchase_warehouse_id': data.warehouse_id.id,
                    'material_req_id': mrq_id.id,
                    'sub_category_id': data.sub_category_id.id,
                    'job_sheet_id': data.job_sheet_id.id
                }
                self.env['material.purchase.line'].create(record)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Back Order'),
            'res_model': 'material.requisition',
            'res_id': mrq_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def validate_material_line_all(self):
        validate = True
        for rec in self.material_line_ids:
            if not rec.is_created and (not rec.warehouse_id or not rec.operation_type):
                validate = False
        if not validate:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': ('Warehouse or operation type Missing !'),
                    'message': "Please Select warehouse or operation Type to validate.",
                    'sticky': False,
                }
            }
            return message
        for rec in self.material_line_ids:
            if not rec.is_created:
                rec.validate_material_line()

    def action_insert_internal_transfer(self):
        for rec in self.material_purchase_ids:
            if not rec.purchase_warehouse_id.id == self.project_id.warehouse_id.id:
                internal_transfer_id = self.env['material.transfer.line'].create({
                    'product_id': rec.product_id.id,
                    'name': rec.name,
                    'pickup_warehouse_id': rec.purchase_warehouse_id.id,
                    'delivery_warehouse_id': self.project_id.warehouse_id.id,
                    'qty': rec.qty,
                    'material_req_id': rec.material_req_id.id,
                    'sub_category_id': rec.sub_category_id.id,
                    'job_sheet_id': rec.job_sheet_id.id,
                    'from_purchase': True
                })
                internal_transfer_id._compute_forcast_qty()
        self.line_added = True

    def action_create_internal_transfer(self):
        internal_transfer_id = self.env['internal.transfer'].create({
            'title': 'Internal Transfer of ' + str(self.name),
            'site_id': self.site_id.id,
            'project_id': self.project_id.id,
            'work_type_id': self.work_type_id.id,
            'job_sheet_id': self.job_sheet_id.id,
            'work_order_id': self.work_order_id.id,
            'material_req_id': self.id,
            'department_id': self.department_id.id,
            'manager_ids': self.manager_ids.ids,
            'user_id': self.user_id.id,
        })
        for data in self.material_transfer_ids:
            self.env['internal.transfer.line'].create({
                'product_id': data.product_id.id,
                'name': data.name,
                'qty': data.qty,
                'pickup_warehouse_id': data.pickup_warehouse_id.id,
                'delivery_warehouse_id': data.delivery_warehouse_id.id,
                'internal_transfer_id': internal_transfer_id.id,
                'sub_category_id': data.sub_category_id.id,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Internal Transfer'),
            'res_model': 'internal.transfer',
            'res_id': internal_transfer_id.id,
            'view_mode': 'form',
            'target': 'current'
        }


class MaterialRequisitionLine(models.Model):
    _name = 'material.requisition.line'
    _description = "Material Requisition Line"

    material_id = fields.Many2one('product.product', string="Material", domain="[('is_material','=',True)]")
    name = fields.Char(string="Description")
    qty = fields.Integer(string="Qty.", default=1)
    uom_id = fields.Many2one(related="material_id.uom_po_id", string="Unit of Measure")
    operation_type = fields.Selection([('purchase_order', 'Purchase Order'),
                                       ('internal_transfer', 'Internal Transfer'), ('back_order', 'Back Order')],
                                      string="Operation Type")
    forcast_qty = fields.Float(string="Forcast Qty.", compute="_compute_forcast_qty")
    warehouse_id = fields.Many2one('stock.warehouse', string="Pickup / Delivery Warehouse")
    material_req_id = fields.Many2one('material.requisition')
    is_created = fields.Boolean()
    forcast_check = fields.Boolean(compute="_compute_forcast_check")
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    stage = fields.Selection(related="material_req_id.stage")
    job_sheet_id = fields.Many2one('job.costing', string="Job Cost Sheet")
    remain_qty = fields.Integer(string="Remaining Qty.")
    back_order_qty = fields.Integer(string="Back Order Qty.")

    @api.depends('receive_qty', 'qty')
    def _compute_receive_qty(self):
        for rec in self:
            if rec.receive_qty and rec.qty:
                rec.remain_qty = rec.qty - rec.receive_qty
            else:
                rec.remain_qty = 0

    @api.onchange('material_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.material_id.name

    @api.depends('forcast_qty', 'qty')
    def _compute_forcast_check(self):
        for rec in self:
            if rec.forcast_qty >= rec.qty:
                rec.forcast_check = True
            else:
                rec.forcast_check = False

    @api.depends('warehouse_id', 'material_id')
    def _compute_forcast_qty(self):
        for rec in self:
            qty = 0.0
            if rec.material_id:
                qty = rec.material_id.with_context(warehouse=rec.warehouse_id.id).virtual_available
            rec.forcast_qty = qty

    def validate_material_line(self):
        if not self.is_created:
            if not self.warehouse_id or not self.operation_type:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'info',
                        'title': ('Warehouse or operation type Missing !'),
                        'message': "Please Select warehouse or operation Type to validate.",
                        'sticky': False,
                    }
                }
                return message
            if self.operation_type == 'purchase_order':
                purchase_data = {
                    'product_id': self.material_id.id,
                    'name': self.name,
                    'qty': self.qty,
                    'purchase_warehouse_id': self.warehouse_id.id,
                    'material_req_id': self.material_req_id.id,
                    'sub_category_id': self.sub_category_id.id,
                    'job_sheet_id': self.job_sheet_id.id,
                    'price': self.material_id.last_po_price if self.material_id.last_po_price != 0 else self.material_id.standard_price
                }
                self.env['material.purchase.line'].create(purchase_data)
            if self.operation_type == 'internal_transfer':
                internal_data = {
                    'product_id': self.material_id.id,
                    'name': self.name,
                    'qty': self.qty,
                    'pickup_warehouse_id': self.warehouse_id.id,
                    'delivery_warehouse_id': self.material_req_id.project_id.warehouse_id.id,
                    'material_req_id': self.material_req_id.id,
                    'sub_category_id': self.sub_category_id.id,
                    'job_sheet_id': self.job_sheet_id.id
                }
                if internal_data['pickup_warehouse_id'] == internal_data['delivery_warehouse_id']:
                    pass
                else:
                    self.env['material.transfer.line'].create(internal_data)
            if self.operation_type == 'back_order':
                if self.qty > self.forcast_qty:
                    self.back_order_qty = self.qty - self.forcast_qty
                    internal_data = {
                        'product_id': self.material_id.id,
                        'name': self.name,
                        'qty': self.forcast_qty,
                        'pickup_warehouse_id': self.warehouse_id.id,
                        'delivery_warehouse_id': self.material_req_id.project_id.warehouse_id.id,
                        'material_req_id': self.material_req_id.id,
                        'sub_category_id': self.sub_category_id.id,
                        'job_sheet_id': self.job_sheet_id.id
                    }
                    if internal_data['pickup_warehouse_id'] == internal_data['delivery_warehouse_id']:
                        pass
                    else:
                        self.env['material.transfer.line'].create(internal_data)
            self.is_created = True


class MaterialPurchaseLine(models.Model):
    _name = 'material.purchase.line'
    _description = "Material Purchase Line"

    product_id = fields.Many2one('product.product', string="Product")
    name = fields.Char(string="Description")
    qty = fields.Integer(string="Qty.", default=1)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    forcast_qty = fields.Float(string="Forcast Qty.", compute="_compute_forcast_qty")
    price = fields.Monetary(string="Price")
    total_price = fields.Monetary(string="Total Price", compute="_compute_total_price")
    uom_id = fields.Many2one(related="product_id.uom_po_id", string="Unit of Measure")
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    purchase_warehouse_id = fields.Many2one('stock.warehouse', string="Delivery Warehouse")
    material_req_id = fields.Many2one('material.requisition')
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    status = fields.Selection([('incomplete', 'Incomplete'), ('partial_complete', 'Partial Complete'),
                               ('complete', 'Complete')], compute="_compute_po_delivery_status")
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    job_sheet_id = fields.Many2one('job.costing', string="Job Cost Sheet")

    def unlink(self):
        if not self.purchase_order_id:
            return super(MaterialPurchaseLine, self).unlink()
        else:
            raise ValidationError(_('You can not delete material purchase line after creating purchase order'))

    @api.depends('purchase_warehouse_id', 'product_id')
    def _compute_forcast_qty(self):
        for rec in self:
            qty = 0.0
            if rec.product_id:
                qty = rec.product_id.with_context(warehouse=rec.purchase_warehouse_id.id).virtual_available
            rec.forcast_qty = qty

    @api.depends('price', 'qty')
    def _compute_total_price(self):
        for rec in self:
            total = 0.0
            if rec.qty and rec.price:
                total = rec.qty * rec.price
            rec.total_price = total

    @api.onchange('product_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.product_id.name

    @api.depends('purchase_order_id')
    def _compute_po_delivery_status(self):
        for rec in self:
            delivery_orders = self.env['stock.picking'].search(
                [('code', '=', 'incoming'), ('origin', '=', rec.purchase_order_id.name)])
            if rec.purchase_order_id and delivery_orders:
                incomplete, complete = False, False
                for data in delivery_orders:
                    if data.state == 'done':
                        complete = True
                    else:
                        incomplete = True
                if complete and not incomplete:
                    rec.status = 'complete'
                elif incomplete and not complete:
                    rec.status = 'incomplete'
                else:
                    rec.status = "partial_complete"
            else:
                rec.status = ""

    @api.onchange('product_id', 'vendor_id')
    def onchange_product_vendor_price_list(self):
        for rec in self:
            if rec.vendor_id and rec.product_id:
                domain = [('partner_id', '=', rec.vendor_id.id), '|',
                          ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id),
                          ('product_id', '=', rec.product_id.id)]
                vendor_price = self.env['product.supplierinfo'].search(domain, limit=1, order='create_date desc')
                if vendor_price.price > 0:
                    rec.price = vendor_price.price
                elif rec.product_id.last_po_price > 0:
                    rec.price = rec.product_id.last_po_price
                else:
                    rec.price = rec.product_id.standard_price


class MaterialTransferLine(models.Model):
    _name = 'material.transfer.line'
    _description = "Material Transfer Line"

    product_id = fields.Many2one('product.product', string="Product")
    name = fields.Char(string="Description")
    qty = fields.Integer(string="Qty.", default=1)
    forcast_qty = fields.Float(string="Forcast Qty.", compute="_compute_forcast_qty")
    pickup_warehouse_id = fields.Many2one('stock.warehouse', string="Picking Warehouse")
    delivery_warehouse_id = fields.Many2one('stock.warehouse', string="Delivery Warehouse")
    material_req_id = fields.Many2one('material.requisition')
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")
    job_sheet_id = fields.Many2one('job.costing', string="Job Cost Sheet")
    from_purchase = fields.Boolean(string="From Purchase")

    @api.depends('pickup_warehouse_id', 'product_id')
    def _compute_forcast_qty(self):
        for rec in self:
            qty = 0.0
            if rec.product_id:
                qty = rec.product_id.with_context(warehouse=rec.pickup_warehouse_id.id).virtual_available
            rec.forcast_qty = qty

    @api.onchange('product_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.product_id.name
