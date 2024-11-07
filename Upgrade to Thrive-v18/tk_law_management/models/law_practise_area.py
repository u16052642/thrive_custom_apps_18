# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import models, fields, api, _


class LawPractiseArea(models.Model):
    """Law Practise Area"""
    _name = "law.practise.area"
    _description = __doc__
    _rec_name = 'practise_area'

    color = fields.Integer()
    practise_area = fields.Char(string="Law Selection", required=True)
