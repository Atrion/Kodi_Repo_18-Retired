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

import threading
from resources.lib.extensions import tools
from resources.lib.extensions import network
from resources.lib.extensions import convert

class Api(object):

	# Only use 32 characters.
	# Remove 0, O, 1, I, due to looking similar, in case the user has to enter the ID.
	Alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'

	Link = tools.Settings.getString('link.api', raw = True)

	ParameterType = 'type'
	ParameterAction = 'action'
	ParameterKey = 'key'
	ParameterTime = 'time'
	ParameterService = 'service'
	ParameterMode = 'mode'
	ParameterSelection = 'selection'
	ParameterContinent = 'continent'
	ParameterCountry = 'country'
	ParameterRegion = 'region'
	ParameterCity = 'city'
	ParameterCount = 'count'
	ParameterDetails = 'details'
	ParameterLast = 'last'
	ParameterId = 'id'
	ParameterName = 'name'
	ParameterVersion = 'version'
	ParameterSuccess = 'success'
	ParameterError = 'error'
	ParameterData = 'data'
	ParameterCurrency = 'currency'
	ParameterLink = 'link'

	TypeFlare = 'flare'
	TypeSpeedtest = 'speedtest'
	TypeUser = 'user'
	TypeDevice = 'device'
	TypeStatistics = 'statistics'
	TypeDonations = 'donations'
	TypeAnnouncements = 'announcements'
	TypePromotions = 'promotions'
	TypeSupport = 'support'

	ActionAdd = 'add'
	ActionRetrieve = 'retrieve'
	ActionUpdate = 'update'
	ActionList = 'list'
	ActionCategories = 'categories'

	SelectionAll = 'all'
	SelectionAverage = 'average'
	SelectionMaximum = 'maximum'
	SelectionMinimum = 'minimum'

	ServiceNone = None
	ServiceGlobal = 'global'
	ServicePremiumize = 'premiumize'
	ServiceOffCloud = 'offcloud'
	ServiceRealDebrid = 'realdebrid'
	ServiceEasyNews = 'easynews'

	@classmethod
	def _idSplit(self, data, size = 2):
		result = []
		for i in range(0, len(data), size):
			result.append(list(data[i : i + size]))
		return result

	@classmethod
	def id(self, data):
		data = tools.Hash.sha256(data)
		data = self._idSplit(data)
		data = [int(i[0], 16) + int(i[1], 16) for i in data]
		data = [Api.Alphabet[i] for i in data]
		return ''.join(data)

	@classmethod
	def idDevice(self):
		return self.id(tools.Hardware.identifier())

	@classmethod
	def _request(self, type = None, action = None, parameters = {}, raw = False):
		if not type == None: parameters[Api.ParameterType] = type
		if not action == None: parameters[Api.ParameterAction] = action

		time = tools.Time.timestamp()
		parameters[Api.ParameterKey] = tools.Hash.sha256(tools.Converter.base64From(tools.Settings.getString(tools.Converter.base64From('aW50ZXJuYWwuYXBp'), raw = True), 15 % 10) + str(time) + tools.System.name().lower())
		parameters[Api.ParameterTime] = time
		try:
			result = network.Networker(link = Api.Link, parameters = parameters).retrieve(addon = True)
			if raw:
				return result
			else:
				result = tools.Converter.jsonFrom(result)
				if result['success']: return result['data']
				else: return None
		except:
			return None

	@classmethod
	def lotteryValid(self):
		return tools.Time.timestamp() < tools.Settings.getInteger('general.statistics.lottery.time.expiry')

	@classmethod
	def _lotteryUpdate(self, result):
		if result and 'lottery' in result:
			result = result['lottery']
			if result['won']:
				tools.Settings.set('general.statistics.lottery.type', result['type'])
				tools.Settings.set('general.statistics.lottery.voucher', result['voucher'])
				tools.Settings.set('general.statistics.lottery.description', result['description'])
				tools.Settings.set('general.statistics.lottery.instruction', result['instruction'])
				tools.Settings.set('general.statistics.lottery.time.claim', result['time']['claim'])
				tools.Settings.set('general.statistics.lottery.time.expiry', result['time']['expiry'])
				tools.Settings.set('general.statistics.lottery.time.duration', result['time']['duration'])
				self.lotteryVoucher()

	@classmethod
	def _lotterVideo(self):
		from resources.lib.extensions import interface
		path = tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'video', 'lottery', 'Gaia.m3u')
		player = interface.Player()
		if not player.isPlaying():
			player.play(path)

	@classmethod
	def lotteryDialog(self):
		from resources.lib.extensions import interface
		type = tools.Settings.getString('general.statistics.lottery.type')
		voucher = tools.Settings.getString('general.statistics.lottery.voucher')
		description = tools.Settings.getString('general.statistics.lottery.description')
		instruction = tools.Settings.getString('general.statistics.lottery.instruction')
		timeClaim = tools.Settings.getInteger('general.statistics.lottery.time.claim')
		timeExpiry = tools.Settings.getInteger('general.statistics.lottery.time.expiry')
		timeDuration = tools.Settings.getInteger('general.statistics.lottery.time.duration')
		indent = '     '
		message = interface.Format.bold(interface.Translation.string(33875)) + interface.Format.newline()
		message += '%s%s: %s' % (indent, interface.Translation.string(33343), interface.Format.bold(type)) + interface.Format.newline()
		message += '%s%s: %s' % (indent, interface.Translation.string(33876), interface.Format.bold(voucher)) + interface.Format.newline()
		if description:
			message += '%s%s: %s' % (indent, interface.Translation.string(33040), interface.Format.bold(description)) + interface.Format.newline()
		if instruction:
			message += instruction
			if not message.endswith('.'): message += '.'
		if timeExpiry and timeDuration:
			expirationDuration = convert.ConverterDuration(timeDuration, convert.ConverterDuration.UnitSecond).string(format = convert.ConverterDuration.FormatWordLong, unit = convert.ConverterDuration.UnitDay)
			expirationTime = convert.ConverterTime(timeExpiry, convert.ConverterTime.FormatTimestamp).string(format = convert.ConverterTime.FormatDate)
			expiration = '%s (%s)' % (expirationDuration, expirationTime)
			message += ' ' + (interface.Translation.string(33877) % expiration)
		message += ' ' + interface.Translation.string(33878)

		interface.Dialog.confirm(title = 33879, message = message)
		interface.Player().stop()

	@classmethod
	def lotteryVoucher(self):
		lotteryType = tools.Settings.getString('general.statistics.lottery.type')
		lotteryVoucher = tools.Settings.getString('general.statistics.lottery.voucher')
		if not lotteryType == None and not lotteryType == '' and not lotteryVoucher == None and not lotteryVoucher == '':
			self._lotterVideo()
			tools.Time.sleep(3)
			self.lotteryDialog()

	@classmethod
	def donations(self, currency = None):
		parameters = {}
		if not currency == None: parameters[Api.ParameterCurrency] = currency
		return self._request(type = Api.TypeDonations, action = Api.ActionRetrieve, parameters = parameters)

	@classmethod
	def announcements(self, last = None, version = None):
		parameters = {}
		if not last == None and not last == '': parameters[Api.ParameterLast] = last
		if not version == None and not version == '': parameters[Api.ParameterVersion] = version
		return self._request(type = Api.TypeAnnouncements, action = Api.ActionRetrieve, parameters = parameters)

	@classmethod
	def promotions(self):
		return self._request(type = Api.TypePromotions, action = Api.ActionRetrieve)

	@classmethod
	def supportCategories(self):
		return self._request(type = Api.TypeSupport, action = Api.ActionCategories)

	@classmethod
	def supportList(self, category = None):
		parameters = {}
		if not category == None and not category == '': parameters[Api.ParameterId] = category
		return self._request(type = Api.TypeSupport, action = Api.ActionList, parameters = parameters)

	@classmethod
	def supportQuestion(self, id):
		parameters = {}
		parameters[Api.ParameterId] = id
		return self._request(type = Api.TypeSupport, action = Api.ActionRetrieve, parameters = parameters)

	@classmethod
	def deviceUpdate(self, data):
		data['identifier'] = self.idDevice()
		parameters = {}
		parameters[Api.ParameterData] = tools.Converter.jsonTo(data)
		result = self._request(type = Api.TypeDevice, action = Api.ActionUpdate, parameters = parameters)
		self._lotteryUpdate(result)

	@classmethod
	def speedtestAdd(self, data):
		data['device'] = self.idDevice()
		parameters = {}
		parameters[Api.ParameterData] = tools.Converter.jsonTo(data)
		result = self._request(type = Api.TypeSpeedtest, action = Api.ActionAdd, parameters = parameters)
		self._lotteryUpdate(result)

	@classmethod
	def speedtestRetrieve(self, service, selection, continent, country, region, city):
		parameters = {}
		if not service == Api.ServiceNone: parameters[Api.ParameterService] = service
		parameters[Api.ParameterSelection] = selection
		parameters[Api.ParameterContinent] = continent
		parameters[Api.ParameterCountry] = country
		parameters[Api.ParameterRegion] = region
		parameters[Api.ParameterCity] = city
		return self._request(type = Api.TypeSpeedtest, action = Api.ActionRetrieve, parameters = parameters)

	@classmethod
	def flare(self, link):
		parameters = {}
		parameters[Api.ParameterLink] = link
		return self._request(type = Api.TypeFlare, parameters = parameters, raw = True)
