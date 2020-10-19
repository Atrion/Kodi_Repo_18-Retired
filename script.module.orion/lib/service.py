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

	# On some Android devices the copying of settings.xml does not work for some reason.
	# This might also happen right after the addon is updated, maybe Kodi has a temporarily file lock during updates.
	# Retry multiple times, sleeping in between, waiting for any locks to be released.
	OrionSettings.adapt(retries = 5)
	if monitor.abortRequested(): break

	# Do not show unreachable errors in the service.
	orion = Orion(key = OrionApi._keyInternal(), silent = True)
	user = OrionUser.instance()

	if user.enabled() and (user.valid() or user.empty()):
		OrionSettings.externalClean()
		if monitor.abortRequested(): break

		OrionIntegration.check(silent = True)
		if monitor.abortRequested(): break

		user.update()
		if monitor.abortRequested(): break

		user.subscriptionCheck()
		if monitor.abortRequested(): break

		OrionSettings.backupExportAutomaticOnline()
		if monitor.abortRequested(): break

		OrionNotification.dialogVersion()
		if monitor.abortRequested(): break

		OrionNotification.dialogNew()
		if monitor.abortRequested(): break

		OrionPromotion.dialogNew()
		if monitor.abortRequested(): break

		OrionTicket.dialogNew()
		if monitor.abortRequested(): break

	OrionDatabase.instancesClear() # Very important. Without this, Kodi will fail to update the addon if a new version comes out, due to active database connections causing failures.
	orion = None # Clear to not keep it in memory while waiting.
	user = None # Clear to not keep it in memory while waiting.

	OrionTools.log('Orion Service Finished')
	if monitor.waitForAbort(86400): break # 24 hours
