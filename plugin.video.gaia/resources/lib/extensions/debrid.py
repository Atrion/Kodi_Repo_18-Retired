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
import os
import sys
import urllib
import urllib2
import urlparse
import time
import datetime
import hashlib
import math
import uuid
import copy
import threading

from resources.lib.modules import client

from resources.lib.externals.beautifulsoup import BeautifulSoup

from resources.lib.extensions import convert
from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import network
from resources.lib.extensions import clipboard
from resources.lib.extensions import metadata
from resources.lib.extensions import clipboard
from resources.lib.extensions import downloader

############################################################################################################################################################
# DEBRID
############################################################################################################################################################

DebridProgressDialog = None

class Debrid(object):

	Enabled = None

	# Modes
	ModeTorrent = 'torrent'
	ModeUsenet = 'usenet'
	ModeHoster = 'hoster'

	ErrorUnknown = 'unknown'
	ErrorUnavailable = 'unavailable'
	ErrorExternal = 'external'
	ErrorCancel = 'cancel'

	Exclusions = ('.txt', '.nfo', '.rtf', '.exe', '.zip', '.7z', '.rar', '.par', '.pdf', '.doc', '.docx', '.ini', '.lnk', '.csvs', '.xml', '.html', '.json', '.jpg', '.jpeg', '.png', '.tiff', '.gif', '.bmp', '.md5', '.sha')

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, name):
		self.mName = name
		self.mId = name.lower()

	##############################################################################
	# GENERAL
	##############################################################################

	def name(self):
		return self.mName

	def id(self):
		return self.mId

	##############################################################################
	# ENABLED
	##############################################################################

	@classmethod
	def enabled(self):
		if Debrid.Enabled is None: Debrid.Enabled = Premiumize().accountValid() or OffCloud().accountValid() or RealDebrid().accountValid() or AllDebrid().accountValid() or RapidPremium().accountValid()
		return Debrid.Enabled

	##############################################################################
	# ADD
	##############################################################################

	@classmethod
	def addError(self):
		return self.addResult(error = Debrid.ErrorUnknown)

	@classmethod
	def addResult(self, error = None, id = None, link = None, extra = None, notification = None, items = None):
		if error == None:
			# Link can be to an external Kodi addon.
			if not link or (not network.Networker.linkIs(link) and not link.startswith('plugin:')):
				error = Debrid.ErrorUnknown
		result = {
			'success' : (error == None),
			'error' : error,
			'id' : id,
			'link' : link,
			'items' : items,
			'notification' : notification,
		}
		if extra:
			for key, value in extra.iteritems():
				result[key] = value
		return result

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {}

	@classmethod
	def cachedAny(self, cache):
		for value in cache.itervalues():
			if value: return True
		return False

	# Virtual
	def cached(self, id, timeout = None, callback = None, sources = None):
		pass

	##############################################################################
	# STREAMING
	##############################################################################

	def streaming(self, mode):
		return tools.Settings.getBoolean('streaming.%s.enabled' % mode) and tools.Settings.getBoolean('streaming.%s.%s.enabled' % (mode, self.mId))

	def streamingTorrent(self):
		return self.streaming(Debrid.ModeTorrent)

	def streamingUsenet(self):
		return self.streaming(Debrid.ModeUsenet)

	def streamingHoster(self):
		return self.streaming(Debrid.ModeHoster)

############################################################################################################################################################
# PREMIUMIZE
############################################################################################################################################################

