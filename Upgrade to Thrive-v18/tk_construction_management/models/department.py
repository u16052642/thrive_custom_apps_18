# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, api, models


class ConstructionDepartment(models.Model):
    _name = 'construction.department'
    _description = "Construction department"

    name = fields.Char(string="Department Name")
    manager_ids = fields.Many2many('res.users', string="Manager")
    user_ids = fields.Many2many('res.users', 'construction_user_team_rel', 'user_id', 'team_id_id',
                                string="Responsible", domain="[('id','not in',manager_ids)]")
    department_id = fields.Many2one('hr.department', string="HR Department")

    @api.model_create_multi
    def create(self, vals):
        res = super(ConstructionDepartment, self).create(vals)
        for rec in res:
            for data in rec.manager_ids:
                data.department_ids = data.department_ids.ids + [rec.id]
        return res
