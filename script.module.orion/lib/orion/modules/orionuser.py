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

	##############################################################################
	# CONSTANTS
	##############################################################################

	StatusUnknown = 'unknown'
	StatusRegistered = 'registered'
	StatusActive = 'active'
	StatusVerified = 'verified'
	StatusSuspended = 'suspended'
	StatusDeleted = 'deleted'

	PackageAnonymous = 'anonymous'
	PackageFree = 'free'

	LinksAnonymous = 50
	LinksFree = 100

	# Add 1 day because none-full days are not counted in the notification.
	# Order is important.
	SubscriptionIntervals = [
		172800, # 2 Days
		345600, # 4 Days
		691200, # 8 Days
	]

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

	def empty(self):
		return not self.mData

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

	def username(self, default = None):
		try: return self.mData['username']
		except: return default

	def email(self, default = None):
		try: return self.mData['email']
		except: return default

	def type(self, default = None):
		try: return self.mData['type']
		except: return default

	def status(self, default = None, verified = False):
		try: return OrionUser.StatusActive if (verified and self.verified()) else self.mData['status']
		except: return default

	def verified(self, default = False):
		try: return self.mData['status'] == OrionUser.StatusVerified
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

	def subscriptionPackageAnonymous(self):
		type = self.subscriptionPackageType()
		return type == None or type == OrionUser.PackageAnonymous

	def subscriptionPackageFree(self, anonymous = True):
		type = self.subscriptionPackageType()
		return type == None or type == OrionUser.PackageFree or (anonymous and type == OrionUser.PackageAnonymous)

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

	def subscriptionPackageLimitDuration(self, default = None):
		try: return self.mData['subscription']['package']['limit']['duration']
		except: return default

	def subscriptionPackageLimitStreams(self, default = None):
		try:
			result = self.mData['subscription']['package']['limit']['streams']
			if result == None: return default
			else: return result
		except: return default

	def subscriptionPackageLimitHashes(self, default = None):
		try:
			result = self.mData['subscription']['package']['limit']['hashes']
			if result == None: return default
			else: return result
		except: return default

	def subscriptionPackageLimitContainers(self, default = None):
		try:
			result = self.mData['subscription']['package']['limit']['containers']
			if result == None: return default
			else: return result
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

	def subscriptionCheck(self):
		if self.subscriptionPackagePremium():
			expiration = self.subscriptionTimeExpiration()
			if expiration:
				remaining = expiration - OrionTools.timestamp()
				if remaining > 0:
					notification = False
					settings = OrionSettings.getInteger('internal.api.subscription')
					if settings == None or remaining > OrionUser.SubscriptionIntervals[-1]:
						settings = 0
					for interval in OrionUser.SubscriptionIntervals:
						if remaining < interval and (settings == 0 or interval < settings):
							settings = interval
							notification = True
					OrionSettings.set('internal.api.subscription', settings)
					if notification:
						message = OrionTools.translate(33031) % OrionTools.timeDays(timeTo = self.subscriptionTimeExpiration(0), format = True)
						OrionInterface.dialogNotification(title = 32035, message = message, icon = OrionInterface.IconWarning, time = 10000)

	##############################################################################
	# ADDON
	##############################################################################

	def addonKodi(self, default = False):
		try: return self.mData['addon']['kodi']
		except: return default

	def addonWako(self, default = False):
		try: return self.mData['addon']['wako']
		except: return default

	##############################################################################
	# REQUESTS
	##############################################################################

	def requestsCount(self, default = None):
		try: return self.mData['requests']['count']
		except: return default

	def requestsStreamsTotal(self, default = None):
		try: return self.mData['requests']['streams']['total']
		except: return default

	def requestsStreamsDailyLimit(self, default = None):
		try:
			if not self.mData['requests']['streams']['daily']['limit']: return default
			return self.mData['requests']['streams']['daily']['limit']
		except: return default

	def requestsStreamsDailyUsed(self, default = None, percent = False):
		try:
			if not self.mData['requests']['streams']['daily']['used']: return default
			if percent: return self.mData['requests']['streams']['daily']['used'] / float(self.requestsStreamsDailyLimit(0))
			else: return self.mData['requests']['streams']['daily']['used']
		except: return default

	def requestsStreamsDailyRemaining(self, default = None, percent = False):
		try:
			if not self.mData['requests']['streams']['daily']['remaining']: return default
			if percent: return self.mData['requests']['streams']['daily']['remaining'] / float(self.requestsStreamsDailyLimit(0))
			else: return self.mData['requests']['streams']['daily']['remaining']
		except: return default

	def requestsHashesTotal(self, default = None):
		try: return self.mData['requests']['hashes']['total']
		except: return default

	def requestsHashesDailyLimit(self, default = None):
		try:
			if not self.mData['requests']['hashes']['daily']['limit']: return default
			return self.mData['requests']['hashes']['daily']['limit']
		except: return default

	def requestsHashesDailyUsed(self, default = None, percent = False):
		try:
			if not self.mData['requests']['hashes']['daily']['used']: return default
			if percent: return self.mData['requests']['hashes']['daily']['used'] / float(self.requestsHashesDailyLimit(0))
			else: return self.mData['requests']['hashes']['daily']['used']
		except: return default

	def requestsHashesDailyRemaining(self, default = None, percent = False):
		try:
			if not self.mData['requests']['hashes']['daily']['remaining']: return default
			if percent: return self.mData['requests']['hashes']['daily']['remaining'] / float(self.requestsHashesDailyLimit(0))
			else: return self.mData['requests']['hashes']['daily']['remaining']
		except: return default

	def requestsContainersTotal(self, default = None):
		try: return self.mData['requests']['containers']['total']
		except: return default

	def requestsContainersDailyLimit(self, default = None):
		try:
			if not self.mData['requests']['containers']['daily']['limit']: return default
			return self.mData['requests']['containers']['daily']['limit']
		except: return default

	def requestsContainersDailyUsed(self, default = None, percent = False):
		try:
			if not self.mData['requests']['containers']['daily']['used']: return default
			if percent: return self.mData['requests']['containers']['daily']['used'] / float(self.requestsContainersDailyLimit(0))
			else: return self.mData['requests']['containers']['daily']['used']
		except: return default

	def requestsContainersDailyRemaining(self, default = None, percent = False):
		try:
			if not self.mData['requests']['containers']['daily']['remaining']: return default
			if percent: return self.mData['requests']['containers']['daily']['remaining'] / float(self.requestsContainersDailyLimit(0))
			else: return self.mData['requests']['containers']['daily']['remaining']
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
		OrionSettings.set('account.valid', valid, backup = False)
		OrionSettings.set('account.label.api', OrionTools.translate(32247) if (self.key('') == '' or not valid) else OrionTools.translate(32169), backup = False)
		OrionSettings.set('account.label.status', self.status(verified = True).capitalize() if valid else OrionTools.translate(32033), backup = False)
		if valid:
			# NB: Strings must be cast with str(...), otherwise getting UnicodeDecodeError in Windows.
			OrionSettings.set('account.label.verified', OrionTools.translate(32278) if self.verified() else OrionTools.translate(32279), backup = False)
			OrionSettings.set('account.label.username', self.username(), backup = False)
			OrionSettings.set('account.label.email', self.email(), backup = False)
			packageName = self.subscriptionPackageName()
			packageLimitStreams = self.subscriptionPackageLimitStreams(OrionTools.translate(32030))
			packageLimitHashes = self.subscriptionPackageLimitHashes(OrionTools.translate(32030))
			packageLimitContainers = self.subscriptionPackageLimitContainers(OrionTools.translate(32030))
			OrionSettings.set('account.label.package', str(packageName), backup = False)
			OrionSettings.set('account.label.time', OrionTools.timeDays(timeTo = self.subscriptionTimeExpiration(0), format = True), backup = False)
			OrionSettings.set('account.label.limit.streams', str(OrionTools.round(100 * self.requestsStreamsDailyUsed(0, True), 0)) + '% (' + str(self.requestsStreamsDailyUsed(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsStreamsDailyLimit(OrionTools.translate(32030))) + ')', backup = False)
			OrionSettings.set('account.label.limit.hashes', str(OrionTools.round(100 * self.requestsHashesDailyUsed(0, True), 0)) + '% (' + str(self.requestsHashesDailyUsed(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsHashesDailyLimit(OrionTools.translate(32030))) + ')', backup = False)
			OrionSettings.set('account.label.limit.containers', str(OrionTools.round(100 * self.requestsContainersDailyUsed(0, True), 0)) + '% (' + str(self.requestsContainersDailyUsed(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsContainersDailyLimit(OrionTools.translate(32030))) + ')', backup = False)
			OrionSettings._backupAutomatic(force = True)
		else:
			OrionSettings.set('account.label.verified', '', backup = False)
			OrionSettings.set('account.label.username', '', backup = False)
			OrionSettings.set('account.label.email', '', backup = False)
			OrionSettings.set('account.label.package', '', backup = False)
			OrionSettings.set('account.label.time', '', backup = False)
			OrionSettings.set('account.label.limit.streams', '', backup = False)
			OrionSettings.set('account.label.limit.hashes', '', backup = False)
			OrionSettings.set('account.label.limit.containers', '', backup = False)
			# OrionSettings._backupAutomatic(force = True) # Do not backup settings, otherwise creates infinite loop.

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
	def login(self, user, password):
		api = OrionApi()
		if api.userLogin(user = user, password = OrionTools.hash(password)):
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
				premium = self.subscriptionPackagePremium()
				self.mData = api.data()
				if premium and self.subscriptionPackageFree():
					OrionInterface.dialogNotification(title = 32035, message = 33032, icon = OrionInterface.IconWarning, time = 10000)
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
						{'title' : 32014, 'value' : self.status('', verified = True).capitalize()},
						{'title' : 32277, 'value' : OrionTools.translate(32278) if self.verified() else OrionTools.translate(32279)},
						{'title' : 32276, 'value' : self.username('')},
						{'title' : 32020, 'value' : self.email('')},
						{'title' : 32021, 'value' : OrionTools.timeFormat(self.timeAdded(), format = OrionTools.FormatDate)},
					],
				},
				{
					'title' : 32022,
					'items' :
					[
						{'title' : 32023, 'value' : self.subscriptionPackageName('')},
						{'title' : 32031, 'value' : str(self.subscriptionPackageLimitStreams(OrionTools.translate(32030)))},
						{'title' : 32198, 'value' : str(self.subscriptionPackageLimitHashes(OrionTools.translate(32030)))},
						{'title' : 32230, 'value' : str(self.subscriptionPackageLimitContainers(OrionTools.translate(32030)))},
						{'title' : 32029, 'value' : OrionTools.timeDays(timeTo = self.subscriptionTimeExpiration(0), format = True)},
						{'title' : 32024, 'value' : OrionTools.timeFormat(self.subscriptionTimeStarted(), format = OrionTools.FormatDate)},
						{'title' : 32025, 'value' : OrionTools.timeFormat(self.subscriptionTimeExpiration(), format = OrionTools.FormatDate, default = 32120)},
					],
				},
				{
					'title' : 32225,
					'items' :
					[
						{'title' : 32027, 'value' : str(self.requestsStreamsTotal(0))},
						{'title' : 32026, 'value' : str(self.requestsStreamsDailyLimit(OrionTools.translate(32030)))},
						{'title' : 32028, 'value' : str(OrionTools.round(100 * self.requestsStreamsDailyUsed(0, True), 0)) + '% (' + str(self.requestsStreamsDailyUsed(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsStreamsDailyLimit(OrionTools.translate(32030))) + ')'},
						{'title' : 32029, 'value' : str(OrionTools.round(100 * self.requestsStreamsDailyRemaining(1, True), 0)) + '% (' + str(self.requestsStreamsDailyRemaining(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsStreamsDailyLimit(OrionTools.translate(32030))) + ')'},
					],
				},
				{
					'title' : 32226,
					'items' :
					[
						{'title' : 32027, 'value' : str(self.requestsHashesTotal(0))},
						{'title' : 32026, 'value' : str(self.requestsHashesDailyLimit(OrionTools.translate(32030)))},
						{'title' : 32028, 'value' : str(OrionTools.round(100 * self.requestsHashesDailyUsed(0, True), 0)) + '% (' + str(self.requestsHashesDailyUsed(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsHashesDailyLimit(OrionTools.translate(32030))) + ')'},
						{'title' : 32029, 'value' : str(OrionTools.round(100 * self.requestsHashesDailyRemaining(1, True), 0)) + '% (' + str(self.requestsHashesDailyRemaining(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsHashesDailyLimit(OrionTools.translate(32030))) + ')'},
					],
				},
				{
					'title' : 32231,
					'items' :
					[
						{'title' : 32027, 'value' : str(self.requestsContainersTotal(0))},
						{'title' : 32026, 'value' : str(self.requestsContainersDailyLimit(OrionTools.translate(32030)))},
						{'title' : 32028, 'value' : str(OrionTools.round(100 * self.requestsContainersDailyUsed(0, True), 0)) + '% (' + str(self.requestsContainersDailyUsed(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsContainersDailyLimit(OrionTools.translate(32030))) + ')'},
						{'title' : 32029, 'value' : str(OrionTools.round(100 * self.requestsContainersDailyRemaining(1, True), 0)) + '% (' + str(self.requestsContainersDailyRemaining(0)) + ' ' + OrionTools.translate(32032) + ' ' + str(self.requestsContainersDailyLimit(OrionTools.translate(32030))) + ')'},
					],
				},
			])
		else:
			if OrionInterface.dialogOption(title = 32017, message = 33001):
				OrionSettings.launch(category = OrionSettings.CategoryAccount)
