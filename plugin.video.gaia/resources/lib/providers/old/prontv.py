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

'''
SETTINGS ACCOUNT

<!-- PRONTV -->
		<setting type="lsep" label="[UPPERCASE][B]PronTv[/B][/UPPERCASE]" />
		<setting type="sep" />
		<setting id="accounts.providers.prontv.enabled" type="bool" label="33192" default="false" />
			<setting type="action" label="[LIGHT]  $ADDON[plugin.video.gaia 33104] [I]pron.tv[/I]  [/LIGHT]" action="RunPlugin(plugin://plugin.video.gaia/?action=linkOpen&link=https://www.pron.tv)" visible="eq(-193,true)" />
			<setting type="text" default="[B]$ADDON[plugin.video.gaia 33239][/B]" label="[LIGHT]  $ADDON[plugin.video.gaia 34062]  [/LIGHT]" visible="eq(-194,true)" />
		<setting id="accounts.providers.prontv.api" type="action" label="33100" option="close" action="RunPlugin(plugin://plugin.video.gaia/?action=settingsProntv)" visible="eq(-3,true)" />
			<setting id="accounts.providers.prontv.api.items" type="text" default="" visible="false" />
			<setting id="accounts.providers.prontv.api.last" type="text" default="" visible="false" />
			<setting type="text" default="[B]$ADDON[plugin.video.gaia 33239][/B]" label="[LIGHT]  $ADDON[plugin.video.gaia 34307]  [/LIGHT]" visible="eq(-198,true) + eq(-6,true)" />
		<setting id="accounts.providers.prontv.language" type="select" label="33478" values="Any|Automatic|Abkhaz|Afar|Afrikaans|Akan|Albanian|Amharic|Arabic|Aragonese|Armenian|Assamese|Avaric|Avestan|Aymara|Azerbaijani|Bambara|Bashkir|Basque|Belarusian|Bengali|Bihari|Bislama|Bokmal|Bosnian|Breton|Bulgarian|Burmese|Catalan|Chamorro|Chechen|Chichewa|Chinese|Chuvash|Cornish|Corsican|Cree|Croatian|Czech|Danish|Divehi|Dutch|Dzongkha|English|Esperanto|Estonian|Ewe|Faroese|Fijian|Finnish|French|Fula|Gaelic|Galician|Ganda|Georgian|German|Greek|Guarani|Gujarati|Haitian|Hausa|Hebrew|Herero|Hindi|Hiri Motu|Hungarian|Icelandic|Ido|Igbo|Indonesian|Interlingua|Interlingue|Inuktitut|Inupiaq|Irish|Italian|Japanese|Javanese|Kalaallisut|Kannada|Kanuri|Kashmiri|Kazakh|Khmer|Kikuyu|Kinyarwanda|Kirundi|Komi|Kongo|Korean|Kurdish|Kwanyama|Kyrgyz|Lao|Latin|Latvian|Limburgish|Lingala|Lithuanian|Luba-Katanga|Luxembourgish|Macedonian|Malagasy|Malay|Malayalam|Maltese|Manx|Maori|Marathi|Marshallese|Mongolian|Nauruan|Navajo|Ndonga|Nepali|Northern Ndebele|Northern Sami|Norwegian|Nuosu|Nynorsk|Occitan|Ojibwe|Oriya|Oromo|Ossetian|Pali|Pashto|Pushto|Persian|Polish|Portuguese|Punjabi|Quechua|Romanian|Romansh|Russian|Samoan|Sango|Sanskrit|Sardinian|Serbian|Shona|Sindhi|Sinhalese|Slavonic|Slovak|Slovene|Somali|Southern Ndebele|Southern Sotho|Spanish|Sundanese|Swahili|Swati|Swedish|Tagalog|Tahitian|Tajik|Tamil|Tatar|Telugu|Thai|Tibetan|Tigrinya|Tonga|Tsonga|Tswana|Turkish|Turkmen|Twi|Ukrainian|Urdu|Uyghur|Uzbek|Venda|Vietnamese|Volapuk|Walloon|Welsh|Western Frisian|Wolof|Xhosa|Yiddish|Yoruba|Zhuang|Zulu" default="Any" visible="eq(-7,true) + eq(-204,true)" />
			<setting type="text" default="[B]$ADDON[plugin.video.gaia 33239][/B]" label="[LIGHT]  $ADDON[plugin.video.gaia 34137]  [/LIGHT]" visible="eq(-200,true) + eq(-8,true) + eq(-205,true)" />
		<setting id="accounts.providers.prontv.quality" type="enum" label="33479" lvalues="33113|33138|33139|33140|33141|33142|33143" default="0" visible="eq(-9,true)" />
			<setting type="text" default="[B]$ADDON[plugin.video.gaia 33239][/B]" label="[LIGHT]  $ADDON[plugin.video.gaia 34138]  [/LIGHT]" visible="eq(-202,true) + eq(-10,true)" />
		<setting id="accounts.providers.prontv.limit" type="slider" label="33480" range="10,5,500" option="int" default="50" visible="eq(-11,true)" />
			<setting type="text" default="[B]$ADDON[plugin.video.gaia 33239][/B]" label="[LIGHT]  $ADDON[plugin.video.gaia 34139]  [/LIGHT]" visible="eq(-204,true) + eq(-12,true)" />
'''

