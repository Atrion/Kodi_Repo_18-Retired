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

import re
import urllib
import urllib2
import threading

from resources.lib.debrid import base
from resources.lib.extensions import convert
from resources.lib.extensions import cache
from resources.lib.extensions import tools
from resources.lib.extensions import network
from resources.lib.extensions import metadata

class Core(base.Core):

	Id = 'offcloud'
	Name = 'OffCloud'
	Abbreviation = 'O'
	Priority = 2

	LinkMain = 'https://offcloud.com'
	LinkApi = 'https://offcloud.com/api/'

	Services = None
	ServiceTorrent = {'id' : 'torrent', 'name' : 'Torrent', 'domain' : 'torrent'}
	ServiceUsenet = {'id' : 'usenet', 'name' : 'Usenet', 'domain' : 'usenet'}

	ServiceStatusUnknown = 'unknown'
	ServiceStatusOnline = 'online' # working flawlessly
	ServiceStatusOffline = 'offline' # broken for the time being
	ServiceStatusCloud = 'cloud' # restricted to cloud
	ServiceStatusLimited = 'limited' # quota reached, 24 hours ETA
	ServiceStatusAwaiting = 'awaiting' # coming soon, waiting for demand
	ServiceStatusSoon = 'soon' # to be implemented within next few days

	# Modes
	ModeGet = 'get'
	ModePost = 'post'
	ModePut = 'put'
	ModeDelete = 'delete'

	# Headers
	UserAgent = tools.System.name() + ' ' + tools.System.version()

	# Categories
	CategoryInstant = 'instant'
	CategoryCloud = 'cloud'
	CategoryCache = 'cache'
	CategoryRemote = 'remote'
	CategoryRemoteAccount = 'remote-account'
	CategoryProxy = 'proxy'
	CategoryLogin = 'login'
	CategoryAccount = 'account'
	CategoryTorrent = 'torrent'
	CategorySites = 'sites'

	# Actions
	ActionDownload = 'download'
	ActionUpload = 'upload'
	ActionList = 'list'
	ActionStatus = 'status'
	ActionExplore = 'explore'
	ActionCheck = 'check'
	ActionGet = 'get'
	ActionStats = 'stats'
	ActionHistory = 'history'
	ActionRemove = 'remove'

	# Parameters
	ParameterApiKey = 'apiKey' # apikey does not work for POST.
	ParameterRequestId = 'requestId'
	ParameterUrl = 'url'
	ParameterProxyId = 'proxyId'
	ParameterRemoteOptionId = 'remoteOptionId'
	ParameterFolderId = 'folderId'
	ParameterHashes = 'hashes[]'
	ParameterMessages = 'messageIds[]'

	# Statuses
	StatusUnknown = 'unknown'
	StatusError = 'error'
	StatusCanceled = 'canceled'
	StatusQueued = 'queued'
	StatusBusy = 'busy'
	StatusProcessing = 'processing' # unzipping a cached archive.
	StatusInitialize = 'initialize'
	StatusFinalize = 'finalize'
	StatusFinished = 'finished'
	StatusQueued = 'queued'

	# Server
	ServerUnknown = 'unknown'
	ServerMain = 'main'
	ServerProxy = 'proxy'

	# Errors
	ErrorUnknown = 'unknown'
	ErrorOffCloud = 'offcloud'
	ErrorLimitCloud = 'limitcloud'
	ErrorLimitPremium = 'limitpremium'
	ErrorLimitLink = 'limitlink'
	ErrorLimitProxy = 'limitproxy'
	ErrorLimitVideo = 'limitvideo'
	ErrorPremium = 'premium'
	ErrorSelection = 'selection' # No file selected from list of items.
	ErrorInaccessible = 'inaccessible' # Eg: 404 error.

	# Limits
	LimitLink = 2000 # Maximum length of a URL.
	LimitHashesGet = 40 # Maximum number of 40-character hashes to use in GET parameter so that the URL length limit is not exceeded.
	LimitHashesPost = 100 # Even when the hashes are send via POST, Premiumize seems to ignore the last ones (+- 1000 hashes). When too many hashes are sent at once (eg 500-900), if often causes a request timeout. Keep the limit small enough. Rather start multiple requests which should create multipel threads on the server.

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		base.Core.__init__(self, Core.Id, Core.Name)

		self.mDebug = True
		self.mLinkBasic = None
		self.mLinkFull = None
		self.mParameters = None
		self.mSuccess = None
		self.mError = None
		self.mResult = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _request(self, mode, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None):
		self.mResult = None
		try:
			if not httpTimeout:
				if httpData: httpTimeout = 60
				else: httpTimeout = 30

			self.mLinkBasic = link
			self.mParameters = parameters
			self.mSuccess = None
			self.mError = None

			# If httpData is set, send the apikey via GET.
			if mode == Core.ModeGet or mode == Core.ModePut or mode == Core.ModeDelete or httpData:
				if parameters:
					if not link.endswith('?'):
						link += '?'
					parameters = urllib.urlencode(parameters, doseq = True)
					link += parameters
			else:
				# urllib only sends a POST request if there is HTTP data.
				# Hence, if there are no parameters, add dummy ones.
				if not parameters: parameters = {'x' : ''}
				httpData = urllib.urlencode(parameters, doseq = True)

			self.mLinkFull = link

			if httpData: request = urllib2.Request(link, data = httpData)
			else: request = urllib2.Request(link)

			if mode == Core.ModePut or mode == Core.ModeDelete:
				request.get_method = lambda: mode.upper()

			request.add_header('User-Agent', Core.UserAgent)
			if httpHeaders:
				for key in httpHeaders:
					request.add_header(key, httpHeaders[key])

			response = urllib2.urlopen(request, timeout = httpTimeout)
			self.mResult = response.read()
			response.close()

			try:
				self.mResult = tools.Converter.jsonFrom(self.mResult)
				if 'error' in self.mResult:
					self.mSuccess = False
					self.mError = 'API Error'
					try:
						if 'downloaded yet' in self.mResult['error'].lower():
							return None # Avoid errors being printed.
					except: pass
				else:
					self.mSuccess = True
			except:
				self.mSuccess = False
				self.mError = 'JSON Error'

			if self.mSuccess: return self.mResult
			else: self._requestErrors('The call to the OffCloud API failed', link, httpData, self.mResult)
		except (urllib2.HTTPError, urllib2.URLError) as error:
			self.mSuccess = False
			if hasattr(error, 'code'):
				errorCode = error.code
				errorString = ' ' + str(errorCode)
			else:
				errorCode = 0
				errorString = ''
			self.mError = 'OffCloud Unavailable [HTTP/URL Error%s]' % errorString
			self._requestErrors(self.mError, link, httpData, self.mResult)
		except Exception as error:
			if isinstance(self.mResult, basestring):
				html = '<html>' in self.mResult
			else:
				html = False
			self.mSuccess = False
			if html: self.mError = 'HTML Error'
			else: self.mError = 'Unknown Error'
			self._requestErrors(self.mError, link, httpData, self.mResult)
		return None

	def _requestErrors(self, message, link, payload, result = None):
		if self.mDebug:
			link = str(link)
			payload = str(payload) if len(str(payload)) < 300 else 'Payload too large to display'
			result = str(result) if len(str(result)) < 300 else 'Result too large to display'
			tools.Logger.error(str(message) + (': Link [%s] Payload [%s] Result [%s]' % (link, payload, result)))

	def _retrieve(self, mode, category, action = None, url = None, proxyId = None, requestId = None, hash = None, segment = None, httpTimeout = None, httpData = None, httpHeaders = None):
		if category == Core.CategoryTorrent and action == Core.ActionUpload:
			# For some reason, this function is not under the API.
			link = network.Networker.linkJoin(Core.LinkMain, category, action)
		elif category == Core.CategoryCloud and action == Core.ActionExplore:
			link = network.Networker.linkJoin(Core.LinkApi, category, action, requestId)
			requestId = None # Do not add as parameter
		elif action == Core.ActionRemove:
			link = network.Networker.linkJoin(Core.LinkMain, category, action, requestId)
			requestId = None # Do not add as parameter
		elif action:
			link = network.Networker.linkJoin(Core.LinkApi, category, action)
		else:
			link = network.Networker.linkJoin(Core.LinkApi, category)

		parameters = {}
		parameters[Core.ParameterApiKey] = self.accountKey()

		if not url == None: parameters[Core.ParameterUrl] = url
		if not proxyId == None: parameters[Core.ParameterProxyId] = proxyId
		if not requestId == None: parameters[Core.ParameterRequestId] = requestId
		if not hash == None:
			if isinstance(hash, basestring):
				parameters[Core.ParameterHashes] = hash.lower()
			else:
				for i in range(len(hash)):
					hash[i] = hash[i].lower()
				parameters[Core.ParameterHashes] = hash
		if not segment == None:
			parameters[Core.ParameterMessages] = segment

		return self._request(mode = mode, link = link, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders)

	##############################################################################
	# SUCCESS
	##############################################################################

	def success(self):
		return self.mSuccess

	def error(self):
		return self.mError

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.offcloud', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.offcloud.enabled')

	def accountValid(self):
		return not self.accountKey() == ''

	def accountKey(self):
		return tools.Settings.getString('accounts.debrid.offcloud.api') if self.accountEnabled() else ''

	def accountVerify(self):
		result = self._retrieve(mode = Core.ModeGet, category = Core.CategoryAccount, action = Core.ActionStats)
		return self.success() == True and 'userId' in result and not result['userId'] == None and not result['userId'] == ''

	def account(self, cached = True):
		try:
			if self.accountValid():
				import datetime

				if cached: result = cache.Cache().cacheShort(self._retrieve, mode = Core.ModeGet, category = Core.CategoryAccount, action = Core.ActionStats)
				else: result = cache.Cache().cacheClear(self._retrieve, mode = Core.ModeGet, category = Core.CategoryAccount, action = Core.ActionStats)

				limits = result['limits']
				expiration = tools.Time.datetime(result['expirationDate'], '%d-%m-%Y')

				return {
					'user' : result['userId'],
					'email' : result['email'],
					'premium' : result['isPremium'],
					'expiration' : {
						'timestamp' : tools.Time.timestamp(expiration),
						'date' : expiration.strftime('%Y-%m-%d'),
						'remaining' : (expiration - datetime.datetime.today()).days
					},
					'limits' : {
						'links' : limits['links'],
						'premium' : limits['premium'],
						'torrents' : limits['torrent'],
						'streaming' : limits['streaming'],
						'cloud' : {
							'bytes' : limits['cloud'],
							'description' : convert.ConverterSize(float(limits['cloud'])).stringOptimal(),
						},
						'proxy' : {
							'bytes' : limits['proxy'],
							'description' : convert.ConverterSize(float(limits['proxy'])).stringOptimal(),
						},
					},
				}
			else:
				return None
		except:
			tools.Logger.error()
			return None

	##############################################################################
	# SERVICES
	##############################################################################

	def services(self, cached = True, onlyEnabled = False):
		# Even thow ServicesUpdate is a class variable, it will be destrcucted if there are no more Premiumize instances.
		if Core.Services == None:
			Core.Services = []

			streamingTorrent = self.streamingTorrent()
			streamingUsenet = self.streamingUsenet()
			streamingHoster = self.streamingHoster()

			try:
				if cached: result = cache.Cache().cacheShort(self._retrieve, mode = Core.ModeGet, category = Core.CategorySites)
				else: result = cache.Cache().cacheClear(self._retrieve, mode = Core.ModeGet, category = Core.CategorySites)

				# Sometimes error HTML page is returned.
				if not isinstance(result, list):
					Core.Services = None
					return None

				for i in result:
					id = i['name']
					if id == Core.ServiceUsenet['id']:
						enabled = streamingUsenet
						name = Core.ServiceUsenet['name']
						domain = Core.ServiceUsenet['domain']
						domains = []
					else:
						enabled = streamingHoster

						name = i['displayName']
						index = name.find('.')
						if index >= 0: name = name[:index]
						name = name.title()

						domain = i['displayName'].lower()
						if not '.' in domain: domain = i['hosts'][0].lower()

						domains = i['hosts']

					try:
						instant = not bool(i['noInstantDownload'])
					except:
						instant = True

					try:
						stream = bool(i['isVideoStreaming'])
					except:
						stream = False

					try:
						status = i['isActive'].lower()
						if 'healthy' in status: status = Core.ServiceStatusOnline
						elif 'dead' in status: status = Core.ServiceStatusOffline
						elif 'cloud' in status: status = Core.ServiceStatusCloud
						elif 'limited' in status: status = Core.ServiceStatusLimited
						elif 'awaiting' in status: status = Core.ServiceStatusAwaiting
						elif 'r&d' in status: status = Core.ServiceStatusSoon
						else: status = Core.ServiceStatusUnknown
					except:
						status = Core.ServiceStatusUnknown

					try:
						limitSize = i['maxAmountPerUser']
						if isinstance(limitSize, basestring) and 'unlimited' in limitSize.lower():
							limitSize = 0
						else:
							limitSize = long(limitSize)
					except:
						limitSize = 0

					try:
						limitChunks = i['maxChunks']
						if isinstance(limitChunks, basestring) and 'unlimited' in limitChunks.lower():
							limitChunks = 0
						else:
							limitChunks = long(limitChunks)
					except:
						limitChunks = 0

					try:
						limitGlobal = i['maxChunksGlobal']
						if isinstance(limitGlobal, basestring) and 'unlimited' in limitGlobal.lower():
							limitGlobal = 0
						else:
							limitGlobal = long(limitGlobal)
					except:
						limitGlobal = 0

					Core.Services.append({
						'id' : id,
						'enabled' : enabled and status == Core.ServiceStatusOnline,
						'status' : status,
						'instant' : instant,
						'stream' : stream,
						'name' : name,
						'domain' : domain,
						'domains' : domains,
						'limits' :
						{
							'size' : limitSize,
							'chunks' : limitChunks,
							'global' : limitGlobal,
						},
					})

				Core.Services.append({
					'id' : Core.ServiceTorrent['id'],
					'enabled' : streamingTorrent,
					'status' : Core.ServiceStatusOnline,
					'instant' : True,
					'stream' : False,
					'name' : Core.ServiceTorrent['name'],
					'domain' : Core.ServiceTorrent['domain'],
					'domains' : [],
					'limits' :
					{
						'size' : 0,
						'chunks' : 0,
						'global' : 0,
					},
				})

			except:
				tools.Logger.error()

		if onlyEnabled:
			return [i for i in Core.Services if i['enabled']]
		else:
			return Core.Services

	def servicesList(self, onlyEnabled = False):
		try:
			services = self.services(onlyEnabled = onlyEnabled)
			result = [service['domain'] for service in services] # Torrents and Usenet
			for service in services:
				if 'domain' in service:
					result.append(service['domain'])
				if 'domains' in service:
					result.extend(service['domains'])
			return list(set(result))
		except:
			return []

	def service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		for service in self.services():
			if service['id'].lower() == nameOrDomain or service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain or ('domains' in service and nameOrDomain in [i.lower() for i in service['domains']]):
				return service
		return None

	##############################################################################
	# PROXY
	##############################################################################

	def proxyList(self):
		try:
			result = self._retrieve(mode = Core.ModePost, category = Core.CategoryProxy, action = Core.ActionList)
			if self.success():
				proxies = []
				result = result['list']
				for proxy in result:
					try:
						location = re.search('\\(([^(0-9)]*)', proxy['name']).group(1).strip()
						location = location.replace('US', 'United States')
						location = location.replace(',', ' -')
					except:
						tools.Logger.error()
						location = None

					try:
						type = re.search('(.*)\\(', proxy['name']).group(1).strip().lower()
						if Core.ServerMain in type: type = Core.ServerMain
						elif Core.ServerProxy in type: type = Core.ServerProxy
						else: type = Core.ServerUnknown
					except:
						type = Core.ServerUnknown

					try:
						if not location == None and not type == Core.ServerUnknown:
							description = '[' + type.capitalize() + '] ' + location
						elif not location == None:
							description = location
						else:
							description = proxy['name']
					except:
						description = proxy['name']

					if not location == None: name = location
					else: name = proxy['name']

					proxies.append({
						'id' : proxy['id'],
						'type' : type,
						'location' : location,
						'region' : proxy['region'].lower(),
						'name' : name,
						'description' : description,
					})
				return proxies
		except:
			tools.Logger.error()
		return None

	##############################################################################
	# ADD
	##############################################################################

	def _addLink(self, category = CategoryCloud, result = None, season = None, episode = None):
		id = None
		link = None
		items = None
		error = None
		try:
			if 'not_available' in result:
				result = result['not_available'].lower()
				if 'cloud' in result: error = Core.ErrorLimitCloud
				elif 'premium' in result: error = Core.ErrorLimitPremium
				elif 'link' in result: error = Core.ErrorLimitLink
				elif 'video' in result: error = Core.ErrorLimitVideo
				elif 'proxy' in result: error = Core.ErrorLimitProxy
				else: error = Core.ErrorUnknown
			elif 'error' in result:
				result = result['error'].lower()
				if 'reserved' in result and 'premium' in result:
					error = Core.ErrorPremium
			elif 'requestId' in result:
				id = result['requestId']
				try:
					items = self.item(category = category, id = id, season = season, episode = episode, transfer = True, files = True)
					link = items['video']['link']
				except: pass
		except:
			pass
		return self.addResult(error = error, id = id, link = link, extra = {'category' : category}, items = items)

	def _addType(self, link, source = None):
		if source == network.Container.TypeTorrent:
			return network.Container.TypeTorrent
		elif source == network.Container.TypeUsenet:
			return network.Container.TypeUsenet
		else:
			result = network.Container(link).type()
			if result == network.Container.TypeUnknown:
				return network.Container.TypeHoster
			else:
				return result

	def _addCategory(self, link = None, type = None, source = None):
		if type == None: type = self._addType(link = link, source = source)
		if type == network.Container.TypeTorrent or type == network.Container.TypeUsenet:
			return Core.CategoryCloud
		else:
			if tools.Settings.getBoolean('accounts.debrid.offcloud.instant'): return Core.CategoryInstant
			else: return Core.CategoryCloud

	def _addProxy(self):
		result = tools.Settings.getString('accounts.debrid.offcloud.location.id')
		if result == '': result = None
		return result

	def add(self, link, category = None, title = None, season = None, episode = None, pack = False, source = None, proxy = None):
		type = self._addType(link = link, source = source)
		if category == None: category = self._addCategory(type = type)
		if category == Core.CategoryInstant and proxy == None: proxy = self._addProxy()
		if type == network.Container.TypeTorrent:
			return self.addTorrent(link = link, title = title, season = season, episode = episode)
		elif type == network.Container.TypeUsenet:
			return self.addUsenet(link = link, title = title, season = season, episode = episode)
		else:
			return self.addHoster(link = link, category = category, season = season, episode = episode, proxy = proxy)

	def addInstant(self, link, season = None, episode = None, proxy = None):
		result = self._retrieve(mode = Core.ModePost, category = Core.CategoryInstant, action = Core.ActionDownload, url = link, proxyId = proxy)
		if self.success(): return self._addLink(category = Core.CategoryInstant, result = result, season = season, episode = episode)
		else: return self.addResult(error = Core.ErrorOffCloud)

	def addCloud(self, link, title = None, season = None, episode = None, source = None):
		result = self._retrieve(mode = Core.ModePost, category = Core.CategoryCloud, action = Core.ActionDownload, url = link)
		if self.success(): return self._addLink(category = Core.CategoryCloud, result = result, season = season, episode = episode)
		else: return self.addResult(error = Core.ErrorOffCloud)

	# Downloads the torrent, nzb, or any other container supported by Core.
	# If mode is not specified, tries to detect the file type automatically.
	def addContainer(self, link, title = None, season = None, episode = None):
		try:
			source = network.Container(link, download = True).information()
			if source['path'] == None and source['data'] == None: # Sometimes the NZB cannot be download, such as 404 errors.
				return self.addResult(error = Core.ErrorInaccessible)

			name = title
			if name == None:
				name = source['name']
				if name == None or name == '':
					name = source['hash']

			# Only needed for Premiumize, but also use here, in case they have the same problems.
			# Name must end in an extension, otherwise Premiumize throws an "unknown type" error for NZBs.
			if not name.endswith(source['extension']):
				name += source['extension']

			boundry = 'X-X-X'
			headers = {'Content-Type' : 'multipart/form-data; boundary=%s' % boundry}

			# Important: OffCloud requires new lines with \r\n, otherwise there are "unexpected errors".
			data = bytearray('--%s\r\n' % boundry, 'utf8')
			data += bytearray('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % name, 'utf8')
			data += bytearray('Content-Type: %s\r\n\r\n' % source['mime'], 'utf8')
			data += source['data']
			data += bytearray('\r\n--%s--\r\n' % boundry, 'utf8')

			result = self._retrieve(mode = Core.ModePost, category = Core.CategoryTorrent, action = Core.ActionUpload, httpData = data, httpHeaders = headers)
			if self.success(): return self.addCloud(link = result['url'], title = title, season = season, episode = episode)
			else: return self.addResult(error = Core.ErrorOffCloud)
		except:
			tools.Logger.error()
			return self.addResult(error = Core.ErrorOffCloud)

	def addHoster(self, link, category = CategoryInstant, season = None, episode = None, proxy = None):
		if category == Core.CategoryInstant:
			return self.addInstant(link = link, season = season, episode = episode, proxy = proxy)
		else:
			return self.addCloud(link = link, season = season, episode = episode)

	def addTorrent(self, link, title = None, season = None, episode = None):
		container = network.Container(link)
		source = container.information()
		if source['magnet']:
			return self.addCloud(link = container.torrentMagnet(title = title, encode = False), title = title, season = season, episode = episode)
		else:
			return self.addContainer(link = link, title = title, season = season, episode = episode)

	def addUsenet(self, link, title = None, season = None, episode = None):
		return self.addContainer(link = link, title = title, season = season, episode = episode)

	##############################################################################
	# DOWNLOADS
	##############################################################################

	def downloadInformation(self, category = None):
		items = self.items(category = category)
		if isinstance(items, list):
			from resources.lib.extensions import interface
			unknown = interface.Translation.string(33387)

			count = [0, 0]
			countBusy = [0, 0]
			countFinished = [0, 0]
			countFailed = [0, 0]
			countCanceled = [0, 0]
			size = [0, 0]
			sizeValue = [0, 0]
			sizeDescription = [unknown, unknown]

			for item in items:
				index = 0 if item['category'] == Core.CategoryInstant else 1
				status = item['status']
				try: size[index] += item['size']['bytes']
				except: pass
				count[index] += 1
				if status in [Core.StatusUnknown, Core.StatusError]:
					countFailed[index] += 1
				elif status in [Core.StatusCanceled]:
					countCanceled[index] += 1
				elif status in [Core.StatusFinished]:
					countFinished[index] += 1
				else:
					countBusy[index] += 1

			if not size[0] == 0:
				size[0] = convert.ConverterSize(value = size[0], unit = convert.ConverterSize.Byte)
				sizeValue[0] = size[0].value()
				sizeDescription[0] = size[0].stringOptimal()
			if not size[1] == 0:
				size[1] = convert.ConverterSize(value = size[1], unit = convert.ConverterSize.Byte)
				sizeValue[1] = size[1].value()
				sizeDescription[1] = size[1].stringOptimal()

			result = {
				'limits' : self.account()['limits']
			}
			if category == None or category == Core.CategoryInstant:
				result.update({
					'instant' : {
						'count' : {
							'total' : count[0],
							'busy' : countBusy[0],
							'finished' : countFinished[0],
							'canceled' : countCanceled[0],
							'failed' : countFailed[0],
						},
						'size' : {
							'bytes' : sizeValue[0],
							'description' : sizeDescription[0],
						},
					},
				})
			if category == None or category == Core.CategoryCloud:
				result.update({
					'cloud' : {
						'count' : {
							'total' : count[1],
							'busy' : countBusy[1],
							'finished' : countFinished[1],
							'canceled' : countCanceled[1],
							'failed' : countFailed[1],
						},
						'size' : {
							'bytes' : sizeValue[1],
							'description' : sizeDescription[1],
						},
					},
				})
			return result
		else:
			return Core.ErrorOffCloud

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent, Core.ModeUsenet}

	# id: single hash or list of hashes.
	def cachedIs(self, id, timeout = None):
		result = self.cached(id = id, timeout = timeout)
		if isinstance(result, dict): return result['cached']
		elif isinstance(result, list): return [i['cached'] for i in result]
		else: return False

	# id: single hash or list of hashes.
	# NB: a URL has a maximum length. Hence, a list of hashes cannot be too long, otherwise the request will fail.
	def cached(self, id, timeout = None, callback = None, sources = None):
		try:
			def segmentExtract(source):
				segment = None
				if segment is None:
					try: segment = source['segment']['first']
					except: pass
				if segment is None:
					try: segment = source['segment']['largest']
					except: pass
				if segment is None:
					try: segment = source['segment']['list'][0]
					except: pass
				return segment

			single = isinstance(id, basestring)
			if single: id = [id] # Must be passed in as a list.

			mode = Core.ModePost # Post can send more at a time.
			if mode == Core.ModePost:
				chunks = [sources[i:i + Core.LimitHashesPost] for i in xrange(0, len(sources), Core.LimitHashesPost)]
			else:
				chunks = [sources[i:i + Core.LimitHashesGet] for i in xrange(0, len(sources), Core.LimitHashesGet)]
			for chunk in chunks:
				for c in range(len(chunk)):
					chunk[c] = [chunk[c]['hash'].lower(), segmentExtract(chunk[c])]

			self.tCacheLock = threading.Lock()
			self.tCacheResult = []

			def cachedChunk(callback, mode, chunk, timeout):
				try:
					hashes = [c[0] for c in chunk if not c[0] is None]
					segments = [c[1] for c in chunk if not c[1] is None]
					offcloud = Core()
					result = offcloud._retrieve(mode = mode, category = Core.CategoryCache, hash = hashes, segment = segments, httpTimeout = timeout)
					if offcloud.success():
						cached = [i.lower() for i in result['cachedItems']]
						claimed = result['claimedItems'] if 'claimedItems' in result else None
						self.tCacheLock.acquire()
						self.tCacheResult.extend(result)
						self.tCacheLock.release()
						if callback:
							for c in chunk:
								try: callback(self.id(), c[0], c[0] in cached and (c[1] is None or claimed is None or not c[1] in claimed))
								except: pass
				except:
					tools.Logger.error()

			threads = []
			for chunk in chunks:
				thread = threading.Thread(target = cachedChunk, args = (callback, mode, chunk, timeout))
				threads.append(thread)
				thread.start()

			[i.join() for i in threads]
			if not callback:
				caches = []
				for source in sources:
					hash = sources['hash'].lower()
					segment = segmentExtract(sources)
					caches.append({'id' : hash, 'hash' : hash, 'cached' : hash in self.tCacheResult['cachedItems'] and (segment is None or self.tCacheResult['claimedItems'] is None or not segment in self.tCacheResult['claimedItems'])})
				if single: return caches[0] if len(caches) > 0 else False
				else: return caches
		except:
			tools.Logger.error()

	##############################################################################
	# ITEM
	##############################################################################

	def _itemStatus(self, status):
		status = status.lower()
		if status == 'downloading': return Core.StatusBusy
		elif status == 'downloaded': return Core.StatusFinished
		elif status == 'created': return Core.StatusInitialize
		elif status == 'processing': return Core.StatusFinalize
		elif status == 'error': return Core.StatusError
		elif status == 'queued': return Core.StatusQueued
		elif status == 'canceled': return Core.StatusCanceled
		elif status == 'fragile': return Core.StatusError
		else: return Core.StatusUnknown

	def _itemFile(self, link):
		name = link.split('/')[-1]
		try: extension = name.split('.')[-1]
		except: extension = None
		stream = tools.Video.extensionValid(extension)
		return {
			'link' : link,
			'name' : name,
			'extension' : extension,
			'stream' : stream,
		}

	# season, episode, transfer and files only for cloud.
	def item(self, category, id, season = None, episode = None, transfer = True, files = True):
		if category == Core.CategoryInstant:
			return self.itemInstant(id = id)
		elif category == Core.CategoryCloud:
			return self.itemCloud(id = id, season = season, episode = episode, transfer = transfer, files = files)
		else:
			return None

	def itemInstant(self, id):
		# Not supported by API.
		# Retrieve entier instant download list and pick the correct one from it.
		items = self.items(category = Core.CategoryInstant)
		for i in items:
			if i['id'] == id:
				return i
		return None

	# transfer requires an one API call.
	# files requires an one API call.
	def itemCloud(self, id, season = None, episode = None, transfer = True, files = True):
		try:
			self.tResulTransfer = None;
			self.tResulContent = None;

			def _itemTransfer(id):
				try: self.tResulTransfer = Core()._retrieve(mode = Core.ModePost, category = Core.CategoryCloud, action = Core.ActionStatus, requestId = id)['status']
				except: pass

			def _itemContent(id):
				try: self.tResulContent = Core()._retrieve(mode = Core.ModeGet, category = Core.CategoryCloud, action = Core.ActionExplore, requestId = id)
				except: pass

			threads = []
			if transfer: threads.append(threading.Thread(target = _itemTransfer, args = (id,)))
			if files: threads.append(threading.Thread(target = _itemContent, args = (id,)))
			[i.start() for i in threads]
			[i.join() for i in threads]

			result = {
				'id' : id,
				'category' : Core.CategoryCloud,
			}

			if self.tResulTransfer:
				status = self._itemStatus(self.tResulTransfer['status'])

				error = None
				try: error = self.tResulTransfer['errorMessage']
				except: pass

				directory = False
				try: directory = self.tResulTransfer['isDirectory']
				except: pass

				name = None
				try: name = self.tResulTransfer['fileName']
				except: pass

				server = None
				try: server = self.tResulTransfer['server']
				except: pass

				size = 0
				try: size = long(self.tResulTransfer['fileSize'])
				except: pass
				sizeObject = convert.ConverterSize(size)

				speed = 0
				try:
					speed = float(re.sub('[^0123456789\.]', '', self.tResulTransfer['downloadingSpeed']))
					speedObject = convert.ConverterSpeed(speed, unit = convert.ConverterSpeed.Byte)
				except:
					# Hoster links downloaded through the cloud.
					try:
						speed = self.tResulTransfer['info'].replace('-', '').strip()
						speedObject = convert.ConverterSpeed(speed)
						speed = speedObject.value(unit = convert.ConverterSpeed.Byte)
					except:
						speedObject = convert.ConverterSpeed(speed, unit = convert.ConverterSpeed.Byte)

				progressValueCompleted = 0
				progressValueRemaining = 0
				progressPercentageCompleted = 0
				progressPercentageRemaining = 0
				progressSizeCompleted = 0
				progressSizeRemaining = 0
				progressTimeCompleted = 0
				progressTimeRemaining = 0
				if status == Core.StatusFinished:
					progressValueCompleted = 1
					progressPercentageCompleted = 1
					progressSizeCompleted = size
				else:
					try:
						progressSizeCompleted = long(self.tResulTransfer['amount'])
						progressSizeRemaining = size - progressSizeCompleted

						progressValueCompleted = progressSizeCompleted / float(size)
						progressValueRemaining = 1 - progressValueCompleted

						progressPercentageCompleted = round(progressValueCompleted * 100, 1)
						progressPercentageRemaining = round(progressValueRemaining * 100, 1)

						progressTimeCompleted = long(self.tResulTransfer['downloadingTime']) / 1000
						progressTimeRemaining = long(progressSizeRemaining / float(speed))
					except:
						pass
				progressSizeCompletedObject = convert.ConverterSize(progressSizeCompleted)
				progressSizeRemainingObject = convert.ConverterSize(progressSizeRemaining)
				progressTimeCompletedObject = convert.ConverterDuration(progressTimeCompleted, convert.ConverterDuration.UnitSecond)
				progressTimeRemainingObject = convert.ConverterDuration(progressTimeRemaining, convert.ConverterDuration.UnitSecond)

				result.update({
					'name' : name,
					'server' : server,
					'status' : status,
					'error' : error,
					'directory' : directory,
					'size' : {
						'bytes' : sizeObject.value(),
						'description' : sizeObject.stringOptimal(),
					},
					'transfer' : {
						'speed' : {
							'bytes' : speedObject.value(convert.ConverterSpeed.Byte),
							'bits' : speedObject.value(convert.ConverterSpeed.Bit),
							'description' : speedObject.stringOptimal(),
						},
						'progress' : {
							'completed' : {
								'value' : progressValueCompleted,
								'percentage' : progressPercentageCompleted,
								'size' : {
									'bytes' : progressSizeCompletedObject.value(),
									'description' : progressSizeCompletedObject.stringOptimal(),
								},
								'time' : {
									'seconds' : progressTimeCompletedObject.value(convert.ConverterDuration.UnitSecond),
									'description' : progressTimeCompletedObject.string(convert.ConverterDuration.FormatDefault),
								},
							},
							'remaining' : {
								'value' : progressValueRemaining,
								'percentage' : progressPercentageRemaining,
								'size' : {
									'bytes' : progressSizeRemainingObject.value(),
									'description' : progressSizeRemainingObject.stringOptimal(),
								},
								'time' : {
									'seconds' : progressTimeRemainingObject.value(convert.ConverterDuration.UnitSecond),
									'description' : progressTimeRemainingObject.string(convert.ConverterDuration.FormatDefault),
								},

							},
						}
					},
				})

				# Cloud downloads with a single file have no way of returning the link.
				# cloud/history and cloud/status do not return the link, and cloud/explore returns "bad archive" for single files.
				# Construct the link manually.
				# This should be removed once OffCloud updates their API to fix this.
				if not self.tResulContent and not directory and status == Core.StatusFinished and not server == None and not server == '':
					self.tResulContent = ['https://%s.offcloud.com/cloud/download/%s/%s' % (server, id, urllib.quote_plus(name))]

			if self.tResulContent:
				video = None
				skip = ['trailer', 'sample', 'preview']
				files = []
				filesVideo = []
				filesMain = []
				filesSelection = []

				for i in self.tResulContent:
					file = self._itemFile(i)
					files.append(file)
					if file['stream']:
						filesVideo.append(file)
						if not any(s in file['name'].lower() for s in skip):
							filesMain.append(file)

				if len(filesMain) > 0: filesSelection = filesMain
				elif len(filesVideo) > 0: filesSelection = filesVideo
				elif len(files) > 0: filesSelection = files

				if season == None and episode == None:
					for i in filesSelection:
						if video == None or len(i['name']) > len(video['name']):
							video = i
				else:
					meta = metadata.Metadata()
					for i in filesSelection:
						# Somtimes the parent folder name contains part of the name and the actual file the other part.
						# Eg: Folder = "Better Call Saul Season 1", File "Part 1 - Episode Name"
						try: fullName = name + ' ' + i['name']
						except: fullName = i['name']
						if meta.episodeContains(title = fullName, season = season, episode = episode): video = i
					if video == None:
						for i in filesSelection:
							# Somtimes the parent folder name contains part of the name and the actual file the other part.
							# Eg: Folder = "Better Call Saul Season 1", File "Part 1 - Episode Name"
							try: fullName = name + ' ' + i['name']
							except: fullName = i['name']
							if meta.episodeContains(title = fullName, season = None, episode = episode, extra = True): video = i

				if video == None:
					if len(filesMain) > 0: video = filesMain[0]
					elif len(filesVideo) > 0: video = filesVideo[0]
					elif len(files) > 0: video = files[0]

				result.update({
					'files' : files,
					'video' : video,
				})

			self.tResulTransfer = None
			self.tResulContent = None

			return result
		except:
			tools.Logger.error()
		return None

	def itemsInstant(self):
		return self.items(category = Core.CategoryInstant)

	def itemsCloud(self):
		return self.items(category = Core.CategoryCloud)

	def items(self, category = None):
		try:
			if category == None:
				threads = []
				self.tResultItemsInstant = None
				self.tResultItemsCloud = None
				def _itemsInstant():
					self.tResultItemsInstant = Core().items(category = Core.CategoryInstant)
				def _itemsCloud():
					self.tResultItemsCloud = Core().items(category = Core.CategoryCloud)
				threads.append(threading.Thread(target = _itemsInstant))
				threads.append(threading.Thread(target = _itemsCloud))
				[i.start() for i in threads]
				[i.join() for i in threads]

				result = []
				if self.tResultItemsInstant: result += self.tResultItemsInstant
				if self.tResultItemsCloud: result += self.tResultItemsCloud
				self.tResultItemsInstant = None
				self.tResultItemsCloud = None
				return result
			else:
				items = []
				result = self._retrieve(mode = Core.ModeGet, category = category, action = Core.ActionHistory)
				for i in result:
					status = self._itemStatus(i['status'])
					video = None

					# Instant links always stay at created.
					if category == Core.CategoryInstant:
						if status == Core.StatusInitialize:
							status = Core.StatusFinished
						try: video = self._itemFile(i['downloadLink'])
						except: pass

					try: id = i['requestId']
					except: id = None
					try: name = i['fileName']
					except: name = None
					try: directory = i['isDirectory']
					except: directory = False
					try: server = i['server']
					except: server = None
					try: time = convert.ConverterTime(i['createdOn'], format = convert.ConverterTime.FormatDateTimeJson).timestamp()
					except: time = None
					try: metadata = i['metaData']
					except: metadata = None

					# Do not include hidden items with an error status. These are internal control items from Core.
					if not(status == Core.StatusError and metadata == 'hide'):
						items.append({
							'id' : id,
							'category' : category,
							'status' : status,
							'name' : name,
							'directory' : directory,
							'server' : server,
							'time' : time,
							'video' : video,
						})
				return items
		except:
			tools.Logger.error()
		return None

	##############################################################################
	# ID
	##############################################################################

	@classmethod
	def idItem(self, idOrLink):
		if network.Networker.linkIs(idOrLink):
			# Matches LAST occurance of a hash.
			# Instant links have both the user account hash and file hash in the link.
			id = re.search('[a-zA-Z0-9]{24}(?!.*[a-zA-Z0-9]{24})', idOrLink, re.IGNORECASE).group(0)
		else:
			return idOrLink

	##############################################################################
	# DELETE
	##############################################################################

	@classmethod
	def deletePossible(self, source):
		return True

	# id can be an ID or link.
	def delete(self, id, category = CategoryCloud, wait = True):
		def _delete(id, category):
			result = self._retrieve(mode = Core.ModeGet, category = category, action = Core.ActionRemove, requestId = id)
			if self.success(): return True
			else: return Core.ErrorOffCloud

		if category == None: category = Core.CategoryCloud
		id = self.idItem(id)
		if wait:
			return _delete(id, category)
		else:
			thread = threading.Thread(target = _delete, args = (id, category))
			thread.start()

	def deleteInstant(self, id):
		return self.delete(id = id, category = Core.CategoryInstant)

	def deleteCloud(self, id):
		return self.delete(id = id, category = Core.CategoryCloud)

	def deleteAll(self, category = None, wait = True):
		items = self.items(category = category)
		if isinstance(items, list):
			if len(items) > 0:
				def _deleteAll(category, id):
					Core().delete(category = category, id = id)
				threads = []
				for item in items:
					threads.append(threading.Thread(target = _deleteAll, args = (item['category'], item['id'])))

				# Complete the first thread in case the token has to be refreshed.
				threads[0].start()
				threads[0].join()

				for i in range(1, len(threads)):
					threads[i].start()
				if wait:
					for i in range(1, len(threads)):
						threads[i].join()
			return True
		else:
			return Core.ErrorOffCloud

	def deleteAllInstant(self, wait = True):
		return self.deleteAll(category = Core.CategoryInstant, wait = wait)

	def deleteAllCloud(self, wait = True):
		return self.deleteAll(category = Core.CategoryCloud, wait = wait)

	# Delete on launch
	def deleteLaunch(self):
		try:
			if tools.Settings.getBoolean('accounts.debrid.offcloud.removal'):
				option = tools.Settings.getInteger('accounts.debrid.offcloud.removal.launch')
				if option == 1:
					self.deleteAll(wait = False)
		except:
			pass

	# Delete on playback ended
	# id can be an ID or link.
	def deletePlayback(self, id, pack = None, category = None):
		try:
			if tools.Settings.getBoolean('accounts.debrid.offcloud.removal'):
				option = tools.Settings.getInteger('accounts.debrid.offcloud.removal.playback')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack):

					self.delete(id = id, category = category, wait = False)
		except:
			pass

	# Delete on failure
	# id can be an ID or link.
	def deleteFailure(self, id, pack = None, category = None):
		try:
			if tools.Settings.getBoolean('accounts.debrid.offcloud.removal'):
				option = tools.Settings.getInteger('accounts.debrid.offcloud.removal.failure')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack):
					self.delete(id = id, category = category, wait = False)
		except:
			pass
