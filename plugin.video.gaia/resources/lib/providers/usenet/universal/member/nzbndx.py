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

import re,urllib,urlparse,datetime
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:
	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['nzbndx.com']
		self.base_link = 'https://www.nzbndx.com'
		self.search_link = '/search/%s&t=%d&offset=%d'
		self.type_movies = 2000
		self.type_tvshows = 5000
		self.offset = 50
		self.exclude_foreign = False # Excludes movies in foreign categories.
		self.enabled = tools.Settings.getBoolean('accounts.providers.nzbndx.enabled')
		self.username = tools.Settings.getString('accounts.providers.nzbndx.user')
		self.password = tools.Settings.getString('accounts.providers.nzbndx.pass')

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

			if not (self.enabled and self.username and not self.username == '' and self.password and not self.password == ''):
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

			# Login
			login = urlparse.urljoin(self.base_link, '/login')
			post = urllib.urlencode({'username': self.username, 'password': self.password, 'submit': 'Login'})
			cookie = client.request(login, post = post, output = 'cookie', close = False)
			response = client.request(login, post = post, cookie = cookie, output = 'extended')
			headers = {'User-Agent': response[3]['User-Agent'], 'Cookie': response[3]['Cookie']}

			url = urlparse.urljoin(self.base_link, self.search_link)

			pageLimit = tools.Settings.getInteger('scraping.providers.pages')
			pageCounter = 0

			type = self.type_tvshows if 'tvshowtitle' in data else self.type_movies
			offset = 0

			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 8
			timer = tools.Time(start = True)

			while True:
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

				pageCounter += 1
				if pageLimit > 0 and pageCounter > pageLimit:
					break

				urlNew = url % (urllib.quote_plus(query), type, offset)
				html = BeautifulSoup(client.request(urlNew, cookie = cookie))

				offset += self.offset

				htmlTable = html.find_all('table', id = 'browsetable')[0] # Will fail if on last page and the table is not present.
				htmlRows = htmlTable.find_all('tr', recursive = False) # Use children and no further.

				for i in range(1, len(htmlRows)): # First row is the header.
					htmlRow = htmlRows[i]
					htmlColumns = htmlRow.find_all('td', recursive = False) # Use children and no further.
					htmlInfo = htmlColumns[1]

					# Name
					htmlName = htmlInfo.find_all('a', class_ = 'title')[0].getText().strip()

					# Size
					htmlSize = htmlColumns[4].getText()
					indexEnd = htmlSize.find('<br')
					if indexEnd >= 0:
						htmlSize = htmlSize[: indexEnd].replace('"', '')

					# Link
					htmlLink = self.base_link + htmlColumns[7].find_all('div', class_ = 'icon_nzb')[0].find_all('a')[0]['href']
					urlparse.urljoin(self.base_link, htmlLink)
					htmlLink += '|' + urllib.urlencode(headers)

					# Age
					htmlAge = htmlColumns[3]['title']
					htmlAge = tools.Time.datetime(htmlAge, '%Y-%m-%d %H:%M:%S')
					htmlAge = datetime.datetime.today() - htmlAge
					htmlAge = htmlAge.days

					# Metadata
					meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, age = htmlAge)

					# Ignore
					if meta.ignore(False):
						continue

					# Ignore Incomplete
					try:
						htmlComplete = htmlColumns[4].find_all('span', class_ = 'label-success')[0].getText()
						if not '100' in htmlComplete:
							continue
					except:
						pass

					# Ignore Foreign
					if self.exclude_foreign:
						htmlCategory = htmlColumns[2].find_all('a')[0].getText()
						if 'foreign' in htmlCategory.lower():
							continue

					# Add
					# Some NZBs have the wrong size (often a few KB) indicated on the site, but are in reaility bigger. Hence, do not show the size of NZBs below 20MB, but still add them.
					sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'usenet', 'memberonly' : True, 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