'''
SETTINGS PROVIDER

<!-- HOSTER - UNIVERSAL MEMBER -->
		<setting id="providers.hoster.universal.member.enabled" type="bool" label="33047" default="false" />
			<setting type="text" default="[B]$ADDON[plugin.video.gaia 33239][/B]" label="[LIGHT]  $ADDON[plugin.video.gaia 34053]  [/LIGHT]" visible="eq(-172,true)" />
		<setting id="providers.hoster.universal.member.alluc" type="bool" label="Alluc" subsetting="true" default="true" enable="eq(-177,true)" visible="eq(-2,true)" />
			<setting type="action" label="[LIGHT]  $ADDON[plugin.video.gaia 33104] [I]alluc.ee[/I]  [/LIGHT]" action="RunPlugin(plugin://plugin.video.gaia/?action=linkOpen&link=https://www.alluc.ee)" visible="eq(-3,true) + eq(-174,true)" />
		<setting id="providers.hoster.universal.member.prontv" type="bool" label="PronTv" subsetting="true" default="true" enable="eq(-178,true)" visible="eq(-4,true)" />
			<setting type="action" label="[LIGHT]  $ADDON[plugin.video.gaia 33104] [I]pron.tv[/I]  [/LIGHT]" action="RunPlugin(plugin://plugin.video.gaia/?action=linkOpen&link=https://www.pron.tv)" visible="eq(-5,true) + eq(-176,true)" />
'''

import re,urllib,urlparse,json,math
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import settings
from resources.lib.extensions import interface

