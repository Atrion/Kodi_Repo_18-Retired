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

"""

##############################################################################################################################################################################################################################################
# FOR DEVELOPERS
##############################################################################################################################################################################################################################################

To use the Orion Kodi addon, do the following:
	1. Add Orion as a dependency to your addon.xml:
			<import addon="script.module.orion" version="1.0.0" />
	2. Import the Orion module in your Python script:
			from orion import *
	3. Create a new Orion object with your app API key:
			orion = Orion('my_app_key')
	4. Search for the streams using the instance from the previous step:
			results = orion.streams(type = Orion.TypeMovie, idXYZ = 'Orion, IMDb, TMDb, TVDb, TVRage, or Trakt ID. Alternatively, the Trakt slug can be used.')

A few things to note:
	1. Do not name your file "orion.py" or your class "Orion", because this will clash with Orion's import.
	2. A query requires a "type" and either and ID (idOrion, idImdb, idTmdb, idTvdb, idTvrage, idTrakt, idSlug) or the "query" parameter.
		In addition, if you search for a show, you have to provide the "numberSeason" and "numberEpisode" together with the ID.

##############################################################################################################################################################################################################################################

STREAM RETRIEVE 1 - Retrieve a movie using an IMDb ID.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350')

##############################################################################################################################################################################################################################################

STREAM RETRIEVE 2 - Retrieve an episode using a TVDb ID.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeShow, idTvdb = '73739', numberSeason = 3, numberEpisode = 5)

##############################################################################################################################################################################################################################################

STREAM RETRIEVE 3 - Retrieve a movie using a query string. Using a query is not advised, since the wrong results might be returned.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, query = 'Night of the Living Dead 1968')

##############################################################################################################################################################################################################################################

STREAM RETRIEVE 4 - Retrieve a movie no larger than 2GB and being either a direct hoster, a cached torrent, or a cached usenet link on Premiumize.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', fileSize = [None, 2147483648], access = [Orion.AccessDirect, Orion.AccessPremiumizeTorrent, Orion.AccessPremiumizeUsenet])

##############################################################################################################################################################################################################################################

STREAM RETRIEVE 5 - Retrieve a movie that has a video quality between SD and HD1080, and a DD or DTS audio system.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', videoQuality = [Orion.QualitySd, Orion.QualityHd1080], audioSystem = [Orion.SystemDd, Orion.SystemDts])

##############################################################################################################################################################################################################################################

STREAM RETRIEVE 6 - Retrieve a movie that has a popularity of at least 50% and sorted by file size in descending order.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', popularityPercent = 0.5, sortValue = Orion.SortFileSize, sortOrder = Orion.OrderDescending)

##############################################################################################################################################################################################################################################

STREAM RETRIEVE 7 - Retrieve a movie with a maximum of 100 links and a page offset of 2 (that is link number 101 - 200).

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', limitCount = 100, limitPage = 2)

##############################################################################################################################################################################################################################################

STREAM RETRIEVE 8 - Retrieve a movie but only torrent MAGNET links or hoster HTTPS links.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', protocolTorrent = [Orion.ProtocolMagnet], protocolHoster = [Orion.ProtocolHttps])

##############################################################################################################################################################################################################################################

STREAM VOTE - Vote up working streams and vote down non-working streams.

	from orion import *
	result = Orion('my_app_key').streamVote(idItem = 'id_of_movie_or_episode', idStream = 'orion_stream_id', vote = Orion.VoteUp)

##############################################################################################################################################################################################################################################

STREAM REMOVE - Request the removal of an incorrect or non-working stream.

	from orion import *
	result = Orion('my_app_key').streamRemove(idItem = 'id_of_movie_or_episode', idStream = 'orion_stream_id')

##############################################################################################################################################################################################################################################

CONTAINER RETRIEVE - Retrieve the details for a list of containers, including links and hashes.

	from orion import *
	result = Orion('my_app_key').containers(links = ['source_link_of_torrent_or_usenet_container', 'source_link_of_torrent_or_usenet_container'])

##############################################################################################################################################################################################################################################

CONTAINER IDENTIFIERS - Retrieve the hashes and segment message IDs for a list of containers.

	from orion import *
	result = Orion('my_app_key').containerIdentifiers(links = ['source_link_of_torrent_or_usenet_container'])

##############################################################################################################################################################################################################################################

CONTAINER HASHES - Retrieve the hashes for a list of containers.

	from orion import *
	result = Orion('my_app_key').containerHashes(links = ['source_link_of_torrent_or_usenet_container', 'source_link_of_torrent_or_usenet_container'])

##############################################################################################################################################################################################################################################

CONTAINER SEGMENTS - Retrieve the segment message IDs for a list of containers.

	from orion import *
	result = Orion('my_app_key').containerSegments(links = ['source_link_of_torrent_or_usenet_container'])

##############################################################################################################################################################################################################################################

CONTAINER DOWNLOAD 1 - Download a container to memory.

	from orion import *
	data = Orion('my_app_key').containerDownload(id = 'container_id_or_sha1_or_link')

##############################################################################################################################################################################################################################################

CONTAINER DOWNLOAD 2 - Download a container to file.

	from orion import *
	result = Orion('my_app_key').containerDownload(id = 'container_id_or_sha1_or_link', path = '/tmp/xyz.torrent')

##############################################################################################################################################################################################################################################

LINK - Retrieve Orion's website URL.

	from orion import *
	result = Orion('my_app_key').link()

##############################################################################################################################################################################################################################################

APP DETAILS - Retrieve your app details and status.

	from orion import *
	result = Orion('my_app_key').app()

##############################################################################################################################################################################################################################################

APP VALID - Check if your app key and status is valid.

	from orion import *
	result = Orion('my_app_key').appValid()

##############################################################################################################################################################################################################################################

APP DIALOG - Show a Kodi dialog with your app details.

	from orion import *
	result = Orion('my_app_key').appDialog()

##############################################################################################################################################################################################################################################

USER DETAILS - Retrieve your user details and status.

	from orion import *
	result = Orion('my_app_key').user()

##############################################################################################################################################################################################################################################

USER VALID - Check if the user key and status is valid.

	from orion import *
	result = Orion('my_app_key').userValid()

##############################################################################################################################################################################################################################################

USER FREE - Check if the user has a free account.

	from orion import *
	result = Orion('my_app_key').userFree()

##############################################################################################################################################################################################################################################

USER PREMIUM - Check if the user has a premium account.

	from orion import *
	result = Orion('my_app_key').userPremium()

##############################################################################################################################################################################################################################################

USER DIALOG - Show a Kodi dialog with the user details.

	from orion import *
	result = Orion('my_app_key').userDialog()

##############################################################################################################################################################################################################################################

SERVER STATS - Retrieve the Orion server stats.

	from orion import *
	result = Orion('my_app_key').serverStats()

##############################################################################################################################################################################################################################################

SERVER DIALOG - Show a Kodi dialog with the Orion server stats.

	from orion import *
	result = Orion('my_app_key').serverDialog()

##############################################################################################################################################################################################################################################

SERVER TEST - Test if the Orion server is up and running.

	from orion import *
	result = Orion('my_app_key').serverTest()

##############################################################################################################################################################################################################################################

"""

