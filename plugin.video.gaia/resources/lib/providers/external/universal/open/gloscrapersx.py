# -*- coding: utf-8 -*-

"""
	Gaia Addon

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

# NB: This script can not have the same name as the external addon.
# Otherwise the import statement will import this script instead of the external addon.
import globalscrapers

from resources.lib.extensions import tools
from resources.lib.extensions import provider

class source(provider.ProviderExternalUnstructured):

	Name = 'GlobalScrapers'

	IdAddon = tools.Extensions.IdGloScrapers
	IdLibrary = 'globalscrapers'
	IdGaia = 'gloscrapersx'

	Path = ['lib', IdLibrary, 'sources']