class Premiumize(Debrid):

	# Services
	ServicesUpdate = None
	Services = [
		{	'name' : 'Torrent',				'domain' : 'torrent',			'limit' : 0,	'factor' : 1	},
		{	'name' : 'Usenet',				'domain' : 'usenet',			'limit' : 0,	'factor' : 1	},
		{	'name' : 'VPN',					'domain' : 'vpn',				'limit' : 0,	'factor' : 1	},
		{	'name' : 'Cloud Storage',		'domain' : 'cloudstorage',		'limit' : 0,	'factor' : 1	},
		{	'name' : 'Cloud Downloads',		'domain' : 'clouddownloads',	'limit' : 0,	'factor' : 1	},
	]

	# Timeouts
	# Number of seconds the requests should be cached.
	TimeoutServices = 1 # 1 hour
	TimeoutAccount = 0.17 # 10 min

	# General
	Name = tools.System.name().upper()
	Prefix = '[' + Name + '] '

	# Usage - Maximum usage bytes and points
	UsageBytes = 1073741824000
	UsagePoints = 1000

	# Encryption
	# On SPMC (Python < 2.7.8), TLS encryption is not supported, which is required by Premiumize.
	# Force ecrypted connections on Python 2.7.8 and lower to be unencrypted.
	# Unencrypted connection on Premiumize need an http prefix/subdomain instead of www/api, otherwise it will automatically redirect to https.
	Encryption = tools.Settings.getBoolean('accounts.debrid.premiumize.encryption') and not sys.version_info < (2, 7, 9)

	Method = tools.Settings.getInteger('accounts.debrid.premiumize.method')
	MethodGet = Method == 2

	# Limits
	LimitLink = 2000 # Maximum length of a URL.
	LimitHashesGet = 40 # Maximum number of 40-character hashes to use in GET parameter so that the URL length limit is not exceeded.
	LimitHashesPost = 100 # Even when the hashes are send via POST, Premiumize seems to ignore the last ones (+- 1000 hashes). When too many hashes are sent at once (eg 500-900), if often causes a request timeout. Keep the limit small enough. Rather start multiple requests which should create multipel threads on the server.

	# Protocols
	ProtocolEncrypted = 'https'
	ProtocolUnencrypted = 'http'

	# Prefixes
	PrefixEncrypted = 'www'
	PrefixUnencrypted = 'http'

	#Links
	LinkMain = 'premiumize.me'
	LinkApi = 'premiumize.me/api/'

	# User Agent
	UserAgent = tools.System.name() + ' ' + tools.System.version()

	# Categories
	CategoryAccount = 'account'
	CategoryFolder = 'folder'
	CategoryTransfer = 'transfer'
	CategoryTorrent = 'torrent'
	CategoryCache = 'cache'
	CategoryServices = 'services'
	CategoryZip = 'zip'
	CategoryToken = 'token'
	CategoryDevice = 'device'

	# Actions
	ActionDownload = 'directdl'
	ActionInfo = 'info'
	ActionCreate = 'create'
	ActionList = 'list'
	ActionRename = 'rename'
	ActionPaste = 'paste'
	ActionDelete = 'delete'
	ActionBrowse = 'browse'
	ActionCheck = 'check'
	ActionCheckHashes = 'checkhashes'
	ActionClear = 'clearfinished'
	ActionGenerate = 'generate'
	ActionCode = 'code'

	# Parameters
	ParameterLogin = 'params[login]'
	ParameterPassword = 'params[pass]'
	ParameterLink = 'params[link]'
	ParameterMethod = 'method'
	ParameterCustomer = 'customer_id'
	ParameterPin = 'pin'
	ParameterId = 'id'
	ParameterParent = 'parent_id'
	ParameterName = 'name'
	ParameterItems = 'items'
	ParameterType = 'type'
	ParameterHash = 'hash'
	ParameterHashes = 'hashes[]'
	ParameterCaches = 'items[]'
	ParameterSource = 'src'
	ParameterItemId = 'items[0][id]'
	ParameterItemType = 'items[0][type]'
	ParameterClientId = 'client_id'
	ParameterClientSecret = 'client_secret'
	ParameterCode = 'code'
	ParameterGrantType = 'grant_type'
	ParameterResponseType = 'response_type'

	# Statuses
	StatusUnknown = 'unknown'
	StatusError = 'error'
	StatusTimeout = 'timeout'
	StatusQueued = 'queued'
	StatusBusy = 'busy'
	StatusFinalize = 'finalize'
	StatusFinished = 'finished'

	# Errors
	ErrorUnknown = 'unknown'
	ErrorAuthentication = 'authentication'
	ErrorInaccessible = 'inaccessible' # Eg: 404 error.
	ErrorTemporary = 'temporary' # Temporary errors
	ErrorPremium = 'premium' # Require premium account.
	ErrorPremiumize = 'premiumize' # Error from Premiumize server.
	ErrorSelection = 'selection' # No file selected from list of items.

	# Client
	ClientId = tools.System.obfuscate(tools.Settings.getString('internal.premiumize.client', raw = True))

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Debrid.__init__(self, 'Premiumize')

		self._accountAuthenticationClear()
		self.mAuthenticationToken = self.accountToken()

		self.mLinkBasic = None
		self.mLinkFull = None
		self.mParameters = None
		self.mSuccess = None
		self.mError = None
		self.mResult = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _parameter(self, parameter, parameters):
		if parameter in parameters:
			return parameters[parameter]
		else:
			return None

	def _link(self, protocol, prefix, link):
		return '%s://%s.%s' % (protocol, prefix, link)

	def _linkMain(self, encrypted = None):
		if encrypted == None: encrypted = Premiumize.Encryption
		if encrypted == True: return self._link(Premiumize.ProtocolEncrypted, Premiumize.PrefixEncrypted, Premiumize.LinkMain)
		else: return self._link(Premiumize.ProtocolUnencrypted, Premiumize.PrefixUnencrypted, Premiumize.LinkMain)

	def _linkApi(self, encrypted = None):
		if encrypted == None: encrypted = Premiumize.Encryption
		if encrypted == True: return self._link(Premiumize.ProtocolEncrypted, Premiumize.PrefixEncrypted, Premiumize.LinkApi)
		else: return self._link(Premiumize.ProtocolUnencrypted, Premiumize.PrefixUnencrypted, Premiumize.LinkApi)

	def _linkApiUnencrypted(self, link):
		if link.startswith(Premiumize.ProtocolEncrypted):
			return link.replace(Premiumize.ProtocolEncrypted, Premiumize.ProtocolUnencrypted, 1).replace(Premiumize.PrefixEncrypted, Premiumize.PrefixUnencrypted, 1)
		else:
			return None

	def _request(self, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None, httpAuthenticate = True, fallback = False):
		self.mResult = None

		linkOriginal = link
		parametersOriginal = parameters
		httpDataOriginal = httpData

		def redo(link, parameters, httpTimeout, httpData, httpHeaders, httpAuthenticate):
			# Premiumize's OAuth does not have a refresh token.
			# The access token is valid for 10 years.
			# In case this 10-year-limit is ever reached, simply inform the user to reauthenticate.
			interface.Dialog.notification(title = 35107, message = 35461, icon = interface.Dialog.IconError, time = 10000)
			return None

		try:
			self.mLinkBasic = link
			self.mParameters = parameters
			self.mSuccess = None
			self.mError = None

			# Use GET parameters for uploading files/containers (src parameter).
			if Premiumize.MethodGet or httpData:
				if parameters:
					if not link.endswith('?'):
						link += '?'
					parameters = urllib.urlencode(parameters, doseq = True)
					parameters = urllib.unquote(parameters) # Premiumize uses [] in the API links. Do not encode those and other URL characters.
					link += parameters
			else: # Use POST for all other requests.
				# List of values, eg: hashes[]
				# http://stackoverflow.com/questions/18201752/sending-multiple-values-for-one-name-urllib2
				if Premiumize.ParameterHashes in parameters:
					# If hashes are very long and if the customer ID and pin is appended to the end of the parameter string, Premiumize will ignore them and say there is no ID/pin.
					# Manually move the hashes to the back.
					hashes = {}
					hashes[Premiumize.ParameterHashes] = parameters[Premiumize.ParameterHashes]
					del parameters[Premiumize.ParameterHashes]
					httpData = urllib.urlencode(parameters, doseq = True) + '&' + urllib.urlencode(hashes, doseq = True)
				elif Premiumize.ParameterCaches in parameters:
					# If hashes are very long and if the customer ID and pin is appended to the end of the parameter string, Premiumize will ignore them and say there is no ID/pin.
					# Manually move the hashes to the back.
					links = {}
					links[Premiumize.ParameterCaches] = parameters[Premiumize.ParameterCaches]
					del parameters[Premiumize.ParameterCaches]
					httpData = urllib.urlencode(parameters, doseq = True) + '&' + urllib.urlencode(links, doseq = True)
				else:
					httpData = urllib.urlencode(parameters, doseq = True)

			# If the link is too long, reduce the size. The maximum URL size is 2000.
			# This occures if GET parameters are used instead of POST for checking a list of hashes.
			# If the user disbaled Premiumize encryption, the parameters MUST be send via GET, since Premiumize will ignore POST parameters on HTTP connections.
			if 'hashes[]=' in link:
				while len(link) > Premiumize.LimitLink:
					start = link.find('hashes[]=')
					end = link.find('&', start)
					link = link[:start] + link[end + 1:]

			self.mLinkFull = link

			if httpData: request = urllib2.Request(link, data = httpData)
			else: request = urllib2.Request(link)

			request.add_header('User-Agent', Premiumize.UserAgent)
			if httpHeaders:
				for key in httpHeaders:
					request.add_header(key, httpHeaders[key])

			if not httpTimeout:
				if httpData: httpTimeout = 60
				else: httpTimeout = 30

			response = urllib2.urlopen(request, timeout = httpTimeout)
			result = response.read()
			response.close()
			self.mResult = tools.Converter.jsonFrom(result)

			self.mSuccess = self._success(self.mResult)
			self.mError = self._error(self.mResult)
			if not self.mSuccess:
				if self.mError == 'bad_token' and httpAuthenticate:
					return redo(link = linkOriginal, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate, fallback = fallback)
				else:
					self._requestErrors('The call to the Premiumize API failed', link, httpData, self.mResult, exception = False)

		except (urllib2.HTTPError, urllib2.URLError) as error:
			self.mSuccess = False
			if hasattr(error, 'code'):
				errorCode = error.code
				errorString = ' ' + str(errorCode)
			else:
				errorCode = 0
				errorString = ''
			self.mError = 'Premiumize Unreachable [HTTP/URL Error%s]' % errorString
			if httpAuthenticate: self._requestErrors(self.mError, link, httpData, self.mResult)
			try:
				errorApi = tools.Converter.jsonFrom(error.read())
				self.mErrorCode = errorApi['error_code']
				self.mErrorDescription = errorApi['error']
			except: pass
			if self.mErrorDescription == 'bad_token' or errorCode == 401:
				return redo(link = linkOriginal, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate, fallback = fallback)
			elif not fallback:
				newLink = self._linkApiUnencrypted(linkOriginal)
				if not newLink == None:
					tools.Logger.log('Retrying the encrypted link over an unencrypted connection: ' + str(newLink))
					return self._request(link = newLink, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate, fallback = True)
		except:
			self.mSuccess = False
			self.mError = 'Unknown Error'
			self._requestErrors(self.mError, link, httpData, self.mResult)
		return self.mResult

	def _requestErrors(self, message, link, payload, result = None, exception = True):
		# While downloading, do not add to log.
		if not result == None and 'message' in result and result['message'] == 'Download is not finished yet.':
			return

		link = str(link)
		payload = str(payload) if len(str(payload)) < 300 else 'Payload too large to display'
		result = str(result)
		tools.Logger.error(str(message) + (': Link [%s] Payload [%s] Result [%s]' % (link, payload, result)), exception = exception)

	def _requestAuthentication(self, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None):
		if not parameters:
			parameters = {}
		if not httpHeaders:
			httpHeaders = {}
		httpHeaders['Authorization'] = 'Bearer %s' % self.mAuthenticationToken
		return self._request(link = link, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders)


	# Retrieve from the API
	# Parameters:
	#	category: CategoryFolder, CategoryTransfer, CategoryTorrent
	#	action: ActionCreate, ActionList, ActionRename, ActionPaste, ActionDelete, ActionBrowse, ActionCheckHashes, ActionClear
	#	remainder: individual parameters for the actions. hash can be single or list.
	def _retrieve(self, category, action, id = None, parent = None, name = None, items = None, caches = None, type = None, source = None, hash = None, itemId = None, itemType = None, httpTimeout = None, httpData = None, httpHeaders = None):
		link = self._linkApi()
		link = network.Networker.linkJoin(link, category, action)

		parameters = {}
		if not id == None: parameters[Premiumize.ParameterId] = id
		if not parent == None: parameters[Premiumize.ParameterParent] = parent
		if not name == None: parameters[Premiumize.ParameterName] = name
		if not items == None: parameters[Premiumize.ParameterItems] = items
		if not type == None: parameters[Premiumize.ParameterType] = type
		if not source == None: parameters[Premiumize.ParameterSource] = source
		if not itemId == None: parameters[Premiumize.ParameterItemId] = itemId
		if not itemType == None: parameters[Premiumize.ParameterItemType] = itemType
		if not caches == None: parameters[Premiumize.ParameterCaches] = caches
		if not hash == None:
			# NB: Always make the hashes lower case. Sometimes Premiumize cannot find the hash if it is upper case.
			if isinstance(hash, basestring):
				parameters[Premiumize.ParameterHash] = hash.lower()
			else:
				for i in range(len(hash)):
					hash[i] = hash[i].lower()
				parameters[Premiumize.ParameterHashes] = hash

		return self._requestAuthentication(link = link, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders)

	def _success(self, result):
		try: return ('status' in result and result['status'].lower() == 'success') or (not 'status' in result and not 'error' in result) or (isinstance(result, list) and len(result) > 0)
		except: return False

	def _error(self, result):
		return result['message'] if 'message' in result else None

	def _errorType(self):
		try:
			error = self.mError.lower()
			if 'try again' in error: return Premiumize.ErrorTemporary
			elif 'premium membership' in error: return Premiumize.ErrorPremium
			elif 'not logged in' in error: return Premiumize.ErrorAuthentication
			else: return Premiumize.ErrorPremiumize
		except:
			return Premiumize.ErrorPremiumize

	##############################################################################
	# INITIALIZE
	##############################################################################

	# Initialize Premiumize account (if set in settings).
	# If not called, Premiumize links will fail in the sources.

	def initialize(self):
		thread = threading.Thread(target = self._initialize)
		thread.start()

	def _initialize(self):
		b = 'base64'
		def notify():
			apiKey = 'V1c5MUlHRnlaU0IxYzJsdVp5QmhiaUIxYm1GMWRHaHZjbWw2WldRZ2RtVnljMmx2YmlCdlppQjBhR1VnYjNKcFoybHVZV3dnWVdSa2IyNGdSMkZwWVM0Z1ZHaHBjeUIyWlhKemFXOXVJRzltSUhSb1pTQmhaR1J2YmlCM2FXeHNJRzV2ZENCM2IzSnJJR0Z6SUdsdWRHVnVaR1ZrTGlCSlppQjViM1VnY0dGcFpDQm1iM0lnZEdocGN5QmhaR1J2YmlCdmNpQjBhR1VnYldWa2FXRWdZbTk0SUdsMElHTmhiV1VnYjI0c0lIbHZkU0JuYjNRZ1cwSmRjMk55WlhkbFpDQnZkbVZ5V3k5Q1hTNGdSMkZwWVNCM2FXeHNJR0ZzZDJGNWN5QmlaU0JtY21WbExpQlFiR1ZoYzJVZ1pHOTNibXh2WVdRZ2RHaGxJRzl5YVdkcGJtRnNJSFpsY25OcGIyNGdiMllnZEdobElHRmtaRzl1SUdaeWIyMDZXME5TWFZ0Q1hWdERUMHhQVWlCemEzbGliSFZsWFdoMGRIQnpPaTh2WjJGcFlXdHZaR2t1WTI5dFd5OURUMHhQVWwxYkwwSmQ='
			apiKey = apiKey.decode(b).decode(b)
			if apiKey: # If API key is invalid, notify the user so that a new key can be entered in the settings.
				interface.Dialog.closeAll()
				import random
				tools.Time.sleep(random.randint(10, 15))
				interface.Dialog.confirm(apiKey)
		try:
			n = tools.System.info(('Ym1GdFpRPT0=').decode(b).decode(b))
			a = tools.System.info(('WVhWMGFHOXk=').decode(b).decode(b))
			l = tools.Settings.getString(('WWtkc2RXRjVOWGRqYlZaMFlWaFdkR0ZZY0d3PQ==').decode(b).decode(b).decode(b), raw = True)

			xn = not ord(n[0]) == 71 or not ord(n[2]) == 105
			xa = not ord(a[1]) == 97 or not ord(a[3]) == 97
			xl = not ('V2pKR2NGbFhkSFphUjJ0MVdUSTVkQT09').decode(b).decode(b).decode(b) in l
			if xn or xa or xl: notify()
		except:
			notify()

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
		link = tools.Settings.getString('link.premiumize', raw = True)
		if open: tools.System.openLink(link)
		return link

	@classmethod
	def vpn(self, open = False):
		link = tools.Settings.getString('link.premiumize.vpn', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def _accountAuthenticationClear(self):
		self.mAuthenticationLink = None
		self.mAuthenticationUser = None
		self.mAuthenticationDevice = None
		self.mAuthenticationInterval = None
		self.mAuthenticationToken = None
		self.mAuthenticationUsername = None

	def _accountAuthenticationSettings(self):
		token = '' if self.mAuthenticationToken == None else self.mAuthenticationToken
		authentication = ''
		if not self.mAuthenticationToken == None:
			if self.mAuthenticationUsername == None or self.mAuthenticationUsername == '':
				authentication = interface.Format.FontPassword
			else:
				authentication = self.mAuthenticationUsername
		tools.Settings.set('accounts.debrid.premiumize.token', token)
		tools.Settings.set('accounts.debrid.premiumize.auth', authentication)

	def accountAuthenticationLink(self):
		return self.mAuthenticationLink

	def accountAuthenticationCode(self):
		return self.mAuthenticationUser

	def accountAuthenticationInterval(self):
		return self.mAuthenticationInterval

	def accountAuthenticationReset(self, save = True):
		self._accountAuthenticationClear()
		if save: self._accountAuthenticationSettings()

	def accountAuthenticationStart(self):
		self._accountAuthenticationClear()

		try:
			link = network.Networker.linkJoin(self._linkMain(), Premiumize.CategoryToken)
			parameters = {
				Premiumize.ParameterClientId : Premiumize.ClientId,
				Premiumize.ParameterResponseType : 'device_code'
			}

			result = self._request(link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)

			self.mAuthenticationLink = result['verification_uri']
			self.mAuthenticationUser = result['user_code']
			self.mAuthenticationDevice = result['device_code']
			self.mAuthenticationInterval = result['interval']

			return True
		except:
			tools.Logger.error()

		return False

	def accountAuthenticationWait(self):
		try:
			link = network.Networker.linkJoin(self._linkMain(), Premiumize.CategoryToken)
			parameters = {
				Premiumize.ParameterClientId : Premiumize.ClientId,
				Premiumize.ParameterGrantType: 'device_code',
				Premiumize.ParameterCode : self.mAuthenticationDevice
			}
			result = self._request(link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)
			if 'access_token' in result:
				self.mAuthenticationToken = result['access_token']
				self._accountAuthenticationSettings()
				return True
		except:
			pass
		return False

	def accountAuthenticationFinish(self):
		try:
			self.mAuthenticationUsername = self.account(cache = False)['user']
			self._accountAuthenticationSettings()
			return True
		except:
			pass
		return False

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.premiumize.enabled')

	def accountValid(self):
		return not self.accountToken() == ''

	def accountToken(self):
		return tools.Settings.getString('accounts.debrid.premiumize.token') if self.accountEnabled() else ''

	def accountVerify(self):
		return not self.account(cache = False) == None

	def account(self, cache = True):
		try:
			if self.accountValid():
				timeout = Premiumize.TimeoutAccount if cache else 0
				def __premiumizeAccount(): # Must have a different name than the tools.Cache.cache call for the hoster list. Otherwise the cache returns the result for the hosters instead of the account.
					return self._retrieve(category = Premiumize.CategoryAccount, action = Premiumize.ActionInfo)
				result = tools.Cache.cache(__premiumizeAccount, timeout)
				if 'status' in result and result['status'] == 401: # Login failed. The user might have entered the incorrect details which are still stuck in the cache. Force a reload.
					result = tools.Cache.cache(__premiumizeAccount, 0)

				expirationDate = datetime.datetime.fromtimestamp(result['premium_until'])

				return {
					'user' : result['customer_id'],
			 		'expiration' : {
						'timestamp' : result['premium_until'],
						'date' : expirationDate.strftime('%Y-%m-%d %H:%M:%S'),
						'remaining' : (expirationDate - datetime.datetime.today()).days
					},
					'usage' : {
						'consumed' : {
							'value' : float(result['limit_used']),
							'points' : int(math.floor(float(result['space_used']) / 1073741824.0)),
							'percentage' : round(float(result['limit_used']) * 100.0, 1),
							'size' : {
								'bytes' : result['space_used'],
								'description' : convert.ConverterSize(float(result['space_used'])).stringOptimal(),
							},
							'description' : '%.0f%%' % round(float(result['limit_used']) * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
						},
						'remaining' : {
							'value' : 1 - float(result['limit_used']),
							'points' : int(Premiumize.UsagePoints - math.floor(float(result['space_used']) / 1073741824.0)),
							'percentage' : round((1 - float(result['limit_used'])) * 100.0, 1),
							'size' : {
								'bytes' : Premiumize.UsageBytes - float(result['space_used']),
								'description' : convert.ConverterSize(Premiumize.UsageBytes - float(result['space_used'])).stringOptimal(),
							},
							'description' : '%.0f%%' % round(round((1 - float(result['limit_used'])) * 100.0, 0)), # Must round, otherwise 2.5% changes to 2% instead of 3%.
						}
					}
				}
			else:
				return None
		except:
			return None

	##############################################################################
	# SERVICES
	##############################################################################

	def _serviceFactor(self, factor):
		return str(factor) + 'x'

	def _service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		if nameOrDomain == 'premiumize': nameOrDomain = 'clouddownloads'
		for service in Premiumize.Services:
			if service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain or ('domains' in service and nameOrDomain in [i.lower() for i in service['domains']]):
				return service
		return None

	def services(self, cache = True, onlyEnabled = False):
		# Even thow ServicesUpdate is a class variable, it will be destrcucted if there are no more Premiumize instances.
		if Premiumize.ServicesUpdate == None:
			Premiumize.ServicesUpdate = []

			streamingTorrent = self.streamingTorrent()
			streamingUsenet = self.streamingUsenet()
			streamingHoster = self.streamingHoster()

			try:
				timeout = Premiumize.TimeoutServices if cache else 0
				def __premiumizeHosters():# Must have a different name than the tools.Cache.cache call for the account details. Otherwise the cache returns the result for the account instead of the hosters.
					return self._retrieve(category = Premiumize.CategoryServices, action = Premiumize.ActionList)
				result = tools.Cache.cache(__premiumizeHosters, timeout)
				if 'status' in result and result['status'] == 401: # Login failed. The user might have entered the incorrect details which are still stuck in the cache. Force a reload.
					result = tools.Cache.cache(__premiumizeHosters, 0)

				aliases = result['aliases']

				factors = result['fairusefactor']
				for key, value in factors.iteritems():
					name = key.lower()
					try: name = name[:name.find('.')]
					except: pass
					name = re.sub('\W+', '', name).capitalize()
					Premiumize.Services.append({'name' : name, 'domain' : key, 'factor' : value})

				# Cache cannot add new direct downloads, but only retrieves existing files in cache.
				# https://blog.premiumize.me/old-api-phaseout-new-api-changes-and-best-practices-for-the-cache/
				'''hosters = {}
				for i in result['directdl']:
					if not i in hosters: hosters[i] = {'direct' : False, 'cache' : False}
					hosters[i]['direct'] = True
				for i in result['cache']:
					if not i in hosters: hosters[i] = {'direct' : False, 'cache' : False}
					hosters[i]['cache'] = True
				for key, value in hosters.iteritems():'''

				for key in result['directdl']:
					host = {}
					host['id'] = key.lower()
					host['enabled'] = streamingHoster

					service = self._service(key)

					if service:
						host['name'] = service['name']
						host['domain'] = service['domain']
						host['domains'] = aliases[service['domain']] if service['domain'] in aliases else [service['domain']]
						host['usage'] = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					else:
						name = key
						index = name.find('.')
						if index >= 0:
							name = name[:index]
						host['name'] = name.title()
						host['domain'] = key
						host['domains'] = aliases[key] if key in aliases else [key]
						host['usage'] = {'factor' : {'value' : 0, 'description' : self._serviceFactor(0)}}

					Premiumize.ServicesUpdate.append(host)

				service = self._service('torrent')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : streamingTorrent, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Premiumize.ServicesUpdate.append(host)

				service = self._service('usenet')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : streamingUsenet, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Premiumize.ServicesUpdate.append(host)

				service = self._service('vpn')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : True, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Premiumize.ServicesUpdate.append(host)

				service = self._service('cloudsstorage')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : True, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Premiumize.ServicesUpdate.append(host)

				service = self._service('clouddownloads')
				if service:
					usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
					host = {'id' : service['name'].lower(), 'enabled' : True, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
					Premiumize.ServicesUpdate.append(host)

			except:
				tools.Logger.error()

		if onlyEnabled:
			return [i for i in Premiumize.ServicesUpdate if i['enabled']]
		else:
			return Premiumize.ServicesUpdate

	def servicesList(self, onlyEnabled = False):
		services = self.services(onlyEnabled = onlyEnabled)
		result = [service['id'] for service in services]
		for service in services:
			if 'domain' in service:
				result.append(service['domain'])
			if 'domains' in service:
				result.extend(service['domains'])
		return list(set(result))

	def service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		if nameOrDomain == 'premiumize': nameOrDomain = 'clouddownloads'
		for service in self.services():
			if service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain or ('domains' in service and nameOrDomain in [i.lower() for i in service['domains']]):
				return service
		return None

	##############################################################################
	# DELETE
	##############################################################################

	# Check if the file can be deleted.
	@classmethod
	def deletePossible(self, source):
		from resources.lib.extensions import handler
		source = source.lower()
		return source == handler.Handler.TypeTorrent or source == handler.Handler.TypeUsenet or source == handler.HandlePremiumize().id()

	# Delete single transfer
	def deleteTransfer(self, id):
		if id: # When using directdl, there is no file in the account and therefore no ID to delete.
			self._retrieve(category = Premiumize.CategoryTransfer, action = Premiumize.ActionDelete, id = id)
			return self.success()
		return False

	# Delete all completed transfers
	def deleteFinished(self):
		self._retrieve(category = Premiumize.CategoryTransfer, action = Premiumize.ActionClear)
		return self.success()

	# Delete all transfers
	def deleteTransfers(self, wait = True):
		try:
			# First clear finished all-at-once, then one-by-one the running downloads.
			self.deleteFinished()
			items = self._itemsTransfer()
			if len(items) > 0:
				def _delete(id):
					Premiumize().deleteTransfer(id)
				threads = []
				for item in items:
					threads.append(threading.Thread(target = _delete, args = (item['id'],)))
				[i.start() for i in threads]
				if wait: [i.join() for i in threads]
			return True
		except:
			return False

	# Delete single item
	def deleteItem(self, id):
		try:
			if id:
				self._retrieve(category = Premiumize.CategoryFolder, action = Premiumize.ActionDelete, id = id)
				return self.success()
		except:
			tools.Logger.error()
		return False

	# Delete all items
	def deleteItems(self, wait = True):
		try:
			items = self._retrieve(category = Premiumize.CategoryFolder, action = Premiumize.ActionList)
			items = items['content']
			if len(items) > 0:
				def _delete(id):
					Premiumize().deleteItem(id)
				threads = []
				for item in items:
					threads.append(threading.Thread(target = _delete, args = (item['id'],)))
				[i.start() for i in threads]
				if wait: [i.join() for i in threads]
			return True
		except:
			return False

	# Delete all items and transfers
	def deleteAll(self, wait = True):
		thread1 = threading.Thread(target = self.deleteTransfers)
		thread2 = threading.Thread(target = self.deleteItems)
		thread1.start()
		thread2.start()
		if wait:
			thread1.join()
			thread2.join()
		return True

	def _deleteSingle(self, id):
		# Deleteing the transfer also deletes the corresponding folder in "My Files".
		'''
		thread1 = threading.Thread(target = self.deleteItem, args = (id,))
		thread2 = threading.Thread(target = self.deleteTransfer, args = (id,))
		thread1.start()
		thread2.start()
		thread1.join()
		thread2.join()
		return True
		'''
		return self.deleteTransfer(id)

	# Delete an item and its corresponding transfer based on the link or hash.
	def deleteSingle(self, id, wait = True):
		thread = threading.Thread(target = self._deleteSingle, args = (id,))
		thread.start()
		if wait: thread.join()
		return True

	# Delete on launch
	def deleteLaunch(self):
		try:
			if tools.Settings.getBoolean('accounts.debrid.premiumize.removal'):
				option = tools.Settings.getInteger('accounts.debrid.premiumize.removal.launch')
				if option == 1:
					self.deleteAll(wait = False)
		except:
			pass

	# Delete on playback ended
	def deletePlayback(self, id, pack = None):
		try:
			if tools.Settings.getBoolean('accounts.debrid.premiumize.removal'):
				option = tools.Settings.getInteger('accounts.debrid.premiumize.removal.playback')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack):
					self.deleteSingle(id, wait = False)
		except:
			pass

	# Delete on failure
	def deleteFailure(self, id, pack = None):
		try:
			if tools.Settings.getBoolean('accounts.debrid.premiumize.removal'):
				option = tools.Settings.getInteger('accounts.debrid.premiumize.removal.failure')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack):
					self.deleteSingle(id, wait = False)
		except:
			pass

	##############################################################################
	# ADD
	##############################################################################

	# Gets the Premiumize link from the previously added download.
	def _addLink(self, result = None, id = None, season = None, episode = None, pack = False):
		link = None
		items = None
		error = None
		success = False
		if result and 'location' in result and network.Networker.linkIs(result['location']):
			link = result['location']
			success = True
		elif result and 'content' in result:
			try:
				link = self._itemLargest(files = result['content'], season = season, episode = episode)['link']
				success = network.Networker.linkIs(link)
			except: pass
		if pack or (not success and id):
			try:
				items = self._item(idTransfer = id, season = season, episode = episode, data = result)
				link = items['video']['link']
			except:
				error = self._errorType()
		return self.addResult(error = error, id = id, link = link, items = items)

	def add(self, link, title = None, season = None, episode = None, pack = False, source = None, cached = False, cloud = False):
		if source == network.Container.TypeTorrent:
			type = network.Container.TypeTorrent
		elif source == network.Container.TypeUsenet:
			type = network.Container.TypeUsenet
		else:
			type = network.Container(link).type()

		if type == network.Container.TypeTorrent:
			return self.addTorrent(link = link, title = title, season = season, episode = episode, pack = pack, cached = cached, cloud = cloud)
		elif type == network.Container.TypeUsenet:
			return self.addUsenet(link = link, title = title, season = season, episode = episode, pack = pack, cached = cached, cloud = cloud)
		else:
			return self.addHoster(link = link, season = season, episode = episode, pack = pack, cached = cached)

	# Downloads the torrent, nzb, or any other container supported by Premiumize.
	# If mode is not specified, tries to detect the file type autoamtically.
	def addContainer(self, link, title = None, season = None, episode = None, pack = False):
		try:
			# https://github.com/tknorris/plugin.video.premiumize/blob/master/local_lib/premiumize_api.py
			source = network.Container(link).information()
			if source['path'] == None and source['data'] == None: # Sometimes the NZB cannot be download, such as 404 errors.
				return self.addResult(error = Premiumize.ErrorInaccessible)

			if title == None:
				title = source['name']
				if title == None or title == '':
					title = source['hash']

			# Name must end in an extension, otherwise Premiumize throws an "unknown type" error for NZBs.
			# Premiumize says this is fixed now. No extension has to be send.
			# However, keeps this here in case of future changes. It doesn't hurt to send the extension.
			if not title.endswith(source['extension']):
				title += source['extension']

			boundry = 'X-X-X'
			headers = {'Content-Type' : 'multipart/form-data; boundary=%s' % boundry}

			data = bytearray('--%s\n' % boundry, 'utf8')
			data += bytearray('Content-Disposition: form-data; name="src"; filename="%s"\n' % title, 'utf8')
			data += bytearray('Content-Type: %s\n\n' % source['mime'], 'utf8')
			data += source['data']
			data += bytearray('\n--%s--\n' % boundry, 'utf8')

			result = self._retrieve(category = Premiumize.CategoryTransfer, action = Premiumize.ActionCreate, httpData = data, httpHeaders = headers)

			# Returns an API error if already on download list. However, the returned ID should be used.
			try: return self._addLink(id = result['id'], season = season, episode = episode)
			except: return self.addResult(error = self._errorType())
		except:
			tools.Logger.error()
			return self.addResult(error = self._errorType())

	def addHoster(self, link, season = None, episode = None, pack = False, cached = False):
		result = self._retrieve(category = Premiumize.CategoryTransfer, action = Premiumize.ActionDownload, source = link)
		if self.success(): return self._addLink(result = result, season = season, episode = episode, pack = pack)
		else: return self.addResult(error = self._errorType())

	def addTorrent(self, link, title = None, season = None, episode = None, pack = False, cached = False, cloud = False):
		container = network.Container(link)
		source = container.information()
		if source['magnet']:
			if cached and not cloud:
				result = self._retrieve(category = Premiumize.CategoryTransfer, action = Premiumize.ActionDownload, source = container.torrentMagnet(title = title, encode = False))
				if self.success(): return self._addLink(result = result, season = season, episode = episode, pack = pack)
			result = self._retrieve(category = Premiumize.CategoryTransfer, action = Premiumize.ActionCreate, source = container.torrentMagnet(title = title, encode = False)) # Do not encode again, already done by _request().
			# Returns an API error if already on download list. However, the returned ID should be used.
			try: return self._addLink(id = result['id'], season = season, episode = episode, pack = pack)
			except: return self.addResult(error = self._errorType())
		else:
			if cached:
				result = self._retrieve(category = Premiumize.CategoryTransfer, action = Premiumize.ActionDownload, source = link)
				if self.success(): return self._addLink(result = result, season = season, episode = episode, pack = pack)
			# NB: Torrent files can also be added by link to Premiumize. Although this is a bit faster, there is no guarantee that Premiumize will be able to download the torrent file remotley.
			return self.addContainer(link = link, title = title, season = season, episode = episode, pack = pack)

	def addUsenet(self, link, title = None, season = None, episode = None, pack = False, cached = False, cloud = False):
		if cached and not cloud:
			result = self._retrieve(category = Premiumize.CategoryTransfer, action = Premiumize.ActionDownload, source = link)
			if self.success(): return self._addLink(result = result, season = season, episode = episode)
		return self.addContainer(link = link, title = title, season = season, episode = episode, pack = pack)

	##############################################################################
	# ITEMS
	##############################################################################

	def itemId(self, link):
		try: return re.search('dl\/([^\/]*)', link, re.IGNORECASE).group(1)
		except: return None

	def _itemStatus(self, status, message = None):
		if not message == None:
			if 'download finished. copying the data' in message:
				return Premiumize.StatusFinalize
			elif 'downloading at' in message:
				return Premiumize.StatusBusy

		status = status.lower()
		if any(state == status for state in ['error', 'fail', 'failure']):
			return Premiumize.StatusError
		elif any(state == status for state in ['timeout', 'time']):
			return Premiumize.StatusTimeout
		elif any(state == status for state in ['queued', 'queue']):
			return Premiumize.StatusQueued
		elif any(state == status for state in ['waiting', 'wait', 'running', 'busy']):
			return Premiumize.StatusBusy
		elif any(state == status for state in ['finished', 'finish', 'seeding', 'seed', 'success']):
			return Premiumize.StatusFinished
		else:
			return Premiumize.StatusUnknown

	def _itemSeeding(self, status, message = None):
		status = status.lower()
		if any(state == status for state in ['seeding', 'seed']):
			return True
		if not message == None and 'seeding' in message:
			return True
		return False

	def _itemSeedingRatio(self, message):
		try:
			indexStart = message.find('ratio of ')
			if indexStart > 0:
				indexStart += 9
				indexEnd = message.find('. ', indexStart)
				if indexEnd > 0: return float(message[indexStart:indexEnd])
				else: return float(message[indexStart:])
		except:
			pass
		return 0

	def _itemName(self, name):
		if name.startswith(Premiumize.Prefix):
			name = name[len(Premiumize.Prefix):]
		return name

	def _itemSize(self, size = None, message = None):
		if (size == None or size <= 0) and not message == None:
			start = message.find('% of ')
			if start < 0:
				size = 0
			else:
				end = message.find('finished.', start)
				if end < 0:
					size = 0
				else:
					size = message[start : end].upper() # Must be made upper, because otherwise it is seen as bits instead of bytes.
					size = convert.ConverterSize(size).value()
		return int(size)

	def _itemSpeed(self, message):
		speed = 0
		try:
			if not message == None:
				start = message.find('downloading at ')
				if start >= 0:
					end = message.find('/s', start)
					if end >= 0:
						end += 2
					else:
						end = message.find('s.', start)
						if end >= 0: end += 1
					if end >= 0:
						speed = convert.ConverterSpeed(message[start : end]).value()
		except:
			pass
		return int(speed)

	def _itemPeers(self, message):
		peers = 0
		try:
			if not message == None:
				start = message.find('from ')
				if start >= 0:
					start += 5
					end = message.find(' peers', start)
					if end >= 0: peers = int(message[start : end].strip())
		except:
			pass
		return peers

	def _itemTime(self, time = None, message = None):
		try:
			if (time == None or time <= 0) and not message == None:
				start = message.find('eta is ')
				if start < 0:
					time = 0
				else:
					message = message[start + 7:]
					parts = message.split(':')
					message = '%02d:%02d:%02d' % (int(parts[0]), int(parts[1]), int(parts[2]))
					time = convert.ConverterDuration(message).value(convert.ConverterDuration.UnitSecond)
			if time == None: time = 0
			return int(time)
		except:
			return 0

	def _itemTransfer(self, id):
		return self._itemsTransfer(id = id)

	def _items(self): # Used by Premiumize provider.
		items = []
		result = self._retrieve(category = Premiumize.CategoryFolder, action = Premiumize.ActionList)
		if self.success() and 'content' in result:
			parentId = result['parent_id'] if 'parent_id' in result else None
			parentName = result['name'] if 'name' in result else None
			content = result['content']
			for i in content:
				type = i['type']
				if type == 'file':
					file = self._itemAddFile(item = i, parentId = parentId, parentName = parentName)
					file['type'] = type
					items.append(file)
				else:
					items.append({
						'id' : i['id'],
						'name' : i['name'],
						'type' : type,
						'parent':
						{
							'id' : parentId,
							'name' : parentName,
						},
					})
		return items

	def _itemsTransfer(self, id = None):
		items = []
		results = self._retrieve(category = Premiumize.CategoryTransfer, action = Premiumize.ActionList)
		if self.success() and 'transfers' in results:
			results = results['transfers']
			for result in results:
				item = {}
				message = result['message'] if 'message' in result else None
				if not message == None:
					message = message.lower()

				# ID
				if 'id' in result and not result['id'] == None:
					idCurrent = result['id']
				else:
					idCurrent = None
				item['id'] = idCurrent

				# If you add a download multiple times, they will show multiple times in the list. Only add one instance.
				found = False
				for i in items:
					if i['id'] == idCurrent:
						found = True
						break
				if found: continue

				# Target
				if 'target_folder_id' in result and not result['target_folder_id'] == None:
					target = result['target_folder_id']
				else:
					target = None
				item['target'] = target

				# Folder
				if 'folder_id' in result and not result['folder_id'] == None:
					folder = result['folder_id']
				else:
					folder = None
				item['folder'] = folder

				# File
				if 'file_id' in result and not result['file_id'] == None:
					file = result['file_id']
				else:
					file = None
				item['file'] = file

				# Name
				if 'name' in result and not result['name'] == None:
					name = self._itemName(result['name'])
				else:
					name = None
				item['name'] = name

				# Size
				size = 0
				if ('size' in result and not result['size'] == None) or (not message == None):
					try: sizeValue = result['size']
					except: sizeValue = None
					size = self._itemSize(size = sizeValue, message = message)
				size = convert.ConverterSize(size)
				item['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}

				# Status
				if 'status' in result and not result['status'] == None:
					status = self._itemStatus(result['status'], message)
				else:
					status = None
				item['status'] = status

				# Error
				if status == Premiumize.StatusError:
					error = None
					if message:
						if 'retention' in message:
							error = 'Out of server retention'
						elif 'missing' in message:
							error = 'The transfer job went missing'
						elif 'password' in message:
							error = 'The file is password protected'
						elif 'repair' in message:
							error = 'The file is unrepairable'

					item['error'] = error

				# Transfer
				transfer = {}

				# Transfer - Speed
				speed = {}
				speedDownload = self._itemSpeed(message)
				speedConverter = convert.ConverterSpeed(speedDownload)
				speed['bytes'] = speedConverter.value(convert.ConverterSpeed.Byte)
				speed['bits'] = speedConverter.value(convert.ConverterSpeed.Bit)
				speed['description'] = speedConverter.stringOptimal()
				transfer['speed'] = speed

				# Transfer - Torrent
				torrent = {}
				if 'status' in result and not result['status'] == None:
					seeding = self._itemSeeding(status = result['status'], message = message)
				else:
					seeding = False
				torrent['seeding'] = seeding
				torrent['peers'] = self._itemPeers(message)
				torrent['seeders'] = result['seeder'] if 'seeder' in result else 0
				torrent['leechers'] = result['leecher'] if 'leecher' in result else 0
				torrent['ratio'] = result['ratio'] if 'ratio' in result and result['ratio'] > 0 else self._itemSeedingRatio(message = message)
				transfer['torrent'] = torrent

				# Transfer - Progress
				if ('progress' in result and not result['progress'] == None) or ('eta' in result and not result['eta'] == None):
					progress = {}

					progressValueCompleted = 0
					progressValueRemaining = 0
					if 'progress' in result and not result['progress'] == None:
						progressValueCompleted = float(result['progress'])
					if progressValueCompleted == 0 and 'status' in item and item['status'] == Premiumize.StatusFinished:
						progressValueCompleted = 1
					progressValueRemaining = 1 - progressValueCompleted

					progressPercentageCompleted = round(progressValueCompleted * 100, 1)
					progressPercentageRemaining = round(progressValueRemaining * 100, 1)

					progressSizeCompleted = 0
					progressSizeRemaining = 0
					if 'size' in item:
						progressSizeCompleted = int(progressValueCompleted * item['size']['bytes'])
						progressSizeRemaining = int(item['size']['bytes'] - progressSizeCompleted)

					progressTimeCompleted = 0
					progressTimeRemaining = 0
					time = result['eta'] if 'eta' in result else None
					progressTimeRemaining = self._itemTime(time, message)

					completed = {}
					size = convert.ConverterSize(progressSizeCompleted)
					time = convert.ConverterDuration(progressTimeCompleted, convert.ConverterDuration.UnitSecond)
					completed['value'] = progressValueCompleted
					completed['percentage'] = progressPercentageCompleted
					completed['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}
					completed['time'] = {'seconds' : time.value(convert.ConverterDuration.UnitSecond), 'description' : time.string(convert.ConverterDuration.FormatDefault)}

					remaining = {}
					size = convert.ConverterSize(progressSizeRemaining)
					time = convert.ConverterDuration(progressTimeRemaining, convert.ConverterDuration.UnitSecond)
					remaining['value'] = progressValueRemaining
					remaining['percentage'] = progressPercentageRemaining
					remaining['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}
					remaining['time'] = {'seconds' : time.value(convert.ConverterDuration.UnitSecond), 'description' : time.string(convert.ConverterDuration.FormatDefault)}

					progress['completed'] = completed
					progress['remaining'] = remaining
					transfer['progress'] = progress

				# Transfer
				item['transfer'] = transfer

				if id and idCurrent == id:
					return item

				# Append
				items.append(item)

		if id: return items[0]
		else: return items

	def _itemIsStream(self, name, extension, status):
		if status == 'good_as_is':
			return True
		else:
			if not extension == None:
				extension = extension.lower()
				if any(e == extension for e in tools.Video.extensions()):
					return True
			if not name == None:
				name = name.lower()
				if any(name.endswith('.' + e) for e in tools.Video.extensions()):
					return True
		return False

	def _itemAddDirectory(self, items, parentId = None, parentName = None, recursive = True):
		files = []
		try:
			for item in items:
				if recursive and 'type' in item and item['type'] == 'folder':
					result = self._retrieve(category = Premiumize.CategoryFolder, action = Premiumize.ActionList, id = item['id'])
					parentId = item['id'] if 'id' in item else parentId
					parentName = item['name'] if 'name' in item else parentName
					if self.success() and 'content' in result:
						result = result['content']
						sub = self._itemAddDirectory(items = result, parentId = parentId, parentName = parentName, recursive = recursive)
						files.extend(sub)
				elif not 'type' in item or item['type'] == 'file':
					sub = self._itemAddFile(item, parentId = parentId, parentName = parentName)
					files.append(sub)
		except:
			tools.Logger.error()
		return files

	def _itemAddFile(self, item, parentId, parentName):
		try:
			if 'type' in item and item['type'] == 'folder':
				return None

			result = {}

			result['id'] = item['id'] if 'id' in item else None
			result['name'] = item['name'] if 'name' in item else None
			result['time'] = item['created_at'] if 'created_at' in item else None
			result['extension'] = item['ext'] if 'ext' in item else None
			result['link'] = item['link'] if 'link' in item else None
			if not result['name'] and 'path' in item:
				path = item['path']
				index = path.rfind('/')
				if index >= 0: path = path[index + 1:]
				result['name'] = path

			if 'size' in item and not item['size'] == None:
				size = item['size']
			size = convert.ConverterSize(size)
			result['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}

			result['extension'] = None
			if not result['extension'] and result['name']:
				try:
					root, extension = os.path.splitext(result['name'])
					if extension.startswith('.'): extension = extension[1:]
					result['extension'] = extension
				except:
					pass
			if not result['extension'] and result['link']:
				try:
					extension = urlparse.urlparse(result['link'])
					root, extension = os.path.splitext(extension.path)
					if extension.startswith('.'): extension = extension[1:]
					result['extension'] = extension
				except:
					pass

			status = item['transcode_status'] if 'transcode_status' in item else None
			result['stream'] = self._itemIsStream(name = result['name'], extension = result['extension'], status = status)

			result['parent'] = {
				'id' : parentId,
				'name' : parentName,
			}

			return result
		except:
			tools.Logger.error()

	def _itemLargest(self, files, season = None, episode = None, valid = True):
		largest = None
		try:
			if not season == None and not episode == None:
				meta = metadata.Metadata()
				for file in files:
					# Somtimes the parent folder name contains part of the name and the actual file the other part.
					# Eg: Folder = "Better Call Saul Season 1", File "Part 1 - Episode Name"
					try: name = file['parent']['name'] + ' ' + file['name']
					except:
						try: name = file['name']
						except: name = file['path'].replace('/', ' ')

					if meta.episodeContains(title = name, season = season, episode = episode):
						try: sizeCurrent = file['size']['bytes']
						except: sizeCurrent = file['size']
						try: sizeLargest = largest['size']['bytes']
						except:
							try: sizeLargest = largest['size']
							except: sizeLargest = 0
						try: streamIs = file['stream']
						except: streamIs = 'stream_link' in file and (file['stream_link'] or not valid)
						if streamIs and (largest == None or sizeCurrent > sizeLargest):
							largest = file

			if largest == None:
				for file in files:
					try: sizeCurrent = file['size']['bytes']
					except: sizeCurrent = file['size']
					try: sizeLargest = largest['size']['bytes']
					except:
						try: sizeLargest = largest['size']
						except: sizeLargest = 0
					try: streamIs = file['stream']
					except: streamIs = 'stream_link' in file and (file['stream_link'] or not valid)
					if streamIs and (largest == None or sizeCurrent > sizeLargest):
						largest = file

			# If transcoding fails on Premiumize's server, stream_link is None.
			# Try again without checking the value of stream_link.
			if largest == None and valid:
				largest = self._itemLargest(files = files, season = season, episode = episode, valid = False)
		except:
			tools.Logger.error()
		return largest

	def _item(self, idTransfer = None, idFolder = None, idFile = None, season = None, episode = None, data = None):
		try:
			if data == None:
				if idTransfer:
					result = self._itemTransfer(id = idTransfer)
					if result:
						idFolder = result['folder']
						idFile = result['file']
					else:
						return None
				if not idFolder and not idFile:
					return None

			item = {}
			if data == None: result = self._retrieve(category = Premiumize.CategoryFolder, action = Premiumize.ActionList, id = idFolder)
			else: result = data
			if (self.success() or not data == None) and 'content' in result:
				content = result['content']
				if idFile:
					for file in content:
						if file['id'] == idFile:
							content = file
							break
					parentId = idFolder
					parentName = result['name'] if 'name' in result else None
					files = [self._itemAddFile(item = content, parentId = parentId, parentName = parentName)]
				else:
					parentId = result['parent_id'] if 'parent_id' in result else None
					parentName = result['name'] if 'name' in result else None
					files = self._itemAddDirectory(items = content, recursive = True, parentId = parentId, parentName = parentName)

				largest = self._itemLargest(files = files, season = season, episode = episode)

				size = 0
				for file in files:
					size += file['size']['bytes']
				size = convert.ConverterSize(size)

				item['name'] = parentName
				item['files'] = files
				item['count'] = len(files)
				item['video'] = largest
				item['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}

			return item
		except:
			tools.Logger.error()

	# Determines if two Premiumize links point to the same file.
	# Cached Premiumize items always return a different link containing a random string, which actually points to the same file.
	# Must be updated in downloader.py as well.
	@classmethod
	def itemEqual(self, link1, link2):
		domain = 'energycdn.com'
		index1 = link1.find(domain)
		index2 = link2.find(domain)
		if index1 >= 0 and index2 >= 0:
			items1 = link1[index1:].split('/')
			items2 = link2[index2:].split('/')
			if len(items1) >= 8 and len(items2) >= 8:
				return items1[-1] == items2[-1] and items1[-2] == items2[-2] and items1[-3] == items2[-3]
		return False

	# Retrieve the info of a single file.
	# content: retrieves the finished file into (My Files)
	# season/episode: filters for specific episode in season pack.
	def item(self, idTransfer = None, idFolder = None, idFile = None, content = True, season = None, episode = None):
		try:
			if idTransfer == None:
				transfer = None
			else:
				transfer = self._itemsTransfer(id = idTransfer)
				for i in transfer:
					if (not idFolder == None and i['folder'] == idFolder) or (not idFile == None and i['file'] == idFile):
						transfer = i
						break
				try:
					idFolder = transfer['folder']
					idFile = transfer['file']
				except:
					pass

			item = self._item(idFolder = idFolder, idFile = idFile, season = season, episode = episode)

			result = None
			if not transfer == None and not item == None:
				result = dict(transfer.items() + item.items()) # Only updates values if non-exisitng. Updates from back to front.
			elif not transfer == None:
				result = transfer
			if result == None: # Not elif.
				result = item

			return result
		except:
			tools.Logger.error()

	##############################################################################
	# DOWNLOADS
	##############################################################################

	def zip(self, id):
		result = self._retrieve(category = Premiumize.CategoryZip, action = Premiumize.ActionGenerate, itemId = id, itemType = 'folder')
		if self.success():
			return result['location']
		else:
			return None

	##############################################################################
	# DOWNLOADS
	##############################################################################

	def downloadInformation(self):
		items = self._itemsTransfer()
		if isinstance(items, list):
			count = len(items)
			countBusy = 0
			countFinished = 0
			countFailed = 0
			size = 0
			for item in items:
				size += item['size']['bytes']
				status = item['status']
				if status in [Premiumize.StatusUnknown, Premiumize.StatusError, Premiumize.StatusTimeout]:
					countFailed += 1
				elif status in [Premiumize.StatusFinished]:
					countFinished += 1
				else:
					countBusy += 1
			size = convert.ConverterSize(value = size, unit = convert.ConverterSize.Byte)

			return {
				'count' : {
					'total' : count,
					'busy' : countBusy,
					'finished' : countFinished,
					'failed' : countFailed,
				},
				'size' : {
					'bytes' : size.value(),
					'description' : size.stringOptimal()
				},
				'usage' : self.account()['usage']
			}
		else:
			return Premiumize.ErrorPremiumize

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {Debrid.ModeHoster, Debrid.ModeTorrent, Debrid.ModeUsenet}

	# id: single hash or list of hashes.
	def cachedIs(self, id, timeout = None):
		result = self.cached(id = id, timeout = timeout)
		if isinstance(result, dict): return result['cached']
		elif isinstance(result, list): return [i['cached'] for i in result]
		else: return result

	# id: single hash or list of hashes.
	def cached(self, id, timeout = None, callback = None, sources = None):
		single = isinstance(id, basestring)
		if single: id = [id] # Must be passed in as a list.

		torrents = []
		hosters = []

		for i in id:
			if network.Networker.linkIs(i): hosters.append(i)
			else: torrents.append(i)

		premiumizeTorrent = Premiumize()
		threadTorrent = threading.Thread(target = premiumizeTorrent.cachedTorrent, args = (torrents, timeout, callback, sources))

		premiumizeHoster = Premiumize()
		threadHoster = threading.Thread(target = premiumizeHoster.cachedHoster, args = (hosters, timeout, callback, sources))

		threadTorrent.start()
		threadHoster.start()

		threadTorrent.join()
		threadHoster.join()

		if not callback:
			caches = []
			for key, value in self.tCacheResult.iteritems():
				key = key.lower()
				caches.append({'id' : key, 'hash' : key, 'cached' : value['status'] == 'finished'})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches

	# id: single hash or list of hashes.
	def cachedUsenet(self, id, timeout = None, callback = None, sources = None):
		return self._cachedCheck(False, id = id, timeout = timeout, callback = callback, sources = sources)

	# id: single hash or list of hashes.
	def cachedTorrent(self, id, timeout = None, callback = None, sources = None):
		return self._cachedCheck(False, id = id, timeout = timeout, callback = callback, sources = sources)

	# id: single hash or list of hashes.
	def cachedHoster(self, id, timeout = None, callback = None, sources = None):
		return self._cachedCheck(True, id = id, timeout = timeout, callback = callback, sources = sources)

	# id: single hash or list of hashes.
	def _cachedCheck(self, hoster, id, timeout = None, callback = None, sources = None):
		single = isinstance(id, basestring)
		if single: id = [id] # Must be passed in as a list.

		# If the encryption setting is disabled, request must happen over GET, since Premiumize ignores POST parameters over HTTP.
		# A URL has a maximum length, so the hashes have to be split into parts and processes sequentially, in order not to exceed the URL limit.
		if Premiumize.Encryption:
			chunks = [id[i:i + Premiumize.LimitHashesPost] for i in xrange(0, len(id), Premiumize.LimitHashesPost)]
		else:
			limit = int(Premiumize.LimitHashesGet / 2) if hoster else Premiumize.LimitHashesGet # Links are noramlly longer than hashes.
			chunks = [id[i:i + limit] for i in xrange(0, len(id), limit)]

		self.tCacheLock = threading.Lock()
		self.tCacheResult = {}

		def cachedChunkTorrent(callback, hashes, timeout):
			premiumize = Premiumize()
			result = premiumize._retrieve(category = Premiumize.CategoryTorrent, action = Premiumize.ActionCheckHashes, hash = hashes, httpTimeout = timeout)
			if premiumize.success():
				result = result['hashes']
				self.tCacheLock.acquire()
				self.tCacheResult.update(result)
				self.tCacheLock.release()
				if callback:
					for key, value in result.iteritems():
						try: callback(self.id(), key, value['status'] == 'finished')
						except: pass

		def cachedChunkHoster(callback, links, timeout):
			premiumize = Premiumize()
			result = premiumize._retrieve(category = Premiumize.CategoryCache, action = Premiumize.ActionCheck, caches = links, httpTimeout = timeout)
			if premiumize.success():
				result = result['response']
				response = {}
				for i in range(len(result)):
					response[links[i]] = result[i]
				self.tCacheLock.acquire()
				self.tCacheResult.update(response)
				self.tCacheLock.release()
				if callback:
					for key, value in response.iteritems():
						try: callback(self.id(), key, value)
						except: pass

		threads = []
		for chunk in chunks:
			if hoster: thread = threading.Thread(target = cachedChunkHoster, args = (callback, chunk, timeout))
			else: thread = threading.Thread(target = cachedChunkTorrent, args = (callback, chunk, timeout))
			threads.append(thread)
			thread.start()

		[i.join() for i in threads]
		if not callback:
			caches = []
			for key, value in self.tCacheResult.iteritems():
				key = key.lower()
				caches.append({'id' : key, 'hash' : key, 'cached' : value['status'] == 'finished'})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches

class PremiumizeInterface(object):

	Name = 'Premiumize'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		self.mDebrid = Premiumize()

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self):
		interface.Loader.show()
		valid = False
		title = PremiumizeInterface.Name + ' ' + interface.Translation.string(33339)
		if self.mDebrid.accountEnabled():
			account = self.mDebrid.account(cache = False)
			if account:
				valid = interface.Translation.string(33341) if self.mDebrid.accountValid() else interface.Translation.string(33342)
				user = account['user']

				date = account['expiration']['date']
				days = str(account['expiration']['remaining'])

				percentage = str(account['usage']['consumed']['percentage']) + '%'

				pointsUsed = account['usage']['consumed']['points']
				pointsTotal = account['usage']['consumed']['points'] + account['usage']['remaining']['points']
				points = str(pointsUsed) + ' ' + interface.Translation.string(33073) + ' ' + str(pointsTotal)

				storageUsed = account['usage']['consumed']['size']['description']
				storageTotal = convert.ConverterSize(account['usage']['consumed']['size']['bytes'] + account['usage']['remaining']['size']['bytes']).stringOptimal()
				storage = storageUsed + ' ' + interface.Translation.string(33073) + ' ' + storageTotal

				items = []

				# Information
				items.append(interface.Format.font(interface.Translation.string(33344), bold = True, uppercase = True))
				items.append(interface.Format.font(interface.Translation.string(33340) + ': ', bold = True) + valid)
				items.append(interface.Format.font(interface.Translation.string(32303) + ': ', bold = True) + user)

				# Expiration
				items.append('')
				items.append(interface.Format.font(interface.Translation.string(33345), bold = True, uppercase = True))
				items.append(interface.Format.font(interface.Translation.string(33346) + ': ', bold = True) + date)
				items.append(interface.Format.font(interface.Translation.string(33347) + ': ', bold = True) + days)

				# Usage
				items.append('')
				items.append(interface.Format.font(interface.Translation.string(33228), bold = True, uppercase = True))
				items.append(interface.Format.font(interface.Translation.string(33348) + ': ', bold = True) + percentage)
				items.append(interface.Format.font(interface.Translation.string(33349) + ': ', bold = True) + points)
				items.append(interface.Format.font(interface.Translation.string(33350) + ': ', bold = True) + storage)

				# Dialog
				interface.Loader.hide()
				interface.Dialog.options(title = title, items = items)
			else:
				interface.Loader.hide()
				interface.Dialog.confirm(title = title, message = interface.Translation.string(33352) % PremiumizeInterface.Name)
		else:
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33351) % PremiumizeInterface.Name)

		return valid

	def accountAuthentication(self, openSettings = True):
		interface.Loader.show()
		try:
			if self.mDebrid.accountValid():
				if interface.Dialog.option(title = PremiumizeInterface.Name, message = 33492):
					self.mDebrid.accountAuthenticationReset(save = False)
				else:
					return None

			self.mDebrid.accountAuthenticationStart()

			# Link and token on top for skins that don't scroll text in a progress dialog.
			message = ''
			message += interface.Format.fontBold(interface.Translation.string(33381) + ': ' + self.mDebrid.accountAuthenticationLink())
			message += interface.Format.newline()
			message += interface.Format.fontBold(interface.Translation.string(33495) + ': ' + self.mDebrid.accountAuthenticationCode())
			message += interface.Format.newline() + interface.Translation.string(33494) + ' ' + interface.Translation.string(33978)

			clipboard.Clipboard.copy(self.mDebrid.accountAuthenticationCode())
			progressDialog = interface.Dialog.progress(title = PremiumizeInterface.Name, message = message, background = False)

			interval = self.mDebrid.accountAuthenticationInterval()
			timeout = 3600
			synchronized = False

			for i in range(timeout):
				try:
					try: canceled = progressDialog.iscanceled()
					except: canceled = False
					if canceled: break
					progressDialog.update(int((i / float(timeout)) * 100))

					if not float(i) % interval == 0:
						raise Exception()
					tools.Time.sleep(1)

					if self.mDebrid.accountAuthenticationWait():
						synchronized = True
						break
				except:
					pass

			try: progressDialog.close()
			except: pass

			if synchronized:
				if self.mDebrid.accountAuthenticationFinish():
					interface.Dialog.notification(title = 33566, message = 35462, icon = interface.Dialog.IconSuccess)
			else:
				self.mDebrid.accountAuthenticationReset(save = True) # Make sure the values are reset if the waiting dialog is canceled.
		except:
			pass
		if openSettings:
			tools.Settings.launch(category = tools.Settings.CategoryAccounts)
		interface.Loader.hide()

	##############################################################################
	# CLEAR
	##############################################################################

	def clear(self):
		title = PremiumizeInterface.Name + ' ' + interface.Translation.string(33013)
		message = 'Do you want to clear your Premiumize downloads and delete all your files from the server?'
		if interface.Dialog.option(title = title, message = message):
			interface.Loader.show()
			self.mDebrid.deleteAll()
			interface.Loader.hide()
			message = 'Premiumize Downloads Cleared'
			interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconSuccess)

	##############################################################################
	# ADD
	##############################################################################

	def addManual(self):
		result = None
		title = 35082
		items = [
			interface.Format.bold(interface.Translation.string(35076) + ': ') + interface.Translation.string(35077),
			interface.Format.bold(interface.Translation.string(33381) + ': ') + interface.Translation.string(35078),
			interface.Format.bold(interface.Translation.string(33380) + ': ') + interface.Translation.string(35079),
		]
		choice = interface.Dialog.select(title = title, items = items)

		if choice >= 0:
			link = None
			if choice == 0 or choice == 1:
				link = interface.Dialog.input(title = title, type = interface.Dialog.InputAlphabetic)
			elif choice == 2:
				link = interface.Dialog.browse(title = title, type = interface.Dialog.BrowseFile, multiple = False, mask = ['torrent', 'nzb'])

			if not link == None and not link == '':
				interface.Dialog.notification(title = 35070, message = 35071, icon = interface.Dialog.IconSuccess)
				interface.Loader.show()
				result = self.add(link)
				if result['success']:
					interface.Dialog.closeAllProgress()
					choice = interface.Dialog.option(title = 35073, message = 35074)
					if choice: interface.Player.playNow(result['link'])

		interface.Loader.hide()
		return result

	# season/episode: Filter out the correct file from a season pack.
	def add(self, link, title = None, season = None, episode = None, pack = False, close = True, source = None, cached = False, select = False, cloud = False):
		result = self.mDebrid.add(link = link, title = title, season = season, episode = episode, pack = pack, source = source, cached = cached, cloud = cloud)
		if select: result = self._addSelect(result)
		if result['success']:
			return result
		elif result['id']:
			return self._addLink(result, season = season, episode = episode, close = close, pack = pack, select = select)
		elif result['error'] == Premiumize.ErrorInaccessible:
			title = 'Stream Error'
			message = 'Stream Is Inaccessible'
		elif result['error'] == Premiumize.ErrorPremiumize:
			title = 'Stream Error'
			message = 'Failed To Add Stream To Premiumize'
		elif result['error'] == Premiumize.ErrorAuthentication:
			title = 'Stream Error'
			message = 'Premiumize Authentication Failed'
		elif result['error'] == Premiumize.ErrorPremium:
			title = 'Stream Error'
			message = 'Premiumize Premium Membership Required'
		elif result['error'] == Premiumize.ErrorTemporary:
			title = 'Stream Error'
			message = 'Temporary Premiumize Error'
		elif result['error'] == Premiumize.ErrorSelection:
			title = 'Selection Error'
			message = 'No File Selected'
		else:
			tools.Logger.errorCustom('Unexpected Premiumize Error: ' + str(result))
			title = 'Stream Error'
			message = 'Stream File Unavailable'
		self._addError(title = title, message = message)
		result['notification'] = True
		return result

	def _addSelect(self, result):
		try:
			if not result: return result
			items = [i for i in result['items']['files'] if i['name'] and not i['name'].endswith(Debrid.Exclusions)]
			items = sorted(items, key = lambda x : x['name'])
			choice = interface.Dialog.options(title = 35542, items = [i['name'] for i in items])
			if choice < 0:
				result['success'] = False
				result['error'] = Premiumize.ErrorSelection
			else:
				result['items']['video'] = items[choice]
				result['link'] = items[choice]['link']
		except:
			tools.Logger.error()
		return result

	def _addDelete(self, id, notification = False):
		def __addDelete(id, notification):
			result = self.mDebrid.deleteTransfer(id = id)
			if notification:
				if result == True:
					interface.Dialog.notification(title = 'Deletion Success', message = 'Download Deleted From List', icon = interface.Dialog.IconSuccess)
				else:
					interface.Dialog.notification(title = 'Deletion Failure', message = 'Download Not Deleted From List', icon = interface.Dialog.IconError)
		thread = threading.Thread(target = __addDelete, args = (id, notification))
		thread.start()

	def _addAction(self, result):
		items = []
		items.append(interface.Format.font(interface.Translation.string(33077) + ': ', bold = True) + interface.Translation.string(33078))
		items.append(interface.Format.font(interface.Translation.string(33079) + ': ', bold = True) + interface.Translation.string(33080))
		items.append(interface.Format.font(interface.Translation.string(33083) + ': ', bold = True) + interface.Translation.string(33084))

		interface.Core.close()
		tools.Time.sleep(0.1) # Ensures progress dialog is closed, otherwise shows flickering.
		choice = interface.Dialog.options(title = 33076, items = items)

		if choice == -1:
			return False
		elif choice == 0:
			return True
		elif choice == 1:
			return False
		elif choice == 2:
			self._addDelete(id = result['id'], notification = True)
			return False

	def _addError(self, title, message, delay = True):
		interface.Loader.hide() # Make sure hided from sources __init__.py
		interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconError)
		if delay: tools.Time.sleep(2) # Otherwise the message disappears to quickley when another notification is shown afterwards.

	def _addErrorDetermine(self, item, api = False, pack = False):
		error = False
		status = item['status'] if 'status' in item else None
		if status == Premiumize.StatusError:
			title = 'Download Error'
			message = None
			if item['error']:
				message = item['error']
			if message == None:
				message = 'Download Failure With Unknown Error'
			self._addError(title = title, message = message)
			error = True
		elif status == Premiumize.StatusTimeout:
			title = 'Download Timeout'
			message = 'Download Timeout Failure'
			self._addError(title = title, message = message)
			error = True
		elif api:
			if not 'video' in item or item['video'] == None:
				title = 'Invalid Stream'
				if pack: message = 'No Episode In Season Pack'
				else: message = 'No Playable Stream Found'
				self._addError(title = title, message = message)
				error = False # Do not return True, since it won't have a video stream while still downloading.

		if error:
			try:
				self.mDebrid.deleteFailure(id = item['id'], pack = pack)
			except: pass

		return error

	def _addLink(self, result, season = None, episode = None, close = True, pack = False, select = False):
		self.tActionCanceled = False
		unknown = 'Unknown'
		id = result['id']

		# In case the progress dialog was canceled while transfering torrent data.
		if interface.Core.canceled():
			self._addDelete(id = id, notification = False)
			return self.mDebrid.addResult(error = Debrid.ErrorCancel)

		self.tLink =  ''
		item = self.mDebrid.item(idTransfer = id, content = True, season = season, episode = episode)
		if select: item = self._addSelect(item)
		if item:
			try:
				self.tLink = item['video']['link']
				if self.tLink: return self.mDebrid.addResult(id = id, link = self.tLink)
			except: pass
			try: percentage = item['transfer']['progress']['completed']['percentage']
			except: percentage = 0
			status = item['status']
			if self._addErrorDetermine(item, pack = pack):
				pass
			elif status == Premiumize.StatusQueued or Premiumize.StatusBusy or status == Premiumize.StatusFinalize:
				title = 'Premiumize Download'
				descriptionWaiting = interface.Format.fontBold('Waiting For Download Start') + '%s'
				descriptionFinalize = interface.Format.fontBold('Finalizing Download') + '%s'

				interface.Loader.hide() # Make sure hided from sources __init__.py

				self.timer = tools.Time(start = True)
				self.timerShort = False
				self.timerLong = False

				def updateProgress(id, percentage, close):
					while True:
						background = interface.Core.background()
						interface.Core.create(type = interface.Core.TypeDownload, title = title, message = descriptionWaiting)
						interface.Core.update(progress = int(percentage), title = title, message = descriptionWaiting)
						try:
							status = Premiumize.StatusQueued
							seconds = None
							counter = 0
							item = self.mDebrid.item(idTransfer = id, content = True, season = season, episode = episode)
							if select: item = self._addSelect(item)
							while True:
								if counter == 10: # Only make an API request every 5 seconds.
									item = self.mDebrid.item(idTransfer = id, content = True, season = season, episode = episode)
									if select: item = self._addSelect(item)
									counter = 0
								counter += 1

								status = item['status'] if 'status' in item else None
								try:
									self.tLink = item['video']['link']
									if self.tLink: return
								except: pass
								if not status == Premiumize.StatusQueued and not status == Premiumize.StatusBusy and not status == Premiumize.StatusFinalize:
									close = True
									self._addErrorDetermine(item, api = True, pack = pack)
									break

								waiting = item['transfer']['speed']['bytes'] == 0 and item['size']['bytes'] == 0 and item['transfer']['progress']['completed']['value'] == 0 and item['transfer']['progress']['completed']['time']['seconds'] == 0

								if status == Premiumize.StatusFinalize:
									interface.Core.update(progress = 0, title = title, message = descriptionFinalize)
								elif waiting:
									interface.Core.update(progress = 0, title = title, message = descriptionWaiting)
								else:
									percentageNew = item['transfer']['progress']['completed']['percentage']
									# If Premiumize looses the connection in the middle of the download, the progress goes back to 0, causing the dialog to close. Avoid this by keeping track of the last progress.
									if percentageNew >= percentage:
										percentage = percentageNew
										description = ''
										speed = item['transfer']['speed']['description']
										speedBytes = item['transfer']['speed']['bytes']
										size = item['size']['description']
										sizeBytes = item['size']['bytes']
										sizeCompleted = item['transfer']['progress']['completed']['size']['description']
										seconds = item['transfer']['progress']['remaining']['time']['seconds']
										if seconds == 0:
											eta = unknown
											if background: eta += ' ETA'
										else:
											eta = item['transfer']['progress']['remaining']['time']['description']

										description = []
										if background:
											if speed: description.append(speed)
											if size and sizeBytes > 0: description.append(size)
											if eta: description.append(eta)
											if len(description) > 0:
												description = interface.Format.fontSeparator().join(description)
											else:
												description = 'Unknown Progress'
										else:
											if speed:
												if speedBytes <= 0:
													speed = unknown
												peers = item['transfer']['torrent']['peers']
												if peers == 0: peers = ''
												else: peers = ' from ' + str(peers) + ' nodes'
												description.append(interface.Format.font('Download Speed: ', bold = True) + speed + peers)
											if size:
												if sizeBytes > 0:
													size = sizeCompleted + ' of ' + size
												else:
													size = unknown
												description.append(interface.Format.font('Download Size: ', bold = True) + size)
											if eta: description.append(interface.Format.font('Remaining Time: ', bold = True) + eta)
											description = interface.Format.fontNewline().join(description)

										interface.Core.update(progress = int(percentage), title = title, message = description)

								if interface.Core.canceled(): break

								# Ask to close a background dialog, because there is no cancel button as with the foreground dialog.
								elapsed = self.timer.elapsed()
								conditionShort = self.timerShort == False and elapsed > 30
								conditionLong = self.timerLong == False and elapsed > 120
								if (conditionShort or conditionLong) and background:
									if conditionShort: question = 'The download is taking a bit longer.'
									else: question = 'The download is taking a lot longer.'

									if seconds: question += ' The estimated remaining time is ' + convert.ConverterDuration(seconds, convert.ConverterDuration.UnitSecond).string(format = convert.ConverterDuration.FormatWordMedium) + '.'
									else: question += ' The estimated remaining time is currently unknown.'

									if conditionShort: question += ' Do you want to take action or let the download continue in the background?'
									else: question += ' Are you sure you do not want to take action and let the download continue in the background?'

									if conditionShort: self.timerShort = True
									if conditionLong: self.timerLong = True

									answer = interface.Dialog.option(title = title, message = question, labelConfirm = 'Take Action', labelDeny = 'Continue Download')
									if answer:
										if self._addAction(result):
											break
										else:
											self.tActionCanceled = True
											return None

								# Sleep
								tools.Time.sleep(0.5)

							if close: interface.Core.close()
						except:
							tools.Logger.error()

						# Action Dialog
						if interface.Core.canceled():
							if not self._addAction(result):
								self.tActionCanceled = True
								return None

						# NB: This is very important.
						# Close the dialog and sleep (0.1 is not enough).
						# This alows the dialog to properley close and reset everything.
						# If not present, the internal iscanceled variable of the progress dialog will stay True after the first cancel.
						interface.Core.close()
						tools.Time.sleep(0.5)

				# END of updateProgress

				try:
					thread = threading.Thread(target = updateProgress, args = (id, percentage, close))
					thread.start()
					thread.join()
				except:
					tools.Logger.error()
		else:
			title = 'Download Error'
			message = 'Download Failure'
			self._addError(title = title, message = message)

		if self.tActionCanceled:
			return self.mDebrid.addResult(error = Debrid.ErrorCancel)
		else:
			return self.mDebrid.addResult(id = id, link = self.tLink)

	##############################################################################
	# DOWNLOAD
	##############################################################################

	def downloadInformation(self):
		interface.Loader.show()
		title = PremiumizeInterface.Name + ' ' + interface.Translation.string(32009)
		if self.mDebrid.accountEnabled():
			account = self.mDebrid.account()
			if account:
				information = self.mDebrid.downloadInformation()
				items = []

				# Count
				count = information['count']
				items.append({
					'title' : 33496,
					'items' : [
						{ 'title' : 33497, 'value' : str(count['total']) },
						{ 'title' : 33291, 'value' : str(count['busy']) },
						{ 'title' : 33294, 'value' : str(count['finished']) },
						{ 'title' : 33295, 'value' : str(count['failed']) },
					]
				})

				# Size
				size = information['size']
				items.append({
					'title' : 33498,
					'items' : [
						{ 'title' : 33497, 'value' : size['description'] },
					]
				})

				# Usage
				percentage = str(information['usage']['consumed']['percentage']) + '%'

				pointsUsed = information['usage']['consumed']['points']
				pointsTotal = information['usage']['consumed']['points'] + information['usage']['remaining']['points']
				points = str(pointsUsed) + ' ' + interface.Translation.string(33073) + ' ' + str(pointsTotal)

				storageUsed = information['usage']['consumed']['size']['description']
				storageTotal = convert.ConverterSize(information['usage']['consumed']['size']['bytes'] + information['usage']['remaining']['size']['bytes']).stringOptimal()
				storage = storageUsed + ' ' + interface.Translation.string(33073) + ' ' + storageTotal

				items.append({
					'title' : 33228,
					'items' : [
						{ 'title' : 33348, 'value' : percentage },
						{ 'title' : 33349, 'value' : points },
						{ 'title' : 33350, 'value' : storage },
					]
				})

				# Dialog
				interface.Loader.hide()
				interface.Dialog.information(title = title, items = items)
			else:
				interface.Loader.hide()
				interface.Dialog.confirm(title = title, message = interface.Translation.string(33352) % PremiumizeInterface.Name)
		else:
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33351) % PremiumizeInterface.Name)

	##############################################################################
	# DIRECTORY
	##############################################################################

	def directoryItemAction(self, item):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew
		link = item['link']

		items = [
			interface.Format.bold(interface.Translation.string(35083) + ': ') + interface.Translation.string(35086),
			interface.Format.bold(interface.Translation.string(33031) + ': ') + interface.Translation.string(35087),
			interface.Format.bold(interface.Translation.string(35085) + ': ') + interface.Translation.string(35088),
		]
		choice = interface.Dialog.select(title = 32009, items = items)
		if choice >= 0:
			if choice == 0: interface.Player.playNow(link)
			elif choice == 1: clipboard.Clipboard.copyLink(link, True)
			elif choice == 2: tools.System.openLink(link)

	def directoryItem(self, item):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew

		directory = interface.Directory(content = interface.Directory.ContentAddons)
		items = item['files']
		itemsNew = []

		for item in items:
			info = []
			icon = 'downloads.png'

			try: info.append(item['extension'].upper())
			except: pass

			try:
				if item['size']['bytes'] > 0:
					info.append(item['size']['description'])
			except: pass

			label = interface.Format.bold(item['name'])
			label += interface.Format.newline()
			label += ' | '.join(info)

			itemJson = tools.Converter.jsonTo(item)

			context = []
			context.append({'label' : 33371, 'command' : tools.System.commandPlugin(action = 'premiumizeItemAction', parameters = {'item' : itemJson})})

			itemsNew.append({'item' : itemJson, 'label' : label, 'context' : context, 'icon' : icon})

		# Sort so that episodes show in ascending order.
		itemsNew.sort(key = lambda i: i['label'])

		for item in itemsNew:
			directory.add(label = item['label'], action = 'premiumizeItemAction', parameters = {'item' : item['item']}, context = item['context'], folder = False, icon = item['icon'], iconDefault = 'DefaultAddonProgram.png')

		directory.finish()

	def directoryListAction(self, item, context = False):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew
		try: context = bool(context)
		except:	context = False

		actions = []
		items = []

		if item['status'] == Premiumize.StatusFinished:
			actions.append('browsecontent')
			items.append(interface.Format.bold(interface.Translation.string(35089) + ': ') + interface.Translation.string(35094))
			actions.append('downloadlargest')
			items.append(interface.Format.bold(interface.Translation.string(35150) + ': ') + interface.Translation.string(35151))
			actions.append('streamlargest')
			items.append(interface.Format.bold(interface.Translation.string(35090) + ': ') + interface.Translation.string(35095))
			actions.append('copylargest')
			items.append(interface.Format.bold(interface.Translation.string(35091) + ': ') + interface.Translation.string(35096))
			actions.append('openlargest')
			items.append(interface.Format.bold(interface.Translation.string(35092) + ': ') + interface.Translation.string(35097))
			actions.append('downloadzip')
			items.append(interface.Format.bold(interface.Translation.string(35152) + ': ') + interface.Translation.string(35153))
			actions.append('copyzip')
			items.append(interface.Format.bold(interface.Translation.string(35084) + ': ') + interface.Translation.string(35098))
			actions.append('openzip')
			items.append(interface.Format.bold(interface.Translation.string(35093) + ': ') + interface.Translation.string(35099))

		actions.append('remove')
		items.append(interface.Format.bold(interface.Translation.string(35100) + ': ') + interface.Translation.string(35101))
		actions.append('refresh')
		items.append(interface.Format.bold(interface.Translation.string(35103) + ': ') + interface.Translation.string(35104))
		actions.append('cancel')
		items.append(interface.Format.bold(interface.Translation.string(35105) + ': ') + interface.Translation.string(35106))

		choice = interface.Dialog.select(title = 32009, items = items)
		if choice >= 0:
			choice = actions[choice]
			if choice == 'refresh':
				interface.Directory.refresh()
			elif not choice == 'cancel':
				hide = True
				interface.Loader.show()
				try:
					id = item['id']
					idFolder = item['folder']
					idFile = item['file']
					if choice == 'remove':
						self.mDebrid.deleteSingle(id, wait = True)
						interface.Directory.refresh()
						hide = False # Already hidden by container refresh.
					else:
						item = self.mDebrid.item(idFolder = idFolder, idFile = idFile)
						itemLink = item['video']['link']
						if choice == 'browsecontent':
							# Kodi cannot set the directory structure more than once in a single run.
							# If the action is launched directly by clicking on the item, Kodi seems to clear the structure so that you can create a new one.
							# This is not the case when the action menu is launched from the "Actions" option in the context menu.
							# Open the window externally. However, this will load longer and the back action is to the main menu.
							if context:
								itemJson = tools.Converter.jsonTo(item)
								tools.System.window(action = 'premiumizeItem', parameters = {'item' : itemJson})
							else:
								self.directoryItem(item)
						elif choice == 'streamlargest':
							if network.Networker.linkIs(itemLink): interface.Player.playNow(itemLink)
							else: raise Exception('Invalid Largest Link: ' + str(itemLink))
						elif choice == 'downloadlargest':
							if network.Networker.linkIs(itemLink): downloader.Downloader(downloader.Downloader.TypeManual).download(media = downloader.Downloader.MediaOther, link = itemLink)
							else: raise Exception('Invalid Largest Link: ' + str(itemLink))
						elif choice == 'copylargest':
							if network.Networker.linkIs(itemLink): clipboard.Clipboard.copyLink(itemLink, True)
							else: raise Exception('Invalid Largest Link: ' + str(itemLink))
						elif choice == 'openlargest':
							if network.Networker.linkIs(itemLink): tools.System.openLink(itemLink)
							else: raise Exception('Invalid Largest Link: ' + str(itemLink))
						else:
							itemZip = self.mDebrid.zip(idFolder)
							if choice == 'downloadzip':
								if network.Networker.linkIs(itemZip): downloader.Downloader(downloader.Downloader.TypeManual).download(media = downloader.Downloader.MediaOther, link = itemZip)
								else: raise Exception('Invalid ZIP Link: ' + str(itemZip))
							elif choice == 'copyzip':
								if network.Networker.linkIs(itemZip): clipboard.Clipboard.copyLink(itemZip, True)
								else: raise Exception('Invalid ZIP Link: ' + str(itemZip))
							elif choice == 'openzip':
								if network.Networker.linkIs(itemZip): tools.System.openLink(itemZip)
								else: raise Exception('Invalid ZIP Link: ' + str(itemZip))
				except:
					tools.Logger.error()
					interface.Dialog.notification(title = 33566, message = 35107, icon = interface.Dialog.IconError)
				if hide: interface.Loader.hide()

	def directoryList(self):
		directory = interface.Directory(content = interface.Directory.ContentAddons)
		items = self.mDebrid._itemsTransfer()
		itemsNew = [[], [], [], [], [], []]

		for item in items:
			info = []
			icon = None

			try: status = item['status']
			except: status = None

			if not status == None and not status == Premiumize.StatusUnknown:
				color = None
				if status == Premiumize.StatusError:
					color = interface.Format.ColorBad
					icon = 'downloadsfailed.png'
				elif status == Premiumize.StatusTimeout:
					color = interface.Format.ColorPoor
					icon = 'downloadsfailed.png'
				elif status == Premiumize.StatusQueued:
					color = interface.Format.ColorMedium
					icon = 'downloadsbusy.png'
				elif status == Premiumize.StatusBusy:
					color = interface.Format.ColorExcellent
					icon = 'downloadsbusy.png'
				elif status == Premiumize.StatusFinalize:
					color = interface.Format.ColorMain
					icon = 'downloadsbusy.png'
				elif status == Premiumize.StatusFinished:
					color = interface.Format.ColorSpecial
					icon = 'downloadscompleted.png'
				info.append(interface.Format.fontColor(status.capitalize(), color))

			if status == Premiumize.StatusBusy:
				try:
					colors = interface.Format.colorGradient(interface.Format.ColorMedium, interface.Format.ColorExcellent, 101) # One more, since it goes from 0 - 100
					percentage = int(item['transfer']['progress']['completed']['percentage'])
					info.append(interface.Format.fontColor('%d%%' % percentage, colors[percentage]))
				except:
					tools.Logger.error()
					pass
				try:
					if item['transfer']['speed']['bits'] > 0:
						info.append(item['transfer']['speed']['description'])
				except: pass
				try:
					if item['transfer']['progress']['remaining']['time']['seconds'] > 0:
						info.append(item['transfer']['progress']['remaining']['time']['description'])
				except: pass

			try:
				if item['size']['bytes'] > 0:
					info.append(item['size']['description'])
			except: pass

			label = interface.Format.bold(item['name'])
			label += interface.Format.newline()
			label += ' | '.join(info)

			itemJson = tools.Converter.jsonTo(item)

			context = []
			context.append({'label' : 32072, 'command' : 'Container.Refresh'})
			context.append({'label' : 33371, 'command' : tools.System.commandPlugin(action = 'premiumizeListAction', parameters = {'item' : itemJson, 'context' : 1})})

			if status == Premiumize.StatusError: index = 0
			elif status == Premiumize.StatusTimeout: index = 1
			elif status == Premiumize.StatusQueued: index = 2
			elif status == Premiumize.StatusBusy: index = 3
			elif status == Premiumize.StatusFinalize: index = 4
			elif status == Premiumize.StatusFinished: index = 5
			else: index = 0

			itemsNew[index].append({'item' : itemJson, 'label' : label, 'context' : context, 'icon' : icon})

		for item in itemsNew:
			for i in item:
				directory.add(label = i['label'], action = 'premiumizeListAction', parameters = {'item' : i['item']}, context = i['context'], folder = True, icon = i['icon'], iconDefault = 'DefaultAddonProgram.png')

		directory.finish()

