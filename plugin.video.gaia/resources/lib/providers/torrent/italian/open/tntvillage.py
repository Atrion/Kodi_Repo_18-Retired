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
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import network
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['it']
		self.domains = ['tntvillage.scambioetico.org']
		self.base_link = 'http://www.tntvillage.scambioetico.org'
		self.search_link = '/src/releaselist.php'
		self.post_link = 'cat=0&page=1&srcrel=%s'

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None:
				raise Exception()

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
						if pack: query = '%s %d' % (title, season)
						else: query = '%s S%02dE%02d' % (title, season, episode)
				else:
					query = '%s %d' % (title, year)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			if not self._query(query): return sources

			url = urlparse.urljoin(self.base_link, self.search_link)
			post = self.post_link % urllib.quote_plus(query)
			html = BeautifulSoup(client.request(url, post = post))

			htmlTable = html.find_all('table')[0]
			htmlRows = htmlTable.find_all('tr', recursive = False)
			for i in range(1, len(htmlRows)):
				try:
					htmlColumns = htmlRows[i].find_all('td', recursive = False)

					# Name
					htmlName = htmlColumns[6].getText().strip()

					# Link
					htmlLink = htmlColumns[1].find_all('a')[0]['href']

					# Seeds
					try: htmlSeeds = int(htmlColumns[4].getText().strip())
					except: htmlSeeds = None

					# Metadata
					meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, seeds = htmlSeeds)
					meta.mIgnoreLength = 8 # Relax this, otherwise too many links are filtered out (eg: Avatar 2009).

					# Ignore
					meta.ignoreAdjust(contains = ignoreContains)
					if meta.ignore(size = False): continue

					# Add
					sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : htmlName, 'pack' : pack})
				except:
					pass

			return sources
		except:
			return sources
