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


import re,sys,json,time,xbmc,xbmcvfs
import hashlib,os,zlib,base64,codecs,xmlrpclib,threading

try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.modules import playcount
from resources.lib.modules import trakt

from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import window
from resources.lib.extensions import downloader
from resources.lib.extensions import debrid
from resources.lib.extensions import handler
from resources.lib.extensions import metadata
from resources.lib.extensions import library
from resources.lib.extensions import orionoid

# If the player automatically closes/crashes because the EOF was reached while still downloading, the player instance is never deleted.
# Now the player keeps a constant lock on the played file and the file cannot be deleted (manually, or by the downloader). The lock is only release when Kodi exits.
# Use a thread and forcefully delete the instance. Although this is still no garantuee that Kodi will release the lock on the file, but it seems to work most of the time.
def playerDelete(instance):
	time.sleep(1)
	# Do not just use "del instance", since this will only call __del__() if the reference count drops to 0. Kodi still has a reference to the instance.
	try: instance.__del__()
	except: pass
	try: del instance
	except: pass

class player(xbmc.Player):

	# Statuses
	StatusIdle = 0
	StatusPlaying = 1
	StatusPaused = 2
	StatusStopped = 3
	StatusEnded = 4

	# Download
	DownloadThresholdStart = 0.01 # If the difference between the download and the playback progress is lower than this percentage, buffering will start.
	DownloadThresholdStop = DownloadThresholdStart * 2 # If the difference between the download and the playback progress is higher than this percentage, buffering will stop.
	DownloadMinimum = 1048576 # 1 MB. The minimum number of bytes that must be available to avoid buffering. If the value is too small, the player with automatically stop/crash due to insufficient data available.
	DownloadFuture = 102400 # 100 KB. The number of bytes to read and update the progress with. Small values increase disk access, large values causes slow/jumpy progress.
	DownloadChunk = 8 # 8 B. The number of null bytes that are considered the end of file.
	DownloadNull = '\x00' * DownloadChunk

	def __init__ (self, type = None, kids = None):
		from resources.lib.extensions import core
		xbmc.Player.__init__(self)
		self.status = self.StatusIdle
		self.core = core.Core(type = type, kids = kids)

	def __del__(self):
		self._downloadClear(delete = False)
		self.core.progressPlaybackClose()
		try: xbmc.Player.__del__(self)
		except: pass

	def run(self, type, title, year, season, episode, imdb, tmdb, tvdb, url, meta, downloadType = None, downloadId = None, handle = None, source = None):
		try:
			control.sleep(200)

			self.navigationStreamsSpecial = tools.Settings.getInteger('interface.navigation.streams') == 0

			self.type = type
			self.typeMovie = tools.Media.typeMovie(self.type)
			self.typeTelevision = tools.Media.typeTelevision(self.type)

			self.timeTotal = 0
			self.timeCurrent = 0

			self.metadata = meta
			self.title = title
			self.year = year
			try: self.name = tools.Media.titleUniversal(metadata = meta)
			except: self.name = self.title

			try:
				self.season = int(season) if self.typeTelevision else None
				self.seasonString = '%01d' % self.season if self.typeTelevision else None
			except:
				self.season = None
				self.seasonString = None
			try:
				self.episode = int(episode) if self.typeTelevision else None
				self.episodeString = '%01d' % self.episode if self.typeTelevision else None
			except:
				self.episode = None
				self.episodeString = None

			self.imdb = imdb
			self.tmdb = tmdb
			self.tvdb = tvdb

			self.progressLock = threading.Lock()
			self.progressBusy = False
			self.progressLast = 0
			self.progress = None
			if tools.Settings.getInteger('general.playback.resume') > 0:
				thread = threading.Thread(target = self._progress)
				thread.start()
			else:
				self.progress = 0

			self.idLocal = None
			self.idImdb = imdb if not imdb == None else '0'
			self.idTvdb = tvdb if not tvdb == None else '0'

			poster, thumb, meta = self.getMeta(meta)

			item = control.item(path = url)
			item.setArt({'icon' : thumb, 'thumb' : thumb, 'poster' : poster, 'tvshow.poster' : poster, 'season.poster' : poster})
			item.setInfo(type = 'Video', infoLabels = tools.Media.metadataClean(meta))

			self.url = url
			self.item = item
			self.timeTotal = 0
			self.timeCurrent = 0
			self.timeProgress = 0
			self.sizeTotal = 0
			self.sizeCurrent = 0
			self.sizeProgress = 0
			self.dialog = None

			self.downloadCheck = False
			if downloadType and downloadId:
				self.download = downloader.Downloader(type = downloadType, id = downloadId)
				self.bufferCounter = 0
				self.bufferShow = True

				# Already check here, so that the player waits when the download is still queued/initialized.
				if not self._downloadCheck():
					return
			else:
				self.download = None
				self.bufferCounter = None
				self.bufferShow = None

			self.handle = handle
			self.source = source
			metadata.Metadata.initialize(self.source)

			self.progressMessage = ''
			self.progressRemaining = 0
			self.progressTotal = 1
			success = False
			delay = 0
			if tools.Settings.getBoolean('general.playback.retry.enabled'):
				self.progressTotal += tools.Settings.getInteger('general.playback.retry.limit')
				delay = tools.Settings.getInteger('general.playback.retry.delay')
			self.progressRemaining = self.progressTotal

			xbmc.executebuiltin('Dialog.Close(notification,true)') # Hide the caching/download notification if still showing.
			while self.progressRemaining > 0:
				self.progressRemaining -= 1
				self.play(url, item)
				interface.Loader.hide()
				success = self.keepPlaybackAlive()
				if success or tools.System.aborted(): break
				if self.progressRemaining > 0:
					if interface.Core.background() and not self.core.progressPlaybackEnabled():
						self.progressMessage = interface.Translation.string(35303)
					else:
						if self.progressRemaining == 1: self.progressMessage = interface.Translation.string(35294)
						elif self.progressRemaining > 1: self.progressMessage = interface.Translation.string(35293) % (self.progressRemaining + 1)

			if not success and self.progressRemaining == 0:
				interface.Dialog.notification(title = 33448, message = 33450, icon = interface.Dialog.IconError)

			control.resolve(int(sys.argv[1]), True, item)

			ids = {}
			if imdb: ids['imdb'] = imdb
			if tvdb: ids['tvdb'] = tvdb
			control.window.setProperty('script.trakt.ids', json.dumps(ids))
			control.window.clearProperty('script.trakt.ids')
		except:
			tools.Logger.error()

	def getMeta(self, meta):
		try:
			poster = '0'
			if 'poster3' in meta: poster = meta['poster3']
			elif 'poster2' in meta: poster = meta['poster2']
			elif 'poster' in meta: poster = meta['poster']

			thumb = '0'
			if 'thumb3' in meta: thumb = meta['thumb3']
			elif 'thumb2' in meta: thumb = meta['thumb2']
			elif 'thumb' in meta: thumb = meta['thumb']

			if poster == '0': poster = control.addonPoster()
			if thumb == '0': thumb = control.addonThumb()

			return (poster, thumb, meta)
		except:
			pass

		try:
			if not self.typeMovie: raise Exception()

			meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "originaltitle", "year", "genre", "studio", "country", "runtime", "rating", "votes", "mpaa", "director", "writer", "plot", "plotoutline", "tagline", "thumbnail", "file"]}, "id": 1}' % (self.year, str(int(self.year)+1), str(int(self.year)-1)))
			meta = unicode(meta, 'utf-8', errors='ignore')
			meta = json.loads(meta)['result']['movies']

			t = cleantitle.get(self.title)
			meta = [i for i in meta if self.year == str(i['year']) and (t == cleantitle.get(i['title']) or t == cleantitle.get(i['originaltitle']))][0]

			for k, v in meta.iteritems():
				if type(v) == list:
					try: meta[k] = str(' / '.join([i.encode('utf-8') for i in v]))
					except: meta[k] = ''
				else:
					try: meta[k] = str(v.encode('utf-8'))
					except: meta[k] = str(v)

			if not 'plugin' in control.infoLabel('Container.PluginName'):
				self.idLocal = meta['movieid']

			poster = thumb = meta['thumbnail']

			return (poster, thumb, meta)
		except:
			pass

		try:
			if not self.typeTelevision: raise Exception()

			meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "year", "thumbnail", "file"]}, "id": 1}' % (self.year, str(int(self.year)+1), str(int(self.year)-1)))
			meta = unicode(meta, 'utf-8', errors='ignore')
			meta = json.loads(meta)['result']['tvshows']

			t = cleantitle.get(self.title)
			meta = [i for i in meta if self.year == str(i['year']) and t == cleantitle.get(i['title'])][0]

			tvshowid = meta['tvshowid'] ; poster = meta['thumbnail']

			meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params":{ "tvshowid": %d, "filter":{"and": [{"field": "season", "operator": "is", "value": "%s"}, {"field": "episode", "operator": "is", "value": "%s"}]}, "properties": ["title", "season", "episode", "showtitle", "firstaired", "runtime", "rating", "director", "writer", "plot", "thumbnail", "file"]}, "id": 1}' % (tvshowid, self.seasonString, self.episodeString))
			meta = unicode(meta, 'utf-8', errors='ignore')
			meta = json.loads(meta)['result']['episodes'][0]

			for k, v in meta.iteritems():
				if type(v) == list:
					try: meta[k] = str(' / '.join([i.encode('utf-8') for i in v]))
					except: meta[k] = ''
				else:
					try: meta[k] = str(v.encode('utf-8'))
					except: meta[k] = str(v)

			if not 'plugin' in control.infoLabel('Container.PluginName'):
				self.idLocal = meta['episodeid']

			thumb = meta['thumbnail']

			return (poster, thumb, meta)
		except:
			pass

		poster, thumb, meta = '', '', {'title': self.name}
		return (poster, thumb, meta)

	def _showStreams(self):
		if not tools.Settings.getBoolean('automatic.enabled'):
			reload = tools.Settings.getInteger('interface.navigation.streams.reload')
			if reload == 1 or (reload == 2 and self.status == self.StatusPaused):
				from resources.lib.extensions import core
				self.core.showStreams()

	def _debridClear(self):
		if self.handle:
			if not isinstance(self.handle, basestring):
				self.handle = self.handle.id()
			self.handle = self.handle.lower()
			source = self.source['source']
			try: id = self.source['stream']['id']
			except: id = self.url
			try: handle = self.source['stream']['handle']
			except: handle = None
			if handle == handler.HandlePremiumize.Id and debrid.Premiumize.deletePossible(source):
				pack = self.source['pack'] if 'pack' in self.source else None
				debrid.Premiumize().deletePlayback(id, pack)
			elif handle == handler.HandleOffCloud.Id and debrid.OffCloud.deletePossible(source):
				try: category = self.source['stream']['category']
				except: category = None
				pack = self.source['pack'] if 'pack' in self.source else None
				debrid.OffCloud().deletePlayback(id, pack, category)
			elif handle == handler.HandleRealDebrid.Id and debrid.RealDebrid.deletePossible(source):
				debrid.RealDebrid().deletePlayback(id)

	def _downloadStop(self):
		self._downloadClear(delete = False)
		if not self.download == None:
			self.download.stop(cacheOnly = True)

	def _downloadClear(self, delete = True):
		try: self.dialog.close()
		except: pass

		if delete:
			thread = threading.Thread(target = playerDelete, args = (self,))
			thread.start()

	def _downloadUpdateSize(self):
		try:
			# Try using the progress from the downloader, since the below code mostly returns 0.
			# Through Python, you can get the total file size (including the empty padded space).

			file = xbmcvfs.File(self.url) # The file must be opened each time this function is called, otherwise it does not refrehs with the new content/size.
			current = self.download.sizeCompleted()
			if current > 0:
				self.sizeCurrent = current
			else:
				file.seek(self.sizeCurrent, 0)
				data = file.read(self.DownloadChunk)
				try: length = len(data)
				except: length = 0
				while not data == self.DownloadNull and not length == 0:
					self.sizeCurrent += self.DownloadFuture
					file.seek(self.sizeCurrent, 0)
					data = file.read(self.DownloadChunk)
					try: length = len(data)
					except: length = 0
			self.sizeTotal = max(self.sizeTotal, file.size())
			file.close()
			if self.sizeTotal > 0: self.sizeProgress = self.sizeCurrent / float(self.sizeTotal)
		except:
			pass
		return self.sizeProgress

	def _downloadUpdateTime(self):
		try: self.timeCurrent = max(self.timeCurrent, self.getTime())
		except: pass
		try: self.timeTotal = max(self.timeTotal, self.getTotalTime())
		except: pass

		if self.timeTotal > 0:
			self.timeProgress = self.timeCurrent / float(self.timeTotal)
		return self.timeProgress

	def _downloadProgressDifference(self):
		progressSize = self._downloadUpdateSize()
		progressTime = self._downloadUpdateTime()
		return max(0, progressSize - progressTime), progressSize

	def _downloadProgress(self):
		progress = ''
		if not self.download == None:
			progress = interface.Format.fontBold(interface.Translation.string(32403) + ': ')
			self.download.refresh()
			progress += self.download.progress()
			progress += ' - ' + self.download.speed() + interface.Format.newline()
		return progress

	def _downloadCheck(self):
		if self.download == None:
			return False

		# Ensures that only one process can access this function at a time. Otherwise this function is executed multiple times at the same time.
		if self.downloadCheck:
			return False

		# If the user constantly cancels the buffering dialog, the dialog will not be shown for the rest of the playback.
		if not self.bufferShow:
			return False

		try:
			self.downloadCheck = True

			# Close all old and other dialogs.
			# Leave this for now. Seems to actually close the cache dialog below.
			#xbmc.executebuiltin('Dialog.Close(progressdialog,true)')
			#xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
			#time.sleep(0.5) # Wait for the dialogs to close.

			# NB: The progress dialog pops up when the download is at 100%. Chack for the download progress (progressSize < 1).
			progressDifference, progressSize = self._downloadProgressDifference()
			if progressSize < 1 and progressDifference < self.DownloadThresholdStart or self.sizeCurrent < self.DownloadMinimum:
				paused = False
				try:
					if self.isPlaying():
						self.pause()
						paused = True
				except: pass

				title = interface.Translation.string(33368)
				message = interface.Translation.string(33369)
				interface.Core.create(type = interface.Core.TypeDownload, title = title, message = self._downloadProgress() + message, background = False)

				progressMinimum = progressDifference
				progressRange = self.DownloadThresholdStop - progressMinimum
				while progressSize < 1 and progressDifference < self.DownloadThresholdStop or self.sizeCurrent < self.DownloadMinimum:
					progress = max(1, int(((progressDifference - progressMinimum) / float(progressRange)) * 99))
					interface.Core.update(progress = progress, message = self._downloadProgress() + message)
					if interface.Core.canceled(): break
					time.sleep(1)
					if interface.Core.canceled(): break
					progressDifference, progressSize = self._downloadProgressDifference()

				canceled = interface.Core.canceled() # Will be reset after the dialog is closed below.
				interface.Core.update(progress = 100, message = message)
				interface.Core.close()
				time.sleep(0.2)

				if canceled:
					if self.isPlayback():
						self.bufferCounter += 1
						if self.bufferCounter % 3 == 0:
							if interface.Dialog.option(title = 33368, message = 33744):
								self.bufferShow = False
					else:
						self._downloadStop()
						return False

				try:
					if paused:
						self.pause() # Unpause
				except: pass

			self.downloadCheck = False
			return True
		except:
			tools.Logger.error()
			self.downloadCheck = False
			return False

	def isVisible(self):
		return window.Window.visible(window.Window.IdWindowPlayer) or window.Window.visible(window.Window.IdWindowPlayerFull)

	def isPlayback(self):
		# Kodi often starts playback where isPlaying() is true and isPlayingVideo() is false, since the video loading is still in progress, whereas the play is already started.
		try: return self.isPlaying() and self.isPlayingVideo() and self.getTime() >= 0
		except: False

	def keepPlaybackWait(self, title, message, status, substatus1, substatus2, timeout):
		from resources.lib.extensions import core
		for i in range(0, timeout):
			if self.isPlayback(): break
			if self.download == None:
				if self.core.progressPlaybackCanceled(): break
				interface.Loader.hide() # Busy icons pops up again in Kodi 18.
				progress = 50 + int((i / float(timeout)) * 50) # Only half the progress, since the other half is from sources __init__.py.
				self.core.progressPlaybackUpdate(progress = progress, title = title, message = message, status = status, substatus1 = substatus1, substatus2 = substatus2, total = self.progressTotal, remaining = self.progressRemaining)
			else:
				self._downloadCheck()
			xbmc.sleep(500)

	def keepPlaybackAlive(self):
		from resources.lib.extensions import core
		self._downloadCheck()

		pname = '%s.player.overlay' % control.addonInfo('id')
		control.window.clearProperty(pname)

		if self.typeMovie:
			overlay = playcount.getMovieOverlay(playcount.getMovieIndicators(), self.idImdb)
		elif self.typeTelevision:
			overlay = playcount.getEpisodeOverlay(playcount.getTVShowIndicators(), self.idImdb, self.idTvdb, self.seasonString, self.episodeString)
		else:
			overlay = '6'

		title = interface.Translation.string(33451)
		status = interface.Translation.string(33452)
		substatus1 = interface.Translation.string(35474)
		substatus2 = interface.Translation.string(35303)
		message = self.progressMessage
		if not message == '':
			if interface.Core.background() and not self.core.progressPlaybackEnabled():
				message += ' - '
			else:
				message += '.' + interface.Format.newline()
		message += status
		interface.Loader.hide()

		self.core.progressPlaybackInitialize(title = title, message = message, metadata = self.metadata)
		timeout = tools.Settings.getInteger('general.playback.timeout')

		# Use a thread for Kodi 18, since the player freezes for a few seconds before starting playback.
		thread = threading.Thread(target = self.keepPlaybackWait, args = (title, message, status, substatus1, substatus2, timeout))
		thread.start()
		thread.join()

		if self.core.progressPlaybackCanceled():
			self.core.progressPlaybackClose()
			self.stop()
			self._debridClear()
			return True

		# Only show the notification if the player is not able to load the file at all.
		if not self.isPlayback():
			self.stop()
			self.core.progressPlaybackUpdate(progress = 100, message = '', status = None) # Must be set to 100 for background dialog, otherwise it shows up in a later dialog.
			control.window.clearProperty(pname)
			return False

		#self.core.progressPlaybackClose()
		addLibrary = tools.Settings.getBoolean('library.updates.watched')
		playbackEnd = tools.Settings.getInteger('general.playback.end') / 100.0

		streamsHas = False
		visibleWas = False

		while self.isPlayingVideo():
			try:
				self.timeTotal = self.getTotalTime()
				self.timeCurrent = self.getTime()

				watcher = (self.timeCurrent / self.timeTotal >= playbackEnd)
				property = control.window.getProperty(pname)

				if watcher == True and not property == '7':
					try: orionoid.Orionoid().streamVote(idItem = self.source['orion']['item'], idStream = self.source['orion']['stream'], vote = orionoid.Orionoid.VoteUp)
					except: pass
					control.window.setProperty(pname, '7')
					if self.typeMovie:
						playcount.markMovieDuringPlayback(self.idImdb, '7')
						if addLibrary: library.Library(type = self.type).add(title = self.title, year = self.year, imdb = self.imdb, tmdb = self.tmdb, metadata = self.metadata)
					else:
						playcount.markEpisodeDuringPlayback(self.idImdb, self.idTvdb, self.seasonString, self.episodeString, '7')
						if addLibrary: library.Library(type = self.type).add(title = self.title, year = self.year, imdb = self.imdb, tvdb = self.tvdb, metadata = self.metadata)
				elif watcher == False and not property == '6':
					control.window.setProperty(pname, '6')
					# Gaia
					# Do not mark as unwatched, otherwise if the video was previously watched and later rewatched, if will mark it as unwatched when played the second time.
					# Trakt can set multiple watches so that you can track on how many times you watched something.
					#playcount.markMovieDuringPlayback(self.idImdb, '6')
					#playcount.markEpisodeDuringPlayback(self.idImdb, self.idTvdb, self.seasonString, self.episodeString, '6')
			except:
				pass

			if self.navigationStreamsSpecial:
				for i in range(4):
					visible = self.isVisible()
					playback = self.isPlayback()
					if not visibleWas and visible: visibleWas = True
					if not streamsHas and playback and visibleWas and not visible:
						streamsHas = True
						self._showStreams()
					elif streamsHas and visible:
						streamsHas = False
						interface.Dialog.closeAll()
					if not self.download == None: self._downloadCheck()
					xbmc.sleep(1000)
			else:
				if self.download == None:
					xbmc.sleep(2000)
				else:
					for i in range(4):
						self._downloadCheck()
						xbmc.sleep(500)

		control.window.clearProperty(pname)
		return True

	def _progress(self):
		progress = Playback().getProgress(type = self.type, imdb = self.imdb, tvdb = self.tvdb, season = self.season, episode = self.episode, wait = True)
		try: self.progressLock.acquire()
		except: pass
		self.progress = progress
		try: self.progressLock.release()
		except: pass

	def getProgress(self):
		if self.timeCurrent <= 0 or self.timeTotal <= 0:
			return 0
		else:
			return (self.timeCurrent / float(self.timeTotal)) * 100.0

	def updateProgress(self, action):
		current = tools.Time.timestamp()
		allow = True
		if action == Playback.ActionPause:
			# When the player buffers, it pauses the video.
			# Only update every 5 minutes, otherwise there are too many Trakt/database calls.
			allow = (current - self.progressLast) > 300
		if allow:
			Playback().setProgress(action = action, type = self.type, imdb = self.imdb, tvdb = self.tvdb, season = self.season, episode = self.episode, progress = self.getProgress(), wait = False)
		self.progressLast = current

	def setProgress(self):
		try:
			if self.timeTotal == 0: self.timeTotal = self.getTotalTime()
			if self.timeCurrent == 0: self.timeCurrent = self.getTime()
		except:
			# When Kodi's player is not playing anything, it throws an exception when calling self.getTotalTime()
			return

		while True:
			try: self.progressLock.acquire()
			except: pass
			progress = self.progress
			try: self.progressLock.release()
			except: pass
			if progress == None:
				time.sleep(0.5)
			else:
				break

		if progress > 0:
			if self.timeTotal > 0:
				seconds = (progress * self.timeTotal) / 100.0
				if seconds > 0 and tools.Settings.getInteger('general.playback.resume') == 1:
					self.progressBusy = True
					self.pause()
					timeMinutes, timeSeconds = divmod(float(seconds), 60)
					timeHours, timeMinutes = divmod(timeMinutes, 60)
					label = '%02d:%02d:%02d' % (timeHours, timeMinutes, timeSeconds)
					label = (control.lang(32502) % label).encode('utf-8')
					resume = interface.Dialog.option(title = 32344, message = label, labelConfirm = 32501, labelDeny = 32503)
					if resume: seconds = 0

				if seconds > 0:
					self.seekTime(seconds)
				if self.progressBusy:
					self.pause()
					self.progressBusy = False

		self.updateProgress(Playback.ActionStart)

	def libForPlayback(self):
		try:
			if self.idLocal == None: raise Exception()

			if self.typeMovie:
				rpc = '{"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {"movieid" : %s, "playcount" : 1 }, "id": 1 }' % str(self.idLocal)
			elif self.typeTelevision:
				rpc = '{"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid" : %s, "playcount" : 1 }, "id": 1 }' % str(self.idLocal)

			control.jsonrpc(rpc) ; control.refresh()
		except:
			pass

	def onPlayBackStarted(self):
		self.status = self.StatusPlaying
		interface.Loader.hide()
		self.setProgress()

		for i in range(0, 600):
			if self.isPlayback(): break
			tools.Time.sleep(0.1)
		interface.Dialog.closeAll()

		Subtitles().get(name = self.name, imdb = self.idImdb, season = self.seasonString, episode = self.episodeString, source = self.source)

	def onPlayBackPaused(self):
		self.status = self.StatusPaused
		if not self.progressBusy: self.updateProgress(Playback.ActionPause)

	def onPlayBackResumed(self):
		self.status = self.StatusPlaying
		if not self.progressBusy: self.updateProgress(Playback.ActionStart)

	def onPlayBackStopped(self):
		self.status = self.StatusStopped
		self.updateProgress(Playback.ActionStop)
		self._downloadStop()
		self._debridClear()
		self._showStreams()
		if control.window.getProperty('%s.player.overlay' % control.addonInfo('id')) == '7':
			trakt.rateShow(imdb = self.imdb, tvdb = self.tvdb, season = self.season, episode = self.episode)

	def onPlayBackEnded(self):
		self.onPlayBackStopped()
		self.status = self.StatusEnded
		self.libForPlayback()
		self._downloadClear()
		self._debridClear()

