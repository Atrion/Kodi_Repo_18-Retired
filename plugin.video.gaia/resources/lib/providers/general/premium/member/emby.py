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

from resources.lib.extensions import provider
from resources.lib.extensions import metadata
from resources.lib.extensions import network
from resources.lib.extensions import tools
from resources.lib.extensions import emby

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.emby = emby.Emby()

		self.pack = False # Checked by provider.py
		self.priority = 0
		self.language = ['un']

		self.base_link = self.emby.link()
		self.domains = [network.Networker.linkDomain(self.base_link)]

	def instanceEnabled(self):
		return self.emby.enabled()

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None: raise Exception()
			if not self.emby.enabled(): raise Exception()

			data = self._decode(url)

			type = tools.Media.TypeShow if 'tvshowtitle' in data else tools.Media.TypeMovie
			imdb = data['imdb'] if 'imdb' in data else None
			if 'exact' in data and data['exact']:
				exact = True
				title = data['tvshowtitle'] if type == tools.Media.TypeShow else data['title']
				titles = None
				year = None
				season = None
				episode = None
			else:
				exact = False
				title = data['tvshowtitle'] if type == tools.Media.TypeShow else data['title']
				titles = data['alternatives'] if 'alternatives' in data else None
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None

			if not self._query(title, year, season, episode): return sources

			streams = self.emby.search(type = type, title = title, year = year, season = season, episode = episode, exact = exact)
			if not streams: return sources

			for stream in streams:
				try:
					try: name = stream['file']['name']
					except: name = None
					try: size = stream['file']['size']
					except: size = None

					meta = metadata.Metadata(name = name, title = title, titles = titles, year = year, season = season, episode = episode, size = size)
					meta.setType(metadata.Metadata.TypePremium)
					meta.setDirect(True)

					try: link = stream['stream']['link']
					except: continue

					try: meta.setLink(link)
					except: pass

					try: meta.setName(stream['file']['name'])
					except: pass
					try: meta.setSize(stream['file']['size'])
					except: pass

					try: meta.setVideoQuality(stream['video']['quality'])
					except: pass
					try: meta.setVideoCodec(stream['video']['codec'])
					except: pass
					try: meta.setVideo3D(stream['video']['3d'])
					except: pass

					try: meta.setAudioChannels(stream['audio']['channels'])
					except: pass
					try: meta.setAudioCodec(stream['audio']['codec'])
					except: pass
					try: meta.setAudioLanguages(stream['audio']['languages'])
					except: pass

					try:
						if len(stream['subtitle']['languages']) > 0: meta.setSubtitlesSoft()
					except: pass

					try: source = stream['stream']['source']
					except: source = None

					try: language = stream['audio']['languages'][0]
					except: language = None

					try: quality = stream['video']['quality']
					except: quality = None

					try: filename = stream['file']['name']
					except: filename = None

					sources.append({'url' : link, 'premium' : True, 'direct' : True, 'memberonly' : True, 'source' : source, 'language' : language, 'quality': quality, 'file' : filename, 'metadata' : meta, 'external' : True})
				except:
					tools.Logger.error()

			return sources
		except:
			tools.Logger.error()
			return sources
