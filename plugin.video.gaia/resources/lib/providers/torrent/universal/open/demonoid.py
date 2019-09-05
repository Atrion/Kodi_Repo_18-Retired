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
		self.domains = ['demonoid.to', 'demonoid.pw', 'dnoidd1.unblocked.lol', 'dnoid.me', 'demonoid.unblocked.bet']
		self.base_link = 'https://www.demonoid.to'
		self.search_link = '/files/?category=%d&subcategory=All&language=0&quality=All&seeded=2&external=2&query=%s&to=1&tk=0&uid=0&sort=S&page=%d'
		self.download_link = 'https://www.hypercache.pw/metadata/%s/?inuid=0'
		self.category_movies = 1
		self.category_shows = 3

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
			query = urllib.quote_plus(query)

			category = self.category_shows if 'tvshowtitle' in data else self.category_movies
			url = urlparse.urljoin(self.base_link, self.search_link)

			pageLimit = tools.Settings.getInteger('scraping.providers.pages')
			pageCounter = 0

			page = 1
			added = False

			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 8
			timer = tools.Time(start = True)

			'''
			while True:
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

				pageCounter += 1
				if pageLimit > 0 and pageCounter > pageLimit:
					break

				urlNew = url % (category, query, page)
				html = client.request(urlNew)

				# Demonoid does not have a closing tag for the rows.
				# This causes BeautifulSoup to only detect the first row.
				# Manually add a closing </tr> tag, except fore the first row.
				html = html.replace('<tr align="left" bgcolor="#CCCCCC">', '<tr align="left" bgcolor="">', 1)
				html = html.replace('<tr align="left" bgcolor="#CCCCCC">', '</tr><tr align="left" bgcolor="#CCCCCC">')

				html = BeautifulSoup(html)

				page += 1
				added = False

				htmlTable = html.find_all('td', class_ = 'ctable_content_no_pad')[0].find_all('table', recursive = False)[1]
				htmlRows = html.find_all('tr')

				i = 0
				while i < len(htmlRows):
					try:
						htmlRow = htmlRows[i]
						i += 1 # Normal loop increment.

						if len(htmlRow.find_all('td', {'rowspan' : '2'})) == 0:
							continue

						# Name
						htmlName = htmlRow.find_all('td', {'colspan' : '9'})[0].find_all('a')[0].getText().strip()

						htmlRow = htmlRows[i]
						i += 1 # Go to next row, because items are split over to lines.

						# Size
						htmlSize = htmlColumns[3].getText().strip()

						# Link
						htmlLink = htmlColumns[2].find_all('a')[0]['href']

						# Seeds
						htmlSeeds = int(htmlColumns[6].getText().strip())

						items = htmlColumns[0].find_all('a')

						# Release
						try:
							htmlRelease = items[1].getText()
							if not 'other' in htmlRelease.lower(): htmlName += ' ' + htmlRelease
						except:
							pass

						# Language
						try:
							htmlLanguage = items[2].getText()
						except:
							htmlLanguage = None

						# Metadata
						meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds, languageAudio = htmlLanguage)

						# Ignore
						meta.ignoreAdjust(contains = ignoreContains)
						if meta.ignore(True): continue

						# Add
						sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
						added = True
					except:
						pass
			'''

			while True:
				# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
				if timer.elapsed() > timerEnd:
					break

				pageCounter += 1
				if pageLimit > 0 and pageCounter > pageLimit:
					break

				urlNew = url % (category, query, page)
				html = client.request(urlNew)

				page += 1
				added = False

				htmlRows = re.findall('<!--\s*tstart\s*-->(.*?)<tr\s*align="left"\s*bgcolor="#CCCCCC">', html, re.M | re.S)
				htmlRows = ['<tr><td>' + i for i in htmlRows]
				for htmlRow in htmlRows:
					try:
						htmlRow = BeautifulSoup(htmlRow)
						htmlColumns = htmlRow.find_all('td')

						# Name
						htmlName = htmlRow.find_all('a')[1].getText().strip()

						# Size
						htmlSize = htmlColumns[4].getText().strip()

						# Link
						htmlLink = htmlRow.find_all('a')[1]['href']
						htmlLink = urlparse.urljoin(self.base_link, htmlLink)
						htmlLink = re.search('genidy=(.*)', htmlLink, re.IGNORECASE)
						if not htmlLink: continue
						htmlLink = self.download_link % htmlLink.group(1)

						# Seeds
						try: htmlSeeds = int(htmlColumns[7].getText().strip())
						except: htmlSeeds = 0

						items = htmlColumns[0].find_all('a')

						# Metadata
						meta = metadata.Metadata(name = htmlName, title = title, titles = titles, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = htmlLink, size = htmlSize, seeds = htmlSeeds)

						# Ignore
						meta.ignoreAdjust(contains = ignoreContains)
						if meta.ignore(True): continue

						# Add
						sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'torrent', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
						added = True
					except:
						pass

				if not added: # Last page reached with a working torrent
					break

			return sources
		except:
			return sources
