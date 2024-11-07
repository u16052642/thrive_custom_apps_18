# -*- coding: utf-8 -*-
# from thrive import http


# class CybatTaskShift(http.Controller):
#     @http.route('/cybat_task_shift/cybat_task_shift', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cybat_task_shift/cybat_task_shift/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cybat_task_shift.listing', {
#             'root': '/cybat_task_shift/cybat_task_shift',
#             'objects': http.request.env['cybat_task_shift.cybat_task_shift'].search([]),
#         })

#     @http.route('/cybat_task_shift/cybat_task_shift/objects/<model("cybat_task_shift.cybat_task_shift"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cybat_task_shift.object', {
#             'object': obj
#         })
