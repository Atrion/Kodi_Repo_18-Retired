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

import re,urllib,urlparse,json
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools

class source:

	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['bitlordsearch.com']
		self.base_link = 'http://www.bitlordsearch.com'
		self.search_link = '/get_list'
		self.category_movies = 3
		self.category_tvshows = 4

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

			torrents = json.loads(client.request(url, post = {
				'query' : urllib.quote_plus(query),
				'filters[category]' : str(category),
				'filters[adult]' : 'false',
				'filters[field]' : 'seeds',
				'filters[sort]' : 'desc',
				'filters[time]' : '4',
				'limit' : '1000',
				'offset' : '0',
			}))['content']

			for torrent in torrents:
				jsonName = torrent['name']
				jsonLink = torrent['magnet']
				try:
					jsonSize = int(torrent['size'])
					if jsonSize < 75: jsonSize = jsonSize * 1073741824
					else: jsonSize = jsonSize * 1048576
				except: jsonSize = None
				try: jsonSeeds = int(torrent['seeds'])
				except: jsonSeeds = None

				# Metadata
				meta = metadata.Metadata(name = jsonName, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = jsonLink, size = jsonSize, seeds = jsonSeeds)

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