############################################################################################################################################################
# OFFCLOUD
############################################################################################################################################################

class OffCloud(Debrid):

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

	# Timeouts
	# Number of seconds the requests should be cached.
	TimeoutServices = 3 # 3 hour
	TimeoutAccount = 0.17 # 10 min

	# Limits
	LimitLink = 2000 # Maximum length of a URL.
	LimitHashesGet = 40 # Maximum number of 40-character hashes to use in GET parameter so that the URL length limit is not exceeded.
	LimitHashesPost = 100 # Even when the hashes are send via POST, Premiumize seems to ignore the last ones (+- 1000 hashes). When too many hashes are sent at once (eg 500-900), if often causes a request timeout. Keep the limit small enough. Rather start multiple requests which should create multipel threads on the server.

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Debrid.__init__(self, 'OffCloud')

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
			if mode == OffCloud.ModeGet or mode == OffCloud.ModePut or mode == OffCloud.ModeDelete or httpData:
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

			if mode == OffCloud.ModePut or mode == OffCloud.ModeDelete:
				request.get_method = lambda: mode.upper()

			request.add_header('User-Agent', OffCloud.UserAgent)
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

	def _retrieve(self, mode, category, action = None, url = None, proxyId = None, requestId = None, hash = None, httpTimeout = None, httpData = None, httpHeaders = None):
		if category == OffCloud.CategoryTorrent and action == OffCloud.ActionUpload:
			# For some reason, this function is not under the API.
			link = network.Networker.linkJoin(OffCloud.LinkMain, category, action)
		elif category == OffCloud.CategoryCloud and action == OffCloud.ActionExplore:
			link = network.Networker.linkJoin(OffCloud.LinkApi, category, action, requestId)
			requestId = None # Do not add as parameter
		elif action == OffCloud.ActionRemove:
			link = network.Networker.linkJoin(OffCloud.LinkMain, category, action, requestId)
			requestId = None # Do not add as parameter
		elif action:
			link = network.Networker.linkJoin(OffCloud.LinkApi, category, action)
		else:
			link = network.Networker.linkJoin(OffCloud.LinkApi, category)

		parameters = {}
		parameters[OffCloud.ParameterApiKey] = self.accountKey()

		if not url == None: parameters[OffCloud.ParameterUrl] = url
		if not proxyId == None: parameters[OffCloud.ParameterProxyId] = proxyId
		if not requestId == None: parameters[OffCloud.ParameterRequestId] = requestId
		if not hash == None:
			if isinstance(hash, basestring):
				parameters[OffCloud.ParameterHash] = hash.lower()
			else:
				for i in range(len(hash)):
					hash[i] = hash[i].lower()
				parameters[OffCloud.ParameterHashes] = hash

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
		result = self._retrieve(mode = OffCloud.ModeGet, category = OffCloud.CategoryAccount, action = OffCloud.ActionStats)
		return self.success() == True and 'userId' in result and not result['userId'] == None and not result['userId'] == ''

	def account(self, cache = True):
		try:
			if self.accountValid():
				timeout = OffCloud.TimeoutAccount if cache else 0
				def __offcloudAccount(): # Must have a different name than the tools.Cache.cache call for the hoster list. Otherwise the cache returns the result for the hosters instead of the account.
					return self._retrieve(mode = OffCloud.ModeGet, category = OffCloud.CategoryAccount, action = OffCloud.ActionStats)
				result = tools.Cache.cache(__offcloudAccount, timeout)

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

	def services(self, cache = True, onlyEnabled = False):
		# Even thow ServicesUpdate is a class variable, it will be destrcucted if there are no more Premiumize instances.
		if OffCloud.Services == None:
			OffCloud.Services = []

			streamingTorrent = self.streamingTorrent()
			streamingUsenet = self.streamingUsenet()
			streamingHoster = self.streamingHoster()

			try:
				timeout = OffCloud.TimeoutServices if cache else 0
				def __offcloudHosters(): # Must have a different name than the tools.Cache.cache call for the account details. Otherwise the cache returns the result for the account instead of the hosters.
					return self._retrieve(mode = OffCloud.ModeGet, category = OffCloud.CategorySites)
				result = tools.Cache.cache(__offcloudHosters, timeout)

				# Sometimes error HTML page is returned.
				if not isinstance(result, list):
					OffCloud.Services = None
					return None

				for i in result:
					id = i['name']
					if id == OffCloud.ServiceUsenet['id']:
						enabled = streamingUsenet
						name = OffCloud.ServiceUsenet['name']
						domain = OffCloud.ServiceUsenet['domain']
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
						if 'healthy' in status: status = OffCloud.ServiceStatusOnline
						elif 'dead' in status: status = OffCloud.ServiceStatusOffline
						elif 'cloud' in status: status = OffCloud.ServiceStatusCloud
						elif 'limited' in status: status = OffCloud.ServiceStatusLimited
						elif 'awaiting' in status: status = OffCloud.ServiceStatusAwaiting
						elif 'r&d' in status: status = OffCloud.ServiceStatusSoon
						else: status = OffCloud.ServiceStatusUnknown
					except:
						status = OffCloud.ServiceStatusUnknown

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

					OffCloud.Services.append({
						'id' : id,
						'enabled' : enabled and status == OffCloud.ServiceStatusOnline,
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

				OffCloud.Services.append({
					'id' : OffCloud.ServiceTorrent['id'],
					'enabled' : streamingTorrent,
					'status' : OffCloud.ServiceStatusOnline,
					'instant' : True,
					'stream' : False,
					'name' : OffCloud.ServiceTorrent['name'],
					'domain' : OffCloud.ServiceTorrent['domain'],
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
			return [i for i in OffCloud.Services if i['enabled']]
		else:
			return OffCloud.Services

	def servicesList(self, onlyEnabled = False):
		services = self.services(onlyEnabled = onlyEnabled)
		result = [service['domain'] for service in services] # Torrents and Usenet
		for service in services:
			if 'domain' in service:
				result.append(service['domain'])
			if 'domains' in service:
				result.extend(service['domains'])
		return list(set(result))

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
			result = self._retrieve(mode = OffCloud.ModePost, category = OffCloud.CategoryProxy, action = OffCloud.ActionList)
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
						if OffCloud.ServerMain in type: type = OffCloud.ServerMain
						elif OffCloud.ServerProxy in type: type = OffCloud.ServerProxy
						else: type = OffCloud.ServerUnknown
					except:
						type = OffCloud.ServerUnknown

					try:
						if not location == None and not type == OffCloud.ServerUnknown:
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
				if 'cloud' in result: error = OffCloud.ErrorLimitCloud
				elif 'premium' in result: error = OffCloud.ErrorLimitPremium
				elif 'link' in result: error = OffCloud.ErrorLimitLink
				elif 'video' in result: error = OffCloud.ErrorLimitVideo
				elif 'proxy' in result: error = OffCloud.ErrorLimitProxy
				else: error = Debrid.ErrorUnknown
			elif 'error' in result:
				result = result['error'].lower()
				if 'reserved' in result and 'premium' in result:
					error = OffCloud.ErrorPremium
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
			return OffCloud.CategoryCloud
		else:
			if tools.Settings.getBoolean('accounts.debrid.offcloud.instant'): return OffCloud.CategoryInstant
			else: return OffCloud.CategoryCloud

	def _addProxy(self):
		result = tools.Settings.getString('accounts.debrid.offcloud.location.id')
		if result == '': result = None
		return result

	def add(self, link, category = None, title = None, season = None, episode = None, pack = False, source = None, proxy = None):
		type = self._addType(link = link, source = source)
		if category == None: category = self._addCategory(type = type)
		if category == OffCloud.CategoryInstant and proxy == None: proxy = self._addProxy()
		if type == network.Container.TypeTorrent:
			return self.addTorrent(link = link, title = title, season = season, episode = episode)
		elif type == network.Container.TypeUsenet:
			return self.addUsenet(link = link, title = title, season = season, episode = episode)
		else:
			return self.addHoster(link = link, category = category, season = season, episode = episode, proxy = proxy)

	def addInstant(self, link, season = None, episode = None, proxy = None):
		result = self._retrieve(mode = OffCloud.ModePost, category = OffCloud.CategoryInstant, action = OffCloud.ActionDownload, url = link, proxyId = proxy)
		if self.success(): return self._addLink(category = OffCloud.CategoryInstant, result = result, season = season, episode = episode)
		else: return self.addResult(error = OffCloud.ErrorOffCloud)

	def addCloud(self, link, title = None, season = None, episode = None, source = None):
		result = self._retrieve(mode = OffCloud.ModePost, category = OffCloud.CategoryCloud, action = OffCloud.ActionDownload, url = link)
		if self.success(): return self._addLink(category = OffCloud.CategoryCloud, result = result, season = season, episode = episode)
		else: return self.addResult(error = OffCloud.ErrorOffCloud)

	# Downloads the torrent, nzb, or any other container supported by OffCloud.
	# If mode is not specified, tries to detect the file type automatically.
	def addContainer(self, link, title = None, season = None, episode = None):
		try:
			# https://github.com/tknorris/plugin.video.premiumize/blob/master/local_lib/premiumize_api.py
			source = network.Container(link).information()
			if source['path'] == None and source['data'] == None: # Sometimes the NZB cannot be download, such as 404 errors.
				return self.addResult(error = OffCloud.ErrorInaccessible)

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

			result = self._retrieve(mode = OffCloud.ModePost, category = OffCloud.CategoryTorrent, action = OffCloud.ActionUpload, httpData = data, httpHeaders = headers)
			if self.success(): return self.addCloud(link = result['url'], title = title, season = season, episode = episode)
			else: return self.addResult(error = OffCloud.ErrorOffCloud)
		except:
			tools.Logger.error()
			return self.addResult(error = OffCloud.ErrorOffCloud)

	def addHoster(self, link, category = CategoryInstant, season = None, episode = None, proxy = None):
		if category == OffCloud.CategoryInstant:
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
				index = 0 if item['category'] == OffCloud.CategoryInstant else 1
				status = item['status']
				try: size[index] += item['size']['bytes']
				except: pass
				count[index] += 1
				if status in [OffCloud.StatusUnknown, OffCloud.StatusError]:
					countFailed[index] += 1
				elif status in [OffCloud.StatusCanceled]:
					countCanceled[index] += 1
				elif status in [OffCloud.StatusFinished]:
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
			if category == None or category == OffCloud.CategoryInstant:
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
			if category == None or category == OffCloud.CategoryCloud:
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
			return OffCloud.ErrorOffCloud

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {Debrid.ModeTorrent}

	# id: single hash or list of hashes.
	def cachedIs(self, id, timeout = None):
		result = self.cached(id = id, timeout = timeout)
		if isinstance(result, dict): return result['cached']
		elif isinstance(result, list): return [i['cached'] for i in result]
		else: return False

	# id: single hash or list of hashes.
	# NB: a URL has a maximum length. Hence, a list of hashes cannot be too long, otherwise the request will fail.
	def cached(self, id, timeout = None, callback = None, sources = None):
		single = isinstance(id, basestring)
		if single: id = [id] # Must be passed in as a list.

		mode = OffCloud.ModePost # Post can send more at a time.
		if mode == OffCloud.ModePost:
			chunks = [id[i:i + OffCloud.LimitHashesPost] for i in xrange(0, len(id), OffCloud.LimitHashesPost)]
		else:
			chunks = [id[i:i + OffCloud.LimitHashesGet] for i in xrange(0, len(id), OffCloud.LimitHashesGet)]

		self.tCacheLock = threading.Lock()
		self.tCacheResult = []

		def cachedChunk(callback, mode, hashes, timeout):
			offcloud = OffCloud()
			result = offcloud._retrieve(mode = mode, category = OffCloud.CategoryTorrent, action = OffCloud.ActionCheck, hash = hashes, httpTimeout = timeout)
			if offcloud.success():
				result = result['cachedItems']
				self.tCacheLock.acquire()
				self.tCacheResult.extend(result)
				self.tCacheLock.release()
				if callback:
					for hash in hashes:
						try: callback(self.id(), hash, hash in result)
						except: pass

		threads = []
		for chunk in chunks:
			thread = threading.Thread(target = cachedChunk, args = (callback, mode, chunk, timeout))
			threads.append(thread)
			thread.start()

		[i.join() for i in threads]
		if not callback:
			caches = []
			for hash in id:
				hash = hash.lower()
				caches.append({'id' : hash, 'hash' : hash, 'cached' : hash in self.tCacheResult})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches

	##############################################################################
	# ITEM
	##############################################################################

	def _itemStatus(self, status):
		status = status.lower()
		if status == 'downloading': return OffCloud.StatusBusy
		elif status == 'downloaded': return OffCloud.StatusFinished
		elif status == 'created': return OffCloud.StatusInitialize
		elif status == 'processing': return OffCloud.StatusFinalize
		elif status == 'error': return OffCloud.StatusError
		elif status == 'queued': return OffCloud.StatusQueued
		elif status == 'canceled': return OffCloud.StatusCanceled
		elif status == 'fragile': return OffCloud.StatusError
		else: return OffCloud.StatusUnknown

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
		if category == OffCloud.CategoryInstant:
			return self.itemInstant(id = id)
		elif category == OffCloud.CategoryCloud:
			return self.itemCloud(id = id, season = season, episode = episode, transfer = transfer, files = files)
		else:
			return None

	def itemInstant(self, id):
		# Not supported by API.
		# Retrieve entier instant download list and pick the correct one from it.
		items = self.items(category = OffCloud.CategoryInstant)
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
				try: self.tResulTransfer = OffCloud()._retrieve(mode = OffCloud.ModePost, category = OffCloud.CategoryCloud, action = OffCloud.ActionStatus, requestId = id)['status']
				except: pass

			def _itemContent(id):
				try: self.tResulContent = OffCloud()._retrieve(mode = OffCloud.ModeGet, category = OffCloud.CategoryCloud, action = OffCloud.ActionExplore, requestId = id)
				except: pass

			threads = []
			if transfer: threads.append(threading.Thread(target = _itemTransfer, args = (id,)))
			if files: threads.append(threading.Thread(target = _itemContent, args = (id,)))
			[i.start() for i in threads]
			[i.join() for i in threads]

			result = {
				'id' : id,
				'category' : OffCloud.CategoryCloud,
			}

			if self.tResulTransfer:
				status = self._itemStatus(self.tResulTransfer['status'])

				error = None
				try:
					error = self.tResulTransfer['errorMessage']
				except: pass

				directory = False
				try:
					directory = self.tResulTransfer['isDirectory']
				except: pass

				name = None
				try:
					name = self.tResulTransfer['fileName']
				except: pass

				server = None
				try:
					server = self.tResulTransfer['server']
				except: pass

				server = None
				try:
					server = self.tResulTransfer['server']
				except: pass

				size = 0
				try:
					size = long(self.tResulTransfer['fileSize'])
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
				if status == OffCloud.StatusFinished:
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
			if not self.tResulContent and not directory and status == OffCloud.StatusFinished and not server == None and not server == '':
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

						if meta.episodeContains(title = fullName, season = season, episode = episode):
							video = i
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
		return self.items(category = OffCloud.CategoryInstant)

	def itemsCloud(self):
		return self.items(category = OffCloud.CategoryCloud)

	def items(self, category = None):
		try:
			if category == None:
				threads = []
				self.tResultItemsInstant = None
				self.tResultItemsCloud = None
				def _itemsInstant():
					self.tResultItemsInstant = OffCloud().items(category = OffCloud.CategoryInstant)
				def _itemsCloud():
					self.tResultItemsCloud = OffCloud().items(category = OffCloud.CategoryCloud)
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
				result = self._retrieve(mode = OffCloud.ModeGet, category = category, action = OffCloud.ActionHistory)
				for i in result:
					status = self._itemStatus(i['status'])
					video = None

					# Instant links always stay at created.
					if category == OffCloud.CategoryInstant:
						if status == OffCloud.StatusInitialize:
							status = OffCloud.StatusFinished
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

					# Do not include hidden items with an error status. These are internal control items from OffCloud.
					if not(status == OffCloud.StatusError and metadata == 'hide'):
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
			result = self._retrieve(mode = OffCloud.ModeGet, category = category, action = OffCloud.ActionRemove, requestId = id)
			if self.success(): return True
			else: return OffCloud.ErrorOffCloud

		if category == None: category = OffCloud.CategoryCloud
		id = self.idItem(id)
		if wait:
			return _delete(id, category)
		else:
			thread = threading.Thread(target = _delete, args = (id, category))
			thread.start()

	def deleteInstant(self, id):
		return self.delete(id = id, category = OffCloud.CategoryInstant)

	def deleteCloud(self, id):
		return self.delete(id = id, category = OffCloud.CategoryCloud)

	def deleteAll(self, category = None, wait = True):
		items = self.items(category = category)
		if isinstance(items, list):
			if len(items) > 0:
				def _deleteAll(category, id):
					OffCloud().delete(category = category, id = id)
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
			return OffCloud.ErrorOffCloud

	def deleteAllInstant(self, wait = True):
		return self.deleteAll(category = OffCloud.CategoryInstant, wait = wait)

	def deleteAllCloud(self, wait = True):
		return self.deleteAll(category = OffCloud.CategoryCloud, wait = wait)

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

class OffCloudInterface(object):

	Name = 'OffCloud'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		self.mDebrid = OffCloud()

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self):
		interface.Loader.show()
		valid = False
		title = OffCloudInterface.Name + ' ' + interface.Translation.string(33339)
		if self.mDebrid.accountEnabled():
			account = self.mDebrid.account(cache = False)
			if account:
				valid = interface.Translation.string(33341) if self.mDebrid.accountValid() else interface.Translation.string(33342)
				premium = interface.Translation.string(33341) if account['premium'] else interface.Translation.string(33342)

				date = account['expiration']['date']
				days = str(account['expiration']['remaining'])

				limitsLinks = interface.Translation.string(35221) if account['limits']['links'] <= 0 else str(account['limits']['links'])
				limitsPremium = interface.Translation.string(35221) if account['premium'] else str(account['limits']['premium'])
				limitsTorrents = interface.Translation.string(35221) if account['limits']['torrents'] <= 0 else str(account['limits']['torrents'])
				limitsStreaming = interface.Translation.string(35221) if account['limits']['streaming'] <= 0 else str(account['limits']['streaming'])
				limitsCloud = account['limits']['cloud']['description']
				limitsProxy = account['limits']['proxy']['description']

				items = []

				# Information
				items.append({
					'title' : 33344,
					'items' : [
						{ 'title' : 33340, 'value' : valid },
						{ 'title' : 33768, 'value' : premium },
						{ 'title' : 32303, 'value' : account['user'] },
						{ 'title' : 32304, 'value' : account['email'] },

					]
				})

				# Expiration
				items.append({
					'title' : 33345,
					'items' : [
						{ 'title' : 33346, 'value' : date },
						{ 'title' : 33347, 'value' : days },
					]
				})

				# Limits
				items.append({
					'title' : 35220,
					'items' : [
						{ 'title' : 35222, 'value' : limitsLinks },
						{ 'title' : 33768, 'value' : limitsPremium },
						{ 'title' : 33199, 'value' : limitsTorrents },
						{ 'title' : 33487, 'value' : limitsStreaming },
						{ 'title' : 35206, 'value' : limitsCloud },
						{ 'title' : 35223, 'value' : limitsProxy },
					]
				})

				# Dialog
				interface.Loader.hide()
				interface.Dialog.information(title = title, items = items)
			else:
				interface.Loader.hide()
				interface.Dialog.confirm(title = title, message = interface.Translation.string(33352) % OffCloudInterface.Name)
		else:
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33351) % OffCloudInterface.Name)

		return valid

	##############################################################################
	# SETTINGS
	##############################################################################

	def settingsLocation(self, settings = True):
		default = interface.Translation.string(33564)
		interface.Loader.show()
		proxies = self.mDebrid.proxyList()
		proxiesNames = [default]
		if proxies: proxiesNames = proxiesNames + [proxy['description'] for proxy in proxies]
		interface.Loader.hide()
		choice = interface.Dialog.options(title = 35207, items = proxiesNames)
		if choice >= 0:
			if choice == 0:
				id = ''
				name = default
			else:
				id = proxies[choice - 1]['id']
				name = proxies[choice - 1]['name']
			tools.Settings.set('accounts.debrid.offcloud.location.id', id)
			tools.Settings.set('accounts.debrid.offcloud.location.name', name)
		if settings: tools.Settings.launch(category = tools.Settings.CategoryAccounts)

	##############################################################################
	# CLEAR
	##############################################################################

	def clear(self, category = None):
		title = OffCloudInterface.Name + ' ' + interface.Translation.string(33013)
		message = 'Do you want to clear'
		if category == None: message += ' all'
		message += ' your OffCloud'
		if category == OffCloud.CategoryInstant: message += ' instant'
		elif category == OffCloud.CategoryCloud: message += ' cloud'
		message += ' downloads and delete your files from the server?'
		if interface.Dialog.option(title = title, message = message):
			interface.Loader.show()
			self.mDebrid.deleteAll(category = category)
			interface.Loader.hide()
			message = 'OffCloud Downloads Cleared'
			interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconSuccess)

	##############################################################################
	# ADD
	##############################################################################

	def addManual(self, category = None):
		result = None
		title = 35082
		items = [
			interface.Format.bold(interface.Translation.string(35076) + ': ') + interface.Translation.string(35077),
			interface.Format.bold(interface.Translation.string(33381) + ': ') + interface.Translation.string(35078),
			interface.Format.bold(interface.Translation.string(33380) + ': ') + interface.Translation.string(35079),
		]
		choice = interface.Dialog.select(title = title, items = items)

		if choice >= 0:
			link = None
			if choice == 0 or choice == 1:
				link = interface.Dialog.input(title = title, type = interface.Dialog.InputAlphabetic)
			elif choice == 2:
				link = interface.Dialog.browse(title = title, type = interface.Dialog.BrowseFile, multiple = False, mask = ['torrent', 'nzb'])

			if not link == None and not link == '':
				interface.Dialog.notification(title = 35070, message = 35071, icon = interface.Dialog.IconSuccess)
				interface.Loader.show()
				result = self.add(link, category = category)
				if result['success']:
					interface.Dialog.closeAllProgress()
					choice = interface.Dialog.option(title = 35073, message = 35074)
					if choice: interface.Player.playNow(result['link'])

		interface.Loader.hide()
		return result

	def add(self, link, category = None, title = None, season = None, episode = None, pack = False, close = True, source = None, cached = None, select = False):
		result = self.mDebrid.add(link = link, category = category, title = title, season = season, episode = episode, pack = pack, source = source)
		if select: result = self._addSelect(result)
		if result['success']:
			return result
		elif result['id']:
			return self._addLink(result = result, season = season, episode = episode, close = close, pack = pack, cached = cached, select = select)
		elif result['error'] == OffCloud.ErrorOffCloud:
			title = 'Stream Error'
			message = 'Failed To Add Stream To OffCloud'
		elif result['error'] == OffCloud.ErrorLimitCloud:
			title = 'Limit Error'
			message = 'OffCloud Cloud Limit Reached'
		elif result['error'] == OffCloud.ErrorLimitPremium:
			title = 'Limit Error'
			message = 'OffCloud Premium Limit Reached'
		elif result['error'] == OffCloud.ErrorLimitLink:
			title = 'Limit Error'
			message = 'OffCloud Link Limit Reached'
		elif result['error'] == OffCloud.ErrorLimitProxy:
			title = 'Limit Error'
			message = 'OffCloud Proxy Limit Reached'
		elif result['error'] == OffCloud.ErrorLimitVideo:
			title = 'Limit Error'
			message = 'OffCloud Video Limit Reached'
		elif result['error'] == OffCloud.ErrorPremium:
			title = 'Premium Account'
			message = 'OffCloud Premium Account Required'
		elif result['error'] == OffCloud.ErrorSelection:
			title = 'Selection Error'
			message = 'No File Selected'
		else:
			tools.Logger.errorCustom('Unexpected OffCloud Error: ' + str(result))
			title = 'Stream Error'
			message = 'Stream File Unavailable'
		self._addError(title = title, message = message)
		result['notification'] = True
		return result

	def _addSelect(self, result):
		try:
			if not result: return result
			items = [i for i in result['items']['files'] if i['name'] and not i['name'].endswith(Debrid.Exclusions)]
			items = sorted(items, key = lambda x : x['name'])
			choice = interface.Dialog.options(title = 35542, items = [i['name'] for i in items])
			if choice < 0:
				result['success'] = False
				result['error'] = OffCloud.ErrorSelection
			else:
				result['items']['video'] = items[choice]
				result['link'] = items[choice]['link']
		except:
			tools.Logger.error()
		return result

	def _addDelete(self, category, id, notification = False):
		def __addDelete(category, id, notification):
			result = self.mDebrid.delete(category = category, id = id, wait = True)
			if notification:
				if result == True:
					interface.Dialog.notification(title = 'Deletion Success', message = 'Download Deleted From List', icon = interface.Dialog.IconSuccess)
				else:
					interface.Dialog.notification(title = 'Deletion Failure', message = 'Download Not Deleted From List', icon = interface.Dialog.IconError)
		thread = threading.Thread(target = __addDelete, args = (category, id, notification))
		thread.start()

	def _addAction(self, result):
		items = []
		items.append(interface.Format.font(interface.Translation.string(33077) + ': ', bold = True) + interface.Translation.string(33078))
		items.append(interface.Format.font(interface.Translation.string(33079) + ': ', bold = True) + interface.Translation.string(33080))
		items.append(interface.Format.font(interface.Translation.string(33083) + ': ', bold = True) + interface.Translation.string(33084))
		interface.Core.close()
		tools.Time.sleep(0.1) # Ensures progress dialog is closed, otherwise shows flickering.
		choice = interface.Dialog.options(title = 33076, items = items)
		if choice == -1:
			return False
		elif choice == 0:
			return True
		elif choice == 1:
			return False
		elif choice == 2:
			self._addDelete(id = result['id'], category = result['category'] if 'category' in result else None, notification = True)
			return False

	def _addError(self, title, message, delay = True):
		interface.Loader.hide() # Make sure hided from sources __init__.py
		interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconError)
		if delay: tools.Time.sleep(2) # Otherwise the message disappears to quickley when another notification is shown afterwards.

	def _addErrorDetermine(self, item, api = False, pack = False, category = None):
		error = False
		status = item['status'] if 'status' in item else None
		if status == OffCloud.StatusError:
			title = 'Download Error'
			message = None
			if 'error' in item and item['error']:
				message = item['error']
				if 'health' in message.lower(): # Usenet health issues.
					message = 'Download File Health Failure'
				else:
					message = message.lower().title()
			if message == None:
				message = 'Download Failure With Unknown Error'
			self._addError(title = title, message = message)
			error = True
		elif status == OffCloud.StatusCanceled:
			title = 'Download Canceled'
			message = 'Download Was Canceled'
			self._addError(title = title, message = message)
			error = True
		elif api:
			if not 'video' in item or item['video'] == None:
				title = 'Invalid Stream'
				if pack: message = 'No Episode In Season Pack'
				else: message = 'No Playable Stream Found'
				self._addError(title = title, message = message)
				error = False # Do not return True, since it won't have a video stream while still downloading.

		if error:
			try: self.mDebrid.deleteFailure(id = item['id'], pack = pack, category = category)
			except: pass

		return error

	def _addProcessing(self, status, cached):
		return status == OffCloud.StatusProcessing or (cached and (status == OffCloud.StatusInitialize or status == OffCloud.StatusFinalize))

	def _addLink(self, result, season = None, episode = None, close = True, pack = False, cached = None, select = False):
		self.tActionCanceled = False
		try: category = result['category']
		except: category = None

		unknown = 'Unknown'
		id = result['id']

		# In case the progress dialog was canceled while transfering torrent data.
		if interface.Core.canceled():
			self._addDelete(category = category, id = id, notification = False)
			return self.mDebrid.addResult(error = Debrid.ErrorCancel)

		self.tLink =  ''
		item = self.mDebrid.item(category = category, id = id, season = season, episode = episode, transfer = True, files = True)
		if select: result = self._addSelect(result)
		if item:
			try:
				self.tLink = item['video']['link']
				if self.tLink: return self.mDebrid.addResult(id = id, link = self.tLink)
			except: pass
			try: percentage = item['transfer']['progress']['completed']['percentage']
			except: percentage = 0
			status = item['status']
			if self._addErrorDetermine(item, pack = pack, category = category):
				pass
			elif status == OffCloud.StatusQueued or status == OffCloud.StatusInitialize or status == OffCloud.StatusBusy or status == OffCloud.StatusFinalize:
				title = 'OffCloud Download'
				descriptionWaiting = interface.Format.fontBold('Waiting For Download Start') + '%s'
				descriptionFinalize = interface.Format.fontBold('Finalizing Download') + '%s'

				interface.Loader.hide() # Make sure hided from sources __init__.py

				self.timer = tools.Time(start = True)
				self.timerShort = False
				self.timerLong = False

				def updateProgress(status, category, id, percentage, close, cached):
					while True:
						background = interface.Core.background()

						# StatusProcessing is when an already cached file (which is stored as an archive) is being extracted to make it accessible for streaming.
						processing = self._addProcessing(status = status, cached = cached)
						if not processing:
							interface.Core.create(type = interface.Core.TypeDownload, title = title, message = descriptionWaiting)
							interface.Core.update(progress = int(percentage), title = title, message = descriptionWaiting)

						try:
							status = OffCloud.StatusQueued
							seconds = None
							counter = 0
							item = self.mDebrid.item(category = category, id = id, season = season, episode = episode, transfer = True, files = True)
							if select: result = self._addSelect(result)

							while True:
								if (processing and counter == 5) or (not processing and counter == 10): # Only make an API request every 2.5 or 5 seconds.
									item = self.mDebrid.item(category = category, id = id, season = season, episode = episode, transfer = True, files = True)
									if select: result = self._addSelect(result)
									counter = 0
								counter += 1

								status = item['status'] if 'status' in item else None
								processing = self._addProcessing(status = status, cached = cached)
								try:
									self.tLink = item['video']['link']
									if self.tLink: return
								except: pass
								if not status == OffCloud.StatusQueued and not status == OffCloud.StatusInitialize and not status == OffCloud.StatusBusy and not status == OffCloud.StatusFinalize:
									close = True
									self._addErrorDetermine(item, api = True, pack = pack, category = category)
									break
								waiting = item['transfer']['speed']['bytes'] == 0 and item['size']['bytes'] == 0 and item['transfer']['progress']['completed']['value'] == 0 and item['transfer']['progress']['completed']['time']['seconds'] == 0

								if processing:
									pass
								elif status == OffCloud.StatusFinalize:
									interface.Core.update(progress = 0, title = title, message = descriptionFinalize)
								elif waiting:
									interface.Core.update(progress = 0, title = title, message = descriptionWaiting)
								else:
									percentageNew = item['transfer']['progress']['completed']['percentage']
									if percentageNew >= percentage:
										percentage = percentageNew
										description = ''
										speed = item['transfer']['speed']['description']
										speedBytes = item['transfer']['speed']['bytes']
										size = item['size']['description']
										sizeBytes = item['size']['bytes']
										sizeCompleted = item['transfer']['progress']['completed']['size']['description']
										seconds = item['transfer']['progress']['remaining']['time']['seconds']
										if seconds == 0:
											eta = unknown
											if background: eta += ' ETA'
										else:
											eta = item['transfer']['progress']['remaining']['time']['description']

										description = []
										if background:
											if speed: description.append(speed)
											if size and sizeBytes > 0: description.append(size)
											if eta: description.append(eta)
											if len(description) > 0:
												description = interface.Format.fontSeparator().join(description)
											else:
												description = 'Unknown Progress'
										else:
											if speed:
												if speedBytes <= 0:
													speed = unknown
												description.append(interface.Format.font('Download Speed: ', bold = True) + speed)
											if size:
												if sizeBytes > 0:
													size = sizeCompleted + ' of ' + size
												else:
													size = unknown
												description.append(interface.Format.font('Download Size: ', bold = True) + size)
											if eta: description.append(interface.Format.font('Remaining Time: ', bold = True) + eta)
											description = interface.Format.fontNewline().join(description)

										interface.Core.update(progress = int(percentage), title = title, message = description)

								if not processing and interface.Core.canceled(): break

								# Ask to close a background dialog, because there is no cancel button as with the foreground dialog.
								elapsed = self.timer.elapsed()
								conditionShort = self.timerShort == False and elapsed > 30
								conditionLong = self.timerLong == False and elapsed > 120
								if (conditionShort or conditionLong) and background:
									if conditionShort: question = 'The download is taking a bit longer.'
									else: question = 'The download is taking a lot longer.'

									if seconds: question += ' The estimated remaining time is ' + convert.ConverterDuration(seconds, convert.ConverterDuration.UnitSecond).string(format = convert.ConverterDuration.FormatWordMedium) + '.'
									else: question += ' The estimated remaining time is currently unknown.'

									if conditionShort: question += ' Do you want to take action or let the download continue in the background?'
									else: question += ' Are you sure you do not want to take action and let the download continue in the background?'

									if conditionShort: self.timerShort = True
									if conditionLong: self.timerLong = True

									answer = interface.Dialog.option(title = title, message = question, labelConfirm = 'Take Action', labelDeny = 'Continue Download')
									if answer:
										if self._addAction(result):
											break
										else:
											self.tActionCanceled = True
											return None

								# Sleep
								tools.Time.sleep(0.5)

							if not processing and close: interface.Core.close()
						except:
							tools.Logger.error()

						# Action Dialog
						if not processing and interface.Core.canceled():
							if not self._addAction(result):
								self.tActionCanceled = True
								return None

						# NB: This is very important.
						# Close the dialog and sleep (0.1 is not enough).
						# This alows the dialog to properley close and reset everything.
						# If not present, the internal iscanceled variable of the progress dialog will stay True after the first cancel.

						if not processing:
							interface.Core.close()
							tools.Time.sleep(0.5)

				# END of updateProgress
				try:
					thread = threading.Thread(target = updateProgress, args = (status, category, id, percentage, close, cached))
					thread.start()
					thread.join()
				except:
					tools.Logger.error()
		else:
			title = 'Download Error'
			message = 'Download Failure'
			self._addError(title = title, message = message)

		if self.tActionCanceled:
			return self.mDebrid.addResult(error = Debrid.ErrorCancel)
		else:
			return self.mDebrid.addResult(id = id, link = self.tLink)

	##############################################################################
	# DOWNLOAD
	##############################################################################

	def downloadInformation(self, category = None):
		interface.Loader.show()
		title = OffCloudInterface.Name + ' ' + interface.Translation.string(32009)
		if self.mDebrid.accountEnabled():
			account = self.mDebrid.account()
			try:
				if account:
					information = self.mDebrid.downloadInformation(category = category)
					items = []

					# Instant
					if 'instant' in information:
						count = information['instant']['count']
						items.append({
							'title' : 35298,
							'items' : [
								{ 'title' : 33497, 'value' : str(count['total']) },
								{ 'title' : 33291, 'value' : str(count['busy']) },
								{ 'title' : 33294, 'value' : str(count['finished']) },
								{ 'title' : 33295, 'value' : str(count['failed']) },
							]
						})

					# Cloud
					if 'cloud' in information:
						count = information['cloud']['count']
						items.append({
							'title' : 35299,
							'items' : [
								{ 'title' : 33497, 'value' : str(count['total']) },
								{ 'title' : 33291, 'value' : str(count['busy']) },
								{ 'title' : 33294, 'value' : str(count['finished']) },
								{ 'title' : 33295, 'value' : str(count['failed']) },
							]
						})

					# Limits
					if 'limits' in information:
						unlimited = interface.Translation.string(35221)
						limits = information['limits']
						items.append({
							'title' : 35220,
							'items' : [
								{ 'title' : 35222, 'value' : limits['links'] if limits['links'] > 0 else unlimited },
								{ 'title' : 33768, 'value' : limits['premium'] if limits['premium'] > 0 else unlimited },
								{ 'title' : 33199, 'value' : limits['torrents'] if limits['torrents'] > 0 else unlimited },
								{ 'title' : 33487, 'value' : limits['streaming'] if limits['streaming'] > 0 else unlimited },
								{ 'title' : 35206, 'value' : limits['cloud']['description'] },
								{ 'title' : 35223, 'value' : limits['proxy']['description'] },
							]
						})

					# Dialog
					interface.Loader.hide()
					interface.Dialog.information(title = title, items = items)
					return
			except:
				pass
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33352) % OffCloudInterface.Name)
		else:
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33351) % OffCloudInterface.Name)

	##############################################################################
	# DIRECTORY
	##############################################################################

	def directoryItemAction(self, item):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew
		link = item['link']

		items = [
			interface.Format.bold(interface.Translation.string(35083) + ': ') + interface.Translation.string(35086),
			interface.Format.bold(interface.Translation.string(33031) + ': ') + interface.Translation.string(35087),
			interface.Format.bold(interface.Translation.string(35085) + ': ') + interface.Translation.string(35088),
		]
		choice = interface.Dialog.select(title = 32009, items = items)
		if choice >= 0:
			if choice == 0: interface.Player.playNow(link)
			elif choice == 1: clipboard.Clipboard.copyLink(link, True)
			elif choice == 2: tools.System.openLink(link)

	def directoryItem(self, item):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew

		directory = interface.Directory(content = interface.Directory.ContentAddons)
		items = item['files']
		itemsNew = []

		for item in items:
			info = []
			icon = 'downloads.png'

			try: info.append(item['extension'].upper())
			except: pass

			try:
				if item['size']['bytes'] > 0:
					info.append(item['size']['description'])
			except: pass

			label = interface.Format.bold(item['name'])
			label += interface.Format.newline()
			label += ' | '.join(info)

			itemJson = tools.Converter.jsonTo(item)

			context = []
			context.append({'label' : 33371, 'command' : tools.System.commandPlugin(action = 'offcloudItemAction', parameters = {'item' : itemJson})})

			itemsNew.append({'item' : itemJson, 'label' : label, 'context' : context, 'icon' : icon})

		# Sort so that episodes show in ascending order.
		itemsNew.sort(key = lambda i: i['label'])

		for item in itemsNew:
			directory.add(label = item['label'], action = 'offcloudItemAction', parameters = {'item' : item['item']}, context = item['context'], folder = False, icon = item['icon'], iconDefault = 'DefaultAddonProgram.png')

		directory.finish()

	def directoryListAction(self, item, context = False):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew
		try: context = bool(context)
		except:	context = False

		id = item['id']
		category = item['category']

		actions = []
		items = []

		if item['status'] == OffCloud.StatusFinished:
			if category == OffCloud.CategoryInstant:
				actions.append('downloadbest')
				items.append(interface.Format.bold(interface.Translation.string(35154) + ': ') + interface.Translation.string(35155))
				actions.append('streambest')
				items.append(interface.Format.bold(interface.Translation.string(35083) + ': ') + interface.Translation.string(35086))
				actions.append('copybest')
				items.append(interface.Format.bold(interface.Translation.string(33031) + ': ') + interface.Translation.string(35087))
				actions.append('openbest')
				items.append(interface.Format.bold(interface.Translation.string(35085) + ': ') + interface.Translation.string(35088))
			else:
				actions.append('browsecontent')
				items.append(interface.Format.bold(interface.Translation.string(35089) + ': ') + interface.Translation.string(35094))
				actions.append('downloadbest')
				items.append(interface.Format.bold(interface.Translation.string(35249) + ': ') + interface.Translation.string(35253))
				actions.append('streambest')
				items.append(interface.Format.bold(interface.Translation.string(35250) + ': ') + interface.Translation.string(35254))
				actions.append('copybest')
				items.append(interface.Format.bold(interface.Translation.string(35251) + ': ') + interface.Translation.string(35255))
				actions.append('openbest')
				items.append(interface.Format.bold(interface.Translation.string(35252) + ': ') + interface.Translation.string(35256))

		actions.append('remove')
		items.append(interface.Format.bold(interface.Translation.string(35100) + ': ') + interface.Translation.string(35101))
		actions.append('refresh')
		items.append(interface.Format.bold(interface.Translation.string(35103) + ': ') + interface.Translation.string(35104))
		actions.append('cancel')
		items.append(interface.Format.bold(interface.Translation.string(35105) + ': ') + interface.Translation.string(35106))

		choice = interface.Dialog.select(title = 32009, items = items)
		if choice >= 0:
			choice = actions[choice]
			if choice == 'refresh':
				interface.Directory.refresh()
			elif not choice == 'cancel':
				hide = True
				interface.Loader.show()
				try:
					if choice == 'remove':
						self.mDebrid.delete(category = category, id = id)
						interface.Directory.refresh()
						hide = False # Already hidden by container refresh.
					else:
						item = self.mDebrid.item(category = category, id = id)
						if 'video' in item and not item['video'] == None:
							itemLink = item['video']['link']
							if choice == 'browsecontent':
								# Kodi cannot set the directory structure more than once in a single run.
								# If the action is launched directly by clicking on the item, Kodi seems to clear the structure so that you can create a new one.
								# This is not the case when the action menu is launched from the "Actions" option in the context menu.
								# Open the window externally. However, this will load longer and the back action is to the main menu.
								if context:
									itemJson = tools.Converter.jsonTo(item)
									tools.System.window(action = 'offcloudItem', parameters = {'item' : itemJson})
								else:
									self.directoryItem(item)
							elif choice == 'streambest':
								if network.Networker.linkIs(itemLink): interface.Player.playNow(itemLink)
								else: raise Exception('Invalid Best Link: ' + str(itemLink))
							elif choice == 'downloadbest':
								if network.Networker.linkIs(itemLink): downloader.Downloader(downloader.Downloader.TypeManual).download(media = downloader.Downloader.MediaOther, link = itemLink)
								else: raise Exception('Invalid Best Link: ' + str(itemLink))
							elif choice == 'copybest':
								if network.Networker.linkIs(itemLink): clipboard.Clipboard.copyLink(itemLink, True)
								else: raise Exception('Invalid Best Link: ' + str(itemLink))
							elif choice == 'openbest':
								if network.Networker.linkIs(itemLink): tools.System.openLink(itemLink)
								else: raise Exception('Invalid Best Link: ' + str(itemLink))
						else:
							interface.Dialog.notification(title = 35200, message = 35259, icon = interface.Dialog.IconError)
				except:
					tools.Logger.error()
					interface.Dialog.notification(title = 35200, message = 35257, icon = interface.Dialog.IconError)
				if hide: interface.Loader.hide()

	def directoryList(self, category = OffCloud.CategoryCloud):
		directory = interface.Directory(content = interface.Directory.ContentAddons)
		items = self.mDebrid.items(category = category)
		if not items: items = []
		itemsNew = [[], [], [], [], [], [], []]
		for item in items:
			info = []
			icon = None

			try: status = item['status']
			except: status = None

			if not status == None and not status == OffCloud.StatusUnknown:
				color = None
				if status == OffCloud.StatusError:
					color = interface.Format.ColorBad
					icon = 'downloadsfailed.png'
				elif status == OffCloud.StatusCanceled:
					color = interface.Format.ColorPoor
					icon = 'downloadsfailed.png'
				elif status == OffCloud.StatusQueued:
					color = interface.Format.ColorMedium
					icon = 'downloadsbusy.png'
				elif status == OffCloud.StatusInitialize:
					color = interface.Format.ColorGood
					icon = 'downloadsbusy.png'
				elif status == OffCloud.StatusBusy:
					color = interface.Format.ColorExcellent
					icon = 'downloadsbusy.png'
				elif status == OffCloud.StatusFinalize:
					color = interface.Format.ColorMain
					icon = 'downloadsbusy.png'
				elif status == OffCloud.StatusFinished:
					color = interface.Format.ColorSpecial
					icon = 'downloadscompleted.png'
				info.append(interface.Format.fontColor(status.capitalize(), color))

			if status == OffCloud.StatusBusy:
				try:
					colors = interface.Format.colorGradient(interface.Format.ColorMedium, interface.Format.ColorExcellent, 101) # One more, since it goes from 0 - 100
					percentage = int(item['transfer']['progress']['completed']['percentage'])
					info.append(interface.Format.fontColor('%d%%' % percentage, colors[percentage]))
				except:
					pass
				try:
					if item['transfer']['speed']['bits'] > 0:
						info.append(item['transfer']['speed']['description'])
				except: pass
				try:
					if item['transfer']['progress']['remaining']['time']['seconds'] > 0:
						info.append(item['transfer']['progress']['remaining']['time']['description'])
				except: pass

			try:
				if item['size']['bytes'] > 0:
					info.append(item['size']['description'])
			except: pass

			name = item['name']
			try:
				if item['directory']:
					info.append(interface.Translation.string(35258))
				else:
					extension = re.search('\.([a-zA-Z0-9]{3,4})$', item['name'], re.IGNORECASE).group(1).upper()
					info.append(extension)
					name = name[:-(len(extension) + 1)]
			except: pass
			if name == None: name = 'Unnamed Download'

			label = interface.Format.bold(name)
			label += interface.Format.newline()
			label += ' | '.join(info)

			itemJson = tools.Converter.jsonTo(item)

			context = []
			context.append({'label' : 32072, 'command' : 'Container.Refresh'})
			context.append({'label' : 33371, 'command' : tools.System.commandPlugin(action = 'offcloudListAction', parameters = {'item' : itemJson, 'context' : 1})})

			if status == OffCloud.StatusError: index = 0
			elif status == OffCloud.StatusCanceled: index = 1
			elif status == OffCloud.StatusQueued: index = 2
			elif status == OffCloud.StatusInitialize: index = 3
			elif status == OffCloud.StatusBusy: index = 4
			elif status == OffCloud.StatusFinalize: index = 5
			elif status == OffCloud.StatusFinished: index = 6
			else: index = 0

			itemsNew[index].append({'item' : itemJson, 'label' : label, 'context' : context, 'icon' : icon})

		for item in itemsNew:
			for i in item:
				directory.add(label = i['label'], action = 'offcloudListAction', parameters = {'item' : i['item']}, context = i['context'], folder = True, icon = i['icon'], iconDefault = 'DefaultAddonProgram.png')

		directory.finish()

