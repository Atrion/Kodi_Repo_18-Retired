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

import xbmc
import re
import os
import urllib
import urllib2
import urlparse
import json
import threading
import time
import random
import hashlib
import StringIO

from resources.lib.extensions import tools
from resources.lib.extensions import provider
from resources.lib.externals.bittorrent import bencode

# Older Python versions (< 2.7.8) do not have a SSL module.
try: import ssl
except: pass

class Networker(object):

	StatusUnknown = 'unknown'
	StatusOnline = 'online'
	StatusOffline = 'offline'

	ResolveNone = 'none' # Do not resolve. Must be string.
	ResolveProvider = 'provider' # Resolve through the provider only
	ResolveService = 'service' # Resolve through provider and service (such as debrid or URLResolver).
	ResolveDefault = ResolveService

	def __init__(self, link = None, parameters = None, debug = True):
		self.mDebug = debug

		self.mHeadersPost = {} # Must be before self.linkClean().

		# Some scrapers like FilmPalast return a ID array (which is resolved later) instead of a link. In such a case, do not use it.
		if isinstance(link, basestring):
			self.mLink = link
			self.linkClean()
		else:
			self.mLink = ''

		self.mUserAgent = None

		self.mError = False
		self.mErrorCode = None
		self.mHeaders = None
		self.mResponse = None
		self.mData = None
		self.mParameters = parameters

	def __del__(self):
		try:
			# Should be automatically closed by garbage collector in any case.
			if self.mResponse:
				self.mResponse.close()
		except:
			pass

	def debugEnable(self, enable = True):
		self.mDebug = enable

	def debugDisable(self, disable = True):
		self.mDebug = not disable

	@classmethod
	def quote(self, data):
		return urllib2.quote(data)

	@classmethod
	def unquote(self, data):
		return urllib2.unquote(data)

	def resolve(self, source, clean = True, timeout = None, info = False, internal = True, resolve = ResolveDefault): # Use timeout with caution.
		if not resolve: resolve = Networker.ResolveNone
		thread = threading.Thread(target = self._resolve, args = (source, clean, info, internal, resolve))
		thread.start()
		if timeout:
			timestep = 0.1
			for i in range(int(timeout / timestep)):
				time.sleep(timestep)
			if thread.is_alive():
				return None
		else:
			thread.join()
		return self.mLink

	def _resolve(self, source, clean = True, info = False, internal = True, resolve = ResolveDefault):
		# Resolves the link using the providers and urlresolver.
		from resources.lib.extensions import core # Must be imported here due to circular imports.
		self.mLink = core.Core().sourcesResolve(source, info = info, internal = internal, resolve = resolve)['link']
		if clean and self.mLink:
			self.mLink, self.mHeadersPost = self._linkClean(self.mLink)
		return self.mLink

	# If randomize is false, returns the most common user agent, aka Mozilla.
	# User agent required, otherwise getting a lot of 403 errors, becasue servers think you are a bot.
	def userAgent(self, randomize = True, mobile = False, forceRenew = False, addon = False):
		if self.mUserAgent == None or forceRenew:
			if addon:
				self.mUserAgent = tools.Platform.agent()
			elif mobile:
				if randomize:
					agents = ['Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36', 'Apple-iPhone/701.341', 'Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30', 'Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36']
					self.mUserAgent = random.choice(agents)
				else:
					self.mUserAgent = 'Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36'
			else:
				if randomize:
					browserVersions = [['%s.0' % i for i in xrange(18, 43)], ['37.0.2062.103', '37.0.2062.120', '37.0.2062.124', '38.0.2125.101', '38.0.2125.104', '38.0.2125.111', '39.0.2171.71', '39.0.2171.95', '39.0.2171.99', '40.0.2214.93', '40.0.2214.111', '40.0.2214.115', '42.0.2311.90', '42.0.2311.135', '42.0.2311.152', '43.0.2357.81', '43.0.2357.124', '44.0.2403.155', '44.0.2403.157', '45.0.2454.101', '45.0.2454.85', '46.0.2490.71', '46.0.2490.80', '46.0.2490.86', '47.0.2526.73', '47.0.2526.80'], ['11.0']]
					windowsVersions = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2', 'Windows NT 6.1', 'Windows NT 6.0', 'Windows NT 5.1', 'Windows NT 5.0']
					features = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
					agents = ['Mozilla/5.0 ({windowsVersion}{feature}; rv:{browserVersion}) Gecko/20100101 Firefox/{browserVersion}', 'Mozilla/5.0 ({windowsVersion}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browserVersion} Safari/537.36', 'Mozilla/5.0 ({windowsVersion}{feature}; Trident/7.0; rv:{browserVersion}) like Gecko']
					index = random.randrange(len(agents))
					self.mUserAgent = agents[index].format(windowsVersion = random.choice(windowsVersions), feature = random.choice(features), browserVersion = random.choice(browserVersions[index]))
				else:
					self.mUserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
		return self.mUserAgent

	@classmethod
	def _linkClean(self, link):
		# Some URLs contain a | character which is not allowed. It seems that everything after the | are HTTP headers (eg: user-agent, referer, etc).
		# The Kodi media player can handle these links (or is it player.py?), but urllib returns an HTTP error. Remove the part.
		# These headers are used by the downloader.
		headers = {}
		if link:
			try: headers = link.rsplit('|', 1)[1]
			except: headers = ''
			headers = urllib.quote_plus(headers).replace('%3D', '=') if ' ' in headers else headers
			headers = dict(urlparse.parse_qsl(headers))

			index = link.find('|')
			if index >= 0:
				link = link[:index]
		return link, headers

	@classmethod
	def linkIs(self, link, magnet = False):
		if isinstance(link, basestring):
			if magnet: prefix = ('magnet:', 'http://', 'https://', 'ftp://', 'ftps://')
			else: prefix = ('http://', 'https://', 'ftp://', 'ftps://')
			return link.startswith(prefix)
		return False

	@classmethod
	def linkJoin(self, *parts):
		if len(parts) == 0:
			return None
		result = parts[0]
		if result.endswith('/'):
			result = result[:-1]
		for i in range(1, len(parts)):
			if parts[i]:
				result += '/' + str(parts[i])
		return result

	def link(self):
		return self.mLink

	def linkClean(self):
		self.mLink, self.mHeadersPost = self._linkClean(self.mLink)
		return self.mLink

	@classmethod
	def linkParameters(self, dictionary, duplicates = False):
		return urllib.urlencode(dictionary, doseq = duplicates)

	@classmethod
	def linkDomain(self, link, subdomain = False, ip = True):
		try:
			if link.startswith('magnet:'): return None
			result = link.split('://')[1].split('/')[0].split(':')[0].strip()
			ipIs = self.ipIs(result)
			if not ip and ipIs: return None
			if not subdomain and not ipIs: result = '.'.join(result.split('.')[-2:])
			return result
		except: return None

	@classmethod
	def ipIs(self, link):
		return isinstance(link, basestring) and bool(re.match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', link))

	def error(self):
		return self.mError

	def errorCode(self):
		return self.mErrorCode

	def download(self, path, timeout = 30, range = None, flare = True):
		data = self.retrieve(timeout = timeout, range = range, force = False, flare = flare)
		if not data: return False
		tools.File.writeNow(path, data)
		return True

	'''
	form = [
		{
			'name' : 'the attribute name',
			'filename' : 'optional file name',
			'type' : 'optional content-type',
			'data' : 'the form data',
		},
		...
	]
	'''
	def retrieve(self, timeout = 30, range = None, force = False, parameters = None, addon = False, flare = True, form = None):
		try:
			self.mData = None
			result = self.request(timeout = timeout, range = range, force = force, parameters = parameters, addon = addon, flare = flare, form = form)
			if self.mError or result == None:
				return self.mData
			else:
				self.mData = self.mResponse.read()
				self.mResponse.close()
				return self.mData
		except:
			return None

	# range: tuple with range byte start and range byte size - (start, size). Both values can be nonean be None.
	def request(self, timeout = 30, range = None, force = False, parameters = None, headers = None, addon = False, flare = True, form = None):
		try:
			if self.mResponse == None or force:
				self.mError = False
				self.mErrorCode = None
				self.mResponse = None
				self.mData = None
				json = False
				if self.mLink:
					if parameters == None: parameters = self.mParameters
					parametersRaw = parameters
					try:
						if isinstance(parameters, dict):
							for key, value in parameters.iteritems():
								if isinstance(value, dict) or isinstance(value, list) or isinstance(value, tuple):
									json = True
									break
						if json: parameters = tools.Converter.jsonTo(parameters)
						else: parameters = urllib.urlencode(parameters, doseq = True)
					except: pass

					if form == None:
						request = urllib2.Request(self.mLink, data = parameters)
					else:
						if not isinstance(form, list): form = [form]
						boundry = 'X-X-X-' + str(tools.Time.timestamp()) + '-X-X-X'
						self.mHeadersPost['Content-Type'] = 'multipart/form-data; boundary=%s' % boundry

						data = bytearray('', 'utf8')
						for f in form:
							disposition = 'Content-Disposition: form-data; name="%s"' % f['name']
							if 'filename' in form: disposition += '; filename="%s"' % f['filename']
							disposition += '\n'

							data += bytearray('--%s\n' % boundry, 'utf8')
							data += bytearray(disposition, 'utf8')
							if 'type' in f: data += bytearray('Content-Type: %s\n' % f['type'], 'utf8')
							data += bytearray('\n', 'utf8')
							try: data += bytearray(f['data'], 'utf8')
							except: data += f['data']
							data += bytearray('\n', 'utf8')

						data += bytearray('--%s--\n' % boundry, 'utf8')
						request = urllib2.Request(self.mLink, data = data)

					if headers == None: headers = {}
					headers['User-Agent'] = self.userAgent(randomize = True, mobile = False, addon = addon)
					if json: headers['Content-Type'] = 'application/json'

					if not range == None:
						start = 0 if range[0] == None else range[0]
						size = 0 if range[1] == None else range[1]
						if start > 0 or size > 0:
							if size == 0: headers['Range'] = 'bytes=%d-' % start
							else: headers['Range'] = 'bytes=%d-%d' % (start, start + size - 1)

					# Will override User-Agent if present in self.mHeadersPost.
					for key, value in self.mHeadersPost.iteritems():
						headers[key] = value

					for key, value in headers.iteritems():
						request.add_header(key, value)

					try:
						secureContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
						self.mResponse = urllib2.urlopen(request, context = secureContext, timeout = timeout)
					except:
						# SPMC (Python < 2.7.8) does not support TLS. Try to do it wihout SSL/TLS, otherwise bad luck.
						self.mResponse = urllib2.urlopen(request, timeout = timeout)
			return self.mResponse
		except urllib2.HTTPError as error: # HTTP error.
			if flare and error.code == 503 and 'cloudflare' in str(error.info()).lower():
				try:
					from resources.lib.externals.cfscrape import cfscrape
					self.mResponse = cfscrape.CloudflareScraper().request(method = 'GET' if parametersRaw == None else 'POST', url = self.mLink, headers = headers, data = parametersRaw, timeout = timeout)
					if self.mResponse.status_code >= 300:
						self.mError = True
						self.mErrorCode = self.mResponse.status_code
						if self.mDebug: tools.Logger.log(tools.System.name() + " Network Error [" + self.mLink + "]: " + str(self.mErrorCode))
					else:
						self.mData = self.mResponse.content
						self.mHeaders = self.mResponse.headers
					return None # Ensure that the response is not read again.
				except urllib2.HTTPError as error: # HTTP error.
					self.mError = True
					self.mErrorCode = error.code
					if self.mDebug: tools.Logger.log(tools.System.name() + " Network Error [" + self.mLink + "]: " + str(self.mErrorCode))
				except urllib2.URLError as error: # Non-HTTP error, like not able to resolve URL.
					self.mError = True
					self.mErrorCode = error.args
					if self.mDebug: tools.Logger.log(tools.System.name() + " Network Error [" + self.mLink + "]: " + str(self.mErrorCode))
				except: # Other possible errors.
					self.mError = True
					self.mErrorCode = None
					if self.mDebug: tools.Logger.error()
			else:
				self.mError = True
				self.mErrorCode = error.code
				if self.mDebug: tools.Logger.log(tools.System.name() + " Network Error [" + self.mLink + "]: " + str(self.mErrorCode))
		except urllib2.URLError as error: # Non-HTTP error, like not able to resolve URL.
			self.mError = True
			self.mErrorCode = error.args
			if self.mDebug: tools.Logger.log(tools.System.name() + " Network Error [" + self.mLink + "]: " + str(self.mErrorCode))
		except: # Other possible errors.
			self.mError = True
			self.mErrorCode = None
			if self.mDebug: tools.Logger.error()
		return None

	def headers(self, timeout = 30, flare = True, request = True):
		# Returns the HTTP header. Do not retrieve this with HEAD, since some servers return a different or no header with HEAD. Use the header of the GET request instead.
		if request:
			self.mHeaders = None
			self.request(timeout = timeout, flare = flare)

		if not self.mError and self.mHeaders == None:
			if self.mResponse:
				try:
					self.mHeaders = self.mResponse.info().dict
				except:
					tools.Logger.error()
					return self.mHeaders
				# This does not work on SPMC Python 2.6. Do it the long way
				#self.mHeaders = {k.lower(): v for k, v in self.mHeaders.items()} # Make keys lower case.
				headers = {}
				for key, value in self.mHeaders.iteritems():
					headers[key.lower()] = value
				self.mHeaders = headers
			elif request:
				self.mHeaders = None
				self.mError = True

		return self.mHeaders

	def header(self, type, timeout = 30, flare = True, request = True):
		self.headers(timeout = timeout, flare = flare, request = request)
		if self.mHeaders and type in self.mHeaders:
			return self.mHeaders[type]
		else:
			return None

	# Retrieves the file size from the HTTP header.
	def headerSize(self, timeout = 30, flare = True, request = True):
		result = self.header('content-range', timeout = timeout, flare = flare, request = request)
		if result:
			index = result.find('/')
			if index >=0:
				result = result[index + 1 :]
				result = int(result) if isinstance(result, basestring) and result.isdigit() else None
			else:
				result = None
		if result == None: # result might be 0
			result = self.header('content-length', timeout = timeout, flare = flare, request = request)
			if result:
				result = int(result) if isinstance(result, basestring) and result.isdigit() else None
		return result

	# Retrieves the file type/mime from the HTTP header.
	def headerType(self, timeout = 30, flare = True, request = True):
		return self.header('content-type', timeout = timeout)

	# Retrieves the file name from the HTTP header.
	def headerName(self, timeout = 30, flare = True, request = True):
		result = str(self.headers(timeout = timeout, flare = flare, request = request))
		start = result.find('filename="')
		if start > 0:
			start += 10
			result = result[start : result.find('"', start)]
		else:
			result = None
		return result

	# Gets a chunk from an HTTP request.
	def data(self, start = None, size = None, timeout = 30, force = False, flare = False):
		try:
			self.mData = None
			result = self.request(timeout = timeout, range = (start, size), flare = flare)
			if self.mError or result == None:
				return self.mData
			else:
				self.mData = self.mResponse.read()
				self.mResponse.close()
				if result == '': return self.mData
				else: return self.mData
		except:
			return None

	# retrieveFile retrieves and checks the content if text (eg: HTML, XML, JSON).
	def check(self, content = False, retrieveHeaders = True, retrieveFile = True, flare = True, request = True):
		# Checks if the link is valid.
		if not self.mHeaders and retrieveHeaders:
			self.headers(flare = flare, request = request)

		# Certain servers block consecutive or batch calls and mark them as 503 (temporarily unavailable). Simply wait a bit and try again.
		counter = 1 # Already checked once
		while not self.mHeaders and retrieveHeaders and self.mErrorCode == 503 and counter < 3:
			counter += 1
			if self.mResponse:
				self.mResponse.close()
				self.mResponse = None
			time.sleep(0.1)
			self.headers(flare = flare, request = request)

		if not self.mHeaders or self.mError:
			if self.mError: # Server might be temporarily overloaded. Might still be accessible.
				return Networker.StatusUnknown
			else:
				return Networker.StatusOffline
		elif content:
			if 'content-type' in self.mHeaders:
				if any(i in self.mHeaders['content-type'] for i in ['text', 'json']):
					if retrieveFile and self.mResponse:
						data = str(self.mResponse.read()).lower()
						failures = ['not found', 'permission denied', 'access denied', 'forbidden access', 'file unavailable', 'bad file', 'unauthorized', 'file remove', 'payment required', 'method not allowed', 'not acceptable', 'authentication required', 'request timeout', 'unavailable for legal reasons', 'too many request', 'file removed', 'file has been removed', 'removed file', 'file expired'] # Do not be too general, like "copyright", beacuase other links/texts on the page might also those phrases.
						if any(failure in data for failure in failures):
							return Networker.StatusOffline
						else:
							return Networker.StatusUnknown
					else:
						return Networker.StatusUnknown
				else:
					return Networker.StatusOnline
			else:
				return Networker.StatusOnline
		else:
			return Networker.StatusOnline

	@classmethod
	def information(self, obfuscate = False):
		result = {}

		# Local
		localIpAddress = xbmc.getIPAddress()
		localHostName = None
		if localHostName == None or localHostName == '':
			try:
				import platform
				localHostName = platform.node()
			except: pass
		if localHostName == None or localHostName == '':
			try:
				import platform
				localHostName = platform.uname()[1]
			except: pass
		if localHostName == None or localHostName == '':
			try: localHostName = os.uname()[1]
			except: pass
		if localHostName == None or localHostName == '':
			try:
				import socket
				localHostName = socket.gethostname()
			except: pass

		# Global
		globalIpAddress = None
		globalIpName = None
		globalIpType = None
		globalProvider = None
		globalOrganisation = None
		globalSystem = None
		globalContinentCode = None
		globalContinentName = None
		globalCountryCode = None
		globalCountryName = None
		globalRegionCode = None
		globalRegionName = None
		globalCityCode = None # Zip code
		globalCityName = None
		globalLatitude = None
		globalLongitude = None

		if None in [globalIpAddress, globalIpName, globalIpType, globalProvider, globalOrganisation, globalSystem, globalContinentName, globalContinentCode, globalCountryName, globalCountryCode, globalRegionName, globalRegionCode, globalCityName, globalCityCode, globalLatitude, globalLongitude] or '' in [globalIpAddress, globalIpName, globalIpType, globalProvider, globalOrganisation, globalSystem, globalContinentName, globalContinentCode, globalCountryName, globalCountryCode, globalRegionName, globalRegionCode, globalCityName, globalCityCode, globalLatitude, globalLongitude]:
			try:
				result = json.load(urllib2.urlopen('https://tools.keycdn.com/geo.json'))['data']['geo']
				if 'ip' in result and globalIpAddress in [None, '']: globalIpAddress = result['ip']
				if 'rdns' in result and globalIpName in [None, '']: globalIpName = result['rdns']
				if 'continent_code' in result and globalContinentCode in [None, '']: globalContinentCode = result['continent_code']
				if 'country_name' in result and globalCountryName in [None, '']: globalCountryName = result['country_name']
				if 'country_code' in result and globalCountryCode in [None, '']: globalCountryCode = result['country_code']
				if 'city' in result and globalCityName in [None, '']: globalCityName = result['city']
				if 'postal_code' in result and globalCityCode in [None, '']: globalCityCode = str(result['postal_code'])
				if 'latitude' in result and globalLatitude in [None, '']: globalLatitude = str(result['latitude'])
				if 'longitude' in result and globalLongitude in [None, '']: globalLongitude = str(result['longitude'])
			except: pass

		if None in [globalIpAddress, globalIpName, globalIpType, globalProvider, globalOrganisation, globalSystem, globalContinentName, globalContinentCode, globalCountryName, globalCountryCode, globalRegionName, globalRegionCode, globalCityName, globalCityCode, globalLatitude, globalLongitude] or '' in [globalIpAddress, globalIpName, globalIpType, globalProvider, globalOrganisation, globalSystem, globalContinentName, globalContinentCode, globalCountryName, globalCountryCode, globalRegionName, globalRegionCode, globalCityName, globalCityCode, globalLatitude, globalLongitude]:
			try:
				result = json.load(urllib2.urlopen('http://extreme-ip-lookup.com/json/'))
				if 'query' in result and globalIpAddress in [None, '']: globalIpAddress = result['query']
				if 'ipName' in result and globalIpName in [None, '']: globalIpName = result['ipName']
				if 'ipType' in result and globalIpType in [None, '']: globalIpType = result['ipType']
				if 'isp' in result and globalProvider in [None, '']: globalProvider = result['isp']
				if 'org' in result and globalOrganisation in [None, '']: globalOrganisation = result['org']
				if 'continent' in result and globalContinentName in [None, '']: globalContinentName = result['continent']
				if 'country' in result and globalCountryName in [None, '']: globalCountryName = result['country']
				if 'countryCode' in result and globalCountryCode in [None, '']: globalCountryCode = result['countryCode']
				if 'region' in result and globalRegionName in [None, '']: globalRegionName = result['region']
				if 'city' in result and globalCityName in [None, '']: globalCityName = result['city']
				if 'lat' in result and globalLatitude in [None, '']: globalLatitude = str(result['lat'])
				if 'lon' in result and globalLongitude in [None, '']: globalLongitude = str(result['lon'])
			except: pass

		if None in [globalIpAddress, globalIpName, globalIpType, globalProvider, globalOrganisation, globalSystem, globalContinentName, globalContinentCode, globalCountryName, globalCountryCode, globalRegionName, globalRegionCode, globalCityName, globalCityCode, globalLatitude, globalLongitude] or '' in [globalIpAddress, globalIpName, globalIpType, globalProvider, globalOrganisation, globalSystem, globalContinentName, globalContinentCode, globalCountryName, globalCountryCode, globalRegionName, globalRegionCode, globalCityName, globalCityCode, globalLatitude, globalLongitude]:
			try:
				result = json.load(urllib2.urlopen('http://ip-api.com/json'))
				if 'query' in result and globalIpAddress in [None, '']: globalIpAddress = result['query']
				if 'isp' in result and globalProvider in [None, '']: globalProvider = result['isp']
				if 'org' in result and globalOrganisation in [None, '']: globalOrganisation = result['org']
				if 'as' in result and globalSystem in [None, '']: globalSystem = result['as']
				if 'country' in result and globalCountryName in [None, '']: globalCountryName = result['country']
				if 'countryCode' in result and globalCountryCode in [None, '']: globalCountryCode = result['countryCode']
				if 'regionName' in result and globalRegionName in [None, '']: globalRegionName = result['regionName']
				if 'region' in result and globalRegionCode in [None, '']: globalRegionCode = result['region']
				if 'city' in result and globalCityName in [None, '']: globalCityName = result['city']
				if 'zip' in result and globalCityCode in [None, '']: globalCityCode = str(result['zip'])
				if 'lat' in result and globalLatitude in [None, '']: globalLatitude = str(result['lat'])
				if 'lon' in result and globalLongitude in [None, '']: globalLongitude = str(result['lon'])
			except: pass

		if None in [globalIpAddress, globalIpName, globalIpType, globalProvider, globalOrganisation, globalSystem, globalContinentName, globalContinentCode, globalCountryName, globalCountryCode, globalRegionName, globalRegionCode, globalCityName, globalCityCode, globalLatitude, globalLongitude] or '' in [globalIpAddress, globalIpName, globalIpType, globalProvider, globalOrganisation, globalSystem, globalContinentName, globalContinentCode, globalCountryName, globalCountryCode, globalRegionName, globalRegionCode, globalCityName, globalCityCode, globalLatitude, globalLongitude]:
			try:
				result = json.load(urllib2.urlopen('http://freegeoip.net/json/'))
				if 'ip' in result and globalIpAddress in [None, '']: globalIpAddress = result['ip']
				if 'country_name' in result and globalCountryName in [None, '']: globalCountryName = result['country_name']
				if 'country_code' in result and globalCountryCode in [None, '']: globalCountryCode = result['country_name']
				if 'region_name' in result and globalRegionName in [None, '']: globalRegionName = result['region_name']
				if 'region_code' in result and globalRegionCode in [None, '']: globalRegionCode = result['region_code']
				if 'city' in result and globalCityName in [None, '']: globalCityName = result['city']
				if 'zip' in result and globalCityCode in [None, '']: globalCityCode = str(result['zip'])
				if 'latitude' in result and globalLatitude in [None, '']: globalLatitude = str(result['latitude'])
				if 'longitude' in result and globalLongitude in [None, '']: globalLongitude = str(result['longitude'])
			except: pass

		if obfuscate and not globalIpAddress == None:
			index = globalIpAddress.rfind('.')
			if index > 0:
				globalIpAddress = globalIpAddress[:index]
				globalIpAddress += '.0'
			globalIpName = None

		globalIpAddress = None if globalIpAddress == '' else globalIpAddress
		globalIpName = None if globalIpName == '' else globalIpName
		globalIpType = None if globalIpType == '' else globalIpType
		globalProvider = None if globalProvider == '' else globalProvider
		globalOrganisation = None if globalOrganisation == '' else globalOrganisation
		globalSystem = None if globalSystem == '' else globalSystem
		globalContinentCode = None if globalContinentCode == '' else globalContinentCode
		globalContinentName = None if globalContinentName == '' else globalContinentName
		globalCountryCode = None if globalCountryCode == '' else globalCountryCode
		globalCountryName = None if globalCountryName == '' else globalCountryName
		globalRegionCode = None if globalRegionCode == '' else globalRegionCode
		globalRegionName = None if globalRegionName == '' else globalRegionName
		globalCityCode = None if globalCityCode == '' else globalCityCode
		globalCityName = None if globalCityName == '' else globalCityName
		globalLatitude = None if globalLatitude == '' else globalLatitude
		globalLongitude = None if globalLongitude == '' else globalLongitude

		return {
			'local' : {
				'connection' : {
					'address' : localIpAddress,
					'name' : localHostName,
				},
			},
			'global' : {
				'connection' : {
					'address' : globalIpAddress,
					'name' : tools.Converter.unicode(globalIpName),
					'type' : globalIpType,
					'provider' : tools.Converter.unicode(globalProvider),
					'organisation' : tools.Converter.unicode(globalOrganisation),
					'system' : tools.Converter.unicode(globalSystem),
				},
				'location' : {
					'continent' : {
						'code' : tools.Converter.unicode(globalContinentCode),
						'name' : tools.Converter.unicode(globalContinentName),
					},
					'country' : {
						'code' : tools.Converter.unicode(globalCountryCode),
						'name' : tools.Converter.unicode(globalCountryName),
					},
					'region' : {
						'code' : tools.Converter.unicode(globalRegionCode),
						'name' : tools.Converter.unicode(globalRegionName),
					},
					'city' : {
						'code' : globalCityCode,
						'name' : tools.Converter.unicode(globalCityName),
					},
					'coordinates' : {
						'latitude' : tools.Converter.unicode(globalLatitude),
						'longitude' : tools.Converter.unicode(globalLongitude),
					},
				},
			}
		}

	@classmethod
	def informationDialog(self):
		from resources.lib.extensions import interface

		def value(val1, val2 = None):
			if val1 == None:
				return 'Unknown'
			elif val2 == None:
				return val1
			else:
				return '%s (%s)' % (val1, val2)

		interface.Loader.show()
		items = []
		information = self.information()

		# Local
		data = information['local']
		items.append({
			'title' : 33704,
			'items' : [
				{ 'title' : 33706, 'value' : value(data['connection']['address']) },
				{ 'title' : 33707, 'value' : value(data['connection']['name']) },
			]
		})

		# Global
		data = information['global']
		items.append({
			'title' : 33705,
			'items' : [
				{ 'title' : 33706, 'value' : value(data['connection']['address']) },
				{ 'title' : 33708, 'value' : value(data['connection']['name']) },
				{ 'title' : 33709, 'value' : value(data['connection']['type']) },
				{ 'title' : 33710, 'value' : value(data['connection']['provider']) },
				{ 'title' : 33711, 'value' : value(data['connection']['organisation']) },
				{ 'title' : 33712, 'value' : value(data['connection']['system']) },
				{ 'title' : 33713, 'value' : value(data['location']['continent']['name'], data['location']['continent']['code']) },
				{ 'title' : 33714, 'value' : value(data['location']['country']['name'], data['location']['country']['code']) },
				{ 'title' : 33715, 'value' : value(data['location']['region']['name'], data['location']['region']['code']) },
				{ 'title' : 33716, 'value' : value(data['location']['city']['name'], data['location']['city']['code']) },
				{ 'title' : 33717, 'value' : value(data['location']['coordinates']['latitude']) },
				{ 'title' : 33718, 'value' : value(data['location']['coordinates']['longitude']) },
			]
		})

		interface.Loader.hide()
		interface.Dialog.information(title = 33703, items = items)

class Container(object):

	Separator = '_'

	# Types
	TypeUnknown = None
	TypeTorrent = 'torrent'
	TypeUsenet = 'usenet'
	TypeHoster = 'hoster'

	# Extensions
	ExtensionData = '.dat'
	ExtensionTorrent = '.torrent'
	ExtensionUsenet = '.nzb'
	ExtensionHoster = '.container'

	# Mimes
	MimeData = 'application/octet-stream'
	MimeTorrent = 'application/x-bittorrent'
	MimeUsenet = 'application/x-nzb'
	MimeHoster = 'application/octet-stream'

	# Paths
	PathTemporary = tools.System.temporary()
	PathTemporaryContainer = tools.File.joinPath(PathTemporary, 'containers')
	PathTemporaryContainerData = tools.File.joinPath(PathTemporaryContainer, 'data')
	PathTemporaryContainerTorrent = tools.File.joinPath(PathTemporaryContainer, TypeTorrent)
	PathTemporaryContainerUsenet = tools.File.joinPath(PathTemporaryContainer, TypeUsenet)
	PathTemporaryContainerHoster = tools.File.joinPath(PathTemporaryContainer, TypeHoster)

	# Common Trackers
	# Do not add too many trackers. Anything above 150 trackers in a magnet link will cause a failure on Premiumize, most likeley due to GET/POST size limits.
	# https://ma.ttias.be/open-torrent-tracker-list-2016/
	# http://www.crizmo.com/torrent-tracker-list-2016.html
	Trackers = ['udp://tracker.opentrackr.org:1337/announce', 'http://explodie.org:6969/announce', 'http://mgtracker.org:2710/announce', 'http://tracker.tfile.me/announce', 'udp://9.rarbg.com:2710/announce', 'udp://9.rarbg.me:2710/announce', 'udp://9.rarbg.to:2710/announce', 'udp://tracker.coppersurfer.tk:6969/announce', 'udp://tracker.glotorrents.com:6969/announce', 'udp://tracker.leechers-paradise.org:6969/announce', 'udp://open.demonii.com:1337', 'udp://tracker.openbittorrent.com:80', 'http://90.180.35.128:6969/annonce', 'udp://90.180.35.128:6969/annonce', 'http://announce.torrentsmd.com:6969/announce', 'http://bt.careland.com.cn:6969/announce', 'http://tracker.torrenty.org:6969/announce', 'http://tracker.trackerfix.com/announce', 'http://www.mvgroup.org:2710/announce']

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	# link: link, magnet, or local path.
	# download: automatically download the torrent or NZB file.
	def __init__(self, link, download = False):
		self.linkSet(link)
		self.downloadSet(download)

	##############################################################################
	# INTERNAL
	##############################################################################

	# GENERAL

	def _type(self, link):
		# Check Magnet
		if self._torrentIsMagnet(link = link):
			return Container.TypeTorrent

		# Check Extensions
		if self._torrentIsExtension(link = link):
			return Container.TypeTorrent
		elif self._usenetIsExtension(link = link):
			return Container.TypeUsenet

		# Check Local Files
		if self._torrentIsFile(link = link, local = True):
			return Container.TypeTorrent
		elif self._usenetIsFile(link = link, local = True):
			return Container.TypeUsenet

		# Check Providers
		if self._torrentIsProvider(link = link):
			return Container.TypeTorrent
		elif self._usenetIsProvider(link = link):
			return Container.TypeUsenet

		# Check Online Files
		if self._torrentIsFile(link = link, local = False):
			return Container.TypeTorrent
		elif self._usenetIsFile(link = link, local = False):
			return Container.TypeUsenet

		# No Type Found
		return Container.TypeUnknown

	def _hash(self, link, type = None):
		if type == None:
			type = self._type(link)

		if type == Container.TypeTorrent:
			return self._torrentHash(link)
		elif type == Container.TypeUsenet:
			return self._usenetHash(link)
		else:
			return None

	def _extension(self, link, type = None):
		if type == None:
			type = self._type(link)

		if type == Container.TypeTorrent:
			return Container.ExtensionTorrent
		elif type == Container.TypeUsenet:
			return Container.ExtensionUsenet
		elif type == Container.TypeHoster:
			return Container.ExtensionHoster
		else:
			return None

	def _mime(self, link, type = None):
		if type == None:
			type = self._type(link)

		if type == Container.TypeTorrent:
			return Container.MimeTorrent
		elif type == Container.TypeUsenet:
			return Container.MimeUsenet
		elif type == Container.TypeHoster:
			return Container.MimeHoster
		else:
			return None

	# CACHE

	def _cache(self, link, type = None, lite = False):
		mime = None
		extension = None
		data = None
		path = None
		name = None
		hash = None
		magnet = None

		if not link == None and not link == '':
			magnet = self._torrentIsMagnet(link)
			if magnet:
				type = Container.TypeTorrent
				hash = self._hash(link = link, type = type)
			else:
				if os.path.exists(link):
					path = link
				else:
					id = self._cacheId(link = link)
					path = self._cacheFind(id = id, type = type)

				if path:
					type = self._type(path)
					name = self._cacheName(path = path)
					data = self._cacheData(path = path)

				if self.mDownload and data == None and not self.mNetworker == None:
					counter = 0
					while counter < 3:
						counter += 1
						data = self.mNetworker.data(flare = True)
						name = self.mNetworker.headerName(request = False)

						if data == None or data == '':
							# Certain servers (eg: UsenetCrawler) block consecutive or batch calls and mark them as 503 (temporarily unavailable). Simply wait a bit and try again.
							if self.mNetworker.errorCode() == 503:
								time.sleep(0.1)
							else:
								break
						else:
							self._cacheInitialize()
							if self._usenetIsData(data):
								data = data.replace('\r', '') # Very important, otherwise the usenent bhashes on Premiumize's server and the local hashes won't match, because the local file got some extra \r.
							path = self._cachePath(type = type, id = id, name = name)
							file = open(path, 'wb')
							file.write(data)
							file.close()

							type = self._type(path)
							if not type == Container.TypeUnknown:
								pathNew = self._cachePath(type = type, id = id, name = name)
								tools.File.move(path, pathNew)
								path = pathNew

							break

				base = path if link == None else link
				if not name and not base == None:
					name = tools.File.name(base)

			if not lite and path:
				mime = self._mime(link = path, type = type)
				extension = self._extension(link = path, type = type)
				hash = self._hash(link = path, type = type)

		return {'type' : type, 'hash' : hash, 'name' : name, 'mime' : mime, 'magnet' : magnet, 'link' : link, 'path' : path, 'extension' : extension, 'data' : data}

	def _cacheInitialize(self):
		try:
			tools.File.makeDirectory(Container.PathTemporaryContainerData)
			tools.File.makeDirectory(Container.PathTemporaryContainerTorrent)
			tools.File.makeDirectory(Container.PathTemporaryContainerUsenet)
			tools.File.makeDirectory(Container.PathTemporaryContainerHoster)
		except:
			pass

	def _cacheClear(self):
		try:
			tools.File.delete(Container.PathTemporaryContainer, force = True)
		except:
			pass

	def _cacheId(self, link):
		return tools.Hash.sha1(link)

	def _cachePath(self, type, id, name = None):
		path = None
		try:
			if type == Container.TypeTorrent:
				path = Container.PathTemporaryContainerTorrent
				extension = Container.ExtensionTorrent
			elif type == Container.TypeUsenet:
				path = Container.PathTemporaryContainerUsenet
				extension = Container.ExtensionUsenet
			elif type == Container.TypeHoster:
				path = Container.PathTemporaryContainerHoster
				extension = Container.ExtensionHoster
			else:
				path = Container.PathTemporaryContainerData
				extension = Container.ExtensionData

			if name == None:
				name = id
			else:
				name = id + Container.Separator + name

			if not name.endswith(extension):
				name += extension
			path = tools.File.joinPath(path, name)
		except:
			pass
		return path

	def _cacheName(self, path):
		name = tools.File.name(path)
		if name:
			index = name.find(Container.Separator)
			if index >= 0:
				name = name[index + 1:]
		return name

	def _cacheData(self, path):
		data = None
		try:
			file = open(path, 'rb')
			data = file.read()
			file.close()
		except:
			pass
		return data

	def _cacheFind(self, id, type = None):
		try:
			id = id.lower()

			if type == Container.TypeTorrent: containers = [Container.PathTemporaryContainerTorrent]
			elif type == Container.TypeUsenet: containers = [Container.PathTemporaryContainerUsenet]
			elif type == Container.TypeHoster: containers = [Container.PathTemporaryContainerHoster]
			else: containers = [Container.PathTemporaryContainerTorrent, Container.PathTemporaryContainerUsenet, Container.PathTemporaryContainerHoster]
			containers.append(Container.PathTemporaryContainerData)

			for container in containers:
				if tools.File.existsDirectory(container):
					directories, files = tools.File.listDirectory(container)
					for file in files:
						if file.lower().startswith(id):
							return tools.File.joinPath(container, file)
		except:
			pass
		return None

	# TORRENT

	def _torrentMagnetClean(self, link):
		index = link.find('&')
		if index > 0:
			link = link[:index]
		return link

	def _torrentData(self, path, info = True, pieces = False):
		# NB: Do not add a try-catch here, since other function rely on this to fail.
		file = open(path, 'rb')
		data = file.read()
		file.close()
		data = bencode.bdecode(data)
		if info or pieces:
			data = data['info']
		if pieces:
			data = StringIO.StringIO(data['pieces'])
		return data

	# Link can be a torrent hash or existing magnet link.
	def _torrentMagnet(self, link, title = None, encode = True, trackers = True):
		titleValid = not title == None and not title == ''

		if self._torrentIsMagnet(link):
			start = link.find('&dn=')
			if start >= 0:
				end = link.find('&', start + 4)
				if end >= 0: text = link[start : end]
				else: text = link[start:]
				link = link.replace(text, '')

			if not trackers:
				while True:
					start = link.find('&tr=')
					if start >= 0:
						end = link.find('&', start + 4)
						if end >= 0: text = link[start : end]
						else: text = link[start:]
						link = link.replace(text, '')
					else:
						break
		else:
			link = 'magnet:?xt=urn:btih:' + link

		if titleValid:
			if encode:
				title = urllib.quote(title) # Do not use quote_plus for title, otherwise adds + to title.
			link += '&dn=' + title

		if trackers:
			for tracker in Container.Trackers:
				if encode:
					tracker = urllib.quote(tracker)
				link += '&tr=' + tracker

		# Some magnet links still have the slash /. This seems to be a problem with RealDebrid. Manually escape these slashes.
		link = link.replace('/', '%2F')

		return link

	def _torrentName(self, link):
		try:
			if self._torrentIsMagnet(link):
				result = urlparse.parse_qs(urlparse.urlparse(link).query)['dn']
				if isinstance(result, list): result = result[0]
				return result
			else:
				path = self._cache(link, lite = True)['path']
				info = self._torrentData(path)
				info = bencode.bencode(info)
				return info['name']
		except:
			tools.Logger.error()
			return None

	# local: If true, does not retrieve any data from the internet, only local extensions, names, and files.
	def _torrentIs(self, link, local = False):
		result = self._torrentIsMagnet(link = link) or self._torrentIsExtension(link = link) or self._torrentIsFile(link = link, local = True) or self._torrentIsProvider(link = link)
		if not result and local == False:
			result = self._torrentIsFile(link = link, local = local)
		return result

	def _torrentIsMagnet(self, link):
		try: return link.startswith('magnet:')
		except: return False

	def _torrentIsExtension(self, link, local = False):
		return link.endswith(Container.ExtensionTorrent)

	def _torrentIsFile(self, link, local = False):
		path = None
		if not local and Networker.linkIs(link):
			path = self._cache(link, lite = True)['path']
		else:
			path = link
		try:
			self._torrentData(path) # Will throw an exception if not torrent
			return True
		except:
			return False

	def _torrentIsProvider(self, link):
		providers = provider.Provider.providersTorrent(enabled = True)
		for p in providers:
			for domain in p['domains']:
				if domain in link:
					return True
		return False

	def _torrentHash(self, link):
		hash = self._torrentHashMagnet(link)
		if hash == None:
			hash = self._torrentHashFile(link)
		return hash

	def _torrentHashMagnet(self, link):
		if self._torrentIsMagnet(link):
			try:
				result = re.search('[:-]([a-fA-F\d]{40})', link)
				if result: result = result.group(1) # Group 1, not 0, because group 1 excludes the leading :
				return result.upper()
			except:
				# Most magnets use HEX encoded hashes of length 40.
				# Some new ones use BASE32 encoded hashes of length 32.
				result = re.search('[:-]([a-zA-Z\d]{32})', link)
				if result: result = result.group(1) # Group 1, not 0, because group 1 excludes the leading :
				return result
		else:
			return None

	def _torrentHashFile(self, link):
		try:
			path = self._cache(link, lite = True)['path']
			try:
				info = self._torrentData(path)
				info = bencode.bencode(info)
				return tools.Hash.sha1(info)
			except:
				return None
		except:
			return None

	# USENET

	def _usenetData(self, path):
		file = open(path, 'rb')
		data = file.read()
		file.close()
		return data

	# local: If true, does not retrieve any data from the internet, only local extensions, names, and files.
	def _usenetIs(self, link, local = False):
		result = self._usenetIsExtension(link = link) or self._usenetIsFile(link = link, local = True) or self._usenetIsProvider(link = link)
		if not result and local == False:
			result = self._usenetIsFile(link = link, local = local)
		return result

	def _usenetIsExtension(self, link):
		return link.endswith(Container.ExtensionUsenet)

	def _usenetIsFile(self, link, local = False):
		path = None
		if not local and Networker.linkIs(link):
			path = self._cache(link, lite = True)['path']
		else:
			path = link
		try:
			data = self._usenetData(path)
			return self._usenetIsData(data)
		except:
			pass
		return False

	def _usenetIsData(self, data):
		try:
			if not data == None:
				data = data.lower()
				if '<!doctype nzb' in data or '<nzb>' in data or '</nzb>' in data:
					return True
		except:
			pass
		return False

	def _usenetIsProvider(self, link):
		providers = provider.Provider.providersUsenet(enabled = True)
		for p in providers:
			for domain in p['domains']:
				if domain in link:
					return True
		return False

	def _usenetHash(self, link):
		try:
			path = self._cache(link, lite = True)['path']
			try:
				data = self._usenetData(path)
				return tools.Hash.sha1(data)
			except:
				return None
		except:
			return None

	##############################################################################
	# BASICS
	##############################################################################

	def linkSet(self, link):
		self.mNetworker = None
		if self._torrentIsMagnet(link):
			self.mLink = link
		else:
			self.mNetworker = Networker(link)
			self.mLink = self.mNetworker.link() # Returns the cleaned link.

	def link(self):
		return self.mLink

	def downloadSet(self, download):
		self.mDownload = download

	def download(self):
		return self.mDownload

	def type(self):
		return self._type(self.mLink)

	def extension(self):
		return self._extension(self.mLink)

	def mime(self):
		return self._mime(self.mLink)

	##############################################################################
	# ADVANCED
	##############################################################################

	# Clear local containers.
	def clear(self):
		self._cacheClear()

	# Get the hash of the container.
	def hash(self):
		return self._hash(self.mLink)

	# Cache the container.
	def cache(self):
		result = self._cache(link = self.mLink)
		return not result['data'] == None

	# Returns a dictionary with the container details.
	def information(self):
		return self._cache(link = self.mLink)

	def isFile(self):
		return self.torrentIsFile() or self.usenetIs()

	##############################################################################
	# TORRENT
	##############################################################################

	# Create a magnet from a hash or existing magnet.
	def torrentMagnet(self, title = None, encode = True, trackers = True):
		return self._torrentMagnet(self.mLink, title = title, encode = encode, trackers = trackers)

	# Clean magnet link from name and trackers.
	def torrentMagnetClean(self):
		return self._torrentMagnetClean(self.mLink)

	def torrentName(self):
		return self._torrentName(self.mLink)

	def torrentIs(self):
		return self._torrentIs(self.mLink)

	def torrentIsMagnet(self):
		return self._torrentIsMagnet(self.mLink)

	def torrentIsFile(self):
		return self._torrentIsFile(self.mLink)

	def torrentHash(self):
		return self._torrentHash(self.mLink)

	def torrentHashMagnet(self):
		return self._torrentHashMagnet(self.mLink)

	def torrentHashFile(self):
		return self._torrentHashFile(self.mLink)

	##############################################################################
	# USENET
	##############################################################################

	def usenetIs(self):
		return self._usenetIs(self.mLink)

	def usenetHash(self):
		return self._usenetHash(self.mLink)
