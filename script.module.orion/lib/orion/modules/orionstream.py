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
# ORIONSTREAM
##############################################################################
# Class for handling streams.
##############################################################################

from orion.modules.oriontools import *

class OrionStream:

	##############################################################################
	# CONSTANTS
	##############################################################################

	TypeTorrent = 'torrent'
	TypeUsenet = 'usenet'
	TypeHoster = 'hoster'

	QualityHd8k = 'hd8k'
	QualityHd6k = 'hd6k'
	QualityHd4k = 'hd4k'
	QualityHd2k = 'hd2k'
	QualityHd1080 = 'hd1080'
	QualityHd720 = 'hd720'
	QualitySd = 'sd'
	QualityScr1080 = 'scr1080'
	QualityScr720 = 'scr720'
	QualityScr = 'scr'
	QualityCam1080 = 'cam1080'
	QualityCam720 = 'cam720'
	QualityCam = 'cam'
	QualityOrder = [QualityCam, QualityCam720, QualityCam1080, QualityScr, QualityScr720, QualityScr1080, QualitySd, QualityHd720, QualityHd1080, QualityHd2k, QualityHd4k, QualityHd6k, QualityHd8k]

	CodecH266 = 'h266'
	CodecH265 = 'h265'
	CodecH264 = 'h264'
	CodecH262 = 'h262'
	CodecH222 = 'h222'
	CodecAv1 = 'av1'
	CodecVp10 = 'vp10'
	CodecVp9 = 'vp9'
	CodecVp8 = 'vp8'
	Codec3gp = '3gp'
	CodecAvi = 'avi'
	CodecDivx = 'divx'
	CodecFlv = 'flv'
	CodecMov = 'mov'
	CodecMpeg = 'mpeg'
	CodecWmv = 'wmv'
	CodecXvid = 'xvid'
	CodecMkv = 'mkv'
	CodecWebm = 'webm'

	ReleaseBdrip = 'bdrip'
	ReleaseBdscr = 'bdscr'
	ReleaseBdrmx = 'bdrmx'
	ReleaseBluray = 'bluray'
	ReleaseCam = 'cam'
	ReleaseDdc = 'ddc'
	ReleaseDvd = 'dvd'
	ReleaseDvdrip = 'dvdrip'
	ReleaseDvdscr = 'dvdscr'
	ReleaseDvdrmx = 'dvdrmx'
	ReleaseHdts = 'hdts'
	ReleaseHdrip = 'hdrip'
	ReleaseHdtv = 'hdtv'
	ReleasePdvd = 'pdvd'
	ReleasePpv = 'ppv'
	ReleaseR5 = 'r5'
	ReleaseScr = 'scr'
	ReleaseTk = 'tk'
	ReleaseTs = 'ts'
	ReleaseTvrip = 'tvrip'
	ReleaseVcd = 'vcd'
	ReleaseVhs = 'vhs'
	ReleaseVhsrip = 'vhsrip'
	ReleaseDcprip = 'dcprip'
	ReleaseWebcap = 'webcap'
	ReleaseWebdl = 'webdl'
	ReleaseWebrip = 'webrip'
	ReleaseWp = 'wp'

	EditionNone = None
	EditionExtended = 'extended'
	EditionCollector = 'collector'
	EditionDirector = 'director'
	EditionCommentary = 'commentary'
	EditionMaking = 'making'
	EditionSpecial = 'special'

	AudioStandard = 'standard'
	AudioDubbed = 'dubbed'

	SystemDd = 'dd'
	SystemDts = 'dts'
	SystemDig = 'dig'
	SystemMpeg = 'mpeg'
	SystemXiph = 'xiph'
	SystemWin = 'win'
	SystemApp = 'app'

	CodecAmsthd = 'amsthd'
	CodecAmspls = 'amspls'
	CodecAms = 'ams'
	CodecThd = 'thd'
	CodecPls = 'pls'
	CodecLve = 'lve'
	CodecSex = 'sex'
	CodecEx = 'ex'
	CodecAc3 = 'ac3'
	CodecAc4 = 'ac4'
	Codec70 = '70'
	Codec9624 = '9624'
	CodecEs = 'es'
	CodecNeo6 = 'neo6'
	CodecNeox = 'neox'
	CodecNeopc = 'neopc'
	CodecNeo = 'neo'
	CodecHdhra = 'hdhra'
	CodecHdma = 'hdma'
	CodecHd = 'hd'
	CodecNx = 'nx'
	CodecHx = 'hx'
	CodecSs = 'ss'
	CodecCon = 'con'
	CodecIna = 'ina'
	CodecPyf = 'pyf'
	CodecX = 'x'
	CodecDra = 'dra'
	CodecAac = 'aac'
	CodecMp3 = 'mp3'
	CodecMp2 = 'mp2'
	CodecFlac = 'flac'
	CodecOgg = 'ogg'
	CodecWma = 'wma'
	CodecAlac = 'alac'
	CodecPcm = 'pcm'

	Channels1 = 1
	Channels2 = 2
	Channels4 = 4
	Channels6 = 6
	Channels8 = 8
	Channels10 = 10
	ChannelsOrder = [Channels1, Channels2, Channels4, Channels6, Channels8, Channels10]

	SubtitleNone = None
	SubtitleSoft = 'soft'
	SubtitleHard = 'hard'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, data = {}):
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
	# POPULARITY
	##############################################################################

	def popularityCount(self, default = None):
		try: return self.mData['popularity']['count']
		except: return default

	def popularityPercent(self, default = None):
		try: return self.mData['popularity']['percent']
		except: return default

	##############################################################################
	# TIME
	##############################################################################

	def timeAdded(self, default = None):
		try: return self.mData['time']['added']
		except: return default

	def timeUpdated(self, default = None):
		try: return self.mData['time']['updated']
		except: return default

	##############################################################################
	# LINKS
	##############################################################################

	def links(self, default = None):
		try: return self.mData['links']
		except: return default

	##############################################################################
	# STREAM
	##############################################################################

	def streamType(self, default = None):
		try: return self.mData['stream']['type']
		except: return default

	def streamOrigin(self, default = None):
		try: return self.mData['stream']['origin']
		except: return default

	def streamSource(self, default = None):
		try: return self.mData['stream']['source']
		except: return default

	def streamHoster(self, default = None):
		try: return self.mData['stream']['hoster']
		except: return default

	def streamSeeds(self, default = None):
		try: return self.mData['stream']['seeds']
		except: return default

	def streamTime(self, default = None):
		try: return self.mData['stream']['time']
		except: return default

	##############################################################################
	# ACCESS
	##############################################################################

	def accessDirect(self, default = None):
		try: return self.mData['access']['direct']
		except: return default

	def accessPremiumize(self, default = None):
		try: return self.mData['access']['premiumize']
		except: return default

	def accessOffcloud(self, default = None):
		try: return self.mData['access']['offcloud']
		except: return default

	def accessRealdebrid(self, default = None):
		try: return self.mData['access']['realdebrid']
		except: return default

	##############################################################################
	# FILE
	##############################################################################

	def fileHash(self, default = None):
		try: return self.mData['file']['hash']
		except: return default

	def fileName(self, default = None):
		try: return self.mData['file']['name']
		except: return default

	def fileSize(self, default = None):
		try: return self.mData['file']['size']
		except: return default

	def filePack(self, default = None):
		try: return self.mData['file']['pack']
		except: return default

	##############################################################################
	# META
	##############################################################################

	def metaRelease(self, default = None):
		try: return self.mData['meta']['release']
		except: return default

	def metaUploader(self, default = None):
		try: return self.mData['meta']['uploader']
		except: return default

	def metaEdition(self, default = None):
		try: return self.mData['meta']['edition']
		except: return default

	##############################################################################
	# VIDEO
	##############################################################################

	def videoRanking(self, default = None):
		try: return self.mData['video']['ranking']
		except: return default

	def videoQuality(self, default = None):
		try: return self.mData['video']['quality']
		except: return default

	def videoCodec(self, default = None):
		try: return self.mData['video']['codec']
		except: return default

	def video3D(self, default = None):
		try: return self.mData['video']['3d']
		except: return default

	##############################################################################
	# AUDIO
	##############################################################################

	def audioType(self, default = None):
		try: return self.mData['audio']['type']
		except: return default

	def audioChannels(self, default = None):
		try: return self.mData['audio']['channels']
		except: return default

	def audioSystem(self, default = None):
		try: return self.mData['audio']['system']
		except: return default

	def audioCodec(self, default = None):
		try: return self.mData['audio']['codec']
		except: return default

	def audioLanguages(self, default = None):
		try: return self.mData['audio']['languages']
		except: return default

	##############################################################################
	# SUBTITLE
	##############################################################################

	def subtitleType(self, default = None):
		try: return self.mData['subtitle']['type']
		except: return default

	def subtitleLanguages(self, default = None):
		try: return self.mData['subtitle']['languages']
		except: return default

	##############################################################################
	# COUNT
	##############################################################################

	@classmethod
	def count(self, streams, quality = None):
		try:
			if quality == None:
				return len(streams)
			else:
				if OrionTools.isString(quality):
					quality = OrionStream.QualityOrder.index(quality)
				count = 0
				for i in streams:
					if OrionTools.isDictionary(i):
						try: qualityStream = i['video']['quality'].lower()
						except: qualityStream = i['quality'].lower()
					else:
						qualityStream = i.videoQuality()
					if OrionStream.QualityOrder.index(qualityStream) >= quality:
						count += 1
				return count
		except:
			return 0
