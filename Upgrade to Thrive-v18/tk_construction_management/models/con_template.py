# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import api, fields, models


class ConstructionTemplate(models.Model):
    _name = 'construction.product.template'
    _description = "Product Template"

    name = fields.Char(string="Title")
    template_ids = fields.One2many('construction.template.line', 'template_id')


class ConstructionTemplateLine(models.Model):
    _name = 'construction.template.line'
    _description = "Product Template Line"

    product_id = fields.Many2one('product.product', string="Product", domain="[('is_material','=',True)]")
    name = fields.Char(string="Description")
    template_id = fields.Many2one('construction.product.template')

    @api.onchange('product_id')
    def _onchange_product_desc(self):
        for rec in self:
            rec.name = rec.product_id.name
