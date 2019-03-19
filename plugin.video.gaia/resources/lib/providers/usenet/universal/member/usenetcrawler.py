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

import re,urllib,urlparse,datetime,math
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:
	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['usenet-crawler.com']
		self.base_link = 'https://www.usenet-crawler.com'

		# Votes 2 = Non-negative votes. Index 0 = Release names, otherwise find other totally unrelated files. Offset = page
		#self.search_link = '/search?val=%s&index=0&votes=2&t=%d&offset=%d'
		self.search_link = '/search?val=%s&index=0&t=%d&offset=%d' # Currently disable votes parameter, does not work in the moment.

		self.type_movies = 2000
		self.type_tvshows = 5000
		self.offset = 50
		self.enabled = tools.Settings.getBoolean('accounts.providers.usenetcrawler.enabled')
		self.username = tools.Settings.getString('accounts.providers.usenetcrawler.user')
		self.password = tools.Settings.getString('accounts.providers.usenetcrawler.pass')

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
		found = []
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
			if self.enabled and self.username and not self.username == '' and self.password and not self.password == '':
				login = urlparse.urljoin(self.base_link, '/login')
				post = urllib.urlencode({'username': self.username, 'password': self.password, 'rememberme' : 'on', 'submit': 'Login'}) # Must have rememberme, otherwise cannot login (UsenetCrawler bug).
				cookie = client.request(login, post = post, output = 'cookie', close = False)
				response = client.request(login, post = post, cookie = cookie, output = 'extended')
				headers = {'User-Agent': response[3]['User-Agent'], 'Cookie': response[3]['Cookie']}
			else:
				cookie = None
				headers = None

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
					htmlInfo = htmlColumns[0]

					# Name
					htmlName = htmlInfo.find_all('a', class_ = 'title')[0].getText()

					# Size
					htmlSize = htmlColumns[3].getText()
					indexEnd = htmlSize.find('<br')
					if indexEnd >= 0:
						htmlSize = htmlSize[: indexEnd]

					# Link
					htmlLink = self.base_link + htmlColumns[6].find_all('a')[0]['href']
					index = htmlLink.rfind('/')
					if index > 0:
						htmlLink = htmlLink[:index] # Remove name at end that contains spaces
					if not headers == None:
						htmlLink += '|' + urllib.urlencode(headers)

					# Age
					htmlAge = htmlColumns[2]['title']
					htmlAge = tools.Time.datetime(htmlAge, '%Y-%m-%d %H:%M:%S')
					htmlAge = datetime.datetime.today() - htmlAge
					htmlAge = htmlAge.days

					# Language
					htmlLanguage = htmlColumns[1].find_all('a')[0].getText()
					if 'Foreign >' in htmlLanguage:
						htmlLanguage = tools.Language.code(htmlLanguage[htmlLanguage.rfind('>') + 1:].strip())
					else:
						htmlLanguage = self.language[0]

					# Metadata
					meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, age = htmlAge)

					# Ignore
					if meta.ignore(False):
						continue

					# Ignore Duplicates
					htmlCategory = htmlColumns[1].find_all('a')[0].getText()
					htmlFiles = htmlColumns[4].find_all('a')[0].getText()
					size = meta.size()
					if isinstance(size, (float, int, long)):
						size = int(math.ceil(size / 1048576.0) * 1048576.0) # Sometimes the file size slightly varies. Round to the upper MB.
					htmlAge = int(math.ceil(htmlAge))
					foundId = htmlName.lower() + '_' + str(htmlAge) + '_' + htmlCategory + '_' + htmlFiles + '_' + str(size)
					if foundId in found:
						continue
					found.append(foundId)

					# Add
					sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'usenet', 'memberonly' : True, 'language' : htmlLanguage, 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
