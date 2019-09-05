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

import re
import os
import sys
import imp
import json
import copy
import time
import pkgutil
import urlparse
import urllib
import threading

from resources.lib.extensions import database
from resources.lib.extensions import tools

ProviderAddon = None

class ProviderBase(object):

	Queries = []

	def __init__(self, supportMovies = None, supportShows = True):
		self.mSupportMovies = supportMovies
		self.mSupportShows = supportShows

	def supportMovies(self):
		return self.mSupportMovies

	def supportShows(self):
		return self.mSupportShows

	def _provider(self):
		id = ''
		try: id += sys.modules[self.__module__].__file__
		except: pass
		try: id += self.instanceId()
		except: pass
		return tools.Hash.sha512(id)

	def _encode(self, dictionary):
		try:
			result = {}
			for k, v in dictionary.iteritems():
				if isinstance(v, (dict, list, tuple)): v =  tools.Converter.jsonTo(v)
				elif isinstance(v, unicode): v = v.encode('utf8')
				elif isinstance(v, str): v.decode('utf8') # not "v = v.decode('utf8')"
				result[k] = v
			return result
		except:
			tools.Logger.error()
			return None

	def _decode(self, url):
		try:
			if isinstance(url, (dict, list, tuple)): return url
			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
			try:
				data['alternatives'] = tools.Converter.jsonFrom(data['alternatives'])
			except: pass
			return data
		except:
			tools.Logger.error()
			return None

	def _query(self, *args):
		# Check if query was already executed, in order to avoid duplicate queries for alternative titles.
		query = self._provider()
		for arg in args:
			if not arg is None:
				try: arg = str(arg)
				except: pass
				try: arg = arg.encode('utf-8')
				except: pass
				query += arg
		if query in ProviderBase.Queries: return False
		ProviderBase.Queries.append(query)
		return True

	def movie(self, imdb, title, alternativetitles, localtitle, year):
		try:
			if isinstance(alternativetitles, dict): alternativetitles = [v for k, v in alternativetitles.iteritems()]
			url = {'imdb': imdb, 'title': title, 'year': year, 'alternatives' : alternativetitles}
			url = urllib.urlencode(self._encode(url))
			return url
		except:
			tools.Logger.error()
			return None

	def tvshow(self, imdb, tvdb, tvshowtitle, alternativetitles, localtitle, year):
		try:
			if isinstance(alternativetitles, dict): alternativetitles = [v for k, v in alternativetitles.iteritems()]
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year, 'alternatives' : alternativetitles}
			url = urllib.urlencode(self._encode(url))
			return url
		except:
			tools.Logger.error()
			return None

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url == None: return
			url = urlparse.parse_qs(url.encode('ascii'))
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urllib.urlencode(self._encode(url))
			return url
		except:
			tools.Logger.error()
			return None

	def resolve(self, url):
		return url

class ProviderExternal(ProviderBase):

	ScrapersSettings = {}
	ScrapersProviders = {}

	SettingLabel = 'providers.external.universal.open.%s.providers.label'
	SettingValue = 'providers.external.universal.open.%s.providers'

	def __init__(self):
		ProviderBase.__init__(self, supportMovies = True, supportShows = True)
		self.addon = self.Name
		self.priority = 1
		self.language = ['un']
		self.domains = []
		self.base_link = ''
		self.id = ''
		self.name = ''
		self.enabled = False
		self.object = None
		self.path = ''

	@classmethod
	def _instancesPath(self):
		return tools.System.pathProviders(self.Name)

	@classmethod
	def _instancesInclude(self):
		sys.path.append(tools.File.joinPath(self._instancesPath(), 'lib'))

	@classmethod
	def _instancesRename(self, path):
		# CloudFlare import can clash with an import from another addon.
		replacements = [
			['from resources.lib.', 'from %s.' % self.IdLibrary],
			['from %s.modules import cfscrape' % self.IdLibrary, 'try: from %s.modules import cfscrape\nexcept: pass' % self.IdLibrary],
			['xbmcaddon.Addon()', 'xbmcaddon.Addon("' + self.IdAddon + '")'],
			['if debrid.status() is False:', 'if False:'],
			['if debrid.status() == False:', 'if False:'],
		]

		try: replacements.extend(self.Replacements)
		except: pass

		directories, files = tools.File.listDirectory(path, absolute = True)
		for file in files:
			if file.endswith('.py'):
				tools.File.replaceNow(file, replacements)
		for directory in directories:
			self._instancesRename(directory)

	@classmethod
	def _instancesPrepare(self):
		pathSource = tools.System.path(self.IdAddon)
		pathDestination = self._instancesPath()
		file = 'addon.xml'
		fileSource = tools.File.joinPath(pathSource, file)
		fileDesitnation = tools.File.joinPath(pathDestination, file)
		if not tools.File.exists(fileDesitnation) or not tools.Hash.fileSha1(fileSource) == tools.Hash.fileSha1(fileDesitnation):
			tools.File.copyDirectory(pathSource, pathDestination)
			self._instancesRename(pathDestination)
		self._instancesInclude()
		return tools.File.joinPath(pathDestination, self.Path)

	def instanceAddon(self):
		return self.addon

	def instanceId(self):
		return self.id

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

	@classmethod
	def instancesProviders(self):
		if not self.IdAddon in ProviderExternal.ScrapersProviders:
			ProviderExternal.ScrapersProviders[self.IdAddon] = tools.Settings.getObject(ProviderExternal.SettingValue % self.IdGaia)
			if not ProviderExternal.ScrapersProviders[self.IdAddon]: ProviderExternal.ScrapersProviders[self.IdAddon] = {}
		return ProviderExternal.ScrapersProviders[self.IdAddon]

	@classmethod
	def instancesSettings(self):
		from resources.lib.extensions import interface
		interface.Loader.show()

		self.instancesProviders()

		addon = copy.deepcopy(ProviderExternal.ScrapersProviders[self.IdAddon])
		addon = {i : False for i in addon}

		enabled = interface.Format.fontColor(32301, interface.Format.colorExcellent())
		disabled = interface.Format.fontColor(32302, interface.Format.colorBad())

		languages = []
		labels = []
		ids = []
		instances = self.instances()
		for i in range(len(instances)):
			instance = instances[i]
			if not instance.id in ProviderExternal.ScrapersProviders[self.IdAddon]: ProviderExternal.ScrapersProviders[self.IdAddon][instance.id] = instance.enabled
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
				items.append(labels[i] + (enabled if ProviderExternal.ScrapersProviders[self.IdAddon][ids[i]] else disabled))
			choice = interface.Dialog.select(title = 32345, items = items)

			if choice <= 0: break
			elif choice == 1: ProviderExternal.ScrapersProviders[self.IdAddon] = {i : False for i in ProviderExternal.ScrapersProviders[self.IdAddon]}
			elif choice == 2: ProviderExternal.ScrapersProviders[self.IdAddon] = {i : True for i in ProviderExternal.ScrapersProviders[self.IdAddon]}
			elif choice == 3: ProviderExternal.ScrapersProviders[self.IdAddon] = copy.deepcopy(addon)
			else:
				index = choice - 4 - len(languages)
				if index >= 0:
					id = ids[index]
					ProviderExternal.ScrapersProviders[self.IdAddon][id] = not ProviderExternal.ScrapersProviders[self.IdAddon][id]
				else:
					language = languages[choice - 4]
					for i in instances:
						if i.language[0] == language:
							ProviderExternal.ScrapersProviders[self.IdAddon][i.id] = True

			tools.Settings.set(ProviderExternal.SettingLabel % self.IdGaia, str(sum(ProviderExternal.ScrapersProviders[self.IdAddon].values())) + ' ' + interface.Translation.string(32301))
			tools.Settings.set(ProviderExternal.SettingValue % self.IdGaia, ProviderExternal.ScrapersProviders[self.IdAddon])

	@classmethod
	def instancesEnable(self, providers, enable = True):
		from resources.lib.extensions import interface
		self.instancesProviders()

		found = False
		single = False
		if not isinstance(providers, list):
			providers = [providers]
			single = True

		for i in range(len(providers)):
			expression = re.search('\w{3}-(.*)', providers[i], re.IGNORECASE)
			if expression: providers[i] = expression.group(1)

		for i in range(len(ProviderExternal.ScrapersProviders[self.IdAddon])):
			for j in providers:
				if j in ProviderExternal.ScrapersProviders[self.IdAddon]:
					ProviderExternal.ScrapersProviders[self.IdAddon][j] = enable
					if single:
						found = True
						break
			if single and found: break

		tools.Settings.set(ProviderExternal.SettingLabel % self.IdGaia, str(sum(ProviderExternal.ScrapersProviders[self.IdAddon].values())) + ' ' + interface.Translation.string(32301))
		tools.Settings.set(ProviderExternal.SettingValue % self.IdGaia, ProviderExternal.ScrapersProviders[self.IdAddon])

	@classmethod
	def instancesDisable(self, providers, disable = True):
		self.instancesEnable(providers, not disable)


