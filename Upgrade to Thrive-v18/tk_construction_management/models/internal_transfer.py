# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, models, api, _


class InternalTransfer(models.Model):
    _name = 'internal.transfer'
    _description = 'Internal transfer material requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: _('New'))
    title = fields.Char(string="Title")
    stage = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done'),
                              ('cancel', 'Cancel')], default='draft', string="Stage", tracking=True)
    is_order_created = fields.Boolean()
    delivery_order_check = fields.Boolean(compute="_compute_delivery_order_status")

    # Other Details
    date = fields.Date(string="Date", default=fields.Date.today())
    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user and self.env.user.id or False,
                                     string="Created By")

    # Project Details
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    site_id = fields.Many2one('tk.construction.site', string="Project")
    project_id = fields.Many2one('tk.construction.project', string="Sub Project")
    warehouse_id = fields.Many2one(related="site_id.warehouse_id")

    # Work Type & Phase
    work_type_id = fields.Many2one('job.type', string="Work Type")
    job_sheet_id = fields.Many2one('job.costing', string="Phase(WBS)")
    work_order_id = fields.Many2one('job.order', string="Work Order")
    material_req_id = fields.Many2one('material.requisition', string="Material Requisition")

    # Internal Transfer & Forward Transfer
    is_forward_transfer = fields.Boolean(tracking=True)
    forward_transfer_id = fields.Many2one('internal.transfer', string="Forward Transfer")
    internal_ref = fields.Char(string="Internal Transfer Ref.")

    # Department
    department_id = fields.Many2one('construction.department', string="Department")
    manager_ids = fields.Many2many('res.users', string="Manager")
    user_id = fields.Many2one('res.users', string="Responsible User ")

    # Additional Info
    vehicle_no = fields.Char(string="Vehicle No")
    vehicle_name = fields.Char(string="Name")
    model = fields.Char(string="Model")
    driver_name = fields.Char(string="Driver Name")
    phone = fields.Char(string="Phone")

    # One 2 many
    internal_line_ids = fields.One2many('internal.transfer.line', 'internal_transfer_id',
                                        string="Internal Transfer Line")

    # Count
    delivery_count = fields.Integer(string="Delivery Count", compute="_compute_count")

    # Create, Write, Unlink, Constrain
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('internal.transfer') or _('New')
        res = super(InternalTransfer, self).create(vals_list)
        return res

    def name_get(self):
        data = []
        for rec in self:
            data.append((rec.id, '%s - %s' % (rec.name, rec.title)))
        return data

    # Compute
    def _compute_count(self):
        for rec in self:
            rec.delivery_count = self.env['stock.picking'].search_count([('transfer_id', '=', rec.id)])

    # Compute
    @api.depends('internal_line_ids')
    def _compute_delivery_order_status(self):
        delivery = True
        delivery_orders = self.env['stock.picking'].search([('transfer_id', '=', self.id)])
        if delivery_orders:
            for rec in delivery_orders:
                if not rec.state == 'done':
                    delivery = False
                    break
        else:
            delivery = False
        if delivery:
            self.delivery_order_check = True
        else:
            self.delivery_order_check = False

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
    def action_view_delivery_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery Orders'),
            'res_model': 'stock.picking',
            'domain': [('transfer_id', '=', self.id)],
            'context': {'default_transfer_id': self.id},
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    # Button
    def action_ready_transfer(self):
        self.stage = 'in_progress'
        self.material_req_id.stage = 'internal_transfer'

    def action_complete_transfer(self):
        self.material_req_id.stage = 'material_arrived'
        self.work_order_id.state = 'material_arrive'
        self.stage = 'done'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order'),
            'res_model': 'job.order',
            'res_id': self.work_order_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def action_cancel_transfer(self):
        self.material_req_id.stage = 'cancel'
        self.stage = 'cancel'

    def action_internal_transfer(self):
        pickup_warehouse_ids = self.internal_line_ids.mapped('pickup_warehouse_id').mapped('id')
        delivery_warehouse_ids = self.internal_line_ids.mapped('delivery_warehouse_id').mapped('id')
        for pickup in pickup_warehouse_ids:
            for delivery in delivery_warehouse_ids:
                lines = []
                created_ids = []
                stock_picking_type_id = False
                source_id = False
                destination_id = False
                for line in self.internal_line_ids:
                    if line.pickup_warehouse_id.id == pickup and line.delivery_warehouse_id.id == delivery:
                        lines.append((0, 0, {
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.qty,
                            'product_uom': line.uom_id.id,
                            'location_id': line.pickup_warehouse_id.lot_stock_id.id,
                            'location_dest_id': line.delivery_warehouse_id.lot_stock_id.id,
                            'name': line.name
                        }))
                        source_id = line.pickup_warehouse_id.lot_stock_id
                        destination_id = line.delivery_warehouse_id.lot_stock_id
                        stock_picking_type_id = self.env['stock.picking.type'].search(
                            [('code', '=', 'internal'), ('warehouse_id', '=', line.pickup_warehouse_id.id)], limit=1)
                        created_ids.append(line.id)
                if lines and stock_picking_type_id and source_id and destination_id:
                    delivery_record = {
                        'picking_type_id': stock_picking_type_id.id,
                        'location_id': source_id.id,
                        'location_dest_id': destination_id.id,
                        'move_ids_without_package': lines,
                        'transfer_id': self.id,
                        'move_type': 'one'
                    }
                    delivery_id = self.env['stock.picking'].create(delivery_record)
                    delivery_id.action_confirm()
                    for data in created_ids:
                        internal_line_id = self.env['internal.transfer.line'].browse(data)
                        internal_line_id.delivery_order_id = delivery_id.id
        self.material_req_id.internal_transfer_id = self.id
        self.is_order_created = True

    def action_forward_transfer(self):
        is_any_forward = False
        for data in self.internal_line_ids:
            if data.delivery_warehouse_id.id == self.warehouse_id.id:
                is_any_forward = True
        if not is_any_forward:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': "There are no any forward transfer in Internal transfer",
                    'sticky': False,
                }
            }
            return message
        if is_any_forward:
            internal_record = {
                'title': self.title,
                'site_id': self.site_id.id,
                'project_id': self.project_id.id,
                'work_type_id': self.work_type_id.id,
                'job_sheet_id': self.job_sheet_id.id,
                'work_order_id': self.work_order_id.id,
                'material_req_id': self.material_req_id.id,
                'company_id': self.company_id.id,
                'department_id': self.department_id.id,
                'manager_ids': self.manager_ids.ids,
                'user_id': self.user_id.id,
                'stage': 'in_progress',
                'internal_ref': self.name
            }
            internal_transfer_id = self.env['internal.transfer'].create(internal_record)
            for data in self.internal_line_ids:
                if data.delivery_warehouse_id.id == self.warehouse_id.id:
                    line_record = {
                        'sub_category_id': data.sub_category_id.id,
                        'product_id': data.product_id.id,
                        'name': data.name,
                        'qty': data.qty,
                        'pickup_warehouse_id': data.delivery_warehouse_id.id,
                        'delivery_warehouse_id': data.building_id.warehouse_id.id,
                        'internal_transfer_id': internal_transfer_id.id
                    }
                    self.env['internal.transfer.line'].create(line_record)
            self.forward_transfer_id = internal_transfer_id.id
            internal_transfer_id.is_forward_transfer = True
            return {
                'type': 'ir.actions.act_window',
                'name': _('Forward Transfer'),
                'res_model': 'internal.transfer',
                'res_id': internal_transfer_id.id,
                'view_mode': 'form',
                'target': 'current'
            }


class InternalTransferLine(models.Model):
    _name = 'internal.transfer.line'
    _description = "Internal Transfer Line"

    product_id = fields.Many2one('product.product', string="Product")
    name = fields.Char(string="Description")
    qty = fields.Integer('Qty.')
    forcast_qty = fields.Char(string="Forecast Qty.", compute="_compute_forcast_qty")
    uom_id = fields.Many2one(related="product_id.uom_po_id", string="UOM")
    pickup_warehouse_id = fields.Many2one('stock.warehouse', string="Pickup Warehouse")
    delivery_warehouse_id = fields.Many2one('stock.warehouse', string="Delivery Warehouse")
    internal_transfer_id = fields.Many2one('internal.transfer', string="Internal Transfer")
    delivery_order_id = fields.Many2one('stock.picking', string="Do")
    state = fields.Selection(related="delivery_order_id.state", string="Status")
    sub_category_id = fields.Many2one('job.sub.category', string="Work Sub Type")

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
