# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import api, fields, models, _
from thrive.exceptions import ValidationError


class RateAnalysis(models.Model):
    _name = 'rate.analysis'
    _description = "Rate Analysis"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Title")
    site_id = fields.Many2one('tk.construction.site', string="Project")
    project_id = fields.Many2one('tk.construction.project', string="Sub Project",domain="[('construction_site_id','=',site_id)]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    activity_id = fields.Many2one('job.type', string="Work Type")
    sub_activity_ids = fields.Many2many(related="activity_id.sub_category_ids", string="Sub Activities")
    sub_activity_id = fields.Many2one('job.sub.category', string="Work Sub Type",domain="[('id','in',sub_activity_ids)]")
    date = fields.Date(string="Date", default=fields.Date.today())
    unit_id = fields.Many2one('uom.uom', string="Unit")

    # Rate Analysis Type
    material_analysis_ids = fields.One2many('rate.analysis.material', 'rate_analysis_id', string="Rate Analysis Material")
    equipment_analysis_ids = fields.One2many('rate.analysis.equipment', 'rate_analysis_id',string="Rate Analysis Equipment")
    labour_analysis_ids = fields.One2many('rate.analysis.labour', 'rate_analysis_id',string="Rate Analysis Labour")
    overhead_analysis_ids = fields.One2many('rate.analysis.overhead', 'rate_analysis_id',string="Rate Analysis Overhead")

    # Amount
    tax_amount = fields.Monetary(string="Tax Amount", compute="compute_total_amount")
    untaxed_amount = fields.Monetary(string="Untaxed Amount", compute="compute_total_amount")
    total_amount = fields.Monetary(string="Total Amount", compute="compute_total_amount")

    @api.depends('material_analysis_ids', 'equipment_analysis_ids', 'labour_analysis_ids', 'overhead_analysis_ids')
    def compute_total_amount(self):
        for rec in self:
            tax_amount = 0.0
            untaxed_amount = 0.0
            total_amount = 0.0
            for data in rec.material_analysis_ids:
                tax_amount = tax_amount + data.tax_amount
                untaxed_amount = untaxed_amount + data.untaxed_amount
                total_amount = total_amount + data.total_amount
            for data in rec.equipment_analysis_ids:
                tax_amount = tax_amount + data.tax_amount
                untaxed_amount = untaxed_amount + data.untaxed_amount
                total_amount = total_amount + data.total_amount
            for data in rec.labour_analysis_ids:
                tax_amount = tax_amount + data.tax_amount
                untaxed_amount = untaxed_amount + data.untaxed_amount
                total_amount = total_amount + data.total_amount
            for data in rec.overhead_analysis_ids:
                tax_amount = tax_amount + data.tax_amount
                untaxed_amount = untaxed_amount + data.untaxed_amount
                total_amount = total_amount + data.total_amount
            rec.tax_amount = tax_amount
            rec.untaxed_amount = untaxed_amount
            rec.total_amount = total_amount

    @api.constrains('material_analysis_ids')
    def _check_cost_material_uniq_product(self):
        for record in self.material_analysis_ids:
            duplicates = self.material_analysis_ids.filtered(
                lambda r: r.id != record.id and r.product_id.id == record.product_id.id)
            if duplicates:
                raise ValidationError(_("Material already added !"))

    @api.constrains('equipment_analysis_ids')
    def _check_cost_equipment_uniq_product(self):
        for record in self.equipment_analysis_ids:
            duplicates = self.equipment_analysis_ids.filtered(
                lambda r: r.id != record.id and r.product_id.id == record.product_id.id)
            if duplicates:
                raise ValidationError(_("Equipment already added !"))

    @api.constrains('labour_analysis_ids')
    def _check_cost_labour_uniq_product(self):
        for record in self.labour_analysis_ids:
            duplicates = self.labour_analysis_ids.filtered(
                lambda r: r.id != record.id and r.product_id.id == record.product_id.id)
            if duplicates:
                raise ValidationError(_("Labour already added !"))

    @api.constrains('overhead_analysis_ids')
    def _check_cost_overhead_uniq_product(self):
        for record in self.overhead_analysis_ids:
            duplicates = self.overhead_analysis_ids.filtered(
                lambda r: r.id != record.id and r.product_id.id == record.product_id.id)
            if duplicates:
                raise ValidationError(_("Overhead already added !"))



class RateAnalysisMaterial(models.Model):
    _name = "rate.analysis.material"
    _description = "Rate Analysis Material Line"

    rate_analysis_id = fields.Many2one('rate.analysis', string="Rate Analysis")
    product_id = fields.Many2one('product.product', string="Material", domain="[('is_material','=',True)]")
    name = fields.Char(string="Description")
    code = fields.Char(related="product_id.default_code", string="Code")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    qty = fields.Integer(string="Qty.", default=1)
    uom_id = fields.Many2one(related="product_id.uom_po_id", string="UOM")
    price = fields.Monetary(string="Price")
    tax_id = fields.Many2one('account.tax', string="Tax")
    untaxed_amount = fields.Monetary(string="Untaxed Amount", compute="compute_total")
    tax_amount = fields.Monetary(string="Tax Amount", compute="compute_total")
    total_amount = fields.Monetary(string="Total Amount", compute="compute_total")

    @api.onchange('product_id')
    def onchange_product_info(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name
                rec.price = rec.product_id.standard_price

    @api.depends('price', 'qty', 'tax_id.amount', 'tax_id')
    def compute_total(self):
        for rec in self:
            untaxed_amount = rec.qty * rec.price
            tax_amount = (rec.tax_id.amount * untaxed_amount / 100) if rec.tax_id else 0.0
            total_amount = untaxed_amount + tax_amount
            rec.untaxed_amount = untaxed_amount
            rec.tax_amount = tax_amount
            rec.total_amount = total_amount


class RateAnalysisEquipment(models.Model):
    _name = "rate.analysis.equipment"
    _description = "Rate Analysis Equipment Line"

    rate_analysis_id = fields.Many2one('rate.analysis', string="Rate Analysis")
    product_id = fields.Many2one('product.product', string="Equipment", domain="[('is_equipment','=',True)]")
    name = fields.Char(string="Description")
    code = fields.Char(related="product_id.default_code", string="Code")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    qty = fields.Integer(string="Qty.", default=1)
    uom_id = fields.Many2one(related="product_id.uom_po_id", string="UOM")
    price = fields.Monetary(string="Price")
    tax_id = fields.Many2one('account.tax', string="Tax")
    untaxed_amount = fields.Monetary(string="Untaxed Amount", compute="compute_total")
    tax_amount = fields.Monetary(string="Tax Amount", compute="compute_total")
    total_amount = fields.Monetary(string="Total Amount", compute="compute_total")

    @api.onchange('product_id')
    def onchange_product_info(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name
                rec.price = rec.product_id.standard_price

    @api.depends('price', 'qty', 'tax_id.amount', 'tax_id')
    def compute_total(self):
        for rec in self:
            untaxed_amount = rec.qty * rec.price
            tax_amount = (rec.tax_id.amount * untaxed_amount / 100) if rec.tax_id else 0.0
            total_amount = untaxed_amount + tax_amount
            rec.untaxed_amount = untaxed_amount
            rec.tax_amount = tax_amount
            rec.total_amount = total_amount


class RateAnalysisLabour(models.Model):
    _name = "rate.analysis.labour"
    _description = "Rate Analysis Labour Line"

    rate_analysis_id = fields.Many2one('rate.analysis', string="Rate Analysis")
    product_id = fields.Many2one('product.product', string="Labour", domain="[('is_labour','=',True)]")
    name = fields.Char(string="Description")
    code = fields.Char(related="product_id.default_code", string="Code")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    qty = fields.Integer(string="Qty.", default=1)
    uom_id = fields.Many2one(related="product_id.uom_po_id", string="UOM")
    price = fields.Monetary(string="Price")
    tax_id = fields.Many2one('account.tax', string="Tax")
    untaxed_amount = fields.Monetary(string="Untaxed Amount", compute="compute_total")
    tax_amount = fields.Monetary(string="Tax Amount", compute="compute_total")
    total_amount = fields.Monetary(string="Total Amount", compute="compute_total")

    @api.onchange('product_id')
    def onchange_product_info(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name
                rec.price = rec.product_id.standard_price

    @api.depends('price', 'qty', 'tax_id.amount', 'tax_id')
    def compute_total(self):
        for rec in self:
            untaxed_amount = rec.qty * rec.price
            tax_amount = (rec.tax_id.amount * untaxed_amount / 100) if rec.tax_id else 0.0
            total_amount = untaxed_amount + tax_amount
            rec.untaxed_amount = untaxed_amount
            rec.tax_amount = tax_amount
            rec.total_amount = total_amount


class RateAnalysisOverhead(models.Model):
    _name = "rate.analysis.overhead"
    _description = "Rate Analysis Overhead Line"

    rate_analysis_id = fields.Many2one('rate.analysis', string="Rate Analysis")
    product_id = fields.Many2one('product.product', string="Overhead", domain="[('is_overhead','=',True)]")
    name = fields.Char(string="Description")
    code = fields.Char(related="product_id.default_code", string="Code")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    qty = fields.Integer(string="Qty.", default=1)
    uom_id = fields.Many2one(related="product_id.uom_po_id", string="UOM")
    price = fields.Monetary(string="Price")
    tax_id = fields.Many2one('account.tax', string="Tax")
    untaxed_amount = fields.Monetary(string="Untaxed Amount", compute="compute_total")
    tax_amount = fields.Monetary(string="Tax Amount", compute="compute_total")
    total_amount = fields.Monetary(string="Total Amount", compute="compute_total")

    @api.onchange('product_id')
    def onchange_product_info(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name
                rec.price = rec.product_id.standard_price

    @api.depends('price', 'qty', 'tax_id.amount', 'tax_id')
    def compute_total(self):
        for rec in self:
            untaxed_amount = rec.qty * rec.price
            tax_amount = (rec.tax_id.amount * untaxed_amount / 100) if rec.tax_id else 0.0
            total_amount = untaxed_amount + tax_amount
            rec.untaxed_amount = untaxed_amount
            rec.tax_amount = tax_amount
            rec.total_amount = total_amount
