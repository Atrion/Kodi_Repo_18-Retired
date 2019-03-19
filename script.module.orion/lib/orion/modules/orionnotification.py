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
# ORIONNOTIFICATION
##############################################################################
# Class for managing Orion notifications.
##############################################################################

from orion.modules.orionapi import *
from orion.modules.orioninterface import *
from orion.modules.orionsettings import *
from orion.modules.orionuser import *
from orion.modules.orionpromotion import *

class OrionNotification:

	##############################################################################
	# CONSTANTS
	##############################################################################

	Time = 7889238 # 3 Months

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

	def timeAdded(self, default = None):
		try: return self.mData['time']['added']
		except: return default

	def timeExpiration(self, default = None):
		try: return self.mData['time']['expiration']
		except: return default

	##############################################################################
	# CONTENT
	##############################################################################

	def contentTitle(self, default = None):
		try: return self.mData['content']['title']
		except: return default

	def contentMessage(self, default = None):
		try: return self.mData['content']['message']
		except: return default

	##############################################################################
	# PROMOTION
	##############################################################################

	def promotion(self, default = None):
		try: return OrionPromotion(self.mData['promotion'])
		except: return default

	##############################################################################
	# UPDATE
	##############################################################################

	@classmethod
	def update(self):
		notifications = []
		try:
			api = OrionApi()
			result = api.notificationRetrieve(time = OrionNotification.Time)
			if not result: return notifications
			result = api.data()
			for i in result: notifications.append(OrionNotification(data = i))
		except: pass
		return notifications

	##############################################################################
	# DIALOG
	##############################################################################

	def dialog(self, wait = False):
		promotion = self.promotion()
		message = ''
		message += OrionInterface.font(OrionTools.addonName() + ' ' + OrionTools.translate(32157), bold = True, color = OrionInterface.ColorPrimary, uppercase = True)
		message += OrionInterface.fontNewline()
		message += OrionInterface.font(OrionTools.timeFormat(time = self.timeAdded(), format = OrionTools.FormatDate), bold = True)
		message += OrionInterface.fontNewline() + OrionInterface.fontNewline()
		message += OrionInterface.font(self.contentTitle(), bold = True, color = OrionInterface.ColorPrimary)
		message += OrionInterface.fontNewline() + OrionInterface.fontNewline()
		if promotion:
			offer = ''
			if promotion.limitMultiplier(): offer = str(promotion.limitMultiplier()) + 'x ' + OrionInterface.font(32198)
			message += OrionInterface.font(OrionTools.translate(32197) + ': ', color = OrionInterface.ColorPrimary) + offer + OrionInterface.fontNewline()
			message += OrionInterface.font(OrionTools.translate(32195) + ': ', color = OrionInterface.ColorPrimary) + OrionInterface.font(OrionTools.timeFormat(time = promotion.timeStart(), format = OrionTools.FormatDate) if promotion.timeStart() else 32199) + OrionInterface.fontNewline()
			message += OrionInterface.font(OrionTools.translate(32196) + ': ', color = OrionInterface.ColorPrimary) + OrionInterface.font(OrionTools.timeFormat(time = promotion.timeEnd(), format = OrionTools.FormatDate) if promotion.timeEnd() else 32199)
			message += OrionInterface.fontNewline() + OrionInterface.fontNewline()
		message += self.contentMessage('')
		OrionInterface.dialogPage(title = 32157, message = message, wait = wait)

	@classmethod
	def dialogNew(self):
		user = OrionUser.instance()
		if user and user.enabled() and OrionSettings.getGeneralNotificationsNews():
			api = OrionApi()
			result = api.notificationRetrieve()
			if not result or not api.data(): return False
			notification = OrionNotification(data = api.data())
			last = OrionSettings.getString('internal.api.notification')
			if not last == notification.id():
				notification.dialog()
				OrionSettings.set('internal.api.notification', notification.id())
				return True
		return False
