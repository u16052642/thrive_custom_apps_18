# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import api, fields, models, _


class SiteProject(models.TransientModel):
    _name = 'site.project'
    _description = "Site Project"

    name = fields.Char(string="Name")

    def action_create_construction_project(self):
        active_id = self._context.get('active_id')
        site_id = self.env['tk.construction.site'].browse(active_id)
        data = {
            'name': self.name,
            'construction_site_id': site_id.id,
            'start_date': site_id.start_date,
            'end_date': site_id.end_date,
            'zip': site_id.zip,
            'street': site_id.street,
            'street2': site_id.street2,
            'city': site_id.city,
            'state_id': site_id.state_id.id,
            'country_id': site_id.country_id.id,
            'longitude': site_id.longitude,
            'latitude': site_id.latitude
        }
        project_id = self.env['tk.construction.project'].create(data)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Project'),
            'res_model': 'tk.construction.project',
            'res_id': project_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