class ProviderExternalUnstructured(ProviderExternal):

	def movie(self, imdb, title, localtitle, aliases, year):
		try: return self.instanceObject().movie(imdb = imdb, title = title, localtitle = localtitle, aliases = aliases, year = year)
		except: return None

	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
		try: return self.instanceObject().tvshow(imdb = imdb, tvdb = tvdb, tvshowtitle = tvshowtitle, localtvshowtitle = localtvshowtitle, aliases = aliases, year = year)
		except: return None

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try: return self.instanceObject().episode(url = url, imdb = imdb, tvdb = tvdb, title = title, premiered = premiered, season = season, episode = episode)
		except: return None

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if not self._query(url): return sources
			result = self.instanceObject().sources(url, hostDict, hostprDict) # Don't use named parameters due to CMovies.
			if result:
				for item in result:
					try:
						item['external'] = True

						if not 'language' in item: item['language'] = self.language[0]
						try: item['url'] = item['url'].replace('http:http:', 'http:').replace('https:https:', 'https:').replace('http:https:', 'https:').replace('https:http:', 'http:') # Some of the links start with a double http.
						except: continue

						# External providers (eg: "Get Out"), sometimes has weird characters in the URL.
						# Ignore the links that have non-printable ASCII or UTF8 characters.
						try: item['url'].decode('utf-8')
						except: continue

						source = item['source'].lower().replace(' ', '')
						if 'torrent' in source: continue
						if source == 'direct' or source == 'directlink':
							source = urlparse.urlsplit(item['url'])[1].split(':')[0]
							from resources.lib.extensions import network
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
						tools.Logger.error(self.instanceAddon() + '-' + self.instanceName())
		except:
			tools.Logger.error(self.instanceAddon() + '-' + self.instanceName())
		return sources

	def resolve(self, url):
		return self.instanceObject().resolve(url)

	def instanceObject(self):
		try:
			if self.object == None:
				self._instancesInclude()
				self.object = imp.load_source(self.id, self.path).source()
		except:
			tools.Logger.error()
		return self.object

	@classmethod
	def instances(self):
		try:
			if not self.IdAddon in ProviderExternal.ScrapersSettings:
				tools.System.addon(self.IdAddon).setSetting('_%s_' % tools.System.name().lower(), '') # Forces Kodi to generate the settings profile file if it does not already exist.
				ProviderExternal.ScrapersSettings[self.IdAddon] = tools.File.readNow(tools.File.joinPath(tools.System.profile(self.IdAddon), 'settings.xml'))

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
						walk2 = []

						# If the scraper does not have a second level of directories, like GlobalScrapers.
						count = 0
						for package2, name2, pkg2 in pkgutil.walk_packages(path2):
							if not pkg2:
								walk2.append((package2, name2, pkg2))
								count += 1
						if count == 0:
							path2 = path1
							walk2 = [(package1, name1, pkg1)]

						for package2, name2, pkg2 in walk2:
							if not pkg2:
								try:
									id = name2
									if id == 'orion' or id == 'orionoid': continue
									name = id.replace(' ', '').replace('-', '').replace('_', '').replace('.', '').capitalize()
									path = tools.File.joinPath(path2[0], id + '.py')
									scraper = imp.load_source(id, path).source()
									scraperNew = self()
									scraperNew.id = id
									scraperNew.name = name
									scraperNew.path = path
									try: scraperNew.language[0] = scraper.language[0]
									except:
										try: scraperNew.language[0] = re.search('^(\w{2})(_.*$|$)', info).group(0)
										except: pass
									if not hasattr(scraper, '_base_link'): # _base_link: Do not use base_link that is defined as a property (eg: KinoX), since this can make additional HTTP requests, slowing down the process.
										if not scraperNew.base_link or scraperNew.base_link == '':
											try: scraperNew.base_link = scraper.base_link
											except: pass
									scraperNew.enabled = tools.Settings.raw('provider.' + id, parameter = tools.Settings.ParameterValue, data = ProviderExternal.ScrapersSettings[self.IdAddon])
									scraperNew.enabled = not scraperNew.enabled == 'false' and not scraperNew.enabled == None
									scraperNew.object = scraper
									result.append(scraperNew)
								except:
									pass
			except:
				tools.Logger.error()
			return result
		except:
			tools.Logger.error()


