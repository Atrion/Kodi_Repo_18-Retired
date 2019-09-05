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
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['ru']
		self.domains = ['avantabg.com']
		self.base_link = 'https://avantabg.com'
		self.search_link = '/torrents.php?active=1&order=seeds&by=DESC&search=%s&page=%d'

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
						# Only this format works for season packs.
						# Does not support individual episodes.
						if pack:
							query = '%s S%02d' % (title, season)
						else:
							pack = True
							query = '%s сезон %d' % (title, season)
				else:
					query = '%s %d' % (title, year)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)

			if not self._query(query): return sources

			url = urlparse.urljoin(self.base_link, self.search_link)

			pageLimit = tools.Settings.getInteger('scraping.providers.pages')
			pageCounter = 0

			page = 0 # Pages start at 0
			added = False

			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 8
			timer = tools.Time(start = True)

			while True:
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

				pageCounter += 1
				if pageLimit > 0 and pageCounter > pageLimit:
					break

				urlNew = url % (urllib.quote_plus(query), page)
				html = client.request(urlNew)

				# There is a quote missing.
				# Replace and add custom class for easy identification.
				html = html.replace('style="width:1095px; class=" lista">', 'style="width:1095px;" class="gaia lista">')

				htmlLower = html.lower()
				start = htmlLower.index('class="gaia')
				start = htmlLower.index('</tr>', start) + 5
				end = htmlLower.index('</table>', start) + 8
				html = html[start : end]
				html = html.replace('\n', '').replace('\r', '')
				html = html.replace('</TR>', '</tr>')
				htmlRows = html.split('</tr>')

				page += 1
				added = False

				for htmlRow in htmlRows:

					# Link
					try: htmlLink = re.search('(magnet:.*?)>', htmlRow, re.IGNORECASE).group(1)
					except: continue

					# Name
					try: htmlName = ' ' + re.search('details\.php.*?>(.*?)<', htmlRow, re.IGNORECASE).group(1).strip()
					except: htmlName = ''

					# Category
					try: htmlName += ' ' + re.search('border=0\s+alt="(.*?)"', htmlRow, re.IGNORECASE).group(1).strip()
					except: pass

					# Size
					try: htmlSize = re.search('>(\d+\.+\d+ [g|m]b)<', htmlRow, re.IGNORECASE).group(1).strip()
					except: htmlSize = None

					# Seeds
					try: htmlSeeds = int(re.search('>(\d+)<', htmlRow, re.IGNORECASE).group(1).strip())
					except: htmlSeeds = None

					htmlName = re.sub('[^A-Za-z0-9\s]', ' ', htmlName)
					htmlName = re.sub('\s\s+', ' ', htmlName).strip()

					# Otherwise if 3D appears multiple time in name, it will be ignored
					# Eg: 3D Avatar 3D 2009 1080p BluR 3D
					try:
						htmlIndex = htmlName.lower().index('3d')
						htmlName = htmlName.replace('3D', '').replace('3D', '')
						if htmlIndex >= 0: htmlName += '3D'
					except: pass

					# Metadata
					meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

					# Ignore
					meta.ignoreAdjust(contains = ignoreContains)
					if meta.ignore(True): continue

					# Add
					sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : htmlName, 'pack' : pack})
					added = True

				if not added: # Last page reached with a working torrent
					break

			return sources
		except:
			return sources
