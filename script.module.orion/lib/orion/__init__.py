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
			results = orion.streams(type = Orion.TypeMovie, idXYZ = 'Orion, IMDb, TMDb, or TVDb ID')

A few things to note:
	1. Do not name your file "orion.py" or your class "Orion", because this will clash with Orion's import.
	2. A query requires a "type" and either and ID (idOrion, idImdb, idTmdb, idTvdb) or the "query" parameter.
		In addition, if you search for a show, you have to provide the "numberSeason" and "numberEpisode" together with the ID.

##############################################################################################################################################################################################################################################

STREAM EXAMPLE 1 - Retrieve a movie using an IMDb ID.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350')

##############################################################################################################################################################################################################################################

STREAM EXAMPLE 2 - Retrieve an episode using a TVDb ID.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeShow, idTvdb = '73739', numberSeason = 3, numberEpisode = 5)

##############################################################################################################################################################################################################################################

STREAM EXAMPLE 3 - Retrieve a movie using a query string. Using a query is not advised, since the wrong results might be returned.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, query = 'Night of the Living Dead 1968')

##############################################################################################################################################################################################################################################

STREAM EXAMPLE 4 - Retrieve a movie no larger than 2GB and being either a direct hoster, a cached torrent, or a cached usenet link on Premiumize.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', fileSize = [None, 2147483648], access = [Orion.AccessDirect, Orion.AccessPremiumizeTorrent, Orion.AccessPremiumizeUsenet])

##############################################################################################################################################################################################################################################

STREAM EXAMPLE 5 - Retrieve a movie that has a video quality between SD and HD1080, and a DD or DTS audio system.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', videoQuality = [Orion.QualitySd, Orion.QualityHd1080], audioSystem = [Orion.SystemDd, Orion.SystemDts])

##############################################################################################################################################################################################################################################

STREAM EXAMPLE 6 - Retrieve a movie that has a popularity of at least 50% and sorted by file size in descending order.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', popularityPercent = 0.5, sortValue = Orion.SortFileSize, sortOrder = Orion.OrderDescending)

##############################################################################################################################################################################################################################################

STREAM EXAMPLE 7 - Retrieve a movie with a maximum of 100 links and a page offset of 2 (that is link number 101 - 200).

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', limitCount = 100, limitPage = 2)

##############################################################################################################################################################################################################################################