class ProviderExternalStructured(ProviderExternal):

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			from resources.lib import debrid
			debridHas = debrid.Debrid.enabled()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			movie = False if 'tvshowtitle' in data else True
			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			year = str(data['year']) if 'year' in data and not data['year'] == None else ''
			season = str(data['season']) if 'season' in data and not data['season'] == None else ''
			episode = str(data['episode']) if 'episode' in data and not data['episode'] == None else ''
			imdb = data['imdb'] if 'imdb' in data else ''
			tvdb = data['tvdb'] if 'tvdb' in data else ''

			if not self._query(title, year, season, episode, imdb, tvdb): return sources

			scraper = self.instanceScrapers(name = self.name.lower())()
			if self.base_link and not self.base_link == '': scraper.base_link = self.base_link
			if movie:
				result = scraper.scrape_movie(title = title, year = year, imdb = imdb, debrid = debridHas)
			else:
				showYear = year
				try:
					if 'premiered' in data and not data['premiered'] == None and not data['premiered'] == '':
						for format in ['%Y-%m-%d', '%Y-%d-%m', '%d-%m-%Y', '%m-%d-%Y']:
							try:
								showYear = str(int(convert.ConverterTime(value = data['premiered'], format = format).string(format = '%Y')))
								if len(showYear) == 4: break
							except:
								pass
				except:
					pass
				result = scraper.scrape_episode(title = title, year = year, show_year = showYear, season = season, episode = episode, imdb = imdb, tvdb = tvdb, debrid = debridHas)

			if result:
				for item in result:
					item['external'] = True
					item['language']= self.language[0]
					item['debridonly'] = False
					item['url'] = item['url'].replace('http:http:', 'http:').replace('https:https:', 'https:').replace('http:https:', 'https:').replace('https:http:', 'http:') # Some of the links start with a double http.

					# External providers (eg: "Get Out"), sometimes has weird characters in the URL.
					# Ignore the links that have non-printable ASCII or UTF8 characters.
					try: item['url'].decode('utf-8')
					except: continue

					source = item['source'].lower().replace(' ', '')
					if 'torrent' in source: continue
					if source == 'direct' or source == 'directlink':
						from resources.lib.extensions import network
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

			return sources
		except:
			tools.Logger.error()
			return sources

	@classmethod
	def instanceScrapers(self, name = None):
		result = self.Module.relevant_scrapers(names_list = name, include_disabled = True, exclude = None)
		if not name is None: result = result[0]
		return result

	@classmethod
	def instances(self):
		result = []
		try:
			scrapers = self.instanceScrapers()
			for scraper in scrapers:
				scraper = scraper()

				# The only way to figure out if it is torrent, is to inspect the source code.
				import inspect
				code = inspect.getsource(scraper.__class__).lower()
				if 'torrent' in code or 'magnet' in code: continue

				id = scraper.name.replace(' ', '').lower()
				if 'torrent' in id: continue
				if id == 'orion' or id == 'orionoid': continue
				scraperNew = self()
				scraperNew.id = id
				scraperNew.name = scraper.name
				try: scraperNew.language[0] = scraper.language[0]
				except: pass
				if not hasattr(scraper, '_base_link'): # _base_link: Do not use base_link that is defined as a property (eg: KinoX), since this can make additional HTTP requests, slowing down the process.
					if not scraperNew.base_link or scraperNew.base_link == '':
						try: scraperNew.base_link = scraper.base_link
						except: pass
				scraperNew.enabled = scraper._is_enabled()
				result.append(scraperNew)
		except:
			tools.Logger.error()
		return result


