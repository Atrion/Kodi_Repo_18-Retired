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

import re,urllib,urlparse,threading
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['fr']
		self.domains = ['ww6.cpasbiens.co', 'ww1.cpabien.xyz']
		self.base_link = 'https://ww6.cpasbiens.co' # NB: Only 2 w, otherwise the search does not work.
		self.search_link = '/search_torrent/%s/%s.html'
		self.type_movies = 'films'
		self.type_shows = 'series'

	def _link(self, url, index):
		try:
			html = BeautifulSoup(client.request(url))
			links = html.find_all('a')
			link = None
			for i in links:
				i = i.get('href')
				if i.startswith('magnet:'):
					link = i
					break
			self.tLock.acquire()
			self.tSources[index]['url'] = link
		except:
			tools.Logger.error()
		finally:
			try: self.tLock.release()
			except: pass

	def _search(self, url, query, show, type, title, titles, year, season, episode, pack, packCount, packException, ignoreContains):
		pageLimit = tools.Settings.getInteger('scraping.providers.pages')
		pageCounter = 0
		page = 0
		added = False

		try:
			while True:
				pageCounter += 1
				if pageLimit > 0 and pageCounter > pageLimit:
					break

				html = BeautifulSoup(client.request(url % (type, query)))

				page += 1
				added = False

				htmlTable = html.find_all('table', class_ = 'table-corps')
				if len(htmlTable) > 0:
					htmlTable = htmlTable[0]
					try: htmlTable = htmlTable.find_all('tbody', recursive = False)[0]
					except: pass
					htmlRows = htmlTable.find_all('tr', recursive = False)
					for i in range(len(htmlRows)):
						htmlRow = htmlRows[i]
						htmlColumns = htmlRow.find_all('td', recursive = False)

						# Name
						htmlName = htmlColumns[0].find_all('a')[0].getText().strip()

						# Link
						htmlLink = urlparse.urljoin(self.base_link, htmlColumns[0].find_all('a')[0].get('href').encode('utf-8'))

						# Size
						htmlSize = re.sub('([mMkKgGtT]?)[oO]', '\\1b', htmlColumns[0].find_all('div', class_ = 'poid')[0].getText())
						if not 'b' in htmlSize: htmlSize = htmlSize + ' mb'

						# Seeds
						try: htmlSeeds = int(htmlColumns[0].find_all('div', class_ = 'up')[0].getText().strip())
						except: htmlSeeds = None

						# Metadata
						meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

						# Ignore
						meta.ignoreAdjust(contains = ignoreContains)
						if meta.ignore(True, season = not packException): continue

						# Add
						self.tLock.acquire()
						self.tSources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
						self.tLock.release()
						added = True

						self.tLock.acquire()
						thread = threading.Thread(target = self._link, args = (htmlLink, len(self.tSources) - 1))
						self.tThreadsLinks.append(thread)
						self.tLock.release()
						thread.start()

				# Only shows 1 page.
				break
		except:
			tools.Logger.error()
		finally:
			try: self.tLock.release()
			except: pass

	def sources(self, url, hostDict, hostprDict):
		self.tSources = []
		try:
			if url == None: raise Exception()

			ignoreContains = None
			data = self._decode(url)

			show = 'tvshowtitle' in data
			type = self.type_shows if 'tvshowtitle' in data else self.type_movies

			if 'exact' in data and data['exact']:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = None
				queries = [title]
				year = None
				season = None
				episode = None
				pack = False
				packCount = None
				packExceptions = None
			else:
				title = data['tvshowtitle'] if show else data['title']
				titles = data['alternatives'] if 'alternatives' in data else None
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False
				packCount = data['packcount'] if 'packcount' in data else None
				packExceptions = None
				if show:
					# Search special episodes by name. All special episodes are added to season 0 by Trakt and TVDb. Hence, do not search by filename (eg: S02E00), since the season is not known.
					if (season == 0 or episode == 0) and ('title' in data and not data['title'] == None and not data['title'] == ''):
						title = '%s %s' % (data['tvshowtitle'], data['title']) # Change the title for metadata filtering.
						queries = [title]
						ignoreContains = len(data['title']) / float(len(title)) # Increase the required ignore ration, since otherwise individual episodes and season packs are found as well.
					else:
						if pack:
							queries = ['%s S%02d' % (title, season), '%s saison %d' % (title, season), '%s intégrale' % title]
							packExceptions = [2] # Index of query where season pack file name detection should be ignored.
						else:
							queries = ['%s S%02dE%02d' % (title, season, episode)]
				else:
					queries = ['%s %d' % (title, year)]
				queries = [re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query) for query in queries]

			if not self._query(queries): return self.tSources

			url = urlparse.urljoin(self.base_link, self.search_link)
			queries = [urllib.quote(query) for query in queries] # quote_plus does not work.

			timerTimeout = tools.Settings.getInteger('scraping.providers.timeout')
			timerEnd = timerTimeout - 8
			timer = tools.Time(start = True)

			self.tThreadsSearches = []
			self.tThreadsLinks = []
			self.tLock = threading.Lock()

			for q in range(len(queries)):
				query = queries[q]
				packException = True if packExceptions and q in packExceptions else False
				thread = threading.Thread(target = self._search, args = (url, query, show, type, title, titles, year, season, episode, pack, packCount, packException, ignoreContains))
				self.tThreadsSearches.append(thread)
				thread.start()

			while True:
				if timer.elapsed() > timerTimeout: break
				if not any([t.is_alive() for t in self.tThreadsSearches]): break
				tools.Time.sleep(0.5)

			# First filter out all non-related links before doing the hash lookup.
			timerTimeout -= 2
			while True:
				if timer.elapsed() > timerTimeout: break
				if not any([t.is_alive() for t in self.tThreadsLinks]): break
				tools.Time.sleep(0.5)

			try: self.tLock.release()
			except: pass

			return self.tSources
		except:
			tools.Logger.error()
			try: self.tLock.release()
			except: pass
			return self.tSources
