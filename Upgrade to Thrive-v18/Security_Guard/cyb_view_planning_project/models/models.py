# -*- coding: utf-8 -*-

from thrive import models, fields, api, _



class Project(models.Model):
    _inherit = "project.project"



    def view_project_planning(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _("%(name)s's Planning", name=self.name),
            'domain': [('project_id', '=', self.id)],
            'res_model': 'planning.slot',
            'views': [(self.env.ref('project_forecast.planning_view_gantt').id, 'gantt')],
            'view_mode': 'gantt',
            'context': {
                'default_project_id': self.id,
                **self.env.context
            }
        }
