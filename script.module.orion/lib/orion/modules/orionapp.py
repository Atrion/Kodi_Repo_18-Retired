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
# ORIONAPP
##############################################################################
# Class for managing Orion custom apps.
##############################################################################

import threading
from orion.modules.orionapi import *
from orion.modules.orioninterface import *
from orion.modules.orionsettings import *

OrionAppInstance = None
OrionAppInstances = []

class OrionApp:

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, id = None, key = None, data = {}, update = True):
		if not data == None: self.mData = data
		if not id == None: self.mData['id'] = id
		if not key == None: self.mData['key'] = key
		if update and not key == None or not id == None:
			self.refresh()

	def __lt__(self, other):
         return self.name() < other.name()

	##############################################################################
	# INSTANCE
	##############################################################################

	@classmethod
	def instance(self, key = None):
		global OrionAppInstance
		global OrionAppInstances

		if key == None:
			return OrionAppInstance

		for app in OrionAppInstances:
			if app.key() == key:
				OrionAppInstance = app
				return OrionAppInstance

		# This can cause a recursive call: OrionApp.instance() -> OrionApp.update() -> OrionApi->retrieve() -> OrionApp.instance()
		# Do not update if the instance is still None. Not neccessary, because the API only needs the key and not the other details.
		app = OrionApp(key = key, update = not OrionAppInstance == None)
		OrionAppInstance = app
		OrionAppInstances.append(app)
		return OrionAppInstance

	@classmethod
	def instances(self, update = False, wait = False, orion = True, sort = False):
		apps = []
		try:
			if update:
				thread = threading.Thread(target = self.updateAll)
				thread.start()
				if wait: thread.join()
			current = self._settingsGet()
			if not current == None and len(current) > 0:
				for data in current:
					apps.append(OrionApp(data = data))
			if not orion: apps = [app for app in apps if not app.name() == OrionTools.addonName()]
			if sort: apps.sort()
		except:
			OrionTool.serror()
		return apps

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	##############################################################################
	# APP
	##############################################################################

	def valid(self, default = None):
		return not self.status() == None

	def id(self, default = None):
		try: return self.mData['id']
		except: return default

	def idSet(self, id):
		self.mData['id'] = id

	def key(self, default = None):
		try: return self.mData['key']
		except: return default

	def keySet(self, key):
		self.mData['key'] = key

	def type(self, default = None):
		try: return self.mData['type']
		except: return default

	def status(self, default = None):
		try: return self.mData['status']
		except: return default

	def name(self, default = None):
		try: return self.mData['name']
		except: return default

	def description(self, default = None):
		try: return self.mData['description']
		except: return default

	def link(self, default = None):
		try: return self.mData['link']
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
	# POPULARITY
	##############################################################################

	def popularityCount(self, default = None):
		try: return self.mData['popularity']['percent']
		except: return default

	def popularityPercent(self, default = None):
		try: return self.mData['popularity']['percent']
		except: return default

	##############################################################################
	# SETTINGS
	##############################################################################

	@classmethod
	def _settingsGet(self):
		return OrionSettings.getList('internal.api.apps')

	@classmethod
	def _settingsSet(self, apps):
		return OrionSettings.set('internal.api.apps', apps)

	def _settingsLoad(self):
		try:
			apps = self._settingsGet()
			id = self.id()
			key = self.key()
			if not id == None:
				for app in apps:
					if app['id'] == id:
						self.mData.update(app)
						return True
			elif not key == None:
				for app in apps:
					if app['key'] == key:
						self.mData.update(app)
						return True
		except:
			OrionTools.error()
		return False

	def _settingsSave(self):
		try:
			apps = self._settingsGet()
			index = None
			id = self.id()
			key = self.key()
			if not id == None:
				for i in range(len(apps)):
					if apps[i]['id'] == id:
						index = i
						break
			elif not key == None:
				for i in range(len(apps)):
					if apps[i]['key'] == key:
						index = i
						break
			if index == None: apps.append(self.mData)
			else: apps[index].update(self.mData)
			self._settingsSet(apps)
			return True
		except:
			OrionTools.error()
		return False

	##############################################################################
	# UPDATE
	##############################################################################

	def refresh(self):
		if not self._settingsLoad():
			if self.update():
				self._settingsSave()
				OrionSettings.externalInsert(self, check = True)

	def update(self):
		try:
			api = OrionApi()
			if self.id(): result = api.appRetrieve(id = self.id())
			else: result = api.appRetrieve(key = self.key())
			if not result: return False
			data = api.data()
			if data:
				self.mData.update(data)
				self._settingsSave()
				return True
			else:
				return False
		except:
			OrionTools.error()
		return False

	@classmethod
	def updateAll(self):
		apps = []
		try:
			appsOld = self._settingsGet()
			if not appsOld == None and len(appsOld) > 0:
				id = [app['id'] for app in appsOld]
				api = OrionApi()
				if api.appRetrieve(id = id):
					appsApi = api.data()
					for data in appsApi:
						app = OrionApp(data = data)
						if app.key() == None:
							for appOld in appsOld:
								if app.id() == appOld['id']:
									app.keySet(appOld['key'])
									break
						apps.append(app)
					self._settingsSet([app.data() for app in apps])
		except:
			OrionTools.error()
		return apps

	##############################################################################
	# DIALOG
	##############################################################################

	def dialog(self):
		OrionInterface.dialogInformation(title = 32003, items = [
			{
				'title' : 32009,
				'items' :
				[
					{'title' : 32011, 'value' : self.name('')},
					{'title' : 32012, 'value' : self.description('')},
					{'title' : 32007, 'value' : self.link(''), 'link' : True},
				],
			},
			{
				'title' : 32010,
				'items' :
				[
					{'title' : 32013, 'value' : self.type('').capitalize()},
					{'title' : 32014, 'value' : self.status('').capitalize()},
					{'title' : 32015, 'value' : str(OrionTools.round(self.popularityPercent(0) * 100, 0)) + '%'},
					{'title' : 32016, 'value' : OrionTools.timeFormat(self.timeAdded(), format = OrionTools.FormatDate)},
				],
			},
		])