############################################################################################################################################################
# REALDEBRID
############################################################################################################################################################

class RealDebrid(Debrid):

	# Service Statuses
	ServiceStatusUp = 'up'
	ServiceStatusDown = 'down'
	ServiceStatusUnsupported = 'unsupported'

	ServicesUpdate = None
	ServicesTorrent = [
		{	'name' : 'Torrent',		'id' : 'torrent',	'domain' : '',	'status' : ServiceStatusUp,	'supported' : True	},
	]

	#Links
	LinkMain = 'https://real-debrid.com'
	LinkApi = 'https://api.real-debrid.com/rest/1.0'
	LinkAuthentication = 'https://api.real-debrid.com/oauth/v2'

	# Modes
	ModeGet = 'get'
	ModePost = 'post'
	ModePut = 'put'
	ModeDelete = 'delete'

	# Types
	TypeTorrent = 'torrent'

	# Statuses
	StatusUnknown = 'unknown'
	StatusError = 'error'
	StatusMagnetError = 'magnet_error'
	StatusMagnetConversion = 'magnet_conversion'
	StatusFileSelection = 'waiting_files_selection'
	StatusQueued = 'queued'
	StatusBusy = 'downloading'
	StatusFinished = 'downloaded'
	StatusVirus = 'virus'
	StatusCompressing = 'compressing'
	StatusUploading = 'uploading'
	StatusDead = 'dead'

	# Categories
	CategoryUser = 'user'
	CategoryHosts = 'hosts'
	CategoryToken = 'token'
	CategoryDevice = 'device'
	CategoryUnrestrict = 'unrestrict'
	CategoryTorrents = 'torrents'
	CategoryTime = 'time'

	# Actions
	ActionStatus = 'status'
	ActionCode = 'code'
	ActionCredentials = 'credentials'
	ActionLink = 'link'
	ActionAddTorrent = 'addTorrent'
	ActionAddMagnet = 'addMagnet'
	ActionActive = 'activeCount'
	ActionInfo = 'info'
	ActionAvailableHosts = 'availableHosts'
	ActionSelectFiles = 'selectFiles'
	ActionDelete = 'delete'
	ActionInstantAvailability = 'instantAvailability'
	ActionDomains = 'domains'

	# Parameters
	ParameterClientId = 'client_id'
	ParameterClientSecret = 'client_secret'
	ParameterCode = 'code'
	ParameterGrantType = 'grant_type'
	ParameterNewCredentials = 'new_credentials'
	ParameterLink = 'link'
	ParameterMagnet = 'magnet'
	ParameterFiles = 'files'

	# Errors
	ErrorUnknown = 'unknown'
	ErrorInaccessible = 'inaccessible' # Eg: 404 error.
	ErrorUnavailable = 'unavailable' # When season pack does not contain a certain episode. Or if there is not usable file in the download.
	ErrorRealDebrid = 'realdebrid' # Error from RealDebrid server.
	ErrorBlocked = 'blocked' # User IP address blocked.
	ErrorSelection = 'selection' # No file selected from list of items.

	# Selection
	SelectionAll = 'all'
	SelectionName = 'name'
	SelectionLargest = 'largest'

	# Limits
	LimitLink = 2000 # Maximum length of a URL.
	LimitHashesGet = 40 # Maximum number of 40-character hashes to use in GET parameter so that the URL length limit is not exceeded.

	# Timeouts
	# Number of seconds the requests should be cached.
	TimeoutServices = 3 # 3 hour
	TimeoutAccount = 0.17 # 10 min

	# Time
	TimeOffset = 0

	# User Agent
	UserAgent = tools.System.name() + ' ' + tools.System.version()

	# Client
	ClientId = tools.System.obfuscate(tools.Settings.getString('internal.realdebrid.client', raw = True))
	ClientGrant = 'http://oauth.net/grant_type/device/1.0'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, debug = True):
		Debrid.__init__(self, 'RealDebrid')

		self._accountAuthenticationClear()
		self.mAuthenticationToken = self.accountToken()

		self.mDebug = debug
		self.mLinkBasic = None
		self.mLinkFull = None
		self.mParameters = None
		self.mSuccess = None
		self.mError = None
		self.mErrorCode = None
		self.mErrorDescription = None
		self.mResult = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _request(self, mode, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None, httpAuthenticate = True):
		self.mResult = None

		linkOriginal = link
		parametersOriginal = parameters
		httpDataOriginal = httpData

		def redo(mode, link, parameters, httpTimeout, httpData, httpHeaders, httpAuthenticate):
			if httpAuthenticate:
				tools.Logger.log('The RealDebrid token expired. Retrying the request with a refreshed token: ' + str(link))
				if self._accountAuthentication():
					httpHeaders['Authorization'] = 'Bearer %s' % self.mAuthenticationToken # Update token in headers.
					return self._request(mode = mode, link = link, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders, httpAuthenticate = False)
			return None

		try:
			if not httpTimeout:
				if httpData: httpTimeout = 60
				else: httpTimeout = 30

			self.mLinkBasic = link
			self.mParameters = parameters
			self.mSuccess = None
			self.mError = None
			self.mErrorCode = None
			self.mErrorDescription = None

			if mode == RealDebrid.ModeGet or mode == RealDebrid.ModePut or mode == RealDebrid.ModeDelete:
				if parameters:
					if not link.endswith('?'):
						link += '?'
					parameters = urllib.urlencode(parameters, doseq = True)
					link += parameters
			elif mode == RealDebrid.ModePost:
				if parameters:
					httpData = urllib.urlencode(parameters, doseq = True)

			self.mLinkFull = link

			if httpData: request = urllib2.Request(link, data = httpData)
			else: request = urllib2.Request(link)

			if mode == RealDebrid.ModePut or mode == RealDebrid.ModeDelete:
				request.get_method = lambda: mode.upper()

			request.add_header('User-Agent', RealDebrid.UserAgent)
			if httpHeaders:
				for key in httpHeaders:
					request.add_header(key, httpHeaders[key])

			response = urllib2.urlopen(request, timeout = httpTimeout)
			self.mResult = response.read()
			response.close()

			self.mResult = tools.Converter.jsonFrom(self.mResult, default = self.mResult)
			self.mSuccess = self._success(self.mResult)
			self.mError = self._error(self.mResult)

			if not self.mSuccess:
				if self.mError == 'bad_token' and httpAuthenticate:
					return redo(mode = mode, link = linkOriginal, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate)
				else:
					self._requestErrors('The call to the RealDebrid API failed', link, httpData, self.mResult)

		except (urllib2.HTTPError, urllib2.URLError) as error:
			self.mSuccess = False
			if hasattr(error, 'code'):
				errorCode = error.code
				errorString = ' ' + str(errorCode)
			else:
				errorCode = 0
				errorString = ''
			self.mError = 'RealDebrid Unavailable [HTTP/URL Error%s]' % errorString
			self._requestErrors(self.mError, link, httpData, self.mResult)
			try:
				errorApi = tools.Converter.jsonFrom(error.read())
				self.mErrorCode = errorApi['error_code']
				self.mErrorDescription = errorApi['error']
			except: pass
			if self.mErrorDescription == 'bad_token' or errorCode == 401:
				return redo(mode = mode, link = linkOriginal, parameters = parametersOriginal, httpTimeout = httpTimeout, httpData = httpDataOriginal, httpHeaders = httpHeaders, httpAuthenticate = httpAuthenticate)
			elif not self.mErrorDescription == None:
				if 'ip_not_allowed' in self.mErrorDescription:
					interface.Dialog.closeAllProgress() # The stream connection progress dialog is still showing.
					interface.Dialog.confirm(title = 33567, message = 35060)
					self.mErrorCode = RealDebrid.ErrorBlocked
		except Exception as error:
			self.mSuccess = False
			self.mError = 'Unknown Error'
			try:
				self.mErrorCode = 0
				self.mErrorDescription = str(error)
			except: pass
			self._requestErrors(self.mError, link, httpData, self.mResult)

		return self.mResult

	def _requestErrors(self, message, link, payload, result = None):
		if self.mDebug:
			try: link = str(link)
			except: link = ''
			try: payload = str(payload) if len(str(payload)) < 300 else 'Payload too large to display'
			except: payload = ''
			try: result = str(result)
			except: result = ''
			tools.Logger.error(str(message) + (': Link [%s] Payload [%s] Result [%s]' % (link, payload, result)))

	def _requestAuthentication(self, mode, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None):
		if not parameters:
			parameters = {}
		if not httpHeaders:
			httpHeaders = {}
		httpHeaders['Authorization'] = 'Bearer %s' % self.mAuthenticationToken
		return self._request(mode = mode, link = link, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders)

	def _retrieve(self, mode, category, action = None, id = None, link = None, magnet = None, files = None, hashes = None, httpTimeout = None, httpData = None, httpHeaders = None):
		linkApi = network.Networker.linkJoin(RealDebrid.LinkApi, category, action)
		if not id == None: linkApi = network.Networker.linkJoin(linkApi, id)

		if not hashes == None:
			for hash in hashes:
				linkApi = network.Networker.linkJoin(linkApi, hash)

		parameters = {}
		if not link == None: parameters[RealDebrid.ParameterLink] = link
		if not magnet == None: parameters[RealDebrid.ParameterMagnet] = magnet
		if not files == None: parameters[RealDebrid.ParameterFiles] = files

		return self._requestAuthentication(mode = mode, link = linkApi, parameters = parameters, httpTimeout = httpTimeout, httpData = httpData, httpHeaders = httpHeaders)

	##############################################################################
	# SUCCESS
	##############################################################################

	def _success(self, result):
		if isinstance(result, dict): return not 'error' in result
		else: return not result == None and not result == ''

	def _error(self, result):
		if isinstance(result, dict): return result['error'] if 'error' in result else None
		else: return None

	def success(self):
		return self.mSuccess

	def error(self):
		return self.mError

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.realdebrid', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def _accountAuthenticationClear(self):
		self.mAuthenticationLink = None
		self.mAuthenticationUser = None
		self.mAuthenticationDevice = None
		self.mAuthenticationInterval = None
		self.mAuthenticationId = None
		self.mAuthenticationSecret = None
		self.mAuthenticationToken = None
		self.mAuthenticationRefresh = None
		self.mAuthenticationUsername = None

	def _accountAuthenticationSettings(self):
		id = '' if self.mAuthenticationId == None else self.mAuthenticationId
		secret = '' if self.mAuthenticationSecret == None else self.mAuthenticationSecret
		token = '' if self.mAuthenticationToken == None else self.mAuthenticationToken
		refresh = '' if self.mAuthenticationRefresh == None else self.mAuthenticationRefresh
		authentication = ''
		if not self.mAuthenticationToken == None:
			if self.mAuthenticationUsername == None or self.mAuthenticationUsername == '':
				authentication = interface.Format.FontPassword
			else:
				authentication = self.mAuthenticationUsername

		tools.Settings.set('accounts.debrid.realdebrid.id', id)
		tools.Settings.set('accounts.debrid.realdebrid.secret', secret)
		tools.Settings.set('accounts.debrid.realdebrid.token', token)
		tools.Settings.set('accounts.debrid.realdebrid.refresh', refresh)
		tools.Settings.set('accounts.debrid.realdebrid.auth', authentication)

	def _accountAuthentication(self):
		try:
			link = network.Networker.linkJoin(RealDebrid.LinkAuthentication, RealDebrid.CategoryToken)
			parameters = {
				RealDebrid.ParameterClientId : self.accountId(),
				RealDebrid.ParameterClientSecret : self.accountSecret(),
				RealDebrid.ParameterCode : self.accountRefresh(),
				RealDebrid.ParameterGrantType : RealDebrid.ClientGrant
			}

			result = self._request(mode = RealDebrid.ModePost, link = link, parameters = parameters, httpTimeout = 20, httpAuthenticate = False)

			if not result or 'error' in result or not 'access_token' in result:
				return False

			self.mAuthenticationToken = result['access_token']
			tools.Settings.set('accounts.debrid.realdebrid.token', self.mAuthenticationToken)
			return True
		except:
			return False

	def accountAuthenticationLink(self):
		return self.mAuthenticationLink

	def accountAuthenticationCode(self):
		return self.mAuthenticationUser

	def accountAuthenticationInterval(self):
		return self.mAuthenticationInterval

	def accountAuthenticationReset(self, save = True):
		self._accountAuthenticationClear()
		if save: self._accountAuthenticationSettings()

	def accountAuthenticationStart(self):
		self._accountAuthenticationClear()

		try:
			link = network.Networker.linkJoin(RealDebrid.LinkAuthentication, RealDebrid.CategoryDevice, RealDebrid.ActionCode)
			parameters = {
				RealDebrid.ParameterClientId : RealDebrid.ClientId,
				RealDebrid.ParameterNewCredentials : 'yes'
			}

			result = self._request(mode = RealDebrid.ModeGet, link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)

			self.mAuthenticationLink = result['verification_url']
			self.mAuthenticationUser = result['user_code']
			self.mAuthenticationDevice = result['device_code']
			self.mAuthenticationInterval = result['interval']

			return True
		except:
			tools.Logger.error()

		return False

	def accountAuthenticationWait(self):
		try:
			link = network.Networker.linkJoin(RealDebrid.LinkAuthentication, RealDebrid.CategoryDevice, RealDebrid.ActionCredentials)
			parameters = {
				RealDebrid.ParameterClientId : RealDebrid.ClientId,
				RealDebrid.ParameterCode : self.mAuthenticationDevice
			}

			result = self._request(mode = RealDebrid.ModeGet, link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)

			if 'client_secret' in result:
				self.mAuthenticationId = result['client_id']
				self.mAuthenticationSecret = result['client_secret']
				return True
		except:
			pass

		return False

	def accountAuthenticationFinish(self):
		try:
			link = network.Networker.linkJoin(RealDebrid.LinkAuthentication, RealDebrid.CategoryToken)
			parameters = {
				RealDebrid.ParameterClientId : self.mAuthenticationId,
				RealDebrid.ParameterClientSecret : self.mAuthenticationSecret,
				RealDebrid.ParameterCode : self.mAuthenticationDevice,
				RealDebrid.ParameterGrantType : RealDebrid.ClientGrant
			}

			result = self._request(mode = RealDebrid.ModePost, link = link, parameters = parameters, httpTimeout = 30, httpAuthenticate = False)

			if 'access_token' in result and 'refresh_token' in result:
				self.mAuthenticationToken = result['access_token']
				self.mAuthenticationRefresh = result['refresh_token']

				try:
					account = self.account()
					self.mAuthenticationUsername = account['user']
					if self.mAuthenticationUsername == None or self.mAuthenticationUsername == '':
						self.mAuthenticationUsername = account['email']
				except:
					self.mAuthenticationUsername = None

				self._accountAuthenticationSettings()
				return True
		except:
			tools.Logger.error()

		return False

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.realdebrid.enabled')

	def accountValid(self):
		return not self.accountId() == '' and not self.accountSecret() == '' and not self.accountToken() == '' and not self.accountRefresh() == ''

	def accountId(self):
		return tools.Settings.getString('accounts.debrid.realdebrid.id') if self.accountEnabled() else ''

	def accountSecret(self):
		return tools.Settings.getString('accounts.debrid.realdebrid.secret') if self.accountEnabled() else ''

	def accountToken(self):
		return tools.Settings.getString('accounts.debrid.realdebrid.token') if self.accountEnabled() else ''

	def accountRefresh(self):
		return tools.Settings.getString('accounts.debrid.realdebrid.refresh') if self.accountEnabled() else ''

	def accountVerify(self):
		return not self.account(cache = False) == None

	def account(self, cache = True):
		try:
			if self.accountValid():
				timeout = RealDebrid.TimeoutAccount if cache else 0
				def __realdebridAccount(): # Must have a different name than the tools.Cache.cache call for the hoster list. Otherwise the cache returns the result for the hosters instead of the account.
					return self._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryUser)
				result = tools.Cache.cache(__realdebridAccount, timeout)

				#if not self.success(): # Do not use this, since it will be false for cache calls.
				if result and isinstance(result, dict) and 'id' in result and result['id']:
					expiration = result['expiration']
					index = expiration.find('.')
					if index >= 0: expiration = expiration[:index]
					expiration = expiration.strip().lower().replace('t', ' ')
					expiration = tools.Time.datetime(expiration, '%Y-%m-%d %H:%M:%S')

					return {
						'user' : result['username'],
						'id' : result['id'],
						'email' : result['email'],
						'type' : result['type'],
						'locale' : result['locale'],
						'points' : result['points'],
						'expiration' : {
							'timestamp' : tools.Time.timestamp(expiration),
							'date' : expiration.strftime('%Y-%m-%d %H:%M:%S'),
							'remaining' : (expiration - datetime.datetime.today()).days
						}
					}
				else:
					return None
			else:
				return None
		except:
			tools.Logger.error()
			return None

	##############################################################################
	# SERVICES
	##############################################################################

	# If available is False, will return all services, including those that are currently down.
	def services(self, available = True, cache = True, onlyEnabled = False):
		# Even thow ServicesUpdate is a class variable, it will be destrcucted if there are no more Premiumize instances.
		if RealDebrid.ServicesUpdate == None:
			RealDebrid.ServicesUpdate = []

			streamingTorrent = self.streamingTorrent()
			streamingHoster = self.streamingHoster()

			try:
				# NB: The /hosts/status always throws errors, sometimes 401 errors, sometimes unknow errors. Just use /hosts

				'''
				timeout = RealDebrid.TimeoutServices if cache else 0
				def __realdebridHosters():# Must have a different name than the tools.Cache.cache call for the account details. Otherwise the cache returns the result for the account instead of the hosters.
					return self._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryHosts, action = RealDebrid.ActionStatus)
				result = tools.Cache.cache(__realdebridHosters, timeout)

				for service in RealDebrid.ServicesTorrent:
					service['enabled'] = streamingTorrent
					RealDebrid.ServicesUpdate.append(service)

				if not result == None:
					for key, value in result.iteritems():
						if not available or value['status'] == RealDebrid.ServiceStatusUp:
							RealDebrid.ServicesUpdate.append({
								'name' : value['name'],
								'id' : key.lower(),
								'identifier' : value['id'],
								'enabled' : streamingHoster,
								'domain' : key,
								'status' : value['status'],
								'supported' : value['supported'] == 1,
							})
				'''

				timeout = RealDebrid.TimeoutServices if cache else 0
				def __realdebridHosters():# Must have a different name than the tools.Cache.cache call for the account details. Otherwise the cache returns the result for the account instead of the hosters.
					return self._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryHosts)
				result = tools.Cache.cache(__realdebridHosters, timeout)

				for service in RealDebrid.ServicesTorrent:
					service['enabled'] = streamingTorrent
					RealDebrid.ServicesUpdate.append(service)

				if not result == None:
					for key, value in result.iteritems():
						RealDebrid.ServicesUpdate.append({
							'name' : value['name'],
							'id' : key.lower(),
							'identifier' : value['id'],
							'enabled' : streamingHoster,
							'domain' : key,
							'status' : 'up',
							'supported' : True,
						})

			except:
				tools.Logger.error()

		if onlyEnabled:
			return [i for i in RealDebrid.ServicesUpdate if i['enabled']]
		else:
			return RealDebrid.ServicesUpdate

	def servicesDomains(self, cache = True):
		timeout = RealDebrid.TimeoutServices if cache else 0
		def __realdebridDomains():# Must have a different name than the tools.Cache.cache call for the account details. Otherwise the cache returns the result for the account instead of the hosters.
			return self._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryHosts, action = RealDebrid.ActionDomains)
		return tools.Cache.cache(__realdebridDomains, timeout)

	def servicesList(self, onlyEnabled = False, domains = True):
		services = self.services(onlyEnabled = onlyEnabled)
		services = [service['id'] for service in services]
		if domains:
			try: services.extend(self.servicesDomains())
			except: tools.Logger.error()
		return list(set(services))

	def service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		for service in self.services():
			if service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain:
				return service
		return None

	##############################################################################
	# ADD
	##############################################################################

	def _addLink(self, result):
		try: id = result['id']
		except: id = None
		try: link = result['download']
		except: link = None
		return self.addResult(id = id, link = link)

	def add(self, link, title = None, season = None, episode = None, pack = False, source = None):
		container = network.Container(link)
		if source == network.Container.TypeTorrent:
			type = network.Container.TypeTorrent
		else:
			type = container.type()
		if type == network.Container.TypeTorrent:
			try:
				hash = container.hash()
				if not hash: raise Exception()
				exisitng = self._itemHash(hash, season = season, episode = episode)
				if not exisitng: raise Exception()
				return self._addLink(exisitng)
			except:
				return self.addTorrent(link = link, title = title, season = season, episode = episode)
		else:
			return self.addHoster(link)

	def addContainer(self, link, title = None):
		try:
			source = network.Container(link).information()
			if source['path'] == None and source['data'] == None:
				return RealDebrid.ErrorInaccessible

			data = source['data']
			result = self._retrieve(mode = RealDebrid.ModePut, category = RealDebrid.CategoryTorrents, action = RealDebrid.ActionAddTorrent, httpData = data)

			if self.success() and 'id' in result: return self._addLink(result)
			elif self.mErrorCode == RealDebrid.ErrorBlocked: return self.addResult(error = RealDebrid.ErrorBlocked, notification = True)
			else: return self.addResult(error = RealDebrid.ErrorRealDebrid)
		except:
			tools.Logger.error()
			return self.addResult(error = RealDebrid.ErrorRealDebrid)

	def addHoster(self, link):
		result = self._retrieve(mode = RealDebrid.ModePost, category = RealDebrid.CategoryUnrestrict, action = RealDebrid.ActionLink, link = link)
		if self.success() and 'download' in result: return self._addLink(result)
		elif self.mErrorCode == RealDebrid.ErrorBlocked: return self.addResult(error = RealDebrid.ErrorBlocked, notification = True)
		else: return self.addResult(error = RealDebrid.ErrorRealDebrid)

	def addTorrent(self, link, title = None, season = None, episode = None):
		container = network.Container(link)
		source = container.information()
		if source['magnet']:
			magnet = container.torrentMagnet(title = title, encode = False)
			result = self._retrieve(mode = RealDebrid.ModePost, category = RealDebrid.CategoryTorrents, action = RealDebrid.ActionAddMagnet, magnet = magnet)
			if self.success() and 'id' in result: return self._addLink(result)
			elif self.mErrorCode == RealDebrid.ErrorBlocked: return self.addResult(error = RealDebrid.ErrorBlocked, notification = True)
			else: return self.addResult(error = RealDebrid.ErrorRealDebrid)
		else:
			return self.addContainer(link = link, title = title)

	##############################################################################
	# SELECT
	##############################################################################

	# Selects the files in the torrent to download.
	# files can be an id, a list of ids, or a Selection type.
	def selectList(self, id, files = None, item = None, season = None, episode = None, manual = False):
		if manual:
			if item == None: item = self.item(id)
			items = {}
			items['items'] = item
			items['link'] = None
			items['selection'] = None
			return items
		else:
			result = None
			largest = None
			try:
				if files == RealDebrid.SelectionAll:
					result = RealDebrid.SelectionAll
				elif files == RealDebrid.SelectionName:
					if item == None: item = self.item(id)
					meta = metadata.Metadata()
					if item and 'files' in item:
						for file in item['files']:
							if meta.episodeContains(title = file['path'], season = season, episode = episode):
								if largest == None or file['size']['bytes'] > largest['size']['bytes']:
									largest = file
					if largest == None:
						return result
					else:
						result = str(largest['id'])
				elif files == RealDebrid.SelectionLargest:
					if item == None:
						item = self.item(id)
					if item and 'files' in item:
						largestId = None
						largestSize = 0
						for file in item['files']:
							size = file['size']['bytes']
							if size > largestSize:
								largestSize = size
								largestId = file['id']
								largest = file
						if largestId == None:
							return result
						else:
							result = str(largestId)
					else:
						return Debrid.ErrorUnavailable
				elif not isinstance(files, basestring):
					if isinstance(files, list):
						result = ','.join(files)
					else:
						result = str(files)
			except:
				pass

			items = {}
			items['items'] = item
			items['link'] = largest['link'] if largest and 'link' in largest else None
			items['selection'] = result
			return items

	# Selects the files in the torrent to download.
	# files can be an id, a list of ids, or a Selection type.
	def select(self, id, files, item = None, season = None, episode = None):
		try:
			items = self.selectList(id = id, files = files, item = item, season = season, episode = episode)
			if items == None or items['selection'] == None: return Debrid.ErrorUnavailable
			result = self._retrieve(mode = RealDebrid.ModePost, category = RealDebrid.CategoryTorrents, action = RealDebrid.ActionSelectFiles, id = id, files = items['selection'])
			if self.success(): return True
			else: return RealDebrid.ErrorRealDebrid
		except:
			# If there are no seeders and RealDebrid cannot retrieve a list of files.
			return RealDebrid.ErrorRealDebrid

	def selectAll(self, id):
		return self.select(id = id, files = RealDebrid.SelectionAll)

	def selectName(self, id, item = None, season = None, episode = None):
		return self.select(id = id, files = RealDebrid.SelectionName, item = item, season = season, episode = episode)

	def selectLargest(self, id, item = None):
		return self.select(id = id, files = RealDebrid.SelectionLargest, item = item)

	def selectManualInitial(self, id, item = None):
		try:
			items = self.selectList(id = id, item = item, manual = True)
			if items == None or items['items'] == None: return Debrid.ErrorUnavailable
			else: return items
		except:
			# If there are no seeders and RealDebrid cannot retrieve a list of files.
			return RealDebrid.ErrorRealDebrid

	def selectManualFinal(self, id, selection):
		try:
			self._retrieve(mode = RealDebrid.ModePost, category = RealDebrid.CategoryTorrents, action = RealDebrid.ActionSelectFiles, id = id, files = str(selection))
			if self.success() or self.mError == 'action_already_done': return True
			else: return RealDebrid.ErrorRealDebrid
		except:
			# If there are no seeders and RealDebrid cannot retrieve a list of files.
			return RealDebrid.ErrorRealDebrid

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {Debrid.ModeTorrent}

	# id: single hash or list of hashes.
	def cachedIs(self, id, timeout = None):
		result = self.cached(id = id, timeout = timeout)
		if isinstance(result, dict): return result['cached']
		elif isinstance(result, list): return[i['cached'] for i in result]
		else: return False

	# id: single hash or list of hashes.
	def cached(self, id, timeout = None, callback = None, sources = None):
		single = isinstance(id, basestring)
		if single: id = [id] # Must be passed in as a list.

		# A URL has a maximum length, so the hashes have to be split into parts and processes independently, in order not to exceed the URL limit.
		chunks = [id[i:i + RealDebrid.LimitHashesGet] for i in xrange(0, len(id), RealDebrid.LimitHashesGet)]
		if sources: chunksSources = [sources[i:i + RealDebrid.LimitHashesGet] for i in xrange(0, len(sources), RealDebrid.LimitHashesGet)]
		else: chunksSources = None

		self.tCacheLock = threading.Lock()
		self.tCacheResult = {}
		def cachedChunk(callback, hashes, sources, timeout):
			realdebrid = RealDebrid()
			result = realdebrid._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryTorrents, action = RealDebrid.ActionInstantAvailability, hashes = hashes, httpTimeout = timeout)
			if realdebrid.success():
				for key, value in result.iteritems():
					key = key.upper()
					result = False
					try:
						files = []
						value = value['rd']
						for group in value:
							# NG says that season packs can be properley detected in the new RD API.
							# For now, include torrents with multiple files.
							#if len(group.keys()) == 1: # More than 1 file means the unrestricted link will be a RAR file.
								for fileKey, fileValue in group.iteritems():
									if tools.Video.extensionValid(path = fileValue['filename']):
										files.append(fileValue['filename'])
						if len(files) > 0:
							if sources:
								source = sources[hashes.index(key)]
								if source['metadata'].pack() or (source['metadata'].isEpisode() and len(files) > 1):
									for file in files:
										meta = metadata.Metadata(name = file, title = source['metadata'].title(raw = True), season = source['metadata'].season(), episode = source['metadata'].episode()) # Do not add pack here, since these are individual files.
										if not meta.ignore(size = False, seeds = False):
											result = True
								else:
									result = True
							else:
								result = True
					except:
						pass

					self.tCacheLock.acquire()
					self.tCacheResult[key] = result
					self.tCacheLock.release()
					if callback:
						try: callback(self.id(), key, result)
						except: pass

		threads = []
		for i in range(len(chunks)):
			try: thread = threading.Thread(target = cachedChunk, args = (callback, chunks[i], chunksSources[i], timeout))
			except: thread = threading.Thread(target = cachedChunk, args = (callback, chunks[i], None, timeout))
			threads.append(thread)
			thread.start()

		[i.join() for i in threads]
		if not callback:
			caches = []
			for key, value in self.tCacheResult.iteritems():
				caches.append({'id' : key, 'hash' : key, 'cached' : value})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches

	##############################################################################
	# DELETE
	##############################################################################

	# Check if the file can be deleted.
	@classmethod
	def deletePossible(self, source):
		from resources.lib.extensions import handler
		source = source.lower()
		return source == handler.Handler.TypeTorrent or source == handler.HandleRealDebrid().id()

	def delete(self, id):
		result = self._retrieve(mode = RealDebrid.ModeDelete, category = RealDebrid.CategoryTorrents, action = RealDebrid.ActionDelete, id = id)
		if self.success():
			return True
		else:
			return RealDebrid.ErrorRealDebrid

	def deleteAll(self, wait = True):
		items = self.items()
		if isinstance(items, list):
			if len(items) > 0:
				def _deleteAll(id):
					RealDebrid().delete(id)
				threads = []
				for item in items:
					threads.append(threading.Thread(target = _deleteAll, args = (item['id'],)))

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
			return RealDebrid.ErrorRealDebrid

	def _deleteSingle(self, hashOrLink):
		id = None
		items = self.items()
		if network.Networker.linkIs(hashOrLink):
			for item in items:
				if item['link'] == hashOrLink:
					id = item['id']
		else:
			hashOrLink = hashOrLink.lower()
			for item in items:
				if item['hash'].lower() == hashOrLink:
					id = item['id']
			if id == None: # If RealDebrid ID was passed instead of hash.
				id = hashOrLink

		if id == None: return False
		self.delete(id)
		return True

	# Delete an item and its corresponding transfer based on the link or hash.
	def deleteSingle(self, hashOrLink, wait = True):
		thread = threading.Thread(target = self._deleteSingle, args = (hashOrLink,))
		thread.start()
		if wait: thread.join()
		return True

	# Delete on launch
	def deleteLaunch(self):
		try:
			if tools.Settings.getBoolean('accounts.debrid.realdebrid.removal'):
				option = tools.Settings.getInteger('accounts.debrid.realdebrid.removal.launch')
				if option == 1:
					self.deleteAll(wait = False)
		except:
			pass

	# Delete on playback ended
	def deletePlayback(self, hashOrLink):
		try:
			if tools.Settings.getBoolean('accounts.debrid.realdebrid.removal'):
				option = tools.Settings.getInteger('accounts.debrid.realdebrid.removal.playback')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2:
					self.deleteSingle(hashOrLink, wait = False)
		except:
			pass

	# Delete on failure
	def deleteFailure(self, hashOrLink):
		try:
			if tools.Settings.getBoolean('accounts.debrid.realdebrid.removal'):
				option = tools.Settings.getInteger('accounts.debrid.realdebrid.removal.failure')
				if option == 1:
					self.deleteAll(wait = False)
				elif option == 2:
					self.deleteSingle(hashOrLink, wait = False)
		except:
			pass

	##############################################################################
	# TIME
	##############################################################################

	def timeOffset(self):
		def __realdebridTime():
			timeServer = self._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryTime)
			timeServer = convert.ConverterTime(timeServer, format = convert.ConverterTime.FormatDateTime).timestamp()
			timeUtc = tools.Time.timestamp()
			timeOffset = timeServer - timeUtc
			RealDebrid.TimeOffset = int(3600 * round(timeOffset / float(3600))) # Round to the nearest hour
			return RealDebrid.TimeOffset
		return tools.Cache.cache(__realdebridTime, 43200)

	##############################################################################
	# ITEMS
	##############################################################################

	def _itemHash(self, hash, season = None, episode = None):
		try:
			hash = hash.lower()
			items = self.items()
			meta = metadata.Metadata()
			for item in items:
				if item['hash'].lower() == hash:
					# Also check for the season/episode for season packs.
					# Otherwise RealDebrid will always return the first ever episode downloaded in the pack, since the hash for the torrent is the same.
					# Force to download again, if the episode does not match, that is a different episode is selected from the season pack.
					if meta.episodeContains(title = item['name'], season = season, episode = episode):
						return item
		except:
			pass
		return None

	def _item(self, dictionary):
		result = {}
		try:
			status = dictionary['status']
			sizeBytes = dictionary['bytes']
			if sizeBytes == 0: # Seems to be a bug in RealDebrid that sometimes the size shows up as 0. Use the largest file instead.
				if 'files' in dictionary:
					for file in dictionary['files']:
						size = file['bytes']
						if size > sizeBytes: sizeBytes = size
				if sizeBytes == 0 and 'original_bytes' in dictionary:
					sizeBytes = dictionary['original_bytes']
			size = convert.ConverterSize(value = sizeBytes, unit = convert.ConverterSpeed.Byte)

			split = convert.ConverterSize(value = dictionary['split'], unit = convert.ConverterSpeed.ByteGiga)
			speed = convert.ConverterSpeed(value = dictionary['speed'] if 'speed' in dictionary else 0, unit = convert.ConverterSpeed.Byte)

			offset = self.timeOffset()
			started = convert.ConverterTime(value = dictionary['added'], format = convert.ConverterTime.FormatDateTimeJson, offset = offset)
			if 'ended' in dictionary:
				finished = convert.ConverterTime(value = dictionary['ended'], format = convert.ConverterTime.FormatDateTimeJson, offset = offset)
				# RealDebrid seems to do caching in the background. In such a case, the finished time might be before the started time, since it was previously downloaded by another user.
				if finished.timestamp() < started.timestamp():
					finished = started
			else:
				finished = None

			seeders = dictionary['seeders'] if 'seeders' in dictionary else 0

			completedProgress = dictionary['progress'] / 100.0
			completedBytes = int(sizeBytes * completedProgress)
			completedSize = convert.ConverterSize(value = completedBytes, unit = convert.ConverterSpeed.Byte)
			if finished == None:
				difference = tools.Time.timestamp() - started.timestamp()
			else: difference = finished.timestamp() - started.timestamp()
			completedDuration = convert.ConverterDuration(value = difference, unit = convert.ConverterDuration.UnitSecond)
			completedSeconds = completedDuration.value(convert.ConverterDuration.UnitSecond)

			remainingProgress = 1 - completedProgress
			remainingBytes = sizeBytes - completedBytes
			remainingSize = convert.ConverterSize(value = remainingBytes, unit = convert.ConverterSpeed.Byte)
			remainingSeconds = int(remainingBytes * (completedSeconds / float(completedBytes))) if completedBytes > 0 else 0
			remainingDuration = convert.ConverterDuration(value = remainingSeconds, unit = convert.ConverterDuration.UnitSecond)

			result = {
				'id' : dictionary['id'],
				'hash' : dictionary['hash'],
				'name' : dictionary['filename'],
				'type' : RealDebrid.TypeTorrent,
				'status' : status,
				'host' : dictionary['host'],
				'time' : {
					'started' : started.string(convert.ConverterTime.FormatDateTime),
					'finished' : finished.string(convert.ConverterTime.FormatDateTime) if finished else None
				},
				'size' : {
					'bytes' : size.value(),
					'description' : size.stringOptimal()
				},
				'split' : {
					'bytes' : split.value(),
					'description' : split.stringOptimal()
				},
				'transfer' : {
					'speed' : {
						'bytes' : speed.value(convert.ConverterSpeed.Byte),
						'bits' : speed.value(convert.ConverterSpeed.Bit),
						'description' : speed.stringOptimal()
					},
					'torrent' : {
						'seeding' : status == RealDebrid.StatusUploading,
						'seeders' : seeders,
					},
					'progress' : {
						'completed' : {
							'value' : completedProgress,
							'percentage' : int(completedProgress * 100),
							'size' : {
								'bytes' : completedSize.value(),
								'description' : completedSize.stringOptimal()
							},
							'time' : {
								'seconds' : completedDuration.value(convert.ConverterDuration.UnitSecond),
								'description' : completedDuration.string(convert.ConverterDuration.FormatDefault)
							}
						},
						'remaining' : {
							'value' : remainingProgress,
							'percentage' : int(remainingProgress * 100),
							'size' : {
								'bytes' : remainingSize.value(),
								'description' : remainingSize.stringOptimal()
							},
							'time' : {
								'seconds' : remainingDuration.value(convert.ConverterDuration.UnitSecond),
								'description' : remainingDuration.string(convert.ConverterDuration.FormatDefault)
							}
						}
					}
				}
			}

			# Link
			if 'links' in dictionary and len(dictionary['links']) > 0:
				result['link'] = dictionary['links'][0]
			else:
				result['link'] = None

			# Files
			if 'files' in dictionary and len(dictionary['files']) > 0:
				files = []
				for file in dictionary['files']:
					size = convert.ConverterSize(value = file['bytes'], unit = convert.ConverterSpeed.Byte)

					name = file['path']
					index = name.rfind('/')
					if index >= 0: name = name[index + 1:]

					files.append({
						'id' : file['id'],
						'path' : file['path'],
						'name' : name,
						'selected' : tools.Converter.boolean(file['selected']),
						'size' : {
							'bytes' : size.value(),
							'description' : size.stringOptimal()
						}
					})
				result['files'] = files
			else:
				result['files'] = None

		except:
			tools.Logger.error()
			pass
		return result

	def items(self):
		results = self._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryTorrents)
		if self.success():
			items = []
			for result in results:
				items.append(self._item(result))
			return items
		else:
			return RealDebrid.ErrorRealDebrid

	def item(self, id):
		result = self._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryTorrents, action = RealDebrid.ActionInfo, id = id)
		if self.success():
			return self._item(result)
		else:
			return RealDebrid.ErrorRealDebrid

	##############################################################################
	# DOWNLOAD
	##############################################################################

	# Number of torrent download slots available.
	def downloadSlots(self):
		results = self._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryTorrents, action = RealDebrid.ActionActive)
		if self.success():
			try: return results['limit'] - results['nb']
			except: return 0
		else:
			return RealDebrid.ErrorRealDebrid

	def downloadHosts(self):
		results = self._retrieve(mode = RealDebrid.ModeGet, category = RealDebrid.CategoryTorrents, action = RealDebrid.ActionAvailableHosts)
		if self.success():
			items = []
			for result in results:
				size = convert.ConverterSize(value = result['max_file_size'], unit = convert.ConverterSpeed.ByteGiga)
				items.append({
					'domain' : result['host'],
					'size' : {
						'bytes' : size.value(),
						'description' : size.stringOptimal()
					}
				})
			return items
		else:
			return RealDebrid.ErrorRealDebrid

	def downloadInformation(self):
		items = self.items()
		if isinstance(items, list):
			count = len(items)
			countBusy = 0
			countFinished = 0
			countFailed = 0
			size = 0
			for item in items:
				size += item['size']['bytes']
				status = item['status']
				if status in [RealDebrid.StatusUnknown, RealDebrid.StatusError, RealDebrid.StatusMagnetConversion, RealDebrid.StatusVirus, RealDebrid.StatusDead]:
					countFailed += 1
				elif status in [RealDebrid.StatusFinished, RealDebrid.StatusUploading]:
					countFinished += 1
				else:
					countBusy += 1
			size = convert.ConverterSize(value = size, unit = convert.ConverterSize.Byte)

			result = {
				'count' : {
					'total' : count,
					'busy' : countBusy,
					'finished' : countFinished,
					'failed' : countFailed,
				},
				'size' : {
					'bytes' : size.value(),
					'description' : size.stringOptimal()
				}
			}

			hosts = self.downloadHosts()
			if isinstance(hosts, list) and len(hosts) > 0:
				result['host'] = hosts[0]

			return result
		else:
			return RealDebrid.ErrorRealDebrid

