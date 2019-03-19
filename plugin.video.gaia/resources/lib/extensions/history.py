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

import json
from resources.lib.extensions import database
from resources.lib.extensions import tools
from resources.lib.extensions import metadata as metadatax

class History(database.Database):

	Name = 'history' # The name of the file. Update version number of the database structure changes.

	def __init__(self):
		database.Database.__init__(self, History.Name)

	def _initialize(self):
		self._createAll('''
			CREATE TABLE IF NOT EXISTS %s
			(
				kids INTEGER,
				time INTEGER,
				link TEXT,
				metadata TEXT,
				source TEXT,
				UNIQUE(link)
			);
			''',
			[tools.Media.TypeMovie, tools.Media.TypeShow, tools.Media.TypeDocumentary, tools.Media.TypeShort]
		)

	def _type(self, type):
		if type == tools.Media.TypeEpisode or type == tools.Media.TypeSeason:
			return tools.Media.TypeShow
		else:
			return type

	def _prepare(self, data):
		if data == None:
			data = self._null()
		elif not isinstance(data, basestring):
			data = json.dumps(data)
		return '"%s"' % data.replace('"', '""').replace("'", "''")

	def insert(self, type, link, metadata, source, kids = tools.Selection.TypeUndefined):
		if 'metadata' in source:
			source['metadata'] = metadatax.Metadata.uninitialize(source)
		type = self._type(type)
		existing = self._select('SELECT link FROM %s WHERE link = "%s";' % (type, link))
		if existing:
			self.update(type, link)
		else:
			self._insert('''
				INSERT INTO %s
				(kids, time, link, metadata, source)
				VALUES
				(%d, %d, "%s", %s, %s);
				'''
				% (type, kids, tools.Time.timestamp(), link, self._prepare(metadata), self._prepare(source))
			)

	def insertMovie(self, link, metadata, source, kids = tools.Selection.TypeUndefined):
		self.insert(type = tools.Media.TypeMovie, kids = kids, link = link, metadata = metadata, source = source)

	def insertShow(self, link, metadata, source, kids = tools.Selection.TypeUndefined):
		self.insert(type = tools.Media.TypeShow, kids = kids, link = link, metadata = metadata, source = source)

	def insertDocumentary(self, link, metadata, source, kids = tools.Selection.TypeUndefined):
		self.insert(type = tools.Media.TypeDocumentary, kids = kids, link = link, metadata = metadata, source = source)

	def insertShort(self, link, metadata, source, kids = tools.Selection.TypeUndefined):
		self.insert(type = tools.Media.TypeShort, kids = kids, link = link, metadata = metadata, source = source)

	def update(self, type, link):
		type = self._type(type)
		self._update('UPDATE %s SET time = %d WHERE link = "%s";' % (type, tools.Time.timestamp(), link))

	def updateMovie(self, link):
		self.update(type = tools.Media.TypeMovie, link = link)

	def updateShow(self, link):
		self.update(type = tools.Media.TypeShow, link = link)

	def updateDocumentary(self, link):
		self.update(type = tools.Media.TypeDocumentary, link = link)

	def updateShort(self, link):
		self.update(type = tools.Media.TypeShort, link = link)

	def retrieve(self, type, count = 30, kids = tools.Selection.TypeUndefined):
		type = self._type(type)
		if type == None:
			return self.retrieveAll(count = count, kids = kids)
		else:
			if kids == tools.Selection.TypeUndefined: kids = ''
			else: kids = 'WHERE kids IS %d' % kids
			return self._select('SELECT "%s" as type, kids, time, link, metadata, source FROM %s %s ORDER BY time DESC LIMIT %d;' % (type, type, kids, count))

	def retrieveAll(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT type, kids, time, link, metadata, source FROM
			(
				SELECT time, kids, time, link, metadata, source, "%s" as type FROM %s
				UNION ALL
				SELECT time, kids, time, link, metadata, source, "%s" as type FROM %s
				UNION ALL
				SELECT time, kids, time, link, metadata, source, "%s" as type FROM %s
				UNION ALL
				SELECT time, kids, time, link, metadata, source, "%s" as type FROM %s
			)
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (tools.Media.TypeMovie, tools.Media.TypeMovie, tools.Media.TypeShow, tools.Media.TypeShow, tools.Media.TypeDocumentary, tools.Media.TypeDocumentary, tools.Media.TypeShort, tools.Media.TypeShort, kids, count))

	def retrieveMovie(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT "%s" as type, kids, time, link, metadata, source FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (tools.Media.TypeMovie, tools.Media.TypeMovie, kids, count))

	def retrieveShow(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT "%s" as type, kids, time, link, metadata, source FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (tools.Media.TypeShow, tools.Media.TypeShow, kids, count))

	def retrieveDocumentary(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT "%s" as type, kids, time, link, metadata, source FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (tools.Media.TypeDocumentary, tools.Media.TypeDocumentary, kids, count))

	def retrieveShort(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT "%s" as type, kids, time, link, metadata, source FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (tools.Media.TypeShort, tools.Media.TypeShort, kids, count))
