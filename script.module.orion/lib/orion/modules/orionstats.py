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
# OrionStats
##############################################################################
# Class for managing Orion server stats.
##############################################################################

from orion.modules.orionapi import *

OrionStatsInstance = None

class OrionStats:

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, data = None):
		self.mData = data

	##############################################################################
	# INSTANCE
	##############################################################################

	@classmethod
	def instance(self):
		global OrionStatsInstance
		if OrionStatsInstance == None: OrionStatsInstance = OrionStats()
		return OrionStatsInstance

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	##############################################################################
	# TIME
	##############################################################################

	def time(self, default = None):
		try: return self.mData['time']
		except: return default

	##############################################################################
	# COUNT
	##############################################################################

	def countStreams(self, default = None):
		try: return self.mData['count']['streams']
		except: return default

	def countContainers(self, default = None):
		try: return self.mData['count']['containers']
		except: return default

	def countHashes(self, default = None):
		try: return self.mData['count']['hashes']
		except: return default

	def countMovies(self, default = None):
		try: return self.mData['count']['movies']
		except: return default

	def countShows(self, default = None):
		try: return self.mData['count']['shows']
		except: return default

	def countEpisodes(self, default = None):
		try: return self.mData['count']['episodes']
		except: return default

	def countUsers(self, default = None):
		try: return self.mData['count']['users']
		except: return default

	def countRequests(self, default = None):
		try: return self.mData['count']['requests']
		except: return default

	def countResults(self, default = None):
		try: return self.mData['count']['results']
		except: return default

	##############################################################################
	# USAGE
	##############################################################################

	def usage(self, default = None):
		try: return self.mData['usage']
		except: return default

	##############################################################################
	# UPDATE
	##############################################################################

	def update(self):
		try:
			api = OrionApi()
			result = api.serverStats()
			if not result: return False
			self.mData = api.data()
			return True
		except:
			OrionTools.error()
		return False
