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

	Id = 'alldebrid'
	Name = 'AllDebrid'
	Abbreviation = 'A'
	Priority = 5

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
		link = tools.Settings.getString('link.alldebrid', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.alldebrid.enabled')

	def accountValid(self):
		return not self.accountUsername() == '' and not self.accountPassword() == ''

	def accountUsername(self):
		return tools.Settings.getString('accounts.debrid.alldebrid.user') if self.accountEnabled() else ''

	def accountPassword(self):
		return tools.Settings.getString('accounts.debrid.alldebrid.pass') if self.accountEnabled() else ''

	##############################################################################
	# SERVICES
	##############################################################################

	def servicesList(self, onlyEnabled = False):
		hosts = []
		try:
			if (not onlyEnabled or self.streamingHoster()) and self.accountValid():
				url = 'https://api.alldebrid.com/hosts'
				result = cache.Cache().cacheMedium(client.request, url)
				result = tools.Converter.jsonFrom(result)
				result = result['hosts']
				hosts = []
				for i in result:
					if i['status']:
						hosts.append(i['domain'])
						try: hosts.extend(i['altDomains'])
						except: pass
				return list(set([i.lower() for i in hosts]))
		except:
			tools.Logger.error()
		return hosts

	##############################################################################
	# ADD
	##############################################################################

	def add(self, link):
		try:
			if self.accountValid():
				import urllib
				from resources.lib.modules import client
				loginData = urllib.urlencode({'action': 'login', 'login_login': self.accountUsername(), 'login_password': self.accountPassword()})
				loginLink = 'http://alldebrid.com/register/?%s' % loginData
				cookie = client.request(loginLink, output = 'cookie', close = False)
				url = 'http://www.alldebrid.com/service.php?link=%s' % urllib.quote_plus(link)
				result = client.request(url, cookie = cookie, close = False)
				url = client.parseDOM(result, 'a', ret = 'href', attrs = {'class': 'link_dl'})[0]
				url = client.replaceHTMLCodes(url)
				url = '%s|Cookie=%s' % (url, urllib.quote_plus(cookie))
				return self.addResult(link = url)
		except:
			tools.Logger.error()
		return self.addError()
