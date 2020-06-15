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
# ORIONSETTINGS
##############################################################################
# Class for handling the Kodi addon settings.
##############################################################################

import re
import threading
import xbmcaddon
from orion.modules.oriontools import *
from orion.modules.orioninterface import *
from orion.modules.orionstream import *
from orion.modules.oriondatabase import *

OrionSettingsLock = threading.Lock()
OrionSettingsCache = None
OrionSettingsSilent = False
OrionSettingsBackupLocal = False
OrionSettingsBackupOnline = False

class OrionSettings:

	##############################################################################
	# CONSTANTS
	##############################################################################

	DatabaseSettings = 'settings'
	DatabaseTemp = 'temp'

	ExtensionManual = 'zip'
	ExtensionAutomatic = 'bck'

	ParameterDefault = 'default'
	ParameterValue = 'value'
	ParameterVisible = 'visible'

	CategoryGeneral = 0
	CategoryAccount = 1
	CategoryFilters = 2

	NotificationsDisabled = 0
	NotificationsEssential = 1
	NotificationsAll = 2

	ScrapingExclusive = 0
	ScrapingSequential = 1
	ScrapingParallel = 2

	ExternalStart = '<!-- ORION FILTERS - %s START -->'
	ExternalEnd = '<!-- ORION FILTERS - %s END -->'

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _filtersAttribute(self, attribute, type = None):
		if not type == None and not type == 'universal':
			attribute = attribute.replace('filters.', 'filters.' + type + '.')
		return attribute

	##############################################################################
	# LAUNCH
	##############################################################################

	@classmethod
	def launch(self, category = None, section = None, addon = None):
		OrionTools.execute('Addon.OpenSettings(%s)' % (OrionTools.addonId() if addon is None else addon))
		if OrionTools.kodiVersionNew():
			if not category == None: OrionTools.execute('SetFocus(%i)' % (int(category) - 100))
		else:
			if not category == None: OrionTools.execute('SetFocus(%i)' % (int(category) + 100))
			if not section == None: OrionTools.execute('SetFocus(%i)' % (int(section) + 200))

	##############################################################################
	# PATH
	##############################################################################

	@classmethod
	def pathAddon(self):
		return OrionTools.pathJoin(OrionTools.addonPath(), 'resources', 'settings.xml')

	@classmethod
	def pathProfile(self):
		return OrionTools.pathJoin(OrionTools.addonProfile(), 'settings.xml')

	##############################################################################
	# HELP
	##############################################################################

	@classmethod
	def help(self, type = None):
		help = not self.getBoolean('help.enabled.general')
		data = OrionTools.fileRead(self.pathProfile())
		if OrionTools.kodiVersionNew(): data = re.sub('(id="help.enabled\..*")(.*)(<\/setting>)', '\\1>%s</setting>' % OrionTools.toBoolean(help, string = True), data, flags = re.IGNORECASE)
		else: data = re.sub('(id="help.enabled\..*?" )(.*)(\/>)', '\\1value="%s" />' % OrionTools.toBoolean(help, string = True), data, flags = re.IGNORECASE)
		OrionTools.fileWrite(self.pathProfile(), data)
		self.launch(category = type)

	##############################################################################
	# SILENT
	##############################################################################

	@classmethod
	def silent(self):
		from orion.modules.orionuser import OrionUser
		global OrionSettingsSilent
		return OrionSettingsSilent or not OrionUser.instance().enabled()

	@classmethod
	def silentSet(self, silent = True):
		global OrionSettingsSilent
		OrionSettingsSilent = silent

	@classmethod
	def silentAllow(self, type = None):
		from orion.modules.orionapi import OrionApi
		if type in OrionApi.TypesEssential: return True
		if self.silent(): return False
		if type in OrionApi.TypesBlock: return False
		notifications = self.getGeneralNotificationsApi()
		if notifications == OrionSettings.NotificationsDisabled: return False
		elif notifications == OrionSettings.NotificationsAll: return True
		return type == None or not type in OrionApi.TypesNonessential

	##############################################################################
	# DATA
	##############################################################################

	@classmethod
	def data(self):
		data = None
		path = OrionTools.pathJoin(self.pathAddon())
		with open(path, 'r') as file: data = file.read()
		return OrionTools.unicodeString(data)

	@classmethod
	def _database(self, path = None):
		return OrionDatabase.instance(OrionSettings.DatabaseSettings, default = OrionTools.pathJoin(OrionTools.addonPath(), 'resources'), path = path)

	@classmethod
	def _commit(self):
		self._database()._commit()
		self._backupAutomatic(force = True)

	##############################################################################
	# LOCK
	##############################################################################

	@classmethod
	def _lock(self):
		global OrionSettingsLock
		OrionSettingsLock.acquire()

	@classmethod
	def _unlock(self):
		global OrionSettingsLock
		try: OrionSettingsLock.release()
		except: pass

	#############################################################################
	# CACHE
	##############################################################################

	@classmethod
	def cache(self):
		global OrionSettingsCache
		if OrionSettingsCache == None:
			OrionSettingsCache = {
				'enabled' : OrionTools.toBoolean(OrionTools.addon().getSetting('general.settings.cache')),
				'static' : {
					'data' : None,
					'values' : {},
				},
				'dynamic' : {
					'data' : None,
					'values' : {},
				},
			}
		return OrionSettingsCache

	@classmethod
	def cacheClear(self):
		global OrionSettingsCache
		OrionSettingsCache = None

	@classmethod
	def cacheEnabled(self):
		return self.cache()['enabled']

	@classmethod
	def cacheGet(self, id, raw, database = False, obfuscate = False):
		cache = self.cache()
		if raw:
			if cache['static']['data'] is None: cache['static']['data'] = OrionTools.fileRead(self.pathAddon())
			data = cache['static']['data']
			values = cache['static']['values']
			parameter = OrionSettings.ParameterDefault
		else:
			if cache['dynamic']['data'] is None: cache['dynamic']['data'] = OrionTools.fileRead(self.pathProfile())
			data = cache['dynamic']['data']
			values = cache['dynamic']['values']
			parameter = OrionSettings.ParameterValue

		if id in values:
			return values[id]
		elif database:
			result = self._getDatabase(id = id)
			if obfuscate: result = OrionTools.obfuscate(result)
			values[id] = result
			return result
		else:
			result = self.getRaw(id = id, parameter = parameter, data = data)
			if result == None: result = OrionTools.addon().getSetting(id)
			if obfuscate: result = OrionTools.obfuscate(result)
			values[id] = result
			return result

	@classmethod
	def cacheSet(self, id, value):
		self.cache()['dynamic']['values'][id] = value

	##############################################################################
	# SET
	##############################################################################

	@classmethod
	def set(self, id, value, commit = True, cached = False, backup = True):
		if value is True or value is False:
			value = OrionTools.toBoolean(value, string = True)
		elif OrionTools.isStructure(value) or value is None:
			database = self._database()
			database.insert('INSERT OR IGNORE INTO %s (id) VALUES(?);' % OrionSettings.DatabaseSettings, parameters = (id,), commit = commit)
			database.update('UPDATE %s SET data = ? WHERE id = ?;' % OrionSettings.DatabaseSettings, parameters = (OrionTools.jsonTo(value), id), commit = commit)
			value = ''
		else:
			value = str(value)
		self._lock()
		OrionTools.addon().setSetting(id = id, value = value)
		if cached or self.cacheEnabled(): self.cacheSet(id = id, value = value)
		self._unlock()
		if commit and backup: self._backupAutomatic(force = True)

	##############################################################################
	# GET
	##############################################################################

	@classmethod
	def _getDatabase(self, id):
		try: return OrionTools.jsonFrom(self._database().selectValue('SELECT data FROM %s WHERE id = "%s";' % (OrionSettings.DatabaseSettings, id)))
		except: return None

	@classmethod
	def get(self, id, raw = False, obfuscate = False, cached = True, database = False):
		if not raw and cached and self.cacheEnabled():
			return self.cacheGet(id = id, raw = raw, database = database, obfuscate = obfuscate)
		elif raw:
			return self.getRaw(id = id, obfuscate = obfuscate)
		else:
			self._backupAutomatic()
			data = OrionTools.addon().getSetting(id)
			if obfuscate: data = OrionTools.obfuscate(data)
			return data

	@classmethod
	def getRaw(self, id, parameter = ParameterDefault, data = None, obfuscate = False):
		try:
			id = OrionTools.unicodeString(id)
			if parameter == OrionSettings.ParameterValue and OrionTools.kodiVersionNew(): expression = 'id\s*=\s*"' + id + '".*?>(.*?)<'
			else: expression = 'id\s*=\s*"' + id + '".*?' + parameter + '\s*=\s*"(.*?)"'
			if data == None: data = self.data()
			match = re.search(expression, data, re.IGNORECASE)
			if match:
				data = match.group(1)
				if obfuscate: data = OrionTools.obfuscate(data)
				return data
		except:
			OrionTools.error()
			return None

	@classmethod
	def getString(self, id, raw = False, obfuscate = False):
		return self.get(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getBoolean(self, id, raw = False, obfuscate = False):
		return OrionTools.toBoolean(self.get(id = id, raw = raw, obfuscate = obfuscate))

	@classmethod
	def getBool(self, id, raw = False, obfuscate = False):
		return self.getBoolean(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getNumber(self, id, raw = False, obfuscate = False):
		return self.getDecimal(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getDecimal(self, id, raw = False, obfuscate = False):
		value = self.get(id = id, raw = raw, obfuscate = obfuscate)
		try: return float(value)
		except: return 0

	@classmethod
	def getFloat(self, id, raw = False, obfuscate = False):
		return self.getDecimal(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getInteger(self, id, raw = False, obfuscate = False):
		value = self.get(id = id, raw = raw, obfuscate = obfuscate)
		try: return int(value)
		except: return 0

	@classmethod
	def getInt(self, id, raw = False, obfuscate = False):
		return self.getInteger(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getList(self, id):
		result = self._getDatabase(id)
		return [] if result == None or result == '' else result

	@classmethod
	def getObject(self, id):
		result = self._getDatabase(id)
		return None if result == None or result == '' else result

	##############################################################################
	# GET CUSTOM
	##############################################################################

	@classmethod
	def getApp(self, app):
		try: return self.getBoolean('filters.' + app + '.app', raw = True)
		except: return False

	@classmethod
	def getIntegration(self, app):
		try: return self.getString('filters.' + app + '.integration')
		except: return ''

	@classmethod
	def getGeneralNotificationsApi(self):
		return self.getInteger('general.notifications.api')

	@classmethod
	def getGeneralNotificationsNews(self):
		return self.getBoolean('general.notifications.news')

	@classmethod
	def getGeneralNotificationsUpdates(self):
		return self.getBoolean('general.notifications.updates')

	@classmethod
	def getGeneralNotificationsTickets(self):
		return self.getBoolean('general.notifications.tickets')

	@classmethod
	def getGeneralScrapingTimeout(self):
		return self.getInteger('general.scraping.timeout')

	@classmethod
	def getGeneralScrapingMode(self):
		return self.getInteger('general.scraping.mode')

	@classmethod
	def getGeneralScrapingCount(self):
		return self.getInteger('general.scraping.count')

	@classmethod
	def getGeneralScrapingQuality(self, index = False):
		quality = max(0, self.getInteger('general.scraping.quality') - 1)
		if not index: quality = OrionStream.QualityOrder[quality]
		return quality

	@classmethod
	def getFiltersBoolean(self, attribute, type = None):
		return self.getBoolean(self._filtersAttribute(attribute, type))

	@classmethod
	def getFiltersInteger(self, attribute, type = None):
		return self.getInteger(self._filtersAttribute(attribute, type))

	@classmethod
	def getFiltersString(self, attribute, type = None):
		return self.getString(self._filtersAttribute(attribute, type))

	@classmethod
	def getFiltersObject(self, attribute, type = None, include = False, exclude = False):
		values = self.getObject(self._filtersAttribute(attribute, type))
		try:
			if include: values = [key for key, value in OrionTools.iterator(values) if value['enabled']]
		except: pass
		try:
			if exclude: values = [key for key, value in OrionTools.iterator(values) if not value['enabled']]
		except: pass
		return values if values else [] if (include or exclude) else {}

	@classmethod
	def getFiltersEnabled(self, type = None):
		return self.getFiltersBoolean('filters.enabled', type = type)

	@classmethod
	def getFiltersStreamOrigin(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.stream.origin', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersStreamSource(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.stream.source', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersStreamHoster(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.stream.hoster', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersMetaRelease(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.meta.release', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersMetaUploader(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.meta.uploader', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersMetaEdition(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.meta.edition', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersVideoCodec(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.video.codec', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersAudioType(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.audio.type', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersAudioSystem(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.audio.system', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersAudioCodec(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.audio.codec', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersAudioLanguages(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.audio.languages', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersSubtitleType(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.subtitle.type', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersSubtitleLanguages(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.subtitle.languages', type = type, include = include, exclude = exclude)

	##############################################################################
	# SET CUSTOM
	##############################################################################

	@classmethod
	def setIntegration(self, app, value, commit = True):
		return self.set('filters.' + app + '.integration', value, commit = commit)

	@classmethod
	def setFilters(self, values, wait = False):
		# Do not use threads directly to update settings. Updating the settings in a threads can cause the settings file to become corrupt.
		# This was possibly fixed through the locking mechanism. Launching the thread directly (setFiltersUpdate) should hopefully work now.
		if wait:
			self.setFiltersUpdate(values)
		else:
			#thread = threading.Thread(target = self._setFiltersThread, args = (values,))
			thread = threading.Thread(target = self.setFiltersUpdate, args = (values,))
			thread.start()

	@classmethod
	def _setFiltersThread(self, values):
		# Do not pass the values as plugin parameters, since this immediately fills up the log, since Kodi prints the entire command.
		database = self._database()
		database.create('CREATE TABLE IF NOT EXISTS %s (data TEXT);' % OrionSettings.DatabaseTemp)
		database.insert('INSERT INTO %s (data) VALUES(?);' % OrionSettings.DatabaseTemp, parameters = (OrionTools.jsonTo([value.data() for value in values]),))
		OrionTools.executePlugin(execute = True, action = 'settingsFiltersUpdate')

		# There are thread limbo exceptions thrown here sometimes.
		# Wait for executePlugin() to finish.
		# Since this is a thread, simply sleeping and waiting isn't a problem.
		OrionTools.sleep(3)

	@classmethod
	def setFiltersUpdate(self, values = None):
		from orion.modules.orionapp import OrionApp
		try:
			if values == None:
				database = self._database()
				values = database.selectValue('SELECT data FROM  %s;' % OrionSettings.DatabaseTemp)
				database.drop(OrionSettings.DatabaseTemp)
			if OrionTools.isString(values):
				values = OrionTools.jsonFrom(values)
				values = [OrionStream(value) for value in values]
		except: pass
		apps = [None] + [i.id() for i in OrionApp.instances()]
		for app in apps:
			self.setFiltersStreamOrigin(values, type = app, commit = False)
			self.setFiltersStreamSource(values, type = app, commit = False)
			self.setFiltersStreamHoster(values, type = app, commit = False)
			self.setFiltersMetaRelease(values, type = app, commit = False)
			self.setFiltersMetaUploader(values, type = app, commit = False)
			self.setFiltersMetaEdition(values, type = app, commit = False)
			self.setFiltersVideoCodec(values, type = app, commit = False)
			self.setFiltersAudioType(values, type = app, commit = False)
			self.setFiltersAudioSystem(values, type = app, commit = False)
			self.setFiltersAudioCodec(values, type = app, commit = False)
		self._commit()

	@classmethod
	def _setFilters(self, values, setting, functionStreams, functionGet, type = None, commit = True):
		if not values: return
		items = {}
		try:
			from orion.modules.orionstream import OrionStream
			for value in values:
				attribute = getattr(value, functionStreams)()
				if not attribute == None:
					items[attribute.lower()] = {'name' : attribute.upper(), 'enabled' : True}
			settings = getattr(self, functionGet)(type = type)
			if settings:
				for key, value in OrionTools.iterator(items):
					if not key in settings:
						settings[key] = value
				items = settings
		except:
			items = values
		if items: count = len([1 for key, value in OrionTools.iterator(items) if value['enabled']])
		else: count = 0
		self.set(self._filtersAttribute(setting, type), items, commit = commit)
		self.set(self._filtersAttribute(setting + '.label', type), str(count) + ' ' + OrionTools.translate(32096), commit = commit)

	@classmethod
	def _setFiltersLanguages(self, values, setting, functionStreams, functionGet, type = None, commit = True):
		if not values: return
		if values: count = len([1 for key, value in OrionTools.iterator(values) if value['enabled']])
		else: count = 0
		self.set(self._filtersAttribute(setting, type), values, commit = commit)
		self.set(self._filtersAttribute(setting + '.label', type), str(count) + ' ' + OrionTools.translate(32096), commit = commit)

	@classmethod
	def setFiltersLimitCount(self, value, type = None, commit = True):
		self.set(self._filtersAttribute('filters.limit.count', type), value, commit = commit)

	@classmethod
	def setFiltersLimitRetry(self, value, type = None, commit = True):
		self.set(self._filtersAttribute('filters.limit.retry', type), value, commit = commit)

	@classmethod
	def setFiltersStreamOrigin(self, values, type = None, commit = True):
		if not values: return
		items = {}
		try:
			from orion.modules.orionstream import OrionStream
			for value in values:
				attribute = value.streamOrigin()
				if not attribute == None and not attribute == '':
					items[attribute.lower()] = {'name' : attribute.upper(), 'type' : value.streamType(), 'enabled' : True}
			settings = self.getFiltersStreamOrigin(type = type)
			if settings:
				for key, value in OrionTools.iterator(items):
					if not key in settings:
						settings[key] = value
				items = settings
		except:
			items = values
		if items: count = len([1 for key, value in OrionTools.iterator(items) if value['enabled']])
		else: count = 0
		self.set(self._filtersAttribute('filters.stream.origin', type), items, commit = commit)
		self.set(self._filtersAttribute('filters.stream.origin.label', type), str(count) + ' ' + OrionTools.translate(32096), commit = commit)

	@classmethod
	def setFiltersStreamSource(self, values, type = None, commit = True):
		if not values: return
		items = {}
		try:
			from orion.modules.orionstream import OrionStream
			for value in values:
				attribute = value.streamSource()
				if not attribute == None and not attribute == '':
					items[attribute.lower()] = {'name' : attribute.upper(), 'type' : value.streamType(), 'enabled' : True}
			settings = self.getFiltersStreamSource(type = type)
			if settings:
				for key, value in OrionTools.iterator(items):
					if not key in settings:
						settings[key] = value
				items = settings
		except:
			items = values
		if items: count = len([1 for key, value in OrionTools.iterator(items) if value['enabled']])
		else: count = 0
		self.set(self._filtersAttribute('filters.stream.source', type), items, commit = commit)
		self.set(self._filtersAttribute('filters.stream.source.label', type), str(count) + ' ' + OrionTools.translate(32096), commit = commit)

	@classmethod
	def setFiltersStreamHoster(self, values, type = None, commit = True):
		if not values: return
		items = {}
		try:
			from orion.modules.orionstream import OrionStream
			for value in values:
				attribute = value.streamHoster()
				if not attribute == None and not attribute == '':
					items[attribute.lower()] = {'name' : attribute.upper(), 'enabled' : True}
			settings = self.getFiltersStreamHoster(type = type)
			if settings:
				for key, value in OrionTools.iterator(items):
					if not key in settings:
						settings[key] = value
				items = settings
		except:
			items = values
		if items: count = len([1 for key, value in OrionTools.iterator(items) if value['enabled']])
		else: count = 0
		self.set(self._filtersAttribute('filters.stream.hoster', type), items, commit = commit)
		self.set(self._filtersAttribute('filters.stream.hoster.label', type), str(count) + ' ' + OrionTools.translate(32096), commit = commit)

	@classmethod
	def setFiltersMetaRelease(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.meta.release', 'metaRelease', 'getFiltersMetaRelease', type, commit = commit)

	@classmethod
	def setFiltersMetaUploader(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.meta.uploader', 'metaUploader', 'getFiltersMetaUploader', type, commit = commit)

	@classmethod
	def setFiltersMetaEdition(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.meta.edition', 'metaEdition', 'getFiltersMetaEdition', type, commit = commit)

	@classmethod
	def setFiltersVideoCodec(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.video.codec', 'videoCodec', 'getFiltersVideoCodec', type, commit = commit)

	@classmethod
	def setFiltersAudioType(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.audio.type', 'audioType', 'getFiltersAudioType', type, commit = commit)

	@classmethod
	def setFiltersAudioSystem(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.audio.system', 'audioSystem', 'getFiltersAudioSystem', type, commit = commit)

	@classmethod
	def setFiltersAudioCodec(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.audio.codec', 'audioCodec', 'getFiltersAudioCodec', type, commit = commit)

	@classmethod
	def setFiltersAudioLanguages(self, values, type = None, commit = True):
		self._setFiltersLanguages(values, 'filters.audio.languages', 'audioLanguages', 'getFiltersAudioLanguages', type, commit = commit)

	@classmethod
	def setFiltersSubtitleType(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.subtitle.type', 'subtitleType', 'getFiltersSubtitleType', type, commit = commit)

	@classmethod
	def setFiltersSubtitleLanguages(self, values, type = None, commit = True):
		self._setFiltersLanguages(values, 'filters.subtitle.languages', 'subtitleLanguages', 'getFiltersSubtitleLanguages', type, commit = commit)

	##############################################################################
	# BACKUP
	##############################################################################

	@classmethod
	def _backupExportOnline(self):
		settings = {}
		try:
			path = OrionTools.pathJoin(OrionTools.addonPath(), 'resources', 'settings.xml')
			if OrionTools.fileExists(path):
				# NB: First get the database values. Do not retrieve non-database values with the database parameter.
				ids = self._database().selectValues('SELECT id FROM %s;' % OrionSettings.DatabaseSettings)
				for id in ids:
					settings[id] = self.get(id, database = True)

				data = OrionTools.fileRead(path)
				pattern = re.compile('id\s*=\s*"(.*?)"')
				ids = [id for id in re.findall(pattern, data)]

				for id in ids:
					if not id in settings:
						settings[id] = self.get(id)

				settings = {key : value for key, value in OrionTools.iterator(settings) if not key.startswith(('help', 'internal', 'account'))}
		except:
			OrionTools.error()
		return settings

	@classmethod
	def _backupImportOnline(self, settings):
		try:
			if settings:
				for key, value in OrionTools.iterator(settings):
					self.set(key, value, commit = False)
				self._commit()
				return True
		except:
			OrionTools.error()
		return False

	@classmethod
	def backupExportOnline(self):
		from orion.modules.orionapi import OrionApi
		from orion.modules.orionuser import OrionUser
		OrionInterface.loaderShow()
		data = self._backupExportOnline()
		success = OrionApi().addonUpdate(data)
		OrionInterface.loaderHide()
		if success:
			self.set('internal.backup', OrionTools.hash(OrionTools.jsonTo(data)))
			OrionInterface.dialogNotification(title = 32170, message = 33013, icon = OrionInterface.IconSuccess)
			return True
		else:
			OrionInterface.dialogNotification(title = 32170, message = 33015, icon = OrionInterface.IconError)
			return False

	@classmethod
	def backupImportOnline(self, refresh = True):
		from orion.modules.orionapi import OrionApi
		from orion.modules.orionuser import OrionUser
		OrionInterface.loaderShow()
		api = OrionApi()
		if api.addonRetrieve():
			if self._backupImportOnline(api.data()):
				# Get updated user status
				if refresh:
					OrionUser.instance().update()
					self.cacheClear()
				OrionInterface.loaderHide()
				OrionInterface.dialogNotification(title = 32170, message = 33014, icon = OrionInterface.IconSuccess)
				return True
			else:
				OrionInterface.loaderHide()
				OrionInterface.dialogNotification(title = 32170, message = 33016, icon = OrionInterface.IconError)
				return False
		else:
			OrionInterface.loaderHide()
			OrionInterface.dialogNotification(title = 32170, message = 33043, icon = OrionInterface.IconError)
			return False

	@classmethod
	def backupExportAutomaticOnline(self):
		if self._backupSetting(online = True):
			from orion.modules.orionapi import OrionApi
			data = self._backupExportOnline()
			current = OrionTools.hash(OrionTools.jsonTo(data))
			previous = self.getString('internal.backup')
			if not current == previous:
				if OrionApi().addonUpdate(data):
					self.set('internal.backup', current)
					return True
		return False

	@classmethod
	def backupImportAutomaticOnline(self):
		global OrionSettingsBackupOnline
		if not OrionSettingsBackupOnline and self._backupSetting(online = True):
			from orion.modules.orionapi import OrionApi
			OrionSettingsBackupOnline = True
			api = OrionApi()
			return api.addonRetrieve() and self._backupImportOnline(api.data())
		return False

	@classmethod
	def _backupPath(self, clear = False):
		path = OrionTools.pathTemporary('backup')
		OrionTools.directoryDelete(path)
		OrionTools.directoryCreate(path)
		return path

	@classmethod
	def _backupName(self, extension = ExtensionManual):
		# Windows does not support colons in file names.
		return OrionTools.addonName() + ' ' + OrionTools.translate(32170) + ' ' + OrionTools.timeFormat(format = '%Y-%m-%d %H.%M.%S', local = True) + '%s.' + extension

	@classmethod
	def _backupSetting(self, local = False, online = False):
		try: setting = int(OrionTools.addon().getSetting(id = 'general.settings.backup'))
		except: setting = 0
		if local and setting in [1, 3]: return True
		elif online and setting in [1, 2]: return True
		else: return False

	@classmethod
	def _backupAutomaticValid(self):
		return OrionTools.toBoolean(OrionTools.addon().getSetting(id = 'account.valid'))

	@classmethod
	def _backupAutomatic(self, force = False):
		success = False
		valid = self._backupAutomaticValid()
		local = self._backupSetting(local = True)
		online = self._backupSetting(online = True)
		if local or online:
			if valid:
				# Do not update the online backup here, since this will create too many requests to the server. Update from the service instead.
				if local: success = self._backupAutomaticExport(force = force)
			else:
				if local: success = self._backupAutomaticImport() and self._backupAutomaticValid()
				if not success and online: success = self.backupImportAutomaticOnline()
				if success:
					from orion.modules.orionuser import OrionUser
					OrionUser.instance().update()
					self.cacheClear()
		return success

	@classmethod
	def _backupAutomaticExport(self, force = False):
		global OrionSettingsBackupLocal
		if force or not OrionSettingsBackupLocal:
			OrionSettingsBackupLocal = True
			directory = OrionTools.addonProfile()
			fileFrom = OrionTools.pathJoin(directory, 'settings.xml')
			if 'account.valid' in OrionTools.fileRead(fileFrom):
				fileTo = OrionTools.pathJoin(directory, 'settings.' + OrionSettings.ExtensionAutomatic)
				return OrionTools.fileCopy(fileFrom, fileTo, overwrite = True)
		return False

	@classmethod
	def _backupAutomaticImport(self):
		directory = OrionTools.addonProfile()
		fileTo = OrionTools.pathJoin(directory, 'settings.xml')
		fileFrom = OrionTools.pathJoin(directory, 'settings.' + OrionSettings.ExtensionAutomatic)
		return OrionTools.fileCopy(fileFrom, fileTo, overwrite = True)

	@classmethod
	def backupCheck(self, path):
		return OrionTools.archiveCheck(path)

	@classmethod
	def backupFiles(self, path = None, extension = ExtensionManual):
		directory = OrionTools.addonProfile()
		files = OrionTools.directoryList(directory, files = True, directories = False)
		names = []
		settings = ['settings.xml', (OrionSettings.DatabaseSettings + OrionDatabase.Extension).lower()]
		for i in range(len(files)):
			if files[i].lower() in settings:
				names.append(files[i])
		return [OrionTools.pathJoin(directory, i) for i in names]

	@classmethod
	def backupImport(self, path = None, extension = ExtensionManual):
		try:
			from orion.modules.orionuser import OrionUser

			if path == None: path = OrionInterface.dialogBrowse(title = 32170, type = OrionInterface.BrowseFile, mask = extension)

			directory = self._backupPath(clear = True)
			directoryData = OrionTools.addonProfile()

			OrionTools.archiveExtract(path, directory)

			directories, files = OrionTools.directoryList(directory)
			counter = 0
			for file in files:
				fileFrom = OrionTools.pathJoin(directory, file)
				fileTo = OrionTools.pathJoin(directoryData, file)
				if OrionTools.fileMove(fileFrom, fileTo, overwrite = True):
					counter += 1

			OrionTools.directoryDelete(path = directory, force = True)

			# Get updated user status
			OrionInterface.loaderShow()
			OrionUser.instance().update()
			self.cacheClear()
			OrionInterface.loaderHide()

			if counter > 0:
				OrionInterface.dialogNotification(title = 32170, message = 33014, icon = OrionInterface.IconSuccess)
				return True
			else:
				OrionInterface.dialogNotification(title = 32170, message = 33016, icon = OrionInterface.IconError)
				return False
		except:
			OrionInterface.dialogNotification(title = 32170, message = 33016, icon = OrionInterface.IconError)
			OrionTools.error()
			return False

	@classmethod
	def backupExport(self, path = None, extension = ExtensionManual):
		try:
			if path == None: path = OrionInterface.dialogBrowse(title = 32170, type = OrionInterface.BrowseDirectoryWrite)

			OrionTools.directoryCreate(path)
			name = self._backupName(extension = extension)
			path = OrionTools.pathJoin(path, name)
			counter = 0
			suffix = ''
			while OrionTools.fileExists(path % suffix):
				counter += 1
				suffix = ' [%d]' % counter
			path = path % suffix

			OrionTools.archiveCreate(path, self.backupFiles())
			if self.backupCheck(path):
				OrionInterface.dialogNotification(title = 32170, message = 33013, icon = OrionInterface.IconSuccess)
				return True
			else:
				OrionTools.fileDelete(path)
				OrionInterface.dialogNotification(title = 32170, message = 33015, icon = OrionInterface.IconError)
				return False
		except:
			OrionInterface.dialogNotification(title = 32170, message = 33015, icon = OrionInterface.IconError)
			OrionTools.error()
			return False

	##############################################################################
	# EXTERNAL
	##############################################################################

	@classmethod
	def _externalComment(self, app):
		return app.upper()

	@classmethod
	def _externalStart(self, app):
		return OrionSettings.ExternalStart % self._externalComment(app)

	@classmethod
	def _externalEnd(self, app):
		return OrionSettings.ExternalEnd % self._externalComment(app)

	@classmethod
	def _externalClean(self, data):
		while re.search('(\r?\n){3,}', data): data = re.sub('(\r?\n){3,}', '\n\n', data)
		return data

	@classmethod
	def externalCategory(self, app):
		if app == None: return self.launch(OrionSettings.CategoryFilters)
		elif not OrionTools.isString(app): app = app.id()
		if app == 'universal': return self.launch(OrionSettings.CategoryFilters)
		data = OrionTools.fileRead(self.pathAddon())
		data = data[:data.find('filters.' + app)]
		self.launch(data.count('<category') - 1)

	@classmethod
	def externalInsert(self, app, check = False, settings = None, commit = True):
		from orion.modules.orionapi import OrionApi
		if not app.key() == OrionApi._keyInternal() and not OrionTools.addonName().lower() == app.name().lower(): # Check name as well, in case the key changes.
			appId = app.id()
			if not check or not self.getApp(appId):
				self.externalRemove(app)
				data = OrionTools.fileRead(self.pathAddon())

				commentStart = self._externalStart('universal')
				commentEnd = self._externalEnd('universal')
				appComment = self._externalComment(appId)

				subset = data[data.find(commentStart) + len(commentStart) : data.find(commentEnd)].strip('\n').strip('\r')

				index = subset.find('filters.app')
				subset = subset[:index] + subset[index:].replace('default="false"', 'default="true"', 1)

				index = subset.find('filters.enabled')
				subset = subset[:index] + subset[index:].replace('default="true"', 'default="false"', 1)

				subset = subset.replace('&type=universal', '&type=' + appId)
				subset = subset.replace('id="filters.', 'id="filters.' + appId + '.')
				subset = subset.replace('id="help.filters.', 'id="help.filters.' + appId + '.')
				subset = subset.replace('id="help.enabled.filters', 'id="help.enabled.filters.' + appId)
				subset = subset.replace('id="help.enable.filters', 'id="help.enable.filters.' + appId)
				subset = subset.replace('id="help.disable.filters', 'id="help.disable.filters.' + appId)
				subset = subset.replace('action=settingsHelp&type=2', 'action=settingsHelp&type=' + str(data.count('<category')))

				appStart = '\n\n' + OrionSettings.ExternalStart % appComment + '\n<category label = "' + app.name() + '">'
				appEnd = '</category>\n' + OrionSettings.ExternalEnd % appComment + '\n'
				subset = appStart + subset + appEnd

				end = '</category>'
				end = data.rfind(end) + len(end)

				endComment = 'END -->'
				if data.find(endComment, end) > 0: end = data.find(endComment, end) + len(endComment)

				data = data[:end] + subset + data[end:]
				OrionTools.fileWrite(self.pathAddon(), self._externalClean(data))

				if not settings:
					database = self._database(path = OrionTools.pathJoin(OrionTools.addonPath(), 'resources', OrionSettings.DatabaseSettings + OrionDatabase.Extension))
					settings = database.select('SELECT id, data FROM  %s;' % OrionSettings.DatabaseSettings)
					settings = [(i[0], OrionTools.jsonFrom(i[1])) for i in settings]
				for setting in settings:
					if setting[0].startswith('filters.'):
						OrionSettings.set(self._filtersAttribute(setting[0], appId), setting[1], commit = False)
				if commit: self._commit()

	@classmethod
	def externalRemove(self, app):
		if not OrionTools.isString(app): app = app.id()
		data = OrionTools.fileRead(self.pathAddon())
		commentStart = self._externalStart(app)
		commentEnd = self._externalEnd(app)
		indexStart = data.find(commentStart)
		if indexStart >= 0:
			indexEnd = data.find(commentEnd)
			if indexStart > 0 and indexEnd > indexStart:
				data = data[:indexStart] + data[indexEnd + len(commentEnd):]
			OrionTools.fileWrite(self.pathAddon(), self._externalClean(data))

	@classmethod
	def externalClean(self):
		# orionremove
		# This is needed for old Orion versions that still used the addon name instead of the app ID.
		# Otherwise each addon might have a double entry in Orion's custom filters.
		# Can be removed in later versions, but leave in for now.
		from orion.modules.orionapp import OrionApp
		from orion.modules.orionintegration import OrionIntegration
		ids = [OrionIntegration.id(i) for i in OrionIntegration.Addons]
		self._database().delete('DELETE FROM %s WHERE %s;' % (OrionSettings.DatabaseSettings, ' OR '.join([('id LIKE "filters.%s.%%"' % i) for i in ids])))
		for i in ids:
			if self.getApp(i): self.externalRemove(i)

		# NB: This has to remain here permanently.
		# Re-insert the filters if the XML file is replaced during addon updates or if the default (universal) settings change in a new version.

		database = self._database(path = OrionTools.pathJoin(OrionTools.addonPath(), 'resources', OrionSettings.DatabaseSettings + OrionDatabase.Extension))
		settings = database.select('SELECT id, data FROM  %s;' % OrionSettings.DatabaseSettings)
		settings = [(i[0], OrionTools.jsonFrom(i[1])) for i in settings]

		for i in OrionApp.instances():
			self.externalRemove(i)
			self.externalInsert(i, check = True, settings = settings, commit = False)
		self._commit()

	##############################################################################
	# ADAPT
	##############################################################################

	@classmethod
	def adapt(self, retries = 1):
		path = OrionTools.pathJoin(OrionTools.addonPath(), 'resources', 'settings.xml')
		exists = OrionTools.fileExists(path)

		version = OrionTools.kodiVersion(major = True)
		# orionremove
		'''
		if version <= 17: pathOriginal = path + '.17'
		elif version == 18: pathOriginal = path + '.18'
		elif version >= 19: pathOriginal = path + '.19'
		'''
		if version <= 17: pathOriginal = path + '.17'
		else: pathOriginal = path + '.18'

		# The XML changed between versions.
		if exists:
			dataOriginal = OrionTools.fileRead(pathOriginal)
			dataCurrent = OrionTools.fileRead(path)
			if dataOriginal and dataCurrent:
				tag = 'UNIVERSAL END'
				dataOriginal = dataOriginal[:dataOriginal.find(tag)]
				dataCurrent = dataCurrent[:dataCurrent.find(tag)]
				dataOriginal = re.sub('\s', '', dataOriginal)
				dataCurrent = re.sub('\s', '', dataCurrent)
				if dataOriginal == dataCurrent:
					OrionTools.log('The settings file exists and has not changed since the previous version. Keeping the current file.')
				else:
					OrionTools.log('The settings file exists, but has changed since the previous version. Making a new copy.')
					exists = False
		else:
			OrionTools.log('The settings file does not exist. Making a new copy.')

		if not exists:
			# Try alternative copy methods (XBMC vs native Python, copy vs file r/w).
			# Some Android devices seem to have problems copying the settings.xml file.
			count = 0
			while count < retries:
				count += 1
				if count > 1 and count < retries: OrionTools.sleep(2)

				# Use XBMC copy functions.
				OrionTools.fileCopy(pathFrom = pathOriginal, pathTo = path, overwrite = True, native = False, copy = True)
				exists = OrionTools.fileExists(path)
				if exists: break
				OrionTools.log('The XBMC file copy mechanism failed. Retry: ' + str(count))
				OrionTools.sleep(1)

				# Use XBMC file r/w functions.
				OrionTools.fileCopy(pathFrom = pathOriginal, pathTo = path, overwrite = True, native = False, copy = False)
				exists = OrionTools.fileExists(path)
				if exists: break
				OrionTools.log('The XBMC file read/write mechanism failed. Retry: ' + str(count))
				OrionTools.sleep(1)

				# Use Python copy functions.
				OrionTools.fileCopy(pathFrom = pathOriginal, pathTo = path, overwrite = True, native = True, copy = True)
				exists = OrionTools.fileExists(path)
				if exists: break
				OrionTools.log('The Python file copy mechanism failed. Retry: ' + str(count))
				OrionTools.sleep(1)

				# Use Python file r/w functions.
				OrionTools.fileCopy(pathFrom = pathOriginal, pathTo = path, overwrite = True, native = True, copy = False)
				exists = OrionTools.fileExists(path)
				if exists: break
				OrionTools.log('The Python file read/write mechanism failed. Retry: ' + str(count))
				OrionTools.sleep(1)

		return exists

	##############################################################################
	# WIZARD
	##############################################################################

	@classmethod
	def wizard(self):
		from orion.modules.orionuser import OrionUser
		from orion.modules.orionnavigator import OrionNavigator
		from orion.modules.orionintegration import OrionIntegration

		title = 32249
		cancel = 32251
		next = 32250
		skip = 32260

		# Welcome
		choice = OrionInterface.dialogOption(title = title, message = 35001, labelConfirm = cancel, labelDeny = next)
		if choice: return

		# Authentication
		choice = OrionInterface.dialogOption(title = title, message = 35002, labelConfirm = 32252, labelDeny = 32253)
		if choice:
			message = OrionTools.translate(35003) % (OrionInterface.fontBold(str(OrionUser.LinksAnonymous)), OrionInterface.fontBold(str(OrionUser.LinksFree)))
			choice = OrionInterface.dialogOption(title = title, message = message, labelConfirm = cancel, labelDeny = next)
			if choice: return
			OrionUser.anonymous()
		else:
			while True:
				if OrionNavigator.settingsAccountLogin(settings = False, refresh = False):
					break
		OrionInterface.containerRefresh()

		# Limit
		choice = OrionInterface.dialogOption(title = title, message = 35004, labelConfirm = cancel, labelDeny = next)
		if choice: return
		choice = OrionInterface.dialogInput(title = 32254, type = OrionInterface.InputNumeric, verify = (1, 30))
		limit = OrionUser.instance().subscriptionPackageLimitStreams() / float(choice)
		limit = int(OrionTools.roundDown(limit, nearest = 10 if limit >= 100 else 5 if limit >= 50 else None))
		limit = min(5000, max(5, limit))
		self.set('filters.limit.count', limit)
		self.set('filters.limit.count.movie', limit)
		self.set('filters.limit.count.show', limit)

		# Quality
		qualityHigh = OrionInterface.dialogOption(title = title, message = 35005)
		self.set('filters.video.quality.maximum', 0 if qualityHigh else 9)
		qualityLow = OrionInterface.dialogOption(title = title, message = 35006)
		self.set('filters.video.quality.minimum', 0 if qualityLow else 7)
		self.set('filters.video.quality', not(qualityHigh and qualityLow))

		# Type
		typeTorrent = OrionInterface.dialogOption(title = title, message = 35007)
		typeUsenet = OrionInterface.dialogOption(title = title, message = 35008)
		typeHoster = OrionInterface.dialogOption(title = title, message = 35009)
		typeStream = None
		if typeTorrent and typeUsenet and typeHoster: typeStream = 0
		elif typeTorrent and typeUsenet: typeStream = 1
		elif typeTorrent and typeHoster: typeStream = 2
		elif typeUsenet and typeHoster: typeStream = 3
		elif typeTorrent: typeStream = 4
		elif typeUsenet: typeStream = 5
		elif typeHoster: typeStream = 6
		if not typeStream is None: self.set('filters.stream.type', typeStream)

		# Gaia
		if OrionTools.addonEnabled('plugin.video.gaia'):
			choice = OrionInterface.dialogOption(title = title, message = 35010, labelConfirm = 32055, labelDeny = 32054)
			self.set('general.scraping.mode', 2 if choice else 1)
			if not choice:
				count = limit * 0.1
				count = OrionTools.roundDown(count, nearest = 10 if count >= 100 else 5 if count >= 50 else None)
				count = min(200, max(5, count))
				self.set('general.scraping.count', count)

		# Integration
		restart = False
		choice = OrionInterface.dialogOption(title = title, message = 35011, labelConfirm = skip, labelDeny = next)
		if not choice:
			while True:
				addons = OrionIntegration.addons(sort = True) # Refresh to recheck integration.
				items = [i['format'] for i in addons]
				choice = OrionInterface.dialogOptions(title = 32174, items = items)
				if choice < 0: break
				if addons[choice]['native']:
					OrionInterface.dialogNotification(title = 32263, message = 33024, icon = OrionInterface.IconSuccess)
				else:
					OrionIntegration.integrate(addons[choice]['scrapers'] if addons[choice]['scrapers'] else addons[choice]['name'], silent = True)
					if not restart: restart = addons[choice]['restart']

		# Finish
		OrionInterface.dialogConfirm(title = title, message = OrionTools.translate(35012))

		# Restart
		if restart and OrionInterface.dialogOption(title = 32174, message = 33026, labelConfirm = 32261, labelDeny = 32262):
			OrionTools.kodiRestart()
