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
# ORIONDATABASE
##############################################################################
# Class for handling SQLite databases.
##############################################################################

import threading
from orion.modules.oriontools import *
try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

class OrionDatabase(object):

	Initialized = False
	Instances = {}
	Locks = {}
	LocksCustom = {}

	##############################################################################
	# CONSTANTS
	##############################################################################

	Timeout = 20
	Extension = '.db'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, name = None, default = None, path = None, connect = True):
		try:
			if name == None: name = OrionTools.hash(path)

			if not name in OrionDatabase.Locks:
				OrionDatabase.Locks[name] = threading.Lock()
			self.mLock = OrionDatabase.Locks[name]

			if not name in OrionDatabase.LocksCustom:
				OrionDatabase.LocksCustom[name] = threading.Lock()
			self.mLockCustom = OrionDatabase.LocksCustom[name]

			if path == None:
				if not name.endswith(OrionDatabase.Extension): name += OrionDatabase.Extension
				self.mPath = OrionTools.pathJoin(OrionTools.pathResolve(OrionTools.addonProfile()), name)
				if default and not OrionTools.fileExists(self.mPath):
					OrionTools.fileCopy(OrionTools.pathJoin(default, name), self.mPath)
			else:
				if not path.endswith(OrionDatabase.Extension): path += OrionDatabase.Extension
				self.mPath = path
			if connect: self._connect()
		except:
			OrionTools.error()

	def __del__(self):
		self._close()

	@classmethod
	def instance(self, name, default = None, path = None, create = None):
		self.instancesInitialize()

		id = name
		if default: id += '_' + default
		if path: id += '_' + path
		id = OrionTools.hash(id)

		if not id in OrionDatabase.Instances:
			OrionDatabase.Instances[id] = OrionDatabase(name = name, default = default, path = path)
			if not create == None: OrionDatabase.Instances[id].create(create)
		return OrionDatabase.Instances[id]

	@classmethod
	def instancesInitialize(self):
		# Python only deletes instances if there are no more references to them.
		# The database instances have to be manually deleted to ensure that the connections are closed.
		# Do not close connections from the Orion() destructor, since some connections might still be running in a thread when the destructor is executed.
		if not OrionDatabase.Initialized:
			import atexit
			OrionDatabase.Initialized = True
			atexit.register(self.instancesClear)

	@classmethod
	def instancesClear(self):
		for instance in OrionTools.iteratorValues(OrionDatabase.Instances):
			instance._close()
		OrionDatabase.Instances = {}
		OrionDatabase.Locks = {}
		OrionDatabase.Custom = {}

	##############################################################################
	# INTERNAL
	##############################################################################

	def _lock(self):
		self.mLockCustom.acquire()

	def _unlock(self):
		if self.mLockCustom.locked():
			self.mLockCustom.release()

	def _connect(self):
		try:
			# When the addon is launched for the first time after installation, an error occurs, since the addon userdata directory does not exist yet and the database file is written to that directory.
			# If the directory does not exist yet, create it.
			OrionTools.directoryCreate(OrionTools.directoryName(self.mPath))

			# SQLite does not allow database objects to be used from multiple threads. Explicitly allow multi-threading.
			try: self.mConnection = database.connect(self.mPath, check_same_thread = False, timeout = OrionDatabase.Timeout)
			except: self.mConnection = database.connect(self.mPath, timeout = OrionDatabase.Timeout)

			self.mDatabase = self.mConnection.cursor()
			return True
		except:
			self._close()
			return False

	def _close(self):
		try:
			self.mLock.acquire()
			self.mConnection.close()
			self.mConnection = None
			self.mDatabase = None
		except:
			pass
		finally:
			self.mLock.release()

	def _list(self, items):
		if not type(items) in [list, tuple]: items = [items]
		return items

	def _null(self):
		return 'NULL'

	def _commit(self):
		try:
			self.mLock.acquire()
			self.mConnection.commit()
			return True
		except:
			return False
		finally:
			self.mLock.release()

	def _commitCheck(self, result, commit = True):
		# NB: Always commit create/insert/update/delete queries.
		# Otherwise there are "OperationalError -> database is locked" errors.
		# If you scrape the first time, everything works and is fast.
		# Scraping a 2nd time right afterwards, takes very long (even though the retrieved streams popup shows early).
		# This is because of the "Timeout". SQLite will wait 20 seconds while the database is locked, but will eventually still throw the error.
		# It seems that if _commit() is always called, the error does not happen, because the database is unlocked immediatly after executing a query.
		#if result and commit: return self._commit()
		return self._commit()

	def _execute(self, query, parameters = None):
		try:
			self.mLock.acquire()
			if parameters == None: self.mDatabase.execute(query)
			else: self.mDatabase.execute(query, parameters)
			return True
		except:
			OrionTools.error()
			return False
		finally:
			self.mLock.release()

	# query must contain %s for table name.
	# tables can be None, table name, or list of tables names.
	# If tables is None, will retrieve all tables in the database.
	def _executeAll(self, query, tables = None, parameters = None):
		result = True
		if tables == None: tables = self.tables()
		tables = self._list(tables)
		for table in tables:
			result = result and self._execute(query % table, parameters = parameters)
		return result

	##############################################################################
	# GENERAL
	##############################################################################

	def tables(self):
		return self.selectValues('SELECT name FROM sqlite_master WHERE type IS "table"')

	def create(self, query, parameters = None, commit = True):
		result = self._execute(query, parameters = parameters)
		result = self._commitCheck(result = result, commit = commit)
		return result

	def createAll(self, query, tables, parameters = None, commit = True):
		result = self._executeAll(query, tables = tables, parameters = parameters)
		result = self._commitCheck(result = result, commit = commit)
		return result

	# Retrieves a list of rows.
	# Each row is a tuple with all the return values.
	# Eg: [(row1value1, row1value2), (row2value1, row2value2)]
	def select(self, query, parameters = None):
		self._execute(query, parameters = parameters)
		return self.mDatabase.fetchall()

	# Retrieves a single row.
	# Each row is a tuple with all the return values.
	# Eg: (row1value1, row1value2)
	def selectSingle(self, query, parameters = None):
		self._execute(query, parameters = parameters)
		return self.mDatabase.fetchone()

	# Retrieves a list of single values from rows.
	# Eg: [row1value1, row1value2]
	def selectValues(self, query, parameters = None):
		try:
			result = self.select(query, parameters = parameters)
			return [i[0] for i in result]
		except: return []

	# Retrieves a signle value from a single row.
	# Eg: row1value1
	def selectValue(self, query, parameters = None):
		try: return self.selectSingle(query, parameters = parameters)[0]
		except: return None

	# Checks if the value exists, such as an ID.
	def exists(self, query, parameters = None):
		return len(self.select(query, parameters = parameters)) > 0

	def insert(self, query, parameters = None, commit = True):
		result = self._execute(query, parameters = parameters)
		result = self._commitCheck(result = result, commit = commit)
		return result

	def update(self, query, parameters = None, commit = True):
		result = self._execute(query, parameters = parameters)
		result = self._commitCheck(result = result, commit = commit)
		return result

	# Deletes specific row in table.
	# If table is none, assumes it was already set in the query
	def delete(self, query, parameters = None, table = None, commit = True):
		if not table == None: query = query % table
		result = self._execute(query, parameters = parameters)
		result = self._commitCheck(result = result, commit = commit)
		return result

	# Deletes all rows in table.
	# tables can be None, table name, or list of tables names.
	# If tables is None, deletes all rows in all tables.
	def deleteAll(self, tables = None, parameters = None, commit = True):
		result = self._executeAll('DELETE FROM %s;', tables, parameters = parameters)
		result = self._commitCheck(result = result, commit = commit)
		return result

	# Drops single table.
	def drop(self, table, parameters = None, commit = True):
		result = self._execute('DROP TABLE IF EXISTS %s;' % table, parameters = parameters)
		result = self._commitCheck(result = result, commit = commit)
		return result

	# Drops all tables.
	def dropAll(self, parameters = None, commit = True):
		result = self._executeAll('DROP TABLE IF EXISTS %s;', parameters = parameters)
		result = self._commitCheck(result = result, commit = commit)
		return result
