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
# ORIONAPI
##############################################################################
# API connection and queries to the Orion server
##############################################################################

import copy
import threading
from orion.modules.oriontools import *
from orion.modules.orionsettings import *
from orion.modules.orioninterface import *
from orion.modules.orionnetworker import *

class OrionApi:

	##############################################################################
	# CONSTANTS
	##############################################################################

	# Used by OrionSettings.
	# Determines which API results to not show a notification for.
	TypesEssential = ['userlogin', 'abuseregister']
	TypesNonessential = ['exception', 'success', 'streammissing']
	TypesBlock = ['streamvoteabuse', 'streamremoveabuse']

	ParameterMode = 'mode'
	ParameterAction = 'action'
	ParameterKeyApp = 'keyapp'
	ParameterKeyUser = 'keyuser'
	ParameterKey = 'key'
	ParameterId = 'id'
	ParameterEmail = 'email'
	ParameterUser = 'user'
	ParameterPassword = 'password'
	ParameterLink = 'link'
	ParameterLinks = 'links'
	ParameterResult = 'result'
	ParameterQuery = 'query'
	ParameterStatus = 'status'
	ParameterType = 'type'
	ParameterItem = 'item'
	ParameterStream = 'stream'
	ParameterToken = 'token'
	ParameterDescription = 'description'
	ParameterMessage = 'message'
	ParameterData = 'data'
	ParameterCount = 'count'
	ParameterTotal = 'total'
	ParameterRequested = 'requested'
	ParameterRetrieved = 'retrieved'
	ParameterTime = 'time'
	ParameterDirection = 'direction'
	ParameterVersion = 'version'
	ParameterCategory = 'category'
	ParameterSubject = 'subject'
	ParameterFiles = 'files'
	ParameterAll = 'all'

	StatusUnknown = 'unknown'
	StatusBusy = 'busy'
	StatusSuccess = 'success'
	StatusError = 'error'

	ModeStream = 'stream'
	ModeContainer = 'container'
	ModeApp = 'app'
	ModeUser = 'user'
	ModeTicket = 'ticket'
	ModeNotification = 'notification'
	ModePromotion = 'promotion'
	ModeServer = 'server'
	ModeAddon = 'addon'
	ModeCoupon = 'coupon'
	ModeFlare = 'flare'

	ActionAdd = 'add'
	ActionUpdate = 'update'
	ActionRetrieve = 'retrieve'
	ActionAnonymous = 'anonymous'
	ActionDownload = 'download'
	ActionLogin = 'login'
	ActionRemove = 'remove'
	ActionIdentifier = 'identifier'
	ActionSegment = 'segment'
	ActionHash = 'hash'
	ActionVote = 'vote'
	ActionTest = 'test'
	ActionRedeem = 'redeem'
	ActionVersion = 'version'
	ActionStatus = 'status'

	TypeMovie = 'movie'
	TypeShow = 'show'

	AddonKodi = 'kodi'

	StreamTorrent = 'torrent'
	StreamUsenet = 'usenet'
	StreamHoster = 'hoster'

	AudioStandard = 'standard'
	AudioDubbed = 'dubbed'

	SubtitleSoft = 'soft'
	SubtitleHard = 'hard'

	VoteUp = 'up'
	VoteDown = 'down'

	DataJson = 'json'
	DataRaw = 'raw'
	DataBoth = 'both'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		self.mStatus = None
		self.mType = None
		self.mDescription = None
		self.mMessage = None
		self.mData = None

	##############################################################################
	# DESTRUCTOR
	##############################################################################

	def __del__(self):
		pass

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _keyInternal(self):
		key = OrionSettings.getString('internal.api.orion', raw = True, obfuscate = True)
		if not key:
			if OrionSettings.adapt():
				key = OrionSettings.getString('internal.api.orion', raw = True, obfuscate = True)
			if not key:
				OrionInterface.dialogConfirm(message = 33038)
				OrionTools.quit()
		return key

	def _logMessage(self):
		result = []
		if not self.mStatus == None: result.append(self.mStatus)
		if not self.mType == None: result.append(self.mType)
		if not self.mDescription == None: result.append(self.mDescription)
		if not self.mMessage == None: result.append(self.mMessage)
		return ' | '.join(result)

	##############################################################################
	# REQUEST
	##############################################################################

	def _request(self, mode = None, action = None, parameters = {}, data = DataJson, silent = False):
		self.mStatus = None
		self.mType = None
		self.mDescription = None
		self.mMessage = None
		self.mData = None

		result = None
		networker = None

		debug = not OrionSettings.silent()
		identifier = ''

		try:
			if not mode == None: parameters[OrionApi.ParameterMode] = mode
			if not action == None: parameters[OrionApi.ParameterAction] = action

			from orion.modules.orionapp import OrionApp
			keyApp = OrionApp.instance().key()
			if keyApp == None and mode == OrionApi.ModeApp and action == OrionApi.ActionRetrieve: keyApp = self._keyInternal()
			if not keyApp == None and not keyApp == '': parameters[OrionApi.ParameterKeyApp] = keyApp

			from orion.modules.orionuser import OrionUser
			user = OrionUser.instance()
			keyUser = user.key()
			if not keyUser == None and not keyUser == '': parameters[OrionApi.ParameterKeyUser] = keyUser

			if debug:
				query = copy.deepcopy(parameters)
				if query:
					truncate = [OrionApi.ParameterId, OrionApi.ParameterPassword, OrionApi.ParameterKey, OrionApi.ParameterKeyApp, OrionApi.ParameterKeyUser, OrionApi.ParameterData, OrionApi.ParameterLink, OrionApi.ParameterLinks, OrionApi.ParameterFiles]
					for key, value in OrionTools.iterator(query):
						if key in truncate: query[key] = '-- truncated --'
				queryString = OrionTools.jsonTo(query)
				identifier = ' [' + OrionTools.hash(queryString)[:5] + ']'
				OrionTools.log('Orion API Request' + identifier + ': ' + queryString)

			networker = OrionNetworker(
				link = OrionTools.linkApi(),
				parameters = parameters,
				headers = {'Premium' : 1 if user.subscriptionPackagePremium() else 0},
				timeout = max(30, OrionSettings.getInteger('general.scraping.timeout')),
				agent = OrionNetworker.AgentOrion,
				debug = debug
			)

			result = networker.request()
			if data == self.DataBoth:
				if not OrionTools.jsonIs(result): return result
			elif data == self.DataRaw:
				return {'status' : networker.status(), 'headers' : networker.headersResponse(), 'body' : result, 'response' : networker.response()}
			json = OrionTools.jsonFrom(result)

			result = json[OrionApi.ParameterResult]
			if OrionApi.ParameterStatus in result: self.mStatus = result[OrionApi.ParameterStatus]
			if OrionApi.ParameterType in result: self.mType = result[OrionApi.ParameterType]
			if OrionApi.ParameterDescription in result: self.mDescription = result[OrionApi.ParameterDescription]
			if OrionApi.ParameterMessage in result: self.mMessage = result[OrionApi.ParameterMessage]

			if OrionApi.ParameterData in json: self.mData = json[OrionApi.ParameterData]

			if self.mStatus == OrionApi.StatusError:
				if debug:
					OrionTools.log('Orion API Error' + identifier + ': ' + self._logMessage())
				if not silent and OrionSettings.silentAllow(self.mType):
					OrionInterface.dialogNotification(title = 32048, message = self.mDescription, icon = OrionInterface.IconError)
			elif self.mStatus == OrionApi.StatusSuccess:
				if debug:
					OrionTools.log('Orion API Success' + identifier + ': ' + self._logMessage())
				if not silent and OrionSettings.silentAllow(self.mStatus):
					if mode == OrionApi.ModeStream:
						if action == OrionApi.ActionVote:
							OrionInterface.dialogNotification(title = 32202, message = 33029, icon = OrionInterface.IconSuccess)
						elif action == OrionApi.ActionRemove:
							OrionInterface.dialogNotification(title = 32203, message = 33030, icon = OrionInterface.IconSuccess)
						elif action == OrionApi.ActionRetrieve:
							count = self.mData[OrionApi.ParameterCount]
							message = OrionTools.translate(32062) + ': ' + str(count[OrionApi.ParameterTotal]) + ' • ' + OrionTools.translate(32063) + ': ' + str(count[OrionApi.ParameterRetrieved])
							OrionTools.log('Orion Streams Found' + identifier + ': ' + message)
							notifications = []
							if self.mDescription: notifications.append({'title' : self.mDescription, 'message' : self.mMessage, 'icon' : OrionInterface.IconInformation})
							notifications.append({'title' : 32060, 'message' : message, 'icon' : OrionInterface.IconSuccess})
							thread = threading.Thread(target = self._notification, args = (notifications,))
							thread.start()
					elif mode == OrionApi.ModeContainer:
						if action == OrionApi.ActionRetrieve:
							count = self.mData[OrionApi.ParameterCount]
							message = OrionTools.translate(32232) + ': ' + str(count[OrionApi.ParameterRequested]) + ' • ' + OrionTools.translate(32233) + ': ' + str(count[OrionApi.ParameterRetrieved])
							OrionTools.log('Orion Containers Found' + identifier + ': ' + message)
						elif action == OrionApi.ActionHash:
							count = self.mData[OrionApi.ParameterCount]
							message = OrionTools.translate(32228) + ': ' + str(count[OrionApi.ParameterRequested]) + ' • ' + OrionTools.translate(32229) + ': ' + str(count[OrionApi.ParameterRetrieved])
							OrionTools.log('Orion Hashes Found' + identifier + ': ' + message)
							# Do not show a notification if hashes are found, especailly if they are requested in chunks, too many popups.
							#OrionInterface.dialogNotification(title = 32227, message = message, icon = OrionInterface.IconSuccess)
		except:
			try:
				self.mStatus = OrionApi.StatusError
				if not networker == None and networker.error() and not silent and debug:
					if not(mode == OrionApi.ModeStream and action == OrionApi.ActionUpdate):
						OrionInterface.dialogNotification(title = 32064, message = 33007, icon = OrionInterface.IconError)
				else:
					if debug:
						OrionTools.error('Orion API Exception' + identifier + '')
						OrionTools.log('Orion API Data' + identifier + ': ' + str(result))
					if not silent and OrionSettings.silentAllow('exception'):
						OrionInterface.dialogNotification(title = 32061, message = 33006, icon = OrionInterface.IconError)
			except:
				OrionTools.error('Orion Unknown API Exception' + identifier)

		return self.statusSuccess()

	##############################################################################
	# NOTIFICATION
	##############################################################################

	@classmethod
	def _notification(self, notifications):
		time = 5000
		single = len(notifications) <= 1
		for notification in notifications:
			OrionInterface.dialogNotification(title = notification['title'], message = notification['message'], icon = notification['icon'], time = time)
			if not single: OrionTools.sleep(time / 1000.0)

	##############################################################################
	# STATUS
	##############################################################################

	def status(self):
		return self.mStatus

	def statusHas(self):
		return not self.mStatus == None

	def statusSuccess(self):
		return self.mStatus == OrionApi.StatusSuccess

	def statusError(self):
		return self.mStatus == OrionApi.StatusError

	##############################################################################
	# TYPE
	##############################################################################

	def type(self):
		return self.mType

	def typeHas(self):
		return not self.mType == None

	##############################################################################
	# DESCRIPTION
	##############################################################################

	def description(self):
		return self.mDescription

	def descriptionHas(self):
		return not self.mDescription == None

	##############################################################################
	# MESSAGE
	##############################################################################

	def message(self):
		return self.mMessage

	def messageHas(self):
		return not self.mMessage == None

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	def dataHas(self):
		return not self.mData == None

	##############################################################################
	# RANGE
	##############################################################################

	@classmethod
	def range(self, value):
		if OrionTools.isArray(value):
			result = ''
			if len(value) == 0: return result
			if len(value) > 1 and not value[0] == None: result += str(value[0])
			result += '_'
			if len(value) > 1 and not value[1] == None: result += str(value[1])
			else: result += str(value[0])
			return result
		else:
			return str(value)

	##############################################################################
	# APP
	##############################################################################

	def appRetrieve(self, id = None, key = None):
		single = False
		if not id == None:
			single = OrionTools.isString(id)
			result = self._request(mode = OrionApi.ModeApp, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterId : id})
		elif not key == None:
			single = OrionTools.isString(key)
			result = self._request(mode = OrionApi.ModeApp, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterKey : key})
		else:
			result = self._request(mode = OrionApi.ModeApp, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterAll : True})
		try:
			if single: self.mData = self.mData[0]
			elif OrionTools.isDictionary(self.mData): self.mData = [self.mData]
		except: pass
		return result

	##############################################################################
	# USER
	##############################################################################

	def userRetrieve(self):
		return self._request(mode = OrionApi.ModeUser, action = OrionApi.ActionRetrieve)

	def userLogin(self, user, password):
		return self._request(mode = OrionApi.ModeUser, action = OrionApi.ActionLogin, parameters = {OrionApi.ParameterUser : user, OrionApi.ParameterPassword : password})

	def userAnonymous(self):
		x = [OrionTools.randomInteger(1,9) for i in range(3)]
		return self._request(mode = OrionApi.ModeUser, action = OrionApi.ActionAnonymous, parameters = {OrionApi.ParameterKey : str(str(x[0])+str(x[1])+str(x[2])+str(x[0]+x[1]*x[2]))[::-1]}, silent = False)

	##############################################################################
	# TICKET
	##############################################################################

	def ticketRetrieve(self, id = None):
		parameters = {}
		if not id == None: parameters[OrionApi.ParameterId] = id
		return self._request(mode = OrionApi.ModeTicket, action = OrionApi.ActionRetrieve, parameters = parameters)

	def ticketAdd(self, category, subject, message, files = None):
		parameters = {OrionApi.ParameterCategory : category, OrionApi.ParameterSubject : subject, OrionApi.ParameterMessage : message}
		if not files == None: parameters[OrionApi.ParameterFiles] = files
		return self._request(mode = OrionApi.ModeTicket, action = OrionApi.ActionAdd, parameters = parameters)

	def ticketUpdate(self, id, message, files = None):
		parameters = {OrionApi.ParameterId : id, OrionApi.ParameterMessage : message}
		if not files == None: parameters[OrionApi.ParameterFiles] = files
		return self._request(mode = OrionApi.ModeTicket, action = OrionApi.ActionUpdate, parameters = parameters)

	def ticketClose(self, id):
		from orion.modules.orionticket import OrionTicket
		return self._request(mode = OrionApi.ModeTicket, action = OrionApi.ActionUpdate, parameters = {OrionApi.ParameterId : id, OrionApi.ParameterStatus : OrionTicket.StatusClosed})

	def ticketStatus(self):
		return self._request(mode = OrionApi.ModeTicket, action = OrionApi.ActionStatus)

	##############################################################################
	# COUPON
	##############################################################################

	def couponRedeem(self, token):
		return self._request(mode = OrionApi.ModeCoupon, action = OrionApi.ActionRedeem, parameters = {OrionApi.ParameterToken : token})

	##############################################################################
	# ADDON
	##############################################################################

	def addonRetrieve(self, silent = True):
		return self._request(mode = OrionApi.ModeAddon, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterType : OrionApi.AddonKodi}, silent = silent)

	def addonUpdate(self, data, silent = True):
		return self._request(mode = OrionApi.ModeAddon, action = OrionApi.ActionUpdate, parameters = {OrionApi.ParameterType : OrionApi.AddonKodi, OrionApi.ParameterData : data}, silent = silent)

	def addonVersion(self, silent = True):
		return self._request(mode = OrionApi.ModeAddon, action = OrionApi.ActionVersion, silent = silent)

	##############################################################################
	# STREAM
	##############################################################################

	def streamRetrieve(self, filters):
		return self._request(mode = OrionApi.ModeStream, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterData : filters})

	def streamUpdate(self, item):
		return self._request(mode = OrionApi.ModeStream, action = OrionApi.ActionUpdate, parameters = {OrionApi.ParameterData : item})

	def streamVote(self, item, stream, vote = VoteUp, silent = True):
		return self._request(mode = OrionApi.ModeStream, action = OrionApi.ActionVote, parameters = {OrionApi.ParameterItem : item, OrionApi.ParameterStream : stream, OrionApi.ParameterDirection : vote}, silent = silent)

	def streamRemove(self, item, stream, silent = True):
		return self._request(mode = OrionApi.ModeStream, action = OrionApi.ActionRemove, parameters = {OrionApi.ParameterItem : item, OrionApi.ParameterStream : stream}, silent = silent)

	##############################################################################
	# CONTAINER
	##############################################################################

	def containerRetrieve(self, links):
		return self._request(mode = OrionApi.ModeContainer, action = OrionApi.ActionRetrieve, parameters = {OrionApi.ParameterLinks : links})

	def containerIdentifier(self, links):
		return self._request(mode = OrionApi.ModeContainer, action = OrionApi.ActionIdentifier, parameters = {OrionApi.ParameterLinks : links})

	def containerHash(self, links):
		return self._request(mode = OrionApi.ModeContainer, action = OrionApi.ActionHash, parameters = {OrionApi.ParameterLinks : links})

	def containerSegment(self, links):
		return self._request(mode = OrionApi.ModeContainer, action = OrionApi.ActionSegment, parameters = {OrionApi.ParameterLinks : links})

	def containerDownload(self, id):
		data = self._request(mode = OrionApi.ModeContainer, action = OrionApi.ActionDownload, parameters = {OrionApi.ParameterId : id}, data = self.DataBoth)
		return None if OrionTools.isBoolean(data) else data

	##############################################################################
	# NOTIFICATION
	##############################################################################

	def notificationRetrieve(self, time = None, count = None):
		parameters = {}
		parameters[OrionApi.ParameterVersion] = OrionTools.addonVersion()
		if not time == None: parameters[OrionApi.ParameterTime] = time
		if not count == None: parameters[OrionApi.ParameterCount] = count
		return self._request(mode = OrionApi.ModeNotification, action = OrionApi.ActionRetrieve, parameters = parameters)

	##############################################################################
	# PROMOTION
	##############################################################################

	def promotionRetrieve(self):
		return self._request(mode = OrionApi.ModePromotion, action = OrionApi.ActionRetrieve)

	##############################################################################
	# SERVER
	##############################################################################

	def serverRetrieve(self, time = None):
		parameters = {}
		if not time == None: parameters[OrionApi.ParameterTime] = time
		return self._request(mode = OrionApi.ModeServer, action = OrionApi.ActionRetrieve, parameters = parameters)

	def serverTest(self):
		return self._request(mode = OrionApi.ModeServer, action = OrionApi.ActionTest)

	##############################################################################
	# FLARE
	##############################################################################

	def flare(self, link):
		return self._request(mode = OrionApi.ModeFlare, parameters = {OrionApi.ParameterLink : link}, data = self.DataRaw)
