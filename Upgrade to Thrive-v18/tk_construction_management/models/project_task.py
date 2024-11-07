# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import fields, api, models


class ConProject(models.Model):
    _inherit = 'project.project'

    construction_project_id = fields.Many2one('tk.construction.project', string="Construction Project")


class ConstructionTask(models.Model):
    _inherit = 'project.task'

    job_order_id = fields.Many2one('job.order', string="Work Order")
    is_inspection_task = fields.Boolean(string="Inspection Task")
    con_project_id = fields.Many2one('tk.construction.project', string="Construction Project")
