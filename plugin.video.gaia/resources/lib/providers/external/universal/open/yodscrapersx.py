# -*- coding: utf-8 -*-

"""
	Gaia Addon

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

import re
import urllib
import urlparse
import pkgutil
import imp
import sys
import shutil
import copy

from resources.lib.extensions import tools
from resources.lib.extensions import debrid
from resources.lib.extensions import convert
from resources.lib.extensions import network
from resources.lib.extensions import interface

YodScrapersSettings = None
YodScrapersProviders = None

class source:

	SettingLabel = 'providers.external.universal.open.yodscrapersx.providers.label'
	SettingValue = 'providers.external.universal.open.yodscrapersx.providers'

	def __init__(self):
		self.addon = 'Yoda'
		self.priority = 1
		self.language = ['un']
		self.domains = []
		self.base_link = ''
		self.id = ''
		self.name = ''
		self.enabled = False
		self.object = None
		self.path = ''

	def instanceAddon(self):
		return self.addon

	def instanceName(self):
		return self.name

	def instanceEnabled(self):
		# Get the latests setting.
		if not self.id == '':
			try: return self.instancesProviders()[self.id]
			except: pass
		return self.enabled

	def instanceParameters(self):
		return {
			'id' : self.id,
			'name' : self.name,
			'enabled' : self.enabled,
			'path' : self.path,
		}

	def instanceParameterize(self, parameters = {}):
		try:
			for key, value in parameters.iteritems():
				try: setattr(self, key, value)
				except: pass
		except: pass

	def instanceObject(self):
		try:
			if self.object == None:
				self._instancesInclude()
				self.object = imp.load_source(self.id, self.path).source()
		except:
			tools.Logger.error()
		return self.object

	@classmethod
	def _instancesPath(self):
		return tools.System.pathProviders('YodaScrapers')

	@classmethod
	def _instancesInclude(self):
		sys.path.append(tools.File.joinPath(self._instancesPath(), 'lib'))

	@classmethod
	def _instancesRename(self, path):
		replacements = [
			['from resources.', 'from yoda.'],
			['xbmcaddon.Addon()', 'xbmcaddon.Addon("' + tools.Extensions.IdYoda + '")'],
			['if debrid.status() is False:', 'if False:'],
			['if debrid.status() == False:', 'if False:'],
		]
		directories, files = tools.File.listDirectory(path, absolute = True)
		for file in files:
			if file.endswith('.py'):
				tools.File.replaceNow(file, replacements)
		for directory in directories:
			self._instancesRename(directory)

	@classmethod
	def _instancesPrepare(self):
		# Yoda's imports (from resources.lib...) clash with Gaia's imports.
		# Copy Yoda's code and change all import statements
		pathSource = tools.System.path(tools.Extensions.IdYodScrapers)
		pathDestination = self._instancesPath()
		file = 'addon.xml'
		fileSource = tools.File.joinPath(pathSource, file)
		fileDesitnation = tools.File.joinPath(pathDestination, file)
		if not tools.File.exists(fileDesitnation) or not tools.Hash.fileSha1(fileSource) == tools.Hash.fileSha1(fileDesitnation):
			tools.File.copyDirectory(pathSource, pathDestination)
			pathResources = tools.File.joinPath(pathDestination, 'lib', 'resources')
			pathYoda = tools.File.joinPath(pathDestination, 'lib', 'yoda')
			tools.File.renameDirectory(pathResources, pathYoda)
			self._instancesRename(pathYoda)
		self._instancesInclude()
		return tools.File.joinPath(pathDestination, 'lib', 'yoda', 'lib', 'sources')

	@classmethod
	def instances(self):
		global YodScrapersSettings
		if YodScrapersSettings == None:
			tools.System.addon(tools.Extensions.IdYoda).setSetting('_%s_' % tools.System.name().lower(), '') # Forces Kodi to generate the settings profile file if it does not already exist.
			YodScrapersSettings = tools.File.readNow(tools.File.joinPath(tools.System.profile(tools.Extensions.IdYoda), 'settings.xml'))

		result = []
		sources = self._instancesPrepare()

		# Sometimes there is a __init__.py file missing in the directories.
		# This file is required for a valid Python module and will cause walk_packages to fail if absence.
		directories, files = tools.File.listDirectory(sources, absolute = True)
		for directory in directories:
			path = tools.File.joinPath(directory, '__init__.py')
			if not tools.File.exists(path): tools.File.create(path)

		try:
			path1 = [sources]
			for package1, name1, pkg1 in pkgutil.walk_packages(path1):
				if not 'torrent' in name1.lower():
					path2 = [tools.File.joinPath(sources, name1)]
					for package2, name2, pkg2 in pkgutil.walk_packages(path2):
						if not pkg2:
							try:
								id = name2
								if id == 'orion' or id == 'orionoid': continue
								name = id.replace(' ', '').replace('-', '').replace('_', '').replace('.', '').capitalize()
								path = tools.File.joinPath(path2[0], id + '.py')
								scraper = imp.load_source(id, path).source()
								scraperNew = source()
								scraperNew.id = id
								scraperNew.name = name
								scraperNew.path = path
								try: scraperNew.language[0] = scraper.language[0]
								except: scraperNew.language[0] = name1
								if not hasattr(scraper, '_base_link'): # _base_link: Do not use base_link that is defined as a property (eg: KinoX), since this can make additional HTTP requests, slowing down the process.
									if not scraperNew.base_link or scraperNew.base_link == '':
										try: scraperNew.base_link = scraper.base_link
										except: pass
								scraperNew.enabled = tools.Settings.raw('provider.' + id, parameter = tools.Settings.ParameterValue, data = YodScrapersSettings)
								scraperNew.enabled = not scraperNew.enabled == 'false' and not scraperNew.enabled == None
								scraperNew.object = scraper
								result.append(scraperNew)
							except:
								pass
		except:
			tools.Logger.error()
		return result

	@classmethod
	def instancesProviders(self):
		global YodScrapersProviders
		if YodScrapersProviders == None:
			YodScrapersProviders = tools.Settings.getObject(self.SettingValue)
			if not YodScrapersProviders: YodScrapersProviders = {}
		return YodScrapersProviders

	@classmethod
	def instancesSettings(self):
		interface.Loader.show()

		global YodScrapersProviders
		self.instancesProviders()

		addon = copy.deepcopy(YodScrapersProviders)
		addon = {i : False for i in addon}

		enabled = interface.Format.fontColor(32301, interface.Format.colorExcellent())
		disabled = interface.Format.fontColor(32302, interface.Format.colorBad())

		languages = []
		labels = []
		ids = []
		instances = self.instances()
		for i in range(len(instances)):
			instance = instances[i]
			if not instance.id in YodScrapersProviders: YodScrapersProviders[instance.id] = instance.enabled
			addon[instance.id] = instance.enabled
			try: language = instance.language[0]
			except: language = 'un'
			languages.append(language)
			labels.append('[%s] %s: ' % (language.upper(), instance.name.upper()))
			ids.append(instance.id)

		languages = list(set(languages))
		actions = [33486, 35436, 35435, 35437] + [(interface.Translation.string(33192) + ' ' + tools.Language.name(i)) for i in languages]
		actions = [interface.Dialog.prefixNext(text = interface.Format.fontBold(i), bold = True) for i in actions]

		interface.Loader.hide()
		while True:
			items = copy.deepcopy(actions)
			for i in range(len(labels)):
				items.append(labels[i] + (enabled if YodScrapersProviders[ids[i]] else disabled))
			choice = interface.Dialog.select(title = 32345, items = items)

			if choice <= 0: break
			elif choice == 1: YodScrapersProviders = {i : False for i in YodScrapersProviders}
			elif choice == 2: YodScrapersProviders = {i : True for i in YodScrapersProviders}
			elif choice == 3: YodScrapersProviders = copy.deepcopy(addon)
			else:
				index = choice - 4 - len(languages)
				if index >= 0:
					id = ids[index]
					YodScrapersProviders[id] = not YodScrapersProviders[id]
				else:
					language = languages[choice - 4]
					for i in instances:
						if i.language[0] == language:
							YodScrapersProviders[i.id] = True

			tools.Settings.set(self.SettingLabel, str(sum(YodScrapersProviders.values())) + ' ' + interface.Translation.string(32301))
			tools.Settings.set(self.SettingValue, YodScrapersProviders)

	@classmethod
	def instancesEnable(self, providers, enable = True):
		global YodScrapersProviders
		self.instancesProviders()

		found = False
		single = False
		if not isinstance(providers, list):
			providers = [providers]
			single = True

		for i in range(len(providers)):
			expression = re.search('\w{3}-(.*)', providers[i], re.IGNORECASE)
			if expression: providers[i] = expression.group(1)

		for i in range(len(YodScrapersProviders)):
			for j in providers:
				if j in YodScrapersProviders:
					YodScrapersProviders[j] = enable
					if single:
						found = True
						break
			if single and found: break

		tools.Settings.set(self.SettingLabel, str(sum(YodScrapersProviders.values())) + ' ' + interface.Translation.string(32301))
		tools.Settings.set(self.SettingValue, YodScrapersProviders)

	@classmethod
	def instancesDisable(self, providers, disable = True):
		self.instancesEnable(providers, not disable)

	def movie(self, imdb, title, localtitle, aliases, year):
		try:
			return self.instanceObject().movie(imdb = imdb, title = title, localtitle = localtitle, aliases = aliases, year = year)
		except:
			return None

	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
		try:
			return self.instanceObject().tvshow(imdb = imdb, tvdb = tvdb, tvshowtitle = tvshowtitle, localtvshowtitle = localtvshowtitle, aliases = aliases, year = year)
		except:
			return None

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			return self.instanceObject().episode(url = url, imdb = imdb, tvdb = tvdb, title = title, premiered = premiered, season = season, episode = episode)
		except:
			return None

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			result = self.instanceObject().sources(url, hostDict, hostprDict) # Don't use named parameters due to CMovies.
			if result:
				for item in result:
					try:
						item['external'] = True

						if not 'language' in item: item['language'] = self.language[0]
						item['url'] = item['url'].replace('http:http:', 'http:').replace('https:https:', 'https:').replace('http:https:', 'https:').replace('https:http:', 'http:') # Some of the links start with a double http.

						# External providers (eg: "Get Out"), sometimes has weird characters in the URL.
						# Ignore the links that have non-printable ASCII or UTF8 characters.
						try: item['url'].decode('utf-8')
						except: continue

						source = item['source'].lower().replace(' ', '')
						if 'torrent' in source: continue
						if source == 'direct' or source == 'directlink':
							source = urlparse.urlsplit(item['url'])[1].split(':')[0]
							if network.Networker.ipIs(source):
								source = 'Anonymous'
							else:
								split = source.split('.')
								for i in split:
									i = i.lower()
									if i in ['www', 'ftp']: continue
									source = i
									break
							item['source'] = source
						sources.append(item)
					except:
						tools.Logger.error()
			return sources
		except:
			tools.Logger.error()
			return sources

	def resolve(self, url):
		return self.instanceObject().resolve(url)
