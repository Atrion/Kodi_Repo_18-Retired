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

import re,urllib,urlparse
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:

	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['prostylex.com']
		self.base_link = 'http://prostylex.com'
		self.search_link = '/torrents-search.php?sort=seeders&order=desc&search=%s&page=%d'
		self.category_movies = '&c1=1&c2=1&c3=1&c4=1&c5=1&c6=1&c7=1&c8=1&c9=1&c65=1'
		self.category_tvshows = '&c12=1&c13=1&c14=1&c15=1&c65=1'

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

			url = urlparse.urljoin(self.base_link, self.search_link)
			category = self.category_tvshows if ('tvshowtitle' in data and not data['tvshowtitle'] == None and not data['tvshowtitle'] == '') else self.category_movies
			url += category

			pageLimit = tools.Settings.getInteger('scraping.providers.pages')
			pageCounter = 0

			page = 0 # Pages start at 0
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

				urlNew = url % (urllib.quote_plus(query), page)
				html = client.request(urlNew)

				htmlLower = html.lower()
				start = htmlLower.index('<img')
				end = htmlLower.index('>', start) + 1
				html = html[:start] + html[end:]
				html = html.replace('</b></a><td', '</b></a></td><td')

				html = html.replace('<shn>', '').replace('</shn>', '')
				html = html.replace('<shnn>', '').replace('</shnn>', '')
				html = html.replace('<shn2>', '').replace('</shn2>', '')

				html = BeautifulSoup(html)

				page += 1
				added = False

				htmlRows = html.find_all('tr', class_ = 't-row') # Missing closing tags. Look for rows directly instead.
				for i in range(len(htmlRows)):
					try:
						htmlRow = htmlRows[i]
						htmlColumns = htmlRow.find_all('th')
						tools.Logger.log("FFFGGGx: "+str(len(htmlColumns)))

						# Name
						htmlName = htmlRow.find_all('td', recursive = False)[0].getText().strip()

						# Size
						htmlSize = htmlColumns[2].getText().strip()

						# Link
						htmlLink = htmlRow.find_all('td', recursive = False)[0].find_all('a')[1]['href'].strip()
						htmlLink = urlparse.urljoin(self.base_link, htmlLink)

						# Seeds
						htmlSeeds = int(re.sub('[^0-9]', '', htmlColumns[4].getText().replace(',', '').replace('.', '').strip()))

						# Metadata
						meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

						# Ignore
						if meta.ignore(True):
							continue

						# Add
						sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
						added = True
					except:
						pass

				if not added: # Last page reached with a working torrent
					break

			return sources
		except:
			return sources

	def resolve(self, url):
		html = BeautifulSoup(client.request(url))
		htmlLinks = html.find_all('a')
		for htmlLink in htmlLinks:
			link = htmlLink['href']
			if link.startswith('magnet:'):
				return link
		return None
