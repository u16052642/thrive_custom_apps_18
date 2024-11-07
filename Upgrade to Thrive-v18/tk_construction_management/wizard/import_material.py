# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import api, fields, models, _


class ImportMaterial(models.TransientModel):
    _name = 'import.material'
    _description = "Import Material for Material Requisition"

    material_req_id = fields.Many2one('material.requisition')
    template_id = fields.Many2one('construction.product.template', string="Template")

    @api.model
    def default_get(self, fields):
        res = super(ImportMaterial, self).default_get(fields)
        res['material_req_id'] = self._context.get('active_id')
        return res

    def action_import_material(self):
        self.material_req_id.material_line_ids = [(5, 0, 0)]
        for data in self.template_id.template_ids:
            record = {
                'material_id': data.product_id.id,
                'name': data.name,
                'material_req_id': self.material_req_id.id
            }
            self.env['material.requisition.line'].create(record)


class ImportMaterialSheet(models.Model):
    _name = 'import.material.sheet'
    _description = "Import Material from Sheet"

    job_cost_id = fields.Many2one('job.costing', string="Jon Cost")
    import_from = fields.Selection([('from_material', 'From Material Requisition'), ('from_template', 'From Template')],
                                   string="Import From", default='from_material')
    template_id = fields.Many2one('construction.product.template', string="Template")
    material_req_id = fields.Many2one('material.requisition', string="Material Requisition")

    @api.model
    def default_get(self, fields):
        res = super(ImportMaterialSheet, self).default_get(fields)
        res['job_cost_id'] = self._context.get('active_id')
        return res

    def action_import_material(self):
        self.job_cost_id.cost_material_ids = [(5, 0, 0)]
        if self.import_from == 'from_material':
            for data in self.material_req_id.material_line_ids:
                record = {
                    'material_id': data.material_id.id,
                    'name': data.name,
                    'job_costing_id': self.job_cost_id.id,
                    'job_type_id': data.job_type_id.id,
                    'sub_category_id': data.sub_category_id.id,
                }
                self.env['cost.material.line'].create(record)
        if self.import_from == 'from_template':
            for data in self.template_id.template_ids:
                record = {
                    'material_id': data.product_id.id,
                    'name': data.name,
                    'job_costing_id': self.job_cost_id.id
                }
                self.env['cost.material.line'].create(record)
