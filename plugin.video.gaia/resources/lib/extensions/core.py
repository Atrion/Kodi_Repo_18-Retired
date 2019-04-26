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

import xbmc,xbmcgui,xbmcvfs,sys,pkgutil,re,json,urllib,urlparse,random,datetime,time,os,copy,threading

from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import debrid
from resources.lib.modules import workers
from resources.lib.modules import trakt
from resources.lib.modules import tvmaze
from resources.lib.extensions import network
from resources.lib.extensions import interface
from resources.lib.extensions import window
from resources.lib.extensions import tools
from resources.lib.extensions import convert
from resources.lib.extensions import handler
from resources.lib.extensions import downloader
from resources.lib.extensions import history
from resources.lib.extensions import provider
from resources.lib.extensions import orionoid
from resources.lib.extensions import debrid as debridx
from resources.lib.extensions import metadata as metadatax
from resources.lib.externals.beautifulsoup import BeautifulSoup

try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

class Core:

	def __init__(self, type = tools.Media.TypeNone, kids = tools.Selection.TypeUndefined):
		self.getConstants()
		self.type = type
		self.kids = kids
		self.sources = []
		self.providers = []
		self.termination = False
		self.downloadCanceled = False

		self.countInitial = 0
		self.countDuplicates = 0
		self.countSupported = 0
		self.countFilters = 0

		self.autoplay = tools.Settings.getBoolean('automatic.enabled')
		self.propertyNotification = 'GaiaStreamsNofitifcation'

		self.navigationScrape = tools.Settings.getInteger('interface.navigation.scrape')
		self.navigationScrapeSpecial = self.navigationScrape == 0
		self.navigationScrapeDialog = self.navigationScrape == 1
		self.navigationScrapeBar = self.navigationScrape == 2

		self.navigationStreams = tools.Settings.getInteger('interface.navigation.streams')
		self.navigationStreamsSpecial = self.navigationStreams == 0
		self.navigationStreamsDirectory = self.navigationStreams == 1
		self.navigationStreamsDialog = self.navigationStreams == 2

		self.navigationPlayback = tools.Settings.getInteger('interface.navigation.playback')
		self.navigationPlaybackSpecial = self.navigationPlayback == 0
		self.navigationPlaybackDialog = self.navigationPlayback == 1
		self.navigationPlaybackBar = self.navigationPlayback == 2

	def parameterize(self, action, type = None):
		if type == None: type = self.type
		if not type == None: action += '&type=%s' % type
		if not self.kids == None: action += '&kids=%d' % self.kids
		return action

	def kidsOnly(self):
		return self.kids == tools.Selection.TypeInclude

	def progressFailure(self, single = False):
		interface.Loader.hide()
		interface.Dialog.notification(title = 33448, message = 32401 if single else 32402, icon = interface.Dialog.IconError)

	def progressNotification(self, loader = False, force = False):
		# Check if the dialog was already shown.
		# Otherwise the notification might be shown twice if:
		#    1. Streams are shown in the directory structure.
		#    2. Playback fails or cache download starts.
		# If playback doesn't start, the directory structure is reloaded and showStreams() is called again.
		if not tools.Converter.boolean(window.Window.propertyGlobal(self.propertyNotification)) or force:
			self.progressClose(force = True, loader = loader)
			if self.countInitial == 0:
				interface.Dialog.notification(title = 33448, message = 35372, icon = interface.Dialog.IconError)
			else:
				counts = []
				counts.append((35452, self.countInitial))

				filterRemovalDuplicates = interface.Filters.removalDuplicates()
				if filterRemovalDuplicates == None: filterRemovalDuplicates = tools.Settings.getBoolean('scraping.providers.duplicates')
				if filterRemovalDuplicates: counts.append((35453, self.countDuplicates))

				filterRemovalUnsupported = interface.Filters.removalUnsupported()
				if filterRemovalUnsupported == None: filterRemovalUnsupported = tools.Settings.getBoolean('scraping.providers.unsupported')
				if filterRemovalUnsupported: counts.append((35454, self.countSupported))

				counts.append((35455, self.countFilters))
				counts = ' • '.join(['%s: %d' % (interface.Translation.string(i[0]), i[1]) for i in counts])
				interface.Dialog.notification(title = 35373, message = counts, icon = interface.Dialog.IconWarning if self.countFilters == 0 else interface.Dialog.IconSuccess, time = 5000)
				if self.countFilters == 0 and self.countSupported > 0:
					interface.Loader.hide()
					result = interface.Dialog.option(title = 33448, message = 35380)
					if result: interface.Loader.show()
					return result
				else:
					window.Window.propertyGlobalSet(self.propertyNotification, True)
		return False

	def progressClose(self, loader = True, force = False):
		if self.navigationScrapeSpecial:
			if force or not self.navigationStreamsSpecial or self.autoplay:
				window.WindowScrape.update(finished = True)
				window.WindowScrape.close()
		else:
			interface.Core.close()
			if force: interface.Dialog.closeAllProgress() # If called from another process, the interface.Core instance might be lost. Close all progress dialogs.
		if loader: interface.Loader.hide()

	def progressCanceled(self):
		if self.navigationScrapeSpecial:
			try:
				if xbmc.abortRequested:
					sys.exit()
					return True
			except: pass
			return not window.WindowScrape.visible()
		else:
			if interface.Core.background():
				return False
			else:
				try:
					if xbmc.abortRequested:
						sys.exit()
						return True
				except: pass
				return interface.Core.canceled()

	def progressPlaybackEnabled(self):
		return self.navigationPlaybackSpecial

	def progressPlaybackInitialize(self, title = None, message = None, metadata = None):
		if self.navigationPlaybackSpecial:
			self.progressClose() # For autoplay.
			try: background = metadata['fanart']
			except:
				try: background = metadata['fanart2']
				except:
					try: background = metadata['fanart3']
					except: background = None
			window.WindowPlayback.show(background = background, status = message)
		else:
			interface.Core.create(type = interface.Core.TypePlayback, title = title, message = message, progress = 0)
			if interface.Core.background(): interface.Loader.hide()

	def progressPlaybackUpdate(self, progress = None, title = None, message = None, status = None, substatus1 = None, substatus2 = None, total = None, remaining = None):
		if self.navigationPlaybackSpecial:
			if status == None: status = message
			window.WindowPlayback.update(progress = progress, status = status, substatus1 = substatus1, substatus2 = substatus2, total = total, remaining = remaining)
		else:
			if message == None: message = ''
			else: message = interface.Format.fontBold(message) + '%s'
			interface.Core.update(progress = progress, title = title, message = message)

	def progressPlaybackClose(self, loader = True, force = False):
		if self.navigationPlaybackSpecial:
			window.WindowPlayback.update(finished = True)
			window.WindowPlayback.close()
		else:
			interface.Core.close()
			if force: interface.Dialog.closeAllProgress() # If called from another process, the interface.Core instance might be lost. Close all progress dialogs.
		if loader: interface.Loader.hide()

	def progressPlaybackCanceled(self):
		if self.downloadCanceled:
			return True
		elif self.navigationPlaybackSpecial:
			try:
				if xbmc.abortRequested:
					sys.exit()
					return True
			except: pass
			return not window.WindowPlayback.visible()
		else:
			if interface.Core.background():
				return False
			else:
				try:
					if xbmc.abortRequested:
						sys.exit()
						return True
				except: pass
				return interface.Core.canceled()

	def scrape(self, title = None, year = None, imdb = None, tvdb = None, season = None, episode = None, tvshowtitle = None, premiered = None, metadata = None, autoplay = None, preset = None, seasoncount = None, library = False, exact = False, items = None, process = True):
		try:
			tools.Donations.popup()

			new = items == None
			interface.Loader.show()
			window.Window.propertyGlobalClear(self.propertyNotification)

			# When the play action is called from the skin's widgets.
			# Otherwise the directory with streams is not shown.
			# Only has to be done if accessed from the home screen. Not necessary if the user is already in a directory structure.
			if self.navigationStreamsDirectory and not 'plugin' in tools.System.infoLabel('Container.PluginName') and not tools.System.infoLabel('Container.FolderPath'):
				if tools.System.versionKodiNew():
					# launchAddon() does not seem to work in Kodi 18 anymore. Switch to dialog. Other addons are doing the same.
					self.navigationStreamsDirectory = False
					self.navigationStreamsDialog = True
				else:
					tools.System.launchAddon()
					tools.Time.sleep(2) # Important, otherwise the dialog is show if the main directory shows a bit late.

			if autoplay == None:
				if tools.Converter.boolean(window.Window.propertyGlobal('PseudoTVRunning')): autoplay = True
				else: autoplay = self.autoplay

			if isinstance(metadata, basestring): metadata = tools.Converter.jsonFrom(metadata)

			# Retrieve metadata if not available.
			# Applies to links from Kodi's local library. The metadata cannot be saved in the link, since Kodi cuts off the link if too long. Retrieve it here afterwards.
			if not metadata:
				if tvshowtitle:
					from resources.lib.indexers import tvshows
					metadata = tvshows.tvshows().metadataRetrieve(title = title, year = year, imdb = imdb, tvdb = tvdb)
				else:
					from resources.lib.indexers import movies
					metadata = movies.movies().metadataRetrieve(imdb = imdb)

			if new:
				tools.Logger.log('Initializing Scraping ...', name = 'CORE', level = tools.Logger.TypeNotice)
				start = tools.Time.timestamp()
				result = self.scrapeItem(title = title, year = year, imdb = imdb, tvdb = tvdb, season = season, episode = episode, tvshowtitle = tvshowtitle, premiered = premiered, metadata = metadata, preset = preset, seasoncount = seasoncount, exact = exact, autoplay = autoplay)
				if result == None or self.progressCanceled(): # Avoid the no-streams notification right after the unavailable notification
					self.progressClose(force = True)
					return None

				try:
					api = orionoid.Orionoid()
					if api.accountAllow():
						sourcesOrion = copy.deepcopy(self.sources)
						sourcesOrion = self.sourcesRemoveDuplicates(sourcesOrion, orion = True)
						api.streamUpdate(metadata, sourcesOrion)
				except: pass
			else:
				if isinstance(items, basestring): items = tools.Converter.jsonFrom(items)
				self.sources = items

			self.sources = self.sourcesPrepare(items = self.sources)

			data = copy.deepcopy(self.sources)
			for i in range(len(data)):
				metadatax.Metadata.uninitialize(data[i])
			window.Window.propertyGlobalClear(self.propertyExtras)
			window.Window.propertyGlobalSet(self.propertyItems, tools.Converter.jsonTo(data))
			window.Window.propertyGlobalSet(self.propertyMeta, tools.Converter.jsonTo(metadata))

			if new and tools.Settings.getBoolean('scraping.termination.enabled') and tools.Settings.getInteger('scraping.termination.mode') == 3:
				autoplay = self.termination or (tools.Time.timestamp() - start) < tools.Settings.getInteger('scraping.providers.timeout')

			self._showClear()
			self.showStreams(items = self.sources, metadata = metadata, autoplay = autoplay, initial = True, library = library, direct = exact, new = new, process = process)
		except:
			tools.Logger.error()
			self.progressClose(force = True)

	def scrapeExact(self, terms = None):
		if not tools.Settings.getBoolean('internal.search.exact'):
			interface.Dialog.confirm(title = 32010, message = 35159)
			tools.Settings.set('internal.search.exact', True)
		if terms == None: terms = interface.Dialog.input(title = 35158, type = interface.Dialog.InputAlphabetic)
		if not terms == None and not terms == '':
			if self.type == tools.Media.TypeEpisode or self.type == tools.Media.TypeShow: return self.scrape(tvshowtitle = terms, exact = True)
			else: return self.scrape(title = terms, exact = True)

	def scrapePreset(self, link):
		try:
			interface.Loader.show()
			items = []

			for i in range(1, 6):
				name = tools.Settings.getString('providers.customization.presets.preset%d' % i)
				if not name == None and not name == '': items.append(name)

			itemCount = len(items)
			if itemCount == 0:
				interface.Loader.hide()
				interface.Dialog.notification(title = 35058, message = 35059, icon = interface.Dialog.IconError)
			else:
				labelManual = interface.Format.bold(interface.Translation.string(33110) + ': ')
				labelAutomatic = interface.Format.bold(interface.Translation.string(33800) + ': ')
				itemsManual = []
				itemsAutomatic = []
				for item in items:
					item = tools.Converter.htmlFrom(item)
					itemsManual.append(labelManual + item)
					itemsAutomatic.append(labelAutomatic + item)
				items = itemsManual + itemsAutomatic

				preset = interface.Dialog.options(title = 35058, items = items)
				if preset >= 0:
					if preset >= itemCount:
						preset -= itemCount
						autoplay = True
					else:
						autoplay = False
					preset += 1 # Settings start at 1.
					control.execute('RunPlugin(%s&autoplay=%d&preset=%d)' % (link, autoplay, preset))
		except:
			pass
		interface.Loader.hide()

	def scrapeManual(self, link):
		tools.System.execute('RunPlugin(%s&autoplay=%d)' % (link, False))

	def scrapeAutomatic(self, link):
		tools.System.execute('RunPlugin(%s&autoplay=%d)' % (link, True))

	def scrapeAlternative(self, link):
		tools.System.execute('RunPlugin(%s&autoplay=%d)' % (link, False if self.autoplay else True))

	def scrapeItem(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, metadata = None, preset = None, seasoncount = None, exact = False, autoplay = False):
		try:
			def titleClean(value):
				if value == None: return None

				# Remove years in brackets from titles.
				# Do not remove years that are not between brackets, since it might be part of the title. Eg: 2001 A Space Oddesy
				# Eg: Heartland (CA) (2007) -> Heartland (CA)
				value = re.sub('\([0-9]{4}\)', '', value)
				value = re.sub('\[[0-9]{4}\]', '', value)
				value = re.sub('\{[0-9]{4}\}', '', value)

				# Remove symbols.
				# Eg: Heartland (CA) -> Heartland CA
				# Replace with space: Brooklyn Nine-Nine -> Brooklyn Nine Nine
				value = re.sub('[^A-Za-z0-9\s]', ' ', value)

				# Replace extra spaces.
				value = re.sub('\s\s+', ' ', value)
				value = value.strip()

				return value

			def _progressShow(title, message, metadata = None):
				self.mLastMessage1 = message
				if self.navigationScrapeSpecial:
					try: background = metadata['fanart']
					except:
						try: background = metadata['fanart2']
						except:
							try: background = metadata['fanart3']
							except: background = None
					window.WindowScrape.show(background = background, status = message)
				else:
					interface.Core.create(type = interface.Core.TypeScrape, title = title, message = message)

			def _progressUpdate(percentage, message1, message2 = None, message2Alternative = None, showElapsed = True):
				if percentage == None: percentage = self.progressPercentage
				else: self.progressPercentage = max(percentage, self.progressPercentage) # Do not let the progress bar go back if more streams are added while precheck is running.

				if self.navigationScrapeSpecial:
					self.mLastMessage1 = message1
					window.WindowScrape.update(
						status = message1, progress = self.progressPercentage, time = _progressElapsed(),
						streamsTotal = self.streamsTotal, streamsHdUltra = self.streamsHdUltra, streamsHd1080 = self.streamsHd1080, streamsHd720 = self.streamsHd720, streamsSd = self.streamsSd, streamsLd = self.streamsCam + self.streamsScr,
						streamsTorrent = self.streamsTorrent, streamsUsenet = self.streamsUsenet, streamsHoster = self.streamsHoster,
						streamsCached = self.streamsCached, streamsDebrid = self.streamsDebrid, streamsDirect = self.streamsDirect, streamsPremium = self.streamsPremium, streamsLocal = self.streamsLocal,
						streamsFinished = self.streamsFinished, streamsBusy = self.streamsBusy,
						providersFinished = self.providersFinished, providersBusy = self.providersBusy, providersLabels = self.providersLabels
					)
				else:
					if not message2: message2 = ''
					if interface.Core.background():
						messageNew = self.mLastName + message1
						if message2Alternative: message2 = message2Alternative
						# Do last, because of message2Alternative. Must be done BEFORE dialog update, otherwise stream count sometimes jumps back.
						self.mLastMessage1 = message1
						self.mLastMessage2 = message2
						elapsedTime = _progressElapsed(mini = True) + interface.Format.separator() if showElapsed else ''
						interface.Core.update(progress = self.progressPercentage, title = messageNew, message = elapsedTime + message2)
					else:
						messageNew = interface.Format.fontBold(message1) + '%s'
						# Do last, because of message2Alternative. Must be done BEFORE dialog update, otherwise stream count sometimes jumps back.
						self.mLastMessage1 = message1
						self.mLastMessage2 = message2
						elapsedTime = _progressElapsed(full = True) if showElapsed else ' '
						interface.Core.update(progress = self.progressPercentage, message = interface.Format.newline().join([messageNew, elapsedTime, message2]))

			def _progressTime():
				while not self.stopThreads:
					_progressUpdate(self.progressPercentage, self.mLastMessage1, self.mLastMessage2)
					time.sleep(0.2)

			def _progressElapsed(raw = True, mini = False, full = False):
				seconds = max(0, timer.elapsed())
				if full: return timeStringDescription % seconds
				elif mini: return timeString % seconds
				else: return seconds

			def additionalInformation(title, tvshowtitle, imdb, tvdb):
				threadsInformation = []

				threadsInformation.append(workers.Thread(additionalInformationTitle, title, tvshowtitle, imdb, tvdb))

				if not tvshowtitle == None: title = tvshowtitle
				if tools.Settings.getBoolean('scraping.foreign.characters'):
					threadsInformation.append(workers.Thread(additionalInformationCharacters, title, imdb, tvdb))

				[thread.start() for thread in threadsInformation]
				[thread.join() for thread in threadsInformation]

				# Title for the foreign language in the settings.
				if self.titleLocal:
					local = tools.Converter.unicode(self.titleLocal)
					if not local == tools.Converter.unicode(title):
						found = False
						for value in self.titleAlternatives.itervalues():
							if tools.Converter.unicode(value) == local:
								found = True
								break
						if not found:
							self.titleAlternatives['local'] = self.titleLocal

			def additionalInformationCharacters(title, imdb, tvdb):
				try:
					# NB: Always compare the unicode (tools.Converter.unicode) of the titles.
					# Some foreign titles have some special character at the end, which will cause titles that are actually the same not to be detected as the same.
					# Unicode function will remove unwanted characters. Still keep the special characters in the variable.

					tmdbApi = tools.Settings.getString('accounts.informants.tmdb.api') if tools.Settings.getBoolean('accounts.informants.tmdb.enabled') else ''
					if tmdbApi == '': tmdbApi = tools.System.obfuscate(tools.Settings.getString('internal.tmdb.api', raw = True))
					if not tmdbApi == '':
						result = cache.get(client.request, 240, 'http://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % (imdb, tmdbApi))
						self.progressInformationCharacters = 25
						result = json.loads(result)
						if 'original_title' in result: # Movies
							self.titleOriginal = result['original_title']
						elif 'original_name' in result: # Shows
							self.titleOriginal = result['original_name']

					if not self.titleOriginal:
						self.progressInformationCharacters = 50
						result = cache.get(client.request, 240, 'http://www.imdb.com/title/%s' % (imdb))
						self.progressInformationCharacters = 75
						result = BeautifulSoup(result)
						resultTitle = result.find_all('div', class_ = 'originalTitle')
						if len(resultTitle) > 0:
							self.titleOriginal = resultTitle[0].getText()
							self.titleOriginal = self.titleOriginal[:self.titleOriginal.rfind('(')]
						else:
							resultTitle = result.find_all('h1', {'itemprop' : 'name'})
							if len(resultTitle) > 0:
								self.titleOriginal = resultTitle[0].getText()
								self.titleOriginal = self.titleOriginal[:self.titleOriginal.rfind('(')]

					try: # UTF-8 and ASCII comparison might fail
						self.titleOriginal = self.titleOriginal.strip() # Sometimes foreign titles have a space at the end.
						if tools.Converter.unicode(self.titleOriginal) == tools.Converter.unicode(title): # Do not search if they are the same.
							self.titleOriginal = None
					except: pass

					self.titleForeign1 = metadatax.Metadata.foreign(title)
					try: # UTF-8 and ASCII comparison might fail
						if any(i == tools.Converter.unicode(self.titleForeign1) for i in [tools.Converter.unicode(title), tools.Converter.unicode(self.titleOriginal)]):
							self.titleForeign1 = None
					except: pass

					if self.titleOriginal:
						self.titleForeign2 = metadatax.Metadata.foreign(self.titleOriginal)
						try: # UTF-8 and ASCII comparison might fail
							if any(i == tools.Converter.unicode(self.titleForeign2) for i in [tools.Converter.unicode(title), tools.Converter.unicode(self.titleOriginal), tools.Converter.unicode(self.titleForeign1)]):
								self.titleForeign2 = None
						except: pass

					self.titleUmlaut1 = metadatax.Metadata.foreign(title, True)
					try: # UTF-8 and ASCII comparison might fail
						if any(i == tools.Converter.unicode(self.titleUmlaut1) for i in [tools.Converter.unicode(title), tools.Converter.unicode(self.titleOriginal), tools.Converter.unicode(self.titleForeign1), tools.Converter.unicode(self.titleForeign2)]):
							self.titleUmlaut1 = None
					except: pass

					if self.titleOriginal:
						self.titleUmlaut2 = metadatax.Metadata.foreign(self.titleOriginal, True)
						try: # UTF-8 and ASCII comparison might fail
							if any(i == tools.Converter.unicode(self.titleUmlaut2) for i in [tools.Converter.unicode(title), tools.Converter.unicode(self.titleOriginal), tools.Converter.unicode(self.titleForeign1), tools.Converter.unicode(self.titleForeign2), tools.Converter.unicode(self.titleUmlaut1)]):
								self.titleUmlaut2 = None
						except: pass

					if not self.titleOriginal == None: self.titleAlternatives['original'] = self.titleOriginal
					if not self.titleForeign1 == None: self.titleAlternatives['foreign1'] = self.titleForeign1
					if not self.titleForeign2 == None: self.titleAlternatives['foreign2'] = self.titleForeign2
					if not self.titleUmlaut1 == None: self.titleAlternatives['umlaut1'] = self.titleUmlaut1
					if not self.titleUmlaut2 == None: self.titleAlternatives['umlaut2'] = self.titleUmlaut2

					# Also search titles that contain abbrviations (consecutive capital letters).
					# Eg: "K.C. Undercover" is retrieved as "KC Undercover" by informants. Most providers have it as "K C Undercover".
					self.titleAbbreviation = self.titleOriginal
					abbreviations = re.findall('[A-Z]{2,}', self.titleAbbreviation)

					if not self.titleAbbreviation == self.titleOriginal:
						self.titleAlternatives['abbreviation'] = self.titleAbbreviation

					self.progressInformationCharacters = 100
				except:
					pass

			def additionalInformationTitle(title, tvshowtitle, imdb, tvdb):
				self.progressInformationLanguage = 25
				if tvshowtitle == None:
					content = 'movie'
					title = cleantitle.normalize(title)
					self.titleLocal = self.getLocalTitle(title, imdb, tvdb, content)
					self.progressInformationLanguage = 50
					self.titleAliases = self.getAliasTitles(imdb, self.titleLocal, content)
				else:
					content = 'tvshow'
					tvshowtitle = cleantitle.normalize(tvshowtitle)
					self.titleLocal = self.getLocalTitle(tvshowtitle, imdb, tvdb, content)
					self.progressInformationLanguage = 50
					self.titleAliases = self.getAliasTitles(imdb, self.titleLocal, content)
				self.progressInformationLanguage = 100

			def initializeProviders(movie, preset, imdb, tvdb, excludes):
				if movie:
					content = 'movie'
					type = 'imdb'
					id = imdb
				else:
					content = 'show'
					type = 'tvdb'
					id = tvdb
				genres = trakt.getGenre(content, type, id)
				if not preset == None: provider.Provider.initialize(forcePreset = preset)
				if movie: self.providers = provider.Provider.providersMovies(enabled = True, local = True, genres = genres, excludes = excludes)
				else: self.providers = provider.Provider.providersTvshows(enabled = True, local = True, genres = genres, excludes = excludes)
				self.providersBusy = len(self.providers)

			tools.Logger.log('Starting Scraping ...', name = 'CORE', level = tools.Logger.TypeNotice)

			threads = []

			self.streamsTotal = 0
			self.streamsHdUltra = 0
			self.streamsHd1080 = 0
			self.streamsHd720 = 0
			self.streamsSd = 0
			self.streamsScr = 0
			self.streamsCam = 0
			self.streamsTorrent = 0
			self.streamsUsenet = 0
			self.streamsHoster = 0
			self.streamsCached = 0
			self.streamsDebrid = 0
			self.streamsDirect = 0
			self.streamsPremium = 0
			self.streamsLocal = 0

			self.providersLabels = None
			self.providersFinished = 0
			self.providersBusy = 0
			self.streamsFinished = 0
			self.streamsBusy = 0

			self.stopThreads = False
			self.threadsAdjusted = []
			self.sourcesAdjusted = []
			self.statusAdjusted = []
			self.cachedAdjusted = 0
			self.cachedAdjustedBusy = False
			self.priortityAdjusted = []
			self.threadsLock = threading.Lock()
			self.dataLock = threading.Lock()

			# Termination

			self.termination = False
			self.terminationLock = threading.Lock()
			self.terminationPrevious = 0
			self.terminationMode = tools.Settings.getInteger('scraping.termination.mode')
			self.terminationEnabled = tools.Settings.getBoolean('scraping.termination.enabled') and (self.terminationMode == 0 or self.terminationMode == 3 or (self.terminationMode == 1 and not autoplay) or (self.terminationMode == 2 and autoplay))
			self.terminationCount = tools.Settings.getInteger('scraping.termination.count')
			self.terminationType = tools.Settings.getInteger('scraping.termination.type')
			self.terminationVideoQuality = tools.Settings.getInteger('scraping.termination.video.quality')
			self.terminationVideoCodec = tools.Settings.getInteger('scraping.termination.video.codec')
			self.terminationAudioChannels = tools.Settings.getInteger('scraping.termination.audio.channels')
			self.terminationAudioCodec = tools.Settings.getInteger('scraping.termination.audio.codec')

			terminationTemporary = {}
			if self.terminationType in [1, 4, 5, 7]:
				terminationTemporary['premium'] = True
			if self.terminationType in [2, 4, 6, 7]:
				terminationTemporary['cache'] = True
			if self.terminationType in [3, 5, 6, 7]:
				terminationTemporary['direct'] = True
			self.terminationType = terminationTemporary
			self.terminationTypeHas = len(self.terminationType) > 0

			terminationTemporary = []
			if self.terminationVideoQuality > 0:
				for i in range(self.terminationVideoQuality - 1, len(metadatax.Metadata.VideoQualityOrder)):
					terminationTemporary.append(metadatax.Metadata.VideoQualityOrder[i])
			self.terminationVideoQuality = terminationTemporary
			self.terminationVideoQualityHas = len(self.terminationVideoQuality) > 0

			terminationTemporary = []
			if self.terminationVideoCodec > 0:
				if self.terminationVideoCodec in [1, 3]:
					terminationTemporary.append('H264')
				if self.terminationVideoCodec in [1, 2]:
					terminationTemporary.append('H265')
			self.terminationVideoCodec = terminationTemporary
			self.terminationVideoCodecHas = len(self.terminationVideoCodec) > 0

			terminationTemporary = []
			if self.terminationAudioChannels > 0:
				if self.terminationAudioChannels in [1, 2]:
					terminationTemporary.append('8CH')
				if self.terminationAudioChannels in [1, 3]:
					terminationTemporary.append('6CH')
				if self.terminationAudioChannels in [4]:
					terminationTemporary.append('2CH')
			self.terminationAudioChannels = terminationTemporary
			self.terminationAudioChannelsHas = len(self.terminationAudioChannels) > 0

			terminationTemporary = []
			if self.terminationAudioCodec > 0:
				if self.terminationAudioCodec in [1, 2, 3]:
					terminationTemporary.append('DTS')
				if self.terminationAudioCodec in [1, 2, 4]:
					terminationTemporary.append('DD')
				if self.terminationAudioCodec in [1, 5]:
					terminationTemporary.append('AAC')
			self.terminationAudioCodec = terminationTemporary
			self.terminationAudioCodecHas = len(self.terminationAudioCodec) > 0

			# Limit the number of running threads.
			# Can be more than actual core count, since threads in python are run on a single core.
			# Do not use too many, otherwise Kodi begins lagging (eg: the dialog is not updated very often, and the elapsed seconds are stuck).
			# NB: Do not use None (aka unlimited). If 500+ links are found, too many threads are started, causing a major delay by having to switch between threads. Use a limited number of threads.
			self.threadsLimit = tools.Hardware.processors() * 2

			enabledPremiumize = debridx.Premiumize().accountValid() and (tools.Settings.getBoolean('streaming.torrent.premiumize.enabled') or tools.Settings.getBoolean('streaming.usenet.premiumize.enabled'))
			enabledOffCloud = debridx.OffCloud().accountValid() and (tools.Settings.getBoolean('streaming.torrent.offcloud.enabled') or tools.Settings.getBoolean('streaming.usenet.offcloud.enabled'))
			enabledRealDebrid = debridx.RealDebrid().accountValid() and tools.Settings.getBoolean('streaming.torrent.realdebrid.enabled')

			control.makeFile(control.dataPath)
			self.sourceFile = control.providercacheFile

			self.titleLanguages = {}
			self.titleAlternatives = {}
			self.titleLocal = None
			self.titleAliases = []
			self.titleOriginal = None
			self.titleAbbreviation = None
			self.titleForeign1 = None
			self.titleForeign2 = None
			self.titleUmlaut1 = None
			self.titleUmlaut2 = None

			self.enabledProviders = tools.Settings.getBoolean('interface.navigation.scrape.providers')
			self.enabledDevelopers = tools.System.developers()
			self.enabledForeign = tools.Settings.getBoolean('scraping.foreign.enabled')
			self.enabledPrecheck = self.enabledDevelopers and tools.Settings.getBoolean('scraping.precheck.enabled')
			self.enabledMetadata = self.enabledDevelopers and tools.Settings.getBoolean('scraping.metadata.enabled')
			self.enabledCache = tools.Settings.getBoolean('scraping.cache.enabled') and ((enabledPremiumize and tools.Settings.getBoolean('scraping.cache.premiumize')) or (enabledOffCloud and tools.Settings.getBoolean('scraping.cache.offcloud')) or (enabledRealDebrid and tools.Settings.getBoolean('scraping.cache.realdebrid')))
			self.enabledFailures = provider.Provider.failureEnabled()

			self.progressInformationLanguage = 0
			self.progressInformationCharacters = 0
			self.progressPercentage = 0
			self.progressCache = 0

			percentageDone = 0
			percentageInitialize = 0.05
			percentageForeign = 0.05 if self.enabledForeign else 0
			percentagePrecheck = 0.15 if self.enabledPrecheck else 0
			percentageMetadata = 0.15 if self.enabledMetadata else 0
			percentageCache = 0.05 if self.enabledCache else 0
			percentageFinalizingStreams = 0.03
			percentageSaveStreams = 0.02
			percentageProviders = 1 - percentageInitialize - percentageForeign - percentagePrecheck - percentageMetadata - percentageCache - percentageFinalizingStreams - percentageSaveStreams - 0.01 # Subtract 0.01 to keep the progress bar always a bit empty in case provided sources something like 123 of 123, even with threads still running.

			self.mLastName = interface.Dialog.title(extension = '', bold = False)
			self.mLastMessage1 = ''
			self.mLastMessage2 = ''

			timer = tools.Time()
			timerSingle = tools.Time()
			timeStep = 0.5
			timeString = '%s ' + control.lang(32405).encode('utf-8')
			timeStringDescription = control.lang(32404).encode('utf-8') + ': ' + timeString

			heading = 'Stream Search'
			message = 'Initializing Providers'
			_progressShow(title = heading, message = message, metadata = metadata)
			interface.Loader.hide()

			timer.start()
			# Ensures that the elapsed time in the dialog is updated more frequently.
			# Otherwise the update is laggy if many threads run.
			timeThread = workers.Thread(_progressTime)
			timeThread.start()

			title = titleClean(title)
			tvshowtitle = titleClean(tvshowtitle)
			movie = tvshowtitle == None if self.type == None else (self.type == tools.Media.TypeMovie or self.type == self.type == tools.Media.TypeDocumentary or self.type == self.type == tools.Media.TypeShort)

			# Clear old sources from database.
			# Due to long links and metadata, the database entries can grow very large, not only wasting disk space, but also reducing search/insert times.
			# Delete old entries that will be ignored in any case.
			self.clearSourcesOld(wait = False)

			message = 'Initializing Providers'
			_progressUpdate(0, message)

			scrapingContinue = True
			scrapingExcludeOrion = False
			orion = orionoid.Orionoid()
			if orion.accountEnabled():
				orionScrapingMode = orion.settingsScrapingMode()
				tools.Logger.log('Launching Orion: ' + str(orionScrapingMode), name = 'CORE', level = tools.Logger.TypeNotice)
				if orionScrapingMode == orionoid.Orionoid.ScrapingExclusive or orionScrapingMode == orionoid.Orionoid.ScrapingSequential:
					tools.Logger.log('Starting Orion', name = 'CORE', level = tools.Logger.TypeNotice)
					timeout = orion.settingsScrapingTimeout()
					percentageOrion = 0.1
					percentageProviders -= percentageOrion
					message = 'Searching Orion'
					self.providersBusy = 1
					self.providersLabels = [orion.Name]

					provider.Provider.initialize(forceAll = True, special = True)
					providerOrion = provider.Provider.provider(orionoid.Orionoid.Scraper, enabled = False)
					if providerOrion and providerOrion['selected']:
						tools.Logger.log('Scraping Orion', name = 'CORE', level = tools.Logger.TypeNotice)
						threadOrion = None
						if movie:
							title = cleantitle.normalize(title)
							threadOrion = workers.Thread(self.scrapeMovie, title, self.titleLocal, self.titleAliases, year, imdb, providerOrion, exact)
						else:
							tvshowtitle = cleantitle.normalize(tvshowtitle)
							threadOrion = workers.Thread(self.scrapeEpisode, title, self.titleLocal, self.titleAliases, year, imdb, tvdb, season, episode, seasoncount, tvshowtitle, premiered, providerOrion, exact)

						threadOrion.start()
						timerSingle.start()
						while True:
							try:
								if self.progressCanceled(): break
								if not threadOrion.is_alive(): break
								_progressUpdate(int((min(1, timerSingle.elapsed() / float(timeout))) * percentageOrion * 100), message)
								time.sleep(timeStep)
							except:
								pass
						del threadOrion

					if orionScrapingMode == orionoid.Orionoid.ScrapingExclusive:
						scrapingContinue = False
					elif orionScrapingMode == orionoid.Orionoid.ScrapingSequential:
						if orion.streamsCount(self.sourcesAdjusted) < orion.settingsScrapingCount(): scrapingExcludeOrion = True
						else: scrapingContinue = False
				self.providersLabels = None

			if scrapingContinue:
				# Start the additional information before the providers are intialized.
				# Save some search time. Even if there are no providers available later, still do this.
				threadAdditional = None
				if not exact and not self.progressCanceled() and self.enabledForeign:
					threadAdditional = workers.Thread(additionalInformation, title, tvshowtitle, imdb, tvdb)
					threadAdditional.start()

				if not self.progressCanceled():
					timeout = 10
					message = 'Initializing Providers'
					thread = workers.Thread(initializeProviders, movie, preset, imdb, tvdb, [orionoid.Orionoid.Scraper] if scrapingExcludeOrion else None)

					thread.start()
					timerSingle.start()
					while True:
						try:
							if self.progressCanceled(): break
							if not thread.is_alive(): break
							_progressUpdate(int((min(1, timerSingle.elapsed() / float(timeout))) * percentageInitialize * 100), message)
							time.sleep(timeStep)
						except:
							tools.Logger.error()
							pass
					del thread

				if len(self.providers) == 0 and not self.progressCanceled():
					interface.Dialog.notification(message = 'No Providers Available', icon = interface.Dialog.IconError)
					self.stopThreads = True
					time.sleep(0.3) # Ensure the time thread (0.2 interval) is stopped.
					if len(self.sourcesAdjusted) == 0: return None # Orion found a few links, but not enough, causing other providers to be searched.
				elif self.progressCanceled():
					self.stopThreads = True
					time.sleep(0.3) # Ensure the time thread (0.2 interval) is stopped.
					return None

				_progressUpdate(int(percentageInitialize * 100), message) # In case the initialization finishes early.

				if not exact and not self.progressCanceled() and self.enabledForeign:
					percentageDone = percentageInitialize
					message = 'Retrieving Additional Information'
					try: timeout = tools.Settings.getInteger('scraping.foreign.timeout')
					except: timeout = 15

					timerSingle.start()
					while True:
						try:
							if self.progressCanceled(): break
							if not threadAdditional.is_alive(): break
							_progressUpdate(int((((self.progressInformationLanguage + self.progressInformationCharacters) / 2.0) * percentageForeign) + percentageDone), message)
							time.sleep(timeStep)
							if timerSingle.elapsed() >= timeout: break
						except: break
					del threadAdditional

					if self.progressCanceled():
						self.stopThreads = True
						time.sleep(0.3) # Ensure the time thread (0.2 interval) is stopped.
						return None

				if movie:
					title = cleantitle.normalize(title)
					for source in self.providers:
						threads.append(workers.Thread(self.scrapeMovieAlternatives, self.titleAlternatives, title, self.titleLocal, self.titleAliases, year, imdb, source, exact)) # Only language title for the first thread.
				else:
					tvshowtitle = cleantitle.normalize(tvshowtitle)
					for source in self.providers:
						threads.append(workers.Thread(self.scrapeEpisodeAlternatives, self.titleAlternatives, title, self.titleLocal, self.titleAliases, year, imdb, tvdb, season, episode, seasoncount, tvshowtitle, premiered, source, exact)) # Only language title for the first thread.

				sourceLabel = [i['label'] for i in self.providers]
				[i.start() for i in threads]

			# Finding Sources
			if not self.progressCanceled():
				percentageDone = percentageForeign + percentageInitialize
				message = 'Finding Stream Sources'
				stringInput1 = 'Processed Providers: %d of %d'
				stringInput2 = 'Providers: %d of %d'
				stringInput3 = interface.Format.newline() + 'Found Streams: %d'
				try: timeout = tools.Settings.getInteger('scraping.providers.timeout')
				except: timeout = 30
				termination = 0
				timerSingle.start()

				while True:
					try:
						if self.progressCanceled() or timerSingle.elapsed() >= timeout:
							break

						termination += 1
						if termination >= 4: # Every 2 secs.
							termination = 0
							if self.adjustTermination():
								self.termination = True
								break

						totalThreads = len(threads)
						self.providersLabels = []
						for x in range(totalThreads):
							if threads[x].is_alive():
								self.providersLabels.append(sourceLabel[x])
						self.providersBusy = len(self.providersLabels)
						self.providersFinished = totalThreads - self.providersBusy

						if self.providersBusy == 0:
							break

						foundStreams = []
						if len(foundStreams) < 2 and self.streamsHdUltra > 0: foundStreams.append('%sx HDULTRA' % self.streamsHdUltra)
						if len(foundStreams) < 2 and self.streamsHd1080 > 0: foundStreams.append('%sx HD1080' % self.streamsHd1080)
						if len(foundStreams) < 2 and self.streamsHd720 > 0: foundStreams.append('%sx HD720' % self.streamsHd720)
						if len(foundStreams) < 2 and self.streamsSd > 0: foundStreams.append('%sx SD' % self.streamsSd)
						if len(foundStreams) < 2 and self.streamsScr > 0: foundStreams.append('%sx SCR' % self.streamsScr)
						if len(foundStreams) < 2 and self.streamsCam > 0: foundStreams.append('%sx CAM' % self.streamsCam)
						if len(foundStreams) > 0: foundStreams = ' [%s]' % (', '.join(foundStreams))
						else: foundStreams = ''

						percentage = int((((self.providersFinished / float(totalThreads)) * percentageProviders) + percentageDone) * 100)
						stringProvidersValue1 = stringInput1 % (self.providersFinished, totalThreads)
						stringProvidersValue2 = stringInput2 % (self.providersFinished, totalThreads)
						if self.enabledProviders and len(self.providersLabels) <= 3: stringProvidersValue1 += ' [%s]' % (', '.join(self.providersLabels))
						stringProvidersValue1 += (stringInput3 % len(self.sourcesAdjusted)) + foundStreams
						_progressUpdate(percentage, message, stringProvidersValue1, stringProvidersValue2)

						time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

				# NB: Check in the end. In case the movie/episode is accessed on a subsequent run, it will be retrieved from the local cache database.
				# In such a case the early termination is not triggered.
				if self.adjustTermination():
					self.termination = True

			self.providersLabels = []

			# Special handle for cancel on scraping. Allows to still inspect debrid cache after cancellation.
			specialAllow = False
			if self.progressCanceled():
				specialAllow = True
				self.progressClose()
				tools.Time.sleep(0.2) # Important, otherwise close and open can clash.
				percentageDone = percentageForeign + percentageProviders + percentageInitialize
				message = 'Stopping Stream Collection'
				_progressShow(title = heading, message = message, metadata = metadata)
				_progressUpdate(percentageDone, message, ' ', ' ')

			# Failures
			# Do not detect failures if the scraping was canceled.
			if not self.progressCanceled() and self.enabledFailures:
				_progressUpdate(None, 'Detecting Provider Failures', ' ', ' ')
				threadsFinished = []
				threadsUnfinished = []
				for i in range(len(threads)):
					id = self.providers[i]['id']
					if threads[i].is_alive():
						threadsUnfinished.append(id)
					else:
						threadsFinished.append(id)
				provider.Provider.failureUpdate(finished = threadsFinished, unfinished = threadsUnfinished)

			del threads[:] # Make sure all providers are stopped.

			# Prechecks
			if (specialAllow or not self.progressCanceled()) and self.enabledPrecheck:
				percentageDone = percentageForeign + percentageProviders + percentageInitialize
				message = 'Checking Stream Availability'
				stringInput1 = 'Processed Streams: %d of %d'
				stringInput2 = 'Streams: %d of %d'
				try: timeout = tools.Settings.getInteger('scraping.precheck.timeout')
				except: timeout = 30
				timerSingle.start()

				while True:
					try:
						if self.progressCanceled():
							specialAllow = False
							break
						if timerSingle.elapsed() >= timeout:
							break

						totalThreads = self.cachedAdjusted + len(self.threadsAdjusted)
						aliveCount = len([x for x in self.threadsAdjusted if x.is_alive()])
						self.streamsFinished = self.cachedAdjusted + len([x for x in self.statusAdjusted if x == 'done'])
						self.streamsBusy = totalThreads - self.streamsFinished

						if aliveCount == 0:
							break

						percentage = int((((self.streamsFinished / float(totalThreads)) * percentagePrecheck) + percentageDone) * 100)
						stringSourcesValue1 = stringInput1 % (self.streamsFinished, totalThreads)
						stringSourcesValue2 = stringInput2 % (self.streamsFinished, totalThreads)
						_progressUpdate(percentage, message, stringSourcesValue1, stringSourcesValue2)

						time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

			# Metadata
			if (specialAllow or not self.progressCanceled()) and self.enabledMetadata:
				percentageDone = percentagePrecheck + percentageForeign + percentageProviders + percentageInitialize
				message = 'Retrieving Additional Metadata'
				stringInput1 = 'Processed Streams: %d of %d'
				stringInput2 = 'Streams: %d of %d'
				try: timeout = tools.Settings.getInteger('scraping.metadata.timeout')
				except: timeout = 30
				timerSingle.start()

				while True:
					try:
						if self.progressCanceled():
							specialAllow = False
							break
						if timerSingle.elapsed() >= timeout:
							break

						totalThreads = self.cachedAdjusted + len(self.threadsAdjusted)
						aliveCount = len([x for x in self.threadsAdjusted if x.is_alive()])
						self.streamsFinished = self.cachedAdjusted + len([x for x in self.statusAdjusted if x == 'done'])
						self.streamsBusy = totalThreads - self.streamsFinished

						if aliveCount == 0:
							break

						percentage = int((((self.streamsFinished / float(totalThreads)) * percentageMetadata) + percentageDone) * 100)
						stringSourcesValue1 = stringInput1 % (self.streamsFinished, totalThreads)
						stringSourcesValue2 = stringInput2 % (self.streamsFinished, totalThreads)
						_progressUpdate(percentage, message, stringSourcesValue1, stringSourcesValue2)

						time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

			# Finalizing Providers
			# Wait for all the source threads to complete.
			# This is especially important if there are not prechecks, metadata, or debrid cache inspection, and a provider finishes with a lot of streams just before the timeout.

			if specialAllow or not self.progressCanceled():
				percentageDone = percentageMetadata + percentagePrecheck + percentageForeign + percentageProviders + percentageInitialize
				message = 'Finalizing Stream Collection'
				stringInput1 = 'Processed Streams: %d of %d'
				stringInput2 = 'Streams: %d of %d'
				timeout = 60 # Can take some while for a lot of streams.
				timerSingle.start()

				while True:
					try:
						elapsedTime = timerSingle.elapsed()
						if self.progressCanceled() or elapsedTime >= timeout:
							break

						totalThreads = self.cachedAdjusted + len(self.threadsAdjusted)
						aliveCount = len([x for x in self.threadsAdjusted if x.is_alive()])
						self.streamsFinished = self.cachedAdjusted + len([x for x in self.statusAdjusted if x == 'done'])
						self.streamsBusy = totalThreads - self.streamsFinished

						if aliveCount == 0:
							break

						percentage = int((((elapsedTime / float(timeout)) * percentageFinalizingStreams) + percentageDone) * 100)
						stringSourcesValue1 = stringInput1 % (self.streamsFinished, totalThreads)
						stringSourcesValue2 = stringInput2 % (self.streamsFinished, totalThreads)
						_progressUpdate(percentage, message, stringSourcesValue1, stringSourcesValue2)

						time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

			# Debrid Cache
			if (specialAllow or not self.progressCanceled()) and self.enabledCache:
				percentageDone = percentageFinalizingStreams + percentageMetadata + percentagePrecheck + percentageForeign + percentageProviders + percentageInitialize
				message = 'Inspecting Debrid Cache'
				stringInput1 = ' ' # Must have space to remove line.
				stringInput2 = 'Inspecting Debrid Cache'
				try: timeout = tools.Settings.getInteger('scraping.cache.timeout')
				except: timeout = 30
				timerSingle.start()

				thread = workers.Thread(self.adjustSourceCache, timeout, False)
				thread.start()
				while True:
					try:
						elapsedTime = timerSingle.elapsed()
						if self.progressCanceled():
							specialAllow = False
							break
						if elapsedTime >= timeout:
							break
						if not thread.is_alive():
							self.adjustLock()
							remaining = self.progressCache
							self.adjustUnlock()
							if remaining == 0: break

						percentage = int((((elapsedTime / float(timeout)) * percentageCache) + percentageDone) * 100)
						_progressUpdate(percentage, message, stringInput1, stringInput2)

						time.sleep(timeStep)
					except:
						tools.Logger.error()
						break
				del thread

			# Finalizing Streams

			percentageDone = percentageFinalizingStreams + percentageMetadata + percentagePrecheck + percentageForeign + percentageProviders + percentageCache + percentageInitialize
			message = 'Saving Streams'
			stringInput1 = ' ' # Must have space to remove line.
			stringInput2 = 'Saving Streams'
			timeout = 15
			timerSingle.start()

			thread = workers.Thread(self.adjustSourceDatabase) # Update Database
			thread.start()

			if not self.progressCanceled(): # The thread is still running in the background, even if the dialog was canceled previously.
				while True:
					try:
						elapsedTime = timerSingle.elapsed()
						if not thread.is_alive():
							break
						if self.progressCanceled() or elapsedTime >= timeout:
							break

						percentage = int((((elapsedTime / float(timeout)) * percentageSaveStreams) + percentageDone) * 100)
						_progressUpdate(percentage, message, stringInput1, stringInput2)

						time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

			# Sources
			self.providers = []
			self.sources = self.sourcesAdjusted

			for i in range(len(self.sources)):
				source = self.sources[i]['source']
				if '.' in source:
					source = source.split('.')
					maximumLength = 0
					maximumString = ''
					for j in source:
						if len(j) > maximumLength:
							maximumLength = len(j)
							maximumString = j
					source = maximumString
				self.sources[i]['source'] = re.sub('\\W+', '', source)

				self.sources[i]['kids'] = self.kids
				self.sources[i]['type'] = self.type
				# Required by handler for selecting the correct episode from a season pack.
				# Do not use the name 'metadata', since that is checked in sourcesResolve().
				self.sources[i]['information'] = metadata

			self.stopThreads = True
			time.sleep(0.3) # Ensure the time thread (0.2 interval) is stopped.

			del self.threadsAdjusted[:] # Make sure all adjustments are stopped.
			self.sourcesAdjusted = [] # Do not delete, since the pointers are in self.sources now.

			# Postprocessing

			_progressUpdate(100, 'Preparing Streams', ' ', ' ', showElapsed = False)

			# Clear because member variable.
			self.threadsAdjusted = []
			self.sourcesAdjusted = []
			self.statusAdjusted = []
			self.priortityAdjusted = []

			return self.sources
		except:
			tools.Logger.error()
			return None

	def scrapeMovieAlternatives(self, alternativetitles, title, localtitle, aliases, year, imdb, source, exact):
		threads = []
		threads.append(workers.Thread(self.scrapeMovie, title, localtitle, aliases, year, imdb, source, exact))
		if not source['id'] == 'oriscrapers': # Do not scrape alternative titles for Orion.
			for key, value in alternativetitles.iteritems():
				threads.append(workers.Thread(self.scrapeMovie, value, localtitle, aliases, year, imdb, source, exact, key))
		[thread.start() for thread in threads]
		[thread.join() for thread in threads]

	def scrapeMovie(self, title, localtitle, aliases, year, imdb, source, exact, mode = None):
		connection = None
		try:
			# Replace symbols with spaces. Eg: K.C. Undercover
			try: title = re.sub('\s{2,}', ' ', re.sub('[^a-zA-Z\d\s:]', ' ', title)).strip()
			except: pass

			if localtitle == None: localtitle = title
			if mode == None: mode = ''
			sourceId = source['id']
			sourceObject = source['object']
			sourceType = source['type']
			sourceName = source['name']
			sourceLabel = source['label']
			sourceAddon = source['addon']
		except:
			pass

		try:
			try:
				connection, cursor = self.databaseOpen()
				cursor.execute("CREATE TABLE IF NOT EXISTS links (""source TEXT, ""mode TEXT, ""imdb TEXT, ""season TEXT, ""episode TEXT, ""link TEXT, ""UNIQUE(source, mode, imdb, season, episode)"");")
				cursor.execute("CREATE TABLE IF NOT EXISTS sources (""source TEXT, ""mode TEXT, ""imdb TEXT, ""season TEXT, ""episode TEXT, ""hosts TEXT, ""time INT, ""UNIQUE(source, mode, imdb, season, episode)"");")
			except: tools.Logger.error()
			finally: self.databaseClose(connection)
		except:
			pass

		try:
			if not sourceType == provider.Provider.TypeLocal:
				sources = []
				try:
					connection, cursor = self.databaseOpen()
					cursor.execute("SELECT * FROM sources WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (sourceId, mode, imdb, '', ''))
					match = cursor.fetchone()
				except: tools.Logger.error()
				finally: self.databaseClose(connection)
				t1 = int(match[6])
				t2 = tools.Time.timestamp()
				update = abs(t2 - t1) > 7200
				if update == False:
					sources = json.loads(match[5])
					self.addSources(sources, False)
					return sources
		except:
			pass

		try:
			url = None
			try:
				connection, cursor = self.databaseOpen()
				cursor.execute("SELECT * FROM links WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (sourceId, mode, imdb, '', ''))
				url = cursor.fetchone()
			except: tools.Logger.error()
			finally: self.databaseClose(connection)
			url = url[5]
		except:
			pass

		try:
			if url == None:
				try: url = sourceObject.movie(imdb, title, localtitle, year)
				except: url = sourceObject.movie(imdb, title, localtitle, aliases, year)
				if exact:
					try: url += '&exact=1'
					except: pass
				if url == None: raise Exception()
				try:
					connection, cursor = self.databaseOpen()
					cursor.execute("DELETE FROM links WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (sourceId, mode, imdb, '', ''))
					cursor.execute("INSERT INTO links VALUES (?, ?, ?, ?, ?, ?)", (sourceId, mode, imdb, '', '', url))
					connection.commit()
				finally: self.databaseClose(connection)
		except:
			pass

		try:
			sources = []
			sources = sourceObject.sources(url, self.hostDict, self.hostprDict)

			# In case the first domain fails, try the other ones in the domains list.
			if tools.System.developers() and tools.Settings.getBoolean('scraping.mirrors.enabled'):
				if (not sources or len(sources) == 0) and hasattr(sourceObject, 'domains') and hasattr(sourceObject, 'base_link'):
					checked = [sourceObject.base_link.replace('http://', '').replace('https://', '')]
					for domain in sourceObject.domains:
						if not domain in checked:
							if not domain.startswith('http'):
								domain = 'http://' + domain
							sourceObject.base_link = domain
							checked.append(domain.replace('http://', '').replace('https://', ''))
							sources = sourceObject.sources(url, self.hostDict, self.hostprDict)
							if len(sources) > 0:
								break

			if sources == None or sources == []:
				# Insert an empty list to avoid the provider being executed again if scraped multiple times.
				timestamp = tools.Time.timestamp()
				data = json.dumps([])
				try:
					connection, cursor = self.databaseOpen()
					cursor.execute("DELETE FROM sources WHERE source = '%s' AND mode = '%s' AND imdb = '%s'" % (sourceId, mode, imdb))
					cursor.execute("INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?)", (sourceId, mode, imdb, '', '', data, timestamp))
					connection.commit()
				except: tools.Logger.error()
				finally: self.databaseClose(connection)
				return

			try: titleadapted = '%s (%s)' % (title, year)
			except: pass

			invalid = []
			for i in range(len(sources)):
				try:
					# Add title which will be used by sourcesResolve()
					sources[i]['title'] = title
					sources[i]['titleadapted'] = titleadapted

					# Add provider.
					if 'origin' in sources[i]:
						sources[i]['providerid'] = provider.Provider.id(addon = sources[i]['origin'], provider = sources[i]['provider'])
						sources[i]['providerlabel'] = provider.Provider.label(addon = sources[i]['origin'], provider = sources[i]['provider'])
					else:
						sources[i]['providerid'] = sourceId
						sources[i]['providerlabel'] = sourceLabel
					if not 'provider' in sources[i] or sources[i]['provider'] == None:
						sources[i]['provider'] = sourceName

					# Add origin.
					if not 'origin' in sources[i]:
						sources[i]['origin'] = sourceAddon

					# Change language
					if 'language' in source and sources[i]['language']:
						sources[i]['language'] = sources[i]['language'].lower()

					# Update Google
					sources[i]['source'] = self.adjustRename(sources[i]['source'])

					# Exact
					sources[i]['exact'] = exact
				except:
					tools.Logger.error(str(sources[i]))
					invalid.append(i)
			sources = [i for j, i in enumerate(sources) if j not in invalid]

			databaseCache = {'source' : sourceId, 'mode' : mode, 'imdb' : imdb, 'season' : '', 'episode' : ''}
			for i in range(len(sources)):
				sources[i]['database'] = copy.deepcopy(databaseCache)
			self.addSources(sources, True)
		except:
			tools.Logger.error()

	def scrapeEpisodeAlternatives(self, alternativetitles, title, localtitle, aliases, year, imdb, tvdb, season, episode, seasoncount, tvshowtitle, premiered, source, exact):
		threads = []
		threads.append(workers.Thread(self.scrapeEpisode, title, localtitle, aliases, year, imdb, tvdb, season, episode, seasoncount, tvshowtitle, premiered, source, exact))
		if not source['id'] == 'oriscrapers': # Do not scrape alternative titles for Orion.
			for key, value in alternativetitles.iteritems():
				threads.append(workers.Thread(self.scrapeEpisode, title, localtitle, aliases, year, imdb, tvdb, season, episode, seasoncount, value, premiered, source, exact, key))
		[thread.start() for thread in threads]
		[thread.join() for thread in threads]

	def scrapeEpisode(self, title, localtitle, aliases, year, imdb, tvdb, season, episode, seasoncount, tvshowtitle, premiered, source, exact, mode = None):
		connection = None
		try:
			# Replace symbols with spaces. Eg: K.C. Undercover
			try: title = re.sub('\s{2,}', ' ', re.sub('[^a-zA-Z\d\s:]', ' ', title)).strip()
			except: pass
			try: tvshowtitle = re.sub('\s{2,}', ' ', re.sub('[^a-zA-Z\d\s:]', ' ', tvshowtitle)).strip()
			except: pass

			if localtitle == None: localtitle = title
			if mode == None: mode = ''
			sourceId = source['id']
			sourceObject = source['object']
			sourceType = source['type']
			sourceName = source['name']
			sourceLabel = source['label']
			sourceAddon = source['addon']
		except:
			pass

		try:
			try:
				connection, cursor = self.databaseOpen()
				cursor.execute("CREATE TABLE IF NOT EXISTS links (""source TEXT, ""mode TEXT, ""imdb TEXT, ""season TEXT, ""episode TEXT, ""link TEXT, ""UNIQUE(source, mode, imdb, season, episode)"");")
				cursor.execute("CREATE TABLE IF NOT EXISTS sources (""source TEXT, ""mode TEXT, ""imdb TEXT, ""season TEXT, ""episode TEXT, ""hosts TEXT, ""time INT, ""UNIQUE(source, mode, imdb, season, episode)"");")
			except: tools.Logger.error()
			finally: self.databaseClose(connection)
		except:
			pass

		try:
			if not sourceType == provider.Provider.TypeLocal:
				sources = []
				try:
					connection, cursor = self.databaseOpen()
					cursor.execute("SELECT * FROM sources WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (sourceId, mode, imdb, season, episode))
					match = cursor.fetchone()
				except: tools.Logger.error()
				finally: self.databaseClose(connection)
				t1 = int(match[6])
				t2 = tools.Time.timestamp()
				update = abs(t2 - t1) > 7200
				if update == False:
					sources = json.loads(match[5])
					self.addSources(sources, False)
					return sources
		except:
			pass

		try:
			url = None
			try:
				connection, cursor = self.databaseOpen()
				cursor.execute("SELECT * FROM links WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (sourceId, mode, imdb, '', ''))
				url = cursor.fetchone()
			except: tools.Logger.error()
			finally: self.databaseClose(connection)
			url = url[5]
		except:
			pass

		try:
			if url == None:
				try: url = sourceObject.tvshow(imdb, tvdb, tvshowtitle, localtitle, year)
				except: url = sourceObject.tvshow(imdb, tvdb, tvshowtitle, localtitle, aliases, year)
				if exact:
					try: url += '&exact=1'
					except: pass
				if url == None: raise Exception()
				try:
					connection, cursor = self.databaseOpen()
					cursor.execute("DELETE FROM links WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (sourceId, mode, imdb, '', ''))
					cursor.execute("INSERT INTO links VALUES (?, ?, ?, ?, ?, ?)", (sourceId, mode, imdb, '', '', url))
					connection.commit()
				finally: self.databaseClose(connection)
		except:
			pass

		try:
			ep_url = None
			try:
				connection, cursor = self.databaseOpen()
				cursor.execute("SELECT * FROM links WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (sourceId, mode, imdb, season, episode))
				ep_url = cursor.fetchone()
			except: tools.Logger.error()
			finally: self.databaseClose(connection)
			ep_url = ep_url[5]
		except:
			pass

		try:
			if url == None: raise Exception()
			if ep_url == None: ep_url = sourceObject.episode(url, imdb, tvdb, title, premiered, season, episode)
			if ep_url == None: return
			try:
				connection, cursor = self.databaseOpen()
				cursor.execute("DELETE FROM links WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (sourceId, mode, imdb, season, episode))
				cursor.execute("INSERT INTO links VALUES (?, ?, ?, ?, ?, ?)", (sourceId, mode, imdb, season, episode, ep_url))
				connection.commit()
			finally: self.databaseClose(connection)
		except:
			pass

		try:
			def _scrapeEpisode(url, mode, sourceId, sourceObject, sourceName, tvshowtitle, season, episode, imdb, currentSources, pack, packcount, exact):
				try:
					sources = []
					sources = sourceObject.sources(url, self.hostDict, self.hostprDict)

					# In case the first domain fails, try the other ones in the domains list.
					if tools.System.developers() and tools.Settings.getBoolean('scraping.mirrors.enabled'):
						if (not sources or len(sources) == 0) and hasattr(sourceObject, 'domains') and hasattr(sourceObject, 'base_link'):
							checked = [sourceObject.base_link.replace('http://', '').replace('https://', '')]
							for domain in sourceObject.domains:
								if not domain in checked:
									if not domain.startswith('http'):
										domain = 'http://' + domain
									sourceObject.base_link = domain
									checked.append(domain.replace('http://', '').replace('https://', ''))
									sources = sourceObject.sources(url, self.hostDict, self.hostprDict)
									if len(sources) > 0:
										break

					if sources == None or sources == []:
						# Insert an empty list to avoid the provider being executed again if scraped multiple times.
						timestamp = tools.Time.timestamp()
						data = json.dumps([])
						try:
							connection, cursor = self.databaseOpen()
							cursor.execute("DELETE FROM sources WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (sourceId, mode, imdb, season, episode))
							cursor.execute("INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?)", (sourceId, mode, imdb, season, episode, data, timestamp))
							connection.commit()
						except: tools.Logger.error()
						finally: self.databaseClose(connection)
						return []

					try: titleadapted = '%s S%02dE%02d' % (tvshowtitle, int(season), int(episode))
					except: titleadapted = tvshowtitle

					invalid = []
					external = bool(re.search('^[a-zA-Z]{3}-', sourceId))
					for i in range(len(sources)):
						try:
							# Add title which will be used by sourceResolve()
							sources[i]['title'] = title
							sources[i]['tvshowtitle'] = tvshowtitle
							sources[i]['titleadapted'] = titleadapted
							sources[i]['season'] = season
							sources[i]['episode'] = episode

							# Set season pack
							# Only overwrite this value if not set by providers. Providers can set this value if it only supports season packs and not individual episodes (eg: Russian torrent).
							# Also used by orionscrapers.
							if not 'pack' in sources[i]: sources[i]['pack'] = pack
							if packcount: sources[i]['packcount'] = packcount

							# Add provider.
							if 'origin' in sources[i]:
								sources[i]['providerid'] = provider.Provider.id(addon = sources[i]['origin'], provider = sources[i]['provider'])
								sources[i]['providerlabel'] = provider.Provider.label(addon = sources[i]['origin'], provider = sources[i]['provider'])
							else:
								sources[i]['providerid'] = sourceId
								sources[i]['providerlabel'] = sourceLabel
							if not 'provider' in sources[i] or sources[i]['provider'] == None:
								sources[i]['provider'] = sourceName

							# Add origin.
							if not 'origin' in sources[i]:
								sources[i]['origin'] = sourceAddon

							# Change language
							sources[i]['language'] = sources[i]['language'].lower()

							# Update Google
							sources[i]['source'] = self.adjustRename(sources[i]['source'])

							# Exact
							sources[i]['exact'] = exact
						except:
							tools.Logger.error(str(sources[i]))
							invalid.append(i)
					sources = [i for j, i in enumerate(sources) if j not in invalid]

					databaseCache = {'source' : sourceId, 'mode' : mode, 'imdb' : imdb, 'season' : season, 'episode' : episode}
					for i in range(len(sources)):
						sources[i]['database'] = copy.deepcopy(databaseCache)

					self.addSources(sources, True)
				except:
					tools.Logger.error()
				return sources

			if ep_url == None: return

			if source['external']:
				new_url_encoded = ep_url
			else:
				try:
					new_url = urlparse.parse_qs(ep_url)
					new_url = dict([(i, new_url[i][0]) if new_url[i] else (i, '') for i in new_url])
					if seasoncount: new_url['packcount'] = seasoncount # Always add the packcount, for providers (eg: Russian torrents), that always use it.
				except:
					new_url = ep_url
				new_url_encoded = urllib.urlencode(new_url)

			# Get normal episodes
			currentSources = []
			currentSources += _scrapeEpisode(new_url_encoded, mode, sourceId, sourceObject, sourceName, tvshowtitle, season, episode, imdb, currentSources, False, seasoncount, exact)

			# Get season packs
			if tools.Settings.getBoolean('scraping.packs.enabled') and source['pack'] and not source['external']:
				try:
					new_url['pack'] = True
					new_url_encoded = urllib.urlencode(new_url)
					_scrapeEpisode(new_url_encoded, mode, sourceId, sourceObject, sourceName, tvshowtitle, season, episode, imdb, currentSources, True, seasoncount, exact)
				except:
					tools.Logger.error()
		except:
			tools.Logger.error()

	def addLink(self, link = None, extras = None, metadata = None):
		if link == None: link = interface.Dialog.input(title = 35434)
		if link == None or link == '': return None

		if metadata == None:
			metadata = window.Window.propertyGlobal(self.propertyMeta)
			metadata = tools.Converter.jsonFrom(metadata)
		elif isinstance(metadata, basestring):
			metadata = tools.Converter.jsonFrom(urllib.unquote(metadata))

		try: title = metadata['tvshowtitle']
		except:
			try: title = metadata['title']
			except: title = None
		try: year = metadata['year']
		except: year = None
		try: season = metadata['season']
		except: season = None
		try: episode = metadata['episode']
		except: episode = None

		try:
			container = network.Container(link)
			if container.torrentIs(): source = 'torrent'
			elif container.usenetIs(): source = 'usenet'
			else: source = network.Networker.linkDomain(link).lower()
		except: source = 'custom'

		item = {}
		item['custom'] = True
		item['quality'] = 'HDULTRA'
		item['url'] = link
		item['origin'] = None
		item['source'] = source
		item['provider'] = 'Custom'
		item['providerlabel'] = 'Custom'
		item['providerid'] = 'custom'
		item['external'] = False
		item['pack'] = False
		item['direct'] = True
		item['local'] = True
		item['exact'] = False
		item['cache'] = {}
		item['debrid'] = {}
		try: item['title'] = metadata['title']
		except: pass
		try: item['tvshowtitle'] = metadata['tvshowtitle']
		except: pass

		meta = metadatax.Metadata(title = title, year = year, season = season, episode = episode, link = link)
		meta.setType(metadatax.Metadata.TypeLocal)
		meta.setVideoQuality(item['quality'], direct = True)
		item['metadata'] = meta

		if not self.navigationStreamsSpecial:
			infos = []
			infos.append('%s%s')

			layout = tools.Settings.getInteger('interface.information.layout')
			layoutType = tools.Settings.getInteger('interface.information.type')

			if layoutType > 0:
				if source == 'torrent': value = 'torrent'
				elif source == 'usenet': value = 'usenet'
				else: value = 'hoster'
				if layoutType == 1: value = value[:1]
				elif layoutType == 2: value = value[:3]
				infos.append(interface.Format.font(value, bold = True, color = interface.Format.ColorMain, uppercase = True))

			number = ''
			layoutNumber = tools.Settings.getInteger('interface.information.number')
			if layoutNumber == 1: number = '%01d'
			elif layoutNumber == 2: number = '%02d'
			elif layoutNumber == 3: number = '%03d'
			if not number == '': number = interface.Format.font(number, bold = True, translate = False)

			infos.append(interface.Format.font(35233, bold = True, uppercase = True, color = interface.Format.ColorOrion))
			item['label'] = item['file'] = (interface.Format.separator().join(infos) % (number % 0, '')) + (interface.Format.newline() if layout == 2 else '') + link

		if extras == None:
			extras = window.Window.propertyGlobal(self.propertyExtras)
			extras = tools.Converter.jsonFrom(extras)
		elif isinstance(extras, basestring):
			extras = tools.Converter.jsonFrom(urllib.unquote(extras))
		if not extras: extras = []
		extras.append(item)
		extras = self.sourcesPrepare(items = extras)

		jsonExtras = copy.deepcopy(extras)
		for i in range(len(jsonExtras)):
			metadatax.Metadata.uninitialize(jsonExtras[i])
		window.Window.propertyGlobalSet(self.propertyExtras, tools.Converter.jsonTo(jsonExtras))

		self.showStreams(extras = extras, metadata = metadata, autoplay = False, add = True)

	def showFilters(self):
		interface.Filters.show()

	def showStreams(self, items = None, extras = None, metadata = None, direct = False, filter = True, autoplay = False, clear = False, library = False, initial = False, new = True, add = False, process = True):
		try:
			if clear: self._showClear()

			if self.navigationScrapeDialog and self.navigationStreamsDirectory:
				# Important to close here and not later.
				self.progressClose(loader = self.navigationStreamsSpecial and new)

			if not direct and self.navigationStreamsDirectory:
				return self._showStreamsDirectory(filter = filter and new, autoplay = autoplay, library = library, initial = initial, new = new, add = add, process = process)

			if items == None:
				items = window.Window.propertyGlobal(self.propertyItems)
				items = tools.Converter.jsonFrom(items)
			elif isinstance(items, basestring):
				items = tools.Converter.jsonFrom(urllib.unquote(items))

			if extras == None:
				extras = window.Window.propertyGlobal(self.propertyExtras)
				extras = tools.Converter.jsonFrom(extras)
			elif isinstance(extras, basestring):
				extras = tools.Converter.jsonFrom(urllib.unquote(extras))

			if (items == None or len(items) == 0) and (extras == None or len(extras) == 0):
				if new: self.progressNotification(loader = True)
				return False

			if metadata == None:
				metadata = window.Window.propertyGlobal(self.propertyMeta)
				metadata = tools.Converter.jsonFrom(metadata)
			elif isinstance(metadata, basestring):
				metadata = tools.Converter.jsonFrom(urllib.unquote(metadata))

			itemsFiltered = []
			if items:
				for i in range(len(items)):
					metadatax.Metadata.initialize(source = items[i])
				if filter:
					if process: itemsFiltered = self.sourcesFilter(items = items, metadata = metadata, autoplay = autoplay)
					else: itemsFiltered = items
					if len(itemsFiltered) == 0:
						if not new or self.progressNotification():
							return self.showStreams(items = items, extras = extras, metadata = metadata, direct = True, library = library, filter = False, autoplay = False, clear = True, new = new, add = add)
						else:
							self.progressClose(force = True, loader = self.navigationStreamsSpecial and new)
							return False
				else:
					if process: itemsFiltered = self.sourcesFilter(items = items, metadata = metadata, apply = False, autoplay = False)
					else: itemsFiltered = items
				itemsFiltered = self.sourcesLabel(items = itemsFiltered, metadata = metadata)

			if extras:
				for i in range(len(extras)):
					metadatax.Metadata.initialize(source = extras[i])
				itemsFiltered = extras + itemsFiltered

			if autoplay:
				result = self._showAutoplay(items = itemsFiltered, metadata = metadata)
				if result:
					self.progressClose(force = True)
					return result
				else:
					return self.showStreams(items = items, extras = extras, metadata = metadata, direct = True, library = library, filter = False, autoplay = False, clear = True, new = new, add = add)

			if self.navigationStreamsDialog:
				if new: self.progressNotification()
				result = self._showStreamsDialog(items = itemsFiltered, metadata = metadata)
			else:
				result = self._showStreams(items = itemsFiltered, metadata = metadata, initial = initial, library = library, add = add)
				if new: self.progressNotification()

			self.progressClose(force = True, loader = self.navigationStreamsSpecial and new)
			return result
		except:
			tools.Logger.error()
			self.progressClose(force = True)
			return None

	def _showClear(self, filter = False, autoplay = False):
		interface.Filters.clear()

	def _showStreamsDirectory(self, filter = False, autoplay = False, library = False, initial = False, new = True, add = False, process = True):
		try:
			interface.Loader.show()
			tools.Time.sleep(0.2)
			# NB: Use "filterx" and not "filter" as parameters.
			# Otherwise for some weird reason the back button in the directory does not work.
			# Maybe Kodi uses that parameter name internally (eg: left side menu "Filter" option).
			command = '%s?action=streamsShow&direct=%d&filterx=%d&autoplay=%d&library=%d&initial=%d&new=%d&add=%d&process=%d' % (sys.argv[0], True, filter, autoplay, library, initial, new, add, process)
			command = self.parameterize(command)
			self.progressClose(force = True, loader = False) # Important to close to free up window memory, since Container.Update is in a separate process which does not know the window anymore.
			interface.Loader.show()
			if autoplay: result = tools.System.execute('RunPlugin(%s)' % command)
			else: result = tools.System.execute('Container.Update(%s)' % command)
			return result
		except:
			tools.Logger.error()
			return None

	def _showStreamsDialog(self, items, metadata):
		try:
			try: multi = 'meta' in items[0]
			except: multi = False

			if not multi:
				number = ''
				layoutNumber = tools.Settings.getInteger('interface.information.number')
				if layoutNumber == 1: number = '%01d'
				elif layoutNumber == 2: number = '%02d'
				elif layoutNumber == 3: number = '%03d'
				if not number == '': number = interface.Format.font(number, bold = True, translate = False) + interface.Format.fontSeparator()

			labels = []
			for i in range(len(items)):

				# Set from history where each item is from a differnt movie/show.
				try:
					extra = ''
					if multi:
						metadata = items[i]['meta']

						try: title = metadata['tvshowtitle']
						except:
							try: title = metadata['originaltitle']
							except:
								try: title = metadata['title']
								except: title = ''

						try: year = metadata['year']
						except: year = None
						try: season = metadata['season']
						except: season = None
						try: episode = metadata['episode']
						except: episode = None

						extra = interface.Format.font(tools.Media.title(metadata = metadata, title = title, year = year, season = season, episode = episode), bold = True, color = interface.Format.ColorOrion)
						if not self.navigationStreamsSpecial: extra += interface.Format.separator()
				except: pass

				label = items[i]['label']
				try: label = label % ('' if multi else number % (0 if 'custom' in items[i] and items[i]['custom'] else (i + 1)), extra)
				except: pass

				label = re.sub(' +', ' ', (label.replace(interface.Format.newline(), ' %s ' % interface.Format.separator()).strip()))
				labels.append(label)
			choice = control.selectDialog(labels)
			if choice < 0: return None
			self.play(items[choice], metadata = metadata)
			return None
		except:
			tools.Logger.error()
			return None

	def _showStreams(self, items = None, metadata = None, library = False, initial = False, add = False):
		metadataKodi = tools.Media.metadataClean(metadata)
		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		sysmeta = tools.Converter.quoteTo(tools.Converter.jsonTo(metadata))
		duration = self._duration(metadata)

		hasFanart = tools.Settings.getBoolean('interface.fanart')
		addonPoster = control.addonPoster()
		addonBanner = control.addonBanner()
		addonFanart = control.addonFanart()

		try: multi = 'meta' in items[0]
		except: multi = False

		if not multi:
			number = ''
			layoutNumber = tools.Settings.getInteger('interface.information.number')
			if layoutNumber == 1: number = '%01d'
			elif layoutNumber == 2: number = '%02d'
			elif layoutNumber == 3: number = '%03d'
			if not number == '': number = interface.Format.font(number, bold = True, translate = False) + interface.Format.fontSeparator()

		try: title = metadata['tvshowtitle']
		except:
			try: title = metadata['originaltitle']
			except:
				try: title = metadata['title']
				except: title = ''

		try: year = metadata['year']
		except: year = None
		try: season = metadata['season']
		except: season = None
		try: episode = metadata['episode']
		except: episode = None

		try: imdb = metadata['imdb']
		except: imdb = None
		try: tmdb = metadata['tmdb']
		except: tmdb = None
		try: tvdb = metadata['tvdb']
		except: tvdb = None

		try: poster = metadata['poster'] if 'poster' in metadata else metadata['poster2'] if 'poster2' in metadata else metadata['poster3'] if 'poster3' in metadata else None
		except: poster = None
		try: fanart = metadata['fanart'] if 'fanart' in metadata else metadata['fanart2'] if 'fanart2' in metadata else metadata['fanart3'] if 'fanart3' in metadata else None
		except: fanart = None
		try: banner = metadata['banner'] if 'banner' in metadata else None
		except: banner = None
		try: thumb = metadata['thumb'] if 'thumb' in metadata else poster
		except: thumb = None

		poster1 = metadata['poster'] if 'poster' in metadata else None
		poster2 = metadata['poster2'] if 'poster2' in metadata else None
		poster3 = metadata['poster3'] if 'poster3' in metadata else None

		if poster == '0' or poster == None: poster = addonPoster
		if banner == '0' or banner == None: banner = addonBanner if poster == '0' or poster == None else poster
		if thumb == '0' or thumb == None: thumb = addonFanart if fanart == '0' or fanart == None else fanart
		if not hasFanart or (fanart == '0' or fanart == None): fanart = addonFanart

		if self.navigationStreamsSpecial:
			window.WindowStreams.show(background = fanart, status = 'Loading Streams', close = not initial)

			window.Window.propertyGlobalSet('GaiaPosterStatic', tools.Settings.getInteger('interface.navigation.streams.poster') == 0)

			window.Window.propertyGlobalSet('GaiaColorOrion', interface.Format.ColorOrion)
			window.Window.propertyGlobalSet('GaiaColorPrimary', interface.Format.ColorPrimary)
			window.Window.propertyGlobalSet('GaiaColorSecondary', interface.Format.ColorSecondary)
			window.Window.propertyGlobalSet('GaiaColorMain', interface.Format.ColorMain)
			window.Window.propertyGlobalSet('GaiaColorDisabled', interface.Format.ColorDisabled)
			window.Window.propertyGlobalSet('GaiaColorAlternative', interface.Format.ColorAlternative)
			window.Window.propertyGlobalSet('GaiaColorSpecial', interface.Format.ColorSpecial)
			window.Window.propertyGlobalSet('GaiaColorUltra', interface.Format.ColorUltra)
			window.Window.propertyGlobalSet('GaiaColorExcellent', interface.Format.ColorExcellent)
			window.Window.propertyGlobalSet('GaiaColorGood', interface.Format.ColorGood)
			window.Window.propertyGlobalSet('GaiaColorMedium', interface.Format.ColorMedium)
			window.Window.propertyGlobalSet('GaiaColorPoor', interface.Format.ColorPoor)
			window.Window.propertyGlobalSet('GaiaColorBad', interface.Format.ColorBad)

			window.Window.propertyGlobalSet('GaiaColorHDULTRA', interface.Format.colorDarker(interface.Format.ColorUltra, 60))
			window.Window.propertyGlobalSet('GaiaColorHD8K', interface.Format.colorDarker(interface.Format.ColorUltra, 40))
			window.Window.propertyGlobalSet('GaiaColorHD6K', interface.Format.colorDarker(interface.Format.ColorUltra, 20))
			window.Window.propertyGlobalSet('GaiaColorHD4K', interface.Format.ColorUltra)
			window.Window.propertyGlobalSet('GaiaColorHD2K', interface.Format.colorLighter(interface.Format.ColorUltra, 20))
			window.Window.propertyGlobalSet('GaiaColorHD1080', interface.Format.ColorExcellent)
			window.Window.propertyGlobalSet('GaiaColorHD720', interface.Format.ColorGood)
			window.Window.propertyGlobalSet('GaiaColorSD480', interface.Format.ColorMedium)
			window.Window.propertyGlobalSet('GaiaColorSCR1080', interface.Format.colorLighter(interface.Format.ColorPoor, 40))
			window.Window.propertyGlobalSet('GaiaColorSCR720', interface.Format.colorLighter(interface.Format.ColorPoor, 20))
			window.Window.propertyGlobalSet('GaiaColorSCR480', interface.Format.ColorPoor)
			window.Window.propertyGlobalSet('GaiaColorCAM1080', interface.Format.colorLighter(interface.Format.ColorBad, 40))
			window.Window.propertyGlobalSet('GaiaColorCAM720', interface.Format.colorLighter(interface.Format.ColorBad, 20))
			window.Window.propertyGlobalSet('GaiaColorCAM480', interface.Format.ColorBad)
		else:
			icons = tools.Settings.getInteger('interface.navigation.streams.icons')

		enabledCache = tools.Settings.getBoolean('downloads.cache.enabled')
		controls = []
		contexts = []
		total = len(items)

		for i in range(total):
			try:
				extra = ''
				itemJson = items[i]
				meta = itemJson['metadata']
				metadatax.Metadata.uninitialize(itemJson)
				syssource = tools.Converter.quoteTo(tools.Converter.jsonTo(itemJson))
				try: orion = itemJson['orion']
				except: orion = None

				# Set from history where each item is from a differnt movie/show.
				try:
					if multi:
						metadata = itemJson['meta']
						metadataKodi = tools.Media.metadataClean(metadata)
						sysmeta = urllib.quote_plus(json.dumps(metadata))
						duration = self._duration(metadata)

						try: title = metadata['tvshowtitle']
						except:
							try: title = metadata['originaltitle']
							except:
								try: title = metadata['title']
								except: title = ''

						try: year = metadata['year']
						except: year = None
						try: season = metadata['season']
						except: season = None
						try: episode = metadata['episode']
						except: episode = None

						try: imdb = metadata['imdb']
						except: imdb = None
						try: tmdb = metadata['tmdb']
						except: tmdb = None
						try: tvdb = metadata['tvdb']
						except: tvdb = None

						extra = interface.Format.font(tools.Media.title(metadata = metadata, title = title, year = year, season = season, episode = episode), bold = True, color = interface.Format.ColorOrion)
						if not self.navigationStreamsSpecial: extra += interface.Format.separator()

						try: poster = metadata['poster'] if 'poster' in metadata else metadata['poster2'] if 'poster2' in metadata else metadata['poster3'] if 'poster3' in metadata else None
						except: poster = None
						try: fanart = metadata['fanart'] if 'fanart' in metadata else metadata['fanart2'] if 'fanart2' in metadata else metadata['fanart3'] if 'fanart3' in metadata else None
						except: fanart = None
						try: banner = metadata['banner'] if 'banner' in metadata else None
						except: banner = None
						try: thumb = metadata['thumb'] if 'thumb' in metadata else poster
						except: thumb = None

						poster1 = metadata['poster'] if 'poster' in metadata else None
						poster2 = metadata['poster2'] if 'poster2' in metadata else None
						poster3 = metadata['poster3'] if 'poster3' in metadata else None

						if poster == '0' or poster == None: poster = addonPoster
						if banner == '0' or banner == None: banner = addonBanner if poster == '0' or poster == None else poster
						if thumb == '0' or thumb == None: thumb = addonFanart if fanart == '0' or fanart == None else fanart
						if not hasFanart or (fanart == '0' or fanart == None): fanart = addonFanart
				except:
					tools.Logger.error()

				# ACTION URL.
				if not meta.local() and enabledCache: url = '%s?action=playCache&handleMode=%s&source=%s&metadata=%s' % (sysaddon, handler.Handler.ModeDefault, syssource, sysmeta)
				else: url = '%s?action=play&handleMode=%s&source=%s&metadata=%s' % (sysaddon, handler.Handler.ModeDefault, syssource, sysmeta)
				url = self.parameterize(url)
				sysurl = tools.Converter.quoteTo(url)

				# ITEM
				if self.navigationStreamsSpecial:
					label = ''
					icon = thumb
				else:
					label = itemJson['label']
					try: label = label % ('' if multi else number % (0 if 'custom' in itemJson and itemJson['custom'] else (i + 1)), extra)
					except: pass
					if multi:
						icon = thumb
					else:
						if icons == 0: icon = ''
						elif icons == 1: icon = thumb
						else:
							quality = meta.videoQuality().lower()
							if quality == 'sd' or quality == 'scr' or quality == 'cam': quality += '480'
							icon = thumb = interface.Icon.path(icon = 'quality' + quality, quality = interface.Icon.QualityLarge, special = interface.Icon.SpecialQuality if icons == 3 else interface.Icon.SpecialNone)

				item = control.item(label = label)
				art = {'icon': icon, 'thumb': thumb, 'poster': poster, 'banner': banner}
				item.setArt(art)
				if not fanart == None: item.setProperty('Fanart_Image', fanart)

				# NB: Needed to transfer the addon handle ID to play
				# https://forum.kodi.tv/showthread.php?tid=328080
				#item.setProperty('IsPlayable', 'true') # Causes popup dialog from Kodi if playback was unsuccesful.

				item.setInfo(type = 'Video', infoLabels = metadataKodi)
				if meta:
					width, height = meta.videoQuality(True)
					item.addStreamInfo('video', {'codec': meta.videoCodec(kodi = True), 'width' : width, 'height': height})
					item.addStreamInfo('audio', {'codec': meta.audioSystemCodec(kodi = True), 'channels': meta.audioChannels(number = True)})

				# SPECIAL WINDOW
				if self.navigationStreamsSpecial:
					link = meta.link()
					try: name = meta.name()
					except: name = None
					if not name and meta.isTorrent():
						container = network.Container(meta.link())
						name = container.torrentName()
						if not name and container.torrentIsMagnet(): name = ''
						elif not name: name = link
					elif not name:
						name = link
					hoster = None if itemJson['source'].lower() == itemJson['providerlabel'].lower() else itemJson['source'] if meta.isHoster() else None
					provider = window.WindowStreams.separator([meta.labelOrion(), interface.Format.font(itemJson['providerlabel'], uppercase = True, bold = True), interface.Format.font(hoster, uppercase = True, bold = True)], color = True)
					stream = window.WindowStreams.separator([extra if extra else None, meta.labelOrion(), interface.Format.font(itemJson['providerlabel'], uppercase = True, bold = True), interface.Format.font(hoster, uppercase = True, bold = True)], color = True)
					access = metadatax.Metadata.labelFill(window.WindowStreams.separator([meta.labelDirect(), meta.labelCached(), meta.labelDebrid(), meta.labelOpen()], color = True))
					info = metadatax.Metadata.labelFill(window.WindowStreams.separator([meta.labelType(), meta.labelAccess()], color = True))
					metas = metadatax.Metadata.labelFill(window.WindowStreams.separator([meta.labelEdition(), meta.labelPack(), meta.labelRelease(), meta.labelUploader()], color = True))
					video = metadatax.Metadata.labelFill(window.WindowStreams.separator([meta.videoQuality(), meta.videoCodec(), meta.labelVideoExtra()], color = True))
					subtitles = metadatax.Metadata.labelFill(meta.labelSubtitles())
					size = metadatax.Metadata.labelFill(meta.size(format = True, color = True, estimate = True, duration = duration))
					popularity = metadatax.Metadata.labelFill(meta.popularity(format = True, color = True, label = metadatax.Metadata.LabelShort))
					age = metadatax.Metadata.labelFill(meta.age(format = True, color = True, label = metadatax.Metadata.LabelFull))
					seeds = metadatax.Metadata.labelFill(meta.seeds(format = True, color = True, label = metadatax.Metadata.LabelFull))

					countries = []
					languages = meta.audioLanguages()
					audio = window.WindowStreams.separator([meta.audioChannels(), meta.audioSystemCodec(), meta.labelAudioDubbed()], color = True)
					audioHas = True if audio else False
					audio = language = metadatax.Metadata.labelFill(audio)
					if len(languages) > 0:
						if audioHas: language += window.WindowStreams.separator(color = True)
						else: language = None
					for j in range(len(languages)):
						country = tools.Language.country(languages[j])
						if not country in countries:
							countries.append(country)
							item.setProperty('AudioFlag' + str(j + 1), country)

					item.setProperty('GaiaPoster1', poster1 if poster1 else '')
					item.setProperty('GaiaPoster2', poster2 if poster2 else '')
					item.setProperty('GaiaPoster3', poster3 if poster3 else '')

					item.setProperty('GaiaAction', url)
					item.setProperty('GaiaNumber', str(i + 1))
					item.setProperty('GaiaExtra', extra)
					item.setProperty('GaiaType', meta.type())
					item.setProperty('GaiaOrion', str(int(meta.orion())))
					item.setProperty('GaiaProvider', provider)
					item.setProperty('GaiaStream', stream)
					item.setProperty('GaiaPopularity', popularity)
					item.setProperty('GaiaAge', age)
					item.setProperty('GaiaSeeds', seeds)
					item.setProperty('GaiaMeta', metas)
					item.setProperty('GaiaName', name)
					item.setProperty('GaiaSize', size)
					item.setProperty('GaiaAccess', access)
					item.setProperty('GaiaInfo', info)
					item.setProperty('GaiaVideo', video)
					item.setProperty('GaiaQuality', meta.videoQuality())
					item.setProperty('GaiaAudio', audio)
					item.setProperty('GaiaLanguage', language)
					item.setProperty('GaiaSubtitles', subtitles)

				# CONTEXT
				context = interface.Context(mode = interface.Context.ModeStream, type = self.type, kids = self.kids, create = True, queue = True, source = syssource, metadata = sysmeta, art = art, orion = orion, link = url, label = label, title = title, year = year, season = season, episode = episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb)

				# ADD ITEM
				if self.navigationStreamsSpecial:
					contexts.append(context)
					controls.append(item)
					window.WindowStreams.update(progress = i / float(total))
				else:
					item.addContextMenuItems([context.menu()])
					controls.append([url, item, False])
			except:
				tools.Logger.error()

		if self.navigationStreamsSpecial:
			window.WindowStreams.itemAdd(item = controls, context = contexts)
			window.WindowStreams.update(finished = True)
			window.WindowStreams.focus()
		else:
			control.addItems(handle = syshandle, items = controls)
			control.content(syshandle, 'files')
			control.directory(syshandle, cacheToDisc = True, updateListing = not initial)
			self.progressClose(force = True, loader = (add or self.navigationScrapeBar))

		# When launching from the local library, Kodi shows an OK dialog and/or a notification stating that the item couldn't be played, or that it coudln't find the next item in the playlist.
		# These popups happen random and sometimes not at all. It probably depends on the time it takes to scrape/launch Gaia.
		# There seems to be nothing that can be done about these popups, except closing them automatically.
		if library:
			def closePopups():
				for i in range(30): # Don't make this too large, otherwise the Gaia stream notification takes too long to show. 20 is too low.
					interface.Dialog.closeOk()
					interface.Dialog.closeNotification()
					tools.Time.sleep(0.05)
				self.progressNotification(force = True) # Reopen.
			thread = threading.Thread(target = closePopups)
			thread.start()

	def _showAutoplay(self, items, metadata):
		filter = [i for i in items if i['source'].lower() in self.hostcapDict and not any(j for j in i['debrid'].itervalues())]
		items = [i for i in items if not i in filter]

		filter = [i for i in items if i['source'].lower() in self.hostblockDict and not any(j for j in i['debrid'].itervalues())]
		items = [i for i in items if not i in filter]

		items = [i for i in items if ('autoplay' in i and i['autoplay'] == True) or not 'autoplay' in i]

		imdb = metadata['imdb'] if 'imdb' in metadata else None
		tmdb = metadata['tmdb'] if 'tmdb' in metadata else None
		tvdb = metadata['tvdb'] if 'tvdb' in metadata else None

		title = metadata['title'] if 'title' in metadata else None
		year = metadata['year'] if 'year' in metadata else None
		season = metadata['season'] if 'season' in metadata else None
		episode = metadata['episode'] if 'episode' in metadata else None

		autoHandler = handler.Handler()
		heading = interface.Translation.string(33451)
		message = interface.Translation.string(33452)
		self.progressPlaybackInitialize(title = heading, message = message, metadata = metadata)

		for i in range(len(items)):
			if self.progressPlaybackCanceled(): break
			percentage = int(((i + 1) / float(len(items))) * 100)
			self.progressPlaybackUpdate(progress = percentage, title = heading, message = message)
			try:
				handle = autoHandler.serviceDetermine(mode = handler.Handler.ModeDefault, item = items[i], popups = False)
				if not handle == handler.Handler.ReturnUnavailable:
					result = self.sourcesResolve(items[i], handle = handle, info = False)
					items[i]['urlresolved'] = result['link']
					items[i]['stream'] = result
					if result['success']:
						if self.progressPlaybackCanceled(): break
						from resources.lib.modules.player import player
						player(type = self.type, kids = self.kids).run(self.type, title, year, season, episode, imdb, tmdb, tvdb, items[i]['urlresolved'], metadata, handle = handle, source = items[i])
						return items[i]
			except:
				tools.Logger.error()

		self.progressPlaybackClose()
		interface.Dialog.notification(title = 33448, message = 33574, sound = False, icon = interface.Dialog.IconInformation)
		return None

	def _duration(self, metadata):
		try: return int(metadata['duration'])
		except: return 1800 if 'episode' in metadata else 7200

	def play(self, source, metadata = None, downloadType = None, downloadId = None, handle = None, handleMode = None, index = None):
		try:
			self.downloadCanceled = False

			sequential = tools.Settings.getBoolean('general.playback.sequential.enabled')
			if sequential:
				items = json.loads(control.window.getProperty(self.propertyItems))
				if index == None:
					for i in range(len(items)):
						if items[i]['url'] == source['url']:
							index = i
							break
				try:
					source = items[index]
				except:
					tools.Logger.error()
					self.progressClose(force = True)
					return

			try:
				if metadata == None:
					metadata = control.window.getProperty(self.propertyMeta)
					metadata = json.loads(metadata)

				year = metadata['year'] if 'year' in metadata else None
				season = metadata['season'] if 'season' in metadata else None
				episode = metadata['episode'] if 'episode' in metadata else None

				imdb = metadata['imdb'] if 'imdb' in metadata else None
				tmdb = metadata['tmdb'] if 'tmdb' in metadata else None
				tvdb = metadata['tvdb'] if 'tvdb' in metadata else None
			except:
				if not metadata == None: metadata = None
				year = None
				season = None
				episode = None
				imdb = None
				tmdb = None
				tvdb = None

			title = source['tvshowtitle'] if 'tvshowtitle' in source else source['title']
			next = []
			prev = []
			total = []
			for i in range(1,1000):
				try:
					u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
					if u in total: raise Exception()
					total.append(u)
					u = dict(urlparse.parse_qsl(u.replace('?','')))
					u = json.loads(u['source'])[0]
					next.append(u)
				except:
					break
			for i in range(-1000,0)[::-1]:
				try:
					u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
					if u in total: raise Exception()
					total.append(u)
					u = dict(urlparse.parse_qsl(u.replace('?','')))
					u = json.loads(u['source'])[0]
					prev.append(u)
				except:
					break

			try:
				item = source
				if isinstance(item, list):
					item = item[0]

				heading = interface.Translation.string(33451)
				message = interface.Translation.string(33452)

				if handle == None and (not 'local' in item or not item['local']):
					try: handle = handler.Handler().serviceDetermine(mode = handleMode, item = item, popups = True)
					except: handle = handler.Handler.ReturnUnavailable

					# Important for Incursion and Placenta providers that must be resolved first.
					if handle == handler.Handler.ReturnUnavailable:
						try:
							if not 'urlresolved' in item or item['urlresolved'] == None or item['urlresolved'] == '':
								url = item['url']
								found = False
								for i in [item['source'], item['source'].lower(), item['providerid'], item['provider'], item['provider'].lower()]:
									if i in self.externalServices:
										source = self.externalServices[i]['object']
										found = True
										break
								if not found:
									sourceObject = provider.Provider.provider(item['providerid'], enabled = False, local = True)
									if sourceObject:
										sourceObject = source['object']
									else:
										# force: get all providers in case of resolving for "disabled" preset providers. Or for historic links when the used providers were disabled.
										provider.Provider.initialize(forceAll = True)

										sourceObject = None
										descriptions = [item['providerid'], item['provider'], item['provider'].lower(), item['source'], item['source'].lower()]

										# Check external addons for old Orion items.
										descriptions = [item['provider'].lower(), item['source'].lower()]
										external = []
										for i in descriptions:
											if not bool(re.search('^[a-zA-Z]{3}-', i)):
												external.extend(['inc-' + i, 'pla-' + i, 'yod-' + i, 'lam-' + i, 'glo-' + i, 'uni-' + i, 'nan-' + i])
										descriptions.extend(external)

										for i in descriptions:
											try:
												sourceObject = provider.Provider.provider(i, enabled = False, local = True)['object']
												break
											except: pass
										if sourceObject == None:
											for i in descriptions:
												try:
													sourceObject = provider.Provider.provider(i, enabled = False, local = True, exact = False)['object']
													break
												except: pass

								try: url = sourceObject.resolve(url, internal = True) # To accomodate Torba's popup dialog.
								except: url = sourceObject.resolve(url)
								item['urlresolved'] = item['url'] = url # Assign to 'url', since it must first be resolved by eg Incursion scrapers and then by eg ResolveUrl
								if not item['source'] == 'torrent' and not item['source'] == 'usenet':
									item['source'] = network.Networker.linkDomain(url).lower()
								handle = handler.Handler().serviceDetermine(mode = handleMode, item = item, popups = True)
						except:
							tools.Logger.error()

					if handle == handler.Handler.ReturnUnavailable or handle == handler.Handler.ReturnExternal or handle == handler.Handler.ReturnCancel:
						interface.Loader.hide()
						return None

				self.progressPlaybackInitialize(title = heading, message = message, metadata = metadata)

				block = None
				image = None
				if not metadata == None:
					keys = ['poster', 'poster1', 'poster2', 'poster3', 'thumb', 'thumb1', 'thumb2', 'thumb3', 'icon', 'icon1', 'icon2', 'icon3']
					for key in keys:
						if key in metadata:
							value = metadata[key]
							if not value == None and not value == '':
								image = value
								break

				try:
					if self.progressPlaybackCanceled():
						interface.Loader.hide()
						return None
				except: pass

				self.progressPlaybackUpdate(progress = 5, title = heading, message = message)

				local = 'local' in item and item['local']
				if item['source'] == block: raise Exception()
				self.tResolved = None

				# OffCloud cloud downloads require a download, even if it is a hoster. Only instant downloads on OffCloud do not need this.
				try: cloud = (not 'premium' in item or not item['premium']) and (not item['source'] == 'torrent' and not item['source'] == 'usenet') and not tools.Settings.getBoolean('accounts.debrid.offcloud.instant') and handler.Handler(handler.Handler.TypeHoster).service(handle).id() == handler.HandleOffCloud.Id
				except: cloud = False

				# Torrents and usenet have a download dialog with their own thread. Do not start a thread for them here.
				if not local and (item['source'] == 'torrent' or item['source'] == 'usenet' or cloud):
					# Do not close the dialog, otherwise there is a period where no dialog is showing.
					# The progress dialog in the debrid downloader (through sourcesResolve), will overwrite this.
					#progressDialog.close()

					labelTransferring = 33674 if item['source'] == 'torrent' else 33675 if item['source'] == 'usenet' else 33943
					labelTransferring = interface.Translation.string(labelTransferring)
					self.progressPlaybackUpdate(progress = 10, title = heading, message = labelTransferring)

					def _resolve(item, handle):
						try:
							# Download the container. This is also done by sourcesResolve(), but download it here to show it to the user in the dialog, because it takes some time.
							try:
								pro = provider.Provider.provider(item['providerid'], enabled = False, local = True)['object']
							except:
								# When playing a stream from History after the provider was disabled.
								provider.Provider.initialize(forceAll = True)
								pro = provider.Provider.provider(item['providerid'], enabled = False, local = True)['object']

							link = item['url']
							try: link = pro.resolve(link, internal = internal)
							except: link = pro.resolve(link)
							network.Container(link = link, download = True).hash()
						except:
							tools.Logger.error()

					thread = workers.Thread(_resolve, item, handle)
					thread.start()

					progress = 0
					while thread.is_alive():
						try:
							if xbmc.abortRequested == True:
								sys.exit()
								interface.Loader.hide()
								return None
							if self.progressPlaybackCanceled():
								self.progressPlaybackClose()
								return None
						except:
							interface.Loader.hide()

						progress += 0.25
						progressCurrent = 5 + min(int(progress), 30)
						self.progressPlaybackUpdate(progress = progressCurrent, title = heading, message = labelTransferring)

						time.sleep(0.5)

					self.progressPlaybackUpdate(progress = 30, title = heading, message = 35537)
					self.tResolved = self.sourcesResolve(item, info = True, handle = handle, handleMode = handleMode, handleClose = False)

					if handler.Handler.serviceExternal(handle):
						if self.tResolved['success']:
							try: return self.tResolved['link']
							except: pass
						return self.url
					if not self.url == None and not self.url == '':
						if not self.progressPlaybackCanceled():
							self.progressPlaybackUpdate(progress = 45, title = heading, message = message)
				else:
					def _resolve(item, handle):
						self.tResolved = self.sourcesResolve(item, info = True, handle = handle, handleMode = handleMode, handleClose = False)

					w = workers.Thread(_resolve, item, handle)
					w.start()

					end = 3600
					for x in range(end):
						try:
							if xbmc.abortRequested == True:
								sys.exit()
								interface.Loader.hide()
								return None
							if self.progressPlaybackCanceled():
								self.progressPlaybackClose()
								return None
						except:
							interface.Loader.hide()

						if not control.condVisibility('Window.IsActive(virtualkeyboard)') and not control.condVisibility('Window.IsActive(yesnoDialog)'):
							break

						progress = 5 + int((x / float(end)) * 20)
						self.progressPlaybackUpdate(progress = progress, title = heading, message = message)

						time.sleep(0.5)

					if not self.progressPlaybackCanceled():
						end = 30
						for x in range(end):
							try:
								if xbmc.abortRequested == True:
									sys.exit()
									interface.Loader.hide()
									return None
								if self.progressPlaybackCanceled():
									self.progressPlaybackClose()
									return None
							except:
								interface.Loader.hide()

							if not w.is_alive(): break

							progress = 25 + int((x / float(end)) * 25)
							self.progressPlaybackUpdate(progress = progress, title = heading, message = message)

							time.sleep(0.5)

						# For pairing dialogs to remain open.
						# Have it in two steps to have a smoother progress, instead of a very long single timeout.
						if not self.progressPlaybackCanceled() and w.is_alive():
							end = 3600
							for x in range(end):
								try:
									if xbmc.abortRequested == True:
										sys.exit()
										interface.Loader.hide()
										return None
									if self.progressPlaybackCanceled():
										self.progressPlaybackClose()
										return None
								except:
									interface.Loader.hide()

								if not w.is_alive(): break

								progress = 50
								self.progressPlaybackUpdate(progress = progress, title = heading, message = message)

								time.sleep(0.5)

						if w.is_alive() == True:
							block = item['source']

				# Close download dialog if opened.
				if self.navigationPlaybackSpecial:
					interface.Core.close()

				if self.progressPlaybackCanceled():
					tools.Logger.error()
					self.progressPlaybackClose()
					return None
				elif handler.Handler.serviceExternal(handle):
					if self.tResolved['success']:
						try: return self.tResolved['link']
						except: pass
					return self.url
				else:
					self.progressPlaybackUpdate(progress = 50, title = heading, message = message)

				if not self.tResolved['success']:
					if sequential:
						return self.play(source = source, metadata = metadata, downloadType = downloadType, downloadId = downloadId, handle = handle, handleMode = handleMode, index = index + 1)
					else:
						self.progressPlaybackClose()
						return None

				item['urlresolved'] = self.tResolved['link']
				item['stream'] = self.tResolved

				history.History().insert(type = self.type, kids = self.kids, link = item['url'], metadata = metadata, source = source)

				control.sleep(200)
				control.execute('Dialog.Close(virtualkeyboard)')
				control.execute('Dialog.Close(yesnoDialog)')

				# If the background dialog is not closed, when another background dialog is launched, it will contain the old information from the previous dialog.
				# Manually close it. Do not close the foreground dialog, since it does not have the issue and keeping the dialog shown is smoother transition.
				# NB: This seems to not be neccessary with the new interface.Core. However, enable again if the problems are observed.
				#if interface.Core.background():
				#	interface.Core.close()
				#	interface.Loader.show() # Since there is no dialog anymore.

				from resources.lib.modules.player import player
				player(type = self.type, kids = self.kids).run(self.type, title, year, season, episode, imdb, tmdb, tvdb, self.url, metadata, downloadType = downloadType, downloadId = downloadId, handle = handle, source = item)

				return self.url
			except:
				tools.Logger.error()
				interface.Loader.hide()

			self.progressPlaybackClose()
			self.progressFailure(single = True)
			return True
		except:
			tools.Logger.error()
			self.progressPlaybackClose()
			return False

	def playCache(self, source, metadata = None, handleMode = None):
		try:
			if tools.Settings.getBoolean('downloads.cache.enabled'):
				interface.Loader.show()

				if metadata == None:
					metadata = control.window.getProperty(self.propertyMeta)
					metadata = json.loads(metadata)

				item = source
				if isinstance(item, list):
					item = item[0]

				handle = handler.Handler().serviceDetermine(mode = handleMode, item = item, popups = True)
				if handle == handler.Handler.ReturnUnavailable or handle == handler.Handler.ReturnExternal or handle == handler.Handler.ReturnCancel:
					interface.Loader.hide()
					return None

				result = self.sourcesResolve(item, handle = handle, handleMode = handleMode, handleClose = False) # Do not use item['urlresolved'], because it has the | HTTP header part removed, which is needed by the downloader.

				# If the Premiumize download is still running and the user clicks cancel in the dialog.
				if not result['success']:
					return

				link = result['link']
				source['stream'] = result

				if 'local' in item and item['local']: # Must be after self.sourcesResolve.
					self.play(source = source, metadata = metadata, handle = handle)
					return

				downloadType = None
				downloadId = None
				if not link == None and not link == '':
					downer = downloader.Downloader(downloader.Downloader.TypeCache)
					path = downer.download(media = self.type, link = link, metadata = metadata, source = source, automatic = True)
					if path and not path == '':
						downloadType = downer.type()
						downloadId = downer.id()
						item['url'] = path

						time.sleep(3) # Allow a few seconds for the download to start. Otherwise the download was queued but not started and the file was not created yet.
						downer.refresh()

				interface.Loader.hide()
				self.playLocal(path = path, source = source, metadata = metadata, downloadType = downloadType, downloadId = downloadId)
			else:
				self.play(source = source, metadata = metadata)
		except:
			interface.Loader.hide()
			tools.Logger.error()

	# Used by downloader.
	def playLocal(self, path, source, metadata, downloadType = None, downloadId = None):
		source['url'] = tools.File.translate(path)
		source['local'] = True
		source['source'] = '0'
		self.play(source = source, metadata = metadata, downloadType = downloadType, downloadId = downloadId)

	def databaseOpen(self, timeout = 30):
		# NB: Very often the execution on the databases throws an exception if multiple threads access the database at the same time.
		# NB: An OperationalError "database is locked" is thrown. Set a timeout to give the connection a few seconds to retry.
		# NB: 10 seconds is often not enough if there are a lot of providers locking the database.
		# NB FOLLOW UP: Even with a higher timeout, the error can still happen with external providers.
		# NB FOLLOW UP: It seems that instead of opening the database once for the entire function, open it, query, and close again. Repeat this for each query seems to solve the problem.
		try:
			self.databaseLock()
			connection = database.connect(self.sourceFile, timeout = timeout)
			cursor = connection.cursor()
			return connection, cursor
		except:
			self.databaseUnlock()
			return None

	def databaseClose(self, connection):
		try: connection.close()
		except: pass
		self.databaseUnlock()

	def databaseLock(self):
		# Lock before writing to the database. This is important for external scrapers, otherwise this error is thrown, even with a database connection timeout: OperationalError -> database is locked.
		# NB: For some reason Python somtimes throws an exception saying that a unlocked/locked lock (tried) to aquire/release. Always keep these statements in a try-catch.
		try: self.dataLock.acquire()
		except: pass

	def databaseUnlock(self):
		# NB: For some reason Python somtimes throws an exception saying that a unlocked/locked lock (tried) to aquire/release. Always keep these statements in a try-catch.
		try: self.dataLock.release()
		except: pass

	def addSources(self, sources, check):
		if self.stopThreads:
			return
		try:
			if len(sources) > 0:
				enabled = tools.Settings.getBoolean('scraping.precheck.enabled') or tools.Settings.getBoolean('scraping.metadata.enabled') or tools.Settings.getBoolean('scraping.cache.enabled')
				self.sources.extend(sources)

				for source in sources:
					# Some external addons return an addon URL instead of the actual URL.
					if 'external' in source and source['external'] and not network.Networker.linkIs(source['url'], magnet = True):
						try: source['url'] = dict(urlparse.parse_qsl(source['url']))['url']
						except: continue

					source['source'] = sourceName = source['source'].replace('www.', '').strip().lower()

					debrid = False
					source['debrid'] = {}
					for key, value in self.debridServices.iteritems():
						source['debrid'][key] = False
						for j in value:
							if j in sourceName or sourceName in j:
								source['debrid'][key] = True
								debrid = True
					if debrid: self.streamsDebrid += 1

					# When loading from cache.
					try:
						if any(i for i in source['cache'].itervalues()):
							self.streamsCached += 1
					except:	pass

					if not 'cache' in source:
						source['cache'] = {}

					quality = metadatax.Metadata.videoQualityConvert(source['quality'])
					source['quality'] = quality
					metadatax.Metadata.initialize(title = source['titleadapted'] if 'titleadapted' in source else source['title'], source = source, update = True)
					index = self.adjustSourceAppend(source)
					if index < 0: continue

					priority = False
					if 'K' in quality:
						priority = True
						self.streamsHdUltra += 1 # 4K or higher
					elif quality == 'HD1080':
						priority = True
						self.streamsHd1080 += 1
					elif quality == 'HD720':
						priority = True
						self.streamsHd720 += 1
					elif quality == 'SD': self.streamsSd += 1
					elif 'SCR' in quality: self.streamsScr += 1
					elif 'CAM' in quality: self.streamsCam += 1

					if sourceName == 'torrent': self.streamsTorrent += 1
					elif sourceName == 'usenet': self.streamsUsenet += 1
					elif not('local' in source and source['local']) and not('premium' in source and source['premium']): self.streamsHoster += 1

					if 'direct' in source and source['direct']: self.streamsDirect += 1
					if 'premium' in source and source['premium']: self.streamsPremium += 1
					if 'local' in source and source['local']: self.streamsLocal += 1

					if source['source'] == 'torrent':
						container = network.Container(link = source['url'], download = False)
						if container.torrentIsMagnet():
							hash = container.hash()
							if not hash == None: source['hash'] = hash

					self.streamsTotal += 1
					if check and enabled:
						thread = workers.Thread(self.adjustSource, source, index)
						self.priortityAdjusted.append(priority) # Give priority to HD links
						self.statusAdjusted.append('queued')
						self.threadsAdjusted.append(thread)
					else:
						self.cachedAdjusted += 1

				self.adjustSourceStart()
				thread = workers.Thread(self.adjustSourceCache, None, True)
				thread.start()
		except:
			tools.Logger.error()

	def adjustRename(self, source):
		name = source.lower()
		if 'gvideo' in name or ('google' in name and 'vid' in name) or ('google' in name and 'link' in name):
			source = 'GoogleVideo'
		elif 'google' in name and ('usercontent' in name or 'cloud' in name):
			source = 'GoogleCloud'
		elif 'google' in name and 'doc' in name:
			source = 'GoogleDocs'
		elif ('google' in name and 'drive' in name) or 'gdrive' in name:
			source = 'GoogleDrive'
		return source

	def adjustLock(self):
		# NB: For some reason Python somtimes throws an exception saying that a unlocked/locked lock (tried) to aquire/release. Always keep these statements in a try-catch.
		try: self.threadsLock.acquire()
		except: pass

	def adjustUnlock(self):
		# NB: For some reason Python somtimes throws an exception saying that a unlocked/locked lock (tried) to aquire/release. Always keep these statements in a try-catch.
		try: self.threadsLock.release()
		except: pass

	def adjustTerminationLock(self):
		try: self.terminationLock.acquire()
		except: pass

	def adjustTerminationUnlock(self):
		try: self.terminationLock.release()
		except: pass

	def adjustTermination(self):
		try:
			self.adjustTerminationLock()

			if self.terminationEnabled:
				self.adjustLock()

				# No new streams.
				if self.terminationPrevious == len(self.sourcesAdjusted):
					return
				self.terminationPrevious = len(self.sourcesAdjusted)

				counter = 0
				for i in range(len(self.sourcesAdjusted)):
					source = self.sourcesAdjusted[i]
					metadata = source['metadata']

					# Type
					if self.terminationTypeHas:
						found = False
						for key, value in self.terminationType.iteritems():
							if key in source:
								result = source[key]
								if isinstance(result, dict): # cache
									for value2 in result.itervalues():
										if value2 == value:
											found = True
											break
									if found: break
								elif result == value:
									found = True
									break
						if not found: continue

					# Video Quality
					if self.terminationVideoQualityHas:
						if not source['quality'] in self.terminationVideoQuality:
							continue

					# Video Codec
					if self.terminationVideoCodecHas:
						videoCodec = metadata.videoCodec()
						if not any([videoCodec == i for i in self.terminationVideoCodec]):
							continue

					# Audio Channels
					if self.terminationAudioChannelsHas:
						audioChannels = metadata.audioChannels()
						if not any([audioChannels == i for i in self.terminationAudioChannels]):
							continue

					# Audio Codec
					if self.terminationAudioCodecHas:
						audioSystem = metadata.audioSystem(full = False)
						audioCodec = metadata.audioCodec(full = False)
						if not any([(audioSystem == i or audioCodec == i) for i in self.terminationAudioCodec]):
							continue

					counter += 1
					if counter >= self.terminationCount:
						return True
		except:
			tools.Logger.error()
		finally:
			try: self.adjustTerminationUnlock()
			except: pass
			try: self.adjustUnlock()
			except: pass
		return False

	def adjustSourceCache(self, timeout = None, partial = False):
		# Premiumize seems to take long to verify usenet hashes.
		# Split torrents and usenet up, with the hope that torrents will complete, even when usenet takes very long.
		# Can also be due to expensive local hash calculation for NZBs.
		if tools.Settings.getBoolean('scraping.cache.enabled'):
			debridTypes = []
			debridObjects = []
			if tools.Settings.getBoolean('scraping.cache.premiumize'):
				premiumize = debridx.Premiumize()
				if premiumize.accountValid():
					if tools.Settings.getBoolean('streaming.torrent.premiumize.enabled'):
						debridTypes.append(handler.Handler.TypeTorrent)
						debridObjects.append(premiumize)
					if tools.Settings.getBoolean('streaming.usenet.premiumize.enabled') and tools.Settings.getBoolean('scraping.cache.preload.usenet'):
						debridTypes.append(handler.Handler.TypeUsenet)
						debridObjects.append(premiumize)
					if tools.Settings.getBoolean('streaming.hoster.premiumize.enabled'):
						debridTypes.append(handler.Handler.TypeHoster)
						debridObjects.append(premiumize)

			if tools.Settings.getBoolean('scraping.cache.offcloud'):
				offcloud = debridx.OffCloud()
				if offcloud.accountValid():
					if tools.Settings.getBoolean('streaming.torrent.offcloud.enabled'):
						debridTypes.append(handler.Handler.TypeTorrent)
						debridObjects.append(offcloud)
					if tools.Settings.getBoolean('streaming.usenet.offcloud.enabled') and tools.Settings.getBoolean('scraping.cache.preload.usenet'):
						debridTypes.append(handler.Handler.TypeUsenet)
						debridObjects.append(offcloud)

			if tools.Settings.getBoolean('scraping.cache.realdebrid'):
				realdebrid = debridx.RealDebrid()
				if realdebrid.accountValid() and tools.Settings.getBoolean('streaming.torrent.realdebrid.enabled'):
					debridTypes.append(handler.Handler.TypeTorrent)
					debridObjects.append(realdebrid)

			if len(debridTypes) > 0:
				if partial: # If it is the final full inspection, always execute, even if another partial inspection is still busy.
					self.adjustLock()
					busy = self.cachedAdjustedBusy
					self.adjustUnlock()
					if busy: return

				if timeout == None:
					try: timeout = tools.Settings.getInteger('scraping.cache.timeout')
					except: timeout = 45

				threads = []
				for i in range(len(debridTypes)):
					threads.append(workers.Thread(self._adjustSourceCache, debridObjects[i], debridTypes[i], timeout, partial))

				self.adjustLock()
				self.cachedAdjustedBusy = True
				self.adjustUnlock()

				[thread.start() for thread in threads]
				[thread.join() for thread in threads]

				self.adjustLock()
				self.cachedAdjustedBusy = False
				self.adjustUnlock()

	def _adjustSourceCache(self, debrid, type, timeout, partial = False):
		try:
			debridId = debrid.id()
			self.adjustLock()
			hashes = []
			sources = []

			modes = debrid.cachedModes()
			modeHash = debridx.Debrid.ModeTorrent in modes or debridx.Debrid.ModeUsenet in modes
			modeLink = debridx.Debrid.ModeHoster in modes
			for source in self.sourcesAdjusted:
				if (source['source'] == type or (modeLink and type == handler.Handler.TypeHoster)) and (not 'premium' in source or not source['premium']):
					# Only check those that were not previously inspected.
					if not debridId in source['cache'] or source['cache'][debridId] == None:
						# NB: Do not calculate the hash if it is not available.
						# The hash is not available because the NZB could not be downloaded, or is still busy in the thread.
						# Calling container.hash() will cause the NZB to download again, which causes long delays.
						# Since the hashes are accumlated here sequentially, it might cause the download to take so long that the actual debrid cache query has never time to execute.
						# If the NZBs' hashes are not available at this stage, ignore it.
						'''if not 'hash' in source:
							container = network.Container(link = source['url'])
							source['hash'] = container.hash()'''
						if modeHash and 'hash' in source and not source['hash'] == None and not source['hash'] == '':
							hashes.append(source['hash'])
							sources.append(source)
						elif modeLink and 'url' in source and not source['url'] == None and not source['url'] == '':
							hashes.append(source['url'])
							sources.append(source)

			self.adjustUnlock()

			# Partial will inspect the cache will the scraping is still busy.
			# Only check if there are a bunch of them, otherwise there are too many API calls (heavy load on both server and local machine).
			if len(hashes) == 0 or (partial and len(hashes) < 40): return

			# NB: Set all statuses to false, otherwise the same links will be send multiple times for inspection, if multiple hosters finish in a short period of time before the previous inspection is done.
			# This will exclude all currently-being-looked-up links from the next iteration in the for-loop above.
			for source in self.sourcesAdjusted:
				if (modeHash and 'hash' in source and source['hash'] in hashes) or (modeLink and 'url' in source and source['url'] in hashes):
					source['cache'][debridId] = False
			self.adjustUnlock()

			def _updateIndividually(debrid, hash, cached):
				hashLower = hash.lower()
				self.adjustLock()
				for i in range(len(self.sourcesAdjusted)):
					try:
						if self.sourcesAdjusted[i]['hash'].lower() == hashLower:
							if cached and (not debrid in self.sourcesAdjusted[i]['cache'] or not self.sourcesAdjusted[i]['cache'][debrid]):
								self.sourcesAdjusted[i]['cache'][debrid] = cached
								if cached and sum(self.sourcesAdjusted[i]['cache'].values()) == 1: # Only count one of the debird service caches.
									self.streamsCached += 1
							break
					except: pass
					try:
						if self.sourcesAdjusted[i]['url'] == hash:
							if cached and (not debrid in self.sourcesAdjusted[i]['cache'] or not self.sourcesAdjusted[i]['cache'][debrid]):
								self.sourcesAdjusted[i]['cache'][debrid] = cached
								if cached and sum(self.sourcesAdjusted[i]['cache'].values()) == 1: # Only count one of the debird service caches.
									self.streamsCached += 1
							break
					except: pass
				self.adjustUnlock()

			self.adjustLock()
			self.progressCache += 1 # Used to determine when the cache-inspection threads are completed.
			self.adjustUnlock()
			debrid.cached(id = hashes, timeout = timeout, callback = _updateIndividually, sources = sources)
			self.adjustLock()
			self.progressCache -= 1
			self.adjustUnlock()
		except:
			tools.Logger.error()
		finally:
			try: self.adjustUnlock()
			except: pass

	# priority starts stream checks HD720 and greater first.
	def adjustSourceStart(self, priority = True):
		if self.stopThreads:
			return
		try:
			self.adjustLock()

			# HD links
			running = [i for i in self.threadsAdjusted if i.is_alive()]
			openSlots = None if self.threadsLimit == None else max(0, self.threadsLimit - len(running))
			counter = 0
			for j in range(len(self.threadsAdjusted)):
				if self.priortityAdjusted == True and self.statusAdjusted[j] == 'queued':
					self.statusAdjusted[j] = 'busy'
					self.threadsAdjusted[j].start()
					counter += 1
					if not openSlots == None and counter > openSlots:
						raise Exception('Maximum thread limit reached.')

			# Non-HD links
			running = [i for i in self.threadsAdjusted if i.is_alive()]
			openSlots = None if self.threadsLimit == None else max(0, self.threadsLimit - len(running))
			counter = 0
			for j in range(len(self.threadsAdjusted)):
				if self.statusAdjusted[j] == 'queued':
					self.statusAdjusted[j] = 'busy'
					self.threadsAdjusted[j].start()
					counter += 1
					if not openSlots == None and counter > openSlots:
						raise Exception('Maximum thread limit reached.')
		except:
			pass
		finally:
			try: self.adjustUnlock()
			except: pass

	def adjustSourceAppend(self, sourceOrSources):
		if self.stopThreads:
			return

		index = -1
		self.adjustLock()
		try:
			if isinstance(sourceOrSources, dict):
				if not self.adjustSourceContains(sourceOrSources, mutex = False):
					self.sourcesAdjusted.append(sourceOrSources)
					index = len(self.sourcesAdjusted) - 1
			else:
				for source in sourceOrSources:
					if not self.adjustSourceContains(source, mutex = False):
						self.sourcesAdjusted.append(source)
						index = len(self.sourcesAdjusted) - 1
		except:
			pass
		finally:
			try: self.adjustUnlock()
			except: pass
		return index

	def adjustSourceContains(self, source, mutex = True): # Filter out duplicate URLs early on, to reduce the prechecks & metadata on them.
		if self.stopThreads:
			return

		contains = False
		if mutex: self.adjustLock()
		try:
			debrids = [debridx.Premiumize().id(), debridx.RealDebrid().id()]
			for i in range(len(self.sourcesAdjusted)):
				sourceAdjusted = self.sourcesAdjusted[i]
				if sourceAdjusted['url'] == source['url']:
					# NB: Compare both debrid caches.
					# If there are different providers and/or different variations of the provider (for different foreing languages or umlauts), the same item might be detected by multiple providers.
					# This is especially important for debrid cached links. One provider might have it flagged as cache, the other one not. Then on the second run of the scraping procees, the values are read from database, and which ever one was written first to the DB will be returned.
					# Later pick the longest dict, since that one is expected to contains most metadata/info.

					# If any one is cached, make both cached.
					for debrid in debrids:
						cache = sourceAdjusted[i]['cache'][debrid] if debrid in sourceAdjusted['cache'] else None
						cacheNew = source['cache'][debrid] if debrid in source['cache'] else None
						if cache == None: cache = cacheNew
						elif not cacheNew == None: cache = cache or cacheNew
						if not cache == None:
							sourceAdjusted['cache'][debrid] = cache
							source['cache'][debrid] = cache

					# Take the one with most info.
					length = len(tools.Converter.jsonTo(sourceAdjusted))
					lengthNew = len(tools.Converter.jsonTo(source))
					if length > lengthNew:
						self.sourcesAdjusted[i] = sourceAdjusted
					else:
						self.sourcesAdjusted[i] = source

					contains = True
					break
		except:
			pass
		finally:
			if mutex:
				try: self.adjustUnlock()
				except: pass
		return contains

	def adjustSourceUpdate(self, index, metadata = None, precheck = None, urlresolved = None, hash = None, mutex = True):
		if self.stopThreads:
			return
		try:
			if index >= 0:
				if mutex: self.adjustLock()
				if not metadata == None:
					self.sourcesAdjusted[index]['metadata'] = metadata
				if not precheck == None:
					self.sourcesAdjusted[index]['precheck'] = precheck
				if not urlresolved == None:
					self.sourcesAdjusted[index]['urlresolved'] = urlresolved
				if not hash == None:
					self.sourcesAdjusted[index]['hash'] = hash

				if mutex: self.adjustUnlock()
		except:
			pass
		finally:
			if mutex:
				try: self.adjustUnlock()
				except: pass

	# Write changes to database.
	def adjustSourceDatabase(self, timeout = 30):
		try:
			self.adjustLock()

			sources = {}
			for i in range(len(self.sourcesAdjusted)):
				try:
					result = copy.deepcopy(self.sourcesAdjusted[i])
					source = result['database']['source']
					mode = result['database']['mode']
					try: id = source + '_' + mode
					except: id = source
					metadatax.Metadata.uninitialize(result)

					if not id in sources:
						sources[id] = {
							'source' : source,
							'mode' : mode,
							'imdb' : result['database']['imdb'],
							'season' : result['database']['season'],
							'episode' : result['database']['episode'],
							'sources' : []
						}

					del result['database']
					sources[id]['sources'].append(result)
				except:
					pass

			timestamp = tools.Time.timestamp()
			try:
				connection, cursor = self.databaseOpen(timeout = timeout)
				for value in sources.itervalues():
					try:
						source = value['source']
						mode = value['mode']
						imdb = value['imdb']
						season = value['season']
						episode = value['episode']
						data = json.dumps(value['sources'])
						cursor.execute("DELETE FROM sources WHERE source = '%s' AND mode = '%s' AND imdb = '%s' AND season = '%s' AND episode = '%s'" % (source, mode, imdb, season, episode))
						cursor.execute("INSERT INTO sources Values (?, ?, ?, ?, ?, ?, ?)", (source, mode, imdb, season, episode, data, timestamp))
					except:
						pass
				connection.commit()
			except: tools.Logger.error()
			finally: self.databaseClose(connection)
		except:
			tools.Logger.error()
		finally:
			try: self.adjustUnlock()
			except: pass

	def adjustSourceDone(self, index):
		try:
			self.adjustLock()
			if index >= 0 and index < len(self.statusAdjusted):
				self.statusAdjusted[index] = 'done'
			self.adjustUnlock()
		except:
			pass
		finally:
			try: self.adjustUnlock()
			except: pass

	def adjustSource(self, source, index):
		if self.stopThreads:
			self.adjustSourceDone(index)
			return None
		try:
			link = source['url']
			special = source['source'] == 'torrent' or source['source'] == 'usenet'
			status = network.Networker.StatusUnknown
			neter = None

			# Resolve Link
			if not special and (self.enabledPrecheck or self.enabledMetadata):
				if not 'urlresolved' in source or ('urlresolved' in source and not source['urlresolved']):
					link = network.Networker().resolve(source, clean = True)
					if link:
						source['urlresolved'] = link
					else:
						link = source['url']
				self.adjustSourceUpdate(index, urlresolved = link)

				neter = network.Networker(link)
				local = 'local' in source and source['local']

			# Debrid Cache
			# Do before precheck and metadata, because it is a lot faster and more important. So execute first.
			if special and self.enabledCache and (not 'hash' in source or not source['hash']):
				# Do not automatically get the hash, since this will have to download the torrent/NZB files.
				# Sometimes more than 150 MB of torrents/NZBs can be downloaded on one go, wasting bandwidth and slowing down the addon/Kodi.
				download = False
				if source['source'] == 'torrent': download = tools.Settings.getBoolean('scraping.cache.preload.torrent')
				elif source['source'] == 'usenet': download = tools.Settings.getBoolean('scraping.cache.preload.usenet')

				container = network.Container(link = link, download = download)
				hash = container.hash()
				if not hash == None:
					self.adjustSourceUpdate(index, hash = hash)

			# Precheck
			if not special and self.enabledPrecheck:
				if local:
					status = network.Networker.StatusOnline
				elif not neter == None:
					neter.headers(timeout = tools.Settings.getInteger('scraping.precheck.timeout'))
					status = neter.check(content = True)
				self.adjustSourceUpdate(index, precheck = status)

			# Metadata
			if not special and self.enabledMetadata and status == network.Networker.StatusOnline:
				if index < 0: # Already in list.
					return None
				metadata = metadatax.Metadata(link = link)
				if not local:
					metadata.loadHeaders(neter, timeout = tools.Settings.getInteger('scraping.metadata.timeout'))
				self.adjustSourceUpdate(index, metadata = metadata)

		except:
			pass

		self.adjustSourceDone(index)
		if not self.threadsLimit == None: self.adjustSourceStart()
		return source

	def clearSources(self, confirm = False):
		try:
			if confirm:
				interface.Loader.show()
				yes = interface.Dialog.option(33042)
				if not yes: return

			control.makeFile(control.dataPath)
			dbcon = database.connect(control.providercacheFile)
			dbcur = dbcon.cursor()
			dbcur.execute("DROP TABLE IF EXISTS sources")
			dbcur.execute("DROP TABLE IF EXISTS links")

			# These are the legacy tables. Can be removed in a lter version.
			# Also in clearSourcesOld()
			dbcur.execute("DROP TABLE IF EXISTS rel_url")
			dbcur.execute("DROP TABLE IF EXISTS rel_src")

			dbcur.execute("VACUUM")
			dbcon.commit()

			if confirm:
				interface.Dialog.notification(33043, sound = True, icon = interface.Dialog.IconInformation)
		except:
			pass

	def clearSourcesOld(self, wait = True):
		def _clearSourcesOld():
			try:
				timestamp = tools.Time.timestamp() - 7200 # Must be the same delay as for retrieving the sources, that is 120 minutes.
				control.makeFile(control.dataPath)
				dbcon = database.connect(control.providercacheFile)
				dbcur = dbcon.cursor()

				# These are the legacy tables. Can be removed in a lter version.
				# Also in clearSources()
				dbcur.execute("DROP TABLE IF EXISTS rel_url")
				dbcur.execute("DROP TABLE IF EXISTS rel_src")

				dbcur.execute("DELETE FROM sources WHERE time < %d" % timestamp)
				dbcon.commit()
			except:
				pass
		thread = workers.Thread(_clearSourcesOld)
		thread.start()
		if wait: thread.join()

	def sourcesRemoveDuplicates(self, sources, orion = False):
		def filterLink(link):
			container = network.Container(link)
			if container.torrentIsMagnet():
				return container.torrentMagnetClean() # Clean magnet from trackers, name, domain, etc.
			else:
				return network.Networker(link).link() # Clean link from HTTP headers.

		def cacheUpdate(sourceOld, sourceNew):
			sourceOld['cache'].update({k : v for k, v in sourceNew['cache'].items() if v})

		def orionReplace(sourceOld, sourceNew):
			return 'orion' in sourceNew and not 'orion' in sourceOld

		result = []
		linksNormal = []
		linksResolved = []
		linksHashes = []
		linksSources = []

		for source in sources:
			# NB: Only remove duplicates if their source is the same. This ensures that links from direct sources are not removed (Eg: Premiumize Direct vs Premiumize Torrent).

			index = None
			duplicate = False
			linkNormal = filterLink(source['url']).lower()
			linkResolved = filterLink(source['urlresolved']) if 'urlresolved' in source else None

			try:
				index = linksNormal.index(linkNormal)
				if index >= 0 and source['source'] == linksSources[index]: duplicate = True
			except: pass

			try:
				if not duplicate:
					if not linkResolved == None:
						index = linksResolved.index(linkResolved)
						if index >= 0 and source['source'] == linksSources[index]: duplicate = True
			except: pass

			try:
				if not duplicate:
					if 'hash' in source and not source['hash'] == None:
						index = linksHashes.index(source['hash'])
						if index >= 0 and source['source'] == linksSources[index]: duplicate = True
			except: pass

			try:
				if duplicate:
					if orion:
						if orionReplace(source, result[index]): result[index] = source
					else:
						if orionReplace(result[index], source): result[index] = source
					result[index]['metadata'].increaseSeeds(source['metadata'].seeds())
					cacheUpdate(result[index], source)
					continue
			except:
				tools.Logger.error()
				pass

			result.append(source)
			linksNormal.append(linkNormal)
			linksResolved.append(linkResolved)
			linksHashes.append(source['hash'] if 'hash' in source else None)
			linksSources.append(source['source'])

		# Force update metadata with the new combined values.
		for i in range(len(result)):
			metadatax.Metadata.initialize(source = result[i], update = True)

		return result

	def sourcesRemoveUnsupported(self, sources):
		# Filter - Unsupported
		# Create handlers in order to reduce overhead in the handlers initialization.
		handleDirect = handler.Handler(type = handler.Handler.TypeDirect)
		handleTorrent = handler.Handler(type = handler.Handler.TypeTorrent)
		handleUsenet = handler.Handler(type = handler.Handler.TypeUsenet)
		handleHoster = handler.Handler(type = handler.Handler.TypeHoster)
		filter = []
		for i in sources:
			source = i['source']
			if source == handler.Handler.TypeTorrent:
				if handleTorrent.supported(i): filter.append(i)
			elif source == handler.Handler.TypeUsenet:
				if handleUsenet.supported(i): filter.append(i)
			elif 'direct' in i and i['direct']:
				if handleDirect.supported(i): filter.append(i)
			elif 'external' in i and i['external'] and (not 'debridonly' in i or not i['debridonly']):
				filter.append(i)
			else:
				if handleHoster.supported(i): filter.append(i)
				elif source in self.externalServices: filter.append(i)
				else: tools.Logger.log('Unsupported Link: ' + '[' + str(source) + '] ' + str(i['url']))
		return filter

	def sourcesFilter(self, items, metadata, autoplay = False, apply = True):
		try:
			if autoplay: autoplay = not tools.Settings.getBoolean('automatic.manual')

			####################################################################################
			# FUNCTIONS
			####################################################################################

			def _filterFlag(source, value):
				return value in source and source[value] == True

			def _filterDebrid(source):
				return any(i for i in source['debrid'].itervalues())

			def _filterSetting(setting):
				if autoplay: return tools.Settings.getString('automatic.' + setting)
				else: return tools.Settings.getString('manual.' + setting)

			def _filterMetadata(sources, filters):
				try:
					result = []
					for filter in filters:
						subresult = []
						i = 0
						length = len(sources)
						while i < length:
							source = sources[i]
							if source['quality'] == filter:
								subresult.append(source)
								del sources[i]
								i -= 1
							i += 1
							length = len(sources)

						subresult = _filterMetadataQuality(subresult)

						if filterSortSecondary:
							if filterSortAge == 3: subresult = _filterAge(subresult)
							if filterSortSeeds == 3: subresult = _filterSeeds(subresult)
							if filterSortSize == 3: subresult = _filterSize(subresult)
							if filterSortPopularity == 3: subresult = _filterPopularity(subresult)

						result += subresult
					return result
				except:
					return sources

			def _filterMetadataQuality(sources):
				result = []
				resultH265 = [[], [], [], [], [], [], [], [], [], [], [], []]
				resultH264 = [[], [], [], [], [], [], [], [], [], [], [], []]
				resultOther = [[], [], [], [], [], [], [], [], [], [], []]
				resultRest = []

				source = None
				for i in range(len(sources)):
					source = sources[i]
					meta = source['metadata']
					videoCodec = meta.videoCodec()
					audioChannels = meta.audioChannels()
					audioCodec = meta.audioCodec()

					if 'H265' == videoCodec:
						if '8CH' == audioChannels:
							if 'DTS' == audioCodec: resultH265[0].append(source)
							elif 'DD' == audioCodec: resultH265[1].append(source)
							else: resultH265[2].append(source)
						elif '6CH' == audioChannels:
							if 'DTS' == audioCodec: resultH265[3].append(source)
							elif 'DD' == audioCodec: resultH265[4].append(source)
							else: resultH265[5].append(source)
						elif 'DTS' == audioCodec:
							resultH265[6].append(source)
						elif 'DD' == audioCodec:
							resultH265[7].append(source)
						elif '2CH' == audioChannels:
							if 'DTS' == audioCodec: resultH265[8].append(source)
							elif 'DD' == audioCodec: resultH265[9].append(source)
							else: resultH265[10].append(source)
						else:
							resultH265[11].append(source)
					elif 'H264' == videoCodec:
						if '8CH' == audioChannels:
							if 'DTS' == audioCodec: resultH264[0].append(source)
							elif 'DD' == audioCodec: resultH264[1].append(source)
							else: resultH264[2].append(source)
						elif '6CH' == audioChannels:
							if 'DTS' == audioCodec: resultH264[3].append(source)
							elif 'DD' == audioCodec: resultH264[4].append(source)
							else: resultH264[5].append(source)
						elif 'DTS' == audioCodec:
							resultH264[6].append(source)
						elif 'DD' == audioCodec:
							resultH264[7].append(source)
						elif '2CH' == audioChannels:
							if 'DTS' == audioCodec: resultH264[8].append(source)
							elif 'DD' == audioCodec: resultH264[9].append(source)
							else: resultH264[10].append(source)
						else:
							resultH264[11].append(source)
					else:
						if '8CH' == audioChannels:
							if 'DTS' == audioCodec: resultOther[0].append(source)
							elif 'DD' == audioCodec: resultOther[1].append(source)
							else: resultOther[2].append(source)
						elif '6CH' == audioChannels:
							if 'DTS' == audioCodec: resultOther[3].append(source)
							elif 'DD' == audioCodec: resultOther[4].append(source)
							else: resultOther[5].append(source)
						elif 'DTS' == audioCodec:
							resultOther[6].append(source)
						elif 'DD' == audioCodec:
							resultOther[7].append(source)
						elif '2CH' == audioChannels:
							if 'DTS' == audioCodec: resultOther[8].append(source)
							elif 'DD' == audioCodec: resultOther[9].append(source)
							else: resultOther[10].append(source)
						else:
							resultRest.append(source)

				for i in range(len(resultH265)):
					result += resultH265[i]
				for i in range(len(resultH264)):
					result += resultH264[i]
				for i in range(len(resultOther)):
					result += resultOther[i]
				result += resultRest

				result = _filterMetadataSpecial(result)
				return result

			def _filterMetadataSpecial(results):
				filter1 = []
				filter2 = []
				filter3 = []
				filter4 = []
				filter5 = []
				for s in results:
					if s['metadata'].premium(): filter1.append(s)
					elif s['metadata'].cached(): filter2.append(s)
					elif s['metadata'].direct(): filter3.append(s)
					elif s['metadata'].debrid(): filter4.append(s)
					else: filter5.append(s)
				filter1 = _filterMetadataPrecheck(filter1)
				filter2 = _filterMetadataPrecheck(filter2)
				filter3 = _filterMetadataPrecheck(filter3)
				filter4 = _filterMetadataPrecheck(filter4)
				filter5 = _filterMetadataPrecheck(filter5)

				if filterSortSecondary:
					if filterSortAge == 6:
						filter1 = _filterAge(filter1)
						filter2 = _filterAge(filter2)
						filter3 = _filterAge(filter3)
						filter4 = _filterAge(filter4)
						filter5 = _filterAge(filter5)
					if filterSortSeeds == 6:
						filter1 = _filterSeeds(filter1)
						filter2 = _filterSeeds(filter2)
						filter3 = _filterSeeds(filter3)
						filter4 = _filterSeeds(filter4)
						filter5 = _filterSeeds(filter5)
					if filterSortSize == 6:
						filter1 = _filterSize(filter1)
						filter2 = _filterSize(filter2)
						filter3 = _filterSize(filter3)
						filter4 = _filterSize(filter4)
						filter5 = _filterSize(filter5)
					if filterSortPopularity == 6:
						filter1 = _filterPopularity(filter1)
						filter2 = _filterPopularity(filter2)
						filter3 = _filterPopularity(filter3)
						filter4 = _filterPopularity(filter4)
						filter5 = _filterPopularity(filter5)

				return filter1 + filter2 + filter3 + filter4 + filter5

			def _filterMetadataPrecheck(results):
				filter1 = []
				filter2 = []
				filter3 = []
				for s in results:
					check = s['metadata'].precheck()
					if check == network.Networker.StatusOnline: filter1.append(s)
					elif check == network.Networker.StatusUnknown: filter2.append(s)
					else: filter3.append(s)
				return filter1 + filter2 + filter3

			def _filterAge(sources):
				sources.sort(key = lambda i: i['metadata'].age(), reverse = False)
				return sources

			def _filterSeeds(sources):
				sources.sort(key = lambda i: i['metadata'].seeds(), reverse = True)
				return sources

			def _filterSize(sources):
				sources.sort(key = lambda i: i['metadata'].size(), reverse = True)
				return sources

			def _filterPopularity(sources):
				sources.sort(key = lambda i: i['metadata'].popularity(), reverse = True)
				return sources

			def _filterValid(value):
				return not _filterInvalid(value)

			def _filterInvalid(value):
				return value == None

			####################################################################################
			# FILTERS
			####################################################################################

			# LABELS

			labelAny = interface.Translation.string(33113)
			labelNone = interface.Translation.string(33112)

			# FILTERS - LIMIT
			filterGeneralLimit = int(_filterSetting('general.limit'))

			# FILTERS - REMOVAL

			filterRemovalDuplicates = interface.Filters.removalDuplicates()
			if _filterInvalid(filterRemovalDuplicates): filterRemovalDuplicates = tools.Settings.getBoolean('scraping.providers.duplicates')
			interface.Filters.removalDuplicates(filterRemovalDuplicates)

			# FILTERS - UNSUPPORTED

			filterRemovalUnsupported = interface.Filters.removalUnsupported()
			if _filterInvalid(filterRemovalUnsupported): filterRemovalUnsupported = tools.Settings.getBoolean('scraping.providers.unsupported')
			interface.Filters.removalUnsupported(filterRemovalUnsupported)

			# FILTERS - PROVIDER SERVICE

			filterProviderService = interface.Filters.providerService()
			if _filterInvalid(filterProviderService): filterProviderService = _filterSetting('provider.service')
			interface.Filters.providerService(filterProviderService)
			filterProviderService = 0 if _filterInvalid(filterProviderService) else int(filterProviderService)

			# FILTERS - PROVIDER SELECTION

			filterProviderSelection = interface.Filters.providerSelection()
			if _filterInvalid(filterProviderSelection): filterProviderSelection = _filterSetting('provider.selection')
			interface.Filters.providerSelection(filterProviderSelection)
			filterProviderSelection = 0 if _filterInvalid(filterProviderSelection) else int(filterProviderSelection)

			# FILTERS - PROVIDER AGE

			filterProviderAge = interface.Filters.providerAge()
			if _filterInvalid(filterProviderAge): filterProviderAge = _filterSetting('provider.age')
			interface.Filters.providerAge(filterProviderAge)
			filterProviderAge = 0 if _filterInvalid(filterProviderAge) else int(filterProviderAge)

			# FILTERS - PROVIDER SEEDS

			filterProviderSeeds = interface.Filters.providerSeeds()
			if _filterInvalid(filterProviderSeeds): filterProviderSeeds = _filterSetting('provider.seeds')
			interface.Filters.providerSeeds(filterProviderSeeds)
			filterProviderSeeds = 0 if _filterInvalid(filterProviderSeeds) else int(filterProviderSeeds)

			# FILTERS - PROVIDER POPULARITY

			filterProviderPopularity = interface.Filters.providerPopularity()
			if _filterInvalid(filterProviderPopularity): filterProviderPopularity = _filterSetting('provider.popularity')
			interface.Filters.providerPopularity(filterProviderPopularity)
			filterProviderPopularity = 0 if _filterInvalid(filterProviderPopularity) else (int(filterProviderPopularity) / 100.0)

			# FILTERS - PROVIDER CACHE

			filterProviderCacheTorrent = interface.Filters.providerCacheTorrent()
			if _filterInvalid(filterProviderCacheTorrent): filterProviderCacheTorrent = _filterSetting('provider.cache.torrent')
			interface.Filters.providerCacheTorrent(filterProviderCacheTorrent)
			filterProviderCacheTorrent = 0 if _filterInvalid(filterProviderCacheTorrent) else int(filterProviderCacheTorrent)

			filterProviderCacheUsenet = interface.Filters.providerCacheUsenet()
			if _filterInvalid(filterProviderCacheUsenet): filterProviderCacheUsenet = _filterSetting('provider.cache.usenet')
			interface.Filters.providerCacheUsenet(filterProviderCacheUsenet)
			filterProviderCacheUsenet = 0 if _filterInvalid(filterProviderCacheUsenet) else int(filterProviderCacheUsenet)

			filterProviderCacheHoster = interface.Filters.providerCacheHoster()
			if _filterInvalid(filterProviderCacheHoster): filterProviderCacheHoster = _filterSetting('provider.cache.hoster')
			interface.Filters.providerCacheHoster(filterProviderCacheHoster)
			filterProviderCacheHoster = 0 if _filterInvalid(filterProviderCacheHoster) else int(filterProviderCacheHoster)

			# FILTERS - FILE NAME

			filterFileNameInclude = interface.Filters.fileNameInclude()
			if _filterInvalid(filterFileNameInclude): filterFileNameInclude = _filterSetting('file.name.include')
			filterFileNameInclude = '' if _filterInvalid(filterFileNameInclude) else filterFileNameInclude
			interface.Filters.fileNameInclude(filterFileNameInclude)
			filterFileNameInclude = re.sub(' +', ' ', filterFileNameInclude).strip().lower().split()

			filterFileNameExclude = interface.Filters.fileNameExclude()
			if _filterInvalid(filterFileNameExclude): filterFileNameExclude = _filterSetting('file.name.exclude')
			filterFileNameExclude = '' if _filterInvalid(filterFileNameExclude) else filterFileNameExclude
			interface.Filters.fileNameExclude(filterFileNameExclude)
			filterFileNameExclude = re.sub(' +', ' ', filterFileNameExclude).strip().lower().split()

			# FILTERS - FILE SIZE

			filterFileSizeMinimum = interface.Filters.fileSizeMinimum()
			if _filterInvalid(filterFileSizeMinimum): filterFileSizeMinimum = _filterSetting('file.size.minimum')
			interface.Filters.fileSizeMinimum(filterFileSizeMinimum)
			filterFileSizeMinimum = 0 if _filterInvalid(filterFileSizeMinimum) else int(filterFileSizeMinimum)

			filterFileSizeMaximum = interface.Filters.fileSizeMaximum()
			if _filterInvalid(filterFileSizeMaximum): filterFileSizeMaximum = _filterSetting('file.size.maximum')
			interface.Filters.fileSizeMaximum(filterFileSizeMaximum)
			filterFileSizeMaximum = 0 if _filterInvalid(filterFileSizeMaximum) else int(filterFileSizeMaximum)

			# FILTERS - VIDEO QUALITY

			filterVideoQualityMinimum = interface.Filters.videoQualityMinimum()
			if _filterInvalid(filterVideoQualityMinimum): filterVideoQualityMinimum = _filterSetting('video.quality.minimum')
			interface.Filters.videoQualityMinimum(filterVideoQualityMinimum)
			filterVideoQualityMinimum = 0 if _filterInvalid(filterVideoQualityMinimum) else int(filterVideoQualityMinimum)

			filterVideoQualityMaximum = interface.Filters.videoQualityMaximum()
			if _filterInvalid(filterVideoQualityMaximum): filterVideoQualityMaximum = _filterSetting('video.quality.maximum')
			interface.Filters.videoQualityMaximum(filterVideoQualityMaximum)
			filterVideoQualityMaximum = 0 if _filterInvalid(filterVideoQualityMaximum) else int(filterVideoQualityMaximum)

			if filterVideoQualityMinimum > filterVideoQualityMaximum:
				filterVideoQualityMinimum, filterVideoQualityMaximum = filterVideoQualityMinimum, filterVideoQualityMaximum # Swap

			# FILTERS - VIDEO CODEC

			filterVideoCodec = interface.Filters.videoCodec()
			if _filterInvalid(filterVideoCodec): filterVideoCodec = _filterSetting('video.codec')
			interface.Filters.videoCodec(filterVideoCodec)
			filterVideoCodec = 0 if _filterInvalid(filterVideoCodec) else int(filterVideoCodec)

			# FILTERS - VIDEO 3D

			filterVideo3D = interface.Filters.video3D()
			if _filterInvalid(filterVideo3D): filterVideo3D = _filterSetting('video.3d')
			interface.Filters.video3D(filterVideo3D)
			filterVideo3D = 0 if _filterInvalid(filterVideo3D) else int(filterVideo3D)

			# FILTERS - AUDIO CHANNELS

			filterAudioChannels = interface.Filters.audioChannels()
			if _filterInvalid(filterAudioChannels): filterAudioChannels = _filterSetting('audio.channels')
			interface.Filters.audioChannels(filterAudioChannels)
			filterAudioChannels = 0 if _filterInvalid(filterAudioChannels) else int(filterAudioChannels)

			# FILTERS - AUDIO CODEC

			filterAudioCodec = interface.Filters.audioCodec()
			if _filterInvalid(filterAudioCodec): filterAudioCodec = _filterSetting('audio.codec')
			interface.Filters.audioCodec(filterAudioCodec)
			filterAudioCodec = 0 if _filterInvalid(filterAudioCodec) else int(filterAudioCodec)

			# FILTERS - AUDIO LANGUAGE

			filterAudioLanguage = interface.Filters.audioLanguage(label = True)
			if _filterInvalid(filterAudioLanguage):
				filterAudioLanguage = _filterSetting('audio.language')
				filterAudioLanguage = 0 if _filterInvalid(filterAudioLanguage) else int(filterAudioLanguage)
				if filterAudioLanguage == 0:
					filterAudioLanguage = None
				else:
					filterAudioLanguage = _filterSetting('audio.language.primary')
					if filterAudioLanguage == labelNone: filterAudioLanguage = None
			elif filterAudioLanguage == labelAny:
				filterAudioLanguage = None
			filterAudioLanguageHas = not _filterInvalid(filterAudioLanguage)
			if filterAudioLanguageHas: filterAudioLanguage = tools.Language.code(filterAudioLanguage)
			interface.Filters.audioLanguage('' if filterAudioLanguage == None else filterAudioLanguage)

			# FILTERS - AUDIO DUBBED

			filterAudioDubbed = interface.Filters.audioDubbed()
			if _filterInvalid(filterAudioDubbed): filterAudioDubbed = _filterSetting('audio.dubbed')
			interface.Filters.audioDubbed(filterAudioDubbed)
			filterAudioDubbed = 0 if _filterInvalid(filterAudioDubbed) else int(filterAudioDubbed)

			# FILTERS - SUBTITLES SOFT

			filterSubtitlesSoft = interface.Filters.subtitlesSoft()
			if _filterInvalid(filterSubtitlesSoft): filterSubtitlesSoft = _filterSetting('subtitles.soft')
			interface.Filters.subtitlesSoft(filterSubtitlesSoft)
			filterSubtitlesSoft = 0 if _filterInvalid(filterSubtitlesSoft) else int(filterSubtitlesSoft)

			# FILTERS - SUBTITLES HARD

			filterSubtitlesHard = interface.Filters.subtitlesHard()
			if _filterInvalid(filterSubtitlesHard): filterSubtitlesHard = _filterSetting('subtitles.hard')
			interface.Filters.subtitlesHard(filterSubtitlesHard)
			filterSubtitlesHard = 0 if _filterInvalid(filterSubtitlesHard) else int(filterSubtitlesHard)

			# FILTERS - SORT

			filterSortSecondary = tools.Converter.boolean(_filterSetting('sort.secondary'))

			filterSortQuality = interface.Filters.sortQuality()
			if _filterInvalid(filterSortQuality): filterSortQuality = _filterSetting('sort.quality')
			interface.Filters.sortQuality(filterSortQuality)
			filterSortQuality = 0 if _filterInvalid(filterSortQuality) else int(filterSortQuality)

			filterSortPrimary = interface.Filters.sortPrimary()
			if _filterInvalid(filterSortPrimary): filterSortPrimary = _filterSetting('sort.primary')
			interface.Filters.sortPrimary(filterSortPrimary)
			filterSortPrimary = 0 if _filterInvalid(filterSortPrimary) else int(filterSortPrimary)

			filterSortSize = interface.Filters.sortSize()
			if filterSortSecondary and _filterInvalid(filterSortSize): filterSortSize = _filterSetting('sort.size')
			filterSortSize = 0 if _filterInvalid(filterSortSize) else int(filterSortSize)
			interface.Filters.sortSize(filterSortSize)

			filterSortAge = interface.Filters.sortAge()
			if filterSortSecondary and _filterInvalid(filterSortAge): filterSortAge = _filterSetting('sort.age')
			filterSortAge = 0 if _filterInvalid(filterSortAge) else int(filterSortAge)
			interface.Filters.sortAge(filterSortAge)

			filterSortSeeds = interface.Filters.sortSeeds()
			if filterSortSecondary and _filterInvalid(filterSortSeeds): filterSortSeeds = _filterSetting('sort.seeds')
			filterSortSeeds = 0 if _filterInvalid(filterSortSeeds) else int(filterSortSeeds)
			interface.Filters.sortSeeds(filterSortSeeds)

			filterSortPopularity = interface.Filters.sortPopularity()
			if filterSortSecondary and _filterInvalid(filterSortPopularity): filterSortPopularity = _filterSetting('sort.popularity')
			filterSortPopularity = 0 if _filterInvalid(filterSortPopularity) else int(filterSortPopularity)
			interface.Filters.sortPopularity(filterSortPopularity)

			filterSortSecondary = filterSortSize > 0 or filterSortAge > 0 or filterSortSeeds > 0 or filterSortPopularity > 0

			####################################################################################
			# PREPROCESSING
			####################################################################################

			handlePremiumize = handler.HandlePremiumize()
			premiumize = debridx.Premiumize()
			premiumizeEnabled = premiumize.accountValid()

			self.countInitial = len(items)
			self.countDuplicates = 0
			self.countSupported = 0
			self.countFilters = 0
			tools.Logger.log('Scraping Streams Initial: ' + str(self.countInitial), name = 'CORE', level = tools.Logger.TypeNotice)

			####################################################################################
			# METADATA DUPLICATES
			####################################################################################

			if filterRemovalDuplicates:
				items = self.sourcesRemoveDuplicates(items)
				self.countDuplicates = len(items)
				tools.Logger.log('Scraping Streams After Duplication Removal: ' + str(self.countDuplicates), name = 'CORE', level = tools.Logger.TypeNotice)
			else:
				self.countDuplicates = len(items)

			####################################################################################
			# METADATA UNSUPPORTED
			####################################################################################

			if filterRemovalUnsupported:
				items = self.sourcesRemoveUnsupported(items)
				self.countSupported = len(items)
				tools.Logger.log('Scraping Streams After Unsupported Removal: ' + str(self.countSupported), name = 'CORE', level = tools.Logger.TypeNotice)
			else:
				self.countSupported = len(items)

			####################################################################################
			# METADATA ELIMINATE
			####################################################################################

			if apply:

				# Filter - Prechecks
				precheck = _filterSetting('provider.precheck') == 'true' and tools.System.developers()
				if precheck:
					items = [i for i in items if not 'precheck' in i or not i['precheck'] == network.Networker.StatusOffline]

				# Filter - Editions
				editions = int(_filterSetting('additional.editions'))
				if editions == 1:
					items = [i for i in items if not i['metadata'].edition()]
				elif editions == 2:
					items = [i for i in items if i['metadata'].edition()]

				# Filter - Releases
				releases = tools.Settings.customGetReleases('automatic' if autoplay else 'manual')
				if releases and not len(releases) == len(metadatax.Metadata.DictionaryReleases):
					filter = []
					for i in items:
						release = i['metadata'].release(full = False)
						if release and release in releases:
							filter.append(i)
					items = filter

				# Filter - Uploaders
				uploaders = tools.Settings.customGetUploaders('automatic' if autoplay else 'manual')
				if uploaders and not len(uploaders) == len(metadatax.Metadata.DictionaryUploaders):
					filter = []
					for i in items:
						uploader = i['metadata'].uploader()
						if uploader and any(u in uploaders for u in uploader):
							filter.append(i)
					items = filter

				# Filter - Video Codec
				if filterVideoCodec == 1:
					items = [i for i in items if i['metadata'].videoCodec() == 'H265' or i['metadata'].videoCodec() == 'H264']
				elif filterVideoCodec == 2:
					items = [i for i in items if i['metadata'].videoCodec() == 'H265']
				elif filterVideoCodec == 3:
					items = [i for i in items if i['metadata'].videoCodec() == 'H264']
				elif filterVideoCodec == 4:
					items = [i for i in items if not i['metadata'].videoCodec() == 'H265']
				elif filterVideoCodec == 5:
					items = [i for i in items if not i['metadata'].videoCodec() == 'H264']

				# Filter - Video 3D
				if filterVideo3D == 1:
					items = [i for i in items if not i['metadata'].videoExtra() == '3D']
				elif filterVideo3D == 2:
					items = [i for i in items if i['metadata'].videoExtra() == '3D']

				# Filter - Audio Channels
				if filterAudioChannels == 1:
					items = [i for i in items if i['metadata'].audioChannels() == '8CH' or i['metadata'].audioChannels() == '6CH']
				elif filterAudioChannels == 2:
					items = [i for i in items if i['metadata'].audioChannels() == '8CH']
				elif filterAudioChannels == 3:
					items = [i for i in items if i['metadata'].audioChannels() == '6CH']
				elif filterAudioChannels == 4:
					items = [i for i in items if i['metadata'].audioChannels() == '2CH']

				# Filter - Audio Codec
				if filterAudioCodec == 1:
					items = [i for i in items if i['metadata'].audioSystem(full = False) == 'DTS' or i['metadata'].audioSystem(full = False) == 'DD' or i['metadata'].audioCodec(full = False) == 'AAC']
				elif filterAudioCodec == 2:
					items = [i for i in items if i['metadata'].audioSystem(full = False) == 'DTS' or i['metadata'].audioSystem(full = False) == 'DD']
				elif filterAudioCodec == 3:
					items = [i for i in items if i['metadata'].audioSystem(full = False) == 'DTS']
				elif filterAudioCodec == 4:
					items = [i for i in items if i['metadata'].audioSystem(full = False) == 'DD']
				elif filterAudioCodec == 5:
					items = [i for i in items if i['metadata'].audioCodec(full = False) == 'AAC']
				elif filterAudioCodec == 6:
					items = [i for i in items if not i['metadata'].audioSystem(full = False) == 'DTS']
				elif filterAudioCodec == 7:
					items = [i for i in items if not i['metadata'].audioSystem(full = False) == 'DD']
				elif filterAudioCodec == 8:
					items = [i for i in items if not i['metadata'].audioCodec(full = False) == 'AAC']

				# Filter - Audio Language

				audioLanguage = int(_filterSetting('audio.language'))
				if filterAudioLanguageHas or not audioLanguage == 0:
					audioLanguageUnknown = tools.Converter.boolean(_filterSetting('audio.language.unknown'))
					if not audioLanguageUnknown:
						items = [i for i in items if not i['metadata'].audioLanguages() == None and len(i['metadata'].audioLanguages()) > 0]

					audioLanguages = []
					if filterAudioLanguageHas:
						audioLanguages = [filterAudioLanguage]
					elif tools.Language.customization():
						language = _filterSetting('audio.language.primary')
						if not language == labelNone: audioLanguages.append(tools.Language.code(language))
						language = _filterSetting('audio.language.secondary')
						if not language == labelNone: audioLanguages.append(tools.Language.code(language))
						language = _filterSetting('audio.language.tertiary')
						if not language == labelNone: audioLanguages.append(tools.Language.code(language))
					else:
						audioLanguages = [language[0] for language in tools.Language.settings()]
					audioLanguages = list(set(audioLanguages))
					filter = []
					for i in items:
						languages = i['metadata'].audioLanguages()
						if audioLanguageUnknown and (languages == None or len(languages) == 0):
							filter.append(i)
						else:
							if languages == None or len(languages) == 0:
								languages = []
							else:
								languages = [l[0] for l in languages]
							if any(l in audioLanguages for l in languages):
								filter.append(i)
					items = filter

				# Filter - Dubbed Audio
				if filterAudioDubbed == 1:
					items = [i for i in items if not i['metadata'].audioDubbed()]
				elif filterAudioDubbed == 2:
					items = [i for i in items if i['metadata'].audioDubbed()]

				# Filter - Subtitles Softcoded
				if filterSubtitlesSoft == 1:
					items = [i for i in items if not i['metadata'].subtitlesIsSoft()]
				elif filterSubtitlesSoft == 2:
					items = [i for i in items if i['metadata'].subtitlesIsSoft()]

				# Filter - Subtitles Hardcoded
				if filterSubtitlesHard == 1:
					items = [i for i in items if not i['metadata'].subtitlesIsHard()]
				elif filterSubtitlesHard == 2:
					items = [i for i in items if i['metadata'].subtitlesIsHard()]

				# Filter - Bandwidth
				bandwidthMaximum = int(_filterSetting('bandwidth.maximum'))
				bandwidthUnknown = int(_filterSetting('bandwidth.unknown')) == 0
				try: duration = int(metadata['duration'])
				except: duration = None

				if bandwidthMaximum > 0:
					settingsBandwidth = tools.Settings.data()
					indexStart = settingsBandwidth.find('automatic.bandwidth.maximum' if autoplay else 'manual.bandwidth.maximum')
					indexStart = settingsBandwidth.find('lvalues', indexStart) + 9
					indexEnd = settingsBandwidth.find('"', indexStart)
					settingsBandwidth = settingsBandwidth[indexStart : indexEnd]
					settingsBandwidth = settingsBandwidth.split('|')
					settingsBandwidth = interface.Translation.string(int(settingsBandwidth[bandwidthMaximum]))

					# All values are calculated at 90% the line speed, due to lag, disconnects, buffering, etc.
					bandwidthMaximum = int(convert.ConverterSpeed(value = settingsBandwidth).value(unit = convert.ConverterSpeed.Byte) * 0.90)

					if bandwidthUnknown:
						items = [i for i in items if not duration or not i['metadata'].size() or i['metadata'].size() / duration <= bandwidthMaximum]
					else:
						items = [i for i in items if duration and i['metadata'].size() and i['metadata'].size() / duration <= bandwidthMaximum]

				# Filter - File Size
				if filterFileSizeMinimum > 0 or filterFileSizeMaximum > 0:
					fileSizeInclude = int(_filterSetting('file.size.unknown')) == 0
					if filterFileSizeMinimum > 0:
						filterFileSizeMinimum *= 1048576 # bytes
						filter = []
						for i in items:
							size = i['metadata'].size(estimate = True)
							if size == None or size == 0:
								if fileSizeInclude: filter.append(i)
							elif size > 0 and size >= filterFileSizeMinimum:
								filter.append(i)
						items = filter
					if filterFileSizeMaximum > 0:
						filterFileSizeMaximum *= 1048576 # bytes
						filter = []
						for i in items:
							size = i['metadata'].size(estimate = True)
							if size == None or size == 0:
								if fileSizeInclude: filter.append(i)
							elif size > 0 and size <= filterFileSizeMaximum:
								filter.append(i)
						items = filter

				# Filter - File Name
				if len(filterFileNameInclude) > 0 or len(filterFileNameExclude) > 0:
					fileNameUnknown = int(_filterSetting('file.name.unknown')) == 0
					filter = []
					for i in items:
						fileNameHas = 'file' in i and not i['file'] == None and not i['file'] == ''
						if fileNameHas:
							fileName = i['file'].lower()
							if all(i in fileName for i in filterFileNameInclude) and not any(i in fileName for i in filterFileNameExclude):
								filter.append(i)
						elif fileNameUnknown:
							filter.append(i)
					items = filter

				# Filter - Providers
				providerSelectionHoster = filterProviderSelection == 0 or filterProviderSelection == 1 or filterProviderSelection == 2 or filterProviderSelection == 4
				providerSelectionTorrents = filterProviderSelection == 0 or filterProviderSelection == 1 or filterProviderSelection == 3 or filterProviderSelection == 5
				providerSelectionUsenet = filterProviderSelection == 0 or filterProviderSelection == 2 or filterProviderSelection == 3 or filterProviderSelection == 6

				# Filter - Age
				if filterProviderAge > 0:
					items = [i for i in items if not i['metadata'].age() or i['metadata'].age() <= filterProviderAge]

				# Filter - Popularity
				if filterProviderPopularity > 0:
					items = [i for i in items if not i['metadata'].popularity() or i['metadata'].popularity() >= filterProviderPopularity]

				# Filter - Torrents
				if providerSelectionTorrents:

					# Filter - Torrent Cache
					torrentCacheInclude = filterProviderCacheTorrent == 0
					torrentCacheExclude = filterProviderCacheTorrent == 1
					torrentCacheRequire = filterProviderCacheTorrent == 2
					if torrentCacheExclude:
						items = [i for i in items if not i['source'] == 'torrent' or not ('cache' in i and debridx.Debrid.cachedAny(i['cache']))]
					elif torrentCacheRequire:
						items = [i for i in items if not i['source'] == 'torrent' or ('cache' in i and debridx.Debrid.cachedAny(i['cache']))]

					# Filter - Torrent Seeds
					if not torrentCacheRequire:
						items = [i for i in items if not i['source'] == 'torrent' or (i['metadata'].seeds() and i['metadata'].seeds() >= filterProviderSeeds)]
				else:
					items = [i for i in items if not i['source'] == 'torrent']

				# Filter - Usenet
				if providerSelectionUsenet:
					# Filter - Usenet Cache
					usenetCacheInclude = filterProviderCacheUsenet == 0
					usenetCacheExclude = filterProviderCacheUsenet == 1
					usenetCacheRequire = filterProviderCacheUsenet == 2
					if usenetCacheExclude:
						items = [i for i in items if not i['source'] == 'usenet' or not ('cache' in i and debridx.Debrid.cachedAny(i['cache']))]
					elif usenetCacheRequire:
						items = [i for i in items if not i['source'] == 'usenet' or ('cache' in i and debridx.Debrid.cachedAny(i['cache']))]
				else:
					items = [i for i in items if not i['source'] == 'usenet']

				# Filter - Hoster
				if providerSelectionHoster:

					# Filter - Hoster Cache
					hosterCacheInclude = filterProviderCacheHoster == 0
					hosterCacheExclude = filterProviderCacheHoster == 1
					hosterCacheRequire = filterProviderCacheHoster == 2

					if hosterCacheExclude:
						items = [i for i in items if not (not i['source'] == 'torrent' and not i['source'] == 'usenet') or not ('cache' in i and debridx.Debrid.cachedAny(i['cache']))]
					elif hosterCacheRequire:
						items = [i for i in items if not (not i['source'] == 'torrent' and not i['source'] == 'usenet') or ('cache' in i and debridx.Debrid.cachedAny(i['cache']))]
				else:
					items = [i for i in items if not (not i['source'] == 'torrent' and not i['source'] == 'usenet')]

				# Filter - Debrid Cost
				costMaximum = int(_filterSetting('provider.service.cost'))
				if costMaximum > 0 and premiumizeEnabled:
					filter = []
					for i in items:
						if handlePremiumize.supported(i):
							try: cost = premiumize.service(i['source'].lower().rsplit('.', 1)[0])['usage']['cost']['value']
							except: cost = None
							if cost == None or cost <= costMaximum:
								filter.append(i)
						else:
							filter.append(i)
					items = filter

				# Filter - Captcha
				if _filterSetting('provider.captcha') == 'true':
					filter = [i for i in items if i['source'].lower() in self.hostcapDict and not _filterDebrid(i)]
					items = [i for i in items if not i in filter]

				# Filter - Block
				filter = [i for i in items if i['source'].lower() in self.hostblockDict and not _filterDebrid(i)]
				items = [i for i in items if not i in filter]

			####################################################################################
			# METADATA SORT INTERNAL
			####################################################################################

			# Filter - Seeds and Age
			if filterSortSecondary:
				if filterSortAge == 1: items = _filterAge(items)
				if filterSortSeeds == 1: items = _filterSeeds(items)
				if filterSortSize == 1: items = _filterSize(items)
				if filterSortPopularity == 1: items = _filterPopularity(items)

			# Filter - Local
			filterLocal = [i for i in items if 'local' in i and i['local'] == True]
			items = [i for i in items if not i in filterLocal]
			filterLocal = _filterMetadata(filterLocal, ['HD8K', 'HD6K', 'HD4K', 'HD2K', 'HD1080', 'HD720', 'SD'])

			# Filter - Add Hosters that are supported by a Debrid service.
			if debrid.status():
				filter = []
				for i in range(len(items)):
					if not 'debrid' in items[i]:
						items[i]['debrid'] = {}
						for j in self.debridServices.itervalues():
							items[i]['debrid'][j] = False
				filter += [i for i in items if _filterDebrid(i)]
				filter += [i for i in items if not _filterDebrid(i)]
				items = filter

			if apply:
				meta = metadatax.Metadata()
				qualities = [None] + meta.VideoQualityOrder
				videoQualityFrom = qualities[filterVideoQualityMinimum]
				videoQualityTo = qualities[filterVideoQualityMaximum]
				# Only get the indexes once, otherwise has to search for it for every stream.
				videoQualityFrom = meta.videoQualityIndex(videoQualityFrom)
				videoQualityTo = meta.videoQualityIndex(videoQualityTo)
				items = [i for i in items if meta.videoQualityRange(i['quality'], videoQualityFrom, videoQualityTo)]

			# Filter - Services
			serviceSelectionDebrid = filterProviderService == 0 or filterProviderService == 1 or filterProviderService == 2 or filterProviderService == 4
			serviceSelectionMembers = filterProviderService == 0 or filterProviderService == 1 or filterProviderService == 3 or filterProviderService == 5
			serviceSelectionFree = filterProviderService == 0 or filterProviderService == 2 or filterProviderService == 3 or filterProviderService == 6

			# Filter - HD - Premium
			filterPremium = [i for i in items if _filterFlag(i, 'premium') and not i['quality'] == 'SD' and not 'SCR' in i['quality'] and not 'CAM' in i['quality']]
			items = [i for i in items if not i in filterPremium]
			if serviceSelectionDebrid:
				filterPremium = _filterMetadata(filterPremium, ['HD8K', 'HD6K', 'HD4K', 'HD2K', 'HD1080', 'HD720'])
			else:
				filterPremium = []

			# Filter - HD - Debrid
			filterDebrids = [i for i in items if _filterDebrid(i) and not i['quality'] == 'SD' and not 'SCR' in i['quality'] and not 'CAM' in i['quality']]
			items = [i for i in items if not i in filterDebrids]
			if serviceSelectionDebrid:
				filterDebrids = _filterMetadata(filterDebrids, ['HD8K', 'HD6K', 'HD4K', 'HD2K', 'HD1080', 'HD720'])
			else:
				filterDebrids = []

			# Filter - HD - Direct
			filterDirect = [i for i in items if _filterFlag(i, 'direct') and not i['quality'] == 'SD' and not 'SCR' in i['quality'] and not 'CAM' in i['quality']]
			items = [i for i in items if not i in filterDirect]
			if serviceSelectionFree:
				filterDirect = _filterMetadata(filterDirect, ['HD8K', 'HD6K', 'HD4K', 'HD2K', 'HD1080', 'HD720'])
			else:
				filterDirect = []

			# Filter - HD - Member
			filterMember = [i for i in items if _filterFlag(i, 'memberonly') and not i['quality'] == 'SD' and not 'SCR' in i['quality'] and not 'CAM' in i['quality']]
			items = [i for i in items if not i in filterMember]
			if serviceSelectionMembers:
				filterMember = _filterMetadata(filterMember, ['HD8K', 'HD6K', 'HD4K', 'HD2K', 'HD1080', 'HD720'])
			else:
				filterMember = []

			# Filter - HD - Free
			filterFree = [i for i in items if not i['quality'] == 'SD' and not 'SCR' in i['quality'] and not 'CAM' in i['quality']]
			items = [i for i in items if not i in filterFree]
			if serviceSelectionFree:
				filterFree = _filterMetadata(filterFree, ['HD8K', 'HD6K', 'HD4K', 'HD2K', 'HD1080', 'HD720'])
			else:
				filterFree = []

			# Filter - SD
			filterSd = [i for i in items if not 'SCR' in i['quality'] and not 'CAM' in i['quality']]
			items = [i for i in items if not i in filterSd]
			filter = []
			if serviceSelectionDebrid:
				filter += _filterMetadata([i for i in filterSd if _filterFlag(i, 'premium')], ['SD'])
				filter += _filterMetadata([i for i in filterSd if _filterDebrid(i) and not _filterFlag(i, 'premium')], ['SD'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterSd if _filterFlag(i, 'direct') and not _filterDebrid(i) and not _filterFlag(i, 'premium')], ['SD'])
			if serviceSelectionMembers:
				filter += _filterMetadata([i for i in filterSd if _filterFlag(i, 'memberonly') and not _filterFlag(i, 'premium') and not _filterDebrid(i) and not _filterFlag(i, 'direct')], ['SD'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterSd if not _filterFlag(i, 'premium')  and not _filterDebrid(i) and not _filterFlag(i, 'direct') and not _filterFlag(i, 'memberonly')], ['SD'])
			filterSd = filter

			# Filter - Combine
			filterLd = items
			items = []
			items += filterLocal

			# Sort again to make sure HD streams from free hosters go to the top.
			filter = []
			filter += filterPremium
			filter += filterDebrids
			filter += filterDirect
			filter += filterMember
			filter += filterFree
			items += _filterMetadata(filter, ['HD8K', 'HD6K', 'HD4K', 'HD2K', 'HD1080', 'HD720'])

			items += _filterMetadataSpecial(filterSd)

			# Filter - LD
			filter = []

			# SCR1080
			if serviceSelectionDebrid:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'premium')], ['SCR1080'])
				filter += _filterMetadata([i for i in filterLd if _filterDebrid(i) and not _filterFlag(i, 'premium')], ['SCR1080'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'direct') and not _filterDebrid(i) and not _filterFlag(i, 'premium')], ['SCR1080'])
			if serviceSelectionMembers:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'memberonly') and not _filterFlag(i, 'premium') and not _filterDebrid(i) and not _filterFlag(i, 'direct')], ['SCR1080'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if not not _filterFlag(i, 'premium') and _filterDebrid(i) and not _filterFlag(i, 'direct') and not _filterFlag(i, 'memberonly')], ['SCR1080'])

			# SCR720
			if serviceSelectionDebrid:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'premium')], ['SCR720'])
				filter += _filterMetadata([i for i in filterLd if _filterDebrid(i) and not _filterFlag(i, 'premium')], ['SCR720'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'direct') and not _filterDebrid(i) and not _filterFlag(i, 'premium')], ['SCR720'])
			if serviceSelectionMembers:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'memberonly') and not _filterFlag(i, 'premium') and not _filterDebrid(i) and not _filterFlag(i, 'direct')], ['SCR720'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if not not _filterFlag(i, 'premium') and _filterDebrid(i) and not _filterFlag(i, 'direct') and not _filterFlag(i, 'memberonly')], ['SCR720'])

			# SCR
			if serviceSelectionDebrid:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'premium')], ['SCR'])
				filter += _filterMetadata([i for i in filterLd if _filterDebrid(i) and not _filterFlag(i, 'premium')], ['SCR'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'direct') and not _filterDebrid(i) and not _filterFlag(i, 'premium')], ['SCR'])
			if serviceSelectionMembers:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'memberonly') and not _filterFlag(i, 'premium') and not _filterDebrid(i) and not _filterFlag(i, 'direct')], ['SCR'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if not not _filterFlag(i, 'premium') and _filterDebrid(i) and not _filterFlag(i, 'direct') and not _filterFlag(i, 'memberonly')], ['SCR'])

			# CAM1080
			if serviceSelectionDebrid:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'premium')], ['CAM1080'])
				filter += _filterMetadata([i for i in filterLd if _filterDebrid(i) and not _filterFlag(i, 'premium')], ['CAM1080'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'direct') and not _filterDebrid(i) and not _filterFlag(i, 'premium')], ['CAM1080'])
			if serviceSelectionMembers:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'memberonly') and not _filterFlag(i, 'premium') and not _filterDebrid(i) and not _filterFlag(i, 'direct')], ['CAM1080'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if not not _filterFlag(i, 'premium') and _filterDebrid(i) and not _filterFlag(i, 'direct') and not _filterFlag(i, 'memberonly')], ['CAM1080'])

			# CAM720
			if serviceSelectionDebrid:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'premium')], ['CAM720'])
				filter += _filterMetadata([i for i in filterLd if _filterDebrid(i) and not _filterFlag(i, 'premium')], ['CAM720'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'direct') and not _filterDebrid(i) and not _filterFlag(i, 'premium')], ['CAM720'])
			if serviceSelectionMembers:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'memberonly') and not _filterFlag(i, 'premium') and not _filterDebrid(i) and not _filterFlag(i, 'direct')], ['CAM720'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if not not _filterFlag(i, 'premium') and _filterDebrid(i) and not _filterFlag(i, 'direct') and not _filterFlag(i, 'memberonly')], ['CAM720'])

			# CAM
			if serviceSelectionDebrid:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'premium')], ['CAM'])
				filter += _filterMetadata([i for i in filterLd if _filterDebrid(i) and not _filterFlag(i, 'premium')], ['CAM'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'direct') and not _filterDebrid(i) and not _filterFlag(i, 'premium')], ['CAM'])
			if serviceSelectionMembers:
				filter += _filterMetadata([i for i in filterLd if _filterFlag(i, 'memberonly') and not _filterFlag(i, 'premium') and not _filterDebrid(i) and not _filterFlag(i, 'direct')], ['CAM'])
			if serviceSelectionFree:
				filter += _filterMetadata([i for i in filterLd if not not _filterFlag(i, 'premium') and _filterDebrid(i) and not _filterFlag(i, 'direct') and not _filterFlag(i, 'memberonly')], ['CAM'])

			items += _filterMetadata(filter, ['SCR1080', 'SCR720', 'SCR', 'CAM1080', 'CAM720', 'CAM'])

			####################################################################################
			# METADATA SORT EXTERNAL
			####################################################################################

			# Reverse video quality order.
			if filterSortQuality == 1:
				filter = []
				order = metadatax.Metadata.VideoQualityOrder
				for o in order:
					for i in items:
						if i['quality'] == o:
							filter.append(i)
				items = filter

			# Sort according to provider
			if filterSortPrimary == 1:
				filter1 = []
				filter2 = []
				filter3 = items
				filter4 = []

				# Always list local first.
				for j in filter3:
					try:
						if j['local']:
							filter1.append(j)
						else:
							filter2.append(j)
					except:
						filter2.append(j)
				filter3 = filter2
				filter2 = []

				# Rest of the items sorted according to provider.
				for i in range(1,11):
					setting = _filterSetting('sort.provider%d' % i)
					if not setting == None and not setting == '':
						filter4 = []
						for j in filter3:
							if setting == j['provider']:
								filter4.append(j)
							else:
								filter2.append(j)

						if filterSortSecondary:
							if filterSortAge == 4: filter4 = _filterAge(filter4)
							if filterSortSeeds == 4: filter4 = _filterSeeds(filter4)
							if filterSortSize == 4: filter4 = _filterSize(filter4)
							if filterSortPopularity == 4: filter4 = _filterPopularity(filter4)
						filter1.extend(filter4)

						filter3 = filter2
						filter2 = []

				if filterSortSecondary:
					if filterSortAge == 4: filter3 = _filterAge(filter3)
					if filterSortSeeds == 4: filter3 = _filterSeeds(filter3)
					if filterSortSize == 4: filter3 = _filterSize(filter3)
					if filterSortPopularity == 4: filter3 = _filterPopularity(filter3)
				items = filter1 + filter3

			# Sort according to priority
			if tools.Converter.boolean(_filterSetting('sort.priority.enabled')):
				filter = [[], [], [], [], []]
				optionLocal = int(_filterSetting('sort.priority.local'))
				optionPremium = int(_filterSetting('sort.priority.premium'))
				optionCached = int(_filterSetting('sort.priority.cached'))
				optionDirect = int(_filterSetting('sort.priority.direct'))

				for i in items:
					if 'local' in i and i['local']:
						filter[optionLocal].append(i)
					elif 'premium' in i and i['premium']:
						filter[optionPremium].append(i)
					elif 'cache' in i and debridx.Debrid.cachedAny(i['cache']):
						filter[optionCached].append(i)
					elif 'direct' in i and i['direct']:
						filter[optionDirect].append(i)
					else:
						filter[0].append(i)

				if filterSortSecondary:
					if filterSortAge == 5:
						filter[0] = _filterAge(filter[0])
						filter[1] = _filterAge(filter[1])
						filter[2] = _filterAge(filter[2])
						filter[3] = _filterAge(filter[3])
						filter[4] = _filterAge(filter[4])
					if filterSortSeeds == 5:
						filter[0] = _filterSeeds(filter[0])
						filter[1] = _filterSeeds(filter[1])
						filter[2] = _filterSeeds(filter[2])
						filter[3] = _filterSeeds(filter[3])
						filter[4] = _filterSeeds(filter[4])
					if filterSortSize == 5:
						filter[0] = _filterSize(filter[0])
						filter[1] = _filterSize(filter[1])
						filter[2] = _filterSize(filter[2])
						filter[3] = _filterSize(filter[3])
						filter[4] = _filterSize(filter[4])
					if filterSortPopularity == 5:
						filter[0] = _filterPopularity(filter[0])
						filter[1] = _filterPopularity(filter[1])
						filter[2] = _filterPopularity(filter[2])
						filter[3] = _filterPopularity(filter[3])
						filter[4] = _filterPopularity(filter[4])

				items = filter[1] + filter[2] + filter[3] + filter[4] + filter[0]

			if filterSortSecondary:
				if filterSortAge == 2: items = _filterAge(items)
				if filterSortSeeds == 2: items = _filterSeeds(items)
				if filterSortSize == 2: items = _filterSize(items)
				if filterSortPopularity == 2: items = _filterPopularity(items)

			####################################################################################
			# POSTPROCESSING
			####################################################################################

			# Filter out duplicates (for original movie title)
			# This must be done at the end, because the filters someties add duplicates (eg: the filterDebrid, filterMember, and filterFree functions).
			# Can also happen if a link is member and debrid, will be filtered and added twice.
			if filterRemovalDuplicates:
				items = self.sourcesRemoveDuplicates(items)

			# Filter - Limit
			if filterGeneralLimit > 0:
				items = items[:filterGeneralLimit]
		except:
			tools.Logger.error()

		self.countFilters = len(items)
		tools.Logger.log('Scraping Streams After Filtering: ' + str(self.countFilters), name = 'CORE', level = tools.Logger.TypeNotice)

		return items

	def sourcesPrepare(self, items):
		try:
			# Convert Quality
			for i in range(len(items)):
				items[i]['quality'] = metadatax.Metadata.videoQualityConvert(items[i]['quality'])

			# Create Metadata
			for i in range(len(items)):
				metadatax.Metadata.initialize(source = items[i])
		except:
			tools.Logger.error()
		return items

	def sourcesLabel(self, items, metadata):
		try:
			if not self.navigationStreamsSpecial:
				duration = self._duration(metadata)

				handlePremiumize = handler.HandlePremiumize()
				premiumize = debridx.Premiumize()
				premiumizeEnabled = premiumize.accountValid()

				debridLabel = interface.Translation.string(33209)
				premiumInformation = tools.Settings.getBoolean('interface.information.premium.enabled')

				# Use the same object, because otherwise it will send a lot of account status request to the Premiumize server, each time a new Premiumize instance is created inside the for-loop.
				premiumizeInformation = tools.Settings.getInteger('interface.information.premium.premiumize')
				premiumizeInformationUsage = None
				if premiumInformation and premiumizeInformation > 0 and premiumizeEnabled:
					if premiumizeInformation == 1 or premiumizeInformation == 2:
						try: premiumizeInformationUsage = premiumize.account()['usage']['consumed']['description']
						except: pass

				easynews = debridx.EasyNews()
				easynewsInformation = tools.Settings.getInteger('interface.information.premium.easynews')
				easynewsInformationUsage = None
				if premiumInformation and easynewsInformation > 0 and easynews.accountValid():
					try:
						easynewsInformationUsage = []
						usage = easynews.account()['usage']
						if easynewsInformation == 1: easynewsInformationUsage.append('%s Consumed' % (usage['consumed']['description']))
						elif easynewsInformation == 2: easynewsInformationUsage.append('%s Remaining' % (usage['remaining']['description']))
						elif easynewsInformation == 3: easynewsInformationUsage.append('%s Total' % (usage['total']['size']['description']))
						elif easynewsInformation == 4: easynewsInformationUsage.append('%s Consumed' % (usage['consumed']['size']['description']))
						elif easynewsInformation == 5: easynewsInformationUsage.append('%s Remaining' % (usage['remaining']['size']['description']))
						elif easynewsInformation == 6: easynewsInformationUsage.append('%s (%s) Consumed' % (usage['consumed']['size']['description'], usage['consumed']['description']))
						elif easynewsInformation == 7: easynewsInformationUsage.append('%s (%s) Remaining' % (usage['remaining']['size']['description'], usage['remaining']['description']))
						if len(easynewsInformationUsage) == 0: easynewsInformationUsage = None
						else: easynewsInformationUsage = interface.Format.fontSeparator().join(easynewsInformationUsage)
					except:
						easynewsInformationUsage = None

				precheck = tools.System.developers() and tools.Settings.getBoolean('scraping.precheck.enabled')
				layout = tools.Settings.getInteger('interface.information.layout')
				layoutColor = tools.Settings.getBoolean('interface.information.layout.color')
				layoutPadding = tools.Settings.getInteger('interface.information.layout.padding') # Try with Confluence. 3 and 3.5 is not enough. 4 by default.
				layoutShort = layout == 0
				layoutLong = layout == 1
				layoutMultiple = layout == 2

				layoutFile = False
				layoutFileUpper = False
				layoutFileLower = False
				if layout > 2:
					layoutFile = True
					layoutShort = layout == 3
					layoutLong = layout == 4
					layoutMultiple = layout >= 5
					layoutFileUpper = layout == 5
					layoutFileLower = layout == 6

				layoutType = tools.Settings.getInteger('interface.information.type')
				layoutProvider = tools.Settings.getInteger('interface.information.provider')
				layoutSource = tools.Settings.getInteger('interface.information.source')

				layoutQuality = tools.Settings.getInteger('interface.information.quality')
				layoutMode = tools.Settings.getInteger('interface.information.mode')
				layoutPack = tools.Settings.getInteger('interface.information.pack')
				layoutRelease = tools.Settings.getInteger('interface.information.release')
				layoutUploader = tools.Settings.getInteger('interface.information.uploader')
				layoutEdition = tools.Settings.getInteger('interface.information.edition')
				layoutPopularity = tools.Settings.getInteger('interface.information.popularity')
				layoutAge = tools.Settings.getInteger('interface.information.age')
				layoutSeeds = tools.Settings.getInteger('interface.information.seeds')

				for i in range(len(items)):
					try: duration = self._duration(items[i]['meta'])
					except: pass

					source = items[i]['source'].lower().rsplit('.', 1)[0]
					pro = re.sub('v\d+$', '', items[i]['providerlabel'])
					meta = items[i]['metadata']

					infos = []
					debridHas = 'debrid' in items[i] and any(i for i in items[i]['debrid'].itervalues())
					number = '%s%s'

					if layoutShort or layoutLong:
						infos.append(meta.information(format = True, precheck = precheck, information = metadatax.Metadata.InformationEssential, quality = layoutQuality, mode = layoutMode, pack = layoutPack, release = layoutRelease, uploader = layoutUploader, edition = layoutEdition, seeds = layoutSeeds, duration = duration))

					if layoutType > 0:
						if source == 'torrent': value = 'torrent'
						elif source == 'usenet': value = 'usenet'
						elif 'local' in items[i] and items[i]['local']: value = 'local'
						elif 'premium' in items[i] and items[i]['premium']: value = 'premium'
						else: value = 'hoster'
						if layoutType == 1: value = value[:1]
						elif layoutType == 2: value = value[:3]
						value = interface.Format.font(value, bold = True, color = interface.Format.ColorMain, uppercase = True)
						infos.append(value)

					if layoutProvider > 0 and not pro == None and not pro == '' and not pro == '0':
						if 'orion' in items[i]:
							value = interface.Format.font(orionoid.Orionoid.Name, color = interface.Format.ColorOrion, bold = True, uppercase = True)
							infos.append(value)
						value = pro
						if layoutProvider == 1: value = value[:3]
						elif layoutProvider == 2: value = value[:6]
						value = interface.Format.font(value, bold = True, uppercase = True)
						infos.append(value)

					if layoutSource > 0 and not source == None and not source == '' and not source == '0' and not source == pro:
						if not source == 'torrent' and not source == 'usenet' and not ('local' in items[i] and items[i]['local']) and not ('premium' in items[i] and items[i]['premium']):
							try: same = source.lower() == pro.lower()
							except: same = False
							if not same:
								value = source
								if layoutSource == 1: value = value[:3]
								elif layoutSource == 2: value = value[:6]
								value = interface.Format.font(value, uppercase = True)
								infos.append(value)

					if not layoutShort and 'exact' in items[i] and items[i]['exact'] and 'file' in items[i] and items[i]['file']:
						infos.append(items[i]['file'])

					if layoutPopularity and not meta.popularity() is None:
						infos.append(meta.popularity(format = True, color = True, label = layoutPopularity))

					if layoutAge and not meta.age() is None:
						infos.append(meta.age(format = True, color = True, label = layoutAge))

					labelTop = interface.Format.fontSeparator().join(infos)

					if premiumizeEnabled and premiumizeInformation > 0 and ((not('direct' in items[i] and items[i]['direct']) and debridHas and handlePremiumize.supported(items[i]) or source == 'premiumize')):
						try: # Somtimes Premiumize().service(source) failes. In such a case, just ignore it.
							cost = None
							limit = None
							service = premiumize.service(source)
							if service:
								if premiumizeInformation == 1 or premiumizeInformation == 2:
									cost = service['usage']['factor']['description']
							information = []
							if cost: information.append(cost)
							if premiumizeInformationUsage: information.append(premiumizeInformationUsage)
							if limit: information.append(limit)
							if len(information) > 0: labelTop += interface.Format.fontSeparator() + interface.Format.fontSeparator().join(information)
						except:
							tools.Logger.error()
							pass
					elif pro.lower() == 'easynews' and easynewsInformationUsage:
						labelTop += interface.Format.fontSeparator() + easynewsInformationUsage

					labelTop = re.sub(' +',' ', labelTop)
					label = ''

					if layoutShort:
						label = labelTop
					elif layoutLong:
						labelBottom = meta.information(format = True, sizeLimit = True, precheck = precheck, information = metadatax.Metadata.InformationNonessential, color = layoutColor, quality = layoutQuality, mode = layoutMode, pack = layoutPack, release = layoutRelease, uploader = layoutUploader, edition = layoutEdition, seeds = layoutSeeds, duration = duration)
						labelBottom = re.sub(' +',' ', labelBottom)
						label = labelTop + interface.Format.fontSeparator() + labelBottom
					elif layoutMultiple:
						labelBottom = meta.information(format = True, sizeLimit = True, precheck = precheck, color = layoutColor, quality = layoutQuality, mode = layoutMode, pack = layoutPack, release = layoutRelease, uploader = layoutUploader, edition = layoutEdition, seeds = layoutSeeds, duration = duration)
						labelBottom = re.sub(' +',' ', labelBottom)
						if layoutPadding <= 0:
							spaceTop = ''
							spaceBottom = ''
						else:
							# Spaces needed, otherwise the second line is cut off when shorter than the first line
							spaceTop = len(number)
							spaceBottom = 0
							lengthTop = len(re.sub('\\[(.*?)\\]', '', labelTop))
							lengthBottom = len(re.sub('\\[(.*?)\\]', '', labelBottom))
							if lengthBottom > lengthTop:
								spaceTop = int((lengthBottom - lengthTop) * layoutPadding)
							else:
								spaceBottom = int((lengthBottom - lengthTop) * layoutPadding)
							spaceTop = ' ' * max(8, spaceTop)
							spaceBottom = ' ' * max(8, spaceBottom)
						label = labelTop + spaceTop + interface.Format.fontNewline() + labelBottom + spaceBottom

					if layoutFile:
						file = ''
						if 'file' in items[i] and items[i]['file']:
							file = items[i]['file'] + interface.Format.fontSeparator()

						if layoutShort:
							label = file + labelTop
						elif layoutLong:
							label = file + labelTop + interface.Format.fontSeparator() + labelBottom
						else:
							if layoutFileUpper:
								labelBottom = labelTop + interface.Format.fontSeparator() + labelBottom
								labelTop = file
							elif layoutFileLower:
								labelTop = labelTop + interface.Format.fontSeparator() + labelBottom
								labelBottom = file

							if layoutPadding <= 0:
								spaceTop = ''
								spaceBottom = ''
							else:
								# Spaces needed, otherwise the second line is cut off when shorter than the first line
								spaceTop = len(number)
								spaceBottom = 0
								lengthTop = len(re.sub('\\[(.*?)\\]', '', labelTop))
								lengthBottom = len(re.sub('\\[(.*?)\\]', '', labelBottom))
								if lengthBottom > lengthTop:
									spaceTop = int((lengthBottom - lengthTop) * layoutPadding)
								else:
									spaceBottom = int((lengthBottom - lengthTop) * layoutPadding)
								spaceTop = ' ' * max(8, spaceTop)
								spaceBottom = ' ' * max(8, spaceBottom)

							label = labelTop + spaceTop + interface.Format.fontNewline() + labelBottom + spaceBottom

					items[i]['label'] = number + label.replace('%', '%%')
		except:
			tools.Logger.error()
		return items

	def sourcesCloud(self, item):
		result = self.sourcesResolve(item = item, info = True, handleMode = handler.Handler.ModeSelection, cloud = True)
		if result['success']: interface.Dialog.notification(title = 33229, message = 33230, icon = interface.Dialog.IconSuccess)

	def sourcesResult(self, error = None, id = None, link = None, local = False):
		if error == None and not local:
			if not network.Networker.linkIs(link):
				error = 'unknown'
		return {
			'success' : (error == None),
			'error' : error,
			'id' : id,
			'link' : link,
		}

	def sourcesResolve(self, item, info = False, internal = False, download = False, handle = None, handleMode = None, handleClose = True, resolve = network.Networker.ResolveService, cloud = False):
		try:
			self.downloadCanceled = False
			log = True
			if not internal: self.url = None
			u = url = item['url']

			if resolve == network.Networker.ResolveNone:
				self.url = url
				return self.sourcesResult(link = url)

			popups = (not internal)

			# Fails for NaN providers.
			try:
				found = False
				for i in [item['source'], item['source'].lower(), item['providerid'], item['provider'], item['provider'].lower()]:
					if i in self.externalServices:
						source = self.externalServices[i]['object']
						found = True
						break
				if not found:
					source = provider.Provider.provider(item['providerid'], enabled = False, local = True)
					if source:
						source = source['object']
					else:
						# force: get all providers in case of resolving for "disabled" preset providers. Or for historic links when the used providers were disabled.
						provider.Provider.initialize(forceAll = True)
						source = provider.Provider.provider(item['providerid'], enabled = False, local = True)['object']

				try:
					# To accomodate Torba's popup dialog.
					u = url = source.resolve(url, internal = internal)
				except:
					u = url = source.resolve(url)

				if not item['source'] == 'torrent' and not item['source'] == 'usenet':
					item['source'] = network.Networker.linkDomain(u).lower()
			except:
				u = url

			if resolve == network.Networker.ResolveProvider:
				self.url = url
				return self.sourcesResult(link = url)

			# Allow magnet links and local files.
			#if url == None or not '://' in str(url): raise Exception()
			isLocalFile = ('local' in item and item['local']) or tools.File.exists(url)
			if isLocalFile:
				self.url = url
				return self.sourcesResult(link = url, local = True)

			if url == None or (not isLocalFile and not '://' in str(url) and not 'magnet:' in str(url)):
				raise Exception('Error Resolve')

			if not internal:
				metadatax.Metadata.initialize(source = item, title = item['titleadapted'], name = item['file'] if 'file' in item else None, quality = item['quality'])

			sourceHandler = handler.Handler()
			if handle == None:
				handle = sourceHandler.serviceDetermine(mode = handleMode, item = item, popups = popups)
				if handle == handler.Handler.ReturnUnavailable or handle == handler.Handler.ReturnExternal or handle == handler.Handler.ReturnCancel:
					info = False
					url = None
					self.downloadCanceled = (handle == handler.Handler.ReturnCancel)
					raise Exception('Error Handler')

			result = sourceHandler.handle(link = u, item = item, name = handle, download = download, popups = popups, close = handleClose, mode = handleMode, cloud = cloud)

			if not result['success']:
				if result['error'] == handler.Handler.ReturnUnavailable or result['error'] == handler.Handler.ReturnExternal or result['error'] == handler.Handler.ReturnCancel:
					info = False
					url = None
					self.downloadCanceled = (result['error'] == handler.Handler.ReturnCancel)
					if result['error'] == handler.Handler.ReturnExternal: log = False
					raise Exception('Error Handle: ' + result['error'])
				else:
					raise Exception('Error Url: ' + result['error'])

			ext = result['link'].split('?')[0].split('&')[0].split('|')[0].rsplit('.')[-1].replace('/', '').lower()
			extensions = ['rar', 'zip', '7zip', '7z', 's7z', 'tar', 'gz', 'gzip', 'iso', 'bz2', 'lz', 'lzma', 'dmg']
			if ext in extensions:
				if info == True:
					message = interface.Translation.string(33757) % ext.upper()
					interface.Dialog.notification(title = 33448, message = message, icon = interface.Dialog.IconError)
				try: orionoid.Orionoid().streamVote(idItem = item['orion']['item'], idStream = item['orion']['stream'], vote = orionoid.Orionoid.VoteDown)
				except: pass
				return self.sourcesResult(error = 'filetype')

			try: headers = result['link'].rsplit('|', 1)[1]
			except: headers = ''
			headers = urllib.quote_plus(headers).replace('%3D', '=') if ' ' in headers else headers
			headers = dict(urlparse.parse_qsl(headers))

			if result['link'].startswith('http') and '.m3u8' in result['link']:
				resultRequest = client.request(url.split('|')[0], headers=headers, output='geturl', timeout='20')
				if resultRequest == None:
					raise Exception('Error M3U8')
			elif result['link'].startswith('http'):
				# Some Premiumize hoster links, eg Vidto, return a 403 error when doing this precheck with client.request, even though the link works.
				# Do not conduct these prechecks for debrid services. If there is a problem with the link, the Kodi player will just fail.
				if not 'handle' in result or not result['handle'] in [i['id'] for i in handler.Handler.handles()]:
					resultRequest = client.request(result['link'].split('|')[0], headers=headers, output='chunk', timeout='20')
					if resultRequest == None:
						raise Exception('Error Server')

			if not internal: self.url = result['link']
			return result
		except:
			if log: tools.Logger.error()
			if info == True:
				interface.Dialog.notification(title = 33448, message = 33449, icon = interface.Dialog.IconError)
			try: orionoid.Orionoid().streamVote(idItem = item['orion']['item'], idStream = item['orion']['stream'], vote = orionoid.Orionoid.VoteDown)
			except: pass
			return self.sourcesResult(link = url, error = 'unknown')

	def sourcesDialog(self, items, metadata, handleMode = None):
		try:
			self.progressClose()
			labels = [re.sub(' +', ' ', i['label'].replace(interface.Format.newline(), ' %s ' % interface.Format.separator()).strip()) for i in items]
			choice = control.selectDialog(labels)
			if choice < 0: return ''
			self.play(items[choice], metadata = metadata, handleMode = handleMode)
			return ''
		except:
			tools.Logger.error()


	def sourcesDirect(self, items, title, year, season, episode, imdb, tvdb, meta):
		def _filterDebrid(source):
			return any(i for i in source['debrid'].itervalues())

		filter = [i for i in items if i['source'].lower() in self.hostcapDict and not _filterDebrid(i)]
		items = [i for i in items if not i in filter]

		filter = [i for i in items if i['source'].lower() in self.hostblockDict and not _filterDebrid(i)]
		items = [i for i in items if not i in filter]

		items = [i for i in items if ('autoplay' in i and i['autoplay'] == True) or not 'autoplay' in i]
		url = None

		tmdb = meta['tmdb'] if 'tmdb' in meta else None
		tmdb = meta['tmdb'] if 'tmdb' in meta else None
		tmdb = meta['tmdb'] if 'tmdb' in meta else None

		try:
			tools.Time.sleep(1)
			heading = interface.Translation.string(33451)
			message = interface.Translation.string(33452)
			self.progressPlaybackInitialize(title = heading, message = message, metadata = meta)
		except:
			pass

		autoHandler = handler.Handler()
		for i in range(len(items)):
			if self.progressPlaybackCanceled(): break
			if xbmc.abortRequested == True: break
			percentage = int(((i + 1) / float(len(items))) * 100)
			self.progressPlaybackUpdate(progress = percentage, title = heading, message = message)
			try:
				handle = autoHandler.serviceDetermine(mode = handler.Handler.ModeDefault, item = items[i], popups = False)
				if not handle == handler.Handler.ReturnUnavailable:
					result = self.sourcesResolve(items[i], handle = handle, info = False)
					items[i]['urlresolved'] = result['link']
					items[i]['stream'] = result
					if result['success']:
						if self.progressPlaybackCanceled(): break
						if xbmc.abortRequested == True: break
						from resources.lib.modules.player import player
						player(type = self.type, kids = self.kids).run(self.type, title, year, season, episode, imdb, tmdb, tvdb, items[i]['urlresolved'], meta, handle = handle, source = items[i])
						return items[i]
			except:
				tools.Logger.error()

		self.progressPlaybackClose()
		interface.Dialog.notification(title = 33448, message = 33574, sound = False, icon = interface.Dialog.IconInformation)
		return None


	def getConstants(self, loader = False):
		self.propertyItems = 'GaiaItems'
		self.propertyExtras = 'GaiaExtras'
		self.propertyMeta = 'GaiaMeta'

		self.hostDict = []
		try: self.hostDict.extend(handler.HandleUrlResolver().services())
		except: pass
		try: self.hostDict.extend(handler.HandleResolveUrl().services())
		except: pass

		self.hostprDict = ['1fichier.com', 'oboom.com', 'rapidgator.net', 'rg.to', 'uploaded.net', 'uploaded.to', 'ul.to', 'filefactory.com', 'nitroflare.com', 'turbobit.net', 'uploadrocket.net']
		self.hostcapDict = ['hugefiles.net', 'kingfiles.net', 'openload.io', 'openload.co', 'oload.tv', 'thevideo.me', 'vidup.me', 'streamin.to', 'torba.se']
		self.hostblockDict = []

		self.debridServices = debrid.services()

		self.externalServices = {}
		providers = provider.Provider.providers(enabled = True, local = False)
		for pro in providers:
			for i in pro['domains']:
				self.externalServices[i] = pro
				i = i.lower()
				self.externalServices[i.replace('.', '').replace('-', '').replace('_', '')] = pro
				if '.' in i: self.externalServices[i[:i.index('.')]] = pro
				if '-' in i: self.externalServices[i[:i.index('-')]] = pro
				if '_' in i: self.externalServices[i[:i.index('_')]] = pro

	def getLocalTitle(self, title, imdb, tvdb, content):
		language = self.getLanguage()
		if not language: return title
		if content.startswith('movie'):
			titleForeign = trakt.getMovieTranslation(imdb, language)
		else:
			titleForeign = tvmaze.tvMaze().getTVShowTranslation(tvdb, language)
		return titleForeign or title


	def getAliasTitles(self, imdb, localtitle, content):
		try:
			localtitle = localtitle.lower()
			language = self.getLanguage()
			titleForeign = trakt.getMovieAliases(imdb) if content.startswith('movie') else trakt.getTVShowAliases(imdb)
			return [i for i in titleForeign if i.get('country', '').lower() in [language, '', 'us'] and not i.get('title', '').lower() == localtitle]
		except:
			return []


	def getLanguage(self):
		if tools.Language.customization():
			language = tools.Settings.getString('scraping.foreign.language')
		else:
			language = tools.Language.Alternative
		return tools.Language.code(language)
