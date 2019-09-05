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
from resources.lib.extensions import cache
from resources.lib.extensions import tools

class Core(base.Core):

	Id = 'rapidpremium'
	Name = 'RapidPremium'
	Abbreviation = 'M'
	Priority = 4

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		base.Core.__init__(self, Core.Id, Core.Name)

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.rapidpremium', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.rapidpremium.enabled')

	def accountValid(self):
		return not self.accountUsername() == '' and not self.accountApi() == ''

	def accountUsername(self):
		return tools.Settings.getString('accounts.debrid.rapidpremium.user') if self.accountEnabled() else ''

	def accountApi(self):
		return tools.Settings.getString('accounts.debrid.rapidpremium.api') if self.accountEnabled() else ''

	##############################################################################
	# SERVICES
	##############################################################################

	def servicesList(self, onlyEnabled = False):
		hosts = []
		try:
			if (not onlyEnabled or self.streamingHoster()) and self.accountValid():
				url = 'http://premium.rpnet.biz/hoster2.json'
				result = cache.Cache().cacheMedium(client.request, url)
				result = tools.Converter.jsonFrom(result)
				result = result['supported']
				hosts = [i.lower() for i in result]
		except:
			tools.Logger.error()
			pass
		return hosts

	##############################################################################
	# ADD
	##############################################################################

	def add(self, link):
		try:
			if self.accountValid():
				import urllib
				from resources.lib.modules import client
				loginData = urllib.urlencode({'username': self.accountUsername(), 'password': self.accountApi(), 'action': 'generate', 'links': link})
				loginLink = 'http://premium.rpnet.biz/client_api.php?%s' % loginData
				result = client.request(loginLink, close = False)
				result = tools.Converter.jsonFrom(result)
				return self.addResult(link = result['links'][0]['generated'])
		except:
			pass
		return self.addError()