class RealDebridInterface(object):

	Name = 'RealDebrid'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		self.mDebrid = RealDebrid()

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self):
		interface.Loader.show()
		valid = False
		title = RealDebridInterface.Name + ' ' + interface.Translation.string(33339)
		if self.mDebrid.accountEnabled():
			account = self.mDebrid.account(cache = False)
			if account:
				valid = interface.Translation.string(33341) if self.mDebrid.accountValid() else interface.Translation.string(33342)
				user = account['user']
				id = str(account['id'])
				email = account['email']
				type = account['type'].capitalize()
				points = str(account['points'])

				date = account['expiration']['date']
				days = str(account['expiration']['remaining'])

				items = []

				# Information
				items.append({
					'title' : 33344,
					'items' : [
						{ 'title' : 33340, 'value' : valid },
						{ 'title' : 32305, 'value' : id },
						{ 'title' : 32303, 'value' : user },
						{ 'title' : 32304, 'value' : email },
						{ 'title' : 33343, 'value' : type },
						{ 'title' : 33349, 'value' : points }
					]
				})

				# Expiration
				items.append({
					'title' : 33345,
					'items' : [
						{ 'title' : 33346, 'value' : date },
						{ 'title' : 33347, 'value' : days }
					]
				})

				# Dialog
				interface.Loader.hide()
				interface.Dialog.information(title = title, items = items)
			else:
				interface.Loader.hide()
				interface.Dialog.confirm(title = title, message = interface.Translation.string(33352) % RealDebridInterface.Name)
		else:
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33351) % RealDebridInterface.Name)

		return valid

	def accountAuthentication(self, openSettings = True):
		interface.Loader.show()
		try:
			if self.mDebrid.accountValid():
				if interface.Dialog.option(title = RealDebridInterface.Name, message = 33492):
					self.mDebrid.accountAuthenticationReset(save = False)
				else:
					return None

			self.mDebrid.accountAuthenticationStart()

			# Link and token on top for skins that don't scroll text in a progress dialog.
			message = ''
			message += interface.Format.fontBold(interface.Translation.string(33381) + ': ' + self.mDebrid.accountAuthenticationLink())
			message += interface.Format.newline()
			message += interface.Format.fontBold(interface.Translation.string(33495) + ': ' + self.mDebrid.accountAuthenticationCode())
			message += interface.Format.newline() + interface.Translation.string(33494) + ' ' + interface.Translation.string(33978)

			clipboard.Clipboard.copy(self.mDebrid.accountAuthenticationCode())
			progressDialog = interface.Dialog.progress(title = RealDebridInterface.Name, message = message, background = False)

			interval = self.mDebrid.accountAuthenticationInterval()
			timeout = 3600
			synchronized = False

			for i in range(timeout):
				try:
					try: canceled = progressDialog.iscanceled()
					except: canceled = False
					if canceled: break
					progressDialog.update(int((i / float(timeout)) * 100))

					if not float(i) % interval == 0:
						raise Exception()
					tools.Time.sleep(1)

					if self.mDebrid.accountAuthenticationWait():
						synchronized = True
						break
				except:
					pass

			try: progressDialog.close()
			except: pass

			if synchronized:
				if self.mDebrid.accountAuthenticationFinish():
					interface.Dialog.notification(title = 33567, message = 35462, icon = interface.Dialog.IconSuccess)
			else:
				self.mDebrid.accountAuthenticationReset(save = True) # Make sure the values are reset if the waiting dialog is canceled.
		except:
			pass
		if openSettings:
			tools.Settings.launch(category = tools.Settings.CategoryAccounts)
		interface.Loader.hide()

	##############################################################################
	# CLEAR
	##############################################################################

	def clear(self):
		title = RealDebridInterface.Name + ' ' + interface.Translation.string(33013)
		message = 'Do you want to clear your RealDebrid downloads and delete all your files from the server?'
		if interface.Dialog.option(title = title, message = message):
			interface.Loader.show()
			self.mDebrid.deleteAll()
			interface.Loader.hide()
			message = 'RealDebrid Downloads Cleared'
			interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconSuccess)

	##############################################################################
	# ADD
	##############################################################################

	def addManual(self):
		result = None
		title = 35082
		items = [
			interface.Format.bold(interface.Translation.string(35076) + ': ') + interface.Translation.string(35077),
			interface.Format.bold(interface.Translation.string(33381) + ': ') + interface.Translation.string(35080),
			interface.Format.bold(interface.Translation.string(33380) + ': ') + interface.Translation.string(35081),
		]
		choice = interface.Dialog.select(title = title, items = items)

		if choice >= 0:
			link = None
			if choice == 0 or choice == 1:
				link = interface.Dialog.input(title = title, type = interface.Dialog.InputAlphabetic)
			elif choice == 2:
				link = interface.Dialog.browse(title = title, type = interface.Dialog.BrowseFile, multiple = False, mask = ['torrent'])

			if not link == None or not link == '':
				interface.Dialog.notification(title = 35070, message = 35072, icon = interface.Dialog.IconSuccess)
				interface.Loader.show()
				result = self.add(link)
				if result['success']:
					interface.Dialog.closeAllProgress()
					choice = interface.Dialog.option(title = 35073, message = 35075)
					if choice: interface.Player.playNow(result['link'])

		interface.Loader.hide()
		return result

	def add(self, link, title = None, season = None, episode = None, pack = False, close = True, source = None, cached = None, select = False):
		result = self.mDebrid.add(link = link, title = title, season = season, episode = episode, pack = pack, source = source)
		if result['success']:
			return result
		elif result['id']:
			return self._addWait(result = result, season = season, episode = episode, close = close, pack = pack, source = source, cached = cached, select = select)
		elif result['error'] == RealDebrid.ErrorInaccessible:
			title = 'Stream Error'
			message = 'Stream Is Inaccessible'
		elif result['error'] == RealDebrid.ErrorRealDebrid:
			title = 'Stream Error'
			message = 'Failed To Add Stream To RealDebrid'
		elif result['error'] == RealDebrid.ErrorSelection:
			title = 'Selection Error'
			message = 'No File Selected'
		else:
			tools.Logger.errorCustom('Unexpected RealDebrid Error: ' + str(result))
			title = 'Stream Error'
			message = 'Stream File Unavailable'
		self._addError(title = title, message = message)
		result['notification'] = True
		return result

	def _addSelect(self, result):
		try:
			if not result: return result
			items = [i for i in result['items']['files'] if i['name'] and not i['name'].endswith(Debrid.Exclusions)]
			items = sorted(items, key = lambda x : x['name'])
			choice = interface.Dialog.options(title = 35542, items = [i['name'].strip('/') for i in items])
			if choice < 0:
				result['success'] = False
				result['error'] = RealDebrid.ErrorSelection
			else:
				result['items']['video'] = items[choice]
				result['selection'] = items[choice]['id']
		except:
			tools.Logger.error()
		return result

	def _addDelete(self, id, notification = False):
		def __addDelete(id, notification):
			result = self.mDebrid.delete(id)
			if notification:
				if result == True:
					interface.Dialog.notification(title = 'Deletion Success', message = 'Download Deleted From List', icon = interface.Dialog.IconSuccess)
				else:
					interface.Dialog.notification(title = 'Deletion Failure', message = 'Download Not Deleted From List', icon = interface.Dialog.IconError)
		thread = threading.Thread(target = __addDelete, args = (id, notification))
		thread.start()

	def _addAction(self, result):
		items = []
		items.append(interface.Format.font(interface.Translation.string(33077) + ': ', bold = True) + interface.Translation.string(33078))
		items.append(interface.Format.font(interface.Translation.string(33079) + ': ', bold = True) + interface.Translation.string(33080))
		items.append(interface.Format.font(interface.Translation.string(33083) + ': ', bold = True) + interface.Translation.string(33084))

		interface.Core.close()
		tools.Time.sleep(0.1) # Ensures progress dialog is closed, otherwise shows flickering.
		choice = interface.Dialog.options(title = 33076, items = items)

		if choice == -1:
			return False
		elif choice == 0:
			return True
		elif choice == 1:
			return False
		elif choice == 2:
			self._addDelete(id = result['id'], notification = True)
			return False

	def _addError(self, title, message, delay = True):
		interface.Loader.hide() # Make sure hided from sources __init__.py
		interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconError)
		if delay: tools.Time.sleep(2) # Otherwise the message disappears to quickley when another notification is shown afterwards.

	def _addErrorDetermine(self, item):
		error = False
		status = item['status']

		if status == RealDebrid.StatusError:
			title = 'Download Error'
			message = 'Download Failure With Unknown Error'
			error = True
		elif status == RealDebrid.StatusMagnetError:
			title = 'Download Magnet'
			message = 'Magnet Link Download Failure'
			error = True
		elif status == RealDebrid.StatusVirus:
			title = 'Download Virus'
			message = 'Download Contains Virus'
			error = True
		elif status == RealDebrid.StatusDead:
			title = 'Download Dead'
			message = 'Torrent Download Dead'
			error = True

		if error:
			self._addError(title = title, message = message)
			try: self.mDebrid.deleteFailure(item['hash'])
			except: pass

		return error

	def _addWaitAction(self, result, seconds = None):
		# Ask to close a background dialog, because there is no cancel button as with the foreground dialog.
		elapsed = self.mTimer.elapsed()
		conditionShort = self.mTimerShort == False and elapsed > 30
		conditionLong = self.mTimerLong == False and elapsed > 120
		if conditionShort or conditionLong:
			if conditionShort: question = 'The download is taking a bit longer.'
			else: question = 'The download is taking a lot longer.'

			if seconds: question += ' The estimated remaining time is ' + convert.ConverterDuration(seconds, convert.ConverterDuration.UnitSecond).string(format = convert.ConverterDuration.FormatWordMedium) + '.'
			else: question += ' The estimated remaining time is currently unknown.'

			if conditionShort: question += ' Do you want to take action or let the download continue in the background?'
			else: question += ' Are you sure you do not want to take action and let the download continue in the background?'

			if conditionShort: self.mTimerShort = True
			if conditionLong: self.mTimerLong = True

			title = RealDebridInterface.Name + ' Download'
			answer = interface.Dialog.option(title = title, message = question, labelConfirm = 'Take Action', labelDeny = 'Continue Download')
			if answer:
				self._addAction(result)
				return True
		return False

	def _addWait(self, result, season = None, episode = None, close = True, pack = False, source = None, cached = None, select = False):
		try:
			id = result['id']

			# In case the progress dialog was canceled while transfering torrent data.
			if interface.Core.canceled():
				self._addDelete(id = id, notification = False)
				return self.mDebrid.addResult(error = Debrid.ErrorCancel)

			self.mTimer = tools.Time(start = True)
			self.mTimerShort = False
			self.mTimerLong = False

			if cached: apiInterval = 5 # Only 2.5 seconds for cached content, to reduce waiting time.
			else: apiInterval = 5 * 2 # Times 2, because the loops run in 0.5 seconds.
			apiCounter = 0

			unknown = 'Unknown'
			title = RealDebridInterface.Name + ' Download'
			descriptionInitialize = interface.Format.fontBold('Initializing Download') + '%s'
			descriptionWaiting = interface.Format.fontBold('Waiting For Download Start') + '%s'
			descriptionSeeds = interface.Format.fontBold('Waiting For Seed Connection') + '%s'
			descriptionFinalize = interface.Format.fontBold('Finalizing Download') + '%s'
			percentage = 0
			selectionFile = None

			interface.Loader.hide()
			background = interface.Core.background()

			while True:

				# Do not launch the dialog if the torrent is cached, since RealDebird downloads do not distiguish between cahced and non-cahced downloads.
				# Do not use the the item's cached status, since it might be outdated (eg: items from the stream history list).
				if not cached:
					interface.Core.create(type = interface.Core.TypeDownload, title = title, message = descriptionInitialize)
					interface.Core.update(progress = int(percentage), title = title, message = descriptionInitialize)

				item = self.mDebrid.item(id = id)
				status = item['status']

				#####################################################################################################################################
				# Select the largest file for download.
				#####################################################################################################################################

				while status == RealDebrid.StatusMagnetConversion or status == RealDebrid.StatusFileSelection or status == RealDebrid.StatusQueued:
					if interface.Core.canceled():
						break

					if background and self._addWaitAction(result = result):
						if not cached and close: interface.Core.close()
						return self.mDebrid.addError()

					if not cached: interface.Core.update(progress = int(percentage), title = title, message = descriptionSeeds)

					apiCounter += 1
					if apiCounter == apiInterval:
						apiCounter = 0
						item = self.mDebrid.item(id = id)
						status = item['status']
						if self._addErrorDetermine(item):
							if not cached and close: interface.Core.close()
							return self.mDebrid.addError()

					# Select the largest/name, so that the direct download link points to the main video file.
					# Otherwise, if all files are selected, RealDebrid will create a rar file in the final link.
					if select:
						selection = False
						while True:
							result = self.mDebrid.selectManualInitial(id = id, item = item)
							if isinstance(result, dict):
								if selectionFile == None: selectionFile = self._addSelect(result)
								selection = self.mDebrid.selectManualFinal(id = id, selection = selectionFile['selection'])
								break
							tools.Time.sleep(1)
					else:
						selection = self.mDebrid.selectName(id = id, item = item, season = season, episode = episode)

					if selection == True:
						item = self.mDebrid.item(id = id)
						status = item['status']
						if status == RealDebrid.StatusFinished: # In case of "cached" RealDebrid torrents that are available immediatley.
							percentage = 100
							if not cached:
								interface.Core.update(progress = int(percentage), title = title, message = descriptionFinalize)
								if close: interface.Core.close()
							result = self.mDebrid.add(item['link'])
							result['id'] = id # Torrent ID is different to the unrestirction ID. The torrent ID is needed for deletion.
							return result
						else:
							break
					elif selection == RealDebrid.ErrorUnavailable and not status == RealDebrid.StatusMagnetConversion:
						if not cached and close: interface.Core.close()
						title = 'Invalid Stream'
						if pack: message = 'No Episode In Season Pack'
						else: message = 'No Playable Stream Found'
						self._addError(title = title, message = message)
						try: self.mDebrid.deleteFailure(item['hash'])
						except: pass
						return self.mDebrid.addError()

					tools.Time.sleep(0.5)

				#####################################################################################################################################
				# Wait for the download to start.
				#####################################################################################################################################

				waiting = item['transfer']['progress']['completed']['value'] == 0 and item['transfer']['speed']['bytes'] == 0
				while status == RealDebrid.StatusQueued or waiting:
					if not cached and interface.Core.canceled():
						break

					if background and self._addWaitAction(result = result):
						if not cached and close: interface.Core.close()
						return self.mDebrid.addError()

					if not cached: interface.Core.update(progress = int(percentage), title = title, message = descriptionWaiting)

					apiCounter += 1
					if apiCounter == apiInterval:
						apiCounter = 0
						item = self.mDebrid.item(id = id)
						status = item['status']
						if self._addErrorDetermine(item):
							if not cached and close: interface.Core.close()
							return self.mDebrid.addError()
						waiting = item['transfer']['progress']['completed']['value'] == 0 and item['transfer']['speed']['bytes'] == 0

					tools.Time.sleep(0.5)

				#####################################################################################################################################
				# Wait for the download to finish.
				#####################################################################################################################################

				seconds = None
				while True:
					if not cached and interface.Core.canceled():
						break

					if background and self._addWaitAction(result = result, seconds = seconds):
						return self.mDebrid.addError()

					apiCounter += 1
					if apiCounter == apiInterval:
						apiCounter = 0
						item = self.mDebrid.item(id = id)

						if self._addErrorDetermine(item):
							if not cached and close: interface.Core.close()
							return self.mDebrid.addError()

						status = item['status']
						if status == RealDebrid.StatusFinished:
							percentage = 100
							if not cached:
								interface.Core.update(progress = int(percentage), title = title, message = descriptionFinalize)
								if close: interface.Core.close()
							result = self.mDebrid.add(item['link'])
							result['id'] = id # Torrent ID is different to the unrestirction ID. The torrent ID is needed for deletion.
							return result

						percentageNew = item['transfer']['progress']['completed']['percentage']
						if percentageNew >= percentage:
							percentage = percentageNew
							speed = item['transfer']['speed']['description']
							speedBytes = item['transfer']['speed']['bytes']
							size = item['size']['description']
							sizeBytes = item['size']['bytes']
							sizeCompleted = item['transfer']['progress']['completed']['size']['description']
							seconds = item['transfer']['progress']['remaining']['time']['seconds']
							if seconds == 0:
								eta = unknown
								if background: eta += ' ETA'
							else:
								eta = item['transfer']['progress']['remaining']['time']['description']

							description = []
							if background:
								if speed: description.append(speed)
								if size and sizeBytes > 0: description.append(size)
								if eta: description.append(eta)
								if len(description) > 0:
									description = interface.Format.fontSeparator().join(description)
								else:
									description = 'Unknown Progress'
							else:
								if speed:
									if speedBytes <= 0:
										speed = unknown
									description.append(interface.Format.font('Download Speed: ', bold = True) + speed)
								if size:
									if sizeBytes > 0:
										size = sizeCompleted + ' of ' + size
									else:
										size = unknown
									description.append(interface.Format.font('Download Size: ', bold = True) + size)
								if eta: description.append(interface.Format.font('Remaining Time: ', bold = True) + eta)
								description = interface.Format.fontNewline().join(description)

							if not cached: interface.Core.update(progress = int(percentage), title = title, message = description)

					tools.Time.sleep(0.5)

				#####################################################################################################################################
				# Continue
				#####################################################################################################################################

				# Action Dialog
				if interface.Core.canceled():
					if not self._addAction(result):
						return self.mDebrid.addResult(error = Debrid.ErrorCancel)

				# NB: This is very important.
				# Close the dialog and sleep (0.1 is not enough).
				# This alows the dialog to properley close and reset everything.
				# If not present, the internal iscanceled variable of the progress dialog will stay True after the first cancel.
				interface.Core.close()
				tools.Time.sleep(0.5)

		except:
			tools.Logger.error()
			if close: interface.Core.close()
			return self.mDebrid.addError()

	##############################################################################
	# DOWNLOAD
	##############################################################################

	def downloadInformation(self):
		interface.Loader.show()
		title = RealDebridInterface.Name + ' ' + interface.Translation.string(32009)
		if self.mDebrid.accountEnabled():
			account = self.mDebrid.account()
			if account:
				information = self.mDebrid.downloadInformation()
				items = []

				# Torrent Count
				count = information['count']
				items.append({
					'title' : 33496,
					'items' : [
						{ 'title' : 33497, 'value' : str(count['total']) },
						{ 'title' : 33291, 'value' : str(count['busy']) },
						{ 'title' : 33294, 'value' : str(count['finished']) },
						{ 'title' : 33295, 'value' : str(count['failed']) },
					]
				})

				# Torrent Size
				# NB: Currently ignore the size, since RealDebrid always returns 0 bytes for downloads.
				'''size = information['size']
				items.append({
					'title' : 33498,
					'items' : [
						{ 'title' : 33497, 'value' : size['description'] },
					]
				})'''

				# Torrent Host
				if 'host' in information:
					host = information['host']
					items.append({
						'title' : 33499,
						'items' : [
							{ 'title' : 33500, 'value' : host['domain'] },
							{ 'title' : 33501, 'value' : host['size']['description'] },
						]
					})

				# Dialog
				interface.Loader.hide()
				interface.Dialog.information(title = title, items = items)
			else:
				interface.Loader.hide()
				interface.Dialog.confirm(title = title, message = interface.Translation.string(33352) % RealDebridInterface.Name)
		else:
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33351) % RealDebridInterface.Name)

	##############################################################################
	# DIRECTORY
	##############################################################################

	def directoryListAction(self, item):
		itemNew = tools.Converter.jsonFrom(item)
		if itemNew: item = itemNew

		actions = []
		items = []

		if item['status'] == RealDebrid.StatusFinished:
			actions.append('download')
			items.append(interface.Format.bold(interface.Translation.string(35154) + ': ') + interface.Translation.string(35155))
			actions.append('stream')
			items.append(interface.Format.bold(interface.Translation.string(35083) + ': ') + interface.Translation.string(35086))
			actions.append('copy')
			items.append(interface.Format.bold(interface.Translation.string(33031) + ': ') + interface.Translation.string(35087))
			actions.append('open')
			items.append(interface.Format.bold(interface.Translation.string(35085) + ': ') + interface.Translation.string(35088))

		actions.append('remove')
		items.append(interface.Format.bold(interface.Translation.string(35100) + ': ') + interface.Translation.string(35101))
		actions.append('refresh')
		items.append(interface.Format.bold(interface.Translation.string(35103) + ': ') + interface.Translation.string(35104))
		actions.append('cancel')
		items.append(interface.Format.bold(interface.Translation.string(35105) + ': ') + interface.Translation.string(35106))

		choice = interface.Dialog.select(title = 32009, items = items)
		if choice >= 0:
			choice = actions[choice]
			if choice == 'refresh':
				interface.Directory.refresh()
			elif not choice == 'cancel':
				hide = True
				interface.Loader.show()
				try:
					id = item['id']
					if choice == 'remove':
						self.mDebrid.deleteSingle(id, wait = True)
						interface.Directory.refresh()
						hide = False # Already hidden by container refresh.
					elif choice == 'download':
						try: itemLink = self.mDebrid.add(item['link'])['link']
						except: itemLink = None
						if network.Networker.linkIs(itemLink): downloader.Downloader(downloader.Downloader.TypeManual).download(media = downloader.Downloader.MediaOther, link = itemLink)
						else: raise Exception('Invalid Link: ' + str(itemLink))
					else:
						item = self.mDebrid.item(id)
						try: itemLink = self.mDebrid.add(item['link'])['link']
						except: itemLink = None
						if network.Networker.linkIs(itemLink):
							if choice == 'stream':
								interface.Player.playNow(itemLink)
							elif choice == 'copy':
								clipboard.Clipboard.copyLink(itemLink, True)
							elif choice == 'open':
								tools.System.openLink(itemLink)
						else: # RealDebrid API errors
							raise Exception('Invalid Link: ' + str(itemLink))
				except:
					tools.Logger.error()
					interface.Dialog.notification(title = 33567, message = 35108, icon = interface.Dialog.IconError)
				if hide: interface.Loader.hide()

	def directoryList(self):
		directory = interface.Directory(content = interface.Directory.ContentAddons)
		items = self.mDebrid.items()
		itemsNew = [[], [], [], [], []]

		for item in items:
			info = []
			icon = None
			index = 0

			try: status = item['status']
			except: status = None

			if not status == None and not status == RealDebrid.StatusUnknown:
				color = None
				if status == RealDebrid.StatusError:
					color = interface.Format.ColorBad
					icon = 'downloadsfailed.png'
					statusLabel = 'Failure'
					index = 0
				elif status == RealDebrid.StatusMagnetError:
					color = interface.Format.ColorBad
					icon = 'downloadsfailed.png'
					statusLabel = 'Magnet'
					index = 0
				elif status == RealDebrid.StatusMagnetConversion:
					color = interface.Format.ColorMedium
					icon = 'downloadsbusy.png'
					statusLabel = 'Conversion'
					index = 1
				elif status == RealDebrid.StatusFileSelection:
					color = interface.Format.ColorMedium
					icon = 'downloadsbusy.png'
					statusLabel = 'Selection'
					index = 1
				elif status == RealDebrid.StatusQueued:
					color = interface.Format.ColorMedium
					icon = 'downloadsbusy.png'
					statusLabel = 'Queued'
					index = 1
				elif status == RealDebrid.StatusBusy:
					color = interface.Format.ColorExcellent
					icon = 'downloadsbusy.png'
					statusLabel = 'Busy'
					index = 2
				elif status == RealDebrid.StatusFinished:
					color = interface.Format.ColorSpecial
					icon = 'downloadscompleted.png'
					statusLabel = 'Finished'
					index = 3
				elif status == RealDebrid.StatusVirus:
					color = interface.Format.ColorBad
					icon = 'downloadsfailed.png'
					statusLabel = 'Virus'
					index = 0
				elif status == RealDebrid.StatusCompressing:
					color = interface.Format.ColorMain
					icon = 'downloadsbusy.png'
					statusLabel = 'Compressing'
					index = 4
				elif status == RealDebrid.StatusUploading:
					color = interface.Format.ColorMain
					icon = 'downloadsbusy.png'
					statusLabel = 'Uploading'
					index = 4
				elif status == RealDebrid.StatusDead:
					color = interface.Format.ColorBad
					icon = 'downloadsfailed.png'
					statusLabel = 'Dead'
					index = 0
				info.append(interface.Format.fontColor(statusLabel, color))

			if status == RealDebrid.StatusBusy:
				try:
					colors = interface.Format.colorGradient(interface.Format.ColorMedium, interface.Format.ColorExcellent, 101) # One more, since it goes from 0 - 100
					percentage = int(item['transfer']['progress']['completed']['percentage'])
					info.append(interface.Format.fontColor('%d%%' % percentage, colors[percentage]))
				except:
					tools.Logger.error()
					pass

				try:
					if item['transfer']['speed']['bits'] > 0:
						info.append(item['transfer']['speed']['description'])
				except: pass
				try:
					if item['transfer']['progress']['remaining']['time']['seconds'] > 0:
						info.append(item['transfer']['progress']['remaining']['time']['description'])
				except: pass

			try:
				if item['size']['bytes'] > 0:
					info.append(item['size']['description'])
			except: pass

			label = interface.Format.bold(item['name'])
			label += interface.Format.newline()
			label += ' | '.join(info)

			itemJson = tools.Converter.jsonTo(item)

			context = []
			context.append({'label' : 32072, 'command' : 'Container.Refresh'})
			context.append({'label' : 33371, 'command' : tools.System.commandPlugin(action = 'realdebridListAction', parameters = {'item' : itemJson})})

			itemsNew[index].append({'item' : itemJson, 'label' : label, 'context' : context, 'icon' : icon})

		for item in itemsNew:
			for i in item:
				directory.add(label = i['label'], action = 'realdebridListAction', parameters = {'item' : i['item']}, context = i['context'], folder = True, icon = i['icon'], iconDefault = 'DefaultAddonProgram.png')

		directory.finish()