STREAM EXAMPLE 8 - Retrieve a movie but only torrent MAGNET links or hoster HTTPS links.

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

	# Item Type
	TypeMovie = OrionItem.TypeMovie									# 'movie'				(Movie streams)
	TypeShow = OrionItem.TypeShow									# 'show'				(Epsiode streams)

	# Stream Protocols
	ProtocolMagnet = OrionItem.ProtocolMagnet						# 'magnet'				(Torrent magnet links)
	ProtocolHttp = OrionItem.ProtocolHttp							# 'http'				(Torrent, usenet, and hoster HTTP links)
	ProtocolHttps = OrionItem.ProtocolHttps							# 'https'				(Torrent, usenet, and hoster HTTPS links)
	ProtocolFtp = OrionItem.ProtocolFtp								# 'ftp'					(Torrent, usenet, and hoster FTP links)
	ProtocolFtps = OrionItem.ProtocolFtps							# 'ftps'				(Torrent, usenet, and hoster FTPS links)

	# Stream Access
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
	Codec3gp = OrionStream.Codec3gp									# '3gp'					(Third Generation Partnership Project)
	CodecAvi = OrionStream.CodecAvi									# 'avi'					(Audio Video Interleave)
	CodecDivx = OrionStream.CodecDivx								# 'divx'				(DivX Video)
	CodecFlv = OrionStream.CodecFlv									# 'flv'					(Flash Video)
	CodecMkv = OrionStream.CodecMkv									# 'mkv'					(Matroska Multimedia Container)
	CodecMov = OrionStream.CodecMov									# 'mov'					(QuickTime File Format)
	CodecMpeg = OrionStream.CodecMpeg								# 'mpeg'				(Moving Picture Experts Group)
	CodecWmv = OrionStream.CodecWmv									# 'wmv'					(Windows Media Video)
	CodecXvid = OrionStream.CodecXvid								# 'xvid'				(XviD)

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
	ReleaseWebcap = OrionStream.ReleaseWebcap						# 'webcap'				(Web Capture)
	ReleaseWebdl = OrionStream.ReleaseWebdl							# 'webdl'				(Web Download)
	ReleaseWebrip = OrionStream.ReleaseWebrip						# 'webrip'				(Web Rip)
	ReleaseWp = OrionStream.ReleaseWp								# 'wp'					(Workprint)

	# Uploader Name
	UploaderPublichd = OrionStream.UploaderPublichd					# 'publichd'			(PublicHD)
	UploaderEttv = OrionStream.UploaderEttv							# 'ettv'				(ETTV)
	UploaderRartv = OrionStream.UploaderRartv						# 'rartv'				(RARTV)
	UploaderRarbg = OrionStream.UploaderRarbg						# 'rarbg'				(RARBG)
	UploaderHdsector = OrionStream.UploaderHdsector					# 'hdsector'			(HDSector)
	UploaderTjet = OrionStream.UploaderTjet							# 'tjet'				(TJET)
	UploaderRick = OrionStream.UploaderRick							# 'rick'				(RiCK)
	Uploader10Bit = OrionStream.Uploader10Bit						# '10bit'				(10bit)
	Uploader8Bit = OrionStream.Uploader8Bit							# '8bit'				(8bit)
	UploaderKillers = OrionStream.UploaderKillers					# 'killers'				(KILLERS)
	UploaderFgt = OrionStream.UploaderFgt							# 'fgt'					(FGT)
	UploaderAvs = OrionStream.UploaderAvs							# 'avs'					(AVS)
	UploaderSva = OrionStream.UploaderSva							# 'sva'					(SVA)
	UploaderFleet = OrionStream.UploaderFleet						# 'fleet'				(FLEET)
	UploaderYifi = OrionStream.UploaderYifi							# 'yifi'				(YIFI)
	UploaderYify = OrionStream.UploaderYify							# 'yify'				(YIFY)
	UploaderYts = OrionStream.UploaderYts							# 'yts'					(YTS)
	UploaderCtrlhd = OrionStream.UploaderCtrlhd						# 'ctrlhd'				(CtrlHD)
	UploaderNtb = OrionStream.UploaderNtb							# 'ntb'					(NTb)
	UploaderEztv = OrionStream.UploaderEztv							# 'eztv'				(EZTV)
	UploaderEtrg = OrionStream.UploaderEtrg							# 'etrg'				(ETRG)
	UploaderEthd = OrionStream.UploaderEthd							# 'ethd'				(EtHD)
	UploaderViethd = OrionStream.UploaderViethd						# 'viethd'				(VietHD)
	UploaderPlutonium = OrionStream.UploaderPlutonium				# 'plutonium'			(PLUTONiUM)
	UploaderTopkek = OrionStream.UploaderTopkek						# 'topkek'				(TOPKEK)
	UploaderTvc = OrionStream.UploaderTvc							# 'tvc'					(TVC)
	UploaderSdi = OrionStream.UploaderSdi							# 'sdi'					(SDI)
	UploaderMtb = OrionStream.UploaderMtb							# 'mtb'					(MTB)
	UploaderFqm = OrionStream.UploaderFqm							# 'fqm'					(FQM)
	UploaderOrganic = OrionStream.UploaderOrganic					# 'organic'				(ORGANiC)
	UploaderFs = OrionStream.UploaderFs								# 'fs'					(FS)
	UploaderSkgtv = OrionStream.UploaderSkgtv						# 'skgtv'				(SKGTV)
	UploaderMorose = OrionStream.UploaderMorose						# 'morose'				(MONROSE)
	UploaderQpel = OrionStream.UploaderQpel							# 'qpel'				(QPEL)
	UploaderTbs = OrionStream.UploaderTbs							# 'tbs'					(TBS)
	UploaderDeflate = OrionStream.UploaderDeflate					# 'deflate'				(DEFLATE)
	UploaderFum = OrionStream.UploaderFum							# 'fum'					(FUM)
	UploaderLol = OrionStream.UploaderLol							# 'lol'					(LOL)
	UploaderAaf = OrionStream.UploaderAaf							# 'aaf'					(aAF)
	UploaderCravers = OrionStream.UploaderCravers					# 'cravers'				(CRAVERS)
	UploaderMoritz = OrionStream.UploaderMoritz						# 'moritz'				(MORiTZ)
	UploaderDeadpool = OrionStream.UploaderDeadpool					# 'deadpool'			(DEADPOOL)
	UploaderEbi = OrionStream.UploaderEbi							# 'ebi'					(Ebi)
	UploaderHeel = OrionStream.UploaderHeel							# 'heel'				(HEEL)
	UploaderStuttershit = OrionStream.UploaderStuttershit			# 'stuttershit'			(STUTTERSHIT)
	UploaderShaanig = OrionStream.UploaderShaanig					# 'shaanig'				(ShAaNiG)
	UploaderDublado = OrionStream.UploaderDublado					# 'dublado'				(Dublado)
	UploaderCpg = OrionStream.UploaderCpg							# 'cpg'					(CPG)
	UploaderExclusive = OrionStream.UploaderExclusive				# 'exclusive'			(Exclusive)
	UploaderHqmic = OrionStream.UploaderHqmic						# 'hqmic'				(HQMic)
	UploaderHivecm8 = OrionStream.UploaderHivecm8					# 'hivecm8'				(HiveCM8)
	UploaderNvee = OrionStream.UploaderNvee							# 'nvee'				(NVEE)
	UploaderFlt = OrionStream.UploaderFlt							# 'flt'					(FLT)
	UploaderJyk = OrionStream.UploaderJyk							# 'jyk'					(JYK)
	UploaderVppv = OrionStream.UploaderVppv							# 'vppv'				(VPPV)
	UploaderW4F = OrionStream.UploaderW4F							# 'w4f'					(W4F)
	UploaderJive = OrionStream.UploaderJive							# 'jive'				(JIVE)
	UploaderRmteam = OrionStream.UploaderRmteam						# 'rmteam'				(RMTeam)
	UploaderWwrg = OrionStream.UploaderWwrg							# 'wwrg'				(WWRG)
	UploaderEpub = OrionStream.UploaderEpub							# 'epub'				(EPUB)
	UploaderGooner = OrionStream.UploaderGooner						# 'gooner'				(Gooner)
	UploaderEvo = OrionStream.UploaderEvo							# 'evo'					(EVO)
	UploaderAfg = OrionStream.UploaderAfg							# 'afg'					(AFG)
	UploaderBrisk = OrionStream.UploaderBrisk						# 'brisk'				(BRISK)
	UploaderDemand = OrionStream.UploaderDemand						# 'demand'				(DEMAND)
	UploaderIsm = OrionStream.UploaderIsm							# 'ism'					(iSm)
	UploaderCrimson = OrionStream.UploaderCrimson					# 'crimson'				(CRiMSON)
	UploaderReward = OrionStream.UploaderReward						# 'reward'				(REWARD)
	UploaderSparks = OrionStream.UploaderSparks						# 'sparks'				(SPARKS)
	UploaderMkvcage = OrionStream.UploaderMkvcage					# 'mkvcage'				(MkvCage)
	UploaderTomcat12 = OrionStream.UploaderTomcat12					# 'tomcat12'			(tomcat12)
	UploaderHon3Y = OrionStream.UploaderHon3Y						# 'hon3y'				(Hon3y)
	UploaderIextv = OrionStream.UploaderIextv						# 'iextv'				(iExTV)
	UploaderGeckos = OrionStream.UploaderGeckos						# 'geckos'				(GECKOS)
	UploaderNezu = OrionStream.UploaderNezu							# 'nezu'				(NeZu)
	UploaderMulvacoded = OrionStream.UploaderMulvacoded				# 'mulvacoded'			(MULVAcoded)
	UploaderPimprg = OrionStream.UploaderPimprg						# 'pimprg'				(pimprg)
	UploaderC4Tv = OrionStream.UploaderC4Tv							# 'c4tv'				(C4TV)
	UploaderPsa = OrionStream.UploaderPsa							# 'psa'					(PSA)
	UploaderReenc = OrionStream.UploaderReenc						# 'reenc'				(ReEnc)
	UploaderDeejayahmed = OrionStream.UploaderDeejayahmed			# 'deejayahmed'			(DeeJayAhmed)
	UploaderUtr = OrionStream.UploaderUtr							# 'utr'					(UTR)
	UploaderJoy = OrionStream.UploaderJoy							# 'joy'					(Joy)
	UploaderMrn = OrionStream.UploaderMrn							# 'mrn'					(MRN)
	UploaderNtg = OrionStream.UploaderNtg							# 'ntg'					(NTG)
	UploaderStrife = OrionStream.UploaderStrife						# 'strife'				(STRiFE)
	UploaderXrg = OrionStream.UploaderXrg							# 'xrg'					(xRG)
	UploaderFightbb = OrionStream.UploaderFightbb					# 'fightbb'				(FightBB)
	UploaderIon10 = OrionStream.UploaderIon10						# 'ion10'				(ION10)
	UploaderGwc = OrionStream.UploaderGwc							# 'gwc'					(GWC)
	UploaderBatv = OrionStream.UploaderBatv							# 'batv'				(BATV)
	UploaderUav = OrionStream.UploaderUav							# 'uav'					(UAV)
	UploaderSpc = OrionStream.UploaderSpc							# 'spc'					(SPC)
	UploaderGirays = OrionStream.UploaderGirays						# 'girays'				(GIRAYS)
	UploaderExyu = OrionStream.UploaderExyu							# 'exyu'				(ExYu)
	UploaderSujaidr = OrionStream.UploaderSujaidr					# 'sujaidr'				(Sujaidr)
	UploaderManning = OrionStream.UploaderManning					# 'manning'				(Manning)
	UploaderN1C = OrionStream.UploaderN1C							# 'n1c'					(N1C)
	UploaderLegi0N = OrionStream.UploaderLegi0N						# 'legi0n'				(LEGi0N)
	UploaderIft = OrionStream.UploaderIft							# 'ift'					(iFT)
	UploaderSecretos = OrionStream.UploaderSecretos					# 'secretos'			(SECRETOS)
	UploaderFreebee = OrionStream.UploaderFreebee					# 'freebee'				(Freebee)
	UploaderX0R = OrionStream.UploaderX0R							# 'x0r'					(x0r)
	UploaderTitan = OrionStream.UploaderTitan						# 'titan'				(TiTAN)
	UploaderCmrg = OrionStream.UploaderCmrg							# 'cmrg'				(CMRG)
	UploaderDhd = OrionStream.UploaderDhd							# 'dhd'					(DHD)
	UploaderGush = OrionStream.UploaderGush							# 'gush'				(GUSH)
	UploaderAdrenaline = OrionStream.UploaderAdrenaline				# 'adrenaline'			(ADRENALiNE)
	UploaderMegusta = OrionStream.UploaderMegusta					# 'megusta'				(MeGusta)
	UploaderM3D = OrionStream.UploaderM3D							# 'm3d'					(M3D)
	UploaderUnveil = OrionStream.UploaderUnveil						# 'unveil'				(UNVEiL)
	UploaderCrooks = OrionStream.UploaderCrooks						# 'crooks'				(CROOKS)
	UploaderD3G = OrionStream.UploaderD3G							# 'd3g'					(d3g)
	UploaderEsc = OrionStream.UploaderEsc							# 'esc'					(eSc)
	UploaderDiamond = OrionStream.UploaderDiamond					# 'diamond'				(DIAMOND)
	UploaderVain = OrionStream.UploaderVain							# 'vain'				(VAiN)
	UploaderCrisc = OrionStream.UploaderCrisc						# 'crisc'				(CRiSC)
	UploaderDon = OrionStream.UploaderDon							# 'don'					(DON)
	UploaderEsir = OrionStream.UploaderEsir							# 'esir'				(ESiR)
	UploaderFuzerhd = OrionStream.UploaderFuzerhd					# 'fuzerhd'				(FuzerHD)
	UploaderWiki = OrionStream.UploaderWiki							# 'wiki'				(WiKi)
	UploaderChd = OrionStream.UploaderChd							# 'chd'					(CHD)
	UploaderHdchina = OrionStream.UploaderHdchina					# 'hdchina'				(HDChina)
	UploaderFramestor = OrionStream.UploaderFramestor				# 'framestor'			(FraMeSToR)
	UploaderGrym = OrionStream.UploaderGrym							# 'grym'				(Grym)
	UploaderHidt = OrionStream.UploaderHidt							# 'hidt'				(HiDt)
	UploaderEbp = OrionStream.UploaderEbp							# 'ebp'					(EbP)
	UploaderDzon3 = OrionStream.UploaderDzon3						# 'dzon3'				(DZON3)
	UploaderMteam = OrionStream.UploaderMteam						# 'mteam'				(MTeam)
	UploaderRapidcows = OrionStream.UploaderRapidcows				# 'rapidcows'			(RAPiDCOWS)
	UploaderExkinoray = OrionStream.UploaderExkinoray				# 'exkinoray'			(ExKinoRay)
	UploaderHifi = OrionStream.UploaderHifi							# 'hifi'				(HiFi)
	UploaderEpsilon = OrionStream.UploaderEpsilon					# 'epsilon'				(EPSiLON)
	UploaderNahom = OrionStream.UploaderNahom						# 'nahom'				(NAHOM)
	UploaderBlueworld = OrionStream.UploaderBlueworld				# 'blueworld'			(BLUEWORLD)
	UploaderDdr = OrionStream.UploaderDdr							# 'ddr'					(DDR)
	UploaderM2Tv = OrionStream.UploaderM2Tv							# 'm2tv'				(M2Tv)
	UploaderVenue = OrionStream.UploaderVenue						# 'venue'				(VENUE)
	UploaderAsh61 = OrionStream.UploaderAsh61						# 'ash61'				(Ash61)
	UploaderPsypher = OrionStream.UploaderPsypher					# 'psypher'				(PSYPHER)
	UploaderSigma = OrionStream.UploaderSigma						# 'sigma'				(SiGMA)
	UploaderPsychd = OrionStream.UploaderPsychd						# 'psychd'				(PSYCHD)
	UploaderFilmanta = OrionStream.UploaderFilmanta					# 'filmanta'			(FiLMANTA)
	UploaderSaphire = OrionStream.UploaderSaphire					# 'saphire'				(SAPHiRE)
	UploaderBlow = OrionStream.UploaderBlow							# 'blow'				(BLOW)
	UploaderBarc0De = OrionStream.UploaderBarc0De					# 'barc0de'				(BARC0DE)
	UploaderHdc = OrionStream.UploaderHdc							# 'hdc'					(HDC)
	UploaderHdclub = OrionStream.UploaderHdclub						# 'hdclub'				(HDCLUB)
	UploaderEncounters = OrionStream.UploaderEncounters				# 'encounters'			(ENCOUNTERS)
	UploaderKorsar = OrionStream.UploaderKorsar						# 'korsar'				(KORSAR)
	UploaderLostfilm = OrionStream.UploaderLostfilm					# 'lostfilm'			(LostFilm)
	UploaderLost = OrionStream.UploaderLost							# 'lost'				(LOST)
	UploaderBaibako = OrionStream.UploaderBaibako					# 'baibako'				(Baibako)
	UploaderSigeris = OrionStream.UploaderSigeris					# 'sigeris'				(SiGERiS)
	UploaderQqss44 = OrionStream.UploaderQqss44						# 'qqss44'				(qqss44)
	UploaderDtone = OrionStream.UploaderDtone						# 'dtone'				(DTOne)
	UploaderHdmaniacs = OrionStream.UploaderHdmaniacs				# 'hdmaniacs'			(HDMaNiAcS)
	UploaderNcmt = OrionStream.UploaderNcmt							# 'ncmt'				(NCmt)
	UploaderDecibel = OrionStream.UploaderDecibel					# 'decibel'				(decibeL)
	UploaderFtwhd = OrionStream.UploaderFtwhd						# 'ftwhd'				(FTWHD)
	UploaderNightripper = OrionStream.UploaderNightripper			# 'nightripper'			(Nightripper)
	UploaderMarge = OrionStream.UploaderMarge						# 'marge'				(MarGe)
	UploaderBlupanther = OrionStream.UploaderBlupanther				# 'blupanther'			(BluPanther)
	UploaderBithd = OrionStream.UploaderBithd						# 'bithd'				(BITHD)
	UploaderBluevo = OrionStream.UploaderBluevo						# 'bluevo'				(BluEvo)
	UploaderTmg = OrionStream.UploaderTmg							# 'tmg'					(TmG)
	UploaderPlayhd = OrionStream.UploaderPlayhd						# 'playhd'				(PlayHD)
	UploaderPlaysd = OrionStream.UploaderPlaysd						# 'playsd'				(PlaySD)
	UploaderSpacehd = OrionStream.UploaderSpacehd					# 'spacehd'				(SpaceHD)
	UploaderCrispy = OrionStream.UploaderCrispy						# 'crispy'				(CRiSPY)
	UploaderHdspace = OrionStream.UploaderHdspace					# 'hdspace'				(HDSpace)
	UploaderVista = OrionStream.UploaderVista						# 'vista'				(ViSTA)
	UploaderKralimarko = OrionStream.UploaderKralimarko				# 'kralimarko'			(KRaLiMaRKo)
	UploaderEpic = OrionStream.UploaderEpic							# 'epic'				(EPiC)
	UploaderDracula = OrionStream.UploaderDracula					# 'dracula'				(DRACULA)
	UploaderTayto = OrionStream.UploaderTayto						# 'tayto'				(TayTO)
	UploaderHdwing = OrionStream.UploaderHdwing						# 'hdwing'				(HDWinG)
	UploaderEpik = OrionStream.UploaderEpik							# 'epik'				(EPiK)
	UploaderPrimalhd = OrionStream.UploaderPrimalhd					# 'primalhd'			(PriMaLHD)
	UploaderHdvn = OrionStream.UploaderHdvn							# 'hdvn'				(HDVN)
	UploaderIde = OrionStream.UploaderIde							# 'ide'					(IDE)
	UploaderInk = OrionStream.UploaderInk							# 'ink'					(iNK)
	UploaderKashmir = OrionStream.UploaderKashmir					# 'kashmir'				(KASHMiR)
	UploaderSbr = OrionStream.UploaderSbr							# 'sbr'					(SbR)
	UploaderLolhd = OrionStream.UploaderLolhd						# 'lolhd'				(LolHD)
	UploaderRovers = OrionStream.UploaderRovers						# 'rovers'				(ROVERS)
	UploaderRmp4L = OrionStream.UploaderRmp4L						# 'rmp4l'				(RMP4L)
	UploaderAjp69 = OrionStream.UploaderAjp69						# 'ajp69'				(AJP69)
	UploaderSa89 = OrionStream.UploaderSa89							# 'sa89'				(SA89)
	UploaderQqq = OrionStream.UploaderQqq							# 'qqq'					(QqQ)
	UploaderDimension = OrionStream.UploaderDimension				# 'dimension'			(DIMENSION)
	UploaderSinners = OrionStream.UploaderSinners					# 'sinners'				(SiNNERS)
	UploaderLord = OrionStream.UploaderLord							# 'lord'				(LoRD)
	UploaderVeto = OrionStream.UploaderVeto							# 'veto'				(VETO)
	UploaderBmf = OrionStream.UploaderBmf							# 'bmf'					(BMF)
	UploaderPbk = OrionStream.UploaderPbk							# 'pbk'					(PbK)
	UploaderForm = OrionStream.UploaderForm							# 'form'				(FoRM)
	UploaderCinefile = OrionStream.UploaderCinefile					# 'cinefile'			(CiNEFiLE)
	UploaderAmiable = OrionStream.UploaderAmiable					# 'amiable'				(AMIABLE)
	UploaderDrones = OrionStream.UploaderDrones						# 'drones'				(DRONES)
	UploaderReplica = OrionStream.UploaderReplica					# 'replica'				(Replica)
	UploaderCytsunee = OrionStream.UploaderCytsunee					# 'cytsunee'			(CyTSuNee)
	UploaderMorpheus = OrionStream.UploaderMorpheus					# 'morpheus'			(Morpheus)
	UploaderVisum = OrionStream.UploaderVisum						# 'visum'				(ViSUM)
	UploaderTerminal = OrionStream.UploaderTerminal					# 'terminal'			(TERMiNAL)
	UploaderKaga = OrionStream.UploaderKaga							# 'kaga'				(KAGA)
	UploaderIcandy = OrionStream.UploaderIcandy						# 'icandy'				(iCANDY)
	UploaderTigole = OrionStream.UploaderTigole						# 'tigole'				(Tigole)
	UploaderLeethd = OrionStream.UploaderLeethd						# 'leethd'				(LeetHD)
	UploaderNohate = OrionStream.UploaderNohate						# 'nohate'				(NoHaTE)
	Uploader2Hd = OrionStream.Uploader2Hd							# '2hd'					(2HD)
	UploaderFto = OrionStream.UploaderFto							# 'fto'					(FTO)
	UploaderMajestic = OrionStream.UploaderMajestic					# 'majestic'			(MAJESTiC)
	UploaderShortbrehd = OrionStream.UploaderShortbrehd				# 'shortbrehd'			(SHORTBREHD)
	UploaderInsidious = OrionStream.UploaderInsidious				# 'insidious'			(iNSIDiOUS)
	UploaderCasstudio = OrionStream.UploaderCasstudio				# 'casstudio'			(CasStudio)
	UploaderTrollhd = OrionStream.UploaderTrollhd					# 'trollhd'				(TrollHD)
	UploaderTrolluhd = OrionStream.UploaderTrolluhd					# 'trolluhd'			(TrollUHD)
	UploaderMonkee = OrionStream.UploaderMonkee						# 'monkee'				(monkee)
	UploaderBamboozle = OrionStream.UploaderBamboozle				# 'bamboozle'			(BAMBOOZLE)
	UploaderLiberty = OrionStream.UploaderLiberty					# 'liberty'				(LiBERTY)
	UploaderMayhem = OrionStream.UploaderMayhem						# 'mayhem'				(MAYHEM)
	UploaderKimchi = OrionStream.UploaderKimchi						# 'kimchi'				(KiMCHi)
	UploaderTurbo = OrionStream.UploaderTurbo						# 'turbo'				(TURBO)
	UploaderYellowbird = OrionStream.UploaderYellowbird				# 'yellowbird'			(YELLOWBiRD)
	UploaderRightsize = OrionStream.UploaderRightsize				# 'rightsize'			(RightSiZE)
	UploaderLektorpl = OrionStream.UploaderLektorpl					# 'lektorpl'			(LektorPL)
	UploaderFratposa = OrionStream.UploaderFratposa					# 'fratposa'			(Fratposa)
	UploaderHdworkshop = OrionStream.UploaderHdworkshop				# 'hdworkshop'			(HDWorkshop)
	UploaderHdil = OrionStream.UploaderHdil							# 'hdil'				(HDIL)
	UploaderSprinter = OrionStream.UploaderSprinter					# 'sprinter'			(SPRiNTER)
	UploaderTdd = OrionStream.UploaderTdd							# 'tdd'					(TDD)
	UploaderHellgate = OrionStream.UploaderHellgate					# 'hellgate'			(HELLGATE)
	UploaderEgen = OrionStream.UploaderEgen							# 'egen'				(EGEN)
	UploaderBhdstudio = OrionStream.UploaderBhdstudio				# 'bhdstudio'			(BHDStudio)
	UploaderSadpanda = OrionStream.UploaderSadpanda					# 'sadpanda'			(SADPANDA)
	UploaderGeek = OrionStream.UploaderGeek							# 'geek'				(Geek)
	UploaderProdji = OrionStream.UploaderProdji						# 'prodji'				(PRoDJi)
	UploaderSkaliwagz = OrionStream.UploaderSkaliwagz				# 'skaliwagz'			(SKALiWAGZ)
	UploaderIvandraren = OrionStream.UploaderIvandraren				# 'ivandraren'			(iVANDRAREN)
	UploaderMannig = OrionStream.UploaderMannig						# 'mannig'				(Mannig)
	UploaderCoaster = OrionStream.UploaderCoaster					# 'coaster'				(COASTER)
	UploaderWdk = OrionStream.UploaderWdk							# 'wdk'					(WDK)
	UploaderSilver007 = OrionStream.UploaderSilver007				# 'silver007'			(Silver007)
	UploaderIsrael = OrionStream.UploaderIsrael						# 'israel'				(iSRAEL)
	UploaderBeast = OrionStream.UploaderBeast						# 'beast'				(beAst)
	UploaderUnitail = OrionStream.UploaderUnitail					# 'unitail'				(UNiTAiL)
	UploaderTusahd = OrionStream.UploaderTusahd						# 'tusahd'				(TUSAHD)
	UploaderNikt0 = OrionStream.UploaderNikt0						# 'nikt0'				(nikt0)
	UploaderKings = OrionStream.UploaderKings						# 'kings'				(KiNGS)
	UploaderDivulged = OrionStream.UploaderDivulged					# 'divulged'			(DiVULGED)
	UploaderZq = OrionStream.UploaderZq								# 'zq'					(ZQ)
	UploaderZest = OrionStream.UploaderZest							# 'zest'				(ZEST)
	UploaderFlame = OrionStream.UploaderFlame						# 'flame'				(FLAME)
	UploaderAcool = OrionStream.UploaderAcool						# 'acool'				(ACOOL)
	UploaderCoo7 = OrionStream.UploaderCoo7							# 'coo7'				(Coo7)
	UploaderHr = OrionStream.UploaderHr								# 'hr'					(HR)
	UploaderSwtyblz = OrionStream.UploaderSwtyblz					# 'swtyblz'				(SWTYBLZ)
	UploaderQmax = OrionStream.UploaderQmax							# 'qmax'				(Qmax)
	UploaderMibr = OrionStream.UploaderMibr							# 'mibr'				(MiBR)
	UploaderHandjob = OrionStream.UploaderHandjob					# 'handjob'				(HANDJOB)
	UploaderIlovehd = OrionStream.UploaderIlovehd					# 'ilovehd'				(iLoveHD)
	UploaderMag = OrionStream.UploaderMag							# 'mag'					(MaG)
	UploaderDawgs = OrionStream.UploaderDawgs						# 'dawgs'				(DAWGS)
	UploaderFookas = OrionStream.UploaderFookas						# 'fookas'				(FooKaS)
	UploaderHon3Yhd = OrionStream.UploaderHon3Yhd					# 'hon3yhd'				(Hon3yHD)
	UploaderChotab = OrionStream.UploaderChotab						# 'chotab'				(Chotab)
	UploaderTwa = OrionStream.UploaderTwa							# 'twa'					(TWA)
	UploaderMelba = OrionStream.UploaderMelba						# 'melba'				(MELBA)
	UploaderPfa = OrionStream.UploaderPfa							# 'pfa'					(PFa)
	UploaderCaligari = OrionStream.UploaderCaligari					# 'caligari'			(CALiGARi)
	UploaderMelite = OrionStream.UploaderMelite						# 'melite'				(MELITE)
	UploaderAdit = OrionStream.UploaderAdit							# 'adit'				(AdiT)
	UploaderTto = OrionStream.UploaderTto							# 'tto'					(TTO)
	UploaderBuymore = OrionStream.UploaderBuymore					# 'buymore'				(BUYMORE)
	UploaderAio = OrionStream.UploaderAio							# 'aio'					(AiO)
	UploaderAfm72 = OrionStream.UploaderAfm72						# 'afm72'				(afm72)
	UploaderNatty = OrionStream.UploaderNatty						# 'natty'				(Natty)
	UploaderTaichi = OrionStream.UploaderTaichi						# 'taichi'				(TAiCHi)

	# Edition Type
	EditionNone = OrionStream.EditionNone							# None					(Normal cinema version)
	EditionExtended = OrionStream.EditionExtended					# 'extended'			(Extended editions and director cuts)

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
	SubtitleHard = OrionStream.SubtitleHard							# 'hard'				(Soft-coded subtitles that cannot be disabled)

	# Sorting Value
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
		self.mApp.refresh() # Must be done here instead of the instance function, otherwise the is recursion with the API.
		self.mEncoding = encoding

	##############################################################################
	# ENCODING
	##############################################################################

	def _encode(self, object, encoding = None):
		if encoding == None: encoding = self.mEncoding
		if object == None: return '' if encoding == Orion.EncodingJson else None
		elif encoding == Orion.EncodingJson:
			if OrionTools.isArray(object): return [OrionTools.jsonTo(i.data()) for i in object]
			else: return OrionTools.jsonTo(object.data())
		elif encoding == Orion.EncodingStruct:
			if OrionTools.isArray(object): return [i.data() for i in object]
			else: return object.data()
		else: return object

	##############################################################################
	# LINK
	##############################################################################

	def link(self):
		return OrionTools.link()

	##############################################################################
	# SETTINGS
	##############################################################################

	def settingsScrapingTimeout(self):
		return OrionSettings.getGeneralScrapingTimeout()

	def settingsScrapingMode(self):
		return OrionSettings.getGeneralScrapingMode()

	def settingsScrapingCount(self):
		return OrionSettings.getGeneralScrapingCount()

	def settingsScrapingQuality(self):
		return OrionSettings.getGeneralScrapingQuality()

	##############################################################################
	# APP
	##############################################################################

	def app(self, encoding = None):
		return self._encode(self.mApp, encoding = encoding)

	def appValid(self):
		return self.mApp.valid()

	def appDialog(self):
		return OrionNavigator.dialogApp()

	##############################################################################
	# USER
	##############################################################################

	def user(self, encoding = None):
		return self._encode(OrionUser.instance(), encoding = encoding)

	def userEnabled(self):
		return OrionUser.instance().enabled()

	def userValid(self):
		return OrionUser.instance().valid()

	def userFree(self):
		return OrionUser.instance().subscriptionPackageFree()

	def userPremium(self):
		return OrionUser.instance().subscriptionPackagePremium()

	def userDialog(self):
		return OrionNavigator.dialogUser()

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

	def serverStats(self, encoding = None):
		stats = OrionStats.instance()
		stats.update()
		return self._encode(stats, encoding = encoding)

	def serverDialog(self):
		return OrionNavigator.dialogServer()

	def serverTest(self):
		return OrionApi().serverTest()

	##############################################################################
	# STREAMS
	##############################################################################

	def streams(self,

				type,

				query = None,

				idOrion = None,
				idImdb = None,
				idTmdb = None,
				idTvdb = None,

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

				fileSize = FilterSettings, # Can be a single value holding the maximum size (eg: 1073741824), or a tuple/list with the minimum and maximum sizes (eg: [536870912,1073741824]). If either value is None, there is no upper/lower bound (eg: [536870912,None])
				fileUnknown = FilterSettings,
				filePack = FilterSettings,

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

			fileSize = fileSize,
			fileUnknown = fileUnknown,
			filePack = filePack,

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

	def streamsCount(self, streams, quality = FilterNone):
		if quality == Orion.FilterSettings: quality = self.settingsScrapingQuality()
		return OrionStream.count(streams = streams, quality = quality)

	def streamVote(self, idItem, idStream, vote = VoteUp, notification = False):
		OrionItem.popularityVote(idItem = idItem, idStream = idStream, vote = vote, notification = notification)

	def streamRemove(self, idItem, idStream, notification = False):
		OrionItem.remove(idItem = idItem, idStream = idStream, notification = notification)

	def streamTypes(self, supported = None):
		types = []
		setting = OrionSettings.getFiltersInteger('filters.stream.type', self.mApp.id())
		if setting in (0, 1, 2, 4) and (supported == None or OrionStream.TypeTorrent in supported): types.append(OrionStream.TypeTorrent)
		if setting in (0, 1, 3, 5) and (supported == None or OrionStream.TypeUsenet in supported): types.append(OrionStream.TypeUsenet)
		if setting in (0, 2, 3, 6) and (supported == None or OrionStream.TypeHoster in supported): types.append(OrionStream.TypeHoster)
		return types
