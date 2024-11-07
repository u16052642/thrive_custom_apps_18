# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, api, models


class ConstructionResUser(models.Model):
    _inherit = 'res.users'

    department_ids = fields.Many2many('construction.department', string="Department ")