############################################################################################################################################################
# ALLDEBRID
############################################################################################################################################################

class AllDebrid(Debrid):

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Debrid.__init__(self, 'AllDebrid')

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.alldebrid', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.alldebrid.enabled')

	def accountValid(self):
		return not self.accountUsername() == '' and not self.accountPassword() == ''

	def accountUsername(self):
		return tools.Settings.getString('accounts.debrid.alldebrid.user') if self.accountEnabled() else ''

	def accountPassword(self):
		return tools.Settings.getString('accounts.debrid.alldebrid.pass') if self.accountEnabled() else ''

	##############################################################################
	# SERVICES
	##############################################################################

	def servicesList(self, onlyEnabled = False):
		hosts = []
		try:
			if (not onlyEnabled or self.streamingHoster()) and self.accountValid():
				from resources.lib.modules import client
				from resources.lib.modules import cache
				url = 'https://api.alldebrid.com/hosts'
				result = cache.get(client.request, 900, url)
				result = tools.Converter.jsonFrom(result)
				result = result['hosts']
				hosts = []
				for i in result:
					if i['status']:
						hosts.append(i['domain'])
						try: hosts.extend(i['altDomains'])
						except: pass
				return list(set([i.lower() for i in hosts]))
		except:
			tools.Logger.error()
		return hosts

	##############################################################################
	# ADD
	##############################################################################

	def add(self, link):
		try:
			if self.accountValid():
				from resources.lib.modules import client
				loginData = urllib.urlencode({'action': 'login', 'login_login': self.accountUsername(), 'login_password': self.accountPassword()})
				loginLink = 'http://alldebrid.com/register/?%s' % loginData
				cookie = client.request(loginLink, output = 'cookie', close = False)
				url = 'http://www.alldebrid.com/service.php?link=%s' % urllib.quote_plus(link)
				result = client.request(url, cookie = cookie, close = False)
				url = client.parseDOM(result, 'a', ret = 'href', attrs = {'class': 'link_dl'})[0]
				url = client.replaceHTMLCodes(url)
				url = '%s|Cookie=%s' % (url, urllib.quote_plus(cookie))
				return self.addResult(link = url)
		except:
			tools.Logger.error()
		return self.addError()

