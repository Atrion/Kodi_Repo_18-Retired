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
from resources.lib.debrid.offcloud import core
from resources.lib.debrid.offcloud import interface

class Handle(base.Handle):

	def __init__(self):
		base.Handle.__init__(self, id = core.Core.Id, name = core.Core.Name, abbreviation = core.Core.Abbreviation, priority = core.Core.Priority, debrid = True)
		self.mService = core.Core()
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True, select = False, cloud = False):
		try: title = item['metadata'].title(extended = True, prefix = True, pack = True)
		except: title = item['title']
		try: pack = item['metadata'].pack()
		except: pack = False
		try: cached = item['cache'][self.id()]
		except: cached = False
		try:
			season = item['information']['season']
			episode = item['information']['episode']
		except:
			season = None
			episode = None

		if self.mService.accountValid():
			if select: pack = True # Even non-season-pack archives should be selectable.
			return interface.Interface().add(link = link, title = title, season = season, episode = episode, pack = pack, close = close, source = item['source'], cached = cached, select = select, cloud = cloud)
		return None

	def services(self):
		try:
			if self.mServices == None and self.mService.accountValid():
				self.mServices = self.mService.servicesList(onlyEnabled = True)
		except: pass
		return self.mServices

	def supported(self, item, cloud = False):
		if isinstance(item, dict) and 'source' in item:
			if item['source'] in [core.Core.ModeTorrent, core.Core.ModeUsenet]:
				return True
		return base.Handle.supported(self, item)
