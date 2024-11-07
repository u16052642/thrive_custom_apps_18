# -*- coding: utf-8 -*-
# from thrive import http


# class CybViewPlanningProject(http.Controller):
#     @http.route('/cyb_view_planning_project/cyb_view_planning_project', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cyb_view_planning_project/cyb_view_planning_project/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cyb_view_planning_project.listing', {
#             'root': '/cyb_view_planning_project/cyb_view_planning_project',
#             'objects': http.request.env['cyb_view_planning_project.cyb_view_planning_project'].search([]),
#         })

#     @http.route('/cyb_view_planning_project/cyb_view_planning_project/objects/<model("cyb_view_planning_project.cyb_view_planning_project"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cyb_view_planning_project.object', {
#             'object': obj
#         })