############################################################################################################################################################
# RAPIDPREMIUM
############################################################################################################################################################

class RapidPremium(Debrid):

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Debrid.__init__(self, 'RapidPremium')

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.rapidpremium', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.rapidpremium.enabled')

	def accountValid(self):
		return not self.accountUsername() == '' and not self.accountApi() == ''

	def accountUsername(self):
		return tools.Settings.getString('accounts.debrid.rapidpremium.user') if self.accountEnabled() else ''

	def accountApi(self):
		return tools.Settings.getString('accounts.debrid.rapidpremium.api') if self.accountEnabled() else ''

	##############################################################################
	# SERVICES
	##############################################################################

	def servicesList(self, onlyEnabled = False):
		hosts = []
		try:
			if (not onlyEnabled or self.streamingHoster()) and self.accountValid():
				from resources.lib.modules import client
				from resources.lib.modules import cache
				url = 'http://premium.rpnet.biz/hoster2.json'
				result = cache.get(client.request, 900, url)
				result = tools.Converter.jsonFrom(result)
				result = result['supported']
				hosts = [i.lower() for i in result]
		except:
			tools.Logger.error()
			pass
		return hosts

	##############################################################################
	# ADD
	##############################################################################

	def add(self, link):
		try:
			if self.accountValid():
				from resources.lib.modules import client
				loginData = urllib.urlencode({'username': self.accountUsername(), 'password': self.accountApi(), 'action': 'generate', 'links': link})
				loginLink = 'http://premium.rpnet.biz/client_api.php?%s' % loginData
				result = client.request(loginLink, close = False)
				result = tools.Converter.jsonFrom(result)
				return self.addResult(link = result['links'][0]['generated'])
		except:
			pass
		return self.addError()

