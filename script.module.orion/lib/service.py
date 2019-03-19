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

from orion import *
from orion.modules.orionuser import *
from orion.modules.orionsettings import *
from orion.modules.orionintegration import *
from orion.modules.orionnotification import *

OrionSettings.adapt()
orion = Orion(OrionApi._keyInternal())
user = OrionUser.instance()
if user.enabled() and user.valid():
	OrionSettings.externalClean()
	OrionIntegration.check()
	user.update()
	OrionNotification.dialogNew()
