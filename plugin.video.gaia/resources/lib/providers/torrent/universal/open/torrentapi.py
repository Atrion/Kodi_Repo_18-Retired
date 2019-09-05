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

import re,urllib,urlparse,json,threading
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import network

# https://torrentapi.org/apidocs_v2.txt

class source(provider.ProviderBase):

	Token = None
	Lock = None

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['torrentapi.org']
		self.base_link = 'https://torrentapi.org'
		self.api_link = '/pubapi_v2.php?app_id=%s' % tools.System.name()
		self.token_link = '&get_token=get_token'
		self.search_link = '&token=%s&mode=search&search_string=%s&category=%s&sort=seeders&ranked=0&format=json_extended&limit=100'
		self.category_movies = 'movies'
		self.category_shows = 'tv'
		self.rate_limit = 2 # 2 secs - https://torrentapi.org/apidocs_v2.txt?app_id=gaia

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None: raise Exception()

			ignoreContains = None
			data = self._decode(url)

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = None
				year = None
				season = None
				episode = None
				pack = False
				packCount = None
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = data['alternatives'] if 'alternatives' in data else None
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False
				packCount = data['packcount'] if 'packcount' in data else None

				if 'tvshowtitle' in data:
					# Search special episodes by name. All special episodes are added to season 0 by Trakt and TVDb. Hence, do not search by filename (eg: S02E00), since the season is not known.
					if (season == 0 or episode == 0) and ('title' in data and not data['title'] == None and not data['title'] == ''):
						title = '%s %s' % (data['tvshowtitle'], data['title']) # Change the title for metadata filtering.
						query = title
						ignoreContains = len(data['title']) / float(len(title)) # Increase the required ignore ration, since otherwise individual episodes and season packs are found as well.
					else:
						if pack: query = '%s S%02d' % (title, season) # Must add S before season, otherwise TorrentAPI throws an error (maybe because the search term is too general).
						else: query = '%s S%02dE%02d' % (title, season, episode)
				else:
					query = '%s %d' % (title, year)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			if not self._query(query): return sources

			# Ensure that only a single token is retrieved when searching for alternative titles.
			# Otherwise a HTTP 429 error is thrown (too many requests).
			first = False
			if source.Lock is None:
				source.Lock = threading.Lock()
				first = True
			source.Lock.acquire()

			if first:
				# Get a token. Expires every 15 minutes, but just request the token on every search. The old token will be returned if the previous one did not yet expire.
				url = self.base_link + self.api_link + self.token_link
				result = json.loads(client.request(url))
				source.Token = result['token']
			else:
				tools.Time.sleep(self.rate_limit * 1.1) # There is a 1req/2s limit.

			category = self.category_shows if 'tvshowtitle' in data else self.category_movies
			url = (self.base_link + self.api_link + self.search_link) % (source.Token, urllib.quote_plus(query), category)

			try:
				result = json.loads(client.request(url))
				torrents = result['torrent_results']

				for torrent in torrents:
					jsonName = torrent['title']
					jsonSize = torrent['size']
					jsonLink = torrent['download']
					try: jsonSeeds = int(torrent['seeders'])
					except: jsonSeeds = None

					# Metadata
					meta = metadata.Metadata(name = jsonName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = jsonLink, size = jsonSize, seeds = jsonSeeds)

					# Ignore
					meta.ignoreAdjust(contains = ignoreContains)
					if meta.ignore(False): continue

					# Add
					sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
			except: pass

			source.Lock.release()
		except:
			tools.Logger.error()

		return sources
