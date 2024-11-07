# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import models, fields, api, _


class MatterCategory(models.Model):
    """Matter Category"""
    _name = "matter.category"
    _description = __doc__
    _rec_name = 'category'

    category = fields.Char(string="Category", required=True)


class MatterSubCategory(models.Model):
    """Matter Sub Category"""
    _name = "matter.sub.category"
    _description = __doc__
    _rec_name = 'sub_category'

    sub_category = fields.Char(string="Sub Category", required=True)
    matter_category_id = fields.Many2one('matter.category', string="Category", required=True)
