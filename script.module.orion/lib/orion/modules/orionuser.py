# -*- coding: utf-8 -*-

"""
	Orion
    https://orionoid.com

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
"""

##############################################################################
# ORIONUSER
##############################################################################
# Class for managing Orion users.
##############################################################################

from orion.modules.orionapi import *
from orion.modules.orioninterface import *
from orion.modules.orionsettings import *

OrionUserInstance = None

class OrionUser:

	PasswordCharacter = '•'

	##############################################################################
	# CONSTANTS
	##############################################################################

	KeyLength = 32
	PackageFree = 'free'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		self.mData = self._settingsUser()

	##############################################################################
	# INSTANCE
	##############################################################################

	@classmethod
	def instance(self):
		global OrionUserInstance
		if OrionUserInstance == None: OrionUserInstance = OrionUser()
		return OrionUserInstance

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	##############################################################################
	# USER
	##############################################################################

	def enabled(self):
		return not self.key() == None

	def valid(self, current = False):
		if current and not OrionSettings.getBoolean('account.valid'): return False
		return not self.status() == None

	def id(self, default = None):
		try: return self.mData['id']
		except: return default

	def key(self, default = None):
		try: key = self.mData['key']
		except: key = self.settingsKey()
		if key == None or key == '': return default
		else: return key

	def email(self, default = None):
		try: return self.mData['email']
		except: return default

	def type(self, default = None):
		try: return self.mData['type']
		except: return default

	def status(self, default = None):
		try: return self.mData['status']
		except: return default

	##############################################################################
	# TIME
	##############################################################################

	def timeAdded(self, default = None):
		try: return self.mData['time']['added']
		except: return default

	def timeUpdated(self, default = None):
		try: return self.mData['time']['updated']
		except: return default

	##############################################################################
	# SUBSCRIPTION
	##############################################################################

	def subscriptionPackageId(self, default = None):
		try: return self.mData['subscription']['package']['id']
		except: return default

	def subscriptionPackageType(self, default = None):
		try: return self.mData['subscription']['package']['type']
		except: return default

	def subscriptionPackageFree(self):
		type = self.subscriptionPackageType()
		return type == None or type == OrionUser.PackageFree

	def subscriptionPackagePremium(self):
		return not self.subscriptionPackageFree()

	def subscriptionPackageEnabled(self, default = None):
		try: return self.mData['subscription']['package']['enabled']
		except: return default

	def subscriptionPackageInternal(self, default = None):
		try: return self.mData['subscription']['package']['internal']
		except: return default

	def subscriptionPackagePopular(self, default = None):
		try: return self.mData['subscription']['package']['popular']
		except: return default

	def subscriptionPackageName(self, default = None):
		try: return self.mData['subscription']['package']['name']
		except: return default

	def subscriptionPackageDescription(self, default = None):
		try: return self.mData['subscription']['package']['description']
		except: return default

	def subscriptionPackageLimit(self, default = None):
		try:
			result = self.mData['subscription']['package']['limit']
			if result == None: return default
			else: return result
		except: return default

	def subscriptionPackageDuration(self, default = None):
		try: return self.mData['subscription']['package']['duration']
		except: return default

	def subscriptionPackagePrice(self, default = None):
		try: return self.mData['subscription']['package']['price']
		except: return default

	def subscriptionPackageGatewayId(self, default = None):
		try: return self.mData['subscription']['package']['gateway']['id']
		except: return default

	def subscriptionPackageGatewayName(self, default = None):
		try: return self.mData['subscription']['package']['gateway']['name']
		except: return default

	def subscriptionPackageGatewayDescription(self, default = None):
		try: return self.mData['subscription']['package']['gateway']['description']
		except: return default

	def subscriptionTimeStarted(self, default = None):
		try: return self.mData['subscription']['time']['started']
		except: return default

	def subscriptionTimeExpiration(self, default = None):
		try: return self.mData['subscription']['time']['expiration']
		except: return default

	def subscriptionTimeExpiration(self, default = None):
		try: return self.mData['subscription']['time']['expiration']
		except: return default

	##############################################################################
	# REQUESTS
	##############################################################################

	def requestsTotalCount(self, default = None):
		try: return self.mData['requests']['total']['count']
		except: return default

	def requestsTotalLinks(self, default = None):
		try: return self.mData['requests']['total']['links']
		except: return default

	def requestsDailyLimit(self, default = None):
		try:
			if not self.mData['requests']['daily']['limit']: return default
			return self.mData['requests']['daily']['limit']
		except: return default

	def requestsDailyUsed(self, default = None, percent = False):
		try:
			if not self.mData['requests']['daily']['used']: return default
			if percent: return self.mData['requests']['daily']['used'] / float(self.requestsDailyLimit(0))
			else: return self.mData['requests']['daily']['used']
		except: return default

	def requestsDailyRemaining(self, default = None, percent = False):
		try:
			if not self.mData['requests']['daily']['remaining']: return default
			if percent: return self.mData['requests']['daily']['remaining'] / float(self.requestsDailyLimit(0))
			else: return self.mData['requests']['daily']['remaining']
		except: return default

	##############################################################################
	# SETTINGS
	##############################################################################

	@classmethod
	def settingsKey(self):
		return OrionSettings.getString('account.key')

	@classmethod
	def settingsKeySet(self, key):
		key = key.upper()
		try: self.instance().mData['key'] = key # If a new API key is set, update mData so that OrionApi retreives the new key.
		except: pass
		return OrionSettings.set('account.key', key)

	@classmethod
	def _settingsUser(self):
		return OrionSettings.getObject('internal.api.user')

	@classmethod
	def _settingsUserSet(self, data):
		OrionSettings.set('internal.api.user', data)

	def _settingsUpdate(self, valid):
		self._settingsUserSet(self.mData)
		OrionSettings.set('account.valid', valid)
		OrionSettings.set('account.label.api', '' if self.key('') == '' else (OrionUser.PasswordCharacter * OrionUser.KeyLength))
		OrionSettings.set('account.label.status', self.status().capitalize() if valid else OrionTools.translate(32033))
		if valid:
			OrionSettings.set('account.label.email', self.email())
			packageName = self.subscriptionPackageName()
			packageLimit = self.subscriptionPackageLimit(OrionTools.translate(32030))
			OrionSettings.set('account.label.package', packageName + ('' if packageName == packageLimit else ' (' + str(packageLimit) + ')'))
			OrionSettings.set('account.label.time', OrionTools.timeDays(timeTo = self.subscriptionTimeExpiration(0), format = True))
			OrionSettings.set('account.label.limit', str(OrionTools.round(100 * self.requestsDailyUsed(0, True), 0)) + '% (' + str(self.requestsDailyUsed(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsDailyLimit(OrionTools.translate(32030))) + ')')
		else:
			OrionSettings.set('account.label.email', '')
			OrionSettings.set('account.label.package', '')
			OrionSettings.set('account.label.time', '')
			OrionSettings.set('account.label.limit', '')

	##############################################################################
	# ANONYMOUS
	##############################################################################

	@classmethod
	def anonymous(self, interface = True):
		api = OrionApi()
		if api.userAnonymous():
			data = api.data()
			if data and 'key' in data and not data['key'] == None and not data['key'] == '':
				key = data['key']
				if interface:
					from orion.modules.orionnavigator import OrionNavigator
					OrionNavigator.settingsAccountLogin(key = key, settings = False)
				return key
		return None

	##############################################################################
	# LOGIN
	##############################################################################

	@classmethod
	def login(self, email, password):
		api = OrionApi()
		if api.userLogin(email = email, password = OrionTools.hash(password)):
			data = api.data()
			if data and 'key' in data and not data['key'] == None and not data['key'] == '':
				return data['key']
		return None

	##############################################################################
	# UPDATE
	##############################################################################

	def update(self, disable = False):
		try:
			if disable:
				self.mData = None
				self._settingsUpdate(False)
				return False
			else:
				api = OrionApi()
				result = api.userRetrieve()
				if not result:
					self._settingsUpdate(False)
					return False
				self.mData = api.data()
				self._settingsUpdate(True)
				return True
		except:
			self._settingsUpdate(False)
			OrionTools.error()
		return False

	##############################################################################
	# DIALOG
	##############################################################################

	def dialog(self):
		if self.valid():
			OrionInterface.dialogInformation(title = 32017, items = [
				{
					'title' : 32019,
					'items' :
					[
						{'title' : 32014, 'value' : self.status('').capitalize()},
						{'title' : 32020, 'value' : self.email('')},
						{'title' : 32021, 'value' : OrionTools.timeFormat(self.timeAdded(''), format = OrionTools.FormatDate)},
					],
				},
				{
					'title' : 32022,
					'items' :
					[
						{'title' : 32023, 'value' : self.subscriptionPackageName('')},
						{'title' : 32026, 'value' : str(self.subscriptionPackageLimit(OrionTools.translate(32030)))},
						{'title' : 32029, 'value' : OrionTools.timeDays(timeTo = self.subscriptionTimeExpiration(0), format = True)},
						{'title' : 32024, 'value' : OrionTools.timeFormat(self.subscriptionTimeStarted(''), format = OrionTools.FormatDate)},
						{'title' : 32025, 'value' : OrionTools.timeFormat(self.subscriptionTimeExpiration(''), format = OrionTools.FormatDate)},
					],
				},
				{
					'title' : 32031,
					'items' :
					[
						{'title' : 32027, 'value' : str(self.requestsTotalLinks(0))},
						{'title' : 32026, 'value' : str(self.requestsDailyLimit(OrionTools.translate(32030)))},
						{'title' : 32028, 'value' : str(OrionTools.round(100 * self.requestsDailyUsed(0, True), 0)) + '% (' + str(self.requestsDailyUsed(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsDailyLimit(OrionTools.translate(32030))) + ')'},
						{'title' : 32029, 'value' : str(OrionTools.round(100 * self.requestsDailyRemaining(1, True), 0)) + '% (' + str(self.requestsDailyRemaining(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsDailyLimit(OrionTools.translate(32030))) + ')'},
					],
				},
			])
		else:
			if OrionInterface.dialogOption(title = 32017, message = 33001):
				OrionSettings.launch(category = OrionSettings.CategoryAccount)
