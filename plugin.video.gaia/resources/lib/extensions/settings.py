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

from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import debrid
from resources.lib.extensions import verification
from resources.lib.extensions import provider
from resources.lib.extensions import vpn
from resources.lib.extensions import handler
from resources.lib.extensions import speedtest
from resources.lib.extensions import support
from resources.lib.extensions import orionoid
from resources.lib.modules import trakt

class Selection(object):

	##############################################################################
	# SHOW
	##############################################################################

	@classmethod
	def show(self):
		choice = interface.Dialog.option(title = 33011, message = 33929, labelConfirm = 33893, labelDeny = 33894)
		if choice: return Wizard.show()
		else: return Advanced.show()

class Adaption(object):

	TypeBasic = 'basic'
	TypeFull = 'full'

	##############################################################################
	# SHOW
	##############################################################################

	@classmethod
	def show(self):
		if tools.System.versionKodiNew():
			title = 'Kodi 18'
			interface.Dialog.confirm(title = title, message = 'Kodi 18 has numerous bugs in the new settings dialog. You won\'t be able to scroll through all settings without a mouse. You can use an adapted settings structure that can be used under Kodi 18 without a mouse.')
			choice = interface.Dialog.options(title = title, items = [interface.Format.fontBold('Full Settings With Help Labels: ') + 'Use Kodi with a mouse', interface.Format.fontBold('Basic Settings Without Help Labels: ') + 'Use Kodi without a mouse'])
			if choice >= 0:
				if self.adapt(type = Adaption.TypeFull if choice == 0 else Adaption.TypeBasic, force = True):
					interface.Dialog.notification(title = title, message = 'Settings Successfully Adapted', icon = interface.Dialog.IconSuccess)
				else:
					interface.Dialog.notification(title = title, message = 'Settings Adaptation Failure', icon = interface.Dialog.IconError)

	@classmethod
	def adapt(self, type = None, force = False):
		if tools.System.versionKodiNew():
			result = False
			if type == None: type = tools.Settings.getString('internal.settings')
			if type == '': return result
			path = tools.Settings.pathAddon()
			pathOriginal = path + '.' + type
			if force or not tools.Hash.file(path) == tools.Hash.file(pathOriginal): result = tools.File.copy(pathFrom = pathOriginal, pathTo = path, overwrite = True)
			if result: tools.Settings.set('internal.settings', type)
			return result
		return False

class Advanced(object):

	##############################################################################
	# SHOW
	##############################################################################

	@classmethod
	def show(self, category = None, section = None):
		return tools.Settings.launch(category = category, section = section)

