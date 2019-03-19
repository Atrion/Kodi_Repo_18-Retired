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
import copy

import nanscrapers

from resources.lib.extensions import tools
from resources.lib.extensions import debrid
from resources.lib.extensions import convert
from resources.lib.extensions import network
from resources.lib.extensions import interface

NanScrapersProviders = None

class source:

	SettingLabel = 'providers.external.universal.open.nanscrapersx.providers.label'
	SettingValue = 'providers.external.universal.open.nanscrapersx.providers'

	def __init__(self):
		self.addon = 'NanScrapers'
		self.priority = 1
		self.language = ['un']
		self.domains = []
		self.base_link = ''
		self.id = ''
		self.name = ''
		self.enabled = False

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
		}

	def instanceParameterize(self, parameters = {}):
		try:
			for key, value in parameters.iteritems():
				try: setattr(self, key, value)
				except: pass
		except: pass

	@classmethod
	def instances(self):
		result = []
		try:
			get_scrapers = nanscrapers.relevant_scrapers(names_list = None, include_disabled = True, exclude = None)
			for scraper in get_scrapers:
				scraper = scraper()
				id = scraper.name.replace(' ', '').lower()
				if id == 'orion' or id == 'orionoid': continue
				scraperNew = source()
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

	@classmethod
	def instancesProviders(self):
		global NanScrapersProviders
		if NanScrapersProviders == None:
			NanScrapersProviders = tools.Settings.getObject(self.SettingValue)
			if not NanScrapersProviders: NanScrapersProviders = {}
		return NanScrapersProviders

	@classmethod
	def instancesSettings(self):
		interface.Loader.show()

		global NanScrapersProviders
		self.instancesProviders()

		addon = copy.deepcopy(NanScrapersProviders)
		addon = {i : False for i in addon}

		enabled = interface.Format.fontColor(32301, interface.Format.ColorExcellent)
		disabled = interface.Format.fontColor(32302, interface.Format.ColorBad)

		languages = []
		labels = []
		ids = []
		instances = self.instances()
		for i in range(len(instances)):
			instance = instances[i]
			if not instance.id in NanScrapersProviders: NanScrapersProviders[instance.id] = instance.enabled
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
				items.append(labels[i] + (enabled if NanScrapersProviders[ids[i]] else disabled))
			choice = interface.Dialog.select(title = 32345, items = items)

			if choice <= 0: break
			elif choice == 1: NanScrapersProviders = {i : False for i in NanScrapersProviders}
			elif choice == 2: NanScrapersProviders = {i : True for i in NanScrapersProviders}
			elif choice == 3: NanScrapersProviders = copy.deepcopy(addon)
			else:
				index = choice - 4 - len(languages)
				if index >= 0:
					id = ids[index]
					NanScrapersProviders[id] = not NanScrapersProviders[id]
				else:
					language = languages[choice - 4]
					for i in instances:
						if i.language[0] == language:
							NanScrapersProviders[i.id] = True

			tools.Settings.set(self.SettingLabel, str(sum(NanScrapersProviders.values())) + ' ' + interface.Translation.string(32301))
			tools.Settings.set(self.SettingValue, NanScrapersProviders)

	@classmethod
	def instancesEnable(self, providers, enable = True):
		global NanScrapersProviders
		self.instancesProviders()

		found = False
		single = False
		if not isinstance(providers, list):
			providers = [providers]
			single = True

		for i in range(len(providers)):
			expression = re.search('\w{3}-(.*)', providers[i], re.IGNORECASE)
			if expression: providers[i] = expression.group(1)

		for i in range(len(NanScrapersProviders)):
			for j in providers:
				if j in NanScrapersProviders:
					NanScrapersProviders[j] = enable
					if single:
						found = True
						break
			if single and found: break

		tools.Settings.set(self.SettingLabel, str(sum(NanScrapersProviders.values())) + ' ' + interface.Translation.string(32301))
		tools.Settings.set(self.SettingValue, NanScrapersProviders)

	@classmethod
	def instancesDisable(self, providers, disable = True):
		self.instancesEnable(providers, not disable)

	def movie(self, imdb, title, localtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return None

	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return None

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url == None: return None
			url = urlparse.parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urllib.urlencode(url)
			return url
		except:
			return None

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			debridHas = False
			if not debridHas:
				premiumize = debrid.Premiumize()
				debridHas = premiumize.accountEnabled() and premiumize.accountValid()
				if not debridHas:
					offcloud = debrid.OffCloud()
					debridHas = offcloud.accountEnabled() and offcloud.accountValid()
					if not debridHas:
						realdebrid = debrid.RealDebrid()
						debridHas = realdebrid.accountEnabled() and realdebrid.accountValid()
						if not debridHas:
							alldebrid = debrid.AllDebrid()
							debridHas = alldebrid.accountEnabled() and alldebrid.accountValid()
							if not debrid:
								rapidpremium = debrid.RapidPremium()
								debridHas = rapidpremium.accountEnabled() and rapidpremium.accountValid()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			movie = False if 'tvshowtitle' in data else True
			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			year = str(data['year']) if 'year' in data and not data['year'] == None else ''
			season = str(data['season']) if 'season' in data and not data['season'] == None else ''
			episode = str(data['episode']) if 'episode' in data and not data['episode'] == None else ''
			imdb = data['imdb'] if 'imdb' in data else ''
			tvdb = data['tvdb'] if 'tvdb' in data else ''

			scraper = nanscrapers.relevant_scrapers(names_list = self.name.lower(), include_disabled = True, exclude = None)[0]()
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

			return sources
		except:
			tools.Logger.error()
			return sources

	def resolve(self, url):
		return url
