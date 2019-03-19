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

import re,urllib,urlparse,json,xbmc
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import network

class source:

	def __init__(self):
		self.pack = False # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['yts.am'] # Other YIFI domains do not have an API.
		self.base_link = 'https://yts.am'
		self.search_link = '/api/v2/list_movies.json?query_term=%s&limit=50&sort_by=seeds&order_by=desc&with_rt_ratings=false'

	def movie(self, imdb, title, localtitle, year):
		try:
			url = {'imdb': imdb, 'title': title, 'year': year}
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
				titleYear = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = None
				season = None
				episode = None
				pack = False
				packCount = None
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titleYear = '%s %s' % (title, str(data['year']))
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None

			query = data['imdb'] if 'imdb' in data and not data['imdb'] == None else title
			url = urlparse.urljoin(self.base_link, self.search_link) % query
			result = json.loads(client.request(url))

			movie = result['data']['movies'][0]
			name = movie['title_long'] + ' '
			torrents = movie['torrents']

			for torrent in torrents:
				quality = torrent['quality']
				if quality.lower() == '3d':
					quality += ' HD1080'
				jsonName = name + quality
				jsonSize = torrent['size_bytes']
				jsonHash = torrent['hash']
				jsonLink = network.Container(jsonHash).torrentMagnet(title = titleYear)
				try: jsonSeeds = int(torrent['seeds'])
				except: jsonSeeds = None

				# Metadata
				meta = metadata.Metadata(name = jsonName, title = title, year = year, season = season, episode = episode, link = jsonLink, size = jsonSize, seeds = jsonSeeds)
				meta.setUploader(['yify', 'yts'])
				jsonLink = network.Container(jsonHash).torrentMagnet(title = meta.title(extended = True))

				# Ignore
				if meta.ignore(False):
					continue

				# Add
				sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
