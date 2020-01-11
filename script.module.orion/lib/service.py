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
# ORIONSERVICE
##############################################################################
# The service to launch on Kodi startup.
##############################################################################

import xbmc
from orion import *
from orion.modules.orionuser import *
from orion.modules.orionsettings import *
from orion.modules.orionintegration import *
from orion.modules.orionnotification import *
from orion.modules.orionticket import *
from orion.modules.oriondatabase import *

monitor = xbmc.Monitor()
while not monitor.abortRequested():
	OrionTools.log('Orion Service Started')
	OrionSettings.adapt()
	orion = Orion(OrionApi._keyInternal())
	user = OrionUser.instance()
	if user.enabled() and (user.valid() or user.empty()):
		OrionSettings.externalClean()
		OrionIntegration.check(silent = True)
		user.update()
		user.subscriptionCheck()
		OrionSettings.backupExportAutomaticOnline()
		OrionNotification.dialogVersion()
		OrionNotification.dialogNew()
		OrionTicket.dialogNew()
	OrionDatabase.instancesClear() # Very important. Without this, Kodi will fail to update the addon if a new version comes out, due to active database connections causing failures.
	orion = None # Clear to not keep it in memory while waiting.
	user = None # Clear to not keep it in memory while waiting.
	OrionTools.log('Orion Service Finished')
	if monitor.waitForAbort(86400): break # 24 hours
