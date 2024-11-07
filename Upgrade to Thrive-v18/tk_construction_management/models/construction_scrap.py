# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, api, models, _


class ScrapOrder(models.Model):
    _name = 'scrap.order'
    _description = "Construction Scrap Order"
    _rec_name = 'name'

    name = fields.Char(string='Sequence', copy=False, required=True, readonly=True, default=lambda self: _('New'))
    date = fields.Date(string="Date", default=fields.Date.today())
    note = fields.Text(string="Note")
    job_order_id = fields.Many2one('job.order', string="Work Order")
    scrap_order_line_ids = fields.One2many('scrap.order.line', 'scrap_order_id', string="Scrap Order Line")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total = fields.Monetary(string="Total", compute="_compute_net_total", store=True)
    invoice_id = fields.Many2one('account.move', string="Invoice")
    vendor_id = fields.Many2one('res.partner', string="Vendor")

    @api.depends('scrap_order_line_ids')
    def _compute_net_total(self):
        for rec in self:
            amount = 0.0
            if rec.scrap_order_line_ids:
                for data in rec.scrap_order_line_ids:
                    amount = amount + data.net_total
                rec.total = amount
            else:
                rec.total = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('scrap.order') or _('New')
        res = super(ScrapOrder, self).create(vals_list)
        return res

    @api.onchange('job_order_id')
    def _onchange_job_order(self):
        for rec in self:
            if not rec.job_order_id:
                return
            if rec.job_order_id:
                lines = []
                rec.scrap_order_line_ids = [(5, 0, 0)]
                for data in rec.job_order_id.material_order_ids:
                    lines.append((0, 0, {
                        'product_id': data.material_id.id,
                        'scrap_type': 'material',
                        'qty': 1,
                    }))
                for data in rec.job_order_id.equipment_order_ids:
                    lines.append((0, 0, {
                        'product_id': data.equipment_id.id,
                        'scrap_type': 'equipment',
                        'qty': 1,
                    }))
                for data in rec.job_order_id.overhead_order_ids:
                    lines.append((0, 0, {
                        'product_id': data.product_id.id,
                        'scrap_type': 'overhead',
                        'qty': 1,
                    }))
                rec.scrap_order_line_ids = lines

    def action_create_invoice(self):
        invoice_line = []
        for data in self.scrap_order_line_ids:
            invoice_line.append((0, 0, {
                'product_id': data.product_id.id,
                'name': data.product_id.name,
                'quantity': data.qty,
                'tax_ids': False,
                'price_unit': data.dep_cost
            }))
        invoice_id = self.env['account.move'].create({
            'partner_id': self.vendor_id.id,
            'invoice_line_ids': invoice_line,
            'move_type': 'out_invoice',
        })
        invoice_id.action_post()
        self.invoice_id = invoice_id.id


class ScrapOrderLine(models.Model):
    _name = 'scrap.order.line'
    _description = "Scrap Order Line"

    scrap_type = fields.Selection([('material', 'Material'), ('equipment', 'Equipment'), ('overhead', 'Overhead')],
                                  string="Scrap of")
    product_id = fields.Many2one("product.product", string="Product")
    qty = fields.Integer(string="Qty.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    dep_cost = fields.Monetary(string="Value")
    scrap_order_id = fields.Many2one('scrap.order', string="Scrap Order")
    net_total = fields.Monetary(string="Total Value", compute="_compute_net_total")

    @api.onchange('scrap_type')
    def filter_materia_equipment(self):
        for rec in self:
            if rec.scrap_type == "material":
                return {'domain': {'product_id': [('is_material', '=', True)]}}
            elif rec.scrap_type == "equipment":
                return {'domain': {'product_id': [('is_equipment', '=', True)]}}
            elif rec.scrap_type == 'overhead':
                return {'domain': {'product_id': [('is_overhead', '=', True)]}}

    @api.depends('dep_cost', 'qty')
    def _compute_net_total(self):
        for rec in self:
            if rec.product_id:
                rec.net_total = rec.dep_cost * rec.qty
            else:
                rec.net_total = 0