class Subtitles:

	def get(self, name, imdb, season, episode, source):

		try:
			mode = tools.Settings.getInteger('subtitles.selection')
			if mode == 0:
				xbmc.Player().showSubtitles(False)
				return False
			elif mode == 1:
				return False
			else:

				langDict = {'Afrikaans': 'afr', 'Albanian': 'alb', 'Arabic': 'ara', 'Armenian': 'arm', 'Basque': 'baq', 'Bengali': 'ben', 'Bosnian': 'bos', 'Breton': 'bre', 'Bulgarian': 'bul', 'Burmese': 'bur', 'Catalan': 'cat', 'Chinese': 'chi', 'Croatian': 'hrv', 'Czech': 'cze', 'Danish': 'dan', 'Dutch': 'dut', 'English': 'eng', 'Esperanto': 'epo', 'Estonian': 'est', 'Finnish': 'fin', 'French': 'fre', 'Galician': 'glg', 'Georgian': 'geo', 'German': 'ger', 'Greek': 'ell', 'Hebrew': 'heb', 'Hindi': 'hin', 'Hungarian': 'hun', 'Icelandic': 'ice', 'Indonesian': 'ind', 'Italian': 'ita', 'Japanese': 'jpn', 'Kazakh': 'kaz', 'Khmer': 'khm', 'Korean': 'kor', 'Latvian': 'lav', 'Lithuanian': 'lit', 'Luxembourgish': 'ltz', 'Macedonian': 'mac', 'Malay': 'may', 'Malayalam': 'mal', 'Manipuri': 'mni', 'Mongolian': 'mon', 'Montenegrin': 'mne', 'Norwegian': 'nor', 'Occitan': 'oci', 'Persian': 'per', 'Polish': 'pol', 'Portuguese': 'por,pob', 'Portuguese(Brazil)': 'pob,por', 'Romanian': 'rum', 'Russian': 'rus', 'Serbian': 'scc', 'Sinhalese': 'sin', 'Slovak': 'slo', 'Slovenian': 'slv', 'Spanish': 'spa', 'Swahili': 'swa', 'Swedish': 'swe', 'Syriac': 'syr', 'Tagalog': 'tgl', 'Tamil': 'tam', 'Telugu': 'tel', 'Thai': 'tha', 'Turkish': 'tur', 'Ukrainian': 'ukr', 'Urdu': 'urd'}

				codePageDict = {'ara': 'cp1256', 'ar': 'cp1256', 'ell': 'cp1253', 'el': 'cp1253', 'heb': 'cp1255', 'he': 'cp1255', 'tur': 'cp1254', 'tr': 'cp1254', 'rus': 'cp1251', 'ru': 'cp1251'}
				quality = ['bluray', 'hdrip', 'brrip', 'bdrip', 'dvdrip', 'webrip', 'hdtv']

				settingsLanguages = tools.Language.settings()

				langs = []

				try:
					lang = tools.Settings.getString('subtitles.language.primary')
					if not tools.Language.customization() or lang.lower() == tools.Language.Automatic:
						if len(settingsLanguages) == 0:
							lang = tools.Language.EnglishName
						else:
							lang = settingsLanguages[0][1]
					if not lang in langDict:
						lang = tools.Language.EnglishName

					try: langs = langDict[lang].split(',')
					except: langs.append(langDict[lang])
				except: pass

				try:
					lang = tools.Settings.getString('subtitles.language.secondary')
					if not tools.Language.customization() or lang.lower() == tools.Language.Automatic:
						if len(settingsLanguages) == 0:
							lang = tools.Language.EnglishName
						elif len(settingsLanguages) == 1:
							lang = settingsLanguages[0][1]
						elif len(settingsLanguages) == 2 and not settingsLanguages[1][1] in langs:
							lang = settingsLanguages[1][1]
						elif len(settingsLanguages) == 3:
							lang = settingsLanguages[2][1]
						else:
							lang = settingsLanguages[0][1]
					if not lang in langDict:
						lang = tools.Language.EnglishName

					try: langs = langs + langDict[lang].split(',')
					except: langs.append(langDict[lang])
				except: pass

				# Always retrieve additional subtitles.
				# Many streams have an integrated subtitle that are empty (eg: only show "Encoded by XYZ" at the start).
				#try: subLang = xbmc.Player().getSubtitles()
				#except: subLang = ''
				#if subLang == langs[0]: return True

				server = xmlrpclib.Server('http://api.opensubtitles.org/xml-rpc', verbose = 0)
				token = server.LogIn('', '', 'en', 'XBMC_Subtitles_v1')
				token = token['token']
				sublanguageid = ','.join(langs)
				imdbid = re.sub('[^0-9]', '', imdb)

				if not (season == None or episode == None):
					result = server.SearchSubtitles(token, [{'sublanguageid': sublanguageid, 'imdbid': imdbid, 'season': season, 'episode': episode}])['data']
					fmt = ['hdtv']
				else:
					result = server.SearchSubtitles(token, [{'sublanguageid': sublanguageid, 'imdbid': imdbid}])['data']
					try: vidPath = xbmc.Player().getPlayingFile()
					except: vidPath = ''
					fmt = re.split('\.|\(|\)|\[|\]|\s|\-', vidPath)
					fmt = [i.lower() for i in fmt]
					fmt = [i for i in fmt if i in quality]

				try: meta = source['metadata']
				except: meta = None
				try: filename = meta.name().lower()
				except: filename = None
				try: release = meta.release(full = False).lower()
				except: release = None
				try: uploader = meta.uploader(full = False).lower()
				except: uploader = None
				try:
					quality = meta.videoQuality().lower()
					if 'hd' in quality: quality = quality.replace('hd', '')
					else: quality = None
				except: quality = None
				try:
					codec = meta.videoCodec().lower()
					if codec.startswith('h2'): codec = codec.replace('h', '')
					else: codec = None
				except: codec = None

				exact = -1
				result = [i for i in result if i['SubSumCD'] == '1']
				subtitleIds = []
				subtitleNames = []
				subtitleLanguages = []
				subtitleLanguageCodes = []

				internal = xbmc.Player().getAvailableSubtitleStreams()
				internalHas = len(internal) > 0
				for i in range(len(internal)):
					subtitleIds.append(internal[i])
					subtitleNames.append(interface.Format.fontItalic(interface.Translation.string(33922)))
					subtitleLanguages.append(internal[i])
					subtitleLanguageCodes.append(internal[i])

				filtersType = ['bluray', 'brrip', 'bdrip', 'web', 'webdl', 'webrip', 'hdrip', 'dvdrip', 'hdtv']
				filtersExact = []
				filters = []

				if uploader and release and codec and quality: filtersExact.append([uploader, release, codec, quality])
				if uploader and release and codec: filtersExact.append([uploader, release, codec])
				if uploader and release and quality: filtersExact.append([uploader, release, quality])

				if uploader and release: filters.append([uploader, release])
				if uploader and codec: filters.append([uploader, codec])
				if uploader and quality: filters.append([uploader, quality])
				if release and codec: filters.append([release, codec])
				if release and quality: filters.append([release, quality])

				if uploader: filters.append([uploader])
				if release: filters.append([release])
				if codec: filters.append([codec])
				if quality: filters.append([quality])
				filters.append([]) # Only manual release type

				temporary = []
				for i in range(len(filtersExact)):
					for j in filtersType:
						f = list(filtersExact[i])
						f.append(j)
						temporary.append(f)
				filtersExact = temporary

				temporary = []
				for i in range(len(filters)):
					for j in filtersType:
						f = list(filters[i])
						f.append(j)
						temporary.append(f)
				filters = temporary

				for lang in langs:

					if filename:
						for i in result:
							try:
								if not i['IDSubtitleFile'] in subtitleIds and not i['MovieReleaseName'] in subtitleNames and i['SubLanguageID'] == lang:
									releasename = i['MovieReleaseName'].lower()

									# Full file name
									if filename == releasename:
										if exact < 0: exact = len(subtitleIds)
										subtitleIds.append(i['IDSubtitleFile'])
										subtitleNames.append(i['MovieReleaseName'])
										subtitleLanguages.append(i['SubLanguageID'])
										subtitleLanguageCodes.append(i['ISO639'])

									# Full file name without extension
									filenameAdpated = filename
									if len(filenameAdpated) > 4 and filenameAdpated[-4] == '.': filenameAdpated = filenameAdpated[:-4]
									releasenameAdpated = releasename
									if len(releasenameAdpated) > 4 and releasenameAdpated[-4] == '.': releasenameAdpated = releasenameAdpated[:-4]
									if filenameAdpated == releasenameAdpated:
										if exact < 0: exact = len(subtitleIds)
										subtitleIds.append(i['IDSubtitleFile'])
										subtitleNames.append(i['MovieReleaseName'])
										subtitleLanguages.append(i['SubLanguageID'])
										subtitleLanguageCodes.append(i['ISO639'])

									# File name with only alphanumeric characters.
									filenameAdpated = re.sub('[^0-9a-zA-Z]+', '', filenameAdpated)
									releasenameAdpated = re.sub('[^0-9a-zA-Z]+', '', releasenameAdpated)
									if filenameAdpated == releasenameAdpated:
										if exact < 0: exact = len(subtitleIds)
										subtitleIds.append(i['IDSubtitleFile'])
										subtitleNames.append(i['MovieReleaseName'])
										subtitleLanguages.append(i['SubLanguageID'])
										subtitleLanguageCodes.append(i['ISO639'])
							except: pass

					# Only check after all full file names were tested

					for filter in filtersExact:
						for i in result:
							try:
								if not i['IDSubtitleFile'] in subtitleIds and not i['MovieReleaseName'] in subtitleNames and i['SubLanguageID'] == lang:
									releasename = i['MovieReleaseName'].lower()
									if all(x in releasename for x in filter):
										if exact < 0: exact = len(subtitleIds)
										subtitleIds.append(i['IDSubtitleFile'])
										subtitleNames.append(i['MovieReleaseName'])
										subtitleLanguages.append(i['SubLanguageID'])
										subtitleLanguageCodes.append(i['ISO639'])
							except: pass

					for filter in filters:
						for i in result:
							try:
								if not i['IDSubtitleFile'] in subtitleIds and not i['MovieReleaseName'] in subtitleNames and i['SubLanguageID'] == lang:
									releasename = i['MovieReleaseName'].lower()
									if all(x in releasename for x in filter):
										subtitleIds.append(i['IDSubtitleFile'])
										subtitleNames.append(i['MovieReleaseName'])
										subtitleLanguages.append(i['SubLanguageID'])
										subtitleLanguageCodes.append(i['ISO639'])
							except: pass

				# Pick the best one.
				filter = []
				for lang in langs:
					filter += [i for i in result if i['SubLanguageID'] == lang and any(x in i['MovieReleaseName'].lower() for x in fmt)]
					if quality: filter += [i for i in result if i['SubLanguageID'] == lang and any(x in i['MovieReleaseName'].lower() for x in quality)]
					filter += [i for i in result if i['SubLanguageID'] == lang]
				for f in filter:
					if not f['IDSubtitleFile'] in subtitleIds and not f['MovieReleaseName'] in subtitleNames:
						subtitleIds.append(f['IDSubtitleFile'])
						subtitleNames.append(f['MovieReleaseName'])
						subtitleLanguages.append(f['SubLanguageID'])
						subtitleLanguageCodes.append(f['ISO639'])
				filter = []

				choice = -1
				selection = tools.Settings.getInteger('subtitles.general.selection')
				notifications = tools.Settings.getBoolean('subtitles.general.notifications')

				if len(subtitleIds) == 0:
					if notifications:
						interface.Dialog.notification(title = 35145, message = 35146, icon = interface.Dialog.IconInformation)
					return False

				subtitleLabels = []
				for i in range(len(subtitleIds)):
					language = tools.Language.name(subtitleLanguageCodes[i])
					if language == None: language = interface.Translation.string(35040)
					name = subtitleNames[i]
					if name == None: name = interface.Translation.string(33387)
					subtitleLabels.append(interface.Format.bold(language + ': ') + name)

				if selection == 0:
					choice = interface.Dialog.select(title = 32353, items = subtitleLabels)
				elif selection == 1:
					choice = 0
				elif selection == 2:
					if len(subtitleIds) == 1:
						choice = 0
					else:
						choice = interface.Dialog.option(title = 32353, message = 35144, labelConfirm = 33110, labelDeny = 33800)
						if choice: choice = interface.Dialog.select(title = 32353, items = subtitleLabels)
						else: choice = 0
				elif selection == 3:
					if exact < 0: choice = interface.Dialog.select(title = 32353, items = subtitleLabels)
					else: choice = exact

				if choice < 0:
					xbmc.Player().disableSubtitles()
					return False

				# Internal subtitles
				if internalHas and isinstance(subtitleIds[choice], (int, long)):
					xbmc.Player().setSubtitles(str(subtitleIds[choice]))
				else:
					try: lang = xbmc.convertLanguage(subtitleLanguages[choice], xbmc.ISO_639_1)
					except: lang = subtitleLanguages[choice]

					content = [subtitleIds[choice],]
					content = server.DownloadSubtitles(token, content)
					content = base64.b64decode(content['data'][0]['data'])
					content = str(zlib.decompressobj(16+zlib.MAX_WBITS).decompress(content))

					subtitle = tools.System.temporary(directory = 'subtitles', file = '%s.%s.srt' % (name, lang)) # Keep the file name with language between dots, because Kodi uses this format to detect the language if the SRT.

					codepage = codePageDict.get(lang, '')
					if codepage and tools.Settings.getBoolean('subtitles.general.foreign'):
						try:
							content_encoded = codecs.decode(content, codepage)
							content = codecs.encode(content_encoded, 'utf-8')
						except:
							pass

					file = control.openFile(subtitle, 'w')
					file.write(str(content))
					file.close()

					xbmc.sleep(1000)
					xbmc.Player().setSubtitles(subtitle)

				if notifications:
					interface.Dialog.notification(title = 35140, message = subtitleNames[choice], icon = interface.Dialog.IconSuccess)

				return True
		except:
			tools.Logger.error()
			return False