############################################################################################################################################################
# EASYNEWS
############################################################################################################################################################

class EasyNews(Debrid):

	Cookie = 'chickenlicker=%s%%3A%s'

	TimeoutAccount = 0.17 # 10 min

	LinkLogin = 'https://account.easynews.com/index.php'
	LinkAccount = 'https://account.easynews.com/editinfo.php'
	LinkUsage = 'https://account.easynews.com/usageview.php'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Debrid.__init__(self, 'EasyNews')
		self.mResult = None
		self.mSuccess = False
		self.mError = None
		self.mCookie = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _request(self, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None):
		self.mResult = None
		self.mSuccess = True
		self.mError = None

		if not httpTimeout: httpTimeout = 30

		def login():
			data = urllib.urlencode({'username': self.accountUsername(), 'password': self.accountPassword(), 'submit': 'submit'})
			self.mCookie = client.request(EasyNews.LinkLogin, post = data, output = 'cookie', close = False)

		try:
			if parameters: parameters = urllib.urlencode(parameters)

			if self.mCookie == None: login()
			if not self.mCookie:
				self.mSuccess = False
				self.mError = 'Login Error'
				return self.mResult

			self.mResult = client.request(link, post = parameters, cookie = self.mCookie, headers = httpHeaders, timeout = httpTimeout, close = True)

			if 'value="Login"' in self.mResult: login()
			if not self.mCookie:
				self.mSuccess = False
				self.mError = 'Login Error'
				return self.mResult

			self.mResult = client.request(link, post = parameters, cookie = self.mCookie, headers = httpHeaders, timeout = httpTimeout, close = True)

			self.mSuccess = self.mCookie and not 'value="Login"' in self.mResult
			if not self.mSuccess: self.mError = 'Login Error'
		except:
			toosl.Logger.error()
			self.mSuccess = False
			self.mError = 'Unknown Error'
		return self.mResult

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('link.easynews', raw = True)
		if open: tools.System.openLink(link)
		return link

	@classmethod
	def vpn(self, open = False):
		link = tools.Settings.getString('link.easynews.vpn', raw = True)
		if open: tools.System.openLink(link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountEnabled(self):
		return tools.Settings.getBoolean('accounts.debrid.easynews.enabled')

	def accountValid(self):
		return not self.accountUsername() == '' and not self.accountPassword() == ''

	def accountUsername(self):
		return tools.Settings.getString('accounts.debrid.easynews.user') if self.accountEnabled() else ''

	def accountPassword(self):
		return tools.Settings.getString('accounts.debrid.easynews.pass') if self.accountEnabled() else ''

	def accountCookie(self):
		return EasyNews.Cookie % (self.accountUsername(), self.accountPassword())

	def accountVerify(self):
		return not self.account(cache = False, minimal = True) == None

	def account(self, cache = True, minimal = False):
		account = None
		try:
			if self.accountValid():
				timeout = EasyNews.TimeoutAccount if cache else 0

				def __easynewsAccount():
					return self._request(EasyNews.LinkAccount)
				accountHtml = tools.Cache.cache(__easynewsAccount, timeout)
				if accountHtml == None or accountHtml == '': raise Exception()

				accountHtml = BeautifulSoup(accountHtml)
				accountHtml = accountHtml.find_all('form', id = 'accountForm')[0]
				accountHtml = accountHtml.find_all('table', recursive = False)[0]
				accountHtml = accountHtml.find_all('tr', recursive = False)

				accountUsername = accountHtml[0].find_all('td', recursive = False)[1].getText()
				accountType = accountHtml[1].find_all('td', recursive = False)[2].getText()
				accountStatus = accountHtml[3].find_all('td', recursive = False)[2].getText()

				accountExpiration = accountHtml[2].find_all('td', recursive = False)[2].getText()
				accountTimestamp = convert.ConverterTime(accountExpiration, format = convert.ConverterTime.FormatDate).timestamp()
				accountExpiration = datetime.datetime.fromtimestamp(accountTimestamp)

				account = {
					'user' : accountUsername,
					'type' : accountType,
					'status' : accountStatus,
			 		'expiration' : {
						'timestamp' : accountTimestamp,
						'date' : accountExpiration.strftime('%Y-%m-%d'),
						'remaining' : (accountExpiration - datetime.datetime.today()).days,
					}
				}

				if not minimal:
					def __easynewsUsage():
						return self._request(EasyNews.LinkUsage)
					usageHtml = tools.Cache.cache(__easynewsUsage, timeout)
					if usageHtml == None or usageHtml == '': raise Exception()

					usageHtml = BeautifulSoup(usageHtml)
					usageHtml = usageHtml.find_all('div', class_ = 'table-responsive')[0]
					usageHtml = usageHtml.find_all('table', recursive = False)[0]
					usageHtml = usageHtml.find_all('tr', recursive = False)

					usageTotal = usageHtml[0].find_all('td', recursive = False)[1].getText()
					index = usageTotal.find('(')
					if index >= 0: usageTotal = int(usageTotal[index + 1 : usageTotal.find(' ', index)].replace(',', '').strip())
					else: usageTotal = 0

					usageConsumed = usageHtml[1].find_all('td', recursive = False)[2].getText()
					index = usageConsumed.find('(')
					if index >= 0: usageConsumed = int(usageConsumed[index + 1 : usageConsumed.find(' ', index)].replace(',', '').strip())
					else: usageConsumed = 0

					usageWeb = usageHtml[2].find_all('td', recursive = False)[2].getText()
					index = usageWeb.find('(')
					if index >= 0: usageWeb = int(usageWeb[index + 1 : usageWeb.find(' ', index)].replace(',', '').strip())
					else: usageWeb = 0

					usageNntp = usageHtml[3].find_all('td', recursive = False)[2].getText()
					index = usageNntp.find('(')
					if index >= 0: usageNntp = int(usageNntp[index + 1 : usageNntp.find(' ', index)].replace(',', '').strip())
					else: usageNntp = 0

					usageNntpUnlimited = usageHtml[4].find_all('td', recursive = False)[2].getText()
					index = usageNntpUnlimited.find('(')
					if index >= 0: usageNntpUnlimited = int(usageNntpUnlimited[index + 1 : usageNntpUnlimited.find(' ', index)].replace(',', '').strip())
					else: usageNntpUnlimited = 0

					usageRemaining = usageHtml[5].find_all('td', recursive = False)[2].getText()
					index = usageRemaining.find('(')
					if index >= 0: usageRemaining = int(usageRemaining[index + 1 : usageRemaining.find(' ', index)].replace(',', '').strip())
					else: usageRemaining = 0

					usageLoyalty = usageHtml[6].find_all('td', recursive = False)[2].getText()
					index = usageLoyalty.find('(')
					if index >= 0:
						usageLoyaltyTime = usageLoyalty[:index].strip()
						usageLoyaltyTimestamp = convert.ConverterTime(usageLoyaltyTime, format = convert.ConverterTime.FormatDate).timestamp()
						usageLoyaltyTime = datetime.datetime.fromtimestamp(usageLoyaltyTimestamp)
						usageLoyaltyPoints = float(usageLoyalty[index + 1 : usageLoyalty.find(')', index)].strip())
					else:
						usageLoyaltyTimestamp = 0
						usageLoyaltyTime = None

					usagePrecentageRemaining = usageRemaining / float(usageTotal)
					usagePrecentageConsumed = usageConsumed / float(usageTotal)
					usagePrecentageWeb = usageWeb / float(usageTotal)
					usagePrecentageNntp = usageNntp / float(usageTotal)
					usagePrecentageNntpUnlimited = usageNntpUnlimited / float(usageTotal)

					account.update({
						'loyalty' : {
							'time' : {
								'timestamp' : usageLoyaltyTimestamp,
								'date' : usageLoyaltyTime.strftime('%Y-%m-%d')
							},
							'points' : usageLoyaltyPoints,
						},
						'usage' : {
							'total' : {
								'size' : {
									'bytes' : usageTotal,
									'description' : convert.ConverterSize(float(usageTotal)).stringOptimal(),
								},
							},
							'remaining' : {
								'value' : usagePrecentageRemaining,
								'percentage' : round(usagePrecentageRemaining * 100.0, 1),
								'size' : {
									'bytes' : usageRemaining,
									'description' : convert.ConverterSize(float(usageRemaining)).stringOptimal(),
								},
								'description' : '%.0f%%' % round(usagePrecentageRemaining * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
							},
							'consumed' : {
								'value' : usagePrecentageConsumed,
								'percentage' : round(usagePrecentageConsumed * 100.0, 1),
								'size' : {
									'bytes' : usageConsumed,
									'description' : convert.ConverterSize(usageConsumed).stringOptimal(),
								},
								'description' : '%.0f%%' % round(usagePrecentageConsumed * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								'web' : {
									'value' : usagePrecentageWeb,
									'percentage' : round(usagePrecentageWeb * 100.0, 1),
									'size' : {
										'bytes' : usageWeb,
										'description' : convert.ConverterSize(usageWeb).stringOptimal(),
									},
									'description' : '%.0f%%' % round(usagePrecentageWeb * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								},
								'nntp' : {
									'value' : usagePrecentageNntp,
									'percentage' : round(usagePrecentageNntp * 100.0, 1),
									'size' : {
										'bytes' : usageNntp,
										'description' : convert.ConverterSize(usageNntp).stringOptimal(),
									},
									'description' : '%.0f%%' % round(usagePrecentageNntp * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								},
								'nntpunlimited' : {
									'value' : usagePrecentageNntpUnlimited,
									'percentage' : round(usagePrecentageNntpUnlimited * 100.0, 1),
									'size' : {
										'bytes' : usageNntpUnlimited,
										'description' : convert.ConverterSize(usageNntpUnlimited).stringOptimal(),
									},
									'description' : '%.0f%%' % round(usagePrecentageNntpUnlimited * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								},
							}
						}
					})
		except:
			pass
		return account

class EasyNewsInterface(object):

	Name = 'EasyNews'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		self.mDebrid = EasyNews()

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self):
		interface.Loader.show()
		valid = False
		title = EasyNewsInterface.Name + ' ' + interface.Translation.string(33339)
		if self.mDebrid.accountEnabled():
			account = self.mDebrid.account(cache = False)
			if account:
				valid = interface.Translation.string(33341) if self.mDebrid.accountValid() else interface.Translation.string(33342)
				user = account['user']
				type = account['type']
				status = account['status'].capitalize()

				date = account['expiration']['date']
				days = str(account['expiration']['remaining'])

				loyaltyDate = account['loyalty']['time']['date']
				loyaltyPoints = '%.3f' % account['loyalty']['points']

				total = convert.ConverterSize(account['usage']['total']['size']['bytes']).stringOptimal()
				remaining = convert.ConverterSize(account['usage']['remaining']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['remaining']['percentage'])
				consumed = convert.ConverterSize(account['usage']['consumed']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['consumed']['percentage'])
				consumedWeb = convert.ConverterSize(account['usage']['consumed']['web']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['consumed']['web']['percentage'])
				consumedNntp = convert.ConverterSize(account['usage']['consumed']['nntp']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['consumed']['nntp']['percentage'])
				consumedNntpUnlimited = convert.ConverterSize(account['usage']['consumed']['nntpunlimited']['size']['bytes']).stringOptimal() + (' (%.1f%%)' % account['usage']['consumed']['nntpunlimited']['percentage'])

				items = []

				items = []

				# Information
				items.append({
					'title' : 33344,
					'items' : [
						{ 'title' : 33340, 'value' : valid },
						{ 'title' : 32303, 'value' : user },
						{ 'title' : 33343, 'value' : type },
						{ 'title' : 33389, 'value' : status },
					]
				})

				# Expiration
				items.append({
					'title' : 33345,
					'items' : [
						{ 'title' : 33346, 'value' : date },
						{ 'title' : 33347, 'value' : days }
					]
				})

				# Loyalty
				items.append({
					'title' : 33750,
					'items' : [
						{ 'title' : 33346, 'value' : loyaltyDate },
						{ 'title' : 33349, 'value' : loyaltyPoints }
					]
				})

				# Usage
				items.append({
					'title' : 33228,
					'items' : [
						{ 'title' : 33497, 'value' : total },
						{ 'title' : 33367, 'value' : remaining },
						{ 'title' : 33754, 'value' : consumed },
						{ 'title' : 33751, 'value' : consumedWeb },
						{ 'title' : 33752, 'value' : consumedNntp },
						{ 'title' : 33753, 'value' : consumedNntpUnlimited },
					]
				})

				# Dialog
				interface.Loader.hide()
				interface.Dialog.information(title = title, items = items)
			else:
				interface.Loader.hide()
				interface.Dialog.confirm(title = title, message = interface.Translation.string(33352) % EasyNewsInterface.Name)
		else:
			interface.Loader.hide()
			interface.Dialog.confirm(title = title, message = interface.Translation.string(33351) % EasyNewsInterface.Name)

		return valid
