# -*- coding: utf-8 -*-
# Part of Thrive Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from thrive import models, fields, api

class Bookmarklink(models.Model):
	_name = 'bookmark.link'
	_description = "Bookmark Link"

	name = fields.Char("Name")
	title = fields.Char("Title")
	url = fields.Char("URL")
	user_id = fields.Many2one('res.users')