class Provider(object):

	DatabaseName = 'providers'
	DatabaseProviders = 'providers'
	DatabaseFailure = 'failure'

	# If enabled is false, retrieves all providers, even if they are disbaled in the settings.
	# If local is false, excludes local providers.
	# If object is true, it will create an instance of the class.

	Providers = None

	# Categories - must have the same value as the directory name
	CategoryUnknown = None
	CategoryGeneral = 'general'
	CategoryTorrent = 'torrent'
	CategoryUsenet = 'usenet'
	CategoryHoster = 'hoster'
	CategoryExternal = 'external'
	Categories = [CategoryGeneral, CategoryTorrent, CategoryUsenet, CategoryHoster, CategoryExternal]

	# Types - must have the same value as the directory name
	TypeUnknown = None
	TypeUniversal = 'universal'
	TypeLocal = 'local'
	TypePremium = 'premium'
	TypeFrench = 'french'
	TypeRussian = 'russian'
	Types = [TypeUniversal, TypeLocal, TypePremium, TypeFrench, TypeRussian]

	# Modes - must have the same value as the directory name
	ModeUnknown = None
	ModeOpen = 'open'
	ModeMember = 'member'

	# Groups
	GroupUnknown = None
	GroupMovies = 'movies'
	GroupTvshows = 'tvshows'
	GroupAll = 'all'

	PerformanceSlow = 'slow'
	PerformanceMedium = 'medium'
	PerformanceFast = 'fast'

	@classmethod
	def copy(self, provider):
		result = {k : v for k, v in provider.iteritems() if not k == 'object'}
		object = provider['class'].source()
		try:
			instanceFunction = getattr(object, 'instanceParameterize')
			if instanceFunction and callable(instanceFunction): instanceFunction(provider['parameters'])
		except: pass
		object.base_link = provider['object'].base_link
		result['object'] = object
		return result

	@classmethod
	def __name(self, data, setting):
		from resources.lib.extensions import interface
		name = ''
		if data:
			dummy = True
			index = 0
			setting = setting.lower()
			while dummy:
				index = data.find(setting, index)
				if index < 0: break
				dummy = 'visible="false"' in data[index : data.find('/>', index)]
				index += 1
			if dummy: index = -1

			if index >= 0:
				index = data.find('label="', index)
				if index >= 0:
					name = data[index + 7 : data.find('" ', index)]
					if name.isdigit():
						name = interface.Translation.string(int(name))
		if '$NUMBER[' in name: name = name.replace('$NUMBER[', '').replace(']', '')
		return name

	@classmethod
	def __domain(self, link):
		domain = urlparse.urlparse(link).netloc
		isIp = re.match('(?:\d{1,3}\.){3}\d{1,3}', domain)
		if not isIp:
			index = domain.rfind('.')
			if index >= 0:
				index = domain.rfind('.', 0, index)
				if index >= 0:
					return domain[index + 1:]
		return domain

	@classmethod
	def _databaseInitialize(self):
		base = database.Database(name = Provider.DatabaseName)
		base._create('CREATE TABLE IF NOT EXISTS %s (version TEXT, data TEXT, UNIQUE(version));' % Provider.DatabaseProviders)
		return base

	@classmethod
	def _databaseRetrieve(self, description = None, enabled = False, forceAll = False, forcePreset = None, quick = False):
		try:
			base = self._databaseInitialize()
			result = base._selectSingle('SELECT version, data FROM %s;' % (Provider.DatabaseProviders))
			version = result[0]
			if version == tools.System.version():
				if quick:
					data = tools.Converter.jsonFrom(result[1])
					#return len(data) > 0
					return data
				else:
					from resources.lib.extensions import handler
					handleDirect = handler.Handler(type = handler.Handler.TypeDirect)
					handleTorrent = handler.Handler(type = handler.Handler.TypeTorrent)
					handleUsenet = handler.Handler(type = handler.Handler.TypeUsenet)
					handleHoster = handler.Handler(type = handler.Handler.TypeHoster)

					failures = self.failureList()

					try:
						force = not forcePreset == None
						if force: forcePreset = tools.Settings.getObject('providers.customization.presets.values%d' % int(forcePreset))
					except:
						force = False

					data = tools.Converter.jsonFrom(result[1])
					providers = []

					for i in range(len(data)):
						provider = data[i]
						allow = False
						id = provider['id']
						setting = provider['setting']
						settingCategory = provider['settingcategory']

						if not force and tools.Settings.getBoolean(settingCategory): allow = True
						elif forceAll: allow = True
						try:
							if force and settingCategory in forcePreset['categories']: allow = True
						except: pass

						if allow:
							enabled1 = tools.Settings.getBoolean(settingCategory)
							enabled2 = tools.Settings.getBoolean(provider['setting'])
							enabled3 = not id in failures
							enabledAll = True if force else (enabled1 and enabled2 and enabled3)

							if enabled and not enabledAll: continue # Saves time to exclude disabled providers.

							type = provider['type']
							file = provider['file']
							if not description == None: # Saves time when only a single provider is needed.
								if not(id == description or provider['name'].lower() == description or setting == description or file == description):
									continue

							try:
								if force and not setting in forcePreset['providers']: continue
							except: pass

							try:
								if type == handler.Handler.TypeDirect:
									if not handleDirect.supported(): continue
								elif type == handler.Handler.TypeTorrent:
									if not handleTorrent.supported(): continue
								elif type == handler.Handler.TypeUsenet:
									if not handleUsenet.supported(): continue
								elif type == handler.Handler.TypeHoster:
									if not handleHoster.supported(): continue
							except: pass

							classPointer = imp.load_source(file.replace('.py', ''), provider['path']) # Don't use id, since the ids from external addons aare changed.
							provider['class'] = classPointer
							provider['object'] = classPointer.source()

							try:
								instanceFunction = getattr(provider['object'], 'instanceParameterize')
								if instanceFunction and callable(instanceFunction): instanceFunction(provider['parameters'])
							except:
								pass

							try:
								instanceFunction = getattr(provider['object'], 'instanceEnabled')
								if instanceFunction and callable(instanceFunction): enabledAll = enabledAll and instanceFunction()
								if enabled and not enabledAll: continue # Saves time to exclude disabled providers.
							except:
								pass

							provider['selected'] = True if force else (enabled1 and enabled2)
							provider['enabled'] = enabledAll

							# Replace custom links which were retrieved from the settings.
							provider['object'].base_link = provider['link']

							providers.append(provider)

							if not description == None:
								break

					return providers
		except:
			tools.Logger.error()
		return None

	@classmethod
	def _databaseUpdate(self, data):
		try:
			self.databaseClear()
			base = self._databaseInitialize()
			data = '"%s"' % tools.Converter.jsonTo(data).replace('"', '""').replace("'", "''")
			base._insert('INSERT INTO %s (version, data) VALUES ("%s", %s);' % (Provider.DatabaseProviders, tools.System.version(), data))
		except:
			tools.Logger.error()

	@classmethod
	def databaseClear(self):
		database.Database(name = Provider.DatabaseName)._drop(Provider.DatabaseProviders)

	@classmethod
	def addon(self):
		global ProviderAddon
		if ProviderAddon == None:
			ProviderAddon = tools.System.name()
		return ProviderAddon

	@classmethod
	def prefix(self, addon = None, dash  =True):
		if addon == None: addon = self.addon()
		prefix = addon[:3].upper()
		if dash: prefix += '-'
		return prefix

	@classmethod
	def label(self, provider, addon = None):
		provider = re.sub('[^0-9a-zA-Z]+', '', provider.capitalize())
		if addon == None: addon = self.addon()
		if addon.lower() == self.addon().lower() or provider.lower() == addon.lower(): return provider
		else: return self.prefix(addon = addon) + provider

	@classmethod
	def id(self, provider, addon = None):
		return self.label(provider = provider, addon = addon).lower()

	@classmethod
	def launch(self):
		thread = threading.Thread(target = self.initialize, args = (None, False, True, None, True))
		thread.start()

	@classmethod
	def initialize(self, description = None, enabled = False, forceAll = False, forcePreset = None, progress = False, special = False):
		from resources.lib.extensions import interface
		try:
			progressDialog = None
			Provider.Providers = []
			data = self._databaseRetrieve(description = description, enabled = enabled, forceAll = forceAll, forcePreset = forcePreset, quick = progress)

			if not data:
				if progress: progressDialog = interface.Dialog.progress(title = 35147, message = 35148, background = True)

				root = os.path.join(tools.System.path(), 'resources')
				settingsData = tools.Settings.data()
				customLinks = tools.Settings.getObject('providers.customization.locations.value')

				providers = []
				data = []
				files = []

				if progress: total = 185 # +- the total number of providers

				if special:
					total = 1
					path1 = [os.path.join(root, 'lib', 'providers', 'general', 'special', 'member')]
					for package1, name1, pkg1 in pkgutil.walk_packages(path1):
						if not pkg1:
							files.append([path1[0], 'general', 'special', 'member', name1])
							if progress: progressDialog.update(int(40 * (len(files) / total)))
				else:
					path1 = [os.path.join(root, 'lib', 'providers')]
					for package1, name1, pkg1 in pkgutil.walk_packages(path1):
						path2 = [os.path.join(path1[0], name1)]
						for package2, name2, pkg2 in pkgutil.walk_packages(path2):
							path3 = [os.path.join(path2[0], name2)]
							for package3, name3, pkg3 in pkgutil.walk_packages(path3):
								path4 = [os.path.join(path3[0], name3)]
								for package4, name4, pkg4 in pkgutil.walk_packages(path4):
									if not pkg4:
										files.append([path4[0], name1, name2, name3, name4])
										if progress: progressDialog.update(int(40 * (len(files) / total)))

				if progress:
					total = len(files)
					providersExtras = 0

				for f in files:
					try:
						directory = f[0]
						settingCategory = 'providers.%s.%s.%s.enabled' % (f[1], f[2], f[3])

						typed = f[2]
						id = f[4]
						setting = '.'.join(['providers', f[1], typed, f[3], id])

						# Ignore developer providers
						try:
							if not tools.System.developers() and tools.System.developersCode() in tools.Settings.raw(setting, parameter = tools.Settings.ParameterVisible):
								continue
						except:
							pass

						addon = None
						label = None
						name = self.__name(settingsData, setting)
						file = id + '.py'

						path = os.path.join(directory, file)
						classPointer = imp.load_source(id, path)
						object = classPointer.source()

						instances = []
						try:
							instanceFunction = getattr(object, 'instances')
							if callable(instanceFunction): instances = instanceFunction()
						except:
							instances.append(object)

						instancesMulti = len(instances) > 1
						if progress and instancesMulti: providersExtras += len(instances) - 1

						for instance in instances:

							try:
								instanceFunction = getattr(instance, 'instanceAddon')
								if callable(instanceFunction): addon = instanceFunction()
							except:
								addon = self.addon()

							if instancesMulti:
								try:
									instanceFunction = getattr(instance, 'instanceName')
									if callable(instanceFunction): name = instanceFunction()
								except:
									pass
								id = self.id(addon = addon, provider = name)

							label = self.label(addon = addon, provider = name)

							try: pack = instance.pack
							except: pack = False

							groupMovies = None
							try:
								support = getattr(instance, 'supportMovies', None)()
								if not support is None: groupMovies = support
							except: pass
							if groupMovies is None:
								try:
									functionMovie = getattr(instance, 'movie', None)
									groupMovies = True if callable(functionMovie) else False
								except:
									groupMovies = False

							groupTvshows = None
							try:
								support = getattr(instance, 'supportShows', None)()
								if not support is None: groupTvshows = support
							except: pass
							if groupTvshows is None:
								try:
									functionTvshow = getattr(instance, 'tvshow', None)
									functionEpisode = getattr(instance, 'episode', None)
									groupTvshows = True if callable(functionTvshow) or callable(functionEpisode) else False
								except:
									groupTvshows = False

							parameters = None
							try:
								functionParameters = getattr(instance, 'instanceParameters')
								if callable(functionParameters): parameters = functionParameters()
							except:
								pass

							if groupMovies and groupTvshows: group = Provider.GroupAll
							elif groupMovies: group = Provider.GroupMovies
							elif groupTvshows: group = Provider.GroupTvshows
							else: group = Provider.GroupUnknown

							link = None
							domain = None
							links = []
							domains = []
							language = None
							languages = []
							genres = []

							if hasattr(instance, 'domains') and isinstance(instance.domains, (list, tuple)) and len(instance.domains) > 0:
								domains = instance.domains
								for i in range(len(domains)):
									if domains[i].startswith('http'):
										domains[i] = self.__domain(domains[i])

							if hasattr(instance, 'language') and isinstance(instance.language, (list, tuple)) and len(instance.language) > 0:
								languages = instance.language
								language = languages[0]

							if hasattr(instance, 'genre_filter') and isinstance(instance.genre_filter, (list, tuple)) and len(instance.genre_filter) > 0:
								genres = instance.genre_filter

							# _base_link: Do not use base_link that is defined as a property (eg: KinoX), since this can make additional HTTP requests, slowing down the process.
							if not hasattr(instance, '_base_link') and hasattr(instance, 'base_link'):
								if customLinks and id in customLinks:
									instance.base_link = customLinks[id]
								link = instance.base_link
							if link == None and len(domains) > 0:
								link = domains[0]
							if isinstance(link, (list, tuple)):
								link = link[0]

							if not link == None:
								if not link.startswith('http'):
									link = 'http://' + link
								links.append(link)
								domain = self.__domain(link)
								domains.append(domain)

							for d in domains:
								if not d.startswith('http'):
									d = 'http://' + d
								links.append(d)
							if domain == None and len(domains) > 0:
								domain = domains[0]

							# Remove duplicates
							links = list(set(links))
							domains = list(set(domains))

							source = {}

							source['parameters'] = parameters

							source['category'] = f[1]
							source['type'] = typed
							source['mode'] = f[3]
							source['group'] = group
							source['external'] = f[1] == 'external'

							source['link'] = link
							source['links'] = links
							source['domain'] = domain
							source['domains'] = domains

							source['language'] = language
							source['languages'] = languages
							source['genres'] = genres

							source['id'] = id
							source['addon'] = addon
							source['name'] = name
							source['label'] = label
							source['pack'] = pack
							source['setting'] = setting
							source['settingcategory'] = settingCategory
							source['selected'] = True
							source['enabled'] = True

							source['file'] = file
							source['directory'] = directory
							source['path'] = path

							providers.append(source)

						if progress:
							total = len(files)
							progressDialog.update(int(40 + (50 * ((len(providers) - providersExtras) / float(total)))))

					except ImportError:
						pass # Do not log errors for non-installed external scraping addons.
					except Exception as error:
						tools.Logger.log('A provider could not be loaded (%s): %s.' % (str(f[4]), str(error)))
						tools.Logger.error()

				self._databaseUpdate(providers)
				if progress: progressDialog.update(100)
				data = self._databaseRetrieve(description = description, enabled = enabled, forceAll = forceAll, forcePreset = forcePreset)

			Provider.Providers = data
		except Exception as error:
			tools.Logger.log('The providers could not be loaded (%s).' % str(error))
			tools.Logger.error()

		if progressDialog:
			try: progressDialog.close()
			except: pass

		return Provider.Providers

	# description can be id, name, file, or setting.
	# exact to match alternative names, eg szukajka vs szukajkatv
	@classmethod
	def _providerEqual(self, source, description, exact = True):
		if exact:
			if source['id'] == description or source['name'] == description or source['setting'] == description or source['file'] == description:
				return True
		else:
			if source['id'] in description or description in source['id'] or source['name'] in description or description in source['name'] or source['setting'] in description or description in source['setting'] or source['file'] in description or description in source['file']:
				return True
		return False

	# description can be id, name, file, or setting.
	@classmethod
	def provider(self, description, enabled = True, local = True, genres = None, exact = True):
		description = description.lower().replace(' ', '') # Important for "local library".
		sources = self.providers(description = description if exact else None, enabled = enabled, local = local, genres = genres)
		for source in sources:
			if self._providerEqual(source, description, exact = exact):
				return source
		return None

	@classmethod
	def providers(self, description = None, enabled = True, local = True, genres = None, excludes = None, orion = True):
		# Extremley important. Only detect providers the first time.
		# If the providers are searched every time, this creates a major overhead and slow-down during the prechecks: sources.sourcesResolve() through the networker.
		if Provider.Providers == None: self.initialize(description = description, enabled = enabled)

		sources = []
		for i in range(len(Provider.Providers)):
			source = Provider.Providers[i]

			if enabled and not source['enabled']:
				continue

			if not local and source['type'] == Provider.TypeLocal:
				continue

			if not orion and (source['id'] == 'orion' or source['id'] == 'oriscrapers'):
				continue

			sourceGenres = source['genres']
			if genres and len(genres) > 0 and sourceGenres and len(sourceGenres) > 0 and not any(genre in sourceGenres for genre in genres):
				continue

			if not excludes == None:
				exclude = False
				for ex in excludes:
					if self._providerEqual(source, ex):
						exclude = True
						break
				if exclude:
					continue

			sources.append(source)

		# Clear providers in case only a single one was searched.
		if not description == None:
			Provider.Providers = None

		return sources

	@classmethod
	def providersMovies(self, enabled = True, local = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, local = local, genres = genres, excludes = excludes)
		return [i for i in sources if i['group'] == Provider.GroupMovies or i['group'] == Provider.GroupAll]

	@classmethod
	def providersTvshows(self, enabled = True, local = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, local = local, genres = genres, excludes = excludes)
		return [i for i in sources if i['group'] == Provider.GroupTvshows or i['group'] == Provider.GroupAll]

	@classmethod
	def providersAll(self, enabled = True, local = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, local = local, genres = genres, excludes = excludes)
		return [i for i in sources if i['group'] == Provider.GroupAll]

	@classmethod
	def providersTorrent(self, enabled = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, genres = genres, excludes = excludes)
		return [i for i in sources if i['category'] == Provider.CategoryTorrent]

	@classmethod
	def providersUsenet(self, enabled = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, genres = genres, excludes = excludes)
		return [i for i in sources if i['category'] == Provider.CategoryUsenet]

	@classmethod
	def providersHoster(self, enabled = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, genres = genres, excludes = excludes)
		return [i for i in sources if i['type'] == Provider.CategoryHoster]

	@classmethod
	def names(self, enabled = True, local = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, local = local, genres = genres, excludes = excludes)
		return [i['name'] for i in sources]

	@classmethod
	def enable(self, providers, enable = True):
		found = False
		single = False
		if Provider.Providers == None: self.initialize()
		if not isinstance(providers, (list, tuple)):
			single = True
			providers = [providers]

		for i in Provider.Providers:
			for j in providers:
				if i['id'] == j or i['name'] == j:
					try: getattr(i['object'], 'instancesEnable')(i['id'], enable)
					except: tools.Settings.set(i['setting'], enable)
					if single:
						found = True
						break
			if single and found: break

	@classmethod
	def disable(self, providers, disable = True):
		self.enable(providers, not disable)

	@classmethod
	def _failureInitialize(self):
		data = database.Database(name = Provider.DatabaseName)
		data._create('CREATE TABLE IF NOT EXISTS %s (id TEXT, count INTEGER, time INTEGER, UNIQUE(id));' % Provider.DatabaseFailure)
		return data

	@classmethod
	def failureClear(self):
		database.Database(name = Provider.DatabaseName)._drop(Provider.DatabaseFailure)

	@classmethod
	def failureEnabled(self):
		return tools.Settings.getBoolean('scraping.failure.enabled')

	@classmethod
	def failureList(self):
		result = []
		if self.failureEnabled():
			thresholdCount = tools.Settings.getInteger('scraping.failure.count')
			thresholdTime = tools.Settings.getInteger('scraping.failure.time')
			if thresholdTime > 0:
				thresholdTime = thresholdTime * 86400 # Convert to seconds.
				thresholdTime = tools.Time.timestamp() - thresholdTime

			data = self._failureInitialize()
			result = data._selectValues('SELECT id FROM %s WHERE NOT (count < %d OR time < %d);' % (Provider.DatabaseFailure, thresholdCount, thresholdTime))
		return result

	@classmethod
	def failureUpdate(self, finished, unfinished):
		if self.failureEnabled():
			from resources.lib.extensions import orionoid

			data = self._failureInitialize()
			current = data._selectValues('SELECT id FROM %s;' % Provider.DatabaseFailure)
			timestamp = tools.Time.timestamp()

			for id in finished:
				if not orionoid.Orionoid.Scraper in id:
					if id in current:
						data._update('UPDATE %s SET count = 0, time = %d WHERE id = "%s";' % (Provider.DatabaseFailure, timestamp, id), commit = False)
					else:
						data._insert('INSERT INTO %s (id, count, time) VALUES ("%s", 0, %d);' % (Provider.DatabaseFailure, id, timestamp), commit = False)

			for id in unfinished:
				if not orionoid.Orionoid.Scraper in id:
					if id in current:
						data._update('UPDATE %s SET count = count + 1, time = %d WHERE id = "%s";' % (Provider.DatabaseFailure, timestamp, id), commit = False)
					else:
						data._insert('INSERT INTO %s (id, count, time) VALUES ("%s", 1, %d);' % (Provider.DatabaseFailure, id, timestamp), commit = False)

			data._commit()

	# mode: manual or automatic
	@classmethod
	def sortDialog(self, mode, slot):
		from resources.lib.extensions import interface
		interface.Loader.show()
		providers = self.providers(enabled = True, local = False)
		items = [interface.Format.fontBold(33112)]
		items += [i['name'] for i in providers]
		interface.Loader.hide()

		index = interface.Dialog.options(title = 33196, items = items)
		if index < 0: return False
		elif index == 0: provider = ''
		else: provider = items[index]

		id = '%s.sort.provider%d' % (mode, int(slot))
		tools.Settings.set(id = id, value = provider)

		slot = tools.Settings.CategoryManual if mode == 'manual' else tools.Settings.CategoryAutomation
		tools.Settings.launch(slot)

		return True

	@classmethod
	def presetDialog(self, slot):
		from resources.lib.extensions import interface
		slot = int(slot)
		slotValues = 'providers.customization.presets.values%d' % slot
		slotPreset = 'providers.customization.presets.preset%d' % slot

		current = tools.Settings.getObject(slotValues)
		if current == None: option = True
		else: option = interface.Dialog.option(title = 33682, message = 33684, labelConfirm = 33686, labelDeny = 33685)

		if option:
			name = tools.Settings.getString(slotPreset)
			if not name == None and not name == '':
				index = name.find(' (')
				if index >= 0:
					name = name[:index]
			name = name.replace('&amp;', '&').replace('&apos;', "'")
			interface.Loader.hide()
			name = interface.Dialog.input(title = 33687, type = interface.Dialog.InputAlphabetic, default = name)
			if name == None or name == '':
				tools.Settings.set(slotValues, '')
				tools.Settings.set(slotPreset, '')
				interface.Dialog.notification(title = 33692, message = 33689, icon = interface.Dialog.IconSuccess)
				tools.Settings.launch(category = tools.Settings.CategoryProviders)
				interface.Loader.hide()
				return False
			interface.Loader.show()

		interface.Loader.show()

		providers = self.providers(enabled = True, local = True)
		categories = list(set([i['settingcategory'] for i in providers]))

		if option:
			items = []
			for i in providers:
				if i['selected']:
					items.append(i['setting'])
			count = len(items)
			items = list(set(items))

			instances = {}
			for i in items:
				settingLabel = i + '.providers.label'
				label = tools.Settings.getString(settingLabel)
				if label:
					settingProvider = i + '.providers'
					instances[settingLabel] = label
					instances[settingProvider] = tools.Settings.getString(settingProvider)

			name = '%s (%d)' % (name, count)
			tools.Settings.set(slotPreset, name)

			categoriesSelected = [i for i in categories if tools.Settings.getBoolean(i)]
			items = {'categories' : categoriesSelected, 'providers' : items, 'instances' : instances}
			tools.Settings.set(slotValues, items)

			interface.Dialog.notification(title = 33692, message = 33688, icon = interface.Dialog.IconSuccess)
		else:
			providers = list(set([i['setting'] for i in providers]))
			currentCategories = current['categories']
			currentProviders = current['providers']
			currentInstances = current['instances']

			for i in categories: tools.Settings.set(i, False)
			for i in providers: tools.Settings.set(i, False)
			for i in currentCategories: tools.Settings.set(i, True)
			for i in currentProviders: tools.Settings.set(i, True)
			for key, value in currentInstances.iteritems(): tools.Settings.set(key, value)

			interface.Dialog.notification(title = 33692, message = 33690, icon = interface.Dialog.IconSuccess)

		tools.Settings.launch(category = tools.Settings.CategoryProviders)
		interface.Loader.hide()

		return True

	@classmethod
	def language(self):
		if tools.Language.customization():
			language = tools.Settings.getString('scraping.alternative.language')
		else:
			language = tools.Language.Alternative
		return tools.Language.code(language)

	@classmethod
	def languageSelect(self):
		from resources.lib.extensions import interface
		id = 'scraping.alternative.language'
		items = tools.Settings.raw(id, 'values').split('|')
		choice = interface.Dialog.select(title = 33787, items = items)
		if choice >= 0: tools.Settings.set(id, items[choice])

	@classmethod
	def _optimizationPerformance(self, performance):
		from resources.lib.extensions import interface
		if performance == Provider.PerformanceSlow: return interface.Translation.string(33997)
		elif performance == Provider.PerformanceFast: return interface.Translation.string(33998)
		else: return interface.Translation.string(33999)

	@classmethod
	def optimizationDevice(self):
		from resources.lib.extensions import interface
		from resources.lib.extensions import convert
		try:
			hardware = tools.Hardware.performance()
			hardwareProcessors = tools.Hardware.processors()
			hardwareMemory = tools.Hardware.memory()
			hardwareMemory = convert.ConverterSize(value = hardwareMemory).stringOptimal()

			labels = []
			label = self._optimizationPerformance(hardware)
			if hardwareProcessors: labels.append(str(hardwareProcessors) + ' ' + interface.Translation.string(35003))
			if hardwareMemory: labels.append(str(hardwareMemory) + ' ' + interface.Translation.string(35004))
			if len(labels) > 0: label += ' (%s)' % (', '.join(labels))

			if hardware == tools.Hardware.PerformanceFast: timeout = 10
			elif hardware == tools.Hardware.PerformanceMedium: timeout = 15
			else: timeout = 20

			return (timeout, label)
		except:
			tools.Logger.error()
			return (10, interface.Translation.string(33387))

	@classmethod
	def optimizationConnection(self, iterations = 3):
		from resources.lib.extensions import interface
		from resources.lib.extensions import speedtest
		try:
			minimum = 0
			maximum = 9999999999
			latency = maximum
			download = minimum
			latencyLabel = None
			downloadLabel = None

			for i in range(iterations):
				speedtester = speedtest.SpeedTesterGlobal()
				speedtester.performance()
				if speedtester.latency() < latency:
					latency = speedtester.latency()
				if speedtester.download() > download:
					download = speedtester.download()

			if latency == maximum: latency = None
			if download == minimum: download = None
			speedtester = speedtest.SpeedTesterGlobal()
			speedtester.latencySet(latency)
			speedtester.downloadSet(download)
			performance = speedtester.performance(test = False)

			labels = []
			label = self._optimizationPerformance(performance)
			download = speedtester.formatDownload(unknown = None)
			latency = speedtester.formatLatency(unknown = None)
			if download: labels.append(download)
			if latency: labels.append(latency)
			if len(labels) > 0: label += ' (%s)' % (', '.join(labels))

			if performance == speedtest.SpeedTester.PerformanceFast: timeout = 10
			elif performance == speedtest.SpeedTester.PerformanceMedium: timeout = 15
			else: timeout = 20

			return (timeout, label)
		except:
			tools.Logger.error()
			return (10, interface.Translation.string(33387))

	@classmethod
	def optimizationProviders(self):
		from resources.lib.extensions import interface
		try:
			providersMovies = len(self.providersMovies(enabled = True, local = False))
			providersTvshows = len(self.providersTvshows(enabled = True, local = False))
			providers = max(providersMovies, providersTvshows)

			label = '%s (' + str(providers) + ' ' + interface.Translation.string(32301) + ')'
			if providers <= 10:
				timeout = 20
				label = label % interface.Translation.string(35000)
			elif providers <= 20:
				timeout = 25
				label = label % interface.Translation.string(35001)
			elif providers <= 30:
				timeout = 30
				label = label % interface.Translation.string(35001)
			elif providers <= 40:
				timeout = 35
				label = label % interface.Translation.string(35002)
			else:
				timeout = 60
				label = label % interface.Translation.string(35002)

			return (timeout, label)
		except:
			tools.Logger.error()
			return (10, interface.Translation.string(33387))

	@classmethod
	def optimizationForeign(self):
		from resources.lib.extensions import interface
		try:
			timeout = 0

			if self.language() == tools.Language.EnglishCode:
				timeout = 0
				label = interface.Translation.string(33342)
			else:
				timeout = 15
				label = interface.Translation.string(33341)

			return (timeout, label)
		except:
			tools.Logger.error()
			return (10, interface.Translation.string(33387))

	# Cannot be static, since it uses a member variable
	def optimization(self, title = 33996, introduction = True, settings = False):
		from resources.lib.extensions import interface
		try:
			if introduction:
				choice = interface.Dialog.option(title = title, message = 35005)
				if not choice:
					if settings: tools.Settings.launch(tools.Settings.CategoryScraping)
					return False

			dialog = interface.Dialog.progress(title = title, message = 35006)
			dots = ''

			self.resultTimeout = 0
			self.resultLabels = []
			resultNames = [35012, 33404, 32345, 35013]
			def results(function):
				result = function()
				self.resultTimeout += result[0]
				self.resultLabels.append(result[1])

			index = 0
			thread = None
			label = None
			functions = [self.optimizationDevice, self.optimizationConnection, self.optimizationProviders, self.optimizationForeign]
			labels = [35007, 35008, 35009, 35010]
			message = interface.Translation.string(35006)

			while True:
				# NB: Do not check for abort here. This will cause the speedtest to close automatically in the configuration wizard.
				if dialog.iscanceled():
					if settings: tools.Settings.launch(tools.Settings.CategoryScraping)
					return False

				if thread == None or not thread.is_alive():
					if index >= len(functions): break
					thread = threading.Thread(target = results, args = (functions[index],))
					thread.start()
					label = interface.Translation.string(labels[index])
					index += 1

				progress = int(((index - 1) / float(len(functions))) * 100)
				dialog.update(progress, message, '     %s %s' % (label, dots))

				dots += '.'
				if len(dots) > 3: dots = ''
				time.sleep(0.5)

			message = interface.Translation.string(35011) % self.resultTimeout
			for i in range(len(self.resultLabels)):
				message += '%s     %s: %s' % (interface.Format.newline(), interface.Translation.string(resultNames[i]), self.resultLabels[i])
			message += interface.Format.newline() + interface.Translation.string(33968)

			dialog.close()
			choice = interface.Dialog.option(title = title, message = message, labelDeny = 33926, labelConfirm = 33925)
			if choice:
				self.resultTimeout = int(interface.Dialog.input(title = title, type = interface.Dialog.InputNumeric, default = str(self.resultTimeout)))
				if self.resultTimeout < 5: self.resultTimeout = 5
				elif self.resultTimeout > 300: self.resultTimeout = 300

			tools.Settings.set('scraping.providers.timeout', self.resultTimeout)
			if settings: tools.Settings.launch(tools.Settings.CategoryScraping)
			return True
		except:
			tools.Logger.error()

	def customization(self, settings = False):
		from resources.lib.extensions import interface
		from resources.lib.extensions import verification
		try:
			def extract(providers, category):
				try:
					subproviders = [i for i in providers if i['category'] == category]
					for i in range(len(subproviders)):
						subproviders[i]['reset'] = interface.Format.bold('[%s %s] ' % (subproviders[i]['category'].capitalize(), subproviders[i]['type'].capitalize())) + subproviders[i]['label']
						subproviders[i]['label'] = interface.Format.bold('[%s %s] ' % (subproviders[i]['category'].capitalize(), subproviders[i]['type'].capitalize())) + interface.Format.color(subproviders[i]['label'], (subproviders[i]['color'] if 'color' in subproviders[i] else None))
					return sorted(subproviders, key=lambda k: k['label'])
				except:
					tools.Logger.error()

			colors = {
				verification.Verification.StatusOperational : interface.Format.colorExcellent(),
				verification.Verification.StatusLimited : interface.Format.colorMedium(),
				verification.Verification.StatusFailure : interface.Format.colorBad(),
				verification.Verification.StatusDisabled : interface.Format.colorMain(),
			}
			message = interface.Translation.string(35234) % (colors[verification.Verification.StatusOperational], colors[verification.Verification.StatusLimited], colors[verification.Verification.StatusFailure], colors[verification.Verification.StatusDisabled])
			verifications = None
			if interface.Dialog.option(title = 33017, message = message):
				verifications = verification.Verification().verifyProviders(dialog = False)

			interface.Loader.show()

			self.initialize(enabled = False, forceAll = True)
			providers = self.providers(enabled = False, local = False, orion = False)

			if verifications:
				for i in range(len(providers)):
					for j in verifications:
						if providers[i]['id'] == j['id']:
							providers[i]['color'] = colors[j['status']]
							break

			items = []
			remaining = []

			items += extract(providers, 'general')
			items += extract(providers, 'torrent')
			items += extract(providers, 'usenet')
			items += extract(providers, 'hoster')
			items += extract(providers, 'external')

			labels = [i['label'] for i in items]
			interface.Loader.hide()

			while True:
				index = interface.Dialog.select(title = 35167, items = labels)
				if index < 0: break
				labels[index] = items[index]['reset'] # Reset color if location is customized
				choice = items[index]
				link = interface.Dialog.input(title = 35167, type = interface.Dialog.InputAlphabetic, default = choice['link'])

				interface.Loader.show()

				id = 'providers.customization.locations.value'
				value = tools.Settings.getObject(id)
				if value == None: value = {}
				if link == '' or link == choice['object'].base_link:
					try: del value[choice['id']]
					except: pass
				else:
					value[choice['id']] = link
				if not value: value = ''
				tools.Settings.set(id, value)
				self.databaseClear() # Ensures that the new links are reloaded.

				interface.Loader.hide()

			if settings: tools.Settings.launch(tools.Settings.CategoryProviders)
			return True
		except:
			tools.Logger.error()
			interface.Loader.hide()
