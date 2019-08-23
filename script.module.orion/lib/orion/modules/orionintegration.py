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
# ORIONINTEGRATION
##############################################################################
# Class for integrating Orion into other addons.
##############################################################################

from orion.modules.oriontools import *
from orion.modules.orionsettings import *
from orion.modules.orioninterface import *

class OrionIntegration:

	ExtensionBackup = '.orion'
	PathLength = 50

	AddonGaia = 'Gaia'
	AddonSeren = 'Seren'
	AddonIncursion = 'Incursion'
	AddonPlacenta = 'Placenta'
	AddonCovenant = 'Covenant'
	AddonMagicality = 'Magicality'
	AddonTheOath = 'TheOath'
	AddonYoda = 'Yoda'
	AddonBodie = 'Bodie'
	AddonNymeria = 'Nymeria'
	AddonVenom = 'Venom'
	AddonScrubs = 'Scrubs'
	AddonMedusa = 'Medusa'
	AddonMercury = 'Mercury'
	AddonDeceit = 'Deceit'
	AddonFen = 'Fen'
	AddonGenesis = 'Genesis'
	AddonExodus = 'Exodus'
	AddonExodusRedux = 'Exodus Redux'
	AddonNeptuneRising = 'Neptune Rising'
	AddonDeathStreams = 'Death Streams'
	AddonBoomMovies = 'Boom Movies'
	AddonOpenScrapers = 'Open Scrapers'
	AddonLambdaScrapers = 'Lambda Scrapers'
	AddonUniversalScrapers = 'Universal Scrapers'
	AddonNanScrapers = 'NaN Scrapers'
	AddonElementum = 'Elementum'
	AddonQuasar = 'Quasar'
	Addons = [AddonGaia, AddonSeren, AddonIncursion, AddonPlacenta, AddonCovenant, AddonMagicality, AddonTheOath, AddonYoda, AddonBodie, AddonNymeria, AddonVenom, AddonScrubs, AddonMedusa, AddonMercury, AddonDeceit, AddonFen, AddonGenesis, AddonExodus, AddonExodusRedux, AddonNeptuneRising, AddonDeathStreams, AddonBoomMovies, AddonOpenScrapers, AddonLambdaScrapers, AddonUniversalScrapers, AddonNanScrapers, AddonElementum, AddonQuasar]
	AddonsNative = [AddonGaia, AddonTheOath]

	LanguageXml = 'xml'
	LanguagePython = 'python'

	CommentXmlStart = '<!-- [ORION/] -->'
	CommentXmlEnd = '<!-- [/ORION] -->'
	CommentPythonStart = '# [ORION/]'
	CommentPythonEnd = '# [/ORION]'

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def id(self, addon, check = False):
		if addon == None: return addon
		addon = addon.lower().replace(' ', '')
		if check:
			addons = [i.lower().replace(' ', '') for i in OrionIntegration.Addons]
			if not addon in addons: return None
		return addon

	@classmethod
	def _comment(self, data, language = LanguagePython, indentation = ''):
		commentStart = ''
		commentEnd = ''
		if language == OrionIntegration.LanguageXml:
			commentStart = OrionIntegration.CommentXmlStart
			commentEnd = OrionIntegration.CommentXmlEnd
		elif language == OrionIntegration.LanguagePython:
			commentStart = OrionIntegration.CommentPythonStart
			commentEnd = OrionIntegration.CommentPythonEnd
		data = data.replace('\n', '\n' + indentation)
		return '\n\n' + indentation + commentStart + '\n' + indentation + data + '\n' + indentation + commentEnd + '\n'

	@classmethod
	def _expression(self, language = LanguagePython, full = True):
		commentStart = ''
		commentEnd = ''
		if language == OrionIntegration.LanguageXml:
			commentStart = OrionIntegration.CommentXmlStart
			commentEnd = OrionIntegration.CommentXmlEnd
		elif language == OrionIntegration.LanguagePython:
			commentStart = OrionIntegration.CommentPythonStart
			commentEnd = OrionIntegration.CommentPythonEnd
		if full: return '\n[\t ]*' + ((commentStart + '.*' + commentEnd).replace('\n', '').replace('[', '\[').replace(']', '\]').replace('/', '\/')) + '[\t ]*\n'
		else: return commentStart.replace('\n', '').replace('[', '\[').replace(']', '\]').replace('/', '\/')

	def _path(self, file):
		return OrionTools.pathJoin(OrionTools.addonPath(), 'lib', 'orion', 'integration', self.id, file)

	def _content(self, file):
		return OrionTools.fileRead(self._path(file)).strip()

	##############################################################################
	# BACKUP
	##############################################################################

	def _backupContains(self, path):
		return OrionTools.fileContains(path, self._expression(OrionIntegration.LanguageXml, False)) or OrionTools.fileContains(path, self._expression(OrionIntegration.LanguagePython, False))

	def _backupCreate(self):
		for i in self.files:
			if not self._backupContains(i):
				OrionTools.fileCopy(i, i + OrionIntegration.ExtensionBackup, overwrite = True)

	def _backupRestore(self):
		for i in self.files:
			j = i + OrionIntegration.ExtensionBackup
			if OrionTools.fileExists(j):
				OrionTools.fileMove(j, i, overwrite = True)

	##############################################################################
	# INIRIALIZE
	##############################################################################

	@classmethod
	def initialize(self, addon):
		integration = OrionIntegration()
		try:
			if addon == OrionIntegration.AddonGaia: integration._gaiaInitialize()
			elif addon == OrionIntegration.AddonSeren: integration._serenInitialize()
			elif addon == OrionIntegration.AddonIncursion: integration._incursionInitialize()
			elif addon == OrionIntegration.AddonPlacenta: integration._placentaInitialize()
			elif addon == OrionIntegration.AddonCovenant: integration._covenantInitialize()
			elif addon == OrionIntegration.AddonMagicality: integration._magicalityInitialize()
			elif addon == OrionIntegration.AddonTheOath: integration._theOathInitialize()
			elif addon == OrionIntegration.AddonYoda: integration._yodaInitialize()
			elif addon == OrionIntegration.AddonDeathStreams: integration._deathStreamsInitialize()
			elif addon == OrionIntegration.AddonBoomMovies: integration._boomMoviesInitialize()
			elif addon == OrionIntegration.AddonScrubs: integration._scrubsInitialize()
			elif addon == OrionIntegration.AddonFen: integration._fenInitialize()
			elif addon == OrionIntegration.AddonGenesis: integration._genesisInitialize()
			elif addon == OrionIntegration.AddonExodus: integration._exodusInitialize()
			elif addon == OrionIntegration.AddonOpenScrapers: integration._openScrapersInitialize()
			elif addon == OrionIntegration.AddonLambdaScrapers: integration._lambdaScrapersInitialize()
			elif addon == OrionIntegration.AddonUniversalScrapers: integration._universalScrapersInitialize()
			elif addon == OrionIntegration.AddonNanScrapers: integration._nanScrapersInitialize()
			elif addon == OrionIntegration.AddonElementum: integration._elementumInitialize()
			elif addon == OrionIntegration.AddonQuasar: integration._quasarInitialize()
		except: pass
		return integration

	##############################################################################
	# CHECK
	##############################################################################

	@classmethod
	def check(self):
		for addon in OrionIntegration.Addons:
			try:
				integration = self.initialize(addon)
				setting = OrionSettings.getIntegration(integration.id)
				if (not setting == '' or addon in OrionIntegration.AddonsNative) and not setting == integration.version:
					integration._integrate(addon)
					OrionSettings.setIntegration(integration.id, integration.version)
			except:
				pass

	##############################################################################
	# CLEAN
	##############################################################################

	def _clean(self, language = None):
		if language == None:
			self._clean(language = OrionIntegration.LanguageXml)
			self._clean(language = OrionIntegration.LanguagePython)
		else:
			expression = self._expression(language, True)
			for i in self.files:
				OrionTools.fileClean(i, expression)
			if not self.deletes == None:
				for i in self.deletes:
					if OrionTools.fileExists(i):
						OrionTools.fileDelete(i)
					elif OrionTools.directoryExists(i):
						OrionTools.directoryDelete(i)

	@classmethod
	def clean(self, addon):
		integration = self.initialize(addon)
		if OrionTools.addonEnabled(integration.idPlugin):
			if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33021) % addon):
				integration._clean()
				integration._backupRestore()
				integration._deintegrate(addon)
				OrionInterface.dialogNotification(title = 32177, message = 33019, icon = OrionInterface.IconSuccess)
				return True
		else:
			OrionInterface.dialogNotification(title = 32175, message = 33027, icon = OrionInterface.IconError)
		return False

	##############################################################################
	# INTEGRATE
	##############################################################################

	@classmethod
	def integrate(self, addon):
		integration = self.initialize(addon)
		if OrionTools.addonEnabled(integration.idPlugin):
			if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33020) % (addon, addon)):
				if integration._integrate(addon):
					try: reintegrate = integration.reintegrate
					except: reintegrate = True
					try: restart = integration.restart
					except: restart = True
					if reintegrate and OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33022) % (addon, addon)):
						OrionSettings.setIntegration(integration.id, integration.version)
					else:
						OrionSettings.setIntegration(integration.id, '')
					if restart:
						OrionInterface.dialogConfirm(title = 32174, message = (OrionTools.translate(33025) % addon) + OrionInterface.fontNewline() + OrionInterface.font(33026, bold = True, color = OrionInterface.ColorPrimary))
		else:
			OrionInterface.dialogNotification(title = 32175, message = 33027, icon = OrionInterface.IconError)
		return False

	def _integrate(self, addon):
		self._backupCreate()
		self._clean()
		result = False
		if addon == OrionIntegration.AddonGaia: result = True
		elif addon == OrionIntegration.AddonSeren: result = self._serenIntegrate()
		elif addon == OrionIntegration.AddonIncursion: result = self._incursionIntegrate()
		elif addon == OrionIntegration.AddonPlacenta: result = self._placentaIntegrate()
		elif addon == OrionIntegration.AddonCovenant: result = self._covenantIntegrate()
		elif addon == OrionIntegration.AddonMagicality: result = self._magicalityIntegrate()
		elif addon == OrionIntegration.AddonTheOath: result = True
		elif addon == OrionIntegration.AddonYoda: result = self._yodaIntegrate()
		elif addon == OrionIntegration.AddonDeathStreams: result = self._deathStreamsIntegrate()
		elif addon == OrionIntegration.AddonBoomMovies: result = self._boomMoviesIntegrate()
		elif addon == OrionIntegration.AddonScrubs: result = self._scrubsIntegrate()
		elif addon == OrionIntegration.AddonFen: result = self._fenIntegrate()
		elif addon == OrionIntegration.AddonGenesis: result = self._genesisIntegrate()
		elif addon == OrionIntegration.AddonExodus: result = self._exodusIntegrate()
		elif addon == OrionIntegration.AddonOpenScrapers: result = self._openScrapersIntegrate()
		elif addon == OrionIntegration.AddonLambdaScrapers: result = self._lambdaScrapersIntegrate()
		elif addon == OrionIntegration.AddonUniversalScrapers: result = self._universalScrapersIntegrate()
		elif addon == OrionIntegration.AddonNanScrapers: result = self._nanScrapersIntegrate()
		elif addon == OrionIntegration.AddonElementum: result = self._elementumIntegrate()
		elif addon == OrionIntegration.AddonQuasar: result = self._quasarIntegrate()
		return result

	def _integrateSuccess(self):
		OrionInterface.dialogNotification(title = 32176, message = 33018, icon = OrionInterface.IconSuccess)
		return True

	def _integrateFailure(self, message = None, path = None):
		self._clean()
		self._backupRestore()
		original = path
		if path == None: path = ''
		else: path = OrionInterface.fontNewline().join([path[i - OrionIntegration.PathLength : i] for i in range(OrionIntegration.PathLength, len(path) + OrionIntegration.PathLength, OrionIntegration.PathLength)])
		OrionInterface.dialogNotification(title = 32175, message = 33017, icon = OrionInterface.IconError)
		OrionInterface.dialogConfirm(title = 32174, message = OrionInterface.fontBold(32175) + OrionInterface.fontNewline() + message + OrionInterface.fontNewline() + path)
		OrionTools.log('INTEGRATION FAILURE: ' + message + ' (' + original + ')')
		return False

	##############################################################################
	# DEINTEGRATE
	##############################################################################

	def _deintegrate(self, addon):
		result = False
		if addon == OrionIntegration.AddonSeren: result = self._serenDeintegrate()
		return result

	##############################################################################
	# LAUNCH
	##############################################################################

	@classmethod
	def launch(self, addon):
		integration = self.initialize(addon)
		if OrionTools.addonEnabled(integration.idPlugin):
			OrionTools.addonLaunch(integration.idPlugin)
			return True
		else:
			OrionInterface.dialogNotification(title = 32175, message = 33027, icon = OrionInterface.IconError)
			return False

	##############################################################################
	# EXECUTE
	##############################################################################

	@classmethod
	def execute(self, addon, integration = True):
		items = []
		if integration:
			items.append(OrionInterface.fontBold(32178) + ': ' + OrionTools.translate(32179))
			items.append(OrionInterface.fontBold(32006) + ': ' + OrionTools.translate(32180))
		items.append(OrionInterface.fontBold(32181) + ': ' + OrionTools.translate(32182))
		choice = OrionInterface.dialogOptions(title = 32174, items = items)
		if integration:
			if choice == 0: return self.integrate(addon)
			elif choice == 1: return self.clean(addon)
			elif choice == 2: return self.launch(addon)
		else:
			if choice == 0: return self.launch(addon)

	@classmethod
	def executeGaia(self):
		OrionInterface.dialogConfirm(title = 32174, message = OrionTools.translate(33024) % OrionIntegration.AddonGaia)
		return self.execute(OrionIntegration.AddonGaia, integration = False)

	@classmethod
	def executeSeren(self):
		return self.execute(OrionIntegration.AddonSeren)

	@classmethod
	def executeIncursion(self):
		return self.execute(OrionIntegration.AddonIncursion)

	@classmethod
	def executePlacenta(self):
		return self.execute(OrionIntegration.AddonPlacenta)

	@classmethod
	def executeCovenant(self):
		return self.execute(OrionIntegration.AddonCovenant)

	@classmethod
	def executeMagicality(self):
		return self.execute(OrionIntegration.AddonMagicality)

	@classmethod
	def executeTheOath(self):
		OrionInterface.dialogConfirm(title = 32174, message = OrionTools.translate(33024) % OrionIntegration.AddonTheOath)
		return self.execute(OrionIntegration.AddonTheOath, integration = False)

	@classmethod
	def executeYoda(self):
		return self.execute(OrionIntegration.AddonYoda)

	@classmethod
	def executeBodie(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (OrionIntegration.AddonBodie, OrionIntegration.AddonLambdaScrapers, OrionIntegration.AddonLambdaScrapers)):
			return self.executeLambdaScrapers()
		else:
			return False

	@classmethod
	def executeNymeria(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (OrionIntegration.AddonNymeria, OrionIntegration.AddonUniversalScrapers, OrionIntegration.AddonUniversalScrapers)):
			return self.executeUniversalScrapers()
		else:
			return False

	@classmethod
	def executeVenom(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (OrionIntegration.AddonVenom, OrionIntegration.AddonOpenScrapers, OrionIntegration.AddonUniversalScrapers)):
			return self.executeOpenScrapers()
		else:
			return False

	@classmethod
	def executeScrubs(self):
		return self.execute(OrionIntegration.AddonScrubs)

	@classmethod
	def executeMedusa(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (OrionIntegration.AddonMedusa, OrionIntegration.AddonUniversalScrapers, OrionIntegration.AddonUniversalScrapers)):
			return self.executeUniversalScrapers()
		else:
			return False

	@classmethod
	def executeMercury(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (OrionIntegration.AddonMercury, OrionIntegration.AddonUniversalScrapers, OrionIntegration.AddonUniversalScrapers)):
			return self.executeUniversalScrapers()
		else:
			return False

	@classmethod
	def executeDeceit(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (OrionIntegration.AddonDeceit, OrionIntegration.AddonUniversalScrapers, OrionIntegration.AddonUniversalScrapers)):
			return self.executeUniversalScrapers()
		else:
			return False

	@classmethod
	def executeFen(self):
		return self.execute(OrionIntegration.AddonFen)

	@classmethod
	def executeGenesis(self):
		return self.execute(OrionIntegration.AddonGenesis)

	@classmethod
	def executeExodus(self):
		return self.execute(OrionIntegration.AddonExodus)

	@classmethod
	def executeExodusRedux(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (OrionIntegration.AddonExodusRedux, OrionIntegration.AddonOpenScrapers, OrionIntegration.AddonOpenScrapers)):
			return self.executeOpenScrapers()
		else:
			return False

	@classmethod
	def executeNeptuneRising(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (OrionIntegration.AddonNeptuneRising, OrionIntegration.AddonUniversalScrapers, OrionIntegration.AddonUniversalScrapers)):
			return self.executeUniversalScrapers()
		else:
			return False

	@classmethod
	def executeDeathStreams(self):
		return self.execute(OrionIntegration.AddonDeathStreams)

	@classmethod
	def executeBoomMovies(self):
		return self.execute(OrionIntegration.AddonBoomMovies)

	@classmethod
	def executeOpenScrapers(self):
		return self.execute(OrionIntegration.AddonOpenScrapers)

	@classmethod
	def executeLambdaScrapers(self):
		return self.execute(OrionIntegration.AddonLambdaScrapers)

	@classmethod
	def executeUniversalScrapers(self):
		return self.execute(OrionIntegration.AddonUniversalScrapers)

	@classmethod
	def executeNanScrapers(self):
		return self.execute(OrionIntegration.AddonNanScrapers)

	@classmethod
	def executeElementum(self):
		return self.execute(OrionIntegration.AddonElementum)

	@classmethod
	def executeQuasar(self):
		return self.execute(OrionIntegration.AddonQuasar)

	##############################################################################
	# GAIA
	##############################################################################

	def _gaiaInitialize(self):
		self.name = OrionIntegration.AddonGaia
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.gaia'
		self.version = OrionTools.addonVersion(self.idPlugin)
		self.files = []
		self.deletes = []

	##############################################################################
	# SEREN
	##############################################################################

	def _serenInitialize(self):
		self.name = OrionIntegration.AddonSeren
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.seren'
		self.version = OrionTools.addonVersion(self.idPlugin)
		self.reintegrate = False
		self.restart = False
		self.link = OrionSettings.getString('internal.providers', raw = True)
		self.files = []
		self.deletes = []

	def _serenIntegrate(self):
		OrionTools.executePlugin(addon = self.idPlugin, action = 'externalProviderInstall', parameters = {'url' : self.link}, execute = True)
		return self._integrateSuccess()

	def _serenDeintegrate(self):
		OrionTools.executePlugin(addon = self.idPlugin, action = 'externalProviderUninstall', parameters = {'url' : 'Orion'}, execute = True)
		return True

	##############################################################################
	# INCURSION
	##############################################################################

	def _incursionInitialize(self):
		self.name = OrionIntegration.AddonIncursion
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.incursion'
		self.idModule = 'script.module.incursion'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _incursionIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Incursion settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]script\.module\.beautifulsoup4[\'"]\s*\/>', data):
			return self._integrateFailure('Incursion addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Incursion sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Incursion directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Incursion provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Incursion module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# PLACENTA
	##############################################################################

	def _placentaInitialize(self):
		self.name = OrionIntegration.AddonPlacenta
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.placenta'
		self.idModule = 'script.module.placenta'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _placentaIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Placenta settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]script\.module\.beautifulsoup4[\'"]\s*\/>', data):
			return self._integrateFailure('Placenta addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Placenta sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Placenta directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Placenta provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Placenta module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# COVENANT
	##############################################################################

	def _covenantInitialize(self):
		self.name = OrionIntegration.AddonCovenant
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.covenant'
		self.idModule = 'script.module.covenant'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _covenantIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Covenant settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
			return self._integrateFailure('Covenant addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Covenant sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Covenant directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Covenant provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Covenant module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# MAGICALITY
	##############################################################################

	def _magicalityInitialize(self):
		self.name = OrionIntegration.AddonMagicality
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.magicality'
		self.idModule = 'script.module.magicality'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _magicalityIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Magicality settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
			return self._integrateFailure('Magicality addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Magicality sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Magicality directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Magicality provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Magicality module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# THEOATH
	##############################################################################

	def _theOathInitialize(self):
		self.name = OrionIntegration.AddonTheOath
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.theoath'
		self.version = OrionTools.addonVersion(self.idPlugin)
		self.files = []
		self.deletes = []

	##############################################################################
	# YODA
	##############################################################################

	def _yodaInitialize(self):
		self.name = OrionIntegration.AddonYoda
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.yoda'
		self.idModule = 'script.module.yoda'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _yodaIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Yoda settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
			return self._integrateFailure('Yoda addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Yoda sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Yoda directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Yoda provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Yoda module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# DEATH STREAMS
	##############################################################################

	def _deathStreamsInitialize(self):
		self.name = OrionIntegration.AddonDeathStreams
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.blamo'
		self.version = OrionTools.addonVersion(self.idPlugin)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')
		self.pathOrionoid = OrionTools.pathJoin(self.pathPlugin, 'scrapers', 'orionoid.py')

		self.files = []
		self.files.append(self.pathAddon)

		self.deletes = []
		self.deletes.append(self.pathOrionoid)

	def _deathStreamsIntegrate(self):
		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]script\.module\.dateutil[\'"]\s*\/>', data):
			return self._integrateFailure('Death Streams addon metadata integration failure', self.pathAddon)

		# orionoid.py
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Death Streams provider integration failure', self.pathOrionoid)

		return self._integrateSuccess()

	##############################################################################
	# BOOMMOVIES
	##############################################################################

	def _boomMoviesInitialize(self):
		self.name = OrionIntegration.AddonBoomMovies
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.BoomMovies'
		self.idModule = 'script.module.BoomMovies'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _boomMoviesIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('BoomMovies settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
			return self._integrateFailure('BoomMovies addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('BoomMovies sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('BoomMovies directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('BoomMovies provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('BoomMovies module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# SCRUBS
	##############################################################################

	def _scrubsInitialize(self):
		self.name = OrionIntegration.AddonScrubs
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.scrubsv2'
		self.idModule = 'script.module.scrubsv2'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _scrubsIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*setting\s*label\s*=\s*"Enable\s*All.*toggleAllNormal.*>', data):
			return self._integrateFailure('Scrubs settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
			return self._integrateFailure('Scrubs addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Scrubs sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Scrubs directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Scrubs provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Scrubs module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# FEN
	##############################################################################

	def _fenInitialize(self):
		self.name = OrionIntegration.AddonFen
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.fen'
		self.idModule = 'script.module.tikiscrapers'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathModule, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'tikiscrapers', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'tikiscrapers', 'sources_tikiscrapers', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _fenIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*\/\s*category\s*>', data):
			return self._integrateFailure('Fen settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
			return self._integrateFailure('Fen addon metadata integration failure', self.pathAddon)

		# __init__.py
		data1 = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		data2 = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '            ')
		if not OrionTools.fileInsert(self.pathSources, ['\.load_module\(module_name\)', 'def\s*scraperNames.*if is_pkg:\s*continue'], [data1, data2], [None, re.S]):
			return self._integrateFailure('Fen sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Fen directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Fen provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Fen module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# GENISIS
	##############################################################################

	def _genesisInitialize(self):
		self.name = OrionIntegration.AddonGenesis
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.genesis'
		self.version = OrionTools.addonVersion(self.idPlugin)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathPlugin, 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathPlugin, 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _genesisIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s*label\s*=\s*"Hosts"\s*>.*?<\s*\/\s*category\s*>', data, re.S):
			return self._integrateFailure('Genesis settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
			return self._integrateFailure('Genesis addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Genesis sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Genesis directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Genesis provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Genesis module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# EXODUS
	##############################################################################

	def _exodusInitialize(self):
		self.name = OrionIntegration.AddonExodus
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.exodus'
		self.idModule = 'script.module.exoscrapers'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathModule, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathScrapers = OrionTools.pathJoin(self.pathModule, 'lib', 'exoscrapers', '__init__.py')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'exoscrapers', 'sources_exoscrapers', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'exoscrapers', 'sources_exoscrapers', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _exodusIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\/category>', data):
			return self._integrateFailure('Exodus settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
			return self._integrateFailure('Exodus addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('scrapers.py'), OrionIntegration.LanguagePython, '    ')
		if not OrionTools.fileInsert(self.pathScrapers, 'return sourceDict', data):
			return self._integrateFailure('Yoda scrapers integration failure', self.pathScrapers)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython)
		if not OrionTools.fileInsert(self.pathSources, 'all_providers\s*=\s*\[\]', data):
			return self._integrateFailure('Exodus sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Exodus directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Exodus provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Exodus module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# OPEN SCRAPERS
	##############################################################################

	def _openScrapersInitialize(self):
		self.name = OrionIntegration.AddonOpenScrapers
		self.id = self.id(self.name)
		self.idPlugin = 'script.module.openscrapers'
		self.version = OrionTools.addonVersion(self.idPlugin)
		self.versionNumber = int(self.version.replace('.', ''))

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')

		self.pathSources = OrionTools.pathJoin(self.pathPlugin, 'lib', 'openscrapers', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathPlugin, 'lib', 'openscrapers', 'sources_openscrapers', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)
		self.files.append(self.pathInit)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _openScrapersIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*/\s*category\s*>', data):
			return self._integrateFailure('Open Scrapers settings integration failure', self.pathSettings)

		# __init__.py
		data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Open Scrapers sources integration failure', self.pathSources)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
			return self._integrateFailure('Open Scrapers addon metadata integration failure', self.pathAddon)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Open Scrapers directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Open Scrapers provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Open Scrapers module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# LAMBDA SCRAPERS
	##############################################################################

	def _lambdaScrapersInitialize(self):
		self.name = OrionIntegration.AddonLambdaScrapers
		self.id = self.id(self.name)
		self.idPlugin = 'script.module.lambdascrapers'
		self.version = OrionTools.addonVersion(self.idPlugin)
		self.versionNumber = int(self.version.replace('.', ''))

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')

		if self.versionNumber < 150: # version < 1.5.3
			self.pathSources = OrionTools.pathJoin(self.pathPlugin, 'lib', 'lambdascrapers', 'sources_ALL', '__init__.py')
			self.pathOrion = OrionTools.pathJoin(self.pathPlugin, 'lib', 'lambdascrapers', 'sources_ALL', 'orion')
			self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
			self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

			self.files = []
			self.files.append(self.pathAddon)
			self.files.append(self.pathSources)
			self.files.append(self.pathInit)

			self.deletes = []
			self.deletes.append(self.pathOrion)
		else:
			self.pathSources = OrionTools.pathJoin(self.pathPlugin, 'lib', 'lambdascrapers', '__init__.py')
			self.pathOrion = OrionTools.pathJoin(self.pathPlugin, 'lib', 'lambdascrapers', 'sources_ lambdascrapers', 'orion')
			self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
			self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

			self.files = []
			self.files.append(self.pathSettings)
			self.files.append(self.pathAddon)
			self.files.append(self.pathSources)
			self.files.append(self.pathInit)

			self.deletes = []
			self.deletes.append(self.pathOrion)

	def _lambdaScrapersIntegrate(self):
		if self.versionNumber < 150: # version < 1.5.3
			# __init__.py
			data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
			if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
				return self._integrateFailure('Lambda Scrapers sources integration failure', self.pathSources)

			# addon.xml
			data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
			if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
				return self._integrateFailure('Lambda Scrapers addon metadata integration failure', self.pathAddon)

			# orionoid.py
			if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
				return self._integrateFailure('Lambda Scrapers directory creation error', self.pathOrion)
			if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
				return self._integrateFailure('Lambda Scrapers provider integration failure', self.pathOrionoid)
			if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
				return self._integrateFailure('Lambda Scrapers module integration failure', self.pathInit)

			return self._integrateSuccess()
		else:
			# settings.xml
			data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t')
			if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]Providers[\'"]\s*>', data):
				return self._integrateFailure('Lambda Scrapers settings integration failure', self.pathSettings)

			# __init__.py
			data = self._comment(self._content('sources.py'), OrionIntegration.LanguagePython, '                    ')
			if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
				return self._integrateFailure('Lambda Scrapers sources integration failure', self.pathSources)

			# addon.xml
			data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
			if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*?\/>', data):
				return self._integrateFailure('Lambda Scrapers addon metadata integration failure', self.pathAddon)

			# orionoid.py
			if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
				return self._integrateFailure('Lambda Scrapers directory creation error', self.pathOrion)
			if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
				return self._integrateFailure('Lambda Scrapers provider integration failure', self.pathOrionoid)
			if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
				return self._integrateFailure('Lambda Scrapers module integration failure', self.pathInit)

			return self._integrateSuccess()

	##############################################################################
	# UNIVERSAL SCRAPERS
	##############################################################################

	def _universalScrapersInitialize(self):
		self.name = OrionIntegration.AddonUniversalScrapers
		self.id = self.id(self.name)
		self.idPlugin = 'script.module.universalscrapers'
		self.version = OrionTools.addonVersion(self.idPlugin)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')
		self.pathOrionoid = OrionTools.pathJoin(self.pathPlugin, 'lib', 'universalscrapers', 'scraperplugins', 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathPlugin, 'lib', 'universalscrapers', '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathInit)

		self.deletes = []
		self.deletes.append(self.pathOrionoid)

	def _universalScrapersIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]Scrapers\s*1[\'"]\s*>', data):
			return self._integrateFailure('Universal Scrapers settings integration failure', self.pathSettings)

		# __init__.py
		data = self._comment(self._content('module.py'), OrionIntegration.LanguagePython, '    ')
		if not OrionTools.fileInsert(self.pathInit, 'relevant_scrapers\(\s*include_disabled\s*=\s*True\s*\),\s*key\s*=\s*lambda\s*x\s*:\s*x\.name\.lower\(\)\s*\)', data):
			return self._integrateFailure('Universal Scrapers module integration failure', self.pathInit)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]repository\.universalscrapers[\'"]\s*\/>', data):
			return self._integrateFailure('Universal Scrapers addon metadata integration failure', self.pathAddon)

		# orionoid.py
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Universal Scrapers provider integration failure', self.pathOrionoid)

		return self._integrateSuccess()

	##############################################################################
	# NAN SCRAPERS
	##############################################################################

	def _nanScrapersInitialize(self):
		self.name = OrionIntegration.AddonNanScrapers
		self.id = self.id(self.name)
		self.idPlugin = 'script.module.nanscrapers'
		self.version = OrionTools.addonVersion(self.idPlugin)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')
		self.pathOrionoid = OrionTools.pathJoin(self.pathPlugin, 'lib', 'nanscrapers', 'scraperplugins', 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathPlugin, 'lib', 'nanscrapers', '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathInit)

		self.deletes = []
		self.deletes.append(self.pathOrionoid)

	def _nanScrapersIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]Scrapers\s*1[\'"]\s*>', data):
			return self._integrateFailure('NaN Scrapers settings integration failure', self.pathSettings)

		# __init__.py
		data = self._comment(self._content('module.py'), OrionIntegration.LanguagePython, '    ')
		if not OrionTools.fileInsert(self.pathInit, 'relevant_scrapers\(\s*include_disabled\s*=\s*True\s*\),\s*key\s*=\s*lambda\s*x\s*:\s*x\.name\.lower\(\)\s*\)', data):
			return self._integrateFailure('NaN Scrapers module integration failure', self.pathInit)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]script\.module\.six[\'"]\s*\/>', data):
			return self._integrateFailure('NaN Scrapers addon metadata integration failure', self.pathAddon)

		# orionoid.py
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('NaN Scrapers provider integration failure', self.pathOrionoid)

		return self._integrateSuccess()

	##############################################################################
	# ELEMENTUM
	##############################################################################

	def _elementumInitialize(self):
		self.name = OrionIntegration.AddonElementum
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.elementum'
		self.idModule = 'script.elementum.burst'

		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)
		self.pathProfile = OrionTools.addonProfile(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathModule, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathBurst = OrionTools.pathJoin(self.pathModule, 'burst', 'burst.py')
		self.pathProvider = OrionTools.pathJoin(self.pathModule, 'burst', 'provider.py')
		self.pathOrionoid = OrionTools.pathJoin(self.pathModule, 'burst', 'providers', 'orionoid.py')
		self.pathIcon = OrionTools.pathJoin(self.pathModule, 'burst', 'providers', 'icons', 'orion.png')
		self.pathScraper = OrionTools.pathJoin(self.pathProfile, 'providers', 'orion.json')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathBurst)
		self.files.append(self.pathProvider)

		self.deletes = []
		self.deletes.append(self.pathOrionoid)
		self.deletes.append(self.pathIcon)
		self.deletes.append(self.pathScraper)

	def _elementumIntegrate(self):
		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]plugin\.video\.elementum[\'"].*\/>', data):
			return self._integrateFailure('Elementum addon metadata integration failure', self.pathAddon)

		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32128[\'"]\s*>', data):
			return self._integrateFailure('Elementum settings integration failure', self.pathSettings)

		# burst.py
		data = self._comment(self._content('burst.py'), OrionIntegration.LanguagePython, '    ')
		if not OrionTools.fileInsert(self.pathBurst, 'max_results\s*=\s*get_setting.*', data):
			return self._integrateFailure('Elementum burst integration failure', self.pathBurst)

		# provider.py
		data = self._comment(self._content('provider.py'), OrionIntegration.LanguagePython, '    ')
		if not OrionTools.fileInsert(self.pathProvider, 'token_auth\s*=\s*False.*', data):
			return self._integrateFailure('Elementum provider integration failure', self.pathProvider)

		# orionoid.py
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Elementum module integration failure', self.pathOrionoid)

		# orion.png
		if not OrionTools.fileCopy(self._path('orion.png'), self.pathIcon, overwrite = True):
			return self._integrateFailure('Elementum icon integration failure', self.pathIcon)

		# orion.json
		if not OrionTools.fileCopy(self._path('orion.json'), self.pathScraper, overwrite = True):
			return self._integrateFailure('Elementum scraper integration failure', self.pathScraper)

		return self._integrateSuccess()

	##############################################################################
	# QUASAR
	##############################################################################

	def _quasarInitialize(self):
		self.name = OrionIntegration.AddonQuasar
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.quasar'
		self.idModule = 'script.quasar.burst'

		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)
		self.pathProfile = OrionTools.addonProfile(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathModule, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathBurst = OrionTools.pathJoin(self.pathModule, 'burst', 'burst.py')
		self.pathProvider = OrionTools.pathJoin(self.pathModule, 'burst', 'provider.py')
		self.pathOrionoid = OrionTools.pathJoin(self.pathModule, 'burst', 'providers', 'orionoid.py')
		self.pathIcon = OrionTools.pathJoin(self.pathModule, 'burst', 'providers', 'icons', 'orion.png')
		self.pathScraper = OrionTools.pathJoin(self.pathProfile, 'providers', 'orion.json')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathBurst)
		self.files.append(self.pathProvider)

		self.deletes = []
		self.deletes.append(self.pathOrionoid)
		self.deletes.append(self.pathIcon)
		self.deletes.append(self.pathScraper)

	def _quasarIntegrate(self):
		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), OrionIntegration.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]plugin\.video\.quasar[\'"].*\/>', data):
			return self._integrateFailure('Quasar addon metadata integration failure', self.pathAddon)

		# settings.xml
		data = self._comment(self._content('settings.xml'), OrionIntegration.LanguageXml, '\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32012[\'"]\s*>', data):
			return self._integrateFailure('Quasar settings integration failure', self.pathSettings)

		# burst.py
		data = self._comment(self._content('burst.py'), OrionIntegration.LanguagePython, '    ')
		if not OrionTools.fileInsert(self.pathBurst, 'max_results\s*=\s*get_setting.*', data):
			return self._integrateFailure('Quasar burst integration failure', self.pathBurst)

		# provider.py
		data = self._comment(self._content('provider.py'), OrionIntegration.LanguagePython, '    ')
		if not OrionTools.fileInsert(self.pathProvider, 'token_auth\s*=\s*False.*', data):
			return self._integrateFailure('Quasar provider integration failure', self.pathProvider)

		# orionoid.py
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Quasar module integration failure', self.pathOrionoid)

		# orion.png
		if not OrionTools.fileCopy(self._path('orion.png'), self.pathIcon, overwrite = True):
			return self._integrateFailure('Quasar icon integration failure', self.pathIcon)

		# orion.json
		if not OrionTools.fileCopy(self._path('orion.json'), self.pathScraper, overwrite = True):
			return self._integrateFailure('Quasar scraper integration failure', self.pathScraper)

		return self._integrateSuccess()