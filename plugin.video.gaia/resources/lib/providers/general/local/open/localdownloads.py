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

import os,re

from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import provider

class source(provider.ProviderBase):

	def __init__(self):
		provider.ProviderBase.__init__(self, supportMovies = True, supportShows = True)

		self.priority = 0
		self.language = ['un']
		self.domains = []
		self.prefix = 'downloads.manual.'

	def _locationMovies(self):
		path = None
		if tools.Settings.getInteger(self.prefix + 'path.selection') == 0:
			path = os.path.join(tools.Settings.path(self.prefix + 'path.combined'), interface.Translation.string(32001))
		else:
			path = tools.Settings.path(self.prefix + 'path.movies')
		return path

	def _locationTvshows(self):
		path = None
		if tools.Settings.getInteger(self.prefix + 'path.selection') == 0:
			path = os.path.join(tools.Settings.path(self.prefix + 'path.combined'), interface.Translation.string(32002))
		else:
			path = tools.Settings.path(self.prefix + 'path.tvshows')
		return path

	def _find(self, path, title):
		title = re.sub('[^a-zA-Z0-9]', ' ', title).lower()
		titleSplit = title.split(' ')

		result = []
		directories, files = tools.File.listDirectory(path)

		for file in files:
			fileSplit = re.sub('[^a-zA-Z0-9]', ' ', file).lower().split(' ')
			contains = True
			for t in titleSplit:
				if not t in fileSplit:
					contains = False
					break
			if contains:
				result.append(os.path.join(path, file))

		for directory in directories:
			result.extend(self._find(os.path.join(path, directory), title))

		return result

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None: return sources
			if not tools.Settings.getBoolean(self.prefix + 'enabled'): return sources

			data = self._decode(url)

			type = 'episode' if 'tvshowtitle' in data else 'movie'
			if type == 'movie':
				path = self._locationMovies()
			elif type == 'episode':
				path = self._locationTvshows()

			if not path.endswith('\\') and not path.endswith('/'): # Must end with a slash for tools.File.exists.
				path += '/'

			if not tools.File.exists(path):
				return sources

			if 'exact' in data and data['exact']:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				titles = None
			else:
				if type == 'episode':
					# Search special episodes by name. All special episodes are added to season 0 by Trakt and TVDb. Hence, do not search by filename (eg: S02E00), since the season is not known.
					if (season == 0 or episode == 0) and ('title' in data and not data['title'] == None and not data['title'] == ''):
						title = '%s %s' % (data['tvshowtitle'], data['title']) # Change the title for metadata filtering.
					else:
						title = '%s S%02dE%02d' % (data['tvshowtitle'], int(data['season']), int(data['episode']))
				else:
					title = '%s %s' % (data['title'], str(data['year']))
				title = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', title)
				titles = data['alternatives'] if 'alternatives' in data else None

			if not self._query(title): return sources

			files = self._find(path, title)
			if titles:
				for t in titles:
					files.extend(self._find(path, t))

			for file in files:
				file = file.replace('\\\\', '/').replace('\\', '/') # For some reason Python sometimes adds backslash instead of forward slash with os.path. This causes duplicate files not to be filtered out due to a "different" path.
				meta = metadata.Metadata()
				meta.loadHeadersFile(file, timeout = 30)
				sources.append({'source': '0', 'quality': meta.videoQuality(), 'language' : self.language[0], 'url': file, 'file' : os.path.basename(file), 'local': True, 'direct': True, 'debridonly': False, 'metadata' : meta})
		except:
			pass

		return sources
