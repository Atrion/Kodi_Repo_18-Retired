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
from resources.lib.extensions import convert
from resources.lib.extensions import cache
from resources.lib.extensions import tools

class Core(base.Core):

	Id = 'easynews'
	Name = 'EasyNews'
	Abbreviation = 'E'

	Cookie = 'chickenlicker=%s%%3A%s'

	LinkLogin = 'https://account.easynews.com/index.php'
	LinkAccount = 'https://account.easynews.com/editinfo.php'
	LinkUsage = 'https://account.easynews.com/usageview.php'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		base.Core.__init__(self, Core.Id, Core.Name)

		self.mResult = None
		self.mSuccess = False
		self.mError = None
		self.mCookie = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _request(self, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None):
		import urllib
		from resources.lib.modules import client

		self.mResult = None
		self.mSuccess = True
		self.mError = None

		if not httpTimeout: httpTimeout = 30

		def login():
			data = urllib.urlencode({'username': self.accountUsername(), 'password': self.accountPassword(), 'submit': 'submit'})
			self.mCookie = client.request(Core.LinkLogin, post = data, output = 'cookie', close = False)

		try:
			if parameters: parameters = urllib.urlencode(parameters)

			if self.mCookie == None: login()
			if not self.mCookie:
				self.mSuccess = False
				self.mError = 'Login Error'
				return self.mResult

			self.mResult = client.request(link, post = parameters, cookie = self.mCookie, headers = httpHeaders, timeout = httpTimeout, close = True)

			if 'value="Login"' in self.mResult: login()
			if not self.mCookie:
				self.mSuccess = False
				self.mError = 'Login Error'
				return self.mResult

			self.mResult = client.request(link, post = parameters, cookie = self.mCookie, headers = httpHeaders, timeout = httpTimeout, close = True)

			self.mSuccess = self.mCookie and not 'value="Login"' in self.mResult
			if not self.mSuccess: self.mError = 'Login Error'
		except:
			toosl.Logger.error()
			self.mSuccess = False
			self.mError = 'Unknown Error'
		return self.mResult

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.easynews', raw = True)
		if open: tools.System.openLink(link)
		return link

	@classmethod
	def vpn(self, open = False):
		link = tools.Settings.getString('link.easynews.vpn', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.easynews.enabled')

	def accountValid(self):
		return not self.accountUsername() == '' and not self.accountPassword() == ''

	def accountUsername(self):
		return tools.Settings.getString('accounts.debrid.easynews.user') if self.accountEnabled() else ''

	def accountPassword(self):
		return tools.Settings.getString('accounts.debrid.easynews.pass') if self.accountEnabled() else ''

	def accountCookie(self):
		return Core.Cookie % (self.accountUsername(), self.accountPassword())

	def accountVerify(self):
		return not self.account(cached = False, minimal = True) == None

	def account(self, cached = True, minimal = False):
		account = None
		try:
			if self.accountValid():
				import datetime
				from resources.lib.externals.beautifulsoup import BeautifulSoup

				if cached: accountHtml = cache.Cache().cacheShort(self._request, Core.LinkAccount)
				else: accountHtml = cache.Cache().cacheClear(self._request, Core.LinkAccount)

				if accountHtml == None or accountHtml == '': raise Exception()

				accountHtml = BeautifulSoup(accountHtml)
				accountHtml = accountHtml.find_all('form', id = 'accountForm')[0]
				accountHtml = accountHtml.find_all('table', recursive = False)[0]
				accountHtml = accountHtml.find_all('tr', recursive = False)

				accountUsername = accountHtml[0].find_all('td', recursive = False)[1].getText()
				accountType = accountHtml[1].find_all('td', recursive = False)[2].getText()
				accountStatus = accountHtml[3].find_all('td', recursive = False)[2].getText()

				accountExpiration = accountHtml[2].find_all('td', recursive = False)[2].getText()
				accountTimestamp = convert.ConverterTime(accountExpiration, format = convert.ConverterTime.FormatDate).timestamp()
				accountExpiration = datetime.datetime.fromtimestamp(accountTimestamp)

				account = {
					'user' : accountUsername,
					'type' : accountType,
					'status' : accountStatus,
			 		'expiration' : {
						'timestamp' : accountTimestamp,
						'date' : accountExpiration.strftime('%Y-%m-%d'),
						'remaining' : (accountExpiration - datetime.datetime.today()).days,
					}
				}

				if not minimal:
					if cached: usageHtml = cache.Cache().cacheShort(self._request, Core.LinkUsage)
					else: usageHtml = cache.Cache().cacheClear(self._request, Core.LinkUsage)

					if usageHtml == None or usageHtml == '': raise Exception()

					usageHtml = BeautifulSoup(usageHtml)
					usageHtml = usageHtml.find_all('div', class_ = 'table-responsive')[0]
					usageHtml = usageHtml.find_all('table', recursive = False)[0]
					usageHtml = usageHtml.find_all('tr', recursive = False)

					usageTotal = usageHtml[0].find_all('td', recursive = False)[1].getText()
					index = usageTotal.find('(')
					if index >= 0: usageTotal = int(usageTotal[index + 1 : usageTotal.find(' ', index)].replace(',', '').strip())
					else: usageTotal = 0

					usageConsumed = usageHtml[1].find_all('td', recursive = False)[2].getText()
					index = usageConsumed.find('(')
					if index >= 0: usageConsumed = int(usageConsumed[index + 1 : usageConsumed.find(' ', index)].replace(',', '').strip())
					else: usageConsumed = 0

					usageWeb = usageHtml[2].find_all('td', recursive = False)[2].getText()
					index = usageWeb.find('(')
					if index >= 0: usageWeb = int(usageWeb[index + 1 : usageWeb.find(' ', index)].replace(',', '').strip())
					else: usageWeb = 0

					usageNntp = usageHtml[3].find_all('td', recursive = False)[2].getText()
					index = usageNntp.find('(')
					if index >= 0: usageNntp = int(usageNntp[index + 1 : usageNntp.find(' ', index)].replace(',', '').strip())
					else: usageNntp = 0

					usageNntpUnlimited = usageHtml[4].find_all('td', recursive = False)[2].getText()
					index = usageNntpUnlimited.find('(')
					if index >= 0: usageNntpUnlimited = int(usageNntpUnlimited[index + 1 : usageNntpUnlimited.find(' ', index)].replace(',', '').strip())
					else: usageNntpUnlimited = 0

					usageRemaining = usageHtml[5].find_all('td', recursive = False)[2].getText()
					index = usageRemaining.find('(')
					if index >= 0: usageRemaining = int(usageRemaining[index + 1 : usageRemaining.find(' ', index)].replace(',', '').strip())
					else: usageRemaining = 0

					usageLoyalty = usageHtml[6].find_all('td', recursive = False)[2].getText()
					index = usageLoyalty.find('(')
					if index >= 0:
						usageLoyaltyTime = usageLoyalty[:index].strip()
						usageLoyaltyTimestamp = convert.ConverterTime(usageLoyaltyTime, format = convert.ConverterTime.FormatDate).timestamp()
						usageLoyaltyTime = datetime.datetime.fromtimestamp(usageLoyaltyTimestamp)
						usageLoyaltyPoints = float(usageLoyalty[index + 1 : usageLoyalty.find(')', index)].strip())
					else:
						usageLoyaltyTimestamp = 0
						usageLoyaltyTime = None

					usagePrecentageRemaining = usageRemaining / float(usageTotal)
					usagePrecentageConsumed = usageConsumed / float(usageTotal)
					usagePrecentageWeb = usageWeb / float(usageTotal)
					usagePrecentageNntp = usageNntp / float(usageTotal)
					usagePrecentageNntpUnlimited = usageNntpUnlimited / float(usageTotal)

					account.update({
						'loyalty' : {
							'time' : {
								'timestamp' : usageLoyaltyTimestamp,
								'date' : usageLoyaltyTime.strftime('%Y-%m-%d')
							},
							'points' : usageLoyaltyPoints,
						},
						'usage' : {
							'total' : {
								'size' : {
									'bytes' : usageTotal,
									'description' : convert.ConverterSize(float(usageTotal)).stringOptimal(),
								},
							},
							'remaining' : {
								'value' : usagePrecentageRemaining,
								'percentage' : round(usagePrecentageRemaining * 100.0, 1),
								'size' : {
									'bytes' : usageRemaining,
									'description' : convert.ConverterSize(float(usageRemaining)).stringOptimal(),
								},
								'description' : '%.0f%%' % round(usagePrecentageRemaining * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
							},
							'consumed' : {
								'value' : usagePrecentageConsumed,
								'percentage' : round(usagePrecentageConsumed * 100.0, 1),
								'size' : {
									'bytes' : usageConsumed,
									'description' : convert.ConverterSize(usageConsumed).stringOptimal(),
								},
								'description' : '%.0f%%' % round(usagePrecentageConsumed * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								'web' : {
									'value' : usagePrecentageWeb,
									'percentage' : round(usagePrecentageWeb * 100.0, 1),
									'size' : {
										'bytes' : usageWeb,
										'description' : convert.ConverterSize(usageWeb).stringOptimal(),
									},
									'description' : '%.0f%%' % round(usagePrecentageWeb * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								},
								'nntp' : {
									'value' : usagePrecentageNntp,
									'percentage' : round(usagePrecentageNntp * 100.0, 1),
									'size' : {
										'bytes' : usageNntp,
										'description' : convert.ConverterSize(usageNntp).stringOptimal(),
									},
									'description' : '%.0f%%' % round(usagePrecentageNntp * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								},
								'nntpunlimited' : {
									'value' : usagePrecentageNntpUnlimited,
									'percentage' : round(usagePrecentageNntpUnlimited * 100.0, 1),
									'size' : {
										'bytes' : usageNntpUnlimited,
										'description' : convert.ConverterSize(usageNntpUnlimited).stringOptimal(),
									},
									'description' : '%.0f%%' % round(usagePrecentageNntpUnlimited * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								},
							}
						}
					})
		except:
			pass
		return account
