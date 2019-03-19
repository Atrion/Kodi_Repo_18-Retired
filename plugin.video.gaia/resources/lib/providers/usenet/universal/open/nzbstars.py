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

import re,urllib,urlparse,datetime,math,locale
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:
	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['nzbstars.com']
		self.base_link = 'http://www.nzbstars.com'
		self.search_link = '/?search[value][]=Title:%s&sortby=&sortdir=ASC'

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

			# Force en_US date encoding.
			# Otherwise the month in the date might be read in a different language.
			locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

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

			url = urlparse.urljoin(self.base_link, self.search_link) % (urllib.quote_plus(query))
			html = BeautifulSoup(client.request(url))

			htmlTable = html.find_all('tbody', id = 'spots')[0]

			# Fix some problems with the markup.
			htmlTable = str(htmlTable)
			htmlTable = htmlTable.replace('\'=""', '=""') # Dangling single quote.
			htmlTable = htmlTable.replace('<b>', '').replace('</b>', '') # There are bold tabgs wrapped arround some td, casuing BeautifulSoup to skip them.
			htmlTable = BeautifulSoup(htmlTable)

			htmlRows = htmlTable.find_all('tr') # Do not switch recursive off here, for some reason BeautifulSoup then detects nothing. Probabley because of markup fixing.

			for i in range(len(htmlRows)):
				htmlRow = htmlRows[i]
				htmlColumns = htmlRow.find_all('td', recursive = False) # Use children and no further.
				htmlInfo = htmlColumns[1]

				# Category
				htmlCategory = htmlColumns[0].find_all('a')[0].getText()
				htmlCategory = htmlCategory.replace('HD', ' HD')

				# Name
				htmlName = htmlInfo.find_all('a')[0].getText()
				htmlName += ' ' + htmlCategory

				# Size
				htmlSize = htmlColumns[6].getText()

				# Link
				htmlLink = htmlColumns[7].find_all('a')[0]['href']

				# Age
				htmlAge = htmlColumns[5]['title']
				index = htmlAge.find(',')
				if index >= 0:
					htmlAge = htmlAge[index + 1:]
				htmlAge = htmlAge.strip()
				htmlAge = tools.Time.datetime(htmlAge, '%d-%b-%Y (%H:%M)')
				htmlAge = datetime.datetime.today() - htmlAge
				htmlAge = htmlAge.days

				# Metadata
				meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, age = htmlAge)

				# Ignore
				if meta.ignore(False):
					continue

				# Ignore Duplicates
				htmlPoster = htmlColumns[4].find_all('a')[0].getText()
				size = meta.size()
				if isinstance(size, (float, int, long)):
					size = int(math.ceil(size / 1048576.0) * 1048576.0) # Sometimes the file size slightly varies. Round to the upper MB.
				htmlAge = int(math.ceil(htmlAge))
				foundId = htmlName.lower() + '_' + str(htmlAge) + '_' + htmlCategory + '_' + htmlPoster + '_' + str(size)
				if foundId in found:
					continue
				found.append(foundId)

				# Add
				sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'usenet', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
