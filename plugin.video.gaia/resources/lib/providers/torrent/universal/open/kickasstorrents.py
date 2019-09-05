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
from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['kat.li', 'kat.how', 'kickasstorrents.video', 'kickasstorrents.to', 'katcr.to', 'kat.am',  'kickass.cd', 'kickass.ukbypass.pro', 'kickass.unlockproject.review'] # Most of these links seem to have a different page layout than kat.how.
		self.base_link = 'https://kat.li' # Link must have the name for provider verification.
		self.search_link = '/usearch/%s/?field=seeders&sorder=desc'

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
						if pack: query = '%s %d' % (title, season)
						else: query = '%s S%02dE%02d' % (title, season, episode)
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

			#while True:
			while page == 0: # KickassTorrents currently has a problem to view any other page than page 1 while sorted by seeders. Only view first page.
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

				pageCounter += 1
				if pageLimit > 0 and pageCounter > pageLimit:
					break

				urlNew = url % (urllib.quote_plus(query))
				html = client.request(urlNew)

				# KickassTorrents has major mistakes in their HTML. manually remove parts to create new HTML.
				indexStart = html.find('<', html.find('<!-- Start of Loop -->') + 1)
				indexEnd = html.rfind('<!-- End of Loop -->')
				html = html[indexStart : indexEnd]

				html = html.replace('<div class="markeredBlock', '</div><div class="markeredBlock') # torrentname div tag not closed.
				html = html.replace('</span></td>', '</td>') # Dangling </span> closing tag.

				html = BeautifulSoup(html)

				page += 1
				added = False

				htmlRows = html.find_all('tr', recursive = False) # Do not search further down the tree (just the direct children).
				for i in range(len(htmlRows)):
					htmlRow = htmlRows[i]
					if 'firstr' in htmlRow['class']: # Header.
						continue
					htmlColumns = htmlRow.find_all('td')
					htmlInfo = htmlColumns[0]

					# Name
					htmlName = htmlInfo.find_all('a', class_ = 'cellMainLink')[0].getText().strip()

					# Size
					htmlSize = htmlColumns[1].getText().replace('&nbsp;', ' ')

					# Link
					htmlLink = ''
					htmlLinks = htmlInfo.find_all('a', class_ = 'icon16')
					for j in range(len(htmlLinks)):
						link = htmlLinks[j]
						if link.has_attr('href'):
							link = link['href']
							if 'magnet' in link:
								htmlLink = urllib.unquote(re.findall('(magnet.*)', link)[0]) # Starts with redirection url, eg: https://mylink.bz/?url=magnet...
								break

					# Seeds
					htmlSeeds = int(htmlColumns[3].getText())

					# Metadata
					meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

					# Ignore
					meta.ignoreAdjust(contains = ignoreContains)
					if meta.ignore(True): continue

					# Add
					sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
					added = True

				if not added: # Last page reached with a working torrent
					break

			return sources
		except:
			return sources