class Playback(object):

	# Used by Trakt scrobble
	ActionStart = 'start'
	ActionPause = 'pause'
	ActionStop = 'stop'

	def __init__(self):
		self.progress = 0

	def _trakt(self):
		if trakt.getTraktCredentialsInfo() == False:
			return False
		else:
			return tools.Settings.getInteger('general.playback.progress.alternative') == 1

	def _id(self, imdb = None, tvdb = None, season = None, episode = None):
		imdbValid = not imdb == None and not imdb == '' and not imdb == '0'
		tvdbValid = not tvdb == None and not tvdb == '' and not tvdb == '0'
		id = hashlib.md5()
		if imdbValid:
			imdb = str(imdb)
			for i in imdb: id.update(str(i))
		if not imdbValid and tvdbValid:
			tvdb = str(tvdb)
			for i in tvdb: id.update(str(i))
		if season:
			season =  '_' + str(season)
			for i in season: id.update(str(i))
		if episode:
			episode = '_' + str(episode)
			for i in episode: id.update(str(i))
		return str(id.hexdigest())

	def getProgress(self, type, imdb = None, tvdb = None, season = None, episode = None, wait = True):
		thread = threading.Thread(target = self._getProgress, args = (type, imdb, tvdb, season, episode))
		thread.start()
		if wait: thread.join()

		# Ignore progress if it is very small or large.
		if self.progress < 1 or (type == tools.Media.TypeMovie and self.progress > 92) or (type == tools.Media.TypeEpisode and self.progress > 96):
			self.progress = 0

		return self.progress

	def _getProgress(self, type, imdb = None, tvdb = None, season = None, episode = None):
		self.progress = 0
		try:
			if self._trakt():
				self.progress = trakt.scrobbleProgress(type = type, imdb = imdb, tvdb = tvdb, season = season, episode = episode)
			else:
				id = self._id(imdb = imdb, tvdb = tvdb, season = season, episode = episode)
				dbcon = database.connect(control.playbackFile)
				dbcur = dbcon.cursor()
				dbcur.execute("SELECT * FROM playback WHERE id = '%s'" % id)
				match = dbcur.fetchone()
				self.progress = float(match[1])
		except:
			pass

	def setProgress(self, action, type, progress, imdb = None, tvdb = None, season = None, episode = None, wait = False):
		thread = threading.Thread(target = self._setProgress, args = (action, type, progress, imdb, tvdb, season, episode))
		thread.start()
		if wait: thread.join()

	def _setProgress(self, action, type, progress, imdb = None, tvdb = None, season = None, episode = None):
		try:
			if self._trakt():
				trakt.scrobbleUpdate(action = action, type = type, imdb = imdb, tvdb = tvdb, season = season, episode = episode, progress = progress)
			else:
				id = self._id(imdb = imdb, tvdb = tvdb, season = season, episode = episode)
				control.makeFile(control.dataPath)
				dbcon = database.connect(control.playbackFile)
				dbcur = dbcon.cursor()
				dbcur.execute("CREATE TABLE IF NOT EXISTS playback (""id TEXT, ""progress REAL, ""UNIQUE(id)"");")
				dbcur.execute("DELETE FROM playback WHERE id = '%s'" % id)
				dbcur.execute("INSERT INTO playback VALUES (?, ?)", (id, progress))
				dbcon.commit()
		except:
			tools.Logger.error()
