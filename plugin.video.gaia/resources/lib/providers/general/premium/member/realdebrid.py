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

import re,urllib,urlparse,time
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import debrid

class source:
	def __init__(self):
		self.pack = True # Checked by provider.py
		self.priority = 0
		self.language = ['un']
		self.domains = ['real-debrid.com']
		self.base_link = 'https://real-debrid.com'

	def instanceEnabled(self):
		realdebrid = debrid.RealDebrid()
		return realdebrid.accountEnabled() and realdebrid.accountValid()

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

			realdebrid = debrid.RealDebrid()

			if not realdebrid.accountValid():
				raise Exception()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			if 'exact' in data and data['exact']:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = None
				season = None
				episode = None
				pack = False
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				pack = data['pack'] if 'pack' in data else False

			items = realdebrid.items()
			for item in items:
				try:
					if item['transfer']['progress']['completed']['value'] == 1: # Only finished downloads.
						jsonName = item['name']
						jsonLink = item['link']
						jsonSize = item['size']['bytes']

						# Metadata
						meta = metadata.Metadata(name = jsonName, title = title, year = year, season = season, episode = episode, pack = pack, size = jsonSize)
						if meta.ignore(False):
							continue

						# Add
						sources.append({'url' : jsonLink, 'premium' : True, 'debridonly' : True, 'direct' : True, 'memberonly' : True, 'source' : 'RealDebrid', 'language' : self.language[0], 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
				except:
					pass
			return sources
		except:
			return sources

	def resolve(self, url):
		# NB: resolving is done by handler.py -> HandleDirect
		return url
