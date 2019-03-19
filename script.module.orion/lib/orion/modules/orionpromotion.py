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
# ORIONPROMOTION
##############################################################################
# Class for managing Orion promotions.
##############################################################################

from orion.modules.orionapi import *

class OrionPromotion:

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, data = None):
		self.mData = data

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	##############################################################################
	# ID
	##############################################################################

	def id(self, default = None):
		try: return self.mData['id']
		except: return default

	##############################################################################
	# TIME
	##############################################################################

	def timeStart(self, default = None):
		try: return self.mData['time']['start']
		except: return default

	def timeEnd(self, default = None):
		try: return self.mData['time']['end']
		except: return default

	##############################################################################
	# LIMIT
	##############################################################################

	def limitMultiplier(self, default = None):
		try: return self.mData['limit']['multiplier']
		except: return default
