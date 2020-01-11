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
# OrionServer
##############################################################################
# Class for managing the Orion server.
##############################################################################

from orion.modules.orionapi import *
from orion.modules.orioninterface import *
from orion.modules.orionsettings import *

OrionServerInstance = None

class OrionServer:

	##############################################################################
	# CONSTANTS
	##############################################################################

	StatusDown = 'down'
	StatusUsage = 'usage'
	StatusMaintenance = 'maintenance'
	StatusOperational = 'operational'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, data = None):
		self.mData = data

	##############################################################################
	# INSTANCE
	##############################################################################

	@classmethod
	def instance(self):
		global OrionServerInstance
		if OrionServerInstance == None: OrionServerInstance = OrionServer()
		return OrionServerInstance

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	##############################################################################
	# SERVER
	##############################################################################

	def time(self, default = None):
		try: return self.mData['time']
		except: return default

	def status(self, default = None):
		try: return self.mData['status']
		except: return default

	def message(self, default = None):
		try: return self.mData['message']
		except: return default

	def stats(self, default = None):
		from orion.modules.orionstats import OrionStats
		try: return OrionStats(self.mData['stats'])
		except: return default

	def notification(self, default = None):
		from orion.modules.orionnotification import OrionNotification
		try: return OrionNotification(self.mData['notification'])
		except: return default

	##############################################################################
	# UPDATE
	##############################################################################

	def update(self):
		try:
			api = OrionApi()
			result = api.serverRetrieve()
			if not result: return False
			self.mData = api.data()
			return True
		except:
			OrionTools.error()
		return False

	##############################################################################
	# DIALOG
	##############################################################################

	def dialog(self):
		items = []

		color = None
		status = self.status()
		if status == OrionServer.StatusDown: color = OrionInterface.ColorBad
		elif status == OrionServer.StatusMaintenance: color = OrionInterface.ColorPoor
		elif status == OrionServer.StatusUsage: color = OrionInterface.ColorMedium
		elif status == OrionServer.StatusOperational: color = OrionInterface.ColorGood
		if status: items.append({'title' : 32014, 'value' : OrionInterface.font(status, color = color, capitalcase = True)})

		message = self.message()
		if message: items.append({'title' : 32161, 'value' : message})

		time = self.time()
		if time: items.append({'title' : 32160, 'value' : OrionTools.timeFormat(time, format = OrionTools.FormatDateTime)})

		items = [{'title' : 32010, 'items' : items}]

		stats = self.stats()
		if stats:
			if not stats.countStreams() == None:
				items.append({'title' : 32283, 'items' : [
					{'title' : 32086, 'value' : str(OrionTools.thousands(stats.countStreams()))},
					{'title' : 32230, 'value' : str(OrionTools.thousands(stats.countContainers()))},
					{'title' : 32198, 'value' : str(OrionTools.thousands(stats.countHashes()))},
				]})
			if not stats.usage() == None:
				items.append({'title' : 32162, 'items' : [{'title' : 32163, 'value' : str(OrionTools.round(stats.usage() * 100, 0)) + '%'}]})

		OrionInterface.dialogInformation(title = 32156, items = items)
