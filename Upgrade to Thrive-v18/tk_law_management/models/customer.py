# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import models, fields, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_lawyer = fields.Boolean(string="Lawyer")
    practise_area_ids = fields.Many2many('law.practise.area', string="Law Selection")

    evidence_count = fields.Integer("Evidence", compute="_get_evidence_count")
    trial_count = fields.Integer("Trial", compute="_get_trial_count")
    matter_count = fields.Integer("Matter", compute="_get_matter_count")

    def _get_evidence_count(self):
        for rec in self:
            evidences = self.env['case.evidence'].search_count([('customer_id', '=', rec.id)])
            rec.evidence_count = evidences

    def action_evidence_view(self):
        return {
            'name': _('Evidences'),
            'type': 'ir.actions.act_window',
            'res_model': 'case.evidence',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'target': 'current',
        }

    def _get_trial_count(self):
        for rec in self:
            trial_count = self.env['court.trial'].search_count([('customer_id', '=', rec.id)])
            rec.trial_count = trial_count

    def action_trial_view(self):
        return {
            'name': _('Trials'),
            'type': 'ir.actions.act_window',
            'res_model': 'court.trial',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'target': 'current',
        }

    def _get_matter_count(self):
        for rec in self:
            matter_count = self.env['case.matter'].search_count([('customer_id', '=', rec.id)])
            rec.matter_count = matter_count

    def action_matter_view(self):
        return {
            'name': _('Matters'),
            'type': 'ir.actions.act_window',
            'res_model': 'case.matter',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'target': 'current',
        }
