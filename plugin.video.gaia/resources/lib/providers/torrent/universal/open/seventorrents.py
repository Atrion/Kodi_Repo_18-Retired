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
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = False)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['7tmirror.info']
		self.base_link = 'http://7tmirror.info'
		self.search_link = '/Movies/%s.aspx'
		self.download_link = '/Torrents/%s.seventorrents.com.torrent'

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None: raise Exception()

			data = self._decode(url)

			if 'exact' in data and data['exact']:
				query = title = data['title']
				titles = None
				year = None
			else:
				title = data['title']
				titles = data['alternatives'] if 'alternatives' in data else None
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				query = '%s %d' % (title, year)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			if not self._query(query): return sources

			url = urlparse.urljoin(self.base_link, self.search_link) % urllib.quote_plus(query)
			html = BeautifulSoup(client.request(url))

			htmlTable = html.find_all('div', id = 'Torrents')[0].find_all('div', class_ = 'DownloadFlags')[0]
			htmlRows = htmlTable.find_all('a', recursive = False) # Do not search further down the tree (just the direct children), because that will also retrieve the header row.
			for i in range(1, len(htmlRows)): # Skip first entry
				try:
					htmlRow = htmlRows[i]
					htmlData = htmlRow['onmouseover'].split(',')

					if not len(htmlData) == 11: continue

					# Name
					htmlName = htmlData[5].strip().strip("'")

					# Link
					htmlLink = htmlRow['href'].strip()
					htmlLink = re.search('\/.*\/(.*)\.aspx', htmlLink).group(1).replace('-', '.')
					htmlLink = urlparse.urljoin(self.base_link, self.download_link) % urllib.quote_plus(htmlLink)

					# Size
					htmlSize = htmlData[7].strip().strip("'")

					# Metadata
					meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, link = htmlLink, size = htmlSize, seeds = 1)

					# Ignore
					meta.mIgnoreLength = 10
					if meta.ignore(True): continue

					# Add
					sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
				except:
					pass

			return sources
		except:
			return sources
