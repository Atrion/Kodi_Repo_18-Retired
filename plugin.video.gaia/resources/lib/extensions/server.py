# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import xbmc
import threading
import SimpleHTTPServer
import SocketServer
from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.externals.mimetypes import mimetypes

# gaiaremove
# New webserver that will allow Gaia to be controled through a webinterface.
# Main feature will be to change Gaia's settings in a webinterface, since Kodi 18 has scroll issues in the settings dialog.

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

	def do_GET(self):
		root = tools.File.joinPath(tools.System.pathResources(), 'resources', 'server')
		if self.path == '/': path = root + '/index.html'
		else: path = root + self.path
		if tools.File.exists(path):
			self.send_response(200)
			type, encoding = mimetypes.MimeTypes().guess_type(path)
			if type == None: type = 'text/plain'
			self.send_header('Content-Type', type)
			self.end_headers()
			self.wfile.write(tools.File.readNow(path, utf = False))
		else:
			self.send_response(404)

	def do_POST(self):
		tools.Logger.log("IIIIIIIIIIIIIIIIIIIIIIIIvv: "+str(self.path))
		self.data_string = self.rfile.read(int(self.headers['Content-Length']))
		self.send_response(200)
		self.send_header('Content-Type', 'application/json')
		self.end_headers()
		self.wfile.write(bytes(tools.Converter.jsonTo('{data:null}')))
		tools.Logger.log("IIIIIIIIIIIIIIIIIIIIIIII: "+str( self.data_string))

class Server(object):

	Instance = None

	@classmethod
	def _init__(self):
		self.mServer = None

	@classmethod
	def instance(self):
		if Server.Instance == None: Server.Instance = Server()
		return Server.Instance

	@classmethod
	def run(self, wait = False):
		instance = self.instance()
		thread = threading.Thread(target = instance._run)
		thread.start()
		if wait: thread.join()

	def _run(self):
		thread = threading.Thread(target = self._start)
		thread.start()
		while thread.is_alive() and not xbmc.abortRequested:
			tools.Time.sleep(2)
		self._stop()

	@classmethod
	def _start(self):
		try:
			PORT = 10006
			self.mServer = SocketServer.TCPServer(("", PORT), ServerHandler)
			self.mServer.allow_reuse_address = True
			self.mServer.serve_forever()
		except:
			interface.Dialog.notification(title='socket',message='socket error')#gaiaremove
			tools.Logger.log("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")#gaiaremove

	def _stop(self):
		try: self.mServer.shutdown()
		except: pass
