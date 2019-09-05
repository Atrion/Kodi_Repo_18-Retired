# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from resources.lib.debrid import base
from resources.lib.debrid.rapidpremium import core

class Handle(base.Handle):

	def __init__(self):
		base.Handle.__init__(self, id = core.Core.Id, name = core.Core.Name, abbreviation = core.Core.Abbreviation, priority = core.Core.Priority, debrid = True)
		self.mService = core.Core()
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False):
		if self.mService.accountValid():
			return self.mService.add(link = link)
		return None

	def services(self):
		try:
			if self.mServices == None and self.mService.accountValid():
				self.mServices = self.mService.servicesList(onlyEnabled = True)
		except: pass
		return self.mServices
