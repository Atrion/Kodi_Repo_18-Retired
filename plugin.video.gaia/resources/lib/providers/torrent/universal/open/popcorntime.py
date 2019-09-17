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
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import network

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = False # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['tv-v2.api-fetch.website']
		self.base_link = 'https://tv-v2.api-fetch.website'
		self.search_link = '/%s/%s'
		self.category_movies = 'movie'
		self.category_shows = 'show'

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None: raise Exception()

			data = self._decode(url)

			movie = False if 'tvshowtitle' in data else True
			imdb = data['imdb']
			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			titles = data['alternatives'] if 'alternatives' in data else None
			year = int(data['year']) if 'year' in data and not data['year'] == None else None
			season = int(data['season']) if 'season' in data and not data['season'] == None else None
			episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None

			if not self._query(imdb, season, episode): return sources

			category = self.category_movies if movie else self.category_shows
			url = urlparse.urljoin(self.base_link, self.search_link) % (category, imdb)
			result = json.loads(client.request(url))

			if movie:
				result = result['torrents']
				for language, value1 in result.iteritems():
					for quality, value2 in value1.iteritems():
						try: jsonSize = value2['filesize']
						except: jsonSize = None
						jsonLink = value2['url']

						# Movies use "seed" and episodes used "seeds".
						try: jsonSeeds = int(value2['seeds'])
						except:
							try: jsonSeeds = int(value2['seed'])
							except: jsonSeeds = None
						if jsonSeeds == 0: jsonSeeds = None # Otherwise they get removed.

						indexStart = jsonLink.find('&dn=')
						if indexStart > 0:
							indexStart += 4
							indexEnd = jsonLink.find('&', indexStart)
							if indexEnd > 0: jsonName = jsonLink[indexStart:indexEnd]
							else: jsonName = jsonLink[indexStart:]
							jsonName = urllib.unquote(jsonName)
						else:
							jsonName = title + ' ' + value2['provider']

						# Metadata
						meta = metadata.Metadata(name = jsonName, title = title, titles = titles, year = year, season = season, episode = episode, quality = quality, link = jsonLink, size = jsonSize, seeds = jsonSeeds)

						# Ignore
						if meta.ignore(False): continue

						# Add
						sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : language, 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
			else:
				result = result['episodes']
				for i in result:
					if int(i['season']) == season and int(i['episode']) == episode:
						result = i['torrents']
						for quality, value in result.iteritems():
							if quality == '' or quality == '0': quality = None

							try: jsonSize = value['filesize']
							except: jsonSize = None
							jsonLink = value['url']

							# Movies use "seed" and episodes used "seeds".
							try: jsonSeeds = int(value2['seeds'])
							except:
								try: jsonSeeds = int(value2['seed'])
								except: jsonSeeds = None
							if jsonSeeds == 0: jsonSeeds = None # Otherwise they get removed. Episodes currently always have 0 seeds/peers.

							indexStart = jsonLink.find('&dn=')
							if indexStart > 0:
								indexStart += 4
								indexEnd = jsonLink.find('&', indexStart)
								if indexEnd > 0: jsonName = jsonLink[indexStart:indexEnd]
								else: jsonName = jsonLink[indexStart:]
								jsonName = urllib.unquote(jsonName)
							else:
								jsonName = title + ' ' + value['provider']

							# Metadata
							meta = metadata.Metadata(name = jsonName, title = title, titles = titles, year = year, season = season, episode = episode, quality = quality, link = jsonLink, size = jsonSize, seeds = jsonSeeds)

							# Ignore
							if meta.ignore(False):
								continue

							# Add
							sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
						break

			return sources
		except:
			return sources