from orion.modules.orionapi import *
from orion.modules.orionapp import *
from orion.modules.orionuser import *
from orion.modules.orionstats import *
from orion.modules.oriontools import *
from orion.modules.orionitem import *
from orion.modules.oriondatabase import *
from orion.modules.orioncontainer import *
from orion.modules.orionsettings import *
from orion.modules.orionnavigator import *

class Orion:

	##############################################################################
	# CONSTANTS
	##############################################################################

	Id = 'script.module.orion'
	Name = 'Orion'

	# Encoding
	EncodingJson = 'json'											# JSON String (encoded JSON)
	EncodingStruct = 'struct'										# Python dictionary/map (decoded JSON)
	EncodingObject = 'object'										# Orion classes (object oriented)
	EncodingDefault = EncodingStruct

	# Filter Type
	FilterNone = OrionItem.FilterNone 								# Do not use any filter at all
	FilterSettings = OrionItem.FilterSettings						# Use the filters set by the user in the Orion addon settings

	# Choice Type
	ChoiceInclude = OrionItem.ChoiceInclude
	ChoiceExclude = OrionItem.ChoiceExclude
	ChoiceRequire = OrionItem.ChoiceRequire

	# Item Type
	TypeMovie = OrionItem.TypeMovie									# 'movie'				(Movie streams)
	TypeShow = OrionItem.TypeShow									# 'show'				(Epsiode streams)

	# Stream Protocols
	ProtocolMagnet = OrionItem.ProtocolMagnet						# 'magnet'				(Torrent magnet links)
	ProtocolHttp = OrionItem.ProtocolHttp							# 'http'				(Torrent, usenet, and hoster HTTP links)
	ProtocolHttps = OrionItem.ProtocolHttps							# 'https'				(Torrent, usenet, and hoster HTTPS links)
	ProtocolFtp = OrionItem.ProtocolFtp								# 'ftp'					(Torrent, usenet, and hoster FTP links)
	ProtocolFtps = OrionItem.ProtocolFtps							# 'ftps'				(Torrent, usenet, and hoster FTPS links)

	# Access Status
	AccessDirect = OrionItem.AccessDirect							# 'direct'				(Direct hoster link)
	AccessIndirect = OrionItem.AccessIndirect						# 'indirect'			(Indirect hoster link)
	AccessPremiumize = OrionItem.AccessPremiumize					# 'premiumize'			(Cached any on Premiumize)
	AccessPremiumizeTorrent = OrionItem.AccessPremiumizeTorrent		# 'premiumizetorrent'	(Cached torrent on Premiumize)
	AccessPremiumizeUsenet = OrionItem.AccessPremiumizeUsenet		# 'premiumizeusenet'	(Cached usenet on Premiumize)
	AccessPremiumizeHoster = OrionItem.AccessPremiumizeHoster		# 'premiumizehoster'	(Cached hoster on Premiumize)
	AccessOffcloud = OrionItem.AccessOffcloud						# 'offcloud'			(Cached any on OffCloud)
	AccessOffcloudTorrent = OrionItem.AccessOffcloudTorrent			# 'offcloudtorrent'		(Cached torrent on OffCloud)
	AccessOffcloudUsenet = OrionItem.AccessOffcloudUsenet			# 'offcloudusenet'		(Cached usenet on OffCloud)
	AccessOffcloudHoster = OrionItem.AccessOffcloudHoster			# 'offcloudhoster'		(Cached hoster on OffCloud)
	AccessRealdebrid = OrionItem.AccessRealdebrid					# 'realdebrid'			(Cached any on RealDebrid)
	AccessRealdebridTorrent = OrionItem.AccessRealdebridTorrent		# 'realdebridtorrent'	(Cached torrent on RealDebrid)
	AccessRealdebridUsenet = OrionItem.AccessRealdebridUsenet		# 'realdebridusenet'	(Cached usenet on RealDebrid)
	AccessRealdebridHoster = OrionItem.AccessRealdebridHoster		# 'realdebridhoster'	(Cached hoster on RealDebrid)

	# Cache Lookup
	LookupPremiumize = OrionItem.LookupPremiumize					# 'premiumize'			(Cache lookup on Premiumize)
	LookupOffcloud = OrionItem.LookupOffcloud						# 'offcloud'			(Cache lookup on OffCloud)
	LookupRealdebrid = OrionItem.LookupRealdebrid					# 'realdebrid'			(Cache lookup on RealDebrid)

	# Stream Type
	StreamTorrent = OrionStream.TypeTorrent							# 'torrent'				(Torrent magnet or link)
	StreamUsenet = OrionStream.TypeUsenet							# 'usenet'				(Usenet NZB link)
	StreamHoster = OrionStream.TypeHoster							# 'hoster'				(File hoster link)

	# Video Quality
	QualityHd8k = OrionStream.QualityHd8k							# 'hd8k'				(High Definition 8k)
	QualityHd6k = OrionStream.QualityHd6k							# 'hd6k'				(High Definition 6k)
	QualityHd4k = OrionStream.QualityHd4k							# 'hd4k'				(High Definition 4k)
	QualityHd2k = OrionStream.QualityHd2k							# 'hd2k'				(High Definition 2k)
	QualityHd1080 = OrionStream.QualityHd1080						# 'hd1080'				(High Definition 1080p)
	QualityHd720 = OrionStream.QualityHd720							# 'hd720'				(High Definition 720p)
	QualitySd = OrionStream.QualitySd								# 'sd'					(Standard Definition 240p, 360, 480p)
	QualityScr1080 = OrionStream.QualityScr1080						# 'scr1080'				(Screener 1080p)
	QualityScr720 = OrionStream.QualityScr720						# 'scr720'				(Screener 720p)
	QualityScr = OrionStream.QualityScr								# 'scr'					(Screener)
	QualityCam1080 = OrionStream.QualityCam1080						# 'cam1080'				(Camera Recording 1080p)
	QualityCam720 = OrionStream.QualityCam720						# 'cam720'				(Camera Recording 720p)
	QualityCam = OrionStream.QualityCam								# 'cam'					(Camera Recording)

	# Video Codec
	CodecH266 = OrionStream.CodecH266								# 'h266'				(Moving Picture Experts Group Future Video Codec)
	CodecH265 = OrionStream.CodecH265								# 'h265'				(Moving Picture Experts Group High Efficiency Video Coding)
	CodecH264 = OrionStream.CodecH264								# 'h264'				(Moving Picture Experts Group Advanced Video Coding)
	CodecH262 = OrionStream.CodecH262								# 'h262'				(Moving Picture Experts Group Part 2)
	CodecH222 = OrionStream.CodecH222								# 'h222'				(Moving Picture Experts Group Part 1)
	CodecAv1 = OrionStream.CodecAv1									# 'av1'					(AOMedia Video 1)
	CodecVp10 = OrionStream.CodecVp10								# 'vp10'				(Google VP10)
	CodecVp9 = OrionStream.CodecVp9									# 'vp9'					(Google VP9)
	CodecVp8 = OrionStream.CodecVp8									# 'vp8'					(Google VP8)
	Codec3gp = OrionStream.Codec3gp									# '3gp'					(Third Generation Partnership Project)
	CodecAvi = OrionStream.CodecAvi									# 'avi'					(Audio Video Interleave)
	CodecDivx = OrionStream.CodecDivx								# 'divx'				(DivX Video)
	CodecFlv = OrionStream.CodecFlv									# 'flv'					(Flash Video)
	CodecMov = OrionStream.CodecMov									# 'mov'					(QuickTime File Format)
	CodecMpeg = OrionStream.CodecMpeg								# 'mpeg'				(Moving Picture Experts Group)
	CodecWmv = OrionStream.CodecWmv									# 'wmv'					(Windows Media Video)
	CodecXvid = OrionStream.CodecXvid								# 'xvid'				(XviD)
	CodecMkv = OrionStream.CodecMkv									# 'mkv'					(Matroska Multimedia Container)
	CodecWebm = OrionStream.CodecWebm								# 'webm'				(Web Multimedia Container)

	# Release Type
	ReleaseBdrip = OrionStream.ReleaseBdrip							# 'bdrip'				(BluRay Rip)
	ReleaseBdscr = OrionStream.ReleaseBdscr							# 'bdscr'				(BluRay Screener)
	ReleaseBdrmx = OrionStream.ReleaseBdrmx							# 'bdrmx'				(BluRay Remux)
	ReleaseBluray = OrionStream.ReleaseBluray						# 'bluray'				(BluRay)
	ReleaseCam = OrionStream.ReleaseCam								# 'cam'					(Camera)
	ReleaseDdc = OrionStream.ReleaseDdc								# 'ddc'					(Direct Digital Content)
	ReleaseDvd = OrionStream.ReleaseDvd								# 'dvd'					(DVD)
	ReleaseDvdrip = OrionStream.ReleaseDvdrip						# 'dvdrip'				(DVD Rip)
	ReleaseDvdscr = OrionStream.ReleaseDvdscr						# 'dvdscr'				(DVD Screener)
	ReleaseDvdrmx = OrionStream.ReleaseDvdrmx						# 'dvdrmx'				(DVD Remux)
	ReleaseHdrip = OrionStream.ReleaseHdrip							# 'hdrip'				(HD Rip)
	ReleaseHdts = OrionStream.ReleaseHdts							# 'hdts'				(HD Telesync)
	ReleaseHdtv = OrionStream.ReleaseHdtv							# 'hdtv'				(HD Television)
	ReleasePdvd = OrionStream.ReleasePdvd							# 'pdvd'				(PDVD)
	ReleasePpv = OrionStream.ReleasePpv								# 'ppv'					(Pay Per View)
	ReleaseR5 = OrionStream.ReleaseR5								# 'r5'					(Region 5)
	ReleaseScr = OrionStream.ReleaseScr								# 'scr'					(Screener)
	ReleaseTk = OrionStream.ReleaseTk								# 'tk'					(Telecine)
	ReleaseTs = OrionStream.ReleaseTs								# 'ts'					(Telesync)
	ReleaseTvrip = OrionStream.ReleaseTvrip							# 'tvrip'				(Television Rip)
	ReleaseVcd = OrionStream.ReleaseVcd								# 'vcd'					(Virtual CD)
	ReleaseVhs = OrionStream.ReleaseVhs								# 'vhs'					(VHS)
	ReleaseVhsrip = OrionStream.ReleaseVhsrip						# 'vhsrip'				(VHS Rip)
	ReleaseDcprip = OrionStream.ReleaseDcprip						# 'dcprip'				(Digital Cinema Package Rip)
	ReleaseWebcap = OrionStream.ReleaseWebcap						# 'webcap'				(Web Capture)
	ReleaseWebdl = OrionStream.ReleaseWebdl							# 'webdl'				(Web Download)
	ReleaseWebrip = OrionStream.ReleaseWebrip						# 'webrip'				(Web Rip)
	ReleaseWp = OrionStream.ReleaseWp								# 'wp'					(Workprint)

	# Edition Type
	EditionNone = OrionStream.EditionNone							# None					(Normal cinema version)
	EditionExtended = OrionStream.EditionExtended					# 'extended'			(Extended editions)
	EditionCollector = OrionStream.EditionCollector					# 'collector'			(Collector editions)
	EditionDirector = OrionStream.EditionDirector					# 'director'			(Director cuts)
	EditionCommentary = OrionStream.EditionCommentary				# 'commentary'			(Commentary voiceovers)
	EditionMaking = OrionStream.EditionMaking						# 'making'				(Making of editions)
	EditionSpecial = OrionStream.EditionSpecial						# 'special'				(Special editions)

	# Audio Type
	AudioStandard = OrionStream.AudioStandard						# 'standard'			(Standard non-dubbed audio)
	AudioDubbed = OrionStream.AudioDubbed							# 'dubbed'				(Dubbed or voiced-over audio)

	# Audio System
	SystemDd = OrionStream.SystemDd									# 'dd'					(Dolby Digital)
	SystemDts = OrionStream.SystemDts								# 'dts'					(Digital Theater Systems)
	SystemDig = OrionStream.SystemDig								# 'dig'					(DigiRise)
	SystemMpeg = OrionStream.SystemMpeg								# 'mpeg'				(Moving Picture Experts Group)
	SystemXiph = OrionStream.SystemXiph								# 'xiph'				(Xiph Foundation)
	SystemWin = OrionStream.SystemWin								# 'win'					(Windows)
	SystemApp = OrionStream.SystemApp								# 'app'					(Apple)

	# Audio Codec
	CodecAmsthd = OrionStream.CodecAmsthd							# 'amsthd'				(Atmos TrueHD)
	CodecAmspls = OrionStream.CodecAmspls							# 'amspls'				(Atmos Plus)
	CodecAms = OrionStream.CodecAms									# 'ams'					(Atmos)
	CodecThd = OrionStream.CodecThd									# 'thd'					(TrueHD)
	CodecPls = OrionStream.CodecPls									# 'pls'					(Plus)
	CodecLve = OrionStream.CodecLve									# 'lve'					(Live)
	CodecSex = OrionStream.CodecSex									# 'sex'					(Surround EX)
	CodecEx = OrionStream.CodecEx									# 'ex'					(EX)
	CodecAc3 = OrionStream.CodecAc3									# 'ac3'					(Audio Codec 3)
	CodecAc4 = OrionStream.CodecAc4									# 'ac4'					(Audio Codec 4)
	Codec70 = OrionStream.Codec70									# '70'					(70MM)
	Codec9624 = OrionStream.Codec9624								# '9624'				(96/24)
	CodecEs = OrionStream.CodecEs									# 'es'					(Extended Surround)
	CodecNeo6 = OrionStream.CodecNeo6								# 'neo6'				(Neo:6)
	CodecNeox = OrionStream.CodecNeox								# 'neox'				(Neo:X)
	CodecNeopc = OrionStream.CodecNeopc								# 'neopc'				(Neo:PC)
	CodecNeo = OrionStream.CodecNeo									# 'neo'					(Neo)
	CodecHdhra = OrionStream.CodecHdhra								# 'hdhra'				(High Definition High Resolution Audio)
	CodecHdma = OrionStream.CodecHdma								# 'hdma'				(High Definition Master Audio)
	CodecHd = OrionStream.CodecHd									# 'hd'					(High Definition)
	CodecNx = OrionStream.CodecNx									# 'nx'					(Neural:X)
	CodecHx = OrionStream.CodecHx									# 'hx'					(Headphone:X)
	CodecSs = OrionStream.CodecSs									# 'ss'					(Surround Sensation)
	CodecCon = OrionStream.CodecCon									# 'con'					(Connect)
	CodecIna = OrionStream.CodecIna									# 'ina'					(Interactive)
	CodecPyf = OrionStream.CodecPyf									# 'pyf'					(PlayFi)
	CodecX = OrionStream.CodecX										# 'x'					(X)
	CodecDra = OrionStream.CodecDra									# 'dra'					(Dynamic Resolution Adaptation)
	CodecAac = OrionStream.CodecAac									# 'aac'					(Advanced Audio Coding)
	CodecMp3 = OrionStream.CodecMp3									# 'mp3'					(Moving Picture Experts Group Audio Layer III)
	CodecMp2 = OrionStream.CodecMp2									# 'mp2'					(Moving Picture Experts Group Audio Layer II)
	CodecFlac = OrionStream.CodecFlac								# 'flac'				(Free Lossless Audio Codec)
	CodecOgg = OrionStream.CodecOgg									# 'ogg'					(Ogg)
	CodecWma = OrionStream.CodecWma									# 'wma'					(Windows Media Audio)
	CodecAlac = OrionStream.CodecAlac								# 'alac'				(Apple Lossless Audio Codec)
	CodecPcm = OrionStream.CodecPcm									# 'pcm'					(Pulse Code Modulation)

	# Audio Channels
	Channels1 = OrionStream.Channels1								# 1						(Mono)
	Channels2 = OrionStream.Channels2								# 2						(Stereo)
	Channels6 = OrionStream.Channels6								# 6						(5.1 Surround Sound)
	Channels8 = OrionStream.Channels8								# 8						(7.1 Surround Sound)

	# Subtitle Type
	SubtitleNone = OrionStream.SubtitleNone							# None					(No subtitles)
	SubtitleSoft = OrionStream.SubtitleSoft							# 'soft'				(Soft-coded subtitles that can be disabled)
	SubtitleHard = OrionStream.SubtitleHard							# 'hard'				(Hard-coded subtitles that cannot be disabled)

	# Sorting Value
	SortNone = OrionItem.SortNone									# 'none'				(No sorting)
	SortBest = OrionItem.SortBest									# 'best'				(Sort by best selection)
	SortShuffle = OrionItem.SortShuffle								# 'shuffle'				(Randomly shuffle results)
	SortShuffle = OrionItem.SortShuffle								# 'shuffle'				(Randomly shuffle results)
	SortPopularity = OrionItem.SortPopularity						# 'popularity'			(Sort by popularity)
	SortTimeAdded = OrionItem.SortTimeAdded							# 'timeadded'			(Sort by time first added)
	SortTimeUpdated = OrionItem.SortTimeUpdated						# 'timeupdated'			(Sort by time last updated)
	SortVideoQuality = OrionItem.SortVideoQuality					# 'videoquality'		(Sort by video quality)
	SortAudioChannels = OrionItem.SortAudioChannels					# 'audiochannels'		(Sort by audio channel count)
	SortFileSize = OrionItem.SortFileSize							# 'filesize'			(Sort by file size)
	SortStreamSeeds = OrionItem.SortStreamSeeds						# 'streamseeds'			(Sort by torrent seed count)
	SortStreamAge = OrionItem.SortStreamAge							# 'streamage'			(Sort by usenet age)

	# Sorting Order
	OrderAscending = OrionItem.OrderAscending						# 'ascending'			(Order by low to high)
	OrderDescending = OrionItem.OrderDescending						# 'descending'			(Order from high to low)

	# Vote
	VoteUp = OrionItem.VoteUp										# 'up'					(Vote the stream up)
	VoteDown = OrionItem.VoteDown									# 'down'				(Vote the stream down)

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, key, encoding = EncodingDefault, silent = False):
		self.mApp = OrionApp.instance(key)
		OrionSettings.silentSet(silent)
		self.mApp.refresh() # Must be done here instead of the instance function, otherwise there is recursion with the API.
		self.mEncoding = encoding

	def __del__(self):
		pass

	##############################################################################
	# ENCODING
	##############################################################################

	def _encode(self, object, encoding = None, dictionary = False):
		if encoding == None: encoding = self.mEncoding
		if object == None:
			return '' if encoding == Orion.EncodingJson else None
		elif encoding == Orion.EncodingJson:
			if OrionTools.isArray(object):
				if dictionary: return OrionTools.jsonTo({key : value for item in object for key, value in item.data().items()})
				else: return [OrionTools.jsonTo(i.data()) for i in object]
			else:
				try: return OrionTools.jsonTo(object.data())
				except: return OrionTools.jsonTo(object)
		elif encoding == Orion.EncodingStruct:
			if OrionTools.isArray(object):
				result = [i.data() for i in object]
				if dictionary: return {key : value for item in result for key, value in item.items()}
				else: return result
			else:
				try: return object.data()
				except: return object
		else:
			return object

	##############################################################################
	# LINK
	##############################################################################

	# Retrieve the link to Orion's website.
	def link(self):
		return OrionTools.link()

	##############################################################################
	# SETTINGS
	##############################################################################

	# Retrieve the scraping timeout from the user settings.
	def settingsScrapingTimeout(self):
		return OrionSettings.getGeneralScrapingTimeout()

	# Retrieve the scraping mode from the user settings.
	def settingsScrapingMode(self):
		return OrionSettings.getGeneralScrapingMode()

	# Retrieve the minimum scraping count from the user settings.
	def settingsScrapingCount(self):
		return OrionSettings.getGeneralScrapingCount()

	# Retrieve the minimum scraping video quality from the user settings.
	def settingsScrapingQuality(self):
		return OrionSettings.getGeneralScrapingQuality()

	##############################################################################
	# APP
	##############################################################################

	# Retrieve the app details.
	def app(self, encoding = None):
		return self._encode(self.mApp, encoding = encoding)

	# Check if the app authentication credentials are valid.
	def appValid(self):
		return self.mApp.valid()

	# Show a dialog with the app details.
	def appDialog(self):
		return OrionNavigator.dialogApp()

	##############################################################################
	# USER
	##############################################################################

	# Retrieve the user details.
	def user(self, encoding = None):
		return self._encode(OrionUser.instance(), encoding = encoding)

	# Check if the user has entered authentication credentials.
	def userEnabled(self):
		return OrionUser.instance().enabled()

	# Check if the user authentication credentials are valid.
	def userValid(self):
		return OrionUser.instance().valid()

	# Check if the user has a free account.
	def userFree(self):
		return OrionUser.instance().subscriptionPackageFree()

	# Check if the user has a premium account.
	def userPremium(self):
		return OrionUser.instance().subscriptionPackagePremium()

	# Show a dialog with the user details.
	def userDialog(self):
		return OrionNavigator.dialogUser()

	# Update the user account with the given API key, or update the user account by showing an API key input dialog.
	def userUpdate(self, key = None, input = False, loader = False):
		if input:
			key = OrionNavigator.settingsAccountKey()
		if key:
			user = OrionUser.instance()
			if not key == None: user.settingsKeySet(key)
			return OrionNavigator.settingsAccountRefresh(launch = False, loader = True, notification = True)
		else:
			return False

	##############################################################################
	# SERVER
	##############################################################################

	# Retrieve the server statistics.
	def serverStats(self, encoding = None):
		stats = OrionStats.instance()
		stats.update()
		return self._encode(stats, encoding = encoding)

	# Show a dialog with the server details.
	def serverDialog(self):
		return OrionNavigator.dialogServer()

	# Test if the server is up and running.
	def serverTest(self):
		return OrionApi().serverTest()

	##############################################################################
	# STREAMS
	##############################################################################

	# Retrieve a list of streams with links and metadata, according to the given filters.
	def streams(self,

				type,

				query = None,

				idOrion = None,
				idImdb = None,
				idTmdb = None,
				idTvdb = None,
				idTvrage = None,
				idTrakt = None,
				idSlug = None,

				numberSeason = None,
				numberEpisode = None,

				limitCount = FilterSettings,
				limitRetry = FilterSettings,
				limitOffset = FilterSettings,
				limitPage = FilterSettings,

				timeAdded = FilterSettings,
				timeAddedAge = FilterSettings,
				timeUpdated = FilterSettings,
				timeUpdatedAge = FilterSettings,

				sortValue = FilterSettings,
				sortOrder = FilterSettings,

				popularityPercent = FilterSettings,
				popularityCount = FilterSettings,

				streamType = FilterSettings,
				streamOrigin = FilterSettings,
				streamSource = FilterSettings,
				streamHoster = FilterSettings,
				streamSeeds = FilterSettings,
				streamAge = FilterSettings,

				protocolTorrent = FilterSettings,
				protocolUsenet = FilterSettings,
				protocolHoster = FilterSettings,

				access = FilterSettings,
				lookup = FilterSettings,

				filePack = FilterSettings,
				fileName = FilterSettings,
				fileSize = FilterSettings, # Can be a single value holding the maximum size (eg: 1073741824), or a tuple/list with the minimum and maximum sizes (eg: [536870912,1073741824]). If either value is None, there is no upper/lower bound (eg: [536870912,None])
				fileUnknown = FilterSettings,

				metaRelease = FilterSettings,
				metaUploader = FilterSettings,
				metaEdition = FilterSettings,

				videoQuality = FilterSettings,
				videoCodec = FilterSettings,
				video3D = FilterSettings,

				audioType = FilterSettings,
				audioChannels = FilterSettings,
				audioSystem = FilterSettings,
				audioCodec = FilterSettings,
				audioLanguages = FilterSettings,

				subtitleType = FilterSettings,
				subtitleLanguages = FilterSettings,

				item = None,

				details = False,
				encoding = None
		):
		result = OrionItem.retrieve(
			type = type,

			query = query,

			idOrion = idOrion,
			idImdb = idImdb,
			idTmdb = idTmdb,
			idTvdb = idTvdb,
			idTvrage = idTvrage,
			idTrakt = idTrakt,
			idSlug = idSlug,

			numberSeason = numberSeason,
			numberEpisode = numberEpisode,

			limitCount = limitCount,
			limitRetry = limitRetry,
			limitOffset = limitOffset,
			limitPage = limitPage,

			timeAdded = timeAdded,
			timeAddedAge = timeAddedAge,
			timeUpdated = timeUpdated,
			timeUpdatedAge = timeUpdatedAge,

			sortValue = sortValue,
			sortOrder = sortOrder,

			popularityPercent = popularityPercent,
			popularityCount = popularityCount,

			streamType = streamType,
			streamOrigin = streamOrigin,
			streamSource = streamSource,
			streamHoster = streamHoster,
			streamSeeds = streamSeeds,
			streamAge = streamAge,

			protocolTorrent = protocolTorrent,
			protocolUsenet = protocolUsenet,
			protocolHoster = protocolHoster,

			access = access,
			lookup = lookup,

			filePack = filePack,
			fileName = fileName,
			fileSize = fileSize,
			fileUnknown = fileUnknown,

			metaRelease = metaRelease,
			metaUploader = metaUploader,
			metaEdition = metaEdition,

			videoQuality = videoQuality,
			videoCodec = videoCodec,
			video3D = video3D,

			audioType = audioType,
			audioChannels = audioChannels,
			audioSystem = audioSystem,
			audioCodec = audioCodec,
			audioLanguages = audioLanguages,

			subtitleType = subtitleType,
			subtitleLanguages = subtitleLanguages,

			item = item
		)
		if not details: result = result.streams()
		return self._encode(result, encoding = encoding)

	# Retrieve the number of streams adhering to the minimum video quality of the user settings.
	def streamsCount(self, streams, quality = FilterNone):
		if quality == Orion.FilterSettings: quality = self.settingsScrapingQuality()
		return OrionStream.count(streams = streams, quality = quality)

	# Vote a stream up or down to change its popularity.
	def streamVote(self, idItem, idStream, vote = VoteUp, notification = False):
		OrionItem.popularityVote(idItem = idItem, idStream = idStream, vote = vote, notification = notification)

	# Request the removal of a specific item.
	def streamRemove(self, idItem, idStream, notification = False):
		OrionItem.remove(idItem = idItem, idStream = idStream, notification = notification)

	# Retrieve the supported stream types from the user settings.
	def streamTypes(self, supported = None):
		types = []
		app = self.mApp.id()
		setting = OrionSettings.getFiltersInteger('filters.stream.type', app if OrionSettings.getFiltersEnabled(app) else None)
		if setting in (0, 1, 2, 4) and (supported == None or OrionStream.TypeTorrent in supported): types.append(OrionStream.TypeTorrent)
		if setting in (0, 1, 3, 5) and (supported == None or OrionStream.TypeUsenet in supported): types.append(OrionStream.TypeUsenet)
		if setting in (0, 2, 3, 6) and (supported == None or OrionStream.TypeHoster in supported): types.append(OrionStream.TypeHoster)
		return types

	##############################################################################
	# CONTAINER
	##############################################################################

	# Retrieve container details for the given links.
	# The links parameter can be a single link or a list of links.
	def containers(self, links, encoding = None):
		single = OrionTools.isString(links)
		result = OrionContainer.retrieve(links = links)
		if single: result = result[0]
		return self._encode(result, encoding = encoding)

	# Retrieve hashes and segment message IDs for the given links.
	# The links parameter can be a single link or a list of links.
	def containerIdentifiers(self, links, encoding = None):
		single = OrionTools.isString(links)
		result = OrionContainer.identifiers(links = links)
		if single:
			result = result[0]
			return self._encode(result, encoding = encoding)
		else:
			return self._encode(result, encoding = encoding, dictionary = True)

	# Retrieve hashes for the given links.
	# The links parameter can be a single link or a list of links.
	def containerHashes(self, links, encoding = None):
		single = OrionTools.isString(links)
		result = OrionContainer.hashes(links = links)
		if single:
			result = result[0]
			if not encoding == Orion.EncodingObject:
				try: result = result.hash()
				except: pass
			return self._encode(result, encoding = encoding)
		else:
			return self._encode(result, encoding = encoding, dictionary = True)

	# Retrieve segment message IDs for the given links.
	# The links parameter can be a single link or a list of links.
	def containerSegments(self, links, encoding = None):
		single = OrionTools.isString(links)
		result = OrionContainer.segments(links = links)
		if single:
			result = result[0]
			return self._encode(result, encoding = encoding)
		else:
			return self._encode(result, encoding = encoding, dictionary = True)

	# Download the container file.
	# The id can be the container's ID, SHA1 hash, or link.
	# If a path is provided, the container will be download to file, otherwise the container's binary data will be returned.
	@classmethod
	def containerDownload(self, id, path = None):
		return OrionContainer.download(id = id, path = path)
