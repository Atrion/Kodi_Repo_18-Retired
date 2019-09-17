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

import json,os

from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.extensions import metadata
from resources.lib.extensions import provider

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.priority = 0
		self.language = ['un']
		self.domains = []

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None: return sources

			data = self._decode(url)

			type = 'episode' if 'tvshowtitle' in data else 'movie'
			years = (data['year'], str(int(data['year'])+1), str(int(data['year'])-1))

			def add(result, title, titles):
				link = result['file'].encode('utf-8')
				name = os.path.basename(link)

				try: videoQuality = int(result['streamdetails']['video'][0]['width'])
				except: videoQuality = -1

				threshold = 20 # Some videos are a bit smaller.
				if videoQuality >= 8192 - threshold: videoQuality = 'HD8K'
				elif videoQuality >= 6144 - threshold: videoQuality = 'HD6K'
				elif videoQuality >= 3840 - threshold: videoQuality = 'HD4K'
				elif videoQuality >= 2048 - threshold: videoQuality = 'HD2K'
				elif videoQuality >= 1920 - threshold: videoQuality = 'HD1080'
				elif videoQuality >= 1280 - threshold: videoQuality = 'HD720'
				else: videoQuality = 'SD'

				try: videoCodec = result['streamdetails']['video'][0]['codec']
				except: videoCodec = None

				try: video3D = len(result['streamdetails']['video'][0]['stereomode']) > 0
				except: video3D = None

				try: audioChannels = result['streamdetails']['audio'][0]['channels']
				except: audioChannels = None

				try: audioCodec = result['streamdetails']['audio'][0]['codec']
				except: audioCodec = None

				try: subtitle = len(result['streamdetails']['subtitle']) > 0
				except: subtitle = None

				try:
					file = control.openFile(link)
					size = file.size()
					file.close()
				except:
					size = None

				try:
					meta = metadata.Metadata(name = name, title = title, titles = titles, link = link, size = size)
					meta.setVideoQuality(videoQuality)
					meta.setVideoCodec(videoCodec)
					meta.setVideo3D(video3D)
					meta.setAudioChannels(audioChannels)
					meta.setAudioCodec(audioCodec)
					meta.setSubtitlesSoft(subtitle)
				except:
					pass

				sources.append({'source': '0', 'quality': meta.videoQuality(), 'language' : self.language[0], 'url': link, 'file' : name, 'local': True, 'direct': True, 'debridonly': False, 'metadata' : meta})

			titles = data['alternatives'] if 'alternatives' in data else None
			if type == 'movie':
				title = cleantitle.get(data['title'])
				ids = [data['imdb']]

				if not self._query(title, ids): return sources

				results = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties": ["imdbnumber", "title", "originaltitle", "file"]}, "id": 1}' % years)
				results = unicode(results, 'utf-8', errors='ignore')
				results = json.loads(results)['result']['movies']

				results = [i for i in results if str(i['imdbnumber']) in ids or title in [cleantitle.get(i['title'].encode('utf-8')), cleantitle.get(i['originaltitle'].encode('utf-8'))]]
				results = [i for i in results if not i['file'].encode('utf-8').endswith('.strm')]

				for result in results:
					result = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovieDetails", "params": {"properties": ["streamdetails", "file"], "movieid": %s }, "id": 1}' % str(result['movieid']))
					result = unicode(result, 'utf-8', errors='ignore')
					result = json.loads(result)['result']['moviedetails']
					add(result, title, titles)

			elif type == 'episode':
				title = cleantitle.get(data['tvshowtitle'])
				season, episode = data['season'], data['episode']
				ids = [data['imdb'], data['tvdb']]

				if not self._query(title, ids, season, episode): return sources

				results = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties": ["imdbnumber", "title"]}, "id": 1}' % years)
				results = unicode(results, 'utf-8', errors='ignore')
				results = json.loads(results)['result']['tvshows']

				results = [i for i in results if str(i['imdbnumber']) in ids or title == cleantitle.get(i['title'].encode('utf-8'))][0]

				results = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "season", "operator": "is", "value": "%s"}, {"field": "episode", "operator": "is", "value": "%s"}]}, "properties": ["file"], "tvshowid": %s }, "id": 1}' % (str(season), str(episode), str(results['tvshowid'])))
				results = unicode(results, 'utf-8', errors='ignore')
				results = json.loads(results)['result']['episodes']

				results = [i for i in results if not i['file'].encode('utf-8').endswith('.strm')]
				for result in results:
					result = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodeDetails", "params": {"properties": ["streamdetails", "file"], "episodeid": %s }, "id": 1}' % str(result['episodeid']))
					result = unicode(result, 'utf-8', errors='ignore')
					result = json.loads(result)['result']['episodedetails']
					add(result, title, titles)

			return sources
		except:
			return sources
