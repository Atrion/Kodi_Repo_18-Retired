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
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:

	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['eztv.ag', 'eztv.unblocked.world', 'eztv.unblocked.today', 'eztv.immunicity.works', 'eztv.immunicity.today']
		self.base_link = 'https://eztv.ag'
		self.search_link = '/search/%s'

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

				if pack: query = '%s %d' % (title, season)
				else: query = '%s S%02dE%02d' % (title, season, episode)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			url = urlparse.urljoin(self.base_link, self.search_link) % urllib.quote_plus(query)
			html = BeautifulSoup(client.request(url))

			htmlTable = None
			tables = html.find_all('table', class_ = 'forum_header_border')
			for table in tables:
				try:
					row = table.find_all('tr')[1]
					headers = row.find_all('td', class_ = 'forum_thread_header')
					if headers[0].getText() == 'Show' and headers[5].getText() == 'Seeds':
						htmlTable = table
						break
				except:
					pass

			if htmlTable == None:
				raise Exception()

			htmlRows = htmlTable.find_all('tr', recursive = False) # Use children and no further.
			for i in range(2, len(htmlRows)): # First two rows are the headers.
				htmlRow = htmlRows[i]
				htmlColumns = htmlRow.find_all('td', recursive = False) # Use children and no further.
				htmlInfo = htmlColumns[1]

				# Name
				htmlName = htmlInfo.find_all('a', class_ = 'epinfo')[0]['title'].strip()

				# Size
				try: htmlSize = htmlColumns[3].getText() # Does not always have size.
				except: htmlSize = None

				# Link
				htmlLink = htmlColumns[2].find_all('a', class_ = 'magnet')[0]['href']

				# Seeds
				try: htmlSeeds = int(htmlColumns[5].find_all('font')[0].getText()) # Does not always have seeds.
				except: htmlSeeds = None

				# Metadata
				meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

				# Ignore
				if meta.ignore(False):
					continue

				# Add
				sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
