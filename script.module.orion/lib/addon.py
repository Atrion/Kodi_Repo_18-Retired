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
# ORIONADDON
##############################################################################
# The main addon navigation and menu.
##############################################################################

from orion import *
from orion.modules.oriontools import *
from orion.modules.orionapi import *
from orion.modules.orionnavigator import *
from orion.modules.orionsettings import *
from orion.modules.orionintegration import *

orion = Orion(OrionApi._keyInternal())
parameters = OrionTools.addonParameters()
action = parameters.get('action')
type = parameters.get('type')
id = parameters.get('id')

##############################################################################
# MENU
##############################################################################

if action == None or action == 'menuMain':
    OrionNavigator.menuMain()

elif action == 'menuAccount':
    OrionNavigator.menuAccount()

elif action == 'menuApps':
    OrionNavigator.menuApps()

elif action == 'menuSupport':
    OrionNavigator.menuSupport()

elif action == 'menuTickets':
   OrionNavigator.menuTickets()

elif action == 'menuNotifications':
	OrionNavigator.menuNotifications()

elif action == 'menuTools':
    OrionNavigator.menuTools()

elif action == 'menuSettings':
    OrionNavigator.menuSettings()

elif action == 'menuIntegration':
    OrionNavigator.menuIntegration()

elif action == 'menuClean':
    OrionNavigator.menuClean()

elif action == 'menuAbout':
    OrionNavigator.menuAbout()

##############################################################################
# DIALOG
##############################################################################

elif action == 'dialogApp':
    OrionNavigator.dialogApp(id = id)

elif action == 'dialogUser':
    OrionNavigator.dialogUser()

elif action == 'dialogVoucher':
    OrionNavigator.dialogVoucher()

elif action == 'dialogTicket':
	OrionNavigator.dialogTicket(id = id, status = parameters.get('status'))

elif action == 'dialogServer':
    OrionNavigator.dialogServer()

elif action == 'dialogBackup':
    OrionNavigator.dialogBackup()

elif action == 'dialogNotification':
	OrionNavigator.dialogNotification(data = OrionTools.jsonFrom(parameters.get('data')))

elif action == 'dialogLink':
    OrionNavigator.dialogLink()

elif action == 'dialogPremium':
    OrionNavigator.dialogPremium()

elif action == 'dialogFree':
    OrionNavigator.dialogFree()

elif action == 'dialogSettings':
    OrionNavigator.dialogSettings(option = OrionTools.toBoolean(parameters.get('option')))

elif action == 'dialogLogin':
    OrionNavigator.dialogLogin()

##############################################################################
# SETTINGS
##############################################################################

elif action == 'settingsHelp':
    OrionSettings.help(type)

elif action == 'settingsAccountLogin':
    OrionNavigator.settingsAccountLogin()

elif action == 'settingsAccountRefresh':
    OrionNavigator.settingsAccountRefresh()

elif action == 'settingsFiltersUpdate':
	OrionSettings.setFiltersUpdate()

elif action == 'settingsFiltersStreamOrigin':
	OrionNavigator.settingsFiltersStreamOrigin(type)

elif action == 'settingsFiltersStreamSource':
	OrionNavigator.settingsFiltersStreamSource(type)

elif action == 'settingsFiltersStreamHoster':
	OrionNavigator.settingsFiltersStreamHoster(type)

elif action == 'settingsFiltersMetaRelease':
	OrionNavigator.settingsFiltersMetaRelease(type)

elif action == 'settingsFiltersMetaUploader':
	OrionNavigator.settingsFiltersMetaUploader(type)

elif action == 'settingsFiltersMetaEdition':
	OrionNavigator.settingsFiltersMetaEdition(type)

elif action == 'settingsFiltersVideoCodec':
	OrionNavigator.settingsFiltersVideoCodec(type)

elif action == 'settingsFiltersAudioType':
	OrionNavigator.settingsFiltersAudioType(type)

elif action == 'settingsFiltersAudioSystem':
	OrionNavigator.settingsFiltersAudioSystem(type)

elif action == 'settingsFiltersAudioCodec':
	OrionNavigator.settingsFiltersAudioCodec(type)

elif action == 'settingsFiltersAudioLanguages':
	OrionNavigator.settingsFiltersAudioLanguages(type)

elif action == 'settingsFiltersSubtitleType':
	OrionNavigator.settingsFiltersSubtitleType(type)

elif action == 'settingsFiltersSubtitleLanguages':
	OrionNavigator.settingsFiltersSubtitleLanguages(type)

##############################################################################
# PLAY
##############################################################################

elif action == 'play':
	from orion.modules.orionplayer import OrionPlayer
	OrionPlayer.play(data = parameters.get('data'))

##############################################################################
# INTEGRATION
##############################################################################

elif action == 'integrationGaia':
	OrionIntegration.executeGaia()

elif action == 'integrationSeren':
	OrionIntegration.executeSeren()

elif action == 'integrationIncursion':
	OrionIntegration.executeIncursion()

elif action == 'integrationPlacenta':
	OrionIntegration.executePlacenta()

elif action == 'integrationCovenant':
	OrionIntegration.executeCovenant()

elif action == 'integrationMagicality':
	OrionIntegration.executeMagicality()

elif action == 'integrationTheoath':
	OrionIntegration.executeTheOath()

elif action == 'integrationYoda':
	OrionIntegration.executeYoda()

elif action == 'integrationBodie':
	OrionIntegration.executeBodie()

elif action == 'integrationNymeria':
	OrionIntegration.executeNymeria()

elif action == 'integrationVenom':
	OrionIntegration.executeVenom()

elif action == 'integrationScrubs':
	OrionIntegration.executeScrubs()

elif action == 'integrationMedusa':
	OrionIntegration.executeMedusa()

elif action == 'integrationMercury':
	OrionIntegration.executeMercury()

elif action == 'integrationDeceit':
	OrionIntegration.executeDeceit()

elif action == 'integrationFen':
	OrionIntegration.executeFen()

elif action == 'integrationGenesis':
	OrionIntegration.executeGenesis()

elif action == 'integrationExodus':
	OrionIntegration.executeExodus()

elif action == 'integrationExodusRedux':
	OrionIntegration.executeExodusRedux()

elif action == 'integrationNeptuneRising':
	OrionIntegration.executeNeptuneRising()

elif action == 'integrationDeathStreams':
	OrionIntegration.executeDeathStreams()

elif action == 'integrationBoomMovies':
	OrionIntegration.executeBoomMovies()

elif action == 'integrationContinuum':
	OrionIntegration.executeContinuum()

elif action == 'integrationMarauder':
	OrionIntegration.executeMarauder()

elif action == 'integrationAsguard':
	OrionIntegration.executeAsguard()

elif action == 'integrationTheCrew':
	OrionIntegration.executeTheCrew()

elif action == 'integrationOpenScrapers':
	OrionIntegration.executeOpenScrapers()

elif action == 'integrationLambdaScrapers':
	OrionIntegration.executeLambdaScrapers()

elif action == 'integrationUniversalScrapers':
	OrionIntegration.executeUniversalScrapers()

elif action == 'integrationNanScrapers':
	OrionIntegration.executeNanScrapers()

elif action == 'integrationElementum':
	OrionIntegration.executeElementum()

elif action == 'integrationQuasar':
	OrionIntegration.executeQuasar()
