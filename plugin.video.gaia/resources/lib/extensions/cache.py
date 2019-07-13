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

import re
import ast
import threading
from resources.lib.extensions import tools
from resources.lib.extensions import database

class Cache(database.Database):

	Name = 'cache' # The name of the file. Update version number of the database structure changes.
	NameTrakt = 'trakt'

	Skip = '[GAIACACHESKIP]' # If a function returns this value, it will not be cached.

	ModeSynchronous = 1		# If expired, wait until the new data has been retrieved, and return the new data.
	ModeAsynchronous = 2	# If expired, retrieve the new data in the background, and immediately return the old data.
	ModeDefault = ModeAsynchronous

	StorageAll = 1		# Cache all data to the database.
	StorageFull = 2		# Only cache non-empty data to the database.
	StorageDefault = StorageAll

	# Keep the timeout as short as possible.
	# The idea is to always update the data in the background on each request.
	# This can cause too many requests if the same cache is access multiple times per second/minute.
	TimeoutClear = -1 # Force refresh the data, but wait until the new data comes in (ModeSynchronous).
	TimeoutRefresh = 0 # Force refresh the data, but still return the current cached data (ModeAsynchronous).
	TimeoutReset = 2592000 # 30 Days. Maximum timeout. If values are greater than this, the timeout will be set to TimeoutClear.
	TimeoutMini = 600  # 10 Minutes.
	TimeoutShort = 3600 # 1 Hour.
	TimeoutMedium = 21600 # 6 Hours.
	TimeoutLong = 259200 # 3 Days.

	def __init__(self, mode = ModeDefault, storage = StorageDefault):
		database.Database.__init__(self, Cache.Name)
		self.mMode = mode
		self.mStorage = storage

	##############################################################################
	# DATABASE
	##############################################################################

	def _initialize(self):
		self._create('''
			CREATE TABLE IF NOT EXISTS %s
			(
				id TEXT,
				time INTEGER,
				data TEXT,
				UNIQUE(id)
			);
			'''
		)
		self._create('''
			CREATE TABLE IF NOT EXISTS %s
			(
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				time INTEGER,
				link TEXT,
				data TEXT
			);
			''' % Cache.NameTrakt
		)

	##############################################################################
	# ID
	##############################################################################

	def _id(self, function, kwargs):
		id = re.sub('>', '', re.sub('.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', repr(function))) + '_'
		id += '_'.join([str(key) + '=' + str(value) for key, value in kwargs.iteritems()])
		return tools.Hash.sha512(id)

	##############################################################################
	# CACHE
	##############################################################################

	def _cacheRetrieve(self, id):
		return self._selectSingle('SELECT time, data FROM %s WHERE id = ?;', parameters = (id,))

	def _cacheUpdate(self, id, data):
		self._insert('INSERT OR IGNORE INTO %s (id) VALUES (?);', (id,))
		return self._update('UPDATE %s SET time = ?, data = ? WHERE id = ?;', parameters = (tools.Time.timestamp(), data, id))

	def _cacheDelete(self, id):
		return self._update('DELETE FROM %s WHERE id = ?;', parameters = (id,))

	def _cacheDataTo(self, data):
		return repr(data)

	def _cacheDataFrom(self, data):
		if data is None: return data
		try: data = data.encode('utf-8')
		except: pass
		return ast.literal_eval(data)

	def _cacheDataValid(self, data):
		if data is None or data == [] or data == {} or data == '': return False
		elif data == 'None' or data == '[]' or data == '{}': return False
		else: return True

	def _cacheArguments(self, function, *args, **kwargs):
		# Convert args to kwargs.
		parameters = function.func_code.co_varnames
		parameters = (parameter for parameter in parameters if not parameter == 'self')
		kwargs.update(dict(zip(parameters, args)))
		return kwargs

	def _cache(self, result, id, function, kwargs):
		try:
			data = function(**kwargs)
			if data == Cache.Skip:
				result[0] = None
			else:
				data = self._cacheDataTo(data)
				if self.mStorage == Cache.StorageAll or self._cacheDataValid(data): self._cacheUpdate(id, data)
				result[0] = data
		except:
			tools.Logger.error()

	def cache(self, timeout, function, *args, **kwargs):
		try:
			kwargs = self._cacheArguments(function, *args, **kwargs)
			id = self._id(function, kwargs)

			if timeout >= Cache.TimeoutRefresh:
				cache = self._cacheRetrieve(id)
				if cache:
					difference = tools.Time.timestamp() - cache[0]
					if difference > Cache.TimeoutReset: timeout = Cache.TimeoutClear
					elif difference <= timeout: return self._cacheDataFrom(cache[1])
			else:
				cache = None

			result = [None]
			thread = threading.Thread(target = self._cache, args = (result, id, function, kwargs))
			thread.start()
			if timeout == Cache.TimeoutClear or self.mMode == Cache.ModeSynchronous or not cache:
				thread.join()
			else:
				result[0] = cache[1]

			return self._cacheDataFrom(result[0])
		except:
			tools.Logger.error()
		return None

	def cacheRetrieve(self, function, *args, **kwargs):
		try:
			kwargs = self._cacheArguments(function, *args, **kwargs)
			id = self._id(function, kwargs)
			return self._cacheDataFrom(self._cacheRetrieve(id)[1])
		except:
			return None

	def cacheExists(self, function, *args, **kwargs):
		return bool(self.cacheRetrieve(function, *args, **kwargs))

	# Delete the entire cahce entry.
	def cacheDelete(self, function, *args, **kwargs):
		kwargs = self._cacheArguments(function, *args, **kwargs)
		id = self._id(function, kwargs)
		self._cacheDelete(id)

	# Force refresh the data, but wait until the new data comes in (ModeSynchronous).
	def cacheClear(self, function, *args, **kwargs):
		return self.cache(Cache.TimeoutClear, function, *args, **kwargs)

	# Force refresh the data, but still return the current cached data (ModeAsynchronous).
	def cacheRefresh(self, function, *args, **kwargs):
		return self.cache(Cache.TimeoutRefresh, function, *args, **kwargs)

	def cacheSeconds(self, timeout, function, *args, **kwargs):
		return self.cache(timeout, function, *args, **kwargs)

	def cacheMinutes(self, timeout, function, *args, **kwargs):
		return self.cache(timeout * 60, function, *args, **kwargs)

	def cacheHours(self, timeout, function, *args, **kwargs):
		return self.cache(timeout * 3600, function, *args, **kwargs)

	def cacheDays(self, timeout, function, *args, **kwargs):
		return self.cache(timeout * 86400, function, *args, **kwargs)

	def cacheMini(self, function, *args, **kwargs):
		return self.cache(Cache.TimeoutMini, function, *args, **kwargs)

	def cacheShort(self, function, *args, **kwargs):
		return self.cache(Cache.TimeoutShort, function, *args, **kwargs)

	def cacheMedium(self, function, *args, **kwargs):
		return self.cache(Cache.TimeoutMedium, function, *args, **kwargs)

	def cacheLong(self, function, *args, **kwargs):
		return self.cache(Cache.TimeoutLong, function, *args, **kwargs)

	##############################################################################
	# TRAKT
	##############################################################################

	def traktCache(self, link, data = None, timestamp = None):
		# Only cache the requests that change something on the Trakt account.
		# Trakt uses JSON post data to set things and only uses GET parameters to retrieve things.
		if data == None: return None
		if timestamp == None: timestamp = tools.Time.timestamp()
		self._insert('INSERT INTO %s (time, link, data) VALUES (?, ?, ?);' % Cache.NameTrakt, parameters = (timestamp, link, self._cacheDataTo(data)))

	def traktRetrieve(self):
		self._lock() # Execute the select and delete as atomic operations.
		result = self._selectSingle('SELECT id, time, link, data FROM %s ORDER BY time ASC LIMIT 1;' % Cache.NameTrakt)
		if not result:
			self._unlock()
			return None
		self._delete('DELETE FROM %s WHERE id = ?;' % Cache.NameTrakt, parameters = (result[0],))
		self._unlock()
		return {'time' : result[1], 'link' : result[2], 'data' : self._cacheDataFrom(result[3])}
