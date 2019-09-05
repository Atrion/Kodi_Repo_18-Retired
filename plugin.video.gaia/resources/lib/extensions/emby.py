# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import re
import copy
import threading
from resources.lib.extensions import tools
from resources.lib.extensions import convert
from resources.lib.extensions import network
from resources.lib.extensions import metadata
from resources.lib.extensions import interface

class Emby(object):

	Name = 'Emby'
	Api = 'emby'
	Link = 'https://emby.media'

	CategoryUsers = 'Users'
	CategoryVideos = 'Videos'
	CategoryItems = 'Items'
	CategorySearch = 'Search'

	ActionAuthenticate = 'AuthenticateByName'
	ActionInfo = 'PlaybackInfo'
	ActionHints = 'Hints'
	ActionStream = 'stream'

	TypeLocal = 'local'
	TypeRemote = 'remote'

	ModeDirect = 'direct'
	ModeDefault = 'default'
	ModeTranscoded = 'transcoded'

	DefaultHost = '127.0.0.1'
	DefaultPort = 8096
	DefaultEncryption = False
	DefaultMode = 0
	DefaultContainer = 'mp4'

	Transcoding = [
		{'mode' : ModeDirect, 'label' : 35560, 'description' : 35576},
		{'mode' : ModeDefault, 'label' : 35561, 'description' : 35577},

		# HD4K
		{'mode' : ModeTranscoded, 'label' : 35562, 'quality' : metadata.Metadata.VideoQualityHd4k, 'bitrate' : 52428800}, # 50 mbps
		{'mode' : ModeTranscoded, 'label' : 35562, 'quality' : metadata.Metadata.VideoQualityHd4k, 'bitrate' : 47185920}, # 45 mbps
		{'mode' : ModeTranscoded, 'label' : 35562, 'quality' : metadata.Metadata.VideoQualityHd4k, 'bitrate' : 41943040}, # 40 mbps
		{'mode' : ModeTranscoded, 'label' : 35562, 'quality' : metadata.Metadata.VideoQualityHd4k, 'bitrate' : 36700160}, # 35 mbps
		{'mode' : ModeTranscoded, 'label' : 35562, 'quality' : metadata.Metadata.VideoQualityHd4k, 'bitrate' : 31457280}, # 30 mbps
		{'mode' : ModeTranscoded, 'label' : 35562, 'quality' : metadata.Metadata.VideoQualityHd4k, 'bitrate' : 26214400}, # 25 mbps
		{'mode' : ModeTranscoded, 'label' : 35562, 'quality' : metadata.Metadata.VideoQualityHd4k, 'bitrate' : 20971520}, # 20 mbps
		{'mode' : ModeTranscoded, 'label' : 35562, 'quality' : metadata.Metadata.VideoQualityHd4k, 'bitrate' : 15728640}, # 15 mbps

		# HD1080
		{'mode' : ModeTranscoded, 'label' : 35563, 'quality' : metadata.Metadata.VideoQualityHd1080, 'bitrate' : 10485760}, # 10 mbps
		{'mode' : ModeTranscoded, 'label' : 35563, 'quality' : metadata.Metadata.VideoQualityHd1080, 'bitrate' : 9437184}, # 9 mbps
		{'mode' : ModeTranscoded, 'label' : 35563, 'quality' : metadata.Metadata.VideoQualityHd1080, 'bitrate' : 8388608}, # 8 mbps
		{'mode' : ModeTranscoded, 'label' : 35563, 'quality' : metadata.Metadata.VideoQualityHd1080, 'bitrate' : 7340032}, # 7 mbps
		{'mode' : ModeTranscoded, 'label' : 35563, 'quality' : metadata.Metadata.VideoQualityHd1080, 'bitrate' : 6291456}, # 6 mbps
		{'mode' : ModeTranscoded, 'label' : 35563, 'quality' : metadata.Metadata.VideoQualityHd1080, 'bitrate' : 5242880}, # 5 mbps

		# HD720
		{'mode' : ModeTranscoded, 'label' : 35564, 'quality' : metadata.Metadata.VideoQualityHd720, 'bitrate' : 4194304}, # 4 mbps
		{'mode' : ModeTranscoded, 'label' : 35564, 'quality' : metadata.Metadata.VideoQualityHd720, 'bitrate' : 3145728}, # 3 mbps
		{'mode' : ModeTranscoded, 'label' : 35564, 'quality' : metadata.Metadata.VideoQualityHd720, 'bitrate' : 2097152}, # 2 mbps
		{'mode' : ModeTranscoded, 'label' : 35564, 'quality' : metadata.Metadata.VideoQualityHd720, 'bitrate' : 1048576}, # 1 mbps

		# SD
		{'mode' : ModeTranscoded, 'label' : 35565, 'quality' : metadata.Metadata.VideoQualitySd480, 'bitrate' : 768000}, # 750 kbps
		{'mode' : ModeTranscoded, 'label' : 35565, 'quality' : metadata.Metadata.VideoQualitySd360, 'bitrate' : 409600}, # 500 kbps
		{'mode' : ModeTranscoded, 'label' : 35565, 'quality' : metadata.Metadata.VideoQualitySd240, 'bitrate' : 409600}, # 400 kbps
		{'mode' : ModeTranscoded, 'label' : 35565, 'quality' : metadata.Metadata.VideoQualitySd144, 'bitrate' : 307200}, # 300 kbps
	]

	Resolutions = {
		metadata.Metadata.VideoQualityHd4k : {'width' : 4096, 'height' : 2160},
		metadata.Metadata.VideoQualityHd1080 : {'width' : 1920, 'height' : 1080},
		metadata.Metadata.VideoQualityHd720 : {'width' : 1280, 'height' : 720},
		metadata.Metadata.VideoQualitySd480 : {'width' : 640, 'height' : 480},
		metadata.Metadata.VideoQualitySd360 : {'width' : 480, 'height' : 360},
		metadata.Metadata.VideoQualitySd240 : {'width' : 352, 'height' : 240},
		metadata.Metadata.VideoQualitySd144 : {'width' : 256, 'height' : 144},
	}

	Channels = {
		metadata.Metadata.VideoQualityHd4k : 8,
		metadata.Metadata.VideoQualityHd1080 : 6,
		metadata.Metadata.VideoQualityHd720 : 2,
		metadata.Metadata.VideoQualitySd480 : 2,
		metadata.Metadata.VideoQualitySd360 : 2,
		metadata.Metadata.VideoQualitySd240 : 2,
		metadata.Metadata.VideoQualitySd144 : 2,
	}

	def __init__(self):
		self.mLock = threading.Lock()
		if tools.Settings.has('accounts.premium.emby.servers.list'):
			self.mServers = tools.Settings.getList('accounts.premium.emby.servers.list')
		else:
			self.mServers = [self._serverCreate()]
			self._settingsSave()

	def _lock(self):
		self.mLock.acquire()

	def _unlock(self):
		self.mLock.release()

	def _identifier(self):
		return tools.Hardware.identifier()

	def _execute(self, function, *arguments):
		threads = []
		arguments = list(arguments)
		for i in range(len(self.mServers)):
			args = copy.deepcopy(arguments)
			args.insert(0, i)
			threads.append(threading.Thread(target = function, args = args))
		[i.start() for i in threads]
		[i.join() for i in threads]

	def _link(self, index, category, action, id = None, parameters = None):
		link = ''
		sever = self.mServers[index]
		if sever['encryption']: link += 'https://'
		else: link += 'http://'
		try: host = re.search('(^.*?\:\/\/)?([^\/:?#]+)(?:[\/:?#]|$)', sever['host']).group(2)
		except: host = sever['host']
		link += host + ':' + str(sever['port'])
		link = network.Networker.linkJoin(link, Emby.Api, category)
		if id: link = network.Networker.linkJoin(link, str(id))
		link = network.Networker.linkJoin(link, action)
		return network.Networker.linkCreate(link = link, parameters = parameters)

	def _stream(self, index, idItem, idSource = None, idSession = None, container = None):
		action = Emby.ActionStream + '.' + (container if container else Emby.DefaultContainer).lower()
		transcoding = Emby.Transcoding[self.mServers[index]['mode']]

		parameters = {}
		parameters['DeviceId'] = self._identifier()
		if idSource: parameters['MediaSourceId'] = idSource
		if idSession: parameters['PlaySessionId'] = idSession
		if transcoding['mode'] == Emby.ModeDirect:
			parameters['Static'] = 'true'
		elif transcoding['mode'] == Emby.ModeTranscoded:
			quality = transcoding['quality']
			parameters['VideoCodec'] = 'h264'
			parameters['VideoBitRate'] = transcoding['bitrate']
			parameters['MaxWidth'] = Emby.Resolutions[quality]['width']
			parameters['MaxHeight'] = Emby.Resolutions[quality]['height']
			parameters['MaxAudioChannels'] = Emby.Channels[quality]

		# Use the source ID in the link. The normal item ID also works, but some remote servers have pre-transcoded files that have the same item ID, but different source ID.
		return self._link(index = index, category = Emby.CategoryVideos, action = action, id = idSource, parameters = parameters)

	def _request(self, index, method, category, action, id = None, parameters = None, authentication = True):
		link = self._link(index = index, category = category, action = action, id = id)
		headers = self._requestHeaders(index = index)
		networker = network.Networker()
		result = networker.retrieveJson(method = method, json = not parameters is None, link = link, headers = headers, parameters = parameters)
		if networker.errorCode() == 401 and authentication: # Reauthenticate if token is expiered or revoked.
			self._authenticate(index = index)
			result = self._request(index = index, method = method, category = category, action = action, parameters = parameters, authentication = False)
		return result

	def _requestHeaders(self, index):
		sever = self.mServers[index]
		version = tools.System.versionKodi()
		device = tools.System.name()
		identifier = self._identifier()
		userid = self.mServers[index]['userid']
		token = self.mServers[index]['token']
		return {'X-Emby-Authorization' : 'Emby UserId="%s", Client="Kodi", Device="%s", DeviceId="%s", Version="%s", Token="%s"' % (userid if userid else '', device, identifier, version, token if token else '')}

	def _authenticate(self, index, username = None, password = None):
		if username is None: username = self.mServers[index]['username']
		if password is None: password = self.mServers[index]['password']
		parameters = {
			'Username' : username,
			'Pw' : password,
			'Password' : tools.Hash.sha1(password),
			'PasswordMd5' : tools.Hash.md5(password),
		}
		result = self._request(index = index, method = network.Networker.MethodPost, category = Emby.CategoryUsers, action = Emby.ActionAuthenticate, parameters = parameters, authentication = False)
		try:
			token = result['AccessToken']
			userid = result['SessionInfo']['UserId']
			result = True
		except:
			token = None
			userid = None
			result = False
		self._lock()
		self.mServers[index]['username'] = username
		self.mServers[index]['password'] = password
		self.mServers[index]['token'] = token
		self.mServers[index]['userid'] = userid
		self._unlock()
		self._settingsSave()
		return result

	def _labelTitle(self, type):
		return interface.Translation.string(35551) + ' ' + interface.Translation.string(type)

	def _labelType(self, host):
		return interface.Translation.string(32314 if network.Networker.local(host) else 35559)

	def _labelEncryption(self, encryption):
		return interface.Translation.string(33341 if encryption else 33342)

	def _labelMode(self, mode):
		item = Emby.Transcoding[mode]
		result = [interface.Translation.string(item['label'])]
		try: result.append(convert.ConverterSpeed(value = item['bitrate'], unit = convert.ConverterSpeed.Bit).stringOptimal(unit = convert.ConverterSpeed.Bit, notation = convert.ConverterSpeed.SpeedLetter, places = 0))
		except: pass
		return interface.Format.fontSeparator().join(result)

	def _labelAuthentication(self, username):
		return username if username else interface.Translation.string(33112)

	def _serverCreate(self, host = None, port = None, encryption = None, mode = None, username = None, password = None, userid = None, token = None):
		return {
			'host' : Emby.DefaultHost if host is None else host,
			'port' : Emby.DefaultPort if port is None else port,
			'encryption' : Emby.DefaultEncryption if encryption is None else encryption,
			'mode' : Emby.DefaultMode if mode is None else mode,
			'username' : '' if username is None else username,
			'password' : '' if password is None else password,
			'userid' : '' if userid is None else userid,
			'token' : '' if token is None else token,
		}

	def _serverAdd(self):
		self.mServers.append(self._serverCreate())
		self._settingsSave()
		self._server(len(self.mServers) - 1)

	def _serverRemove(self, index):
		del self.mServers[index]
		self._settingsSave()
		self.settings()

	def _serverHost(self, index):
		self.mServers[index]['host'] = interface.Dialog.input(title = self._labelTitle(35556), default = self.mServers[index]['host'], type = interface.Dialog.InputAlphabetic)
		self._server(index = index, save = True)

	def _serverPort(self, index):
		self.mServers[index]['port'] = interface.Dialog.input(title = self._labelTitle(35557), default = self.mServers[index]['port'], type = interface.Dialog.InputNumeric)
		self._server(index = index, save = True)

	def _serverEncryption(self, index):
		self.mServers[index]['encryption'] = interface.Dialog.option(title = self._labelTitle(35558), message = 35574)
		self._server(index = index, save = True)

	def _serverMode(self, index):
		items = [{'title' : interface.Dialog.prefixBack(35374), 'action' : self._server, 'parameters' : {'index' : index}, 'close' : True},]

		for i in range(len(Emby.Transcoding)):
			item = Emby.Transcoding[i]
			description = []
			try:
				description.append(interface.Translation.string(item['description']))
			except: pass
			try:
				description.append(convert.ConverterSpeed(value = item['bitrate'], unit = convert.ConverterSpeed.Bit).stringOptimal(unit = convert.ConverterSpeed.Bit, notation = convert.ConverterSpeed.SpeedLetter, places = 0))
				description.append(item['quality'])
				description.append(metadata.Metadata.audioChannelsConvert(Emby.Channels[item['quality']]))
			except: pass
			items.append({'title' : interface.Translation.string(item['label']), 'value' : interface.Format.fontSeparator().join(description), 'return' : i, 'close' : True})

		result = interface.Dialog.information(title = self._labelTitle(35160), items = items)
		if result: self.mServers[index]['mode'] = result
		self._server(index = index, save = True)

	def _serverAuthentication(self, index):
		username = interface.Dialog.input(title = self._labelTitle(33267), default = self.mServers[index]['username'], type = interface.Dialog.InputAlphabetic)
		password = interface.Dialog.input(title = self._labelTitle(32307), default = self.mServers[index]['password'], type = interface.Dialog.InputAlphabetic)
		interface.Loader.show()
		success = self._authenticate(index = index, username = username, password = password)
		interface.Loader.hide()
		if not success: interface.Dialog.confirm(title = self._labelTitle(33101), message = 35578)
		self._server(index = index, save = True)

	def _server(self, index, save = False):
		if save: self._settingsSave()
		server = self.mServers[index]
		items = [
			{'title' : interface.Dialog.prefixBack(33486), 'close' : True},
			{'title' : interface.Dialog.prefixBack(35374), 'action' : self.settings, 'close' : True},
			{'title' : interface.Dialog.prefixNext(35555), 'action' : self._serverRemove, 'parameters' : {'index' : index}, 'close' : True},
			{'title' : 35556, 'value' : server['host'], 'action' : self._serverHost, 'parameters' : {'index' : index}, 'close' : True},
			{'title' : 35557, 'value' : str(server['port']), 'action' : self._serverPort, 'parameters' : {'index' : index}, 'close' : True},
			{'title' : 35558, 'value' : self._labelEncryption(server['encryption']), 'action' : self._serverEncryption, 'parameters' : {'index' : index}, 'close' : True},
			{'title' : 35160, 'value' : self._labelMode(server['mode']), 'action' : self._serverMode, 'parameters' : {'index' : index}, 'close' : True},
			{'title' : 33101, 'value' : self._labelAuthentication(server['username']), 'action' : self._serverAuthentication, 'parameters' : {'index' : index}, 'close' : True},
		]
		interface.Dialog.information(title = self._labelTitle(35553), items = items)

	def _settingsSave(self):
		self._lock()
		count = len(self.mServers)
		tools.Settings.set('accounts.premium.emby.servers.list', self.mServers)
		tools.Settings.set('accounts.premium.emby.servers', '%d %s' % (count, interface.Translation.string(35553 if count == 1 else 35552)))
		self._unlock()

	def enabled(self):
		return tools.Settings.getBoolean('accounts.premium.emby.enabled')

	@classmethod
	def link(self):
		return Emby.Link

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.emby', raw = True)
		if open: tools.System.openLink(link)
		return link

	def verify(self):
		self._execute(self._authenticate)
		count = sum(1 if i['token'] else 0 for i in self.mServers)
		if count == 0: return False
		elif count == len(self.mServers): return True
		else: return None # Some of the servers work.

	def settings(self):
		items = [
			{'title' : interface.Dialog.prefixBack(33486), 'close' : True},
			{'title' : interface.Dialog.prefixNext(35554), 'action' : self._serverAdd, 'close' : True},
		]
		for i in range(len(self.mServers)):
			server = self.mServers[i]
			items.append({'title' : interface.Dialog.prefixNext('%s %d' % (interface.Translation.string(35553), i + 1)), 'value' : '%s (%s)' % (server['host'], self._labelType(server['host'])), 'action' : self._server, 'parameters' : {'index' : i}, 'close' : True})
		interface.Dialog.information(title = self._labelTitle(35552), items = items)

	def _info(self, index, id):
		try:
			host = self.mServers[index]['host']
			source = 'localhost' if network.Networker.local(host) else network.Networker.linkDomain(host, subdomain = False, topdomain = False)

			infos = self._request(index = index, method = network.Networker.MethodGet, category = Emby.CategoryItems, action = Emby.ActionInfo, id = id)
			session = infos['PlaySessionId']
			infos = infos['MediaSources']

			for info in infos:
				streams = info['MediaStreams']
				item = {
					'id' :
					{
						'item' : id,
						'source' : info['Id'],
						'session' : session,
					},
					'stream' : {
						'link' : None,
						'server' : host,
						'source' : source,
					},
					'file' : {
						'name' : info['Name'],
						'size' : info['Size'],
						'container' : info['Container'],
					},
					'video' : {
						'quality' : None,
						'width' : None,
						'height' : None,
						'codec' : None,
						'bitrate' : None,
						'framerate' : None,
						'3d' : None,
					},
					'audio' : {
						'languages' : None,
						'channels' : None,
						'codec' : None,
						'bitrate' : None,
						'samplerate' : None,
					},
					'subtitle' : {
						'languages' : None,
						'codec' : None,
					},
				}

				item['stream']['link'] = self._stream(index = index, idItem = item['id']['item'], idSource = item['id']['source'], idSession = item['id']['session'], container = item['file']['container'])

				video = [i for i in streams if i['Type'] == 'Video']
				if len(video) > 0:
					if len(video) > 1:
						try: video = [i for i in video if i['IsDefault']][0]
						except: pass
					else:
						video = video[0]
					try: item['video']['quality'] = metadata.Metadata.videoResolutionQuality(width = video['Width'], height = video['Height'])
					except: pass
					try: item['video']['width'] = video['Width']
					except: pass
					try: item['video']['height'] = video['Height']
					except: pass
					try: item['video']['codec'] = video['Codec']
					except: pass
					try: item['video']['bitrate'] = video['BitRate']
					except: pass
					try: item['video']['framerate'] = video['RealFrameRate']
					except: pass
				try: item['video']['3d'] = bool(video['Video3DFormat'])
				except: item['video']['3d'] = False

				audio = [i for i in streams if i['Type'] == 'Audio']
				if len(audio) > 0:
					try: item['audio']['languages'] = list(set([tools.Language.code(i['Language']) for i in audio]))
					except: pass
					if len(audio) > 1:
						try: audio = [i for i in audio if i['IsDefault']][0]
						except: pass
					else:
						audio = audio[0]
					try: item['audio']['channels'] = audio['Channels']
					except: pass
					try: item['audio']['codec'] = audio['Codec']
					except: pass
					try: item['audio']['bitrate'] = audio['BitRate']
					except: pass
					try: item['audio']['samplerate'] = audio['SampleRate']
					except: pass

				subtitle = [i for i in streams if i['Type'] == 'Subtitle']
				if len(subtitle) > 0:
					try: item['subtitle']['languages'] = list(set([tools.Language.code(i['Language']) for i in subtitle]))
					except: pass
					if len(subtitle) > 1:
						try: subtitle = [i for i in subtitle if i['IsDefault']][0]
						except: pass
					else:
						subtitle = subtitle[0]
					try: item['subtitle']['codec'] = subtitle['Codec']
					except: pass

				self._lock()
				self.mResults.append(item)
				self._unlock()
		except:
			tools.Logger.error()

	def _search(self, index, type, title, year, season, episode, exact):
		try:
			television = None
			if exact:
				type = 'Movie,Episode'
			else:
				television = tools.Media.typeTelevision(type)
				type = 'Episode' if television else 'Movie'
			items = self._request(index = index, method = network.Networker.MethodGet, category = Emby.CategorySearch, action = Emby.ActionHints, parameters = {'SearchTerm' : title, 'IncludeItemTypes' : type})
			items = items['SearchHints']
			if not exact:
				if television: items = [i for i in items if i['ParentIndexNumber'] == season and i['IndexNumber'] == episode]
				else: items = [i for i in items if i['ProductionYear'] == year]
			threads = [threading.Thread(target = self._info, args = (index, i['Id'])) for i in items]
			[i.start() for i in threads]
			[i.join() for i in threads]
		except:
			tools.Logger.error()

	def search(self, type, title, year = None, season = None, episode = None, exact = False):
		self.mResults = []
		self._execute(self._search, type, title, year, season, episode, exact)

		# Emby can return mutiple item IDs, but all items have the same source ID.
		# Seems to be episodes that can be listed multiple times (show, season, episode, etc).
		ids = []
		results = []
		for i in self.mResults:
			id = i['id']['source']
			if not id in ids:
				ids.append(id)
				results.append(i)

		return results
