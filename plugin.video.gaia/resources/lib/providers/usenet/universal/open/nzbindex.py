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

import re,json
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import network

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['nzbindex.com']
		self.base_link = 'https://nzbindex.com'
		self.search_link = '/search/json?max=250&minage=0&maxage=0&hidespam=1&hidepassword=1&hidecross=1&hasNFO=0&complete=1&minsize=50&maxsize=0&sort=agedesc&poster=&q=%s&p=%d'
		self.download_link = '/download/%s'

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

			urlSearch = self.base_link + self.search_link
			urlDownload = self.base_link + self.download_link

			page = 0
			while True:
				result = json.loads(client.request(urlSearch % (query, page)))
				torrents = result['results']

				page += 1
				added = False

				for torrent in torrents:
					try:
						jsonName = torrent['name']
						jsonSize = torrent['size']
						jsonAge = int((tools.Time.timestamp() - (torrent['posted'] / 1000.0)) / 86400.0)
						jsonLink = urlDownload % str(torrent['id'])

						# Metadata
						meta = metadata.Metadata(name = jsonName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = jsonLink, size = jsonSize, age = jsonAge)

						# Ignore
						meta.ignoreAdjust(contains = ignoreContains, length = 0.3)
						if meta.ignore(False): continue

						# Add
						sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'source' : 'usenet', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
						added = True
					except:
						pass

				if not added: break

			return sources
		except:
			return sources
