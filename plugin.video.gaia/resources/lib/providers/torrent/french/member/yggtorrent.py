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
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import network
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:

	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['fr']
		self.domains = ['yggtorrent.gg', 'yggtorrent.site', 'yggtorrent.is']
		self.base_link = 'https://www2.yggtorrent.gg' # www subdomain does not work.
		self.search_link = '/engine/search?category=%s&subcategory=%s&name=%s&page=%s&order=desc&sort=seed&do=search'
		self.download_link = '/engine/download_torrent?id='
		self.login_link = '/user/login'
		self.category_video = 2145
		self.subcategory_any = "all"
		self.subcategories_show = {'Série TV': '2184'}
		self.subcategories_movie = {'Film': '2183', 'Animation': '2178'}

		self.username = tools.Settings.getString('accounts.providers.yggtorrent.user')
		self.password = tools.Settings.getString('accounts.providers.yggtorrent.pass')
		self.inspection = tools.Settings.getBoolean('accounts.providers.yggtorrent.inspection')
		self.enabled = tools.Settings.getBoolean('accounts.providers.yggtorrent.enabled') and self.username and self.password

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

	def _authenticate(self, url):
		login = self.base_link + self.login_link
		form = urllib.urlencode({'id' : self.username, 'pass' : self.password})
		cookie = client.request(login, post = form, output = 'cookie')
		if cookie: url += '|Cookie=' + urllib.quote_plus(cookie)
		return url

	def sources(self, url, hostDict, hostprDict):
		self.tSources = []
		try:
			if url == None:
				raise Exception()

			if not self.enabled or self.username == '' or self.password == '':
				raise Exception()

			data = urlparse.parse_qs(url)

			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			show = 'tvshowtitle' in data
			title = data['tvshowtitle'] if show else data['title']
			titleYear = '%s S%02dE%02d' % (data['tvshowtitle'], int(data['season']), int(data['episode'])) if show else '%s (%s)' % (data['title'], data['year'])

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = None
				season = None
				episode = None
				pack = False
				packCount = None
			else:
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False
				packCount = data['packcount'] if 'packcount' in data else None

				if show: subcategory = self.subcategories_show.values()[0] if len(self.subcategories_show) == 1 else self.subcategory_any
				else: subcategory = self.subcategories_movie.values()[0] if len(self.subcategories_movie) == 1 else self.subcategory_any

				if show:
					if pack: query = '%s S%02d' % (title, season)
					else: query = '%s S%02dE%02d' % (title, season, episode)
				else:
					query = '%s %d' % (title, year)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)
				querySplit = query.split()

			url = urlparse.urljoin(self.base_link, self.search_link)
			query = urllib.quote_plus(query)

			pageLimit = tools.Settings.getInteger('scraping.providers.pages')
			pageCounter = 0

			page = 0
			added = False

			timerTimeout = tools.Settings.getInteger('scraping.providers.timeout')
			timerEnd = timerTimeout - 8
			timer = tools.Time(start = True)

			threads = []
			self.tLock = threading.Lock()
			while True:
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

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
						# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
						if timer.elapsed() > timerEnd:
							break

						htmlRow = htmlRows[i]

						# Name
						htmlInfo = htmlRows[i].find_all('a', href = True)[1]
						htmlName = htmlInfo.getText()

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
						meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)
						
						# Ignore
						if meta.ignore(True):
							continue

						# Add
						self.tLock.acquire()
						self.tSources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
						self.tLock.release()
						added = True

						# Hash
						if self.inspection:
							htmlHash = urllib.quote(str(htmlInfo.get('href').encode('utf-8')), ':/+')
							thread = threading.Thread(target = self._hash, args = (htmlHash, len(self.tSources) - 1))
							threads.append(thread)
							thread.start()

				if not added: # Last page reached with a working torrent
					break

			# First filter out all non-related links before doing the hash lookup.
			if self.inspection:
				timerTimeout -= 2
				while True:
					if timer.elapsed() > timerTimeout: break
					if not any([thread.is_alive() for thread in threads]): break
					tools.Time.sleep(0.3)

			try: self.tLock.release()
			except: pass

			return self.tSources
		except:
			tools.Logger.error()
			try: self.tLock.release()
			except: pass
			return self.tSources

	def resolve(self, url):
		return self._authenticate(url)
