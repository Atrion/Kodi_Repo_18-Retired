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

import urllib
import time
import xbmc
import xbmcaddon
import threading

from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import network

class Vpn(object):

	ExecutionKodi = 'kodi'
	ExecutionGaia = 'gaia'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		pass

	##############################################################################
	# INTERNAL
	##############################################################################

	def _information(self, loader = True):
		if loader: interface.Loader.show()
		information = network.Networker.information()
		information = information['global']
		try: informationAddress = information['connection']['address']
		except: informationAddress = interface.Translation.string(33702)
		try: informationProvider = information['connection']['provider']
		except: informationProvider = interface.Translation.string(33702)
		try:
			information = information['location']
			informationLocation = ''

			if 'city' in information:
				informationLocation += information['city']['name']
			elif 'region' in information:
				informationLocation += information['region']['name']

			if not informationLocation == '' and ('country' in information or 'continent' in information):
				informationLocation += ', '

			if 'country' in information:
				informationLocation += information['country']['name']
			elif 'continent' in information:
				informationLocation += information['continent']['name']
		except: informationLocation = interface.Translation.string(33702)
		if loader: interface.Loader.hide()
		return (informationAddress, informationProvider, informationLocation)

	def _mask(self, address):
		while address.endswith('.0') or address.endswith('.*'):
			address = address[:-2]
		return address

	##############################################################################
	# VERIFICATION
	##############################################################################

	def _verification(self, loader = False):
		try:
			mask = tools.Settings.getString('general.vpn.mask')
			if mask == None or mask == '' or mask == '0.0.0.0':
				return (None, '', '', '')
			informationAddress, informationProvider, informationLocation = self._information(loader = loader)

			detection = tools.Settings.getInteger('general.vpn.detection')
			valid = informationAddress.startswith(self._mask(mask))
			if detection == 1: valid = not valid

			return (valid, informationAddress, informationProvider, informationLocation)
		except:
			tools.Logger.error()
			return (False, '', '', '')

	def verification(self, settings = False, background = False, showSuccess = True, showError = True):
		success = None
		try:
			informationVerification, informationAddress, informationProvider, informationLocation = self._verification(loader = not background)
			if informationVerification == True:
				message = 33839
				notification = 33826
				icon = interface.Dialog.IconSuccess
				success = True
			elif informationVerification == False:
				message = 33828
				notification = 33827
				icon = interface.Dialog.IconError
				success = False
			else:
				choice = interface.Dialog.option(title = 33801, message = 35047)
				interface.Loader.hide()
				if choice: self.configuration()
				return False

			message = interface.Translation.string(message) % (informationAddress, informationProvider, informationLocation)
			if background:
				if (success and showSuccess) or (not success and showError):
					interface.Dialog.notification(title = 33801, message = notification, icon = icon)
			if not background or not success:
				if (success and showSuccess) or (not success and showError):
					interface.Dialog.confirm(title = 33842, message = message)
		except:
			tools.Logger.error()
			if success == None and showError:
				if background:
					interface.Dialog.notification(title = 33801, message = notification, icon = icon)
				else:
					interface.Dialog.confirm(title = 33842, message = 33840)

		interface.Loader.hide()
		if settings: self.settings()
		if success == None: success = False
		return success

	##############################################################################
	# CONFIGURATION
	##############################################################################

	def configuration(self, settings = False, title = 33841, finish = 33832, introduction = True):
		success = None
		try:
			unknown = interface.Translation.string(33702)
			counter = 0

			if introduction:
				message = 33822
				choice = interface.Dialog.option(title = title, message = message, labelConfirm = 33743, labelDeny = 33821)
				if choice:
					success = False
					raise Exception()

			message = 33823
			choice = interface.Dialog.option(title = title, message = message, labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()

			informationAddress, informationProvider, informationLocation = self._information()

			message = interface.Translation.string(33824) % (informationAddress, informationProvider, informationLocation)
			choice = interface.Dialog.option(title = title, message = message, labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()
			elif informationAddress == unknown:
				raise Exception('Unknown IP Address')
			elif not '.' in informationAddress:
				raise Exception('Invalid IP Address: ' + str(informationAddress))

			counter += 1
			index = informationAddress.rfind('.')
			informationPart = informationAddress[:index]
			informationMask = informationPart + '.0'
			informationMaskDisplay = informationPart + '.*'

			message = interface.Translation.string(33830) % informationMaskDisplay
			choice = interface.Dialog.option(title = title, message = message, labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()

			message = 33834
			choice = interface.Dialog.option(title = title, message = message, labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()

			informationAddressNew, informationProviderNew, informationLocationNew = self._information()

			while informationAddressNew.startswith(informationPart):
				while informationAddress == informationAddressNew:
					message = interface.Translation.string(33835) % (informationAddress, informationProvider, informationLocation)
					choice = interface.Dialog.option(title = title, message = message, labelConfirm = 33743, labelDeny = 33821)
					if choice:
						success = False
						raise Exception()
					elif informationAddress == unknown:
						raise Exception('Unknown IP Address')
					elif not '.' in informationAddress:
						raise Exception('Invalid IP Address: ' + str(informationAddress))
					informationAddressNew, informationProviderNew, informationLocationNew = self._information()

				if informationAddressNew.startswith(informationPart):
					informationAddress = informationAddressNew
					informationProvider = informationProviderNew
					informationLocation = informationLocationNew
					index = informationPart.rfind('.')
					if index <= 0:
						raise Exception('ISP and VPN running on the same network')
					counter += 1
					informationPart = informationPart[:index]
					informationMask = informationPart + ('.0' * counter)
					informationMaskDisplay = informationPart + ('.*' * counter)

					message = interface.Translation.string(33830) % informationMaskDisplay
					choice = interface.Dialog.option(title = title, message = message, labelConfirm = 33743, labelDeny = 33821)
					if choice:
						success = False
						raise Exception()

			message = interface.Translation.string(33836) % (informationAddressNew, informationProviderNew, informationLocationNew)
			choice = interface.Dialog.option(title = title, message = message, labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()

			tools.Settings.set('general.vpn.enabled', True)
			tools.Settings.set('general.vpn.detection', 1)
			tools.Settings.set('general.vpn.mask', informationMask)
			message = 33833
			interface.Dialog.option(title = title, message = message, labelConfirm = 33743, labelDeny = finish)

			success = True
		except:
			if success == None:
				tools.Logger.error()
				interface.Dialog.confirm(title = 33841, message = 33829)

		interface.Loader.hide()
		if settings: self.settings()
		if success == None: success = False
		return success

	##############################################################################
	# SETTINGS
	##############################################################################

	def settings(self):
		tools.Settings.launch(category = tools.Settings.CategoryGeneral)

	##############################################################################
	# EXECUTE
	##############################################################################

	def _launchEnabled(self, execution):
		if tools.Settings.getBoolean('general.vpn.enabled'):
			launch = tools.Settings.getInteger('general.vpn.launch')
			if execution == Vpn.ExecutionKodi and (launch == 1 or launch == 3):
				return True
			if execution == Vpn.ExecutionGaia and (launch == 2 or launch == 3):
				return True
		return False

	def launchAutomatic(self):
		self.launch(Vpn.ExecutionKodi)

	def launch(self, execution):
		if self._launchEnabled(execution = execution):
			thread = threading.Thread(target = self._launch, args = (execution,))
			thread.start()

	def _launch(self, execution):
		if self._launchEnabled(execution = execution):
			verified = self.verification(background = True, showSuccess = True, showError = True)

			interval = tools.Settings.getInteger('general.vpn.interval')
			if interval == 0: return
			elif interval == 1: interval = 300
			elif interval == 2: interval = 600
			elif interval == 3: interval = 900
			elif interval == 4: interval = 1800
			elif interval == 5: interval = 2700
			elif interval == 6: interval = 3600
			elif interval == 7: interval = 7200
			elif interval == 8: interval = 10800
			elif interval == 9: interval = 21600
			elif interval == 10: interval = 43200
			elif interval == 11: interval = 86400

			stepInterval = 60 # 1 minute
			steps = interval / stepInterval # 1 minute
			while self._launchEnabled(execution = execution): # Check the settings again, in case user has deactivated it.
				for i in range(steps):
					if xbmc.abortRequested:
						sys.exit()
						return
					time.sleep(stepInterval)
				verified = self.verification(background = True, showSuccess = not verified, showError = verified)
