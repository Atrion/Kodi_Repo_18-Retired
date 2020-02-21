# -*- coding: utf-8 -*-

"""
	Orion
    https://orionoid.com

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
"""

##############################################################################
# ORIONITEM
##############################################################################
# Class for handling items that contain movie/show info and a list of streams.
##############################################################################

import re
import threading
from orion.modules.oriontools import *
from orion.modules.orionstream import *
from orion.modules.orionapi import *
from orion.modules.orionapp import *
from orion.modules.orionsettings import *

class OrionItem:

	##############################################################################
	# CONSTANTS
	##############################################################################

	TypeMovie = 'movie'
	TypeShow = 'show'

	IdOrion = 'orion'
	IdImdb = 'imdb'
	IdTmdb = 'tmdb'
	IdTvdb = 'tvdb'
	IdTvrage = 'tvrage'
	IdTrakt = 'trakt'
	IdSlug = 'slug'
	IdDefault = IdOrion

	SelectDefault = None
	SelectMovie = 'movie'
	SelectShow = 'show'
	SelectSeason = 'season'
	SelectEpisode = 'episode'

	ProtocolMagnet = 'magnet'
	ProtocolHttp = 'http'
	ProtocolHttps = 'https'
	ProtocolFtp = 'ftp'
	ProtocolFtps = 'ftps'

	AccessDirect = 'direct'
	AccessIndirect = 'indirect'
	AccessPremiumize = 'premiumize'
	AccessPremiumizeTorrent = 'premiumizetorrent'
	AccessPremiumizeUsenet = 'premiumizeusenet'
	AccessPremiumizeHoster = 'premiumizehoster'
	AccessOffcloud = 'offcloud'
	AccessOffcloudTorrent = 'offcloudtorrent'
	AccessOffcloudUsenet = 'offcloudusenet'
	AccessOffcloudHoster = 'offcloudhoster'
	AccessRealdebrid = 'realdebrid'
	AccessRealdebridTorrent = 'realdebridtorrent'
	AccessRealdebridUsenet = 'realdebridusenet'
	AccessRealdebridHoster = 'realdebridhoster'

	LookupPremiumize = 'premiumize'
	LookupOffcloud = 'offcloud'
	LookupRealdebrid = 'realdebrid'

	FilterNone = None
	FilterSettings = -1

	SortNone = 'none'
	SortBest = 'best'
	SortShuffle = 'shuffle'
	SortPopularity = 'popularity'
	SortTimeAdded = 'timeadded'
	SortTimeUpdated = 'timeupdated'
	SortVideoQuality = 'videoquality'
	SortAudioChannels = 'audiochannels'
	SortFileSize = 'filesize'
	SortStreamSeeds = 'streamseeds'
	SortStreamAge = 'streamage'
	SortIds = [SortNone, SortBest, SortShuffle, SortPopularity, SortTimeAdded, SortTimeUpdated, SortVideoQuality, SortAudioChannels, SortFileSize, SortStreamSeeds, SortStreamAge]

	OrderAscending = 'ascending'
	OrderDescending = 'descendig'
	OrderIds = [OrderAscending, OrderDescending]

	VoteUp = OrionApi.VoteUp
	VoteDown = OrionApi.VoteDown

	ChoiceInclude = 'include'
	ChoiceExclude = 'exclude'
	ChoiceRequire = 'require'
	ChoiceIds = [ChoiceInclude, ChoiceExclude, ChoiceRequire]

	QualityOrder = [None] + OrionStream.QualityOrder
	ChannelsOrder = [None] + OrionStream.ChannelsOrder

	Editions = [OrionStream.EditionExtended, OrionStream.EditionCollector, OrionStream.EditionDirector, OrionStream.EditionCommentary, OrionStream.EditionMaking, OrionStream.EditionSpecial]

	LimitLink = 1024
	LimitMagnet = 65535

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, data = {}):
		self.mData = None
		self.mStreams = None
		self.dataSet(data = data)

	##############################################################################
	# INTERNAL
	##############################################################################

	def _select(self, select):
		return self.type() if select == OrionItem.SelectDefault else select

	def _valid(self, value):
		return not value == None and not value == ''

	##############################################################################
	# ACCESS
	##############################################################################

	def _accessEqual(self, access1, access2):
		if not len(access1.keys()) == len(access2.keys()):
			return False
		for key1, value1 in OrionTools.iterator(access1):
			for key2, value2 in OrionTools.iterator(access2):
				if key1 == key2 and not value1 == value2:
					return False
		return True

	def _accessSave(self):
		access = {}
		for stream in self.mData['streams']:
			access[stream['id']] = stream['access']
		OrionSettings.set('internal.api.access', access)

	def _accessLoad(self):
		access = OrionSettings.getObject('internal.api.access')
		if access:
			streams = []
			for stream in self.mData['streams']:
				if not 'id' in stream or not stream['id']:
					streams.append(stream)
				elif 'id' in stream and stream['id']:
					try:
						if not self._accessEqual(access[stream['id']], stream['access']):
							# Only send neccessary information
							new = {'id' : stream['id'], 'access' : stream['access']}
							try: new['movie'] = {'id' : stream['movie']['id']}
							except: pass
							try: new['show'] = {'id' : stream['show']['id']}
							except: pass
							try: new['episode'] = {'number' : stream['episode']['number']}
							except: pass
							streams.append(new)
					except:
						# Sometimes access[id] can fail to lookup id if something unexpected happens during scraping and the items was not added to the settings.
						# OrionTools.error() # Do not print errors, since this can happen too often.
						OrionTools.error(message = 'Failed to lookup previous stream access', exception = False)
			self.mData['streams'] = streams
			OrionSettings.set('internal.api.access', '')

	##############################################################################
	# UPDATE
	##############################################################################

	def update(self):
		try:
			if self.mStreams == None or self.mStreams == []: return False
			if not self.mData['type']: return False

			if self.mData['type'] == OrionItem.TypeMovie:
				if not self._valid(self.mData['movie']['id']['imdb']): return False
			elif self.mData['type'] == OrionItem.TypeShow:
				if not self._valid(self.mData['show']['id']['imdb']): return False
				if not self._valid(self.mData['episode']['number']['season']): return False
				if not self._valid(self.mData['episode']['number']['episode']): return False
			else:
				return False

			# Invalid links
			streams = []
			for stream in self.mData['streams']:
				link = stream['links']
				if OrionTools.isArray(link):
					for i in link:
						if not OrionTools.linkIsMagnet(link):
							link = i
							break
					if OrionTools.isArray(link):
						link = link[0]
				if link == None or link == '': continue
				magnet = OrionTools.linkIsMagnet(link)

				# Not a standard torrent magnet of HTTP/FTP link
				if not magnet and not link.startswith('http://') and not link.startswith('https://') and not link.startswith('ftp://') and not link.startswith('ftps://'):
					continue

				if not magnet:
					# Not normal link (eg: http://localhost or http://downloads)
					if not '.' in link.split('://')[1].split('/')[0]: continue

					# Streams with cookie/session/headers
					if '|' in link: continue

					# Very long links which are most likely invalid or contain other cookie/session/headers data
					if len(link) > OrionItem.LimitLink: continue

				if len(link) > OrionItem.LimitMagnet: continue

				streams.append(stream)
			self.mData['streams'] = streams
			self._accessLoad()
			if len(self.mData['streams']) == 0: return False
			return OrionApi().streamUpdate(self.mData)
		except:
			OrionTools.error()
			return False

	##############################################################################
	# RETRIEVE
	##############################################################################

	@classmethod
	def retrieve(self,

				type,

				query = None,

				idOrion = None,
				idImdb = None,
				idTmdb = None,
				idTvdb = None,
				idTvrage = None,
				idTrakt = None,
				idSlug = None,

				numberSeason = None,
				numberEpisode = None,

				limitCount = FilterSettings,
				limitRetry = FilterSettings,
				limitOffset = FilterSettings,
				limitPage = FilterSettings,

				timeAdded = FilterSettings,
				timeAddedAge = FilterSettings,
				timeUpdated = FilterSettings,
				timeUpdatedAge = FilterSettings,

				sortValue = FilterSettings,
				sortOrder = FilterSettings,

				popularityPercent = FilterSettings,
				popularityCount = FilterSettings,

				streamType = FilterSettings,
				streamOrigin = FilterSettings,
				streamSource = FilterSettings,
				streamHoster = FilterSettings,
				streamSeeds = FilterSettings,
				streamAge = FilterSettings,

				protocolTorrent = FilterSettings,
				protocolUsenet = FilterSettings,
				protocolHoster = FilterSettings,

				access = FilterSettings,
				lookup = FilterSettings,

				filePack = FilterSettings,
				fileName = FilterSettings,
				fileSize = FilterSettings,
				fileUnknown = FilterSettings,

				metaRelease = FilterSettings,
				metaUploader = FilterSettings,
				metaEdition = FilterSettings,

				videoQuality = FilterSettings,
				videoCodec = FilterSettings,
				video3D = FilterSettings,

				audioType = FilterSettings,
				audioChannels = FilterSettings,
				audioSystem = FilterSettings,
				audioCodec = FilterSettings,
				audioLanguages = FilterSettings,

				subtitleType = FilterSettings,
				subtitleLanguages = FilterSettings,

				item = None
			):

		try:
			app = OrionApp.instance().id()
			if not OrionSettings.getFiltersEnabled(app): app = None

			def pick(app, function):
				include = getattr(OrionSettings, function)(app, True, False)
				if include == None: include = []
				exclude = getattr(OrionSettings, function)(app, False, True)
				if exclude == None: exclude = []
				if len(exclude) > len(include): return include
				else: return [('-' + value) for value in exclude]

			def typeIs(type, input, settings):
				try:
					if type is input: return True
				except: pass
				try:
					if type in input: return True
				except: pass
				try:
					if input is settings: return True
				except: pass
				try:
					if input in settings: return True
				except: pass
				return False

			# Important to use "is" (equivalent to ===)
			modeCombined = OrionSettings.getFiltersInteger('filters.limit.mode', app) == 0
			if limitCount is OrionItem.FilterSettings:
				if modeCombined: limitCount = OrionSettings.getFiltersInteger('filters.limit.count', app)
				else: limitCount = OrionSettings.getFiltersInteger('filters.limit.count.' + type, app)
			if limitRetry is OrionItem.FilterSettings:
				if modeCombined: limitRetry = OrionSettings.getFiltersInteger('filters.limit.retry', app)
				else: limitRetry = OrionSettings.getFiltersInteger('filters.limit.retry.' + type, app)
			if limitOffset is OrionItem.FilterSettings: limitOffset = OrionItem.FilterNone
			if limitPage is OrionItem.FilterSettings: limitPage = OrionItem.FilterNone
			if sortValue is OrionItem.FilterSettings: sortValue = OrionItem.SortIds[OrionSettings.getFiltersInteger('filters.sort.value', app)]
			if sortOrder is OrionItem.FilterSettings: sortOrder = OrionItem.OrderIds[OrionSettings.getFiltersInteger('filters.sort.order', app)]
			if popularityPercent is OrionItem.FilterSettings: popularityPercent = OrionSettings.getFiltersInteger('filters.limit.popularity', app)
			if popularityCount is OrionItem.FilterSettings: popularityCount = OrionItem.FilterNone
			if timeAdded is OrionItem.FilterSettings: timeAdded = OrionItem.FilterNone
			if timeAddedAge is OrionItem.FilterSettings: timeAddedAge = OrionItem.FilterNone
			if timeUpdated is OrionItem.FilterSettings: timeUpdated = OrionItem.FilterNone
			if timeUpdatedAge is OrionItem.FilterSettings: timeUpdatedAge = OrionSettings.getFiltersInteger('filters.limit.age', app)
			if streamType is OrionItem.FilterSettings: streamType = OrionSettings.getFiltersInteger('filters.stream.type', app)
			if streamOrigin is OrionItem.FilterSettings: streamOrigin = pick(app, 'getFiltersStreamOrigin')
			if streamSource is OrionItem.FilterSettings: streamSource = pick(app, 'getFiltersStreamSource')
			if streamHoster is OrionItem.FilterSettings: streamHoster = pick(app, 'getFiltersStreamHoster')
			if streamSeeds is OrionItem.FilterSettings: streamSeeds = OrionSettings.getFiltersInteger('filters.stream.seeds', app)
			if streamAge is OrionItem.FilterSettings: streamAge = OrionSettings.getFiltersInteger('filters.stream.age', app)
			if protocolTorrent is OrionItem.FilterSettings:
				protocolTorrent = []
				protocol = OrionSettings.getFiltersInteger('filters.stream.protocol.torrent', app)
				if protocol in (2, 3, 4, 5, 14): protocolTorrent.append(OrionItem.ProtocolMagnet)
				if protocol in (1, 2, 4, 6, 7, 10): protocolTorrent.append(OrionItem.ProtocolHttp)
				if protocol in (1, 2, 5, 6, 8, 11): protocolTorrent.append(OrionItem.ProtocolHttps)
				if protocol in (1, 3, 4, 7, 9, 12): protocolTorrent.append(OrionItem.ProtocolFtp)
				if protocol in (1, 3, 5, 8, 9, 13): protocolTorrent.append(OrionItem.ProtocolFtps)
			if protocolUsenet is OrionItem.FilterSettings:
				protocolUsenet = []
				protocol = OrionSettings.getFiltersInteger('filters.stream.protocol.usenet', app)
				if protocol in (1, 2, 3, 6): protocolUsenet.append(OrionItem.ProtocolHttp)
				if protocol in (1, 2, 4, 7): protocolUsenet.append(OrionItem.ProtocolHttps)
				if protocol in (1, 3, 5, 8): protocolUsenet.append(OrionItem.ProtocolFtp)
				if protocol in (1, 4, 5, 9): protocolUsenet.append(OrionItem.ProtocolFtps)
			if protocolHoster is OrionItem.FilterSettings:
				protocolHoster = []
				protocol = OrionSettings.getFiltersInteger('filters.stream.protocol.hoster', app)
				if protocol in (1, 2, 3, 6): protocolHoster.append(OrionItem.ProtocolHttp)
				if protocol in (1, 2, 4, 7): protocolHoster.append(OrionItem.ProtocolHttps)
				if protocol in (1, 3, 5, 8): protocolHoster.append(OrionItem.ProtocolFtp)
				if protocol in (1, 4, 5, 9): protocolHoster.append(OrionItem.ProtocolFtps)
			if access is OrionItem.FilterSettings:
				access = []
				accessSettings = OrionSettings.getFiltersInteger('filters.access', app)
				if accessSettings in (1, 3, 5): access.append(OrionItem.AccessDirect)
				if accessSettings in (4, 5): access.append(OrionItem.AccessIndirect)
				if accessSettings in (1, 2, 4, 5):
					value = OrionSettings.getFiltersInteger('filters.access.premiumize', app)
					if value == 1: access.append(OrionItem.AccessPremiumize)
					if value in (2, 3, 5): access.append(OrionItem.AccessPremiumizeTorrent)
					if value in (2, 4, 6): access.append(OrionItem.AccessPremiumizeUsenet)
					if value in (3, 4, 7): access.append(OrionItem.AccessPremiumizeHoster)
				if accessSettings in (1, 2, 4, 5):
					value = OrionSettings.getFiltersInteger('filters.access.offcloud', app)
					if value == 1: access.append(OrionItem.AccessOffcloud)
					if value in (2, 3, 5): access.append(OrionItem.AccessOffcloudTorrent)
					if value in (2, 4, 6): access.append(OrionItem.AccessOffcloudUsenet)
					if value in (3, 4, 7): access.append(OrionItem.AccessOffcloudHoster)
				if accessSettings in (1, 2, 4, 5):
					value = OrionSettings.getFiltersInteger('filters.access.realdebrid', app)
					if value == 1: access.append(OrionItem.AccessRealdebrid)
					if value in (2, 3, 5): access.append(OrionItem.AccessRealdebridTorrent)
					if value in (2, 4, 6): access.append(OrionItem.AccessRealdebridUsenet)
					if value in (3, 4, 7): access.append(OrionItem.AccessRealdebridHoster)
			if lookup is OrionItem.FilterSettings:
				lookup = []
				if OrionSettings.getFiltersBoolean('filters.lookup', app):
					if OrionSettings.getFiltersBoolean('filters.lookup.premiumize', app): lookup.append(OrionItem.LookupPremiumize)
					if OrionSettings.getFiltersBoolean('filters.lookup.offcloud', app): lookup.append(OrionItem.LookupOffcloud)
					if OrionSettings.getFiltersBoolean('filters.lookup.realdebrid', app): lookup.append(OrionItem.LookupRealdebrid)
			if filePack is OrionItem.FilterSettings: filePack = OrionItem.ChoiceIds[OrionSettings.getFiltersInteger('filters.file.pack', app)]
			if fileName is OrionItem.FilterSettings: fileName = OrionItem.ChoiceIds[OrionSettings.getFiltersInteger('filters.file.name', app)]
			if fileSize is OrionItem.FilterSettings: fileSize = [OrionSettings.getFiltersInteger('filters.file.size.minimum', app), OrionSettings.getFiltersInteger('filters.file.size.maximum', app)] if OrionSettings.getFiltersBoolean('filters.file.size', app) else OrionItem.FilterNone
			if fileUnknown is OrionItem.FilterSettings: fileUnknown = OrionSettings.getFiltersBoolean('filters.file.size.unknown', app)
			if metaRelease is OrionItem.FilterSettings: metaRelease = pick(app, 'getFiltersMetaRelease')
			if metaUploader is OrionItem.FilterSettings: metaUploader = pick(app, 'getFiltersMetaUploader')
			if metaEdition is OrionItem.FilterSettings: metaEdition = pick(app, 'getFiltersMetaEdition')
			if videoQuality is OrionItem.FilterSettings:
				minimum = OrionSettings.getFiltersInteger('filters.video.quality.minimum', app)
				maximum = OrionSettings.getFiltersInteger('filters.video.quality.maximum', app)
				videoQuality = [OrionItem.QualityOrder[min(minimum, maximum)], OrionItem.QualityOrder[max(minimum, maximum)]] if OrionSettings.getFiltersBoolean('filters.video.quality', app) else OrionItem.FilterNone
			if videoCodec is OrionItem.FilterSettings: videoCodec = pick(app, 'getFiltersVideoCodec')
			if video3D is OrionItem.FilterSettings: video3D = OrionItem.ChoiceIds[OrionSettings.getFiltersInteger('filters.video.3d', app)]
			if audioType is OrionItem.FilterSettings: audioType = pick(app, 'getFiltersAudioType')
			if audioSystem is OrionItem.FilterSettings: audioSystem = pick(app, 'getFiltersAudioSystem')
			if audioCodec is OrionItem.FilterSettings: audioCodec = pick(app, 'getFiltersAudioCodec')
			if audioChannels is OrionItem.FilterSettings:
				minimum = OrionSettings.getFiltersInteger('filters.audio.channels.minimum', app)
				maximum = OrionSettings.getFiltersInteger('filters.audio.channels.maximum', app)
				audioChannels = [OrionItem.ChannelsOrder[min(minimum, maximum)], OrionItem.ChannelsOrder[max(minimum, maximum)]] if OrionSettings.getFiltersBoolean('filters.audio.channels', app) else OrionItem.FilterNone
			if audioLanguages is OrionItem.FilterSettings: audioLanguages = pick(app, 'getFiltersAudioLanguages')

			if not limitCount is OrionItem.FilterNone:
				if limitCount <= 0: limitCount == OrionItem.FilterNone
				if limitCount > 5000: limitCount == 5000
			if not limitRetry is OrionItem.FilterNone:
				if limitRetry <= 0: limitRetry == OrionItem.FilterNone
				if limitRetry > 5000: limitRetry == 5000
			if sortValue is OrionItem.FilterNone:
				sortOrder = OrionItem.FilterNone
			elif sortValue <= 0:
				sortValue = OrionItem.SortNone
				sortOrder = OrionItem.FilterNone
			if not popularityPercent is OrionItem.FilterNone:
				if popularityPercent <= 0: popularityPercent == OrionItem.FilterNone
				elif popularityPercent > 1: popularityPercent /= 100.0 # Important for the percentage retrieved from settings
			if not timeAdded is OrionItem.FilterNone and timeAdded <= 0:
				timeAdded = OrionItem.FilterNone
			if not timeAddedAge is OrionItem.FilterNone and timeAddedAge <= 0:
				timeAddedAge = OrionItem.FilterNone
			if not timeUpdated is OrionItem.FilterNone and timeUpdated <= 0:
				timeUpdated = OrionItem.FilterNone
			if not timeUpdatedAge is OrionItem.FilterNone and timeUpdatedAge <= 0:
				timeUpdatedAge = OrionItem.FilterNone
			if not streamOrigin is OrionItem.FilterNone:
				if OrionTools.isString(streamOrigin) and not streamOrigin == '': streamOrigin = [streamOrigin]
				if OrionTools.isList(streamOrigin):
					if len(streamOrigin) == 0: streamOrigin = OrionItem.FilterNone
				else: streamOrigin = OrionItem.FilterNone
			if not streamSource is OrionItem.FilterNone:
				if OrionTools.isString(streamSource) and not streamSource == '': streamSource = [streamSource]
				if OrionTools.isList(streamSource):
					if len(streamSource) == 0: streamSource = OrionItem.FilterNone
				else: streamSource = OrionItem.FilterNone
			if not streamHoster is OrionItem.FilterNone:
				if OrionTools.isString(streamHoster) and not streamHoster == '': streamHoster = [streamHoster]
				if OrionTools.isList(streamHoster):
					if len(streamHoster) == 0: streamHoster = OrionItem.FilterNone
				else: streamHoster = OrionItem.FilterNone
			if not streamSeeds is OrionItem.FilterNone and (streamSeeds <= 0 or not streamType in (0, 1, 2, 4)):
				streamSeeds = OrionItem.FilterNone
			if not streamAge is OrionItem.FilterNone and (streamAge <= 0 or not streamType in (0, 1, 3, 5)):
				streamAge = OrionItem.FilterNone
			if not streamType is OrionItem.FilterNone: # Must be after subsettings.
				types = []
				if typeIs(OrionStream.TypeTorrent, streamType, (1, 2, 4)): types.append(OrionStream.TypeTorrent)
				if typeIs(OrionStream.TypeUsenet, streamType, (1, 3, 5)): types.append(OrionStream.TypeUsenet)
				if typeIs(OrionStream.TypeHoster, streamType, (2, 3, 6)): types.append(OrionStream.TypeHoster)
				if len(types) == 0: streamType = OrionItem.FilterNone
				else: streamType = types
			if not protocolTorrent is OrionItem.FilterNone:
				if len(protocolTorrent) == 0: protocolTorrent = None
			if not protocolUsenet is OrionItem.FilterNone:
				if len(protocolUsenet) == 0: protocolUsenet = None
			if not protocolHoster is OrionItem.FilterNone:
				if len(protocolHoster) == 0: protocolHoster = None
			if not access is OrionItem.FilterNone:
				if len(access) == 0: access = None
			if not lookup is OrionItem.FilterNone:
				if len(lookup) == 0: lookup = None
			if not filePack is OrionItem.FilterNone:
				if filePack is OrionItem.ChoiceInclude: filePack = OrionItem.FilterNone
				elif filePack is OrionItem.ChoiceRequire: filePack = True
				elif filePack is OrionItem.ChoiceExclude: filePack = False
				else: filePack = OrionItem.FilterNone
			if not fileName is OrionItem.FilterNone:
				if fileName is OrionItem.ChoiceInclude: fileName = OrionItem.FilterNone
				elif fileName is OrionItem.ChoiceRequire: fileName = True
				elif fileName is OrionItem.ChoiceExclude: fileName = False
				elif OrionTools.isString(videoCodec) and not fileName == '': fileName = [fileName]
				elif OrionTools.isList(fileName):
					if len(fileName) == 0: fileName = OrionItem.FilterNone
				else: fileName = OrionItem.FilterNone
			if not fileSize is OrionItem.FilterNone:
				# If given in MB.
				try:
					if OrionTools.isNumber(fileSize):
						if fileSize < 1048576: fileSize *= 1048576
					else:
						for i in range(len(fileSize)):
							if fileSize[i] < 1048576: fileSize[i] *= 1048576
				except: pass
				fileSize = OrionApi.range(fileSize)
			if not fileUnknown is OrionItem.FilterNone:
				fileUnknown = bool(fileUnknown)
			if not metaRelease is OrionItem.FilterNone:
				if OrionTools.isString(metaRelease) and not metaRelease == '': metaRelease = [metaRelease]
				if OrionTools.isList(metaRelease):
					if len(metaRelease) == 0: metaRelease = OrionItem.FilterNone
				else: metaRelease = OrionItem.FilterNone
			if not metaUploader is OrionItem.FilterNone:
				if OrionTools.isString(metaUploader) and not metaUploader == '': metaUploader = [metaUploader]
				if OrionTools.isList(metaUploader):
					if len(metaUploader) == 0: metaUploader = OrionItem.FilterNone
				else: metaUploader = OrionItem.FilterNone
			if not metaEdition is OrionItem.FilterNone:
				if OrionTools.isString(metaEdition):
					metaEdition = metaEdition.lower()
					if metaEdition in OrionItem.Editions: metaEdition = [metaEdition]
					else: metaEdition = OrionItem.FilterNone
				if OrionTools.isList(metaEdition):
					if len(metaEdition) == 0: metaEdition = OrionItem.FilterNone
				else: metaEdition = OrionItem.FilterNone
			if not videoQuality is OrionItem.FilterNone:
				videoQuality = OrionApi.range(videoQuality)
			if not videoCodec is OrionItem.FilterNone:
				if OrionTools.isString(videoCodec) and not videoCodec == '': videoCodec = [videoCodec]
				if OrionTools.isList(videoCodec):
					if len(videoCodec) == 0: videoCodec = OrionItem.FilterNone
				else: videoCodec = OrionItem.FilterNone
			if not video3D is OrionItem.FilterNone:
				if video3D is OrionItem.ChoiceInclude: video3D = OrionItem.FilterNone
				elif video3D is OrionItem.ChoiceRequire: video3D = True
				elif video3D is OrionItem.ChoiceExclude: video3D = False
				else: video3D = OrionItem.FilterNone
			if not audioType is OrionItem.FilterNone:
				if OrionTools.isString(audioType) and not audioType == '': audioType = [audioType]
				if OrionTools.isList(audioType):
					if len(audioType) == 0: audioType = OrionItem.FilterNone
				else: audioType = OrionItem.FilterNone
			if not audioSystem is OrionItem.FilterNone:
				if OrionTools.isString(audioSystem) and not audioSystem == '': audioSystem = [audioSystem]
				if OrionTools.isList(audioSystem):
					if len(audioSystem) == 0: audioSystem = OrionItem.FilterNone
				else: audioSystem = OrionItem.FilterNone
			if not audioCodec is OrionItem.FilterNone:
				if OrionTools.isString(audioCodec) and not audioCodec == '': audioCodec = [audioCodec]
				if OrionTools.isList(audioCodec):
					if len(audioCodec) == 0: audioCodec = OrionItem.FilterNone
				else: audioCodec = OrionItem.FilterNone
			if not audioChannels is OrionItem.FilterNone:
				audioChannels = OrionApi.range(audioChannels)
			if not audioLanguages is OrionItem.FilterNone:
				if OrionTools.isString(audioLanguages) and not audioLanguages == '': audioLanguages = [audioLanguages]
				if OrionTools.isList(audioLanguages):
					if len(audioLanguages) == 0: audioLanguages = OrionItem.FilterNone
				else: audioLanguages = OrionItem.FilterNone
			if not subtitleType is OrionItem.FilterNone:
				if OrionTools.isString(subtitleType) and not subtitleType == '': subtitleType = [subtitleType]
				if OrionTools.isList(subtitleType):
					if len(subtitleType) == 0: subtitleType = OrionItem.FilterNone
				else: subtitleType = OrionItem.FilterNone
			if not subtitleLanguages is OrionItem.FilterNone:
				if OrionTools.isString(subtitleLanguages) and not subtitleLanguages == '': subtitleLanguages = [subtitleLanguages]
				if OrionTools.isList(subtitleLanguages):
					if len(subtitleLanguages) == 0: subtitleLanguages = OrionItem.FilterNone
				else: subtitleLanguages = OrionItem.FilterNone

			filters = {}

			if not type == None: filters['type'] = type
			if not query == None: filters['query'] = query

			if not idOrion == None or not idImdb == None or not idTmdb == None or not idTvdb == None or not idTvrage == None or not idTrakt == None or not idSlug == None:
				filters['id'] = {}
				if not idOrion == None: filters['id']['orion'] = idOrion
				if not idImdb == None: filters['id']['imdb'] = idImdb
				if not idTmdb == None: filters['id']['tmdb'] = idTmdb
				if not idTvdb == None: filters['id']['tvdb'] = idTvdb
				if not idTvrage == None: filters['id']['tvrage'] = idTvrage
				if not idTrakt == None: filters['id']['trakt'] = idTrakt
				if not idSlug == None: filters['id']['slug'] = idSlug

			if not numberSeason == None or not numberEpisode == None:
				filters['number'] = {}
				if not numberSeason == None: filters['number']['season'] = numberSeason
				if not numberEpisode == None: filters['number']['episode'] = numberEpisode

			if not limitCount == None or not limitRetry == None or not limitOffset == None or not limitPage == None:
				filters['limit'] = {}
				if not limitCount == None: filters['limit']['count'] = limitCount
				if not limitRetry == None: filters['limit']['retry'] = limitRetry
				if not limitOffset == None: filters['limit']['offset'] = limitOffset
				if not limitPage == None: filters['limit']['page'] = limitPage

			if not timeAdded == None or not timeUpdated == None:
				filters['time'] = {}
				if not timeAdded == None: filters['time']['added'] = timeAdded
				if not timeUpdated == None: filters['time']['updated'] = timeUpdated

			if not timeAddedAge == None or not timeUpdatedAge == None:
				filters['age'] = {}
				if not timeAddedAge == None: filters['age']['added'] = timeAddedAge
				if not timeUpdatedAge == None: filters['age']['updated'] = timeUpdatedAge

			if not sortValue == None or not sortOrder == None:
				filters['sort'] = {}
				if not sortValue == None: filters['sort']['value'] = sortValue
				if not sortOrder == None: filters['sort']['order'] = sortOrder

			if not popularityPercent == None or not popularityCount == None:
				filters['popularity'] = {}
				if not popularityPercent == None: filters['popularity']['percent'] = popularityPercent
				if not popularityCount == None: filters['popularity']['count'] = popularityCount

			if not streamType == None or not streamOrigin == None or not streamSource == None or not streamHoster == None or not streamSeeds == None or not streamAge == None:
				filters['stream'] = {}
				if not streamType == None: filters['stream']['type'] = streamType
				if not streamOrigin == None: filters['stream']['origin'] = streamOrigin
				if not streamSource == None: filters['stream']['source'] = streamSource
				if not streamHoster == None: filters['stream']['hoster'] = streamHoster
				if not streamSeeds == None: filters['stream']['seeds'] = streamSeeds
				if not streamAge == None: filters['stream']['age'] = streamAge

			if not protocolTorrent == None or not protocolUsenet == None or not protocolHoster == None:
				filters['protocol'] = {}
				if not protocolTorrent == None:
					if OrionTools.isString(protocolTorrent): protocolTorrent = [protocolTorrent]
					filters['protocol']['torrent'] = protocolTorrent
				if not protocolUsenet == None:
					if OrionTools.isString(protocolUsenet): protocolUsenet = [protocolUsenet]
					filters['protocol']['usenet'] = protocolUsenet
				if not protocolHoster == None:
					if OrionTools.isString(protocolHoster): protocolHoster = [protocolHoster]
					filters['protocol']['hoster'] = protocolHoster

			if not access == None:
				if OrionTools.isString(access): access = [access]
				filters['access'] = access

			if not lookup == None:
				if OrionTools.isString(lookup): lookup = [lookup]
				filters['lookup'] = lookup

			if not filePack == None or not fileName == None or not fileSize == None or not fileUnknown == None:
				filters['file'] = {}
				if not filePack == None: filters['file']['pack'] = filePack
				if not fileName == None: filters['file']['name'] = fileName
				if not fileSize == None: filters['file']['size'] = fileSize
				if not fileUnknown == None: filters['file']['unknown'] = fileUnknown

			if not metaRelease == None or not metaUploader == None or not metaEdition == None:
				filters['meta'] = {}
				if not metaRelease == None: filters['meta']['release'] = metaRelease
				if not metaUploader == None: filters['meta']['uploader'] = metaUploader
				if not metaEdition == None: filters['meta']['edition'] = metaEdition

			if not videoQuality == None or not videoCodec == None or not video3D == None:
				filters['video'] = {}
				if not videoQuality == None: filters['video']['quality'] = videoQuality
				if not videoCodec == None: filters['video']['codec'] = videoCodec
				if not video3D == None: filters['video']['3d'] = video3D

			if not audioType == None or not audioChannels == None or not audioSystem == None or not audioCodec == None or not audioLanguages == None:
				filters['audio'] = {}
				if not audioType == None: filters['audio']['type'] = audioType
				if not audioChannels == None: filters['audio']['channels'] = audioChannels
				if not audioSystem == None: filters['audio']['system'] = audioSystem
				if not audioCodec == None: filters['audio']['codec'] = audioCodec
				if not audioLanguages == None: filters['audio']['languages'] = audioLanguages

			if not subtitleType == None or not subtitleLanguages == None:
				filters['subtitle'] = {}
				if not subtitleType == None: filters['subtitle']['type'] = subtitleType
				if not subtitleLanguages == None: filters['subtitle']['languages'] = subtitleLanguages

			api = OrionApi()
			api.streamRetrieve(filters)
			if api.statusSuccess():
				item = OrionItem(data = api.data())
				item._accessSave()
				return item
			else: return None
		except:
			OrionTools.error()
			return None

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	def dataSet(self, data):
		try:
			self.mData = data
			self.mStreams = []
			streams = self.mData['streams']
			for stream in streams:
				self.mStreams.append(OrionStream(data = stream))
			if len(self.mStreams) > 0:
				OrionSettings.setFilters(self.mStreams)
			return True
		except:
			OrionTools.error()
			return False

	##############################################################################
	# TYPE
	##############################################################################

	def type(self, default = None):
		try: return self.mData['type']
		except: return default

	##############################################################################
	# ID
	##############################################################################

	def idOrion(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['orion']
		except: return default

	def idOrionMovie(self, default = None):
		return self.idOrion(select = OrionItem.SelectMovie, default = default)

	def idOrionShow(self, default = None):
		return self.idOrion(select = OrionItem.SelectShow, default = default)

	def idOrionEpisode(self, default = None):
		return self.idOrion(select = OrionItem.SelectEpisode, default = default)

	def idImdb(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['imdb']
		except: return default

	def idTmdb(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['tmdb']
		except: return default

	def idTvdb(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['tvdb']
		except: return default

	def idTvrage(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['tvrage']
		except: return default

	def idTrakt(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['trakt']
		except: return default

	def idSlug(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['slug']
		except: return default

	##############################################################################
	# POPULARITY
	##############################################################################

	def popularityCount(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['popularity']['count']
		except: return default

	def popularityCountMovie(self, default = None):
		return self.popularityCount(select = OrionItem.SelectMovie, default = default)

	def popularityCountShow(self, default = None):
		return self.popularityCount(select = OrionItem.SelectShow, default = default)

	def popularityCountEpisode(self, default = None):
		return self.popularityCount(select = OrionItem.SelectEpisode, default = default)

	def popularityPercent(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['popularity']['percent']
		except: return default

	def popularityPercentMovie(self, default = None):
		return self.popularityPercent(select = OrionItem.SelectMovie, default = default)

	def popularityPercentShow(self, default = None):
		return self.popularityPercent(select = OrionItem.SelectShow, default = default)

	def popularityPercentEpisode(self, default = None):
		return self.popularityPercent(select = OrionItem.SelectEpisode, default = default)

	@classmethod
	def _popularityVote(self, idItem, idStream, vote = VoteUp, notification = False):
		return OrionApi().streamVote(item = idItem, stream = idStream, vote = vote, silent = not notification)

	@classmethod
	def popularityVote(self, idItem, idStream, vote = VoteUp, notification = False, wait = False):
		thread = threading.Thread(target = self._popularityVote, args = (idItem, idStream, vote, notification))
		thread.start()
		if wait: thread.join()

	##############################################################################
	# REMOVE
	##############################################################################

	@classmethod
	def _remove(self, idItem, idStream, notification = False):
		return OrionApi().streamRemove(item = idItem, stream = idStream, silent = not notification)

	@classmethod
	def remove(self, idItem, idStream, notification = False, wait = False):
		thread = threading.Thread(target = self._remove, args = (idItem, idStream, notification))
		thread.start()
		if wait: thread.join()

	##############################################################################
	# TIME
	##############################################################################

	def timeAdded(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['time']['added']
		except: return default

	def timeAddedMovie(self, default = None):
		return self.timeAdded(select = OrionItem.SelectMovie, default = default)

	def timeAddedShow(self, default = None):
		return self.timeAdded(select = OrionItem.SelectShow, default = default)

	def timeAddedEpisode(self, default = None):
		return self.timeAdded(select = OrionItem.SelectEpisode, default = default)

	def timeUpdated(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['time']['updated']
		except: return default

	def timeUpdatedMovie(self, default = None):
		return self.timeUpdated(select = OrionItem.SelectMovie, default = default)

	def timeUpdatedShow(self, default = None):
		return self.timeUpdated(select = OrionItem.SelectShow, default = default)

	def timeUpdatedEpisode(self, default = None):
		return self.timeUpdated(select = OrionItem.SelectEpisode, default = default)

	##############################################################################
	# META
	##############################################################################

	def metaTitle(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['title']
		except: return default

	def metaTitleMovie(self, default = None):
		return self.metaTitle(select = OrionItem.SelectMovie, default = default)

	def metaTitleShow(self, default = None):
		return self.metaTitle(select = OrionItem.SelectShow, default = default)

	def metaTitleEpisode(self, default = None):
		return self.metaTitle(select = OrionItem.SelectEpisode, default = default)

	def metaYear(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['year']
		except: return default

	def metaYearMovie(self, default = None):
		return self.metaYear(select = OrionItem.SelectMovie, default = default)

	def metaYearShow(self, default = None):
		return self.metaYear(select = OrionItem.SelectShow, default = default)

	def metaYearEpisode(self, default = None):
		return self.metaYear(select = OrionItem.SelectEpisode, default = default)

	##############################################################################
	# NUMBER
	##############################################################################

	def number(self, select = SelectDefault, default = None):
		try: return self.mData[OrionItem.SelectEpisode]['number'][OrionItem.SelectEpisode if select == OrionItem.SelectEpisode else OrionItem.SelectSeason]
		except: return default

	def numberSeason(self, default = None):
		return self.number(select = OrionItem.SelectSeason, default = default)

	def numberEpisode(self, default = None):
		return self.number(select = OrionItem.SelectEpisode, default = default)

	##############################################################################
	# COUNT
	##############################################################################

	def count(self, default = None):
		return self.countFiltered(default = default)

	def countTotal(self, default = None):
		try: return self.mData['count']['total']
		except: return default

	def countFiltered(self, default = None):
		try: return self.mData['count']['filtered']
		except: return default

	##############################################################################
	# REQUESTS
	##############################################################################

	def requestsTotal(self, default = None):
		try: return self.mData['requests']['total']
		except: return default

	def requestsDailyLimit(self, default = None):
		try: return self.mData['requests']['daily']['limit']
		except: return default

	def requestsDailyUsed(self, default = None):
		try: return self.mData['requests']['daily']['used']
		except: return default

	def requestsDailyRemaining(self, default = None):
		try: return self.mData['requests']['daily']['remaining']
		except: return default

	##############################################################################
	# STREAMS
	##############################################################################

	def streams(self):
		return self.mStreams
