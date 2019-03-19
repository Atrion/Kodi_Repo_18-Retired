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

import re,urllib,urlparse,xbmc
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import proxy
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:

	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['rarbg.to', 'rarbg.unblocked.cool', 'rarbg.immunicity.cool', 'rarbg.bypassed.cool', 'rarbg.bypassed.cool']
		self.base_link = 'https://rarbg.to'
		self.search_link = '/torrents.php?search=%s&category=%s&page=%d&order=seeders&by=DESC'
		self.magnet_link = 'magnet:?xt=urn:btih:%s&dn=%s&tr=http%%3A%%2F%%2Ftracker.trackerfix.com%%3A80%%2Fannounce&tr=udp%%3A%%2F%%2F9.rarbg.me%%3A2710&tr=udp%%3A%%2F%%2F9.rarbg.to%%3A2710'
		self.torrent_link = 'https://rarbg.to/download.php?id=%s&f=%s.torrent'
		self.category_movies = '14;48;17;44;45;47;42;46'
		self.category_tvshows = '18;41'

		# Disable it if it was previously enabled before it became a developer-only provider.
		if not tools.System.developers():
			tools.Settings.set('providers.universal.torrent.open.rarbg', False)

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

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if not tools.System.developers():
				raise Exception()

			if url == None:
				raise Exception()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = None
				season = None
				episode = None
				pack = False
				packCount = None
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False
				packCount = data['packcount'] if 'packcount' in data else None

				if 'tvshowtitle' in data:
					if pack: query = '%s %d' % (title, season)
					else: query = '%s S%02dE%02d' % (title, season, episode)
				else:
					query = '%s %d' % (title, year)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			category = self.category_tvshows if ('tvshowtitle' in data and not data['tvshowtitle'] == None and not data['tvshowtitle'] == '') else self.category_movies
			url = urlparse.urljoin(self.base_link, self.search_link)

			pageLimit = tools.Settings.getInteger('scraping.providers.pages')
			pageCounter = 0

			page = 1 # Pages start at 1
			added = False

			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 8
			timer = tools.Time(start = True)

			while True:
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

				pageCounter += 1
				if pageLimit > 0 and pageCounter > pageLimit:
					break

				urlNew = url % (urllib.quote_plus(query), category, page)
				data = client.request(urlNew)

				# RarBg's HTML is not valid and a total mess, prababley to make it hard for scrapers.
				# First try to parse the HTML. If it fails, extract only the table from the markup and construct new HTML.
				# Sometimes both fail, seems like RarBg randomizes the corruption in its HTML.
				htmlRows = []
				try:
					html = BeautifulSoup(data)
					htmlTable = html.find_all('table', class_ = 'lista2t')[0]
					htmlRows = htmlTable.find_all('tr', class_ = 'lista2', recursive = False)
					if len(htmlRows) == 0: raise Exception()
				except:
					start = data.find('lista2t')
					if start < 0: raise Exception()
					start += 7
					start = data.find('lista2', start)
					start = data.find('>', start) + 1
					end = data.find('<tr><td align="center" colspan="2">', start)
					data = '<html><body><table class="lista2t"><tr class="lista2">' + data[start : end] + '</table></body></html>'
					html = BeautifulSoup(data)
					htmlTable = html.find_all('table', class_ = 'lista2t')[0]
					htmlRows = htmlTable.find_all('tr', class_ = 'lista2', recursive = False)

				page += 1
				added = False

				for i in range(len(htmlRows)):
					htmlRow = htmlRows[i]
					htmlColumns = htmlRow.find_all('td')
					htmlInfo = htmlColumns[1]

					# Name
					htmlName = htmlInfo.find_all('a')[0].getText().strip()

					# 3D
					htmlImages = htmlInfo.find_all('img')
					for j in range(len(htmlImages)):
						try:
							if htmlImages[j]['src'].endswith('3d.png'):
								htmlName += ' 3D'
								break
						except:
							pass

					# Size
					htmlSize = htmlColumns[3].getText().strip()

					# Link
					# TODO: If the hash cannot be retrieved from the mouse-over image, fallback to the .torrent file.
					try:
						htmlLink = htmlInfo.find_all('a')[0]['onmouseover']
						start = htmlLink.find('/over/')
						if start < 0:
							raise Exception()
						start += 6
						end = htmlLink.find('.', start)
						htmlLink = htmlLink[start : end]
						if not len(htmlLink) == 40:
							raise Exception()
						htmlLink = self.magnet_link % (htmlLink, htmlName.replace(' ', ''))
					except:
						try:
							htmlLink = htmlInfo.find_all('a')[0]['href']
							start = htmlLink.find('torrent/')
							if start < 0:
								raise Exception()
							start += 8
							htmlLink = htmlLink[start:]
							if len(htmlLink) == 0:
								raise Exception()
							htmlLink = self.torrent_link % (htmlLink, htmlName.replace(' ', ''))
						except:
							continue

					# Seeds
					htmlSeeds = int(htmlColumns[4].getText().strip())

					# Metadata
					meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

					# Ignore
					if meta.ignore(True):
						continue

					# Add
					sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
					added = True

				if not added: # Last page reached with a working torrent
					break

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
