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
# ORIONCONTAINER
##############################################################################
# Class for managing Orion hash lookups.
##############################################################################

import threading
from orion.modules.orionapi import *

class OrionContainer:

	##############################################################################
	# CONSTANTS
	##############################################################################

	# Split hash lookups into chunks to ensure that the server can do the lookups before timing out.
	# Could potentially have very large chunks, but smaller chunks will be more efficient as multithreaded API requests.
	ChunkSize = 100

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, data = None, full = True):
		self.mData = data
		self.mFull = full

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	##############################################################################
	# ID
	##############################################################################

	def id(self, default = None):
		if self.mFull:
			try: return self.mData['id']
			except: pass
		return default

	##############################################################################
	# TIME
	##############################################################################

	def time(self, default = None):
		if self.mFull:
			try: return self.mData['time']
			except: pass
		return default

	##############################################################################
	# LINK
	##############################################################################

	def link(self, default = None):
		return self.linkSource(default = default)

	def linkSource(self, default = None):
		if self.mFull:
			try: return self.mData['link']['source']
			except: return default
		else:
			try: return self.mData.keys()[0]
			except: return default

	def linkOrion(self, default = None):
		if self.mFull:
			try: return self.mData['link']['orion']
			except: pass
		return default

	def linkMagnet(self, default = None):
		if self.mFull:
			try: return self.mData['link']['magnet']
			except: pass
		return default

	##############################################################################
	# HASH
	##############################################################################

	def hash(self, default = None):
		if self.mFull:
			try: return self.mData['hash']
			except: return default
		else:
			try: return self.mData.values()[0]
			except: return default

	##############################################################################
	# SEGMENT
	##############################################################################

	def segmentFirst(self, default = None):
		if self.mFull:
			try: return self.mData['segment']['first']
			except: return default
		else:
			try: return self.mData.values()[0]['segment']['first']
			except:
				try: return self.mData.values()[0]['first']
				except: return default

	def segmentLargest(self, default = None):
		if self.mFull:
			try: return self.mData['segment']['largest']
			except: return default
		else:
			try: return self.mData.values()[0]['segment']['largest']
			except:
				try: return self.mData.values()[0]['largest']
				except: return default

	def segmentList(self, default = None):
		if self.mFull:
			try: return self.mData['segment']['list']
			except: return default
		else:
			try: return self.mData.values()[0]['segment']['list']
			except:
				try: return self.mData.values()[0]['list']
				except: return default

	##############################################################################
	# IDENTIFIERS
	##############################################################################

	@classmethod
	def identifiers(self, links):
		if links:
			if OrionTools.isString(links): links = [links]
			chunks = [links[i : i + OrionContainer.ChunkSize] for i in xrange(0, len(links), OrionContainer.ChunkSize)]
			results = []
			threads = []
			for i in range(len(chunks)):
				results.append(None)
				threads.append(threading.Thread(target = self._identifiers, args = (chunks[i], results, i)))
			[i.start() for i in threads]
			[i.join() for i in threads]
			result = [i for j in results if j for i in j if i]
			if len(result) > 0: return result
		return []

	@classmethod
	def _identifiers(self, links, results, index):
		try:
			api = OrionApi()
			api.containerIdentifier(links = links)
			if api.statusSuccess():
				identifiers = []
				data = api.data()['identifiers']
				for key, value in OrionTools.iterator(data):
					identifiers.append(OrionContainer(data = {key : value}, full = False))
				results[index] = identifiers
		except:
			OrionTools.error()

	##############################################################################
	# HASHES
	##############################################################################

	@classmethod
	def hashes(self, links):
		if links:
			if OrionTools.isString(links): links = [links]
			chunks = [links[i : i + OrionContainer.ChunkSize] for i in xrange(0, len(links), OrionContainer.ChunkSize)]
			results = []
			threads = []
			for i in range(len(chunks)):
				results.append(None)
				threads.append(threading.Thread(target = self._hashes, args = (chunks[i], results, i)))
			[i.start() for i in threads]
			[i.join() for i in threads]
			result = [i for j in results if j for i in j if i]
			if len(result) > 0: return result
		return []

	@classmethod
	def _hashes(self, links, results, index):
		try:
			api = OrionApi()
			api.containerHash(links = links)
			if api.statusSuccess():
				hashes = []
				data = api.data()['hashes']
				for key, value in OrionTools.iterator(data):
					hashes.append(OrionContainer(data = {key : value}, full = False))
				results[index] = hashes
		except:
			OrionTools.error()

	##############################################################################
	# SEGMENTS
	##############################################################################

	@classmethod
	def segments(self, links):
		if links:
			if OrionTools.isString(links): links = [links]
			chunks = [links[i : i + OrionContainer.ChunkSize] for i in xrange(0, len(links), OrionContainer.ChunkSize)]
			results = []
			threads = []
			for i in range(len(chunks)):
				results.append(None)
				threads.append(threading.Thread(target = self._segments, args = (chunks[i], results, i)))
			[i.start() for i in threads]
			[i.join() for i in threads]
			result = [i for j in results if j for i in j if i]
			if len(result) > 0: return result
		return []

	@classmethod
	def _segments(self, links, results, index):
		try:
			api = OrionApi()
			api.containerSegment(links = links)
			if api.statusSuccess():
				identifiers = []
				data = api.data()['segments']
				for key, value in OrionTools.iterator(data):
					identifiers.append(OrionContainer(data = {key : value}, full = False))
				results[index] = identifiers
		except:
			OrionTools.error()

	##############################################################################
	# RETRIEVE
	##############################################################################

	@classmethod
	def retrieve(self, links):
		if links:
			if OrionTools.isString(links): links = [links]
			chunks = [links[i : i + OrionContainer.ChunkSize] for i in xrange(0, len(links), OrionContainer.ChunkSize)]
			results = []
			threads = []
			for i in range(len(chunks)):
				results.append(None)
				threads.append(threading.Thread(target = self._retrieve, args = (chunks[i], results, i)))
			[i.start() for i in threads]
			[i.join() for i in threads]
			result = [i for j in results if j for i in j if i]
			if len(result) > 0: return result
		return []

	@classmethod
	def _retrieve(self, links, results, index):
		try:
			api = OrionApi()
			api.containerRetrieve(links = links)
			if api.statusSuccess():
				containers = []
				data = api.data()['containers']
				for container in data:
					containers.append(OrionContainer(data = container, full = True))
				results[index] = containers
		except:
			OrionTools.error()

	##############################################################################
	# DOWNLOAD
	##############################################################################

	# The id can be the container's ID, SHA1 hash, or link.
	# If a path is provided, the container will be download to file, otherwise the container's binary data will be returned.
	@classmethod
	def download(self, id, path = None, wait = True):
		if wait:
			return self._download(id = id, path = path)
		else:
			thread = threading.Thread(target = self._download, args = (id, path))
			thread.start()

	@classmethod
	def _download(self, id, path = None):
		try:
			api = OrionApi()
			data = api.containerDownload(id = id)
			if path == None: return data
			if data: return OrionTools.fileWrite(path = path, data = data, binary = True)
		except:
			OrionTools.error()
		return False