class Wizard(object):

	ChoiceLeft = True
	ChoiceRight = False

	OptionContinue = 'continue'
	OptionCancelStep = 'cancelstep'
	OptionCancelWizard = 'cancelwizard'

	ModeAutomatic = 0
	ModeReaper = 1
	ModeQuick = 2
	ModeExtensive = 3
	ModeManual = 4

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		self.mMode = None

	##############################################################################
	# SHOW
	##############################################################################

	@classmethod
	def _sleep(self, seconds):
		tools.Time.sleep(seconds)

	@classmethod
	def _confirm(self, message, title = 33895):
		return interface.Dialog.confirm(title = title, message = message)

	@classmethod
	def _option(self, message, left, right, title = 33895):
		return interface.Dialog.option(title = title, message = message, labelConfirm = left, labelDeny = right)

	@classmethod
	def _input(self, default = None, title = 33895):
		return interface.Dialog.input(title = title, type = interface.Dialog.InputAlphabetic, default = default)

	@classmethod
	def _cancel(self):
		choice = self._option(33975, 33976, 33977)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelWizard
		else: return Wizard.OptionCancelStep

	@classmethod
	def _showWelcome(self, launch = False):
		self._confirm(33930)
		'''choice = self._confirm(33930, 33342, 33341)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelWizard
		else: return Wizard.OptionContinue'''

	@classmethod
	def _showMode(self):
		minute = interface.Translation.string(35347)
		colors = interface.Format.colorGradient(interface.Format.ColorExcellent, interface.Format.ColorBad, count = 5)
		items = [
			interface.Format.fontBold(interface.Format.fontColor('[ 0 ' + minute + ']  ', colors[0]) + interface.Translation.string(35337) + ': ') + interface.Translation.string(35342),
			interface.Format.fontBold(interface.Format.fontColor('[ 3 ' + minute + ']  ', colors[1]) + interface.Translation.string(35340) + ': ') + interface.Translation.string(35345),
			interface.Format.fontBold(interface.Format.fontColor('[ 5 ' + minute + ']  ', colors[2]) + interface.Translation.string(35338) + ': ') + interface.Translation.string(35343),
			interface.Format.fontBold(interface.Format.fontColor('[10 ' + minute + ']  ', colors[3]) + interface.Translation.string(35339) + ': ') + interface.Translation.string(35344),
			interface.Format.fontBold(interface.Format.fontColor('[15 ' + minute + ']  ', colors[4]) + interface.Translation.string(35341) + ': ') + interface.Translation.string(35346),
		]
		self.mMode = interface.Dialog.options(title = 35348, items = items)
		if self.mMode == Wizard.ModeAutomatic:
			self._showFinish()
			return Wizard.OptionCancelWizard
		elif self.mMode == Wizard.ModeReaper:
			if tools.Backup.reaper():
				return Wizard.OptionContinue
			else:
				return self._showMode()
		elif self.mMode == Wizard.ModeManual:
			tools.Settings.launch()
			tools.Time.sleep(2) # Wait for settings to show
			while tools.Settings.visible():
				tools.Time.sleep(0.5)
			tools.Time.sleep(2)
			while tools.Settings.visible(): # Test again, in case the settings dialog is hidden during config.
				tools.Time.sleep(0.5)
			self._showFinish()
			return Wizard.OptionCancelWizard
		else:
			return Wizard.OptionContinue

	@classmethod
	def _showFinish(self):
		choice = self._option(33974, 33505, 33832)
		tools.System.openLink(tools.Settings.getString('link.website', raw = True), popup = False)
		if choice == Wizard.ChoiceLeft:
			# Do not use navigator().donationsNavigator().
			# This will not update Kodi's directory.
			tools.Donations.show()
		else:
			return Wizard.OptionContinue

	@classmethod
	def _showLanguage(self):
		choice = self._option(33964, 33743, 33821)
		if choice == Wizard.ChoiceLeft: return self._cancel()

		id = 'general.language.primary'
		language = tools.Settings.getString(id)
		language = interface.Translation.string(35046) if language == 'None' else language
		message = interface.Translation.string(35041) % language
		choice = self._option(message, 35045, 35044)
		if choice == Wizard.ChoiceLeft:
			items = tools.Settings.raw(id, 'values').split('|')
			choice = interface.Dialog.select(title = 33895, items = items)
			if choice >= 0: tools.Settings.set(id, items[choice])

		if self.mMode == Wizard.ModeExtensive:
			id = 'general.language.secondary'
			language = tools.Settings.getString(id)
			language = interface.Translation.string(35046) if language == 'None' else language
			message = interface.Translation.string(35042) % language
			choice = self._option(message, 35045, 35044)
			if choice == Wizard.ChoiceLeft:
				items = tools.Settings.raw(id, 'values').split('|')
				choice = interface.Dialog.select(title = 33895, items = items)
				if choice >= 0: tools.Settings.set(id, items[choice])

		'''
		id = 'general.language.tertiary'
		language = tools.Settings.getString(id)
		language = interface.Translation.string(35046) if language == 'None' else language
		message = interface.Translation.string(35043) % language
		choice = self._option(message, 35045, 35044)
		if choice == Wizard.ChoiceLeft:
			items = tools.Settings.raw(id, 'values').split('|')
			choice = interface.Dialog.select(title = 33895, items = items)
			if choice >= 0: tools.Settings.set(id, items[choice])
		'''

	@classmethod
	def _showAccounts(self, first = True):
		if first:
			choice = self._option(35288, 33743, 33821)
			if choice == Wizard.ChoiceLeft: return self._cancel()

		orion = orionoid.Orionoid()
		enabled = interface.Format.fontBold(interface.Format.fontColor(interface.Translation.string(32301), interface.Format.ColorExcellent))
		disabled = interface.Format.fontBold(interface.Format.fontColor(interface.Translation.string(32302), interface.Format.ColorBad))
		special = interface.Translation.string(33105)
		premium = interface.Translation.string(33768)
		provider = interface.Translation.string(33681)
		general = interface.Translation.string(32310)

		items = [
			interface.Format.fontBold(interface.Translation.string(33821)),
			interface.Format.fontBold('[' + special + '] ' + interface.Translation.string(35400) + ': ') + (enabled if orion.accountValid() else disabled),
			interface.Format.fontBold('[' + general + '] ' + interface.Translation.string(32315) + ': ') + (enabled if tools.Settings.getBoolean('accounts.informants.trakt.enabled') else disabled),
			interface.Format.fontBold('[' + general + '] ' + interface.Translation.string(32034) + ': ') + (enabled if tools.Settings.getBoolean('accounts.informants.imdb.enabled') else disabled),
			interface.Format.fontBold('[' + general + '] ' + interface.Translation.string(35260) + ': ') + (enabled if tools.Settings.getBoolean('accounts.artwork.fanart.enabled') else disabled),
			interface.Format.fontBold('[' + premium + '] ' + interface.Translation.string(33566) + ': ') + (enabled if debrid.Premiumize().accountValid() else disabled),
			interface.Format.fontBold('[' + premium + '] ' + interface.Translation.string(35200) + ': ') + (enabled if debrid.OffCloud().accountValid() else disabled),
			interface.Format.fontBold('[' + premium + '] ' + interface.Translation.string(33567) + ': ') + (enabled if debrid.RealDebrid().accountValid() else disabled),
			interface.Format.fontBold('[' + premium + '] ' + interface.Translation.string(33794) + ': ') + (enabled if debrid.EasyNews().accountValid() else disabled),
			interface.Format.fontBold('[' + premium + '] ' + interface.Translation.string(33568) + ': ') + (enabled if debrid.AllDebrid().accountValid() else disabled),
			interface.Format.fontBold('[' + premium + '] ' + interface.Translation.string(33569) + ': ') + (enabled if debrid.RapidPremium().accountValid() else disabled),
		]

		choice = interface.Dialog.options(title = 32346, items = items)
		if choice < 0: return self._cancel()

		if choice == 0:
			return Wizard.OptionContinue
		elif choice == 1:
			if self._showOrion() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard
		elif choice == 2:
			if self._showTrakt() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard
		elif choice == 3:
			if self._showImdb() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard
		elif choice == 4:
			if self._showFanart() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard
		elif choice == 5:
			if self._showPremiumize() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard
		elif choice == 6:
			if self._showOffCloud() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard
		elif choice == 7:
			if self._showRealDebrid() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard
		elif choice == 8:
			if self._showEasyNews() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard
		elif choice == 9:
			if self._showAllDebrid() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard
		elif choice == 10:
			if self._showRapidPremium() == Wizard.OptionCancelWizard: return Wizard.OptionCancelWizard

		return self._showAccounts(first = False)

	@classmethod
	def _showOrion(self):
		try:
			orion = orionoid.Orionoid()
			choice = self._option(35408, 33897, 33898)
			if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
			choice = self._option(35409, 33899, 33900)
			if choice == Wizard.ChoiceLeft:
				tools.System.openLink(orion.link())
				choice = self._option(35410, 33743, 33898)
				if choice == Wizard.ChoiceLeft: return self._cancel()
			while True:
				if orion.accountUpdate(input = True, loader = True):
					orion.accountEnable()
					choice = self._option(35412, 33743, 33821)
					if choice == Wizard.ChoiceLeft: return self._cancel()
					return Wizard.OptionContinue
				else:
					orion.accountDisable()
					choice = self._option(35413, 33743, 33902)
					if choice == Wizard.ChoiceLeft: return self._cancel()
			return Wizard.OptionContinue
		except:
			tools.Logger.error()

	@classmethod
	def _showTrakt(self):
		choice = self._option(33931, 33897, 33898)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
		choice = self._option(33932, 33899, 33900)
		if choice == Wizard.ChoiceLeft:
			tools.System.openLink(tools.Settings.getString('link.trakt', raw = True))
			choice = self._option(33981, 33743, 33898)
			if choice == Wizard.ChoiceLeft: return self._cancel()
		while True:
			tools.Settings.set('accounts.informants.trakt.enabled', True) # Has to be enabled before verification, since trakt.py uses it internally.
			authentication = trakt.authTrakt(openSettings = False)
			interface.Loader.show()
			# Kodi has a problem to set settings, and immediately read them afterwards. It always retruns the old value.
			# Instead, pass the new login information manually.
			valid = trakt.verify(authentication = authentication)
			interface.Loader.hide()
			if valid:
				choice = self._option(33933, 33743, 33821)
				if choice == Wizard.ChoiceLeft: return self._cancel()
				return Wizard.OptionContinue
			else:
				tools.Settings.set('accounts.informants.trakt.enabled', False)
				choice = self._option(33979, 33743, 33902)
				if choice == Wizard.ChoiceLeft: return self._cancel()
		return Wizard.OptionContinue

	@classmethod
	def _showImdb(self):
		choice = self._option(33910, 33897, 33898)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
		choice = self._option(35363, 33899, 33900)
		if choice == Wizard.ChoiceLeft:
			tools.System.openLink(tools.Settings.getString('link.imdb', raw = True))
			choice = self._option(35364, 33743, 33898)
			if choice == Wizard.ChoiceLeft: return self._cancel()
		user = tools.Settings.getString('accounts.informants.imdb.user')
		while True:
			choice = self._option(35365, 33743, 33903)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			user = self._input(default = user)
			interface.Loader.show()
			valid = verification.Verification()._verifyAccountsImdb(checkDisabled = False, user = user) == verification.Verification.StatusOperational
			interface.Loader.hide()
			if valid:
				tools.Settings.set('accounts.informants.imdb.enabled', True)
				tools.Settings.set('accounts.informants.imdb.user', user)
				choice = self._option(35366, 33743, 33821)
				if choice == Wizard.ChoiceLeft: return self._cancel()
				return Wizard.OptionContinue
			else:
				tools.Settings.set('accounts.informants.imdb.enabled', False)
				choice = self._option(35367, 33743, 33902)
				if choice == Wizard.ChoiceLeft: return self._cancel()
		return Wizard.OptionContinue

	@classmethod
	def _showFanart(self):
		choice = self._option(33934, 33897, 33898)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
		choice = self._option(33935, 33899, 33900)
		if choice == Wizard.ChoiceLeft:
			tools.System.openLink(tools.Settings.getString('link.fanart', raw = True))
			choice = self._option(33982, 33743, 33898)
			if choice == Wizard.ChoiceLeft: return self._cancel()
		api = tools.Settings.getString('accounts.artwork.fanart.api')
		while True:
			choice = self._option(33936, 33743, 33901)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			api = self._input(default = api)
			interface.Loader.show()
			valid = verification.Verification()._verifyAccountsFanart(checkDisabled = False, key = api) == verification.Verification.StatusOperational
			interface.Loader.hide()
			if valid:
				tools.Settings.set('accounts.artwork.fanart.enabled', True)
				tools.Settings.set('accounts.artwork.fanart.api', api)
				choice = self._option(33938, 33743, 33821)
				if choice == Wizard.ChoiceLeft: return self._cancel()
				return Wizard.OptionContinue
			else:
				tools.Settings.set('accounts.artwork.fanart.enabled', False)
				choice = self._option(33980, 33743, 33902)
				if choice == Wizard.ChoiceLeft: return self._cancel()
		return Wizard.OptionContinue

	@classmethod
	def _showPremiumize(self):
		choice = self._option(33939, 33897, 33898)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
		choice = self._option(33940, 33899, 33900)
		if choice == Wizard.ChoiceLeft:
			tools.System.openLink(tools.Settings.getString('link.premiumize', raw = True))
			choice = self._option(33986, 33743, 33898)
			if choice == Wizard.ChoiceLeft: return self._cancel()
		while True:
			tools.Settings.set('accounts.debrid.premiumize.enabled', True)
			debrid.PremiumizeInterface().accountAuthentication(openSettings = False)
			interface.Loader.show()
			valid = debrid.Premiumize().accountVerify()
			interface.Loader.hide()
			if valid:
				tools.Settings.set('providers.universal.premium.member.premiumize', True)
				choice = self._option(33944, 33743, 33821)
				if choice == Wizard.ChoiceLeft: return self._cancel()
				return Wizard.OptionContinue
			else:
				tools.Settings.set('accounts.debrid.premiumize.enabled', False)
				choice = self._option(33989, 33743, 33902)
				if choice == Wizard.ChoiceLeft: return self._cancel()
		return Wizard.OptionContinue

	@classmethod
	def _showOffCloud(self):
		choice = self._option(35262, 33897, 33898)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
		choice = self._option(35263, 33899, 33900)
		if choice == Wizard.ChoiceLeft:
			tools.System.openLink(tools.Settings.getString('link.offcloud', raw = True))
			choice = self._option(35266, 33743, 33898)
			if choice == Wizard.ChoiceLeft: return self._cancel()
		api = apiOriginal = tools.Settings.getString('accounts.debrid.offcloud.api')
		while True:
			choice = self._option(35264, 33743, 33901)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			api = self._input(default = api)
			interface.Loader.show()
			tools.Settings.set('accounts.debrid.offcloud.enabled', True)
			tools.Settings.set('accounts.debrid.offcloud.api', api)
			valid = debrid.OffCloud().accountVerify()
			interface.Loader.hide()
			if valid:
				tools.Settings.set('providers.universal.premium.member.offcloud', True)
				choice = self._option(35265, 33743, 33821)
				if choice == Wizard.ChoiceLeft: return self._cancel()
				return Wizard.OptionContinue
			else:
				tools.Settings.set('accounts.debrid.offcloud.enabled', False)
				tools.Settings.set('accounts.debrid.offcloud.api', apiOriginal)
				choice = self._option(35267, 33743, 33902)
				if choice == Wizard.ChoiceLeft: return self._cancel()
		return Wizard.OptionContinue

	@classmethod
	def _showRealDebrid(self):
		choice = self._option(33945, 33897, 33898)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
		choice = self._option(33946, 33899, 33900)
		if choice == Wizard.ChoiceLeft:
			tools.System.openLink(tools.Settings.getString('link.realdebrid', raw = True))
			choice = self._option(33987, 33743, 33898)
			if choice == Wizard.ChoiceLeft: return self._cancel()
		while True:
			tools.Settings.set('accounts.debrid.realdebrid.enabled', True)
			debrid.RealDebridInterface().accountAuthentication(openSettings = False)
			interface.Loader.show()
			valid = debrid.RealDebrid().accountVerify()
			interface.Loader.hide()
			if valid:
				tools.Settings.set('providers.universal.premium.member.realdebrid', True)
				choice = self._option(33947, 33743, 33821)
				if choice == Wizard.ChoiceLeft: return self._cancel()
				return Wizard.OptionContinue
			else:
				tools.Settings.set('accounts.debrid.realdebrid.enabled', False)
				choice = self._option(33990, 33743, 33902)
				if choice == Wizard.ChoiceLeft: return self._cancel()
		return Wizard.OptionContinue

	@classmethod
	def _showEasyNews(self):
		choice = self._option(33948, 33897, 33898)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
		choice = self._option(33949, 33899, 33900)
		if choice == Wizard.ChoiceLeft:
			tools.System.openLink(tools.Settings.getString('link.easynews', raw = True))
			choice = self._option(33988, 33743, 33898)
			if choice == Wizard.ChoiceLeft: return self._cancel()
		user = userOriginal = tools.Settings.getString('accounts.debrid.easynews.user')
		password = passwordOriginal = tools.Settings.getString('accounts.debrid.easynews.pass')
		while True:
			choice = self._option(33950, 33743, 33994)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			user = self._input(default = user)
			choice = self._option(33951, 33743, 33995)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			password = self._input(default = password)
			interface.Loader.show()
			tools.Settings.set('accounts.debrid.easynews.enabled', True)
			tools.Settings.set('accounts.debrid.easynews.user', user)
			tools.Settings.set('accounts.debrid.easynews.pass', password)
			valid = debrid.EasyNews().accountVerify()
			interface.Loader.hide()
			if valid:
				tools.Settings.set('providers.universal.premium.member.easynews', True)
				choice = self._option(33953, 33743, 33821)
				if choice == Wizard.ChoiceLeft: return self._cancel()
				return Wizard.OptionContinue
			else:
				tools.Settings.set('accounts.debrid.easynews.enabled', False)
				tools.Settings.set('accounts.debrid.easynews.user', userOriginal)
				tools.Settings.set('accounts.debrid.easynews.pass', passwordOriginal)
				choice = self._option(33991, 33743, 33902)
				if choice == Wizard.ChoiceLeft: return self._cancel()
		return Wizard.OptionContinue

	@classmethod
	def _showAllDebrid(self):
		choice = self._option(35268, 33897, 33898)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
		choice = self._option(35269, 33899, 33900)
		if choice == Wizard.ChoiceLeft:
			tools.System.openLink(tools.Settings.getString('link.alldebrid', raw = True))
			choice = self._option(35273, 33743, 33898)
			if choice == Wizard.ChoiceLeft: return self._cancel()
		user = userOriginal = tools.Settings.getString('accounts.debrid.alldebrid.user')
		password = passwordOriginal = tools.Settings.getString('accounts.debrid.alldebrid.pass')
		while True:
			choice = self._option(35270, 33743, 33994)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			user = self._input(default = user)
			choice = self._option(35271, 33743, 33995)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			password = self._input(default = password)
			interface.Loader.show()
			tools.Settings.set('accounts.debrid.alldebrid.enabled', True)
			tools.Settings.set('accounts.debrid.alldebrid.user', user)
			tools.Settings.set('accounts.debrid.alldebrid.pass', password)
			valid = debrid.AllDebrid().accountValid()
			interface.Loader.hide()
			if valid:
				choice = self._option(35272, 33743, 33821)
				if choice == Wizard.ChoiceLeft: return self._cancel()
				return Wizard.OptionContinue
			else:
				tools.Settings.set('accounts.debrid.alldebrid.enabled', False)
				tools.Settings.set('accounts.debrid.alldebrid.user', userOriginal)
				tools.Settings.set('accounts.debrid.alldebrid.pass', passwordOriginal)
				choice = self._option(35274, 33743, 33902)
				if choice == Wizard.ChoiceLeft: return self._cancel()
		return Wizard.OptionContinue

	@classmethod
	def _showRapidPremium(self):
		choice = self._option(35275, 33897, 33898)
		if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
		choice = self._option(35276, 33899, 33900)
		if choice == Wizard.ChoiceLeft:
			tools.System.openLink(tools.Settings.getString('link.rapidpremium', raw = True))
			choice = self._option(35280, 33743, 33898)
			if choice == Wizard.ChoiceLeft: return self._cancel()
		user = userOriginal = tools.Settings.getString('accounts.debrid.rapidpremium.user')
		api = apiOriginal = tools.Settings.getString('accounts.debrid.rapidpremium.api')
		while True:
			choice = self._option(35277, 33743, 33994)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			user = self._input(default = user)
			choice = self._option(35278, 33743, 33901)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			api = self._input(default = api)
			interface.Loader.show()
			tools.Settings.set('accounts.debrid.rapidpremium.enabled', True)
			tools.Settings.set('accounts.debrid.rapidpremium.user', user)
			tools.Settings.set('accounts.debrid.rapidpremium.api', api)
			valid = debrid.RapidPremium().accountValid()
			interface.Loader.hide()
			if valid:
				choice = self._option(35279, 33743, 33821)
				if choice == Wizard.ChoiceLeft: return self._cancel()
				return Wizard.OptionContinue
			else:
				tools.Settings.set('accounts.debrid.rapidpremium.enabled', False)
				tools.Settings.set('accounts.debrid.rapidpremium.user', userOriginal)
				tools.Settings.set('accounts.debrid.rapidpremium.api', apiOriginal)
				choice = self._option(35281, 33743, 33902)
				if choice == Wizard.ChoiceLeft: return self._cancel()
		return Wizard.OptionContinue

	@classmethod
	def _showProviders(self, first = True):
		if first:
			choice = self._option(33908, 33743, 33821)
			if choice == Wizard.ChoiceLeft: return self._cancel()

		orion = orionoid.Orionoid()
		enabled = interface.Format.fontColor(interface.Translation.string(32301), interface.Format.ColorExcellent)
		disabled = interface.Format.fontColor(interface.Translation.string(32302), interface.Format.ColorBad)
		special = '[' + interface.Translation.string(33105) + '] '
		general = '[' + interface.Translation.string(32310) + '] '
		torrent = '[' + interface.Translation.string(33199) + '] '
		usenet = '[' + interface.Translation.string(33200) + '] '
		hoster = '[' + interface.Translation.string(33198) + '] '
		external = '[' + interface.Translation.string(35354) + '] '

		choices = [None]
		items = [interface.Format.fontBold(interface.Translation.string(33821))]

		if orion.accountValid():
			choices.append('specialorion')
			items.append(interface.Format.fontBold(special + interface.Translation.string(35414) + ': ' + (enabled if orion.accountEnabled() else disabled)))

		choices.append('generallocal')
		items.append(interface.Format.fontBold(general + interface.Translation.string(35356) + ': ' + (enabled if tools.Settings.getBoolean('providers.general.local.open.enabled') or tools.Settings.getBoolean('providers.general.local.member.enabled') else disabled)))

		if tools.Settings.getBoolean('accounts.debrid.premiumize.enabled') or tools.Settings.getBoolean('accounts.debrid.offcloud.enabled') or tools.Settings.getBoolean('accounts.debrid.realdebrid.enabled') or tools.Settings.getBoolean('accounts.debrid.easynews.enabled'):
			choices.append('generalpremium')
			items.append(interface.Format.fontBold(general + interface.Translation.string(35357) + ': ' + (enabled if tools.Settings.getBoolean('providers.general.premium.open.enabled') or tools.Settings.getBoolean('providers.general.premium.member.enabled') else disabled)))

		if handler.Handler(handler.Handler.TypeTorrent).serviceHas():
			choices.append('torrentuniversal')
			items.append(interface.Format.fontBold(torrent + interface.Translation.string(35355) + ': ' + (enabled if tools.Settings.getBoolean('providers.torrent.universal.open.enabled') or tools.Settings.getBoolean('providers.torrent.universal.distributed.enabled') or tools.Settings.getBoolean('providers.torrent.universal.member.enabled') else disabled)))
			choices.append('torrentfrench')
			items.append(interface.Format.fontBold(torrent + interface.Translation.string(35033) + ': ' + (enabled if tools.Settings.getBoolean('providers.torrent.french.open.enabled') or tools.Settings.getBoolean('providers.torrent.french.member.enabled') else disabled)))
			choices.append('torrentrussian')
			items.append(interface.Format.fontBold(torrent + interface.Translation.string(35353) + ': ' + (enabled if tools.Settings.getBoolean('providers.torrent.russian.open.enabled') or tools.Settings.getBoolean('providers.torrent.russian.member.enabled') else disabled)))
			choices.append('torrentitalian')
			items.append(interface.Format.fontBold(torrent + interface.Translation.string(35389) + ': ' + (enabled if tools.Settings.getBoolean('providers.torrent.italian.open.enabled') or tools.Settings.getBoolean('providers.torrent.italian.member.enabled') else disabled)))

		if handler.Handler(handler.Handler.TypeUsenet).serviceHas():
			choices.append('usenetuniversal')
			items.append(interface.Format.fontBold(usenet + interface.Translation.string(35355) + ': ' + (enabled if tools.Settings.getBoolean('providers.usenet.universal.open.enabled') or tools.Settings.getBoolean('providers.usenet.universal.member.enabled') else disabled)))

		if handler.Handler(handler.Handler.TypeHoster).serviceHas():
			choices.append('hosteruniversal')
			items.append(interface.Format.fontBold(hoster + interface.Translation.string(35355) + ': ' + (enabled if tools.Settings.getBoolean('providers.hoster.universal.open.enabled') or tools.Settings.getBoolean('providers.hoster.universal.member.enabled') else disabled)))

		choices.append('externalopescrapers')
		items.append(interface.Format.fontBold(external + interface.Translation.string(35550) + ': ' + (enabled if tools.Settings.getBoolean('providers.external.universal.open.opescrapersx') else disabled)))
		choices.append('externallamscrapers')
		items.append(interface.Format.fontBold(external + interface.Translation.string(35530) + ': ' + (enabled if tools.Settings.getBoolean('providers.external.universal.open.lamscrapersx') else disabled)))
		choices.append('externalcivscrapers')
		items.append(interface.Format.fontBold(external + interface.Translation.string(35531) + ': ' + (enabled if tools.Settings.getBoolean('providers.external.universal.open.civscrapersx') else disabled)))
		choices.append('externalgloscrapers')
		items.append(interface.Format.fontBold(external + interface.Translation.string(35532) + ': ' + (enabled if tools.Settings.getBoolean('providers.external.universal.open.gloscrapersx') else disabled)))
		choices.append('externaluniscrapers')
		items.append(interface.Format.fontBold(external + interface.Translation.string(35349) + ': ' + (enabled if tools.Settings.getBoolean('providers.external.universal.open.uniscrapersx') else disabled)))
		choices.append('externalnanscrapers')
		items.append(interface.Format.fontBold(external + interface.Translation.string(35350) + ': ' + (enabled if tools.Settings.getBoolean('providers.external.universal.open.nanscrapersx') else disabled)))
		choices.append('externalincscrapers')
		items.append(interface.Format.fontBold(external + interface.Translation.string(35352) + ': ' + (enabled if tools.Settings.getBoolean('providers.external.universal.open.incscrapersx') else disabled)))
		choices.append('externalplascrapers')
		items.append(interface.Format.fontBold(external + interface.Translation.string(35351) + ': ' + (enabled if tools.Settings.getBoolean('providers.external.universal.open.plascrapersx') else disabled)))
		choices.append('externalyodscrapers')
		items.append(interface.Format.fontBold(external + interface.Translation.string(35533) + ': ' + (enabled if tools.Settings.getBoolean('providers.external.universal.open.yodscrapersx') else disabled)))

		choice = interface.Dialog.options(title = 33014, items = items)
		if choice < 0: return self._cancel()
		choice = choices[choice]

		# Takes about 3 secs. By default they are all set to true, so this can be skipped.
		'''tools.Settings.set('streaming.torrent.enabled', True)
		tools.Settings.set('streaming.torrent.premiumize.enabled', True)
		tools.Settings.set('streaming.torrent.offcloud.enabled', True)
		tools.Settings.set('streaming.torrent.realdebrid.enabled', True)
		tools.Settings.set('streaming.usenet.enabled', True)
		tools.Settings.set('streaming.usenet.premiumize.enabled', True)
		tools.Settings.set('streaming.usenet.offcloud.enabled', True)
		tools.Settings.set('streaming.hoster.enabled', True)
		tools.Settings.set('streaming.hoster.premiumize.enabled', True)
		tools.Settings.set('streaming.hoster.offcloud.enabled', True)
		tools.Settings.set('streaming.hoster.realdebrid.enabled', True)
		tools.Settings.set('streaming.hoster.alldebrid.enabled', True)
		tools.Settings.set('streaming.hoster.rapidpremium.enabled', True)
		tools.Settings.set('streaming.hoster.resolveurl.enabled', True)
		tools.Settings.set('streaming.hoster.urlresolver.enabled', True)'''

		defaultTorrent = 0
		defaultUsenet = 0
		defaultHoster = 0
		handlerPremium = tools.Settings.getBoolean('accounts.debrid.premiumize.enabled')
		handlerOffcloud = tools.Settings.getBoolean('accounts.debrid.offcloud.enabled')
		handlerRealdebrid = tools.Settings.getBoolean('accounts.debrid.realdebrid.enabled')
		handlers = int(handlerPremium) + int(handlerOffcloud) + int(handlerRealdebrid)
		if handlers == 1:
			defaultTorrent = 1 if handlerPremium else 2 if handlerOffcloud else 3
			defaultUsenet = 1 if handlerPremium else 2 if handlerOffcloud else 0
			defaultHoster = 1 if handlerPremium else 2 if handlerOffcloud else 3
		tools.Settings.set('streaming.torrent.default', defaultTorrent)
		tools.Settings.set('streaming.usenet.default', defaultUsenet)
		tools.Settings.set('streaming.hoster.default', defaultHoster)

		if choice == None:
			interface.Loader.show()
			count = len(provider.Provider.providers())
			interface.Loader.hide()
			if count > 200:
				if self._option(interface.Translation.string(33909) % count, 35045, 35044) == Wizard.ChoiceLeft:
					return self._showProviders(first = False)
			return Wizard.OptionContinue
		elif choice == 'specialorion':
			active = self._option(35415, 33737, 33192) == Wizard.ChoiceRight
			orion.accountEnable(active)
		elif choice == 'generallocal':
			active = self._option(33958, 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.general.local.open.enabled', active)
			tools.Settings.set('providers.general.local.member.enabled', active)
		elif choice == 'generalpremium':
			active = self._option(33906, 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.general.premium.open.enabled', active)
			tools.Settings.set('providers.general.premium.member.enabled', active)
		elif choice == 'torrentuniversal':
			active = self._option(interface.Translation.string(33956) % interface.Translation.string(35358), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.torrent.universal.open.enabled', active)
			tools.Settings.set('providers.torrent.universal.distributed.enabled', active)
			tools.Settings.set('providers.torrent.universal.member.enabled', active)
		elif choice == 'torrentfrench':
			active = self._option(interface.Translation.string(33956) % interface.Translation.string(33790), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.torrent.french.open.enabled', active)
			tools.Settings.set('providers.torrent.french.member.enabled', active)
		elif choice == 'torrentrussian':
			active = self._option(interface.Translation.string(33956) % interface.Translation.string(33992), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.torrent.russian.open.enabled', active)
			tools.Settings.set('providers.torrent.russian.member.enabled', active)
		elif choice == 'torrentitalian':
			active = self._option(interface.Translation.string(33956) % interface.Translation.string(35388), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.torrent.italian.open.enabled', active)
			tools.Settings.set('providers.torrent.italian.member.enabled', active)
		elif choice == 'usenetuniversal':
			active = self._option(interface.Translation.string(33957) % interface.Translation.string(35358), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.usenet.universal.open.enabled', active)
			tools.Settings.set('providers.usenet.universal.member.enabled', active)
		elif choice == 'hosteruniversal':
			active = self._option(interface.Translation.string(33905) % interface.Translation.string(35358), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.hoster.universal.open.enabled', active)
			tools.Settings.set('providers.hoster.universal.member.enabled', active)
		elif choice == 'externalopescrapers':
			active = self._option(interface.Translation.string(33907) % interface.Translation.string(35548), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.external.universal.open.opescrapersx', active)
		elif choice == 'externallamscrapers':
			active = self._option(interface.Translation.string(33907) % interface.Translation.string(35431), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.external.universal.open.lamscrapersx', active)
		elif choice == 'externalcivscrapers':
			active = self._option(interface.Translation.string(33907) % interface.Translation.string(35504), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.external.universal.open.civscrapersx', active)
		elif choice == 'externalgloscrapers':
			active = self._option(interface.Translation.string(33907) % interface.Translation.string(35534), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.external.universal.open.gloscrapersx', active)
		elif choice == 'externaluniscrapers':
			active = self._option(interface.Translation.string(33907) % interface.Translation.string(35359), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.external.universal.open.uniscrapersx', active)
		elif choice == 'externalnanscrapers':
			active = self._option(interface.Translation.string(33907) % interface.Translation.string(35360), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.external.universal.open.nanscrapersx', active)
		elif choice == 'externalincscrapers':
			active = self._option(interface.Translation.string(33907) % interface.Translation.string(35362), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.external.universal.open.incscrapersx', active)
		elif choice == 'externalplascrapers':
			active = self._option(interface.Translation.string(33907) % interface.Translation.string(35361), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.external.universal.open.plascrapersx', active)
		elif choice == 'externalyodscrapers':
			active = self._option(interface.Translation.string(33907) % interface.Translation.string(35535), 33737, 33192) == Wizard.ChoiceRight
			tools.Settings.set('providers.external.universal.open.yodscrapersx', active)

		return self._showProviders(first = False)

	@classmethod
	def _showAutomation(self):
		if self.mMode == Wizard.ModeReaper or self.mMode == Wizard.ModeQuick or self.mMode == Wizard.ModeExtensive:
			choice = self._option(35322, 33800, 33110)
			enable = choice == Wizard.ChoiceLeft
			tools.Settings.set('automatic.enabled', enable)
		return Wizard.OptionContinue

	@classmethod
	def _showScraping(self):
		if self.mMode == Wizard.ModeExtensive:
			choice = self._option(33965, 33923, 33924)
			enable = choice == Wizard.ChoiceRight
			tools.Settings.set('scraping.failure.enabled', enable)

			choice = self._option(33966, 33743, 33821)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			choice = self._option(33967, 33564, 33800)
			if choice == Wizard.ChoiceRight:
				provider.Provider().optimization(title = 33895, introduction = False)
		return Wizard.OptionContinue

	@classmethod
	def _showVpn(self):
		if self.mMode == Wizard.ModeExtensive:
			choice = self._option(33969, 33743, 33821)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			choice = self._option(33970, 33743, 33821)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			choice = self._option(33971, 33897, 33927)
			if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
			vpn.Vpn().configuration(settings = False, title = 33895, finish = 33821, introduction = False)
		return Wizard.OptionContinue

	@classmethod
	def _showSpeedTest(self):
		if self.mMode == Wizard.ModeExtensive:
			choice = self._option(33972, 33743, 33821)
			if choice == Wizard.ChoiceLeft: return self._cancel()
			choice = self._option(33973, 33897, 33928)
			if choice == Wizard.ChoiceLeft: return Wizard.OptionCancelStep
			speedtest.SpeedTesterGlobal().show()
		return Wizard.OptionContinue

	@classmethod
	def show(self, launch = False):
		if self._showWelcome(launch = launch) == Wizard.OptionCancelWizard:
			return False

		Adaption.show()
		if self._showMode() == Wizard.OptionCancelWizard:
			return False

		if self.mMode == Wizard.ModeQuick or self.mMode == Wizard.ModeExtensive:
			if self._showLanguage() == Wizard.OptionCancelWizard:
				return False

		if self._showAccounts() == Wizard.OptionCancelWizard:
			return False
		if self._showProviders() == Wizard.OptionCancelWizard:
			return False

		if self._showAutomation() == Wizard.OptionCancelWizard:
			return False

		if self.mMode == Wizard.ModeExtensive:
			if self._showScraping() == Wizard.OptionCancelWizard:
				return False
			if self._showVpn() == Wizard.OptionCancelWizard:
				return False
			if self._showSpeedTest() == Wizard.OptionCancelWizard:
				return False

		# Backup the new settings.
		tools.Backup.automaticExport(force = True)

		self._showFinish()

	@classmethod
	def launchInitial(self):
		if tools.Settings.getBoolean('internal.wizard.initialized'):
			return False
		else:
			self.show(launch = True)
			tools.Settings.set('internal.wizard.initialized', True)
			return True
