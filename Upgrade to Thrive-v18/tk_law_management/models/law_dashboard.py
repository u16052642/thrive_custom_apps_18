# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from thrive import models, fields, api, _


class LawDashboard(models.Model):
    _name = "law.dashboard"
    _description = "Law Dashboard"

    @api.model
    def get_law_dashboard(self):
        case_matter = self.env['case.matter'].sudo().search_count([])
        open_case_matter = self.env['case.matter'].sudo().search_count([('state', '=', 'open')])
        pending_case_matter = self.env['case.matter'].sudo().search_count([('state', '=', 'pending')])
        close_case_matter = self.env['case.matter'].sudo().search_count([('state', '=', 'close')])
        law_practise_area = self.env['law.practise.area'].sudo().search_count([])
        matter_category = self.env['matter.category'].sudo().search_count([])
        law_court = self.env['law.court'].sudo().search_count([])
        case_judge = self.env['res.users'].sudo().search_count([])
        case_lawyer = self.env['res.partner'].sudo().search_count([('is_lawyer', '=', True)])

        case_matter_status = [['Open', 'Pending', 'Close'], [open_case_matter, pending_case_matter, close_case_matter]]
        over_all_info = [['Judges', 'Lawyers'], [case_judge, case_lawyer]]

        data = {
            'case_matter': case_matter,
            'open_case_matter': open_case_matter,
            'pending_case_matter': pending_case_matter,
            'close_case_matter': close_case_matter,
            'law_practise_area': law_practise_area,
            'matter_category': matter_category,
            'law_court': law_court,
            'case_judge': case_judge,
            'case_lawyer': case_lawyer,
            'case_matter_status': case_matter_status,
            'over_all_info': over_all_info,
        }
        return data
