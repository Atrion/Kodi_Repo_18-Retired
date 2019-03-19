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
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.externals.beautifulsoup import BeautifulSoup

class source:
	def __init__(self):
		self.priority = 0
		self.language = ['un']
		self.domains = ['www.youtube.com']
		self.base_link = 'https://www.youtube.com'
		self.search_link = '/results?search_query=%s&sp=CAM%%253D'
		self.excludes = ['trailer', 'sample', 'preview', 'scene']

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
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				query = '%s S%02dE%02d' % (title, season, episode) if 'tvshowtitle' in data else '%s %d' % (title, year)
			query = urllib.quote_plus(query)

			# The returned website is different to the normal website.
			# Probably a mobile version.
			url = urlparse.urljoin(self.base_link, self.search_link) % query
			html = BeautifulSoup(client.request(url))
			htmlRows = html.find_all('div', class_ = 'yt-lockup-content')

			for htmlRow in htmlRows:
				htmlInfo = htmlRow.find_all('a')[0]

				# Name
				htmlName = htmlInfo.getText().strip()

				# Link
				htmlLink = urlparse.urljoin(self.base_link, htmlInfo['href'])

				# Duration
				htmlDuration = 0
				try:
					htmlDurationItem = htmlRow.find_all('span')[0].getText().lower()
					indexStart = htmlDurationItem.find(':')
					if indexStart > 0:
						indexStart += 1
						indexEnd = htmlDurationItem.find('.', indexStart)
						if indexEnd > 0:
							htmlDuration = htmlDurationItem[indexStart:indexEnd].strip()
							htmlDuration = htmlDuration.split(':')
							if len(htmlDuration) == 3:
								htmlDuration = (int(htmlDuration[0]) * 3600) + (int(htmlDuration[1]) * 60) + int(htmlDuration[2])
							else:
								htmlDuration = (int(htmlDuration[0]) * 60) + int(htmlDuration[1])
						else:
							htmlDuration = 0
				except:
					pass

				# Ignore trailers, etc.
				if any(s in htmlName.lower() for s in self.excludes):
					continue

				# Ignore less than 10 minutes.
				if htmlDuration < 600:
					continue

				# Metadata
				meta = metadata.Metadata(name = htmlName, title = title, year = year, season = season, episode = episode, link = htmlLink)

				# Ignore
				if meta.ignore(False):
					continue

				# Add
				sources.append({'url' : htmlLink, 'debridonly' : False, 'direct' : False, 'source' : 'youtube', 'language' : self.language[0], 'quality': meta.videoQuality(), 'metadata' : meta, 'file' : htmlName})
				added = True

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