class source:
	def __init__(self):
		self.priority = 0
		self.language = ['un']
		self.domains = ['pron.tv']
		self.base_link = 'https://www.pron.tv'
		self.search_link = '/api/search/%s/?apikey=%s&getmeta=0&query=%s&count=%d&from=%d'
		self.types = ['download', 'stream']

		language = tools.Settings.getString('accounts.providers.prontv.language')
		if language.lower() == 'any':
			self.streamLanguage = None
		else:
			if not tools.Language.customization():
				language = tools.Language.Automatic
			self.streamLanguage = tools.Language.code(language)

		self.streamQuality = tools.Settings.getInteger('accounts.providers.prontv.quality')
		if self.streamQuality == 1: self.streamQuality = '720'
		elif self.streamQuality == 2: self.streamQuality = '1080'
		elif self.streamQuality == 3: self.streamQuality = '2K'
		elif self.streamQuality == 4: self.streamQuality = '4K'
		elif self.streamQuality == 5: self.streamQuality = '6K'
		elif self.streamQuality == 6: self.streamQuality = '8K'
		else: self.streamQuality = None

		self.streamLimit = tools.Settings.getInteger('accounts.providers.prontv.limit')
		self.streamIncrease = 100 # The maximum number of links to retrieved for one API call. Alluc currently caps it at 100.

		self.enabled = tools.Settings.getBoolean('accounts.providers.prontv.enabled')

	def movie(self, imdb, title, localtitle, year):
		try:
			url = {'imdb': imdb, 'title': title, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def tvshow(self, imdb, tvdb, tvshowtitle, localtitle, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url == None: return
			url = urlparse.parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urllib.urlencode(url)
			return url
		except:
			return

	def retrieve(self, type, api, query, searchCount, searchFrom):
		try:
			url = urlparse.urljoin(self.base_link, self.search_link)
			url = url % (type, api, query, searchCount, searchFrom)
			results = client.request(url)
			return json.loads(results)
		except:
			return None

	def limit(self, result):
		return 'limit' in result['message'].lower() and result['fetchedtoday'] > 0

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None:
				raise Exception()

			if not self.enabled:
				raise Exception()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = None
				season = None
				episode = None
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				query = '%s S%02dE%02d' % (title, season, episode) if 'tvshowtitle' in data else '%s %d' % (title, year)

			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)
			if not self.streamQuality == None and not self.streamQuality == '' and not self.streamQuality == 'sd':
				query += ' %s' % self.streamQuality
			if not self.streamLanguage == None and not self.streamLanguage == '' and not self.streamLanguage == 'un':
				query += ' lang:%s' % self.streamLanguage
			query = urllib.quote_plus(query)

			hostDict = hostprDict + hostDict

			iterations = self.streamLimit / float(self.streamIncrease)
			if iterations < 1:
				last = self.streamLimit
				iterations = 1
			else:
				difference = iterations - math.floor(iterations)
				last = self.streamIncrease if difference == 0 else int(difference * self.streamIncrease)
				iterations = int(math.ceil(iterations))

			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 8
			timer = tools.Time(start = True)

			last = settings.Prontv.apiLast()
			api = settings.Prontv.apiNext()
			first = last

			for type in self.types:
				for offset in range(iterations):
					# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
					if timer.elapsed() > timerEnd:
						break

					if len(sources) >= self.streamLimit:
						break

					searchCount = last if offset == iterations - 1 else self.streamIncrease
					searchFrom = (offset * self.streamIncrease) + 1

					results = self.retrieve(type, api, query, searchCount, searchFrom)

					try:
						while self.limit(results):
							last = settings.Prontv.apiLast()
							if first == last: break
							api = settings.Prontv.apiNext()
							results = self.retrieve(type, api, query, searchCount, searchFrom)

						if self.limit(results):
							interface.Dialog.notification(title = 35261, message = interface.Translation.string(33952) + ' (' + str(results['fetchedtoday']) + ' ' + interface.Translation.string(35222) + ')', icon = interface.Dialog.IconWarning)
							tools.Time.sleep(2)
							return sources
					except: pass

					results = results['result']
					added = False
					for result in results:
						# Information
						jsonName = result['title']
						jsonSize = result['sizeinternal']
						jsonExtension = result['extension']
						jsonLanguage = result['lang']
						jsonHoster = result['hostername'].lower()
						jsonLink = result['hosterurls'][0]['url']

						# Ignore Hosters
						if not jsonHoster in hostDict:
							continue

						# Ignore Non-Videos
						# Alluc often has other files, such as SRT, also listed as streams.
						if not jsonExtension == None and not jsonExtension == '' and not tools.Video.extensionValid(jsonExtension):
							continue

						# Metadata
						meta = metadata.Metadata(name = jsonName, title = title, year = year, season = season, episode = episode, link = jsonLink, size = jsonSize)

						# Ignore
						if meta.ignore(False):
							continue

						# Add
						sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'memberonly' : True, 'source' : jsonHoster, 'language' : jsonLanguage, 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
						added = True

					if not added:
						break

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
