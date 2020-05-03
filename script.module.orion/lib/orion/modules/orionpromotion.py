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
# ORIONPROMOTION
##############################################################################
# Class for managing Orion promotions.
##############################################################################

from orion.modules.orionuser import *

class OrionPromotion:

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, data = None):
		self.mData = data

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	##############################################################################
	# ID
	##############################################################################

	def id(self, default = None):
		try: return self.mData['id']
		except: return default

	##############################################################################
	# TIME
	##############################################################################

	def timeStart(self, default = None):
		try: return self.mData['time']['start']
		except: return default

	def timeEnd(self, default = None):
		try: return self.mData['time']['end']
		except: return default

	##############################################################################
	# MULTIPLIER
	##############################################################################

	def multiplierStreams(self, default = None):
		return self.freeStreams(default = default) if OrionUser.instance().subscriptionPackageFree() else self.premiumStreams(default = default)

	def multiplierHashes(self, default = None):
		return self.freeHashes(default = default) if OrionUser.instance().subscriptionPackageFree() else self.premiumHashes(default = default)

	def multiplierContainers(self, default = None):
		return self.freeContainers(default = default) if OrionUser.instance().subscriptionPackageFree() else self.premiumContainers(default = default)

	##############################################################################
	# FREE MULTIPLIER
	##############################################################################

	def freeStreams(self, default = None):
		try: return self.mData['free']['streams']
		except: return default

	def freeHashes(self, default = None):
		try: return self.mData['free']['hashes']
		except: return default

	def freeContainers(self, default = None):
		try: return self.mData['free']['containers']
		except: return default

	##############################################################################
	# PREMIUM MULTIPLIER
	##############################################################################

	def premiumStreams(self, default = None):
		try: return self.mData['premium']['streams']
		except: return default

	def premiumHashes(self, default = None):
		try: return self.mData['premium']['hashes']
		except: return default

	def premiumContainers(self, default = None):
		try: return self.mData['premium']['containers']
		except: return default

	##############################################################################
	# DIALOG
	##############################################################################

	@classmethod
	def dialog(self):
		from orion.modules.orionnotification import OrionNotification
		OrionInterface.loaderShow()
		api = OrionApi()
		result = api.promotionRetrieve()
		OrionInterface.loaderHide()
		if not result or not api.data() or len(api.data()) == 0:
			OrionInterface.dialogNotification(title = 32315, message = 33069, icon = OrionInterface.IconInformation)
			return False
		data = api.data()[0]
		dataNew = {}
		if 'notification' in data: dataNew = data['notification']
		else: dataNew['time'] = {'added' : data['time']['start']}
		dataNew['promotion'] = data
		notification = OrionNotification(data = dataNew)
		notification.dialog(title = 32315)
		return True

	def dialogNotification(self):
		multiplier = max(self.multiplierStreams(0), self.multiplierHashes(0), self.multiplierContainers(0))
		OrionInterface.dialogNotification(title = 32313, message = OrionTools.translate(33068) % multiplier, icon = OrionInterface.IconInformation, time = 10000)

	@classmethod
	def dialogNew(self):
		user = OrionUser.instance()
		if user and user.enabled() and OrionSettings.getGeneralNotificationsNews():
			api = OrionApi()
			result = api.promotionRetrieve()
			if not result or not api.data() or len(api.data()) == 0: return False
			promotion = OrionPromotion(data = api.data()[0])
			last = OrionSettings.getString('internal.api.promotion')
			if not last == promotion.id():
				promotion.dialogNotification()
				OrionSettings.set('internal.api.promotion', promotion.id())
				return True
		return False
