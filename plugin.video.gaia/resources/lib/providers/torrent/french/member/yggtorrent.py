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

import re, urllib, urlparse, json, threading
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import network
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['fr']
		self.domains = ['yggtorrent.ch', 'yggtorrent.gg', 'yggtorrent.site', 'yggtorrent.is']
		self.base_link = 'https://www2.yggtorrent.ch' # www subdomain does not work.
		self.search_link = '/engine/search?category=%s&subcategory=%s&name=%s&page=%s&order=desc&sort=seed&do=search'
		self.download_link = '/engine/download_torrent?id='
		self.login_link = '/user/login'
		self.category_video = 2145
		self.subcategory_any = 'all'
		self.subcategories_show = {'Série TV': '2184'}
		self.subcategories_movie = {'Film': '2183', 'Animation': '2178'}

		self.username = tools.Settings.getString('accounts.providers.yggtorrent.user')
		self.password = tools.Settings.getString('accounts.providers.yggtorrent.pass')
		self.inspection = tools.Settings.getBoolean('accounts.providers.yggtorrent.inspection')
		self.enabled = tools.Settings.getBoolean('accounts.providers.yggtorrent.enabled') and self.username and self.password

	def authenticationAdd(self, links):
		result = []
		for link in links:
			if self._linkValid(link):
				if self.enabled: result.append(link)
			else:
				result.append(link)
		return result

	def authenticationRemove(self, links):
		for i in range(len(links)):
			links[i] = network.Networker._linkClean(links[i])
		return links

	def _authentication(self, url):
		if not '|Cookie' in url: # Avoid adding multiple cookies in case the URL is resolved multiple times.
			link = self.base_link + self.login_link
			data = {'id' : self.username, 'pass' : self.password}

			# NB: Must make two requests.
			# The first request does not have any CloudFlare cookies. YGG will return its own cookie, but it will be an unauthenticated-cookie.
			# Make a second request with the CloudFlare cookies to get an authenticated-cookie.
			# Both requests must use the same networker in order to share the cookie jar.
			net = network.Networker()
			cookies = net.cookies(link = link, parameters = data, raw = True, force = True)
			cookies = net.cookies(link = link, parameters = data, raw = True, force = True, headers = {'Cookie' : cookies})

			if cookies: url += '|Cookie=' + urllib.quote_plus(cookies)
		return url

	def _linkValid(self, link):
		domain = network.Networker.linkDomain(link, subdomain = False, topdomain = True).lower()
		return domain in self.domains

	def _hash(self, url, index):
		try:
			htmlSingle = BeautifulSoup(client.request(url))
			htmlInfo = htmlSingle.find('table', 'informations')
			htmlHash = htmlInfo.find_all('tr')[4].find_all('td')[1].getText()
			self.tLock.acquire()
			if htmlHash: self.tSources[index]['hash'] = htmlHash
		except:
			tools.Logger.error()
		finally:
			try: self.tLock.release()
			except: pass

	def _search(self, url, query, subcategory, show, title, titles, year, season, episode, pack, packCount, packException, ignoreContains):
		pageLimit = tools.Settings.getInteger('scraping.providers.pages')
		pageCounter = 0
		page = 0
		added = False

		try:
			while True:
				pageCounter += 1
				if pageLimit > 0 and pageCounter > pageLimit:
					break

				urlNew = url % (self.category_video, subcategory, query, page)
				html = BeautifulSoup(client.request(urlNew))

				page += 25
				added = False

				htmlTables = html.find_all('table', class_ = 'table')
				if htmlTables:
					htmlTable = htmlTables[0]
					htmlTbody = htmlTable.find_all('tbody')[0]
					htmlRows = htmlTbody.find_all('tr', recursive = False)
					for i in range(len(htmlRows)):
						htmlRow = htmlRows[i]

						# Name
						htmlInfo = htmlRows[i].find_all('a', href = True)[1]
						htmlName = htmlInfo.getText().strip()

						# Category
						if subcategory is self.subcategory_any:
							htmlCategory = htmlRow.find_all('div', class_ = 'hidden')[0].getText()
							if show and len(self.subcategories_show) > 1:
								if htmlCategory not in self.subcategories_show.keys():
									continue
							elif len(self.subcategories_show) > 1:
								if htmlCategory not in self.subcategories_movie.keys():
									continue

						# Size
						htmlSize = re.sub('([mMkKgGtT]?)[oO]', '\\1b', htmlRow.find_all('td')[5].getText())

						# Link
						htmlLink = self.base_link + self.download_link + str(htmlInfo.get('href').encode('utf-8')).split('/')[-1].split('-')[0]

						# Seeds
						htmlSeeds = int(htmlRow.find_all('td')[7].getText())

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

						# Hash
						if self.inspection:
							htmlHash = urllib.quote(str(htmlInfo.get('href').encode('utf-8')), ':/+')
							self.tLock.acquire()
							thread = threading.Thread(target = self._hash, args = (htmlHash, len(self.tSources) - 1))
							self.tThreadsHashes.append(thread)
							self.tLock.release()
							thread.start()

				if not added: # Last page reached with a working torrent
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
			if not self.enabled or self.username == '' or self.password == '': raise Exception()

			ignoreContains = None
			data = self._decode(url)

			show = 'tvshowtitle' in data
			if show: subcategory = self.subcategories_show.values()[0] if len(self.subcategories_show) == 1 else self.subcategory_any
			else: subcategory = self.subcategories_movie.values()[0] if len(self.subcategories_movie) == 1 else self.subcategory_any

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
							queries = ['%s S%02d' % (title, season), '%s saison %d' % (title, season), '%s intégrale' % title, '%s complet' % title]
							packExceptions = [2, 3] # Index of query where season pack file name detection should be ignored.
						else:
							queries = ['%s S%02dE%02d' % (title, season, episode)]
				else:
					queries = ['%s %d' % (title, year)]
				queries = [re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query) for query in queries]

			if not self._query(queries): return self.tSources

			url = urlparse.urljoin(self.base_link, self.search_link)
			queries = [urllib.quote_plus(query) for query in queries]

			timerTimeout = tools.Settings.getInteger('scraping.providers.timeout')
			timerEnd = timerTimeout - 8
			timer = tools.Time(start = True)

			self.tThreadsSearches = []
			self.tThreadsHashes = []
			self.tLock = threading.Lock()

			for q in range(len(queries)):
				query = queries[q]
				packException = True if packExceptions and q in packExceptions else False
				thread = threading.Thread(target = self._search, args = (url, query, subcategory, show, title, titles, year, season, episode, pack, packCount, packException, ignoreContains))
				self.tThreadsSearches.append(thread)
				thread.start()

			while True:
				if timer.elapsed() > timerTimeout: break
				if not any([t.is_alive() for t in self.tThreadsSearches]): break
				tools.Time.sleep(0.5)

			# First filter out all non-related links before doing the hash lookup.
			if self.inspection:
				timerTimeout -= 2
				while True:
					if timer.elapsed() > timerTimeout: break
					if not any([t.is_alive() for t in self.tThreadsHashes]): break
					tools.Time.sleep(0.5)

			try: self.tLock.release()
			except: pass

			return self.tSources
		except:
			tools.Logger.error()
			try: self.tLock.release()
			except: pass
			return self.tSources

	def resolve(self, url):
		return self._authentication(url)
