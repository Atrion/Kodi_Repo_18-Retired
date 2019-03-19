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
import os
import sys
import json
import platform
import subprocess
import datetime
import time
import collections
import math
import threading
import signal
import uuid
import numbers
import copy

from difflib import SequenceMatcher

from resources.lib.modules import client
from resources.lib.modules import cleantitle

from resources.lib.externals.unidecode import unidecode
from resources.lib.externals.hachoir.hachoir_parser import createParser
from resources.lib.externals.hachoir.hachoir_metadata import extractMetadata

from resources.lib.extensions import network
from resources.lib.extensions import tools
from resources.lib.extensions import interface

# Python 2.6 and lower (eg: Android SPMC) do not have an OrderedDict module. Use a manual one.
try: from collections import OrderedDict
except: from resources.lib.externals.ordereddict.ordereddict import OrderedDict

class Metadata(object):

	TypeNone = None
	TypeLocal = 'local'
	TypePremium = 'premium'
	TypeTorrent = 'torrent'
	TypeUsenet = 'usenet'
	TypeHoster = 'hoster'

	LabelNone = 0
	LabelMini = 1
	LabelShort = 2
	LabelFull = 3

	# Information
	InformationAll = 0
	InformationEssential = 1
	InformationNonessential = 2

	IgnoreDifference = 0.4 # The minimum difference between the name and the title. If below, the file will be ignored. 0.3 is not enough (EzTV Kings of Queens S05E03)
	IgnoreContains = 0.5 # The percentage of split parts of the title that has to match the file name split.
	IgnoreLength = 1.8 # The percentage the file name length (everything before the year) can be longer than the actual title. 2 is too much for "Wonder 2017" vs "Wonder Woman 2017".
	IgnoreSize = 20971520 # Files smaller than this will be ignored. 20 MB.

	Fill = '•••••'

	SizeStep = 4000 # Reduce the number of colors generated.
	SizeMinimum = 174762 # 300 MB for 30 minutes for HD1080.
	SizeMaximum = 1193046 # 2GB for 30 minutes for HD1080.
	SizeDifference = SizeMaximum - SizeMinimum
	SizeCount = int(SizeDifference / float(SizeStep))

	Seasons = [
		'season%02d',
		'season %02d',
		'season_%02d',
		'season-%02d',
		'season.%02d',
		'season%d',
		'season %d',
		'season_%d',
		'season-%d',
		'season.%d',

		# Must contains space/character after season, else will also match format S01E01
		's%02d ',
		's%02d_',
		's%02d_',
		's%02d.',
		's%d ',
		's%d_',
		's%d-',
		's%d.',

		# French
		'box%02d',
		'box %02d',
		'box_%02d',
		'box-%02d',
		'box.%02d',
		'saison%02d',
		'saison %02d',
		'saison_%02d',
		'saison-%02d',
		'saison.%02d',
		'saison%d',
		'saison %d',
		'saison_%d',
		'saison-%d',
		'saison.%d',

		# Russian
		'сезон%02d',
		'сезон %02d',
		'сезон_%02d',
		'сезон-%02d',
		'сезон.%02d',
		'сезон%d',
		'сезон %d',
		'сезон_%d',
		'сезон-%d',
		'сезон.%d',
	]

	SeasonsExclude = '(e|ep|episode)\s*[0-9]+'

	Episodes = [
		's%02de%02d',
		's%02d e%02d',
		'%02dx%02d',
		'%02d_%02d',
		'%02d-%02d',
		'%02d.%02d',
		'season%02depisode%02d',
		'season%02d episode%02d',
		'season %02d episode %02d',
		'season%02dpart%02d',
		'season%02d part%02d',
		'season %02d part %02d',
		's%de%d',
		's%d e%d',
		'%dx%d',
		'%d_%d',
		'%d-%d',
		'%d.%d',
		'season%depisode%d',
		'season%d episode%d',
		'season %d episode %d',
		'season%dpart%d',
		'season%d part%d',
		'season %d part %d',
		'episode %d',
		'episode %02d',
		'ep %d',
		'ep %02d',
	]

	# Must be in order, so that eg DVD Rip comes before DVD.
	# Do not add space to end of values. otherwise detects it everywhere.
	DictionaryReleases = OrderedDict([
		('CAM|Camera' , ['camrip', 'cam rip', 'hdcam', 'hd cam', 'dvdcam', 'dvd cam', 'cam']),
		('HDTS|HD Telesync' , ['hdts', 'hdtelesync', 'hdtsync']),
		('TS|Telesync' , ['ts', 'telesync', 'tsync', 'tsrip', 'dvdts', 'dvd ts']),
		('TK|Telecine' , ['tc', 'tk', 'telecine', 'tcine', 'tcrip', 'dvdtc', 'dvd tc']),
		('DVDSCR|DVD Screener' , ['dvdscr', 'dvdscreener']),
		('BDSCR|BluRay Screener' , ['bdscr', 'bdscreener', 'blurayscreener', 'bluray screener']),
		('SCR|Screener' , ['screener', 'scr']),
		('VHSRIP|VHS Rip' , ['vhsrip', 'vhs rip']),
		('DVDRIP|DVD Rip' , ['dvdrip', 'dvd rip']),
		('BDRIP|BluRay Rip' , ['bdrip', 'bd rip', 'brrip', 'br rip', 'blurayrip', 'bluray rip']),
		('TVRIP|Television Rip' , ['tvrip', 'tv rip']),
		('HDRIP|HD Rip' , ['hdrip', 'hd rip']),
		('HDTV|HD Television' , ['hdtv', 'hd tv']),
		('WP|Workprint' , ['wp', 'workprint']),
		('R5|Region 5' , ['r5']),
		('PPV|Pay Per View' , ['ppv', 'ppvrip', 'ppv rip']),
		('DDC|Direct Digital Content' , ['ddc']),
		('VCD|Virtual CD' , ['vcd', 'virtualcd', 'virtual cd']),
		('VHS|VHS' , ['vhs']),
		('PDVD|PDVD' , ['pdvd']),
		('DVD|DVD' , ['dvd']),
		('DVDRMX|DVD Remux' , ['dvdremux', 'dvd remux']),
		('WEBDL|Web Download' , ['webdl', 'web dl', 'webdownload', 'web download']),
		('WEBRIP|Web Rip' , ['webrip', 'web rip']),
		('WEBCAP|Web Capture' , ['webcap', 'web cap']),
		('BDRMX|BluRay Remux' , ['bdrmx', 'bd rmx', 'blurayremux', 'bluray remux', 'remux']),
		('BLURAY|BluRay' , ['bd', 'br', 'bluray', 'blu ray']),
	])

	DictionaryUploaders = OrderedDict([
		# These are website, forums, and main uploaders. List them first so that their name appears first.
		('PublicHD' , ['publichd']),
		('ETTV' , ['ettv']),
		('RARTV' , ['rartv']),
		('RARBG' , ['rarbg']),
		('HDSector' , ['hdsector']),
		('TJET' , ['tjet']),
		('RiCK' , ['rick']),

		('10bit' , ['10bit']),
		('8bit' , ['8bit']),
		('KILLERS' , ['killers']),
		('FGT' , ['fgt']),
		('AVS' , ['avs']),
		('SVA' , ['sva']),
		('FLEET' , ['fleet']),
		('YIFI' , ['yifi']),
		('YIFY' , ['yify']),
		('YTS' , ['yts']),
		('CtrlHD' , ['ctrlhd']),
		('NTb' , ['ntb']),
		('EZTV' , ['eztv']),
		('ETRG' , ['etrg']),
		('EtHD' , ['ethd']),
		('VietHD' , ['viethd']),
		('PLUTONiUM' , ['plutonium']),
		('TOPKEK' , ['topkek']),
		('TVC' , ['tvc']),
		('SDI' , ['sdi']),
		('MTB' , ['mtb']),
		('FQM' , ['fqm']),
		('ORGANiC' , ['organic']),
		('FS' , ['fs']),
		('SKGTV' , ['skgtv']),
		('MONROSE' , ['morose']),
		('QPEL' , ['qpel']),
		('TBS' , ['tbs']),
		('DEFLATE' , ['deflate']),
		('FUM' , ['fum']),
		('LOL' , ['lol']),
		('aAF' , ['aaf']),
		('CRAVERS' , ['cravers']),
		('MORiTZ' , ['moritz']),
		('DEADPOOL' , ['deadpool']),
		('Ebi' , ['ebi']),
		('HEEL' , ['heel']),
		('STUTTERSHIT' , ['stuttershit']),
		('ShAaNiG' , ['shaanig']),
		('Dublado' , ['dublado']),
		('CPG' , ['cpg']),
		('Exclusive' , ['exclusive']),
		('HQMic' , ['hqmic']),
		('HiveCM8' , ['hivecm8', 'hive cm8']),
		('NVEE' , ['nvee']),
		('FLT' , ['flt']),
		('JYK' , ['jyk']),
		('VPPV' , ['vppv']),
		('W4F' , ['w4f']),
		('JIVE' , ['jive']),
		('RMTeam' , ['rmteam']),
		('WWRG' , ['wwrg']),
		('EPUB' , ['epub']),
		('Gooner' , ['gooner']),
		('EVO' , ['evo']),
		('AFG' , ['afg']),
		('BRISK' , ['brisk']),
		('DEMAND' , ['demand']),
		('iSm' , ['ism']),
		('CRiMSON' , ['crimson']),
		('REWARD' , ['reward']),
		('SPARKS' , ['sparks']),
		('MkvCage' , ['mkvcage']),
		('tomcat12' , ['tomcat12']),
		('Hon3y' , ['hon3y']),
		('iExTV' , ['iextv']),
		('GECKOS' , ['geckos']),
		('NeZu' , ['nezu']),
		('MULVAcoded' , ['mulvacoded']),
		('pimprg' , ['pimprg']),
		('C4TV' , ['c4tv']),
		('PSA' , ['psa']),
		('ReEnc' , ['reenc']),
		('DeeJayAhmed' , ['deejayahmed']),
		('UTR' , ['utr']),
		('Joy' , ['joy']),
		('MRN' , ['mrn']),
		('NTG' , ['ntg']),
		('STRiFE' , ['strife']),
		('xRG' , ['xrg']),
		('FightBB' , ['fightbb', 'fight bb']),
		('ION10' , ['ion10', 'ion 10']),
		('GWC' , ['gwc']),
		('BATV' , ['batv']),
		('UAV' , ['uav']),
		('SPC' , ['spc']),
		('GIRAYS' , ['girays']),
		('ExYu' , ['exyu']),
		('Sujaidr' , ['sujaidr']),
		('Manning' , ['manning']),
		('N1C' , ['n1c']),
		('LEGi0N' , ['legi0n']),
		('iFT' , ['ift']),
		('SECRETOS' , ['secretos']),
		('Freebee' , ['freebee']),
		('x0r' , ['x0r']),
		('TiTAN' , ['titan']),
		('CMRG' , ['cmrg']),
		('DHD' , ['dhd']),
		('GUSH' , ['gush']),
		('ADRENALiNE' , ['adrenaline']),
		('MeGusta' , ['megusta']),
		('M3D' , ['m3d']),
		('UNVEiL' , ['unveil']),
		('CROOKS' , ['crooks']),
		('d3g' , ['d3g']),
		('eSc' , ['esc']),
		('DIAMOND' , ['diamond']),
		('VAiN' , ['vain']),

		('CRiSC' , ['crisc']),
		('DON' , ['don']),
		('ESiR' , ['esir']),
		('FuzerHD' , ['fuzerhd']),
		('WiKi' , ['wiki']),
		('CHD' , ['chd']),
		('HDChina' , ['hdchina']),
		('FraMeSToR' , ['framestor']),
		('Grym' , ['grym']),
		('HiDt' , ['hidt']),
		('EbP' , ['ebp']),
		('DZON3' , ['d-zon3', 'dzon3']),
		('MTeam' , ['mteam']),
		('RAPiDCOWS' , ['rapidcows']),
		('ExKinoRay' , ['exkinoray']),
		('HiFi' , ['hifi']),
		('EPSiLON' , ['epsilon']),
		('NAHOM' , ['nahom']),
		('BLUEWORLD' , ['blueworld']),
		('DDR' , ['ddr']),
		('M2Tv' , ['m2tv']),
		('VENUE' , ['venue']),
		('Ash61' , ['ash61']),
		('PSYPHER' , ['psypher']),
		('SiGMA' , ['sigma']),
		('PSYCHD' , ['psychd']),
		('FiLMANTA' , ['filmanta']),
		('SAPHiRE' , ['saphire']),
		('BLOW' , ['blow']),
		('BARC0DE' , ['barc0de']),
		('HDC' , ['hdc']),
		('HDCLUB' , ['hdclub']),
		('ENCOUNTERS' , ['encounters']),
		('KORSAR' , ['korsar']),
		('LostFilm' , ['lostfilm', 'lost film']),
		('LOST' , ['lost']),
		('Baibako' , ['baibako']),
		('SiGERiS' , ['sigeris']),
		('qqss44' , ['qqss44']),
		('DTOne' , ['dtone']),
		('HDMaNiAcS' , ['hdmaniacs']),
		('NCmt' , ['ncmt']),
		('decibeL' , ['decibel']),
		('FTWHD' , ['ftw-hd', 'ftwhd', 'ftw hd']),
		('Nightripper' , ['nightripper']),
		('MarGe' , ['marge']),
		('BluPanther' , ['blupanther']),
		('BITHD' , ['bithd']),
		('BluEvo' , ['bluevo']),
		('TmG' , ['tmg']),
		('PlayHD' , ['playhd']),
		('PlaySD' , ['playsd']),
		('SpaceHD' , ['spacehd']),
		('CRiSPY' , ['crispy']),
		('HDSpace' , ['hdspace']),
		('ViSTA' , ['vista']),
		('KRaLiMaRKo' , ['kralimarko']),
		('EPiC' , ['epic']),
		('DRACULA' , ['dracula']),
		('TayTO' , ['tayto']),
		('HDWinG' , ['hdwing']),
		('EPiK' , ['epik']),
		('PriMaLHD' , ['primalhd']),
		('HDVN' , ['hdvn']),
		('IDE' , ['ide']),
		('iNK' , ['ink']),
		('KASHMiR' , ['kashmir']),
		('SbR' , ['sbr']),
		('LolHD' , ['lolhd']),
		('ROVERS' , ['rovers']),
		('RMP4L' , ['rmp4l']),
		('AJP69' , ['ajp69']),
		('SA89' , ['sa89']),
		('QqQ' , ['qqq']),
		('DIMENSION' , ['dimension']),
		('SiNNERS' , ['sinners']),
		('LoRD' , ['lord']),
		('VETO' , ['veto']),
		('BMF' , ['bmf']),
		('PbK' , ['pbk']),
		('FoRM' , ['form']),
		('CiNEFiLE' , ['cinefile']),
		('AMIABLE' , ['amiable']),
		('DRONES' , ['drones']),
		('Replica' , ['replica']),
		('CyTSuNee' , ['cytsunee']),
		('Morpheus' , ['morpheus']),
		('ViSUM' , ['visum']),
		('TERMiNAL' , ['terminal']),
		('KAGA' , ['kaga']),
		('iCANDY' , ['icandy']),
		('Tigole' , ['tigole']),
		('LeetHD' , ['leethd']),
		('NoHaTE' , ['nohate']),
		('2HD' , ['2hd']),
		('FTO' , ['fto']),
		('MAJESTiC' , ['majestic']),
		('SHORTBREHD' , ['shortbrehd']),
		('iNSIDiOUS' , ['insidious']),
		('CasStudio' , ['casstudio']),
		('TrollHD' , ['trollhd']),
		('TrollUHD' , ['trolluhd']),
		('monkee' , ['monkee']),
		('BAMBOOZLE' , ['bamboozle']),
		('LiBERTY' , ['liberty']),
		('MAYHEM' , ['mayhem']),
		('KiMCHi' , ['kimchi']),
		('TURBO' , ['turbo']),
		('YELLOWBiRD' , ['yellowbird']),
		('RightSiZE' , ['rightsize']),
		('LektorPL' , ['lektorpl']),
		('Fratposa' , ['fratposa']),
		('HDWorkshop' , ['hd workshop', 'hdworkshop']),
		('HDIL', ['hdil']),
		('SPRiNTER', ['sprinter']),
		('TDD', ['tdd']),
		('HELLGATE', ['hellgate']),
		('EGEN', ['egen']),
		('BHDStudio', ['bhdstudio']),
		('SADPANDA', ['sadpanda']),
		('Geek', ['geek']),
		('PRoDJi', ['prodji']),
		('SKALiWAGZ', ['skaliwagz']),
		('iVANDRAREN', ['ivandraren']),
		('Mannig', ['mannig']),
		('COASTER', ['coaster']),
		('WDK', ['wdk']),
		('Silver007', ['silver007']),
		('iSRAEL', ['israel']),
		('beAst', ['beast']),
		('UNiTAiL', ['unitail']),
		('TUSAHD', ['tusahd']),
		('nikt0', ['nikt0']),
		('KiNGS', ['kings']),
		('DiVULGED', ['divulged']),
		('ZQ', ['zq']),
		('ZEST', ['zest']),
		('FLAME', ['flame']),
		('ACOOL', ['acool']),
		('Coo7', ['coo7']),
		('HR', ['hr']),
		('SWTYBLZ', ['swtyblz']),
		('Qmax', ['qmax']),
		('MiBR', ['mibr']),
		('HANDJOB', ['handjob']),
		('iLoveHD', ['ilovehd']),
		('MaG', ['mag']),
		('DAWGS', ['dawgs']),
		('FooKaS', ['fookas']),
		('Hon3yHD', ['hon3yhd']),
		('Chotab', ['chotab']),
		('TWA', ['twa']),
		('MELBA', ['melba']),
		('PFa', ['pfa']),
		('CALiGARi', ['caligari']),
		('MELITE', ['melite']),
		('AdiT', ['adit']),
		('TTO', ['tto']),
		('BUYMORE', ['buymore']),
		('AiO', ['aio']),
		('afm72', ['afm72']),
		('Natty', ['natty']),
		('TAiCHi', ['taichi']),
	])

	VideoQualityDefault = 'SD'
	VideoQualityUltra = 'HDULTRA'
	VideoQualityOrder = ['CAM', 'CAM720', 'CAM1080', 'SCR', 'SCR720', 'SCR1080', 'SD', 'HD720', 'HD1080', 'HD2K', 'HD4K', 'HD6K', 'HD8K']

	# Must be ordered from best to worst. Especially if HD is in the title, it should default to 720, but the true HD quality might be somewhere else in the title.
	# Always check for SCR and CAM first, because later CAM versions are often 720p or 1080p, but should not be detected as HD quality. Eg: The.Great.Wall.2016.1080p.HC.HDRip.X264.AC3-EVO[EtHD]
	DictionaryVideoQuality = OrderedDict([
		('CAM1080' , [['camrip', 'cam rip', 'tsrip', 'ts rip', 'hdcam', 'hd cam', 'hdts', 'hd ts', 'dvdcam', 'dvd cam', 'dvdts', 'dvd ts', 'cam', 'telesync', 'tele sync', 'ts', 'pdvd', 'camrip ', 'tsrip ', 'hdcam ', 'hdts ', 'dvdcam ', 'dvdts ', 'telesync ', 'hdtc', 'hd tc', 'telecine'], ['1080', '1080p', '1080i', 'hd1080', '1080hd', '1080 ', '1080p ', '1080i ', 'hd1080 ', '1080hd ', '1200p', '1200i', 'hd1200', '1200hd', '1200p ', '1200i ', 'hd1200 ', '1200hd ']]),
		('CAM720' , [['camrip', 'cam rip', 'tsrip', 'ts rip', 'hdcam', 'hd cam', 'hdts', 'hd ts', 'dvdcam', 'dvd cam', 'dvdts', 'dvd ts', 'cam', 'telesync', 'tele sync', 'ts', 'pdvd', 'camrip ', 'tsrip ', 'hdcam ', 'hdts ', 'dvdcam ', 'dvdts ', 'telesync ', 'hdtc', 'hd tc', 'telecine'], ['720', '720p', '720i', 'hd720', '720hd', 'hd', '720 ', '720p ', '720i ', 'hd720 ', '720hd ']]),
		('CAM' , ['camrip', 'cam rip', 'tsrip', 'ts rip', 'hdcam', 'hd cam', 'hdts', 'hd ts', 'dvdcam', 'dvd cam', 'dvdts', 'dvd ts', 'cam', 'telesync', 'tele sync', 'ts', 'pdvd', 'camrip ', 'tsrip ', 'hdcam ', 'hdts ', 'dvdcam ', 'dvdts ', 'telesync ', 'hdtc', 'hd tc', 'telecine']),
		('SCR1080' , [['dvdscr', 'dvdscreener', 'screener', 'scr', 'bdscr', 'r5', 'dvdscr ', 'r5 ', 'ddc'], ['1080', '1080p', '1080i', 'hd1080', '1080hd', '1080 ', '1080p ', '1080i ', 'hd1080 ', '1080hd ', '1200p', '1200i', 'hd1200', '1200hd', '1200p ', '1200i ', 'hd1200 ', '1200hd ']]),
		('SCR720' , [['dvdscr', 'dvdscreener', 'screener', 'scr', 'bdscr', 'r5', 'dvdscr ', 'r5 ', 'ddc'], ['720', '720p', '720i', 'hd720', '720hd', 'hd', '720 ', '720p ', '720i ', 'hd720 ', '720hd ']]),
		('SCR' , ['dvdscr', 'dvdscreener', 'screener', 'scr', 'bdscr', 'r5', 'dvdscr ', 'r5 ', 'ddc']),

		('HD8K' , ['8k', 'hd8k', 'hd8k ', '8khd', '8khd ', '4320p', '4320i', 'hd4320', '4320hd', '4320p ', '4320i ', 'hd4320 ', '4320hd ', '5120p', '5120i', 'hd5120', '5120hd', '5120p ', '5120i ', 'hd5120 ', '5120hd ', '8192p', '8192i', 'hd8192', '8192hd', '8192p ', '8192i ', 'hd8192 ', '8192hd ']),
		('HD6K' , ['6k', 'hd6k', 'hd6k ', '6khd', '6khd ', '3160p', '3160i', 'hd3160', '3160hd', '3160p ', '3160i ', 'hd3160 ', '3160hd ', '4096p', '4096i', 'hd4096', '4096hd', '4096p ', '4096i ', 'hd4096 ', '4096hd ']),
		('HD4K' , ['4k', 'hd4k', 'hd4k ', '4khd', '4khd ', 'uhd', 'ultrahd', 'ultra hd', 'ultra high', '2160', '2160p', '2160i', 'hd2160', '2160hd', '2160 ', '2160p ', '2160i ', 'hd2160 ', '2160hd ', '1716p', '1716i', 'hd1716', '1716hd', '1716p ', '1716i ', 'hd1716 ', '1716hd ', '2664p', '2664i', 'hd2664', '2664hd', '2664p ', '2664i ', 'hd2664 ', '2664hd ', '3112p', '3112i', 'hd3112', '3112hd', '3112p ', '3112i ', 'hd3112 ', '3112hd ', '2880p', '2880i', 'hd2880', '2880hd', '2880p ', '2880i ', 'hd2880 ', '2880hd ']),
		('HD2K' , ['2k', 'hd2k', 'hd2k ', '2khd', '2khd ', '2048p', '2048i', 'hd2048', '2048hd', '2048p ', '2048i ', 'hd2048 ', '2048hd ', '1332p', '1332i', 'hd1332', '1332hd', '1332p ', '1332i ', 'hd1332 ', '1332hd ', '1440p', '1440i', 'hd1440', '1440hd', '1440p ', '1440i ', 'hd1440 ', '1440hd ', '1556p', '1556i', 'hd1556', '1556hd', '1556p ', '1556i ', 'hd1556 ', '1556hd ', ]),
		('HD1080' , ['1080', '1080p', '1080i', 'hd1080', '1080hd', '1080 ', '1080p ', '1080i ', 'hd1080 ', '1080hd ', '1200p', '1200i', 'hd1200', '1200hd', '1200p ', '1200i ', 'hd1200 ', '1200hd ']),
		('HD720' , ['720', '720p', '720i', 'hd720', '720hd', 'hd', '720 ', '720p ', '720i ', 'hd720 ', '720hd ']),
		('SD' , ['sd', '576', '576p', '576i', 'sd576', '576sd', '576 ', '576p ', '576i ', 'sd576 ', '576sd ', '480', '480p', '480i', 'sd480', '480sd', '480 ', '480p ', '480i ', 'sd480 ', '480sd ', '360', '360p', '360i', 'sd360', '360sd', '360 ', '360p ', '360i ', 'sd360 ', '360sd ', '240', '240p', '240i', 'sd240', '240sd', '240 ', '240p ', '240i ', 'sd240 ', '240sd ']),
	])

	DictionaryVideoCodec = OrderedDict([
		('H266' , ['fvc', 'h266', 'x266', '266', 'fvc ', 'h266 ', 'x266 ']),
		('H265' , ['hevc', 'h265', 'x265', '265', 'hevc ', 'h265 ', 'x265 ']),
		('H264' , ['avc', 'h264', 'x264', '264', 'h264 ', 'x264 ']),
		('H262' , ['h262', 'x262', '262', 'h262 ', 'x262 ']),
		('H222' , ['h222', 'x222', '222', 'h222 ', 'x222 ']),
		('XVID' , ['xvid', 'xvid ']),
		('DIVX' , ['divx', 'divx ', 'div2', 'div2 ', 'div3', 'div3 ']),
		('MPEG' , ['mp4', 'mpeg', 'm4v', 'mpg', 'mpg1', 'mpg2', 'mpg3', 'mpg4', 'mp4 ', 'mpeg ', 'msmpeg', 'msmpeg4', 'mpegurl', 'm4v ', 'mpg ', 'mpg1 ', 'mpg2 ', 'mpg3 ', 'mpg4 ', 'msmpeg ', 'msmpeg4 ']),
		('AVI' , ['avi']),
		('FLV' , ['flv', 'f4v', 'swf', 'flv ', 'f4v ', 'swf ']),
		('WMV' , ['wmv', 'wmv ']),
		('MOV' , ['mov']),
		('3GP' , ['3gp', '3gp ']),
		('MKV' , ['mkv', 'mkv ', 'matroska', 'matroska ']),
	])

	DictionaryVideoExtra = OrderedDict([
		('3D' , ['3d', 'sbs', 'hsbs', 'sidebyside', 'side by side', 'stereoscopic', 'tab', 'htab', 'topandbottom', 'top and bottom']),
	])

	DictionaryEdition = OrderedDict([
		('Extended' , ['ee', 'see', 'ece', 'ext', 'exted', 'extendededition', 'extended', 'extendedcut', 'directors', 'directorsedition', 'directorscut', 'special', 'specialedition', 'specialcut', 'collector', 'collectoredition', 'collectorcut', 'collectors', 'collectorsedition', 'collectorscut']),
	])

	DictionaryAudioChannels = OrderedDict([
		('8CH' , ['ch8', '8ch', 'ch7', '7ch', '7 1', 'ch7 1', '7 1ch', 'ch8 ', '8ch ', 'ch7 ', '7ch ']),
		('6CH' , ['ch6', '6ch', 'ch6', '6ch', '6 1', 'ch6 1', '6 1ch', '5 1', 'ch5 1', '5 1ch', 'ch6 ', '6ch ', 'ch6 ', '6ch ']),
		('2CH' , ['ch2', '2ch', 'stereo', 'dualaudio', 'dual', '2 0', 'ch2 0', '2 0ch', 'ch2 ', '2ch ', 'stereo ', 'dualaudio ', 'dual ']),
		('1CH' , ['ch1', '1ch', 'mono', 'monoaudio', 'ch1 0', '1 0ch', 'ch1 ', '1ch ', 'mono ']),
	])

	DictionaryAudioSystem = OrderedDict([
		('DD|Dolby Digital' ,					['dolbydigital', 'dolby digital', 'dolby', 'dd', 'dd5', 'dd7',  'dolbydigital ', 'dolby digital ', 'dolby ', 'dd ', 'dd5 ', 'dd7 ']),
		('DTS|Digital Theater Systems' ,		['digitaltheatersystems', 'digital theater systems', 'dts', 'dts5', 'dts7', 'digitaltheatersystems ', 'digital theater systems ', 'dts ', 'dts5 ', 'dts7 ']),
		('DIG|DigiRise' ,						['digirise', 'digi rise', 'digirise ', 'digi rise ']),
	])

	# References DictionaryAudioCodec.
	DictionaryAudioSystemReference = OrderedDict([
		('DD|Dolby Digital' ,					['ac3', 'ac4', 'thd', 'amsthd', 'amspls', 'ams', 'pls', 'lve', 'ex', 'sex']),
		('DTS|Digital Theater Systems' ,		['70', '9624', 'es', 'neo6', 'neox', 'neopc', 'neo', 'hdhra', 'hdma', 'hd', 'x', 'nx', 'hx', 'ss', 'con', 'ina', 'pyf']),
		('DIG|DigiRise' ,						['dra']),
		('MPEG|Moving Picture Experts Group' ,	['aac', 'mp3', 'mp2']),
		('XIPH|Xiph Foundation' ,				['flac', 'ogg']),
		('WIN|Windows' ,						['wma']),
		('APP|Apple' ,							['alac']),
	])

	# Order important.
	DictionaryAudioCodec = OrderedDict([
		# DD
		('AMSTHD|Atmos TrueHD' ,								[['dolbydigitalatmos', 'dolbyatmos', 'ddatmos', 'dolby digital atmos', 'dolby atmos', 'dd atmos', 'atmos', 'dolbydigitalatmos ', 'dolbyatmos ', 'ddatmos ', 'dolby digital atmos ', 'dolby atmos ', 'dd atmos ', 'atmos '], ['dolbydigitaltruehd', 'dolbytruehd', 'ddtruehd', 'truehd', 'dolbydigitaltrue', 'dolbytrue', 'ddtrue', 'dolbydigitalhd', 'dolbyhd', 'dolby digital truehd', 'dolby truehd', 'dd truehd', 'dolby digital true', 'dolby true', 'dd true', 'dolby digital hd', 'true hd', 'ddhd', 'dolbydigitaltruehd ', 'dolbytruehd ', 'ddtruehd ', 'truehd ', 'dolbydigitaltrue ', 'dolbytrue ', 'ddtrue ', 'dolbydigitalhd ', 'dolbyhd ', 'dolby digital truehd ', 'dolby truehd ', 'dd truehd ', 'dolby digital true ', 'dolby true ', 'dd true ', 'dolby digital hd ', 'true hd ', 'ddhd ']]),
		('AMSPLS|Atmos Plus' ,									[['dolbydigitalatmos', 'dolbyatmos', 'ddatmos', 'dolby digital atmos', 'dolby atmos', 'dd atmos', 'atmos', 'dolbydigitalatmos ', 'dolbyatmos ', 'ddatmos ', 'dolby digital atmos ', 'dolby atmos ', 'dd atmos ', 'atmos '], ['dolbydigitaleac3', 'dolbyeac3', 'ddeac3', 'dolby digital eac3', 'dolby eac3', 'dd eac3', 'eac3', 'eac 3', 'dolbydigitalplus', 'dolbyplus', 'ddplus', 'dolby digital plus', 'dolby plus', 'dd plus', 'dolbydigitaleac3 ', 'dolbyeac3 ', 'ddeac3 ', 'dolby digital eac3 ', 'dolby eac3 ', 'dd eac3 ', 'eac3 ', 'eac 3 ', 'dolbydigitalplus ', 'dolbyplus ', 'ddplus ', 'dolby digital plus ', 'dolby plus ', 'dd plus ']]),
		('AMS|Atmos' ,											['dolbydigitalatmos', 'dolbyatmos', 'ddatmos', 'dolby digital atmos', 'dolby atmos', 'dd atmos', 'atmos', 'dolbydigitalatmos ', 'dolbyatmos ', 'ddatmos ', 'dolby digital atmos ', 'dolby atmos ', 'dd atmos ', 'atmos ']),
		('THD|TrueHD' ,											['dolbydigitaltruehd', 'dolbytruehd', 'ddtruehd', 'truehd', 'dolbydigitaltrue', 'dolbytrue', 'ddtrue', 'dolbydigitalhd', 'dolbyhd', 'dolby digital truehd', 'dolby truehd', 'dd truehd', 'dolby digital true', 'dolby true', 'dd true', 'dolby digital hd', 'true hd', 'ddhd', 'dolbydigitaltruehd ', 'dolbytruehd ', 'ddtruehd ', 'truehd ', 'dolbydigitaltrue ', 'dolbytrue ', 'ddtrue ', 'dolbydigitalhd ', 'dolbyhd ', 'dolby digital truehd ', 'dolby truehd ', 'dd truehd ', 'dolby digital true ', 'dolby true ', 'dd true ', 'dolby digital hd ', 'true hd ', 'ddhd ']),
		('PLS|Plus' ,											['dolbydigitaleac3', 'dolbyeac3', 'ddeac3', 'dolby digital eac3', 'dolby eac3', 'dd eac3', 'eac3', 'eac 3', 'dolbydigitalplus', 'dolbyplus', 'ddplus', 'dolby digital plus', 'dolby plus', 'dd plus', 'dolbydigitalp', 'dolbyp', 'dolby digital p', 'dolby p', 'ddp'

		, 'dolbydigitaleac3 ', 'dolbyeac3 ', 'ddeac3 ', 'dolby digital eac3 ', 'dolby eac3 ', 'dd eac3 ', 'eac3 ', 'eac 3 ', 'dolbydigitalplus ', 'dolbyplus ', 'ddplus ', 'dolby digital plus ', 'dolby plus ', 'dd plus ', 'dolbydigitalp ', 'dolbyp ', 'dolby digital p ', 'dolby p ', 'ddp ']),
		('LVE|Live' ,											['dolbydigitallive', 'dolbylive', 'ddlive', 'dolby digital live', 'dolby live', 'dd live', 'dolbydigitallive ', 'dolbylive ', 'ddlive ', 'dolby digital live ', 'dolby live ', 'dd live ']),
		('SEX|Surround EX' ,									['dolbydigitalsurroundex', 'dolbysurroundex', 'ddsurroundex', 'dolby digital surroundex', 'dolby surroundex', 'dd surroundex', 'dolby digital surround ex', 'dolby surround ex', 'dd surround ex', 'dolbydigitalsurroundex ', 'dolbysurroundex ', 'ddsurroundex ', 'dolby digital surroundex ', 'dolby surroundex ', 'dd surroundex ', 'dolby digital surround ex ', 'dolby surround ex ', 'dd surround ex ']),
		('EX|EX' ,												['dolbydigitalex', 'dolbyex', 'ddex', 'dolbydigitalpro', 'dolbypro', 'ddpro', 'dolby digital ex', 'dolby digital pro', 'dolby pro', 'dd pro', 'dolbydigitalex ', 'dolbyex ', 'ddex ', 'dolbydigitalpro ', 'dolbypro ', 'ddpro ', 'dolby digital ex ', 'dolby digital pro ', 'dolby pro ', 'dd pro ']),
		('AC3|Audio Codec 3' ,									['dolbydigitalac3', 'dolbyac3', 'ddac3', 'dolby digital ac3', 'dolby ac3', 'dd ac3', 'ac3', 'ac 3', 'dolbydigitalac3 ', 'dolbyac3 ', 'ddac3 ', 'dolby digital ac3 ', 'dolby ac3 ', 'dd ac3 ', 'ac3 ', 'ac 3 ']),
		('AC4|Audio Codec 4' ,									['dolbydigitalac4', 'dolbyac4', 'ddac4', 'dolby digital ac4', 'dolby ac4', 'dd ac4', 'ac4', 'ac 4', 'dolbydigitalac4 ', 'dolbyac4 ', 'ddac4 ', 'dolby digital ac4 ', 'dolby ac4 ', 'dd ac4 ', 'ac4 ', 'ac 4 ']),

		# DTS
		('70|70MM' ,											['dts70', 'dts 70', 'dts70 ', 'dts 70 ']),
		('9624|96/24' ,											['dts9624', 'dts 9624', 'dts 96 24', 'dts9624 ', 'dts 9624 ', 'dts 96 24 ']),
		('ES|Extended Surround' ,								['dtses', 'dts es', 'dtsextendedsurround', 'dts extendedsurround', 'dts extended surround', 'dtses ', 'dts es ', 'dtsextendedsurround ', 'dts extendedsurround ', 'dts extended surround ']),
		('NEO6|Neo:6' ,											['dtsneo6', 'dts neo6', 'dts neo 6', 'neo6', 'neo 6', 'dtsneo6 ', 'dts neo6 ', 'dts neo 6 ', 'neo6 ', 'neo 6 ']),
		('NEOX|Neo:X' ,											['dtsneox', 'dts neox', 'dts neo x', 'neox', 'neo x', 'dtsneox ', 'dts neox ', 'dts neo x ', 'neox ', 'neo x ']),
		('NEOPC|Neo:PC' ,										['dtsneopc', 'dts neopc', 'dts neo pc', 'neopc', 'neo pc', 'dtsneopc ', 'dts neopc ', 'dts neo pc ', 'neopc ', 'neo pc ']),
		('NEO|Neo' ,											['dtsneo', 'dts neo', 'dtsneo ', 'dts neo ']),
		('HDHRA|High Definition High Resolution Audio' ,		['dtshdhra', 'dts hdhra', 'dtshdhra ', 'dts hdhra ', 'dts hd hra', 'dts hd hra ', 'dtshighresolutionaudio', 'dts highresolutionaudio', 'dts highresolution audio', 'dtshighresolutionaudio ', 'dts highresolutionaudio ', 'dts highresolution audio ']),
		('HDMA|High Definition Master Audio' ,					['dtshdma', 'dts hdma', 'dtshdma ', 'dts hdma ', 'dts hd ma', 'dts hd ma ', 'dtsmasteraudio', 'dts masteraudio', 'dts master audio', 'dtsmasteraudio ', 'dts masteraudio ', 'dts master audio ']),
		('HD|High Definition' ,									['dtshd', 'dts hd', 'dtshd ', 'dts hd ']),
		('NX|Neural:X' ,										['dtsneuralx', 'dts neuralx', 'dts neural x', 'neuralx', 'neural x', 'dtsneuralx ', 'dts neuralx ', 'dts neural x ', 'neuralx ', 'neural x ']),
		('HX|Headphone:X' ,										['dtsheaphonex', 'dts heaphonex', 'dts heaphone x', 'heaphonex', 'heaphone x', 'dtsheaphonex ', 'dts heaphonex ', 'dts heaphone x ', 'heaphonex ', 'heaphone x ']),
		('SS|Surround Sensation' ,								['dtssurroundsensation', 'dts surroundsensation', 'dts surround sensation', 'dtssurroundsensation ', 'dts surroundsensation ', 'dts surround sensation ']),
		('CON|Connect' ,										['dtsconnect', 'dts connect', 'dtsconnect ', 'dts connect ']),
		('INA|Interactive' ,									['dtsinteractive', 'dts interactive', 'dtsinteractive ', 'dts interactive ']),
		('PYF|PlayFi' ,											['dtsplayfi', 'dts playfi', 'dts play fi', 'playfi', 'dtsplayfi ', 'dts playfi ', 'dts play fi ', 'playfi ']),
		('X|X' ,												['dtsx', 'dtsx ', 'dts x ']), # dont use 'dts x', since it will detect '... DTS x264 ...'

		# DIG
		('DRA|Dynamic Resolution Adaptation' ,					['dra', 'digirise', 'dra ', 'digirise ']),

		# MPEG
		('AAC|Advanced Audio Coding' ,							['aac', 'aacp', 'heaac', 'aac ', 'aacp ', 'heaac ', 'he aac ']),
		('MP3|Moving Picture Experts Group Audio Layer III' ,	['mp3', 'mp3 ']),
		('MP2|Moving Picture Experts Group Audio Layer II' ,	['mp2', 'mp2 ']),

		# XIPH
		('FLAC|Free Lossless Audio Codec' ,						['flac', 'flac ']),
		('OGG|Ogg' ,											['vorbis', 'vorbis ', 'ogg', 'ogg ']),

		# WIN
		('WMA|Windows Media Audio' ,							['wma', 'wma ']),

		# APP
		('ALAC|Apple Lossless Audio Codec' ,					['alac', 'ale' 'alac ', 'ale ']),

		# PCM
		('PCM|Pulse Code Modulation' ,							['lpcm', 'pcm', 'lpcm ', 'pcm ']),
	])

	DictionaryAudioDubbed = OrderedDict([
		('Dubbed' , ['dubbed', 'dubb', 'dub']),
	])

	DictionarySubtitles = OrderedDict([
		('Hard Subs' , ['hc', 'hardsubs', 'hard subs', 'hardcoded', 'hard coded', 'hardcodedsubs', 'hard coded subs']),
		('Soft Subs' , ['sub', 'subs', 'subtitle', 'sub title', 'subtitles', 'sub titles', 'ensub', 'esub', 'aarsub', 'abksub', 'acesub', 'achsub', 'adasub', 'adysub', 'afasub', 'afhsub', 'afrsub', 'ainsub', 'akasub', 'akksub', 'albsub', 'sqisub', 'alesub', 'algsub', 'altsub', 'amhsub', 'angsub', 'anpsub', 'apasub', 'arasub', 'arcsub', 'argsub', 'armsub', 'hyesub', 'arnsub', 'arpsub', 'artsub', 'arwsub', 'asmsub', 'astsub', 'athsub', 'aussub', 'avasub', 'avesub', 'awasub', 'aymsub', 'azesub', 'badsub', 'baisub', 'baksub', 'balsub', 'bamsub', 'bansub', 'baqsub', 'eussub', 'bassub', 'batsub', 'bejsub', 'belsub', 'bemsub', 'bensub', 'bersub', 'bhosub', 'bihsub', 'biksub', 'binsub', 'bissub', 'blasub', 'bntsub', 'tibsub', 'bodsub', 'bossub', 'brasub', 'bresub', 'btksub', 'buasub', 'bugsub', 'bulsub', 'bursub', 'myasub', 'bynsub', 'cadsub', 'caisub', 'carsub', 'catsub', 'causub', 'cebsub', 'celsub', 'czesub', 'cessub', 'chasub', 'chbsub', 'chesub', 'chgsub', 'chisub', 'zhosub', 'chksub', 'chmsub', 'chnsub', 'chosub', 'chpsub', 'chrsub', 'chusub', 'chvsub', 'chysub', 'cmcsub', 'copsub', 'corsub', 'cossub', 'cpesub', 'cpfsub', 'cppsub', 'cresub', 'crhsub', 'crpsub', 'csbsub', 'cussub', 'welsub', 'cymsub', 'daksub', 'dansub', 'darsub', 'daysub', 'delsub', 'densub', 'gersub', 'deusub', 'dgrsub', 'dinsub', 'divsub', 'doisub', 'drasub', 'dsbsub', 'duasub', 'dumsub', 'dutsub', 'nldsub', 'dyusub', 'dzosub', 'efisub', 'egysub', 'ekasub', 'gresub', 'ellsub', 'elxsub', 'engsub', 'enmsub', 'eposub', 'estsub', 'ewesub', 'ewosub', 'fansub', 'faosub', 'persub', 'fassub', 'fatsub', 'fijsub', 'filsub', 'finsub', 'fiusub', 'fonsub', 'fresub', 'frasub', 'frmsub', 'frosub', 'frrsub', 'frssub', 'frysub', 'fulsub', 'fursub', 'gaasub', 'gaysub', 'gbasub', 'gemsub', 'geosub', 'katsub', 'gezsub', 'gilsub', 'glasub', 'glesub', 'glgsub', 'glvsub', 'gmhsub', 'gohsub', 'gonsub', 'gorsub', 'gotsub', 'grbsub', 'grcsub', 'grnsub', 'gswsub', 'gujsub', 'gwisub', 'haisub', 'hatsub', 'hausub', 'hawsub', 'hebsub', 'hersub', 'hilsub', 'himsub', 'hinsub', 'hitsub', 'hmnsub', 'hmosub', 'hrvsub', 'hsbsub', 'hunsub', 'hupsub', 'ibasub', 'ibosub', 'icesub', 'islsub', 'idosub', 'iiisub', 'ijosub', 'ikusub', 'ilesub', 'ilosub', 'inasub', 'incsub', 'indsub', 'inesub', 'inhsub', 'ipksub', 'irasub', 'irosub', 'itasub', 'javsub', 'jbosub', 'jpnsub', 'jprsub', 'jrbsub', 'kaasub', 'kabsub', 'kacsub', 'kalsub', 'kamsub', 'kansub', 'karsub', 'kassub', 'kausub', 'kawsub', 'kazsub', 'kbdsub', 'khasub', 'khisub', 'khmsub', 'khosub', 'kiksub', 'kinsub', 'kirsub', 'kmbsub', 'koksub', 'komsub', 'konsub', 'korsub', 'kossub', 'kpesub', 'krcsub', 'krlsub', 'krosub', 'krusub', 'kuasub', 'kumsub', 'kursub', 'kutsub', 'ladsub', 'lahsub', 'lamsub', 'laosub', 'latsub', 'lavsub', 'lezsub', 'limsub', 'linsub', 'litsub', 'lolsub', 'lozsub', 'ltzsub', 'luasub', 'lubsub', 'lugsub', 'luisub', 'lunsub', 'luosub', 'lussub', 'macsub', 'mkdsub', 'madsub', 'magsub', 'mahsub', 'maisub', 'maksub', 'malsub', 'mansub', 'maosub', 'mrisub', 'mapsub', 'marsub', 'massub', 'maysub', 'msasub', 'mdfsub', 'mdrsub', 'mensub', 'mgasub', 'micsub', 'minsub', 'missub', 'mkhsub', 'mlgsub', 'mltsub', 'mncsub', 'mnisub', 'mnosub', 'mohsub', 'monsub', 'mossub', 'mulsub', 'munsub', 'mussub', 'mwlsub', 'mwrsub', 'mynsub', 'myvsub', 'nahsub', 'naisub', 'napsub', 'nausub', 'navsub', 'nblsub', 'ndesub', 'ndosub', 'ndssub', 'nepsub', 'newsub', 'niasub', 'nicsub', 'niusub', 'nnosub', 'nobsub', 'nogsub', 'nonsub', 'norsub', 'nqosub', 'nsosub', 'nubsub', 'nwcsub', 'nyasub', 'nymsub', 'nynsub', 'nyosub', 'nzisub', 'ocisub', 'ojisub', 'orisub', 'ormsub', 'osasub', 'osssub', 'otasub', 'otosub', 'paasub', 'pagsub', 'palsub', 'pamsub', 'pansub', 'papsub', 'pausub', 'peosub', 'phisub', 'phnsub', 'plisub', 'polsub', 'ponsub', 'porsub', 'prasub', 'prosub', 'pussub', 'quesub', 'rajsub', 'rapsub', 'rarsub', 'roasub', 'rohsub', 'romsub', 'rumsub', 'ronsub', 'runsub', 'rupsub', 'russub', 'sadsub', 'sagsub', 'sahsub', 'saisub', 'salsub', 'samsub', 'sansub', 'sassub', 'satsub', 'scnsub', 'scosub', 'selsub', 'semsub', 'sgasub', 'sgnsub', 'shnsub', 'sidsub', 'sinsub', 'siosub', 'sitsub', 'slasub', 'slosub', 'slksub', 'slvsub', 'smasub', 'smesub', 'smisub', 'smjsub', 'smnsub', 'smosub', 'smssub', 'snasub', 'sndsub', 'snksub', 'sogsub', 'somsub', 'sonsub', 'sotsub', 'spasub', 'srdsub', 'srnsub', 'srpsub', 'srrsub', 'ssasub', 'sswsub', 'suksub', 'sunsub', 'sussub', 'suxsub', 'swasub', 'swesub', 'sycsub', 'syrsub', 'tahsub', 'taisub', 'tamsub', 'tatsub', 'telsub', 'temsub', 'tersub', 'tetsub', 'tgksub', 'tglsub', 'thasub', 'tigsub', 'tirsub', 'tivsub', 'tklsub', 'tlhsub', 'tlisub', 'tmhsub', 'togsub', 'tonsub', 'tpisub', 'tsisub', 'tsnsub', 'tsosub', 'tuksub', 'tumsub', 'tupsub', 'tursub', 'tutsub', 'tvlsub', 'twisub', 'tyvsub', 'udmsub', 'ugasub', 'uigsub', 'ukrsub', 'umbsub', 'undsub', 'urdsub', 'uzbsub', 'vaisub', 'vensub', 'viesub', 'volsub', 'votsub', 'waksub', 'walsub', 'warsub', 'wassub', 'wensub', 'wlnsub', 'wolsub', 'xalsub', 'xhosub', 'yaosub', 'yapsub', 'yidsub', 'yorsub', 'ypksub', 'zapsub', 'zblsub', 'zensub', 'zghsub', 'zhasub', 'zndsub', 'zulsub', 'zunsub', 'zxxsub', 'zzasub', 'aarsubs', 'abksubs', 'acesubs', 'achsubs', 'adasubs', 'adysubs', 'afasubs', 'afhsubs', 'afrsubs', 'ainsubs', 'akasubs', 'akksubs', 'albsubs', 'sqisubs', 'alesubs', 'algsubs', 'altsubs', 'amhsubs', 'angsubs', 'anpsubs', 'apasubs', 'arasubs', 'arcsubs', 'argsubs', 'armsubs', 'hyesubs', 'arnsubs', 'arpsubs', 'artsubs', 'arwsubs', 'asmsubs', 'astsubs', 'athsubs', 'aussubs', 'avasubs', 'avesubs', 'awasubs', 'aymsubs', 'azesubs', 'badsubs', 'baisubs', 'baksubs', 'balsubs', 'bamsubs', 'bansubs', 'baqsubs', 'eussubs', 'bassubs', 'batsubs', 'bejsubs', 'belsubs', 'bemsubs', 'bensubs', 'bersubs', 'bhosubs', 'bihsubs', 'biksubs', 'binsubs', 'bissubs', 'blasubs', 'bntsubs', 'tibsubs', 'bodsubs', 'bossubs', 'brasubs', 'bresubs', 'btksubs', 'buasubs', 'bugsubs', 'bulsubs', 'bursubs', 'myasubs', 'bynsubs', 'cadsubs', 'caisubs', 'carsubs', 'catsubs', 'causubs', 'cebsubs', 'celsubs', 'czesubs', 'cessubs', 'chasubs', 'chbsubs', 'chesubs', 'chgsubs', 'chisubs', 'zhosubs', 'chksubs', 'chmsubs', 'chnsubs', 'chosubs', 'chpsubs', 'chrsubs', 'chusubs', 'chvsubs', 'chysubs', 'cmcsubs', 'copsubs', 'corsubs', 'cossubs', 'cpesubs', 'cpfsubs', 'cppsubs', 'cresubs', 'crhsubs', 'crpsubs', 'csbsubs', 'cussubs', 'welsubs', 'cymsubs', 'daksubs', 'dansubs', 'darsubs', 'daysubs', 'delsubs', 'densubs', 'gersubs', 'deusubs', 'dgrsubs', 'dinsubs', 'divsubs', 'doisubs', 'drasubs', 'dsbsubs', 'duasubs', 'dumsubs', 'dutsubs', 'nldsubs', 'dyusubs', 'dzosubs', 'efisubs', 'egysubs', 'ekasubs', 'gresubs', 'ellsubs', 'elxsubs', 'engsubs', 'enmsubs', 'eposubs', 'estsubs', 'ewesubs', 'ewosubs', 'fansubs', 'faosubs', 'persubs', 'fassubs', 'fatsubs', 'fijsubs', 'filsubs', 'finsubs', 'fiusubs', 'fonsubs', 'fresubs', 'frasubs', 'frmsubs', 'frosubs', 'frrsubs', 'frssubs', 'frysubs', 'fulsubs', 'fursubs', 'gaasubs', 'gaysubs', 'gbasubs', 'gemsubs', 'geosubs', 'katsubs', 'gezsubs', 'gilsubs', 'glasubs', 'glesubs', 'glgsubs', 'glvsubs', 'gmhsubs', 'gohsubs', 'gonsubs', 'gorsubs', 'gotsubs', 'grbsubs', 'grcsubs', 'grnsubs', 'gswsubs', 'gujsubs', 'gwisubs', 'haisubs', 'hatsubs', 'hausubs', 'hawsubs', 'hebsubs', 'hersubs', 'hilsubs', 'himsubs', 'hinsubs', 'hitsubs', 'hmnsubs', 'hmosubs', 'hrvsubs', 'hsbsubs', 'hunsubs', 'hupsubs', 'ibasubs', 'ibosubs', 'icesubs', 'islsubs', 'idosubs', 'iiisubs', 'ijosubs', 'ikusubs', 'ilesubs', 'ilosubs', 'inasubs', 'incsubs', 'indsubs', 'inesubs', 'inhsubs', 'ipksubs', 'irasubs', 'irosubs', 'itasubs', 'javsubs', 'jbosubs', 'jpnsubs', 'jprsubs', 'jrbsubs', 'kaasubs', 'kabsubs', 'kacsubs', 'kalsubs', 'kamsubs', 'kansubs', 'karsubs', 'kassubs', 'kausubs', 'kawsubs', 'kazsubs', 'kbdsubs', 'khasubs', 'khisubs', 'khmsubs', 'khosubs', 'kiksubs', 'kinsubs', 'kirsubs', 'kmbsubs', 'koksubs', 'komsubs', 'konsubs', 'korsubs', 'kossubs', 'kpesubs', 'krcsubs', 'krlsubs', 'krosubs', 'krusubs', 'kuasubs', 'kumsubs', 'kursubs', 'kutsubs', 'ladsubs', 'lahsubs', 'lamsubs', 'laosubs', 'latsubs', 'lavsubs', 'lezsubs', 'limsubs', 'linsubs', 'litsubs', 'lolsubs', 'lozsubs', 'ltzsubs', 'luasubs', 'lubsubs', 'lugsubs', 'luisubs', 'lunsubs', 'luosubs', 'lussubs', 'macsubs', 'mkdsubs', 'madsubs', 'magsubs', 'mahsubs', 'maisubs', 'maksubs', 'malsubs', 'mansubs', 'maosubs', 'mrisubs', 'mapsubs', 'marsubs', 'massubs', 'maysubs', 'msasubs', 'mdfsubs', 'mdrsubs', 'mensubs', 'mgasubs', 'micsubs', 'minsubs', 'missubs', 'mkhsubs', 'mlgsubs', 'mltsubs', 'mncsubs', 'mnisubs', 'mnosubs', 'mohsubs', 'monsubs', 'mossubs', 'mulsubs', 'munsubs', 'mussubs', 'mwlsubs', 'mwrsubs', 'mynsubs', 'myvsubs', 'nahsubs', 'naisubs', 'napsubs', 'nausubs', 'navsubs', 'nblsubs', 'ndesubs', 'ndosubs', 'ndssubs', 'nepsubs', 'newsubs', 'niasubs', 'nicsubs', 'niusubs', 'nnosubs', 'nobsubs', 'nogsubs', 'nonsubs', 'norsubs', 'nqosubs', 'nsosubs', 'nubsubs', 'nwcsubs', 'nyasubs', 'nymsubs', 'nynsubs', 'nyosubs', 'nzisubs', 'ocisubs', 'ojisubs', 'orisubs', 'ormsubs', 'osasubs', 'osssubs', 'otasubs', 'otosubs', 'paasubs', 'pagsubs', 'palsubs', 'pamsubs', 'pansubs', 'papsubs', 'pausubs', 'peosubs', 'phisubs', 'phnsubs', 'plisubs', 'polsubs', 'ponsubs', 'porsubs', 'prasubs', 'prosubs', 'pussubs', 'quesubs', 'rajsubs', 'rapsubs', 'rarsubs', 'roasubs', 'rohsubs', 'romsubs', 'rumsubs', 'ronsubs', 'runsubs', 'rupsubs', 'russubs', 'sadsubs', 'sagsubs', 'sahsubs', 'saisubs', 'salsubs', 'samsubs', 'sansubs', 'sassubs', 'satsubs', 'scnsubs', 'scosubs', 'selsubs', 'semsubs', 'sgasubs', 'sgnsubs', 'shnsubs', 'sidsubs', 'sinsubs', 'siosubs', 'sitsubs', 'slasubs', 'slosubs', 'slksubs', 'slvsubs', 'smasubs', 'smesubs', 'smisubs', 'smjsubs', 'smnsubs', 'smosubs', 'smssubs', 'snasubs', 'sndsubs', 'snksubs', 'sogsubs', 'somsubs', 'sonsubs', 'sotsubs', 'spasubs', 'srdsubs', 'srnsubs', 'srpsubs', 'srrsubs', 'ssasubs', 'sswsubs', 'suksubs', 'sunsubs', 'sussubs', 'suxsubs', 'swasubs', 'swesubs', 'sycsubs', 'syrsubs', 'tahsubs', 'taisubs', 'tamsubs', 'tatsubs', 'telsubs', 'temsubs', 'tersubs', 'tetsubs', 'tgksubs', 'tglsubs', 'thasubs', 'tigsubs', 'tirsubs', 'tivsubs', 'tklsubs', 'tlhsubs', 'tlisubs', 'tmhsubs', 'togsubs', 'tonsubs', 'tpisubs', 'tsisubs', 'tsnsubs', 'tsosubs', 'tuksubs', 'tumsubs', 'tupsubs', 'tursubs', 'tutsubs', 'tvlsubs', 'twisubs', 'tyvsubs', 'udmsubs', 'ugasubs', 'uigsubs', 'ukrsubs', 'umbsubs', 'undsubs', 'urdsubs', 'uzbsubs', 'vaisubs', 'vensubs', 'viesubs', 'volsubs', 'votsubs', 'waksubs', 'walsubs', 'warsubs', 'wassubs', 'wensubs', 'wlnsubs', 'wolsubs', 'xalsubs', 'xhosubs', 'yaosubs', 'yapsubs', 'yidsubs', 'yorsubs', 'ypksubs', 'zapsubs', 'zblsubs', 'zensubs', 'zghsubs', 'zhasubs', 'zndsubs', 'zulsubs', 'zunsubs', 'zxxsubs', 'zzasubs']),
	])

	DictionarySeeds = OrderedDict([
		('Seed' , ['seed']),
	])

	DictionaryAge = OrderedDict([
		('Day' , ['day']),
	])

	DictionarySize = OrderedDict([
		('B' , ['b']),
		('KB' , ['kb', 'kib']),
		('MB' , ['mb', 'mib']),
		('GB' , ['gb', 'gib']),
		('TB' , ['tb', 'tib']),
	])

	DictionaryIgnore = OrderedDict([
		('Extras' , ['extra', 'extras']),
		('Soundtrack' , ['ost', 'soundtrack', 'soundtracks', 'thememusic', 'theme music', 'themesong', 'themesongs', 'theme song', 'theme songs', 'album', 'albums', 'mp3', 'flac']),
		('Trailer' , ['trailer', 'trailers', 'preview', 'previews']),
	])

	def __init__(self, name = None, title = None, year = None, season = None, episode = None, pack = None, packCount = None, link = None, quality = None, size = None, languageAudio = None, seeds = None, age = None, popularity = None, source = None):
		# So that they can be overwritten by providers
		self.mIgnoreDifference = Metadata.IgnoreDifference
		self.mIgnoreContains = Metadata.IgnoreContains
		self.mIgnoreLength = Metadata.IgnoreLength
		self.mIgnoreSize = Metadata.IgnoreSize

		self.mInfo = None

		self.mName = None
		self.mNameProcessed = None
		self.mNameSplit = None
		self.mNameReduced = None

		self.mTitle = None
		self.mTitleProcessed = None
		self.mTitleSplit = None

		self.mYear = None
		self.mSeason = None
		self.mEpisode = None
		self.mPack = None
		self.mPackCount = None

		self.mTorrent = None
		self.mUsenet = None
		self.mHoster = None
		self.mOrion = None
		self.mLocal = None
		self.mDirect = None
		self.mPremium = None
		self.mLink = None
		self.mSize = None
		self.mEdition = None

		self.mDebrid = {}
		self.mCache = {}

		self.mRelease = None
		self.mUploader = None

		self.mVideoQuality = None
		self.mVideoCodec = None
		self.mVideoExtra = None

		self.mSubtitles = None

		self.mAudioLanguages = None
		self.mAudioDubbed = None
		self.mAudioChannels = None
		self.mAudioSystem = None
		self.mAudioCodec = None

		self.mPrecheck = None
		self.mSeeds = None
		self.mAge = None
		self.mPopularity = None

		self.load(name = name, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = link, quality = quality, size = size, languageAudio = languageAudio, seeds = seeds, age = age, popularity = popularity, source = source)

	@classmethod
	def serialize(self, metadata):
		return tools.Converter.base64To(tools.Converter.serialize(metadata)).replace('\n', '').replace('\r', '')

	@classmethod
	def unserialize(self, metadata):
		return tools.Converter.unserialize(tools.Converter.base64From(metadata))

	@classmethod
	def initialize(self, source, name = None, title = None, year = None, season = None, episode = None, pack = None, packCount = None, link = None, quality = None, size = None, languageAudio = None, seeds = None, age = None, popularity = None, force = False, initialize = False, update = False):
		created = False
		if not 'metadata' in source or not source['metadata'] or not isinstance(source['metadata'], Metadata):
			if 'metabase' in source and source['metabase']:
				source['metadata'] = self.unserialize(source['metabase'])
			else:
				created = True
				source['metadata'] = Metadata(name = name, title = title, year = year, season = season, episode = episode, pack = pack, packCount = packCount, link = link, quality = quality, size = size, languageAudio = languageAudio, seeds = seeds, age = age, popularity = popularity, source = source)
		if update and not created:
			source['metadata'].update(source)
		if initialize and (force or not 'metabase' in source or not source['metabase']):
			source['metabase'] = self.serialize(source['metadata'])
		return source['metadata']

	@classmethod
	def uninitialize(self, source, base = True):
		if base and (not 'metabase' in source or not source['metabase']):
			source['metabase'] = self.serialize(source['metadata'])
		if 'metadata' in source:
			del source['metadata']

	# Do not resolve the link by default, since this takes a long time.
	# Resolving it does not really add any benefit, since the link can't be copied.
	@classmethod
	def showDialog(self, source, metadata, resolve = False):
		try:
			items = []
			unknown = 'Unknown'
			standard = 'Standard'
			local = 'Local'
			yes = 'Yes'
			no = 'No'

			stream = None
			if 'urlresolved' in source:
				stream = source['urlresolved']

			file = None
			if 'file' in source and not source['file'] == None:
				# Remove non-ASCII characters, since Kodi can't display them and will not show the dialog.
				file = source['file'].encode('ascii', errors = 'ignore').strip()
			hash = None
			if 'hash' in source:
				try: hash = source['hash'].upper()
				except: hash = source['hash']

			title = source['tvshowtitle'] if 'tvshowtitle' in source else source['title']
			try: title = tools.Media.titleUniversal(metadata = metadata, title = title, encode = True)
			except: title = unknown # Exact searches
			meta = self.initialize(name = file, title = title, source = source)

			debrid = no
			if 'debrid' in source:
				for i in source['debrid'].itervalues():
					if i:
						debrid = yes
						break

			release = None
			if meta.release():
				full = meta.release(full = True)
				abbreviation = meta.release(full = False)
				if full and abbreviation: release = '%s (%s)' % (full, abbreviation)
				elif full: release = full
				elif abbreviation: release = abbreviation

			uploader = meta.uploader()
			if uploader: uploader = ', '.join(uploader)

			pack = None
			if not meta.mPack == None:
				pack = yes if meta.mPack else no

			if meta.size():
				if meta.size(estimate = True) == meta.size(estimate = False):
					size = meta.size(format = True)
				else:
					size = '%s (%s)' % (meta.size(format = True, estimate = True), meta.size(format = True, estimate = False))
			else:
				size = unknown

			audioLanguages = meta.audioLanguages()
			if not audioLanguages or audioLanguages[0] == tools.Language.UniversalCode:
				audioLanguages = unknown
			else:
				audioLanguages = ', '.join([i[1] for i in meta.audioLanguages()])

			audioSystem = None
			if meta.audioSystem():
				full = meta.audioSystem(full = True)
				abbreviation = meta.audioSystem(full = False)
				if full and abbreviation: audioSystem = '%s (%s)' % (full, abbreviation)
				elif full: audioSystem = full
				elif abbreviation: audioSystem = abbreviation

			audioCodec = None
			if meta.audioCodec():
				full = meta.audioCodec(full = True)
				abbreviation = meta.audioCodec(full = False)
				if full and abbreviation: audioCodec = '%s (%s)' % (full, abbreviation)
				elif full: audioCodec = full
				elif abbreviation: audioCodec = abbreviation

			if resolve:
				try: link = network.Networker().resolve(source, clean = True, resolve = network.Networker.ResolveProvider)
				except: link = meta.link()
				link = network.Networker(link).link() # Clean link.
				if not link or link == '':
					link = stream
			else:
				link = source['url']

			origin = None
			if 'origin' in source:
				origin = source['origin']
				if origin:
					origin = origin.capitalize()
					if 'orion' in source: origin += ' (Orion)'
			if not origin and 'orion' in source: origin = 'Orion'

			theSource = ''
			if 'local' in source and source['local']:
				theSource = local
			elif not source['source'] == None and not source['source'] == '0':
				theSource = source['source']
			index = theSource.find('.')
			if index >= 0: theSource = theSource[:index]

			def splitLine(text, characters = 45):
				if text:
					return re.sub("(.{" + str(characters) + "})", "\\1\n", text, 0, re.DOTALL)
				else:
					return None

			# Item Details
			items.append({
				'title' : 'Item Details',
				'items' : [
					{'title' : 'Title', 'value' : title},
					{'title' : 'Edition', 'value' : meta.edition() if meta.edition() else standard},
					{'title' : 'Release', 'value' : release if release else unknown},
					{'title' : 'Uploader', 'value' : uploader if uploader else unknown},
					{'title' : 'Pack', 'value' : pack if pack else unknown},
					{'title' : 'Size', 'value' : size},
					{'title' : 'File', 'value' : file if file else unknown},
					{'title' : 'Hash', 'value' : hash if hash else unknown},
				]
			})

			# Video Details
			items.append({
				'title' : 'Video Details',
				'items' : [
					{'title' : 'Quality', 'value' : meta.videoQuality() if meta.videoQuality() else unknown},
					{'title' : 'Codec', 'value' : meta.videoCodec() if meta.videoCodec() else unknown},
					{'title' : '3D', 'value' : yes if meta.videoExtra() == '3D' else no},
				]
			})

			# Audio Details
			items.append({
				'title' : 'Audio Details',
				'items' : [
					{'title' : 'Language', 'value' : audioLanguages},
					{'title' : 'Dubbed', 'value' : yes if meta.audioDubbed() else no},
					{'title' : 'System', 'value' : audioSystem if audioSystem else unknown},
					{'title' : 'Codec', 'value' : audioCodec if audioCodec else unknown},
					{'title' : 'Channels', 'value' : str(meta.audioChannels()) if meta.audioChannels() else unknown},
				]
			})

			# Subtitles
			items.append({
				'title' : 'Subtitle Details',
				'items' : [
					{'title' : 'Subtitles', 'value' : yes if meta.subtitles() else no},
					{'title' : 'Soft Coded', 'value' : yes if 'soft' in meta.subtitles().lower() else no} if meta.subtitles() else None,
					{'title' : 'Hard Coded', 'value' : yes if 'hard' in meta.subtitles().lower() else no} if meta.subtitles() else None,
				]
			})

			# Stream Details
			items.append({
				'title' : 'Stream Details',
				'items' : [
					{'title' : 'Origin', 'value' : origin if origin else unknown},
					{'title' : 'Provider', 'value' : interface.Format.font(source['provider'], capitalcase = True)},
					{'title' : 'Source', 'value' : interface.Format.font(theSource, capitalcase = True)},
					{'title' : 'Local', 'value' : yes if meta.local() else no},
					{'title' : 'Debrid', 'value' : debrid},
					{'title' : 'Direct', 'value' : yes if meta.direct() else no},
					{'title' : 'Cached', 'value' : yes if meta.cached() else no},
					{'title' : 'Seeds', 'value' : str(meta.seeds())} if not meta.seeds() is None else None,
					{'title' : 'Age', 'value' : meta.age(True)} if not meta.age() is None else None,
					{'title' : 'Popularity', 'value' : meta.popularity(format = True)} if not meta.popularity() is None else None,
					{'title' : 'Link', 'value' : link, 'link' : True},
					{'title' : 'Stream', 'value' : stream, 'link' : True} if stream else None,
				]
			})

			# Dialog
			interface.Loader.hide()
			interface.Dialog.information(title = 'Stream Details', items = items)
		except:
			tools.Logger.error()

	@classmethod
	def foreign(self, title, umlaut = False):
		return tools.Converter.unicode(string = title, umlaut = umlaut)

	@classmethod
	def videoResolutionQuality(self, width = 0, height = 0):
		threshold = 20 # Some videos are a bit smaller.
		if width:
			if width >= 7680 - threshold: return 'HD8K'
			elif width >= 6144 - threshold: return 'HD6K'
			elif width >= 3840 - threshold: return 'HD4K'
			elif width >= 2048 - threshold: return 'HD2K'
			elif width >= 1920 - threshold: return 'HD1080'
			elif width >= 1280 - threshold: return 'HD720'
			elif width >= 1: return 'SD'
		if height:
			if height >= 4320 - threshold: return 'HD8K'
			elif height >= 3160 - threshold: return 'HD6K'
			elif height >= 2160 - threshold: return 'HD4K'
			elif height >= 1200 - threshold: return 'HD2K' # Increase, because the same as HD1080.
			elif height >= 1080 - threshold: return 'HD1080'
			elif height >= 720 - threshold: return 'HD720'
			elif height >= 1: return 'SD'
		return None

	@classmethod
	def videoQualityResolution(self, quality):
		if quality == 'HD720': return 1280, 720
		elif quality == 'HD1080': return 1920, 1080
		elif quality == 'HD2K': return 2048, 1080
		elif quality == 'HD4K': return 3840, 2160
		elif quality == 'HD6K': return 6144, 3160
		elif quality == 'HD8K': return 7680, 4320
		else: return 720, 480

	@classmethod
	def videoQualityConvert(self, quality):
		quality = quality.lower()
		for key, value in Metadata.DictionaryVideoQuality.iteritems():
			if quality == key.lower():
				return key
			else:
				if len(value) > 1 and isinstance(value[0], list) and not isinstance(value[0], basestring):
					 pass # Ignore SCR1080, SCR720, CAM1080, CAM720
				elif quality in value:
					return key
		return Metadata.VideoQualityDefault

	def videoQualityRange(self, quality, qualityFrom = None, qualityTo = None):
		if quality == None:
			return False

		quality = Metadata.VideoQualityOrder.index(quality)
		qualityFrom = self.videoQualityIndex(qualityFrom)
		qualityTo = self.videoQualityIndex(qualityTo)

		# In case the qualities were passed in the wrong order.
		if not qualityFrom == None and not qualityTo == None and qualityFrom > qualityTo:
			temporary = qualityFrom
			qualityFrom = qualityTo
			qualityTo = temporary

		if not qualityFrom == None and quality < qualityFrom:
			return False
		if not qualityTo == None and quality > qualityTo:
			return False
		return True

	def videoQualityIndex(self, quality):
		if quality == None or isinstance(quality, (int, long)):
			return quality
		else:
			return Metadata.VideoQualityOrder.index(quality)

	def setType(self, type):
		if type == Metadata.TypeLocal: self.mLocal = True
		elif type == Metadata.TypePremium: self.mPremium = True
		elif type == Metadata.TypeTorrent: self.mTorrent = True
		elif type == Metadata.TypeUsenet: self.mUsenet = True
		elif type == Metadata.TypeHoster: self.mHoster = True

	def setOrion(self, orion):
		self.mOrion = orion

	def setRelease(self, release):
		self.mRelease = release

	def setUploader(self, uploader):
		if isinstance(uploader, basestring):
			self.mUploader = [uploader]
		elif isinstance(uploader, (list, tuple)):
			self.mUploader = uploader
		else:
			self.mUploader = uploader

	def setEdition(self, edition):
		if isinstance(edition, basestring):
			edition = edition.lower()
			for key, value in Metadata.DictionaryEdition.iteritems():
				if edition in value:
					self.mEdition = key
					break
		else:
			self.mEdition = edition

	def setVideoQuality(self, quality, direct = False):
		if direct: self.mVideoQuality = quality
		else: self.mVideoQuality = self.__searchFind(quality, Metadata.DictionaryVideoQuality)

	def setVideoCodec(self, codec):
		self.mVideoCodec = self.__searchFind(codec, Metadata.DictionaryVideoCodec)

	def setVideo3D(self, video3d):
		if video3d == True:
			self.mVideoExtra = list(Metadata.DictionaryVideoExtra)[0]
		else:
			self.mVideoExtra = self.__searchFind(video3d, Metadata.DictionaryVideoExtra)

	def setAudioLanguages(self, languages):
		if self.mAudioLanguages == None:
			self.mAudioLanguages = []
		if isinstance(languages, list):
			self.mAudioLanguages.extend([tools.Language.language(i) for i in languages])
		else:
			self.mAudioLanguages.extend([tools.Language.language(languages)])
		if len(self.mAudioLanguages) > 1:
			self.mAudioLanguages = list(set(self.mAudioLanguages))
			if len(self.mAudioLanguages) > 1:
				result = []
				for i in range(len(self.mAudioLanguages)):
					if not tools.Language.isUniversal(self.mAudioLanguages[i]):
						if tools.Language.isEnglish(self.mAudioLanguages[i]):
							result.insert(0, self.mAudioLanguages[i])
						else:
							result.append(self.mAudioLanguages[i])
				self.mAudioLanguages = result

		self.mAudioLanguages = list(set(self.mAudioLanguages))
		self.mAudioLanguages = [i for i in self.mAudioLanguages if i]
		if len(self.mAudioLanguages) > 0:
			languages = []
			for i in range(len(self.mAudioLanguages)): # Move English to front.
				if tools.Language.isEnglish(self.mAudioLanguages[i]):
					languages.append(self.mAudioLanguages[i])
					del self.mAudioLanguages[i]
					break
			self.mAudioLanguages = languages + self.mAudioLanguages

	def setAudioChannels(self, channels):
		if isinstance(channels, numbers.Number):
			channels = str(channels) + 'CH'
		self.mAudioChannels = self.__searchFind(channels, Metadata.DictionaryAudioChannels)

	def setAudioSystem(self, system = None):
		if system == None and not self.mAudioCodec == None:
			codec = self.mAudioCodec.split('|')[0].lower()
			for key, values in Metadata.DictionaryAudioSystemReference.iteritems():
				if codec in values:
					system = key
					break
		if system == None: self.mAudioSystem = self.__searchExtract(Metadata.DictionaryAudioSystem)
		else: self.mAudioSystem = self.__searchFind(system, Metadata.DictionaryAudioSystem)

	def setAudioCodec(self, codec):
		lower = codec.lower()
		if lower == 'dd' or lower == 'dts':
			self.mAudioCodec = None
			self.setAudioSystem(codec)
		else:
			self.mAudioCodec = self.__searchFind(codec, Metadata.DictionaryAudioCodec)
			if self.mAudioSystem  == None: self.setAudioSystem()

	def setAudioDubbed(self, dubbed = True):
		self.mAudioDubbed = Metadata.DictionaryAudioDubbed[0][0] if dubbed else None

	def setSubtitles(self, subtitles):
		self.mSubtitles = self.__searchFind(subtitles, Metadata.DictionarySubtitles)

	def setSubtitlesSoft(self, enable = True):
		if enable:
			self.mSubtitles = list(Metadata.DictionarySubtitles)[1]

	def setSubtitlesHard(self, enable = True):
		if enable:
			self.mSubtitles = list(Metadata.DictionarySubtitles)[0]

	def setDirect(self, direct):
		self.mDirect = direct

	def setLink(self, link):
		# Some scrapers like FilmPalast return a ID array (which is resolved later) instead of a link. In such a case, do not use it.
		if isinstance(link, basestring):
			self.mLink = link
		else:
			self.mLink = ''

	def setName(self, name):
		self.mName = name
		try: self.mName = re.sub(' +', ' ', self.mName.replace('\r', '').replace('\n', ' ')).strip()
		except: pass

	def setSize(self, size):
		# Size can be bytes or string.
		self.mSize = self.__loadSize(size)

	def setSeeds(self, seeds):
		try: self.mSeeds = int(seeds)
		except: pass

	def setAge(self, age):
		self.mAge = age

	def setPopularity(self, popularity):
		self.mPopularity = popularity

	def setPack(self, pack):
		self.mPack = pack

	def increaseSeeds(self, seeds):
		try:
			if seeds == None: return
			elif self.mSeeds == None: self.mSeeds = seeds
			else: self.mSeeds = max(seeds, self.mSeeds)
		except: pass

	def name(self):
		return self.mName

	# full: If true, returns full name, if false, returns abbreviation. If None, return string with both.
	def release(self, full = None):
		try:
			if full == None or self.mRelease == None: return self.mRelease
			elif not '|' in self.mRelease: return None
			elif full == True: return self.mRelease.split('|')[1]
			elif full == False: return self.mRelease.split('|')[0]
		except: return None

	# full: If true, returns full names of all uploaders, if false, returns first uploader. If None, return tuple with both.
	def uploader(self, full = None):
		try:
			if full == None: return self.mUploader
			elif not self.mUploader == None and len(self.mUploader) > 0:
				if full == True: return '-'.join(self.mUploader)
				elif full == False: return self.mUploader[0]
			return None
		except: return None

	def videoQuality(self, kodi = False):
		if kodi:
			if self.mVideoQuality:
				return self.videoQualityResolution(self.mVideoQuality)
			return self.videoQualityResolution('SD')
		else:
			return self.mVideoQuality

	def videoCodec(self, kodi = False):
		if kodi and self.mVideoCodec:
			return self.mVideoCodec.lower()
		else:
			return self.mVideoCodec

	def videoExtra(self):
		return self.mVideoExtra

	def videoExtra3d(self):
		return self.mVideoExtra == '3D'

	def audioLanguages(self, universal = False):
		if not self.mAudioLanguages: return self.mAudioLanguages
		elif universal: return self.mAudioLanguages
		else: return tools.Language.ununiversalze(self.mAudioLanguages)

	def audioDubbed(self, boolean = True):
		if boolean: return not(self.mAudioDubbed == False or self.mAudioDubbed == None or self.mAudioDubbed == '')
		else: return self.mAudioDubbed

	def audioChannels(self, number = False):
		if number and self.mAudioChannels:
			return int(self.mAudioChannels.replace('CH', ''))
		else:
			return self.mAudioChannels

	def audioSystem(self, full = None):
		try:
			if full == None or self.mAudioSystem == None: return self.mAudioSystem
			elif not '|' in self.mAudioSystem: return None
			elif full == True: return self.mAudioSystem.split('|')[1]
			elif full == False: return self.mAudioSystem.split('|')[0]
		except: return None

	def audioCodec(self, full = None):
		try:
			result = None
			if full == None or self.mAudioCodec == None: result = self.mAudioCodec
			elif not '|' in self.mAudioCodec: result = None
			elif full == True: result = self.mAudioCodec.split('|')[1]
			elif full == False: result = self.mAudioCodec.split('|')[0]
			return result
		except: return None

	def audioSystemCodec(self, kodi = False):
		if kodi:
			system = self.audioSystem(full = False)
			if system == 'DTS': return system
			elif system == 'DD': return 'AC3'
			else: return self.audioCodec(full = False)
		else:
			result = ''
			system = self.audioSystem(full = False)
			codec = self.audioCodec(full = False)
			if system and (system == 'DD' or system == 'DTS'):
				result += system
			if codec:
				if result: result += '-'
				result += codec
			return result

	def subtitles(self):
		return self.mSubtitles

	def subtitlesIsSoft(self):
		if self.mSubtitles: return 'soft' in self.mSubtitles.lower()
		else: return False

	def subtitlesIsHard(self):
		if self.mSubtitles: return 'hard' in self.mSubtitles.lower()
		else: return False

	def orion(self):
		return self.mOrion == True

	def local(self):
		return self.mLocal == True

	def direct(self):
		return self.mDirect == True

	def debrid(self, any = True):
		if any:
			for i in self.mDebrid.itervalues():
				if i: return True
			return False
		else:
			return self.mDebrid

	def premium(self):
		return self.mPremium == True

	def cached(self, any = True):
		if any:
			for i in self.mCache.itervalues():
				if i: return True
			return False
		else:
			return self.mCache

	def link(self):
		return self.mLink

	def edition(self):
		return self.mEdition

	def __size(self, estimate = False):
		if self.mSize and estimate and self.mPack and not self.mPackCount == None and self.mPackCount > 1: return int(self.mSize / self.mPackCount)
		else: return self.mSize

	def size(self, format = False, color = False, estimate = False, duration = None):
		if format:
			result = self.__formatSize(estimate = estimate)
			if color and duration: result = interface.Format.font(result, color = self.__colorSize(self.__size(estimate = estimate), duration), uppercase = True)
			return result
		else:
			return self.__size(estimate = estimate)

	def seeds(self, format = False, color = False, label = LabelFull):
		if format:
			result = self.__formatSeeds(label = label)
			if color: result = interface.Format.font(result, color = self.__colorSeeds(), uppercase = True)
			return result
		else:
			return self.mSeeds

	def age(self, format = False, color = False, label = LabelFull):
		if format:
			result = self.__formatAge(label = label)
			if color: result = interface.Format.font(result, color = self.__colorAge(), uppercase = True)
			return result
		else:
			return self.mAge

	def popularity(self, format = False, color = False, label = LabelFull):
		if format:
			result = self.__formatPopularity(label = label)
			if color: result = interface.Format.font(result, color = self.__colorPopularity(), uppercase = True)
			return result
		else:
			return self.mPopularity

	def season(self):
		return self.mSeason

	def episode(self):
		return self.mEpisode

	def pack(self):
		return self.mPack == True

	def precheck(self):
		if self.mPrecheck == network.Networker.StatusOnline or self.cached() or self.mSeeds >= 10:
			return network.Networker.StatusOnline
		else:
			return self.mPrecheck

	def isEpisode(self):
		return (not self.mSeason == None and not self.mEpisode == None) or re.match('s\d{2,}e\d{2,}', self.mTitleProcessed) or re.match('s\d{2,}e\d{2,}', self.mNameProcessed)

	def isPack(self):
		return self.mPack == True

	def isHoster(self):
		return self.mHoster == True or (self.mHoster == None and (not self.isTorrent() and not self.isUsenet() and not self.isLocal() and not self.isPremium()))

	def isTorrent(self):
		return self.mTorrent == True

	def isUsenet(self):
		return self.mUsenet == True

	def isLocal(self):
		return self.local()

	def isPremium(self):
		return self.premium()

	def type(self):
		if self.isLocal(): return Metadata.TypeLocal
		elif self.isPremium(): return Metadata.TypePremium
		elif self.isTorrent(): return Metadata.TypeTorrent
		elif self.isUsenet(): return Metadata.TypeUsenet
		elif self.isHoster(): return Metadata.TypeHoster
		else: return Metadata.TypeNone

	# extended: adds metadata to title
	# prefix: adds Gaia name to the front
	def title(self, extended = False, prefix = False, raw = False, pack = False):
		title = self.mTitle

		if raw: return title

		if not self.mSeason == None and not self.mEpisode == None:
			if pack:
				try: title += ' S%02d' % int(self.mSeason)
				except: pass
			else:
				try: title += ' S%02dE%02d' % (int(self.mSeason), int(self.mEpisode))
				except: pass

		if prefix:
			title = '[' + tools.System.name().upper() + '] ' + title

		if extended:
			metadata = []

			if self.mVideoQuality: metadata.append(self.mVideoQuality)
			if self.mVideoExtra: metadata.append(self.mVideoExtra)
			if self.mEdition: metadata.append(self.mEdition)
			if self.mVideoCodec: metadata.append(self.mVideoCodec)
			audio = self.__formatAudio(format = False)
			if audio: metadata.append(audio)
			if self.mSubtitles: metadata.append(self.mSubtitles)

			if len(metadata) > 0:
				title += ' [' + ', '.join(metadata) + ']'

		return title

	@classmethod
	def labelFill(self, value, bold = True, color = interface.Format.ColorDisabled):
		if value: return value
		else: return interface.Format.font(Metadata.Fill, bold = bold, color = color, translate = False)

	def labelOrion(self, format = True, color = interface.Format.ColorOrion, bold = True, uppercase = True):
		label = None
		if self.orion():
			from resources.lib.extensions import orionoid
			label = orionoid.Orionoid.Name
			if format:
				label = interface.Format.font(label, bold = bold, color = color, uppercase = uppercase)
		return label

	def labelType(self, format = True, color = interface.Format.ColorMain, bold = True, uppercase = True, setting = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.type')
		if setting > 0:
			if self.mTorrent == True: label = 'torrent'
			elif self.mUsenet == True: label = 'usenet'
			elif self.mLocal == True: label = 'local'
			elif self.mPremium == True: label = 'premium'
			else: label = 'hoster'
			if setting == 1: label = label[:1]
			elif setting == 2: label = label[:3]
			if not label == None and format:
				label = interface.Format.font(label, bold = bold, color = color, uppercase = uppercase)
		return label

	def labelCached(self, format = True, color = interface.Format.ColorSpecial, bold = True, uppercase = True, setting = None, handles = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.mode')
		if not setting == Metadata.LabelNone:
			if self.cached():
				from resources.lib.extensions import handler
				if handles == None: handles = handler.Handler.handles()
				if setting == Metadata.LabelMini: label = 'C'
				elif setting == Metadata.LabelShort: label = 'CHD'
				else: label = 'CACHED'
				if not handler.Handler.handlesSingleCache():
					label += '-'
					for handle in handles:
						try:
							if self.mCache[handle['id']]: label += handle['abbreviation']
						except: pass
			if not label == None and format:
				label = interface.Format.font(label, color = color, bold = bold, uppercase = uppercase)
		return label

	def labelDebrid(self, format = True, color = interface.Format.ColorSpecial, bold = True, uppercase = True, setting = None, handles = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.mode')
		if not setting == Metadata.LabelNone:
			if self.debrid():
				from resources.lib.extensions import handler
				if handles == None: handles = handler.Handler.handles()
				if setting == Metadata.LabelMini: label = 'D'
				elif setting == Metadata.LabelShort: label = 'DEB'
				else: label = 'DEBRID'
				if not handler.Handler.handlesSingleHoster():
					label += '-'
					for handle in handles:
						try:
							if self.mDebrid[handle['id']]: label += handle['abbreviation']
						except: pass
			if not label == None and format:
				label = interface.Format.font(label, color = interface.Format.colorLighter(color = color, change = 30), bold = bold, uppercase = uppercase)
		return label

	def labelDirect(self, format = True, color = interface.Format.ColorSpecial, bold = True, uppercase = True, setting = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.mode')
		if not setting == Metadata.LabelNone:
			if self.mPremium == True or self.mLocal == True or self.mDirect == True:
				if setting == Metadata.LabelMini: label = 'DR'
				elif setting == Metadata.LabelShort: label = 'DIR'
				else: label = 'DIRECT'
				if self.mLocal == True: color = interface.Format.colorDarker(color = color, change = 20)
				elif self.mPremium == True: color = interface.Format.colorDarker(color = color, change = 10)
				else: color = interface.Format.colorLighter(color = color, change = 10)
			if not label == None and format:
				label = interface.Format.font(label, color = color, bold = bold, uppercase = uppercase)
		return label

	def labelOpen(self, format = True, color = interface.Format.ColorSpecial, bold = True, uppercase = True, setting = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.mode')
		if not setting == Metadata.LabelNone:
			if not(self.mPremium == True or self.mLocal == True or self.mDirect == True or self.cached() or self.debrid()):
				if setting == Metadata.LabelMini: label = 'OP'
				elif setting == Metadata.LabelShort: label = 'OPN'
				else: label = 'OPEN'
			if not label == None and format:
				label = interface.Format.font(label, color = interface.Format.colorLighter(color = color, change = 50), bold = bold, uppercase = uppercase)
		return label

	def labelAccess(self, format = True, color = interface.Format.ColorSpecial, bold = True, uppercase = True, setting = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.mode')
		if not setting == Metadata.LabelNone:
			from resources.lib.extensions import handler
			handles = handler.Handler.handles()
			if self.mPremium == True or self.mLocal == True or self.mDirect == True:
				label = self.labelDirect(format = format, color = color, bold = bold, uppercase = uppercase, setting = setting)
			elif self.cached():
				label = self.labelCached(format = format, color = color, bold = bold, uppercase = uppercase, setting = setting, handles = handles)
			elif self.debrid():
				label = self.labelDebrid(format = format, color = color, bold = bold, uppercase = uppercase, setting = setting, handles = handles)
			else:
				label = self.labelOpen(format = format, color = color, bold = bold, uppercase = uppercase, setting = setting)
		return label

	def labelEdition(self, format = True, color = interface.Format.ColorAlternative, bold = False, uppercase = True, setting = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.edition')
		if self.mEdition and not self.isEpisode():
			try:
				label = self.mEdition
				if setting == Metadata.LabelMini: label = label[:2]
				elif setting == Metadata.LabelShort: label = label[:3]
				if not label == None and format:
					label = interface.Format.font(label, color = color, bold = bold, uppercase = uppercase)
			except: pass
		return label

	def labelPack(self, format = True, color = interface.Format.ColorAlternative, bold = False, uppercase = True, setting = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.pack')
		if not setting == Metadata.LabelNone and self.pack():
			if setting == Metadata.LabelMini: label = 'PK'
			elif setting == Metadata.LabelShort: label = 'PCK'
			else: label = 'PACK'
			if not label == None and format:
				label = interface.Format.font(label, color = color, bold = bold, uppercase = uppercase)
		return label

	def labelRelease(self, format = True, color = None, bold = False, uppercase = True, setting = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.release')
		if not setting == Metadata.LabelNone and self.release():
			try:
				if setting == Metadata.LabelMini: label = self.release(full = False)[:2]
				elif setting == Metadata.LabelShort: label = self.release(full = False)
				else: label = self.release(full = True)
			except: pass
			if not label == None and format:
				label = interface.Format.font(label, color = color, bold = bold, uppercase = uppercase)
		return label

	def labelUploader(self, format = True, color = None, bold = False, uppercase = True, setting = None):
		label = None
		if setting == None:
			setting = tools.Settings.getInteger('interface.information.uploader')
		if not setting == Metadata.LabelNone and self.uploader():
			try:
				if setting == Metadata.LabelMini: label = self.uploader(full = True)[:2]
				elif setting == Metadata.LabelShort: label = self.uploader(full = True)[:3]
				else: label = self.uploader(full = True)
			except: pass
			if not label == None and format:
				label = interface.Format.font(label, color = color, bold = bold, uppercase = uppercase)
		return label

	def labelVideoExtra(self, format = True, color = True, bold = False, uppercase = True):
		label = self.videoExtra()
		if not label == None and format:
			label = interface.Format.font(label, color = interface.Format.ColorPoor, bold = bold, uppercase = uppercase)
		return label

	def labelAudioDubbed(self, format = True, color = True, bold = False, uppercase = True):
		label = self.audioDubbed(False)
		if not label == None and format:
			label = interface.Format.font(label, color = interface.Format.ColorPoor, bold = bold, uppercase = uppercase)
		return label

	def labelSubtitles(self, format = True, color = True, bold = False, uppercase = True):
		label = self.subtitles()
		if not label == None and format:
			if color == True: color = interface.Format.ColorBad if list(Metadata.DictionarySubtitles)[0] == self.mSubtitles else None
			label = interface.Format.font(label, color = color, bold = bold, uppercase = uppercase)
		return label

	# If sizeLimit == True, will use the default size limit.
	def information(self, format = False, sizeLimit = True, precheck = False, information = InformationAll, quality = LabelFull, mode = LabelFull, pack = LabelFull, release = LabelFull, uploader = LabelFull, edition = LabelFull, color = True, popularity = LabelNone, age = LabelNone, seeds = LabelNone, duration = None):
		try:
			values = []
			if information == Metadata.InformationAll or information == Metadata.InformationEssential:
				from resources.lib.extensions import handler

				if precheck:
					check = self.precheck()
					if check == network.Networker.StatusOnline:
						values.append(interface.Format.font(' + ', bold = True, color = interface.Format.ColorExcellent if color else None))
					elif check == network.Networker.StatusOffline:
						values.append(interface.Format.font(' - ', bold = True, color = interface.Format.ColorBad if color else None))
					else:
						values.append(interface.Format.font(' = ', bold = True, color = interface.Format.ColorMedium if color else None))

				if not quality == Metadata.LabelNone and self.mVideoQuality:
					if quality == Metadata.LabelMini:
						mini = ['CM', 'CM', 'CM', 'SC', 'SC', 'SC', 'SD', '1K', '2K', '2K', '4K', '6K', '8K']
						label = mini[Metadata.VideoQualityOrder.index(self.mVideoQuality)]
					elif quality == Metadata.LabelShort:
						short = ['CAM', 'CAM', 'CAM', 'SCR', 'SCR', 'SCR', 'SD', '720', '1080', '2K', '4K', '6K', '8K']
						label = short[Metadata.VideoQualityOrder.index(self.mVideoQuality)]
					else:
						label = self.mVideoQuality
					if format: values.append(interface.Format.font(label, color = self.__colorVideoQuality() if color else None, bold = True, uppercase = True))
					else: values.append(label)

				label = self.labelAccess()
				if label: values.append(label)

				label = self.labelPack()
				if label: values.append(label)

			if information == Metadata.InformationAll or information == Metadata.InformationNonessential:
				label = self.labelEdition()
				if label: values.append(label)

				label = self.labelVideoExtra()
				if label: values.append(label)

				label = self.labelRelease()
				if label: values.append(label)

				label = self.labelUploader()
				if label: values.append(label)

			if information == Metadata.InformationAll or information == Metadata.InformationNonessential:
				if self.mVideoCodec:
					if format: values.append(interface.Format.font(self.mVideoCodec, uppercase = True))
					else: values.append(self.mVideoCodec)

				audio = self.__formatAudio(format = format)
				if audio:
					if format: values.append(interface.Format.font(audio, uppercase = True))
					else: values.append(audio)

				label = self.labelSubtitles()
				if label: values.append(label)

				if sizeLimit == True: sizeLimit = self.mIgnoreSize
				if self.mSize and self.mSize > sizeLimit:
					if format: values.append(self.size(format = True, color = True, duration = duration))
					else: values.append(self.__formatSize(estimate = True))

				if popularity:
					popularityValue = self.popularity()
					if popularityValue:
						if format: values.append(self.popularity(format = True, color = True, label = popularity))
						else: values.append(popularityValue)

				if age:
					ageValue = self.age()
					if ageValue:
						if format: values.append(self.age(format = True, color = True, label = age))
						else: values.append(ageValue)

				if seeds:
					seedsValue = self.seeds()
					if seedsValue:
						if format: values.append(self.seeds(format = True, color = True, label = seeds))
						else: values.append(seedsValue)

			values = interface.Format.fontSeparator().join(filter(None, values))
			return values
		except:
			tools.Logger.error()

	def __matchSequential(self, main, sub):
		try:
			if isinstance(main, list): main = ' '.join(main)
			if isinstance(sub, list): sub = ' '.join(sub)
			return sub in main
		except:
			return False

	def __matchClean(self, value):
		value = re.sub('(\.|\(|\[|\s)(\d{4}|S\d*E\d*|S\d*|3D)(\.|\)|\]|\s|)', '', value.upper())
		value = re.sub(r'[^\w]', '', value)
		return cleantitle.get(value).lower()

	def __match(self):
		# Match the parts of the title with the name, since self.__match() is not enough. Eg Detective Conan (anime) S19E01 gets True Detective episodes.
		try:
			if not self.__containsEpisode():
				return False
			if not self.__containsTitle():
				return False

			# Ignore this for now, since it filters out too much, like Taboo S01E01.
			#if not self.__matchTitle():
			#	return False

			return True
		except:
			return False

	def __matchTitle(self):
		value1 = self.__matchClean(self.mNameProcessed)
		value2 = self.__matchClean(self.mTitleProcessed)
		if SequenceMatcher(None, value1, value2).ratio() >= self.mIgnoreDifference:
			return True
		elif len(value1) > len(value2) * 2:
			# Sometimes there are very long strings before or after the actual name, causing a non-match. Divide the string into 2 and check each part.
			# Only do this for long strings, becasue short string almost always give a good match if just a few characters match.
			split = -((-len(value1))//2)
			difference = self.mIgnoreDifference
			if len(value2) < 30: # Increase the requirnments for short titles, because the typically have a high match rate.
				difference = min(0.8, difference * 2)
			return SequenceMatcher(None, value1[:split], value2).ratio() >= difference or SequenceMatcher(None, value1[split:], value2).ratio() >= difference
		return False

	def seasonNames(self, season = None):
		if season == None:
			return Metadata.Seasons
		else:
			season = int(season)
			seasons = Metadata.Seasons
			for i in range(seasons):
				seasons[i] = seasons[i] % season
		return seasons

	def seasonContains(self, title, season):
		if season == None: return True # For movies
		title = title.lower()
		processedTitle, splitTitle = self.__loadValue(title)
		joinedTitle = ' '.join(splitTitle)
		season = int(season)
		for i in Metadata.Seasons:
			seasonValue = i % season
			if self.__matchSequential(joinedTitle, seasonValue) and not re.search(Metadata.SeasonsExclude, title):
				return True
		return False

	def episodeNames(self, season = None, episode = None):
		if season == None or episode == None:
			return Metadata.Episodes
		else:
			season = int(season)
			episode = int(episode)
			episodes = Metadata.Episodes
			for i in range(episodes):
				try: episodes[i] = episodes[i] % (season, episode)
				except: episodes[i] = episodes[i] % episode
		return episodes

	def episodeContains(self, title, season, episode):
		if season == None or episode == None: return True # For movies
		processedTitle, splitTitle = self.__loadValue(title)
		joinedTitle = ' '.join(splitTitle)
		season = int(season)
		episode = int(episode)
		for i in Metadata.Episodes:
			try: name = i % (season, episode)
			except: name = i % episode
			processedEpisode, splitEpisode = self.__loadValue(name, splitAll = False)
			if self.__matchSequential(joinedTitle, splitEpisode):
				return True
		return False

	def __containsEpisode(self):
		# Must always match the episode number.
		if self.mSeason == None or self.mEpisode == None: # Eg: movie, does not contain season/episode.
			return True

		splitName = self.mNameSplit
		joinedName = ' '.join(splitName)

		# Ignore for season packs:
		if self.mPack:
			for i in Metadata.Seasons:
				seasonValue = i % self.mSeason
				if self.__matchSequential(joinedName, seasonValue) and not re.search(Metadata.SeasonsExclude, self.mTitleProcessed):
					return True
		else:
			for i in Metadata.Episodes:
				try: name = i % (self.mSeason, self.mEpisode)
				except: name = i % self.mEpisode
				processedEpisode, splitEpisode = self.__loadValue(name, splitAll = False)
				if self.__matchSequential(joinedName, splitEpisode):
					return True

		return False

	def __containsTitle(self):
		total = len(self.mTitleSplit)
		split = copy.deepcopy(self.mNameSplit)
		count = 0

		# Check if the file name does not contain too many words.
		# Otherwise "Wonder 2017" will mostly detect "Wonder Woman 2017" links.
		# Only check until the year, ignore everything after the year (eg: uploader, metadata, etc).
		skip = False
		if self.mSeason == None and self.mEpisode == None:
			try: index = split.index(str(self.mYear))
			except: index = -1
			if index > 0:
				skip = index > total * self.mIgnoreLength

		setting = tools.Settings.getInteger('scraping.providers.filename')
		for i in self.mTitleSplit:
			try:
				index = split.index(i)
				count += 1
				if setting == 1: split.remove(i)
				elif setting == 2: split = split[index + 1:]
			except: pass
		percentage = count / float(total)

		if total <= 2: # Short titles
			return percentage >= (self.mIgnoreContains * 1.25) and not skip
		else:
			return percentage >= self.mIgnoreContains and not skip

	def ignore(self, size = True, seeds = True):
		# Ignore if the title and name do not correspond.
		if not self.__match():
			return True

		for value in Metadata.DictionaryIgnore.itervalues():
			if self.__searchContains(value):
				return True

		# Ignore small files.
		if size and self.mSize < self.mIgnoreSize:
			return True

		# Ignore torrents with no seeds.
		if seeds and self.mSeeds == 0:
			return True

		return False

	def load(self, name = None, title = None, year = None, season = None, episode = None, pack = None, packCount = None, link = None, quality = None, size = None, languageAudio = None, seeds = None, age = None, popularity = None, source = None):
		try:
			if source:

				if name and not name == '':
					self.mName = name
				if isinstance(source, dict) and 'url' in source:
					self.setLink(source['url'])
					if name == None or name == '':
						self.mName = self.mLink.rsplit('/', 1)[-1]
						if not '.' in self.mName or re.match('^[a-zA-Z0-9]*$', self.mName) or re.match('^[a-zA-Z0-9]{16,}$', self.mName) or re.match('^[0-9]{6,}$', self.mName): # Links that end with a hash or random strings should not be used.
							self.mName = None
				if not self.mName: self.mName = ''
				self.setName(self.mName)

				self.mTitle = title
				if not self.mTitle:
					self.mTitle = ''

				if 'year' in source:
					self.mYear = int(source['year'])

				if 'season' in source:
					self.mSeason = int(source['season'])

				if 'episode' in source:
					self.mEpisode = int(source['episode'])

				if 'pack' in source:
					self.mPack = bool(source['pack'])

				if 'packCount' in source:
					self.mPackCount = int(source['packCount'])

				if 'local' in source:
					self.mLocal = source['local']
				else:
					self.mLocal = False

				if 'premium' in source:
					self.mPremium = source['premium']
				else:
					self.mPremium = False

				if 'source' in source and source['source'] == Metadata.TypeTorrent:
					self.mTorrent = True
				else:
					self.mTorrent = False

				if 'source' in source and source['source'] == Metadata.TypeUsenet:
					self.mUsenet = True
				else:
					self.mUsenet = False

				if not self.mLocal and not self.mPremium and not self.mTorrent and not self.mUsenet:
					self.mHoster = True
				else:
					self.mHoster = False

				if 'orion' in source:
					self.mOrion = True
				else:
					self.mOrion = False

				if 'direct' in source:
					self.mDirect = source['direct']
				else:
					self.mDirect = False

				if 'debrid' in source:
					self.mDebrid = source['debrid']
					if self.mDebrid == None: self.mDebrid = {}
				else:
					self.mDebrid = {}

				if 'cache' in source:
					self.mCache = source['cache']
					if self.mCache == None: self.mCache = {}
				else:
					self.mCache = {}

				if not languageAudio == None:
					self.setAudioLanguages(languageAudio)
				elif 'language' in source:
					self.setAudioLanguages(source['language'])

				if isinstance(source, basestring):
					self.mInfo = source
				elif isinstance(source, dict) and 'info' in source:
					self.mInfo = source['info']

				if not self.mInfo or self.mInfo == '':
					self.mInfo = None
				else:
					try: self.mInfo = [i.lower() for i in self.mInfo.split(interface.Format.fontSeparator())]
					except: self.mInfo = None

				if 'precheck' in source:
					self.mPrecheck = source['precheck']

				if quality and not quality == '':
					self.mVideoQuality = self.videoQualityConvert(quality.replace(' ', '').lower())
				elif isinstance(source, dict) and 'quality' in source:
					self.mVideoQuality = self.videoQualityConvert(source['quality'].replace(' ', '').lower())
			else:
				self.mName = name
				if not self.mName: self.mName = ''
				self.setName(self.mName)
				self.mTitle = title
				if not self.mTitle: self.mTitle = ''

				self.mYear = None if year == None else int(year)
				self.mSeason = None if season == None else int(season)
				self.mEpisode = None if episode == None else int(episode)
				self.mPack = None if pack == None else bool(pack)
				self.mPackCount = None if packCount == None else int(packCount)

				self.setLink(link)
				self.setSize(size)
				self.setAudioLanguages(languageAudio)
				self.setSeeds(seeds)
				self.setAge(age)
				self.setPopularity(popularity)
				self.setVideoQuality(quality)

			self.__loadValues()
			self.__extract()
		except:
			tools.Logger.error()

	def update(self, source):
		try:
			if 'year' in source:
				self.mYear = int(source['year'])

			if 'season' in source:
				self.mSeason = int(source['season'])

			if 'episode' in source:
				self.mEpisode = int(source['episode'])

			if 'pack' in source:
				self.mPack = bool(source['pack'])

			if 'packCount' in source:
				self.mPackCount = int(source['packCount'])

			if 'local' in source:
				self.mLocal = source['local']
			else:
				self.mLocal = False

			if 'premium' in source:
				self.mPremium = source['premium']
			else:
				self.mPremium = False

			if source['source'] == Metadata.TypeTorrent:
				self.mTorrent = True
			else:
				self.mTorrent = False

			if source['source'] == Metadata.TypeUsenet:
				self.mUsenet = True
			else:
				self.mUsenet = False

			if not self.mLocal and not self.mPremium and not self.mTorrent and not self.mUsenet:
				self.mHoster = True
			else:
				self.mHoster = False

			if 'orion' in source:
				self.mOrion = True
			else:
				self.mOrion = False

			if 'direct' in source:
				self.mDirect = source['direct']
			else:
				self.mDirect = False

			if 'debrid' in source:
				self.mDebrid = source['debrid']
				if self.mDebrid == None: self.mDebrid = {}
			else:
				self.mDebrid = {}

			if 'cache' in source:
				self.mCache = source['cache']
				if self.mCache == None: self.mCache = {}
			else:
				self.mCache = {}

			if 'language' in source:
				self.setAudioLanguages(source['language'])

			if 'precheck' in source:
				self.mPrecheck = source['precheck']

			if 'quality' in source:
				self.mVideoQuality = self.videoQualityConvert(source['quality'].replace(' ', '').lower())

			if self.mName == None:
				if 'file' in source:
					self.mName = source['file']
				elif 'url' in source:
					self.setLink(source['url'])
					self.mName = self.mLink.rsplit('/', 1)[-1]
					if re.match('^[a-zA-Z0-9]*$', self.mName) or re.match('^[a-zA-Z0-9]{16,}$', self.mName) or re.match('^[0-9]{6,}$', self.mName): # Links that end with a hash or random strings should not be used.
						self.mName = None
				if not self.mName: self.mName = ''
				self.setName(self.mName)
				self.__loadValues()
				self.__extract()
		except:
			tools.Logger.error()

	# Loads from the HTTP and file headers.
	def loadHeaders(self, linkOrNetworker, timeout = 30):
		try:
			if isinstance(linkOrNetworker, basestring):
				linkOrNetworker = network.Networker(linkOrNetworker)
			self.loadHeadersHttp(linkOrNetworker, timeout = int(timeout / 3))
			if linkOrNetworker.check(content = True, retrieveHeaders = False) == network.Networker.StatusOnline: # Do not check metadata that is HTML or cannot be retrieved.
				self.loadHeadersFile(linkOrNetworker, timeout = timeout)
		except:
			pass

	# Loads from the HTTP headers.
	def loadHeadersHttp(self, linkOrNetworker, timeout = 30):
		try:
			if isinstance(linkOrNetworker, basestring):
				linkOrNetworker = network.Networker(linkOrNetworker)

			size = linkOrNetworker.headerSize()
			if size:
				if size > self.mIgnoreSize:
					self.setSize(size)

			type = linkOrNetworker.headerType(timeout = timeout)
			name = linkOrNetworker.headerName(timeout = timeout)

			if not type and not name:
				name = None
			elif type and name:
				name += ' ' + type
			elif type:
				name = type
			else:
				name = ''

			self.mName = name
			self.setName(self.mName)
			self.__loadValues()
			self.__extract()
		except:
			pass

	# Loads from the file headers.
	def loadHeadersFile(self, linkOrNetworker, timeout = 30):
		try:
			if not isinstance(linkOrNetworker, basestring):
				linkOrNetworker = linkOrNetworker.link()

			meta = Extractor().extract(linkOrNetworker, timeout = timeout)

			if isinstance(linkOrNetworker, basestring):
				if tools.File.exists(linkOrNetworker):
					self.mSize = tools.File.size(linkOrNetworker)

			if meta:
				# File
				# Do this first, because value like video quality will be overwritten later.
				if not self.mName or self.mName == '':
					self.mName = ''
					if 'name' in meta:
						self.mName += meta['name']
					if 'mime' in meta:
						self.mName += ' ' + meta['mime']
					self.setName(self.mName)
					if not self.mName == '':
						self.__loadValues()
						self.__extract()
				if not self.mSize or self.mSize == 0:
					if 'size' in meta:
						self.mSize = meta['size']

				# Video
				if 'video' in meta:
					# Video Quality
					if 'width' in meta['video']: width = meta['video']['width']
					else: width = 0
					if 'height' in meta['video']: height = meta['video']['height']
					else: height = 0
					if width > 0 or height > 0:
						self.setVideoQuality(self.videoResolutionQuality(width, height))
					# Video Codec
					if 'codec' in meta['video']:
						self.setVideoCodec(meta['video']['codec'])

				# Audio
				if 'audio' in meta:
					# Audio Codec
					if 'codec' in meta['audio']:
						self.setAudioCodec(meta['audio']['codec'])
					# Audio Codec
					if 'system' in meta['audio']:
						self.setAudioSystem(meta['audio']['system'])
					elif 'codec' in meta['audio']:
						self.setAudioSystem()
					# Audio Channels
					if 'channels' in meta['audio']:
						self.setAudioChannels(meta['audio']['channels'])

				# Subtitle
				if 'subtitle' in meta and meta['subtitle']:
					self.setSubtitlesSoft(True)
		except:
			pass

	def __loadValues(self):
		self.mNameProcessed, self.mNameSplit = self.__loadValue(self.mName)
		self.mTitleProcessed, self.mTitleSplit = self.__loadValue(self.mTitle)

		# This is needed, otherwise the audio channels are detected as 8CH in a string link "S10E07 1080p".
		self.mNameReduced = ' '.join(self.mNameSplit)
		for split in self.mTitleSplit:
			self.mNameReduced = self.mNameReduced.replace(split, '')
		if not self.mSeason == None or not self.mEpisode == None:
			self.mNameReduced = re.sub('[sS]\d{1,5}[eE]\d{1,5}|[sS]\d{1,5}', '', self.mNameReduced)

	def __loadValue(self, value, splitAll = True):
		if value:
			value = value.lower()
			value = client.replaceHTMLCodes(value)
			value = value.replace("\n", '') # Double quotes with escape characters.
			if splitAll: split = [item for item in re.split('\.|\,|\(|\)|\[|\]|\s|\-|\_|\+|\/|\\\'|\"', value) if not item == '']
			else: split = [item for item in re.split('\s', value) if not item == '']
			return value, split
		else:
			return '', []

	def __loadSize(self, size):
		try:
			if size == None:
				return size
			elif isinstance(size, numbers.Number):
				return int(size)
			elif size.replace(' ', '').isdigit():
				return int(size.replace(' ', ''))
			else:
				size = size.lower()
				bytes = 0

				units = list(Metadata.DictionarySize)
				unitsAll = []
				for unit in units: unitsAll.extend(Metadata.DictionarySize[unit])

				if any(i in unitsAll for i in size):
					bytes = self.__loadNumber(size)
					unit = re.sub('[^a-zA-Z]', '', size)
					if any(unit in i for i in Metadata.DictionarySize[units[1]]): bytes *= 1024
					elif any(unit in i for i in Metadata.DictionarySize[units[2]]): bytes *= 1048576
					elif any(unit in i for i in Metadata.DictionarySize[units[3]]): bytes *= 1073741824
					elif any(unit in i for i in Metadata.DictionarySize[units[4]]): bytes *= 1099511627776

				return int(bytes)
		except:
			return None

	def __loadNumber(self, value):
		return float(re.sub('[^0-9\.]', '', value))

	def __searchFind(self, item, dictionary):
		if not item: return None
		item = item.lower()
		for key, value in dictionary.iteritems():
			if len(value) > 0 and isinstance(value[0], list):
				counter = 0
				for i in range(len(value)):
					for w in value[i]:
						if item in w or w in item:
							counter += 1
							break
					if counter <= i: break
				if counter == len(value):
					return key
			else:
				for v in value:
					if item in v or v in item:
						return key
		return None

	def __searchExtract(self, dictionary, multiple = False):
		multiples = []
		for key, value in dictionary.iteritems():
			if len(value) > 1 and isinstance(value[0], list) and not isinstance(value[0], basestring):
				contains = True
				for v in value:
					if not self.__searchContains(v):
						contains = False
						break
				if contains:
					if multiple: multiples.append(key)
					else: return key
			else:
				if self.__searchContains(value):
					if multiple: multiples.append(key)
					else: return key

		if multiple and len(multiples) > 0: return multiples
		else: return None

	def __searchContains(self, values = []):
		# If a value contains a space, it will compare it against the full file name (not the split) and also try it with .,+-_
		#   Eg: '5 1' -> '5 1', '5.1', '5,1', '5+1', '5-1', '5_1'
		# If the value starts/ends with a space, it compares against the full file name, with the space trimmed.
		#   Eg: '5 ' -> '5'
		try:
			values = self.__searchRemove(values)
			for value in values:
				if value.startswith(' ') or value.endswith(' '):
					if len(value) > 3:
						if value.replace(' ', '') in self.mNameReduced:
							return True
					elif value.replace(' ', '') in self.mNameSplit:
						return True
				elif ' ' in value:
					if any(i in self.mNameReduced for i in [value, value.replace(' ', '.'), value.replace(' ', ','), value.replace(' ', '+'), value.replace(' ', '-'), value.replace(' ', '_')]):
						return True
				elif value in self.mNameSplit:
					return True
			return None
		except:
			return None

	def __searchRemove(self, values = []):
		# Remove words from the values that are present in the title.
		values = [i.lower() for i in values]
		if self.mTitleSplit:
			for split in self.mTitleSplit:
				result = []
				for value in values:
					if not value == split:
						result.append(value)
				values = result
		return values

	def __searchLanguages(self, language = None):
		results = []
		try:
			if language == None:
				return results
			elif len(language) <= 1:
				try: result = tools.Language.language(language[0][0])
				except: result = None
				if result == None or tools.Language.isUniversal(result[0]):
					languages = tools.Language.detection()

					# Do not use a language that appears in the title, eg: "French Love"
					titleContains = False
					for l in languages:
						for t in self.mTitleSplit:
							if l == t:
								titleContains = True
								break
						if titleContains: break

					if not titleContains:
						for l in languages:
							for n in self.mNameSplit:
								if l == n:
									results.append(tools.Language.language(l))
				else:
					results = language
			elif len(language) > 1:
				results = [tools.Language.language(l[0]) for l in language]
		except:
			tools.Logger.error()

		return results

	def __extract(self):
		self.mEdition = self.__searchExtract(Metadata.DictionaryEdition)

		self.mRelease = self.__searchExtract(Metadata.DictionaryReleases)
		self.mUploader = self.__searchExtract(Metadata.DictionaryUploaders, multiple = True)

		if self.mVideoQuality == None or self.mVideoQuality == '':
			self.mVideoQuality = self.__searchExtract(Metadata.DictionaryVideoQuality)
			if not self.mVideoQuality: self.mVideoQuality = Metadata.VideoQualityDefault

		self.mVideoCodec = self.__searchExtract(Metadata.DictionaryVideoCodec)
		self.mVideoExtra = self.__searchExtract(Metadata.DictionaryVideoExtra)

		self.mSubtitles = self.__searchExtract(Metadata.DictionarySubtitles)

		self.setAudioLanguages(self.__searchLanguages(self.mAudioLanguages))
		self.mAudioDubbed = self.__searchExtract(Metadata.DictionaryAudioDubbed)

		self.mAudioChannels = self.__searchExtract(Metadata.DictionaryAudioChannels)
		self.mAudioCodec = self.__searchExtract(Metadata.DictionaryAudioCodec)
		self.setAudioSystem()
		self.__processAudio()

	def __processAudio(self):
		if not self.mAudioChannels:
			codec = self.audioCodec(full = False)
			if codec == 'AAC' or codec == 'MP3' or codec == 'FLAC' or codec == 'OGG' or codec == 'WMA' or codec == 'PMC':
				self.mAudioChannels = '2CH'
			if not self.mAudioChannels:
				system = self.audioSystem(full = False)
				if system == 'DD' or system == 'DTS' or system == 'DRA':
					self.mAudioChannels = '6CH'

	def __colorVideoQuality(self):
		qualities = list(Metadata.DictionaryVideoQuality)
		if self.mVideoQuality == Metadata.VideoQualityUltra:
			return interface.Format.colorLighter(interface.Format.ColorBad, 60)
		elif self.mVideoQuality == qualities[0]:
			return interface.Format.colorLighter(interface.Format.ColorBad, 40)
		elif self.mVideoQuality == qualities[1]:
			return interface.Format.colorLighter(interface.Format.ColorBad, 20)
		elif self.mVideoQuality == qualities[2]:
			return interface.Format.ColorBad
		elif self.mVideoQuality == qualities[3]:
			return interface.Format.colorLighter(interface.Format.ColorPoor, 40)
		elif self.mVideoQuality == qualities[4]:
			return interface.Format.colorLighter(interface.Format.ColorPoor, 20)
		elif self.mVideoQuality == qualities[5]:
			return interface.Format.ColorPoor
		elif self.mVideoQuality == qualities[6]:
			return interface.Format.colorDarker(interface.Format.ColorUltra, 40)
		elif self.mVideoQuality == qualities[7]:
			return interface.Format.colorDarker(interface.Format.ColorUltra, 20)
		elif self.mVideoQuality == qualities[8]:
			return interface.Format.ColorUltra
		elif self.mVideoQuality == qualities[9]:
			return interface.Format.colorLighter(interface.Format.ColorUltra, 20)
		elif self.mVideoQuality == qualities[10]:
			return interface.Format.ColorExcellent
		elif self.mVideoQuality == qualities[11]:
			return interface.Format.ColorGood
		elif self.mVideoQuality == qualities[12]:
			return interface.Format.ColorMedium
		else:
			return interface.Format.ColorUltra

	def __colorSubtitles(self):
		if list(Metadata.DictionarySubtitles)[0] == self.mSubtitles:
			return interface.Format.ColorBad
		else:
			return None

	def __colorSize(self, size, duration):
		if size == None:
			return None
		else:
			size /= duration
			size = int((size - Metadata.SizeMinimum) / Metadata.SizeStep)

			# Adjust size according to quality where HD1080 is the base.
			if self.mVideoQuality == 'HD8K': size *= 0.125
			elif self.mVideoQuality == 'HD6K': size *= 0.17
			elif self.mVideoQuality == 'HD4K': size *= 0.25
			elif self.mVideoQuality == 'HD2K': size *= 0.5
			elif self.mVideoQuality == 'HD720': size *= 2.25
			elif not self.mVideoQuality == 'HD1080': size *= 6
			size = int(size)

			colors = interface.Format.colorGradientDecrease(Metadata.SizeCount)
			if size >= len(colors): return colors[-1]
			elif size < 0: return colors[0]
			else: return colors[size]

	def __colorSeeds(self):
		if self.mSeeds == None:
			return None
		else:
			colors = interface.Format.colorGradientIncrease(50)
			if self.mSeeds >= len(colors): return colors[-1]
			else: return colors[self.mSeeds]

	def __colorAge(self):
		if self.mAge == None:
			return None
		else:
			colors = interface.Format.colorGradientDecrease(730)
			if self.mAge >= len(colors): return colors[-1]
			else: return colors[self.mAge]

	def __colorPopularity(self):
		colors = interface.Format.colorGradientIncrease(90)
		if not self.mPopularity == None:
			popularity = int(self.mPopularity * 100)
			if popularity >= len(colors): return colors[-1]
			else: return colors[popularity]
		try: return colors[0]
		except: return None

	def __formatAccess(self, access, services):
		try:
			from resources.lib.extensions import handler
			if not isinstance(services, list): services = [services]
			handles = handler.Handler.handles()
			result = []
			for service in services:
				service = service.lower()
				for handle in handles:
					if handle['id'] == service:
						result.append(handle['abbreviation'])
						break
			if len(result) > 0: return access.upper() + '-' + ''.join(result)
		except: pass
		return None

	def __formatCached(self, services):
		return self.__formatAccess('CACHED', services)

	def __formatDebrid(self, services):
		return self.__formatAccess('DEBRID', services)

	def __formatAudio(self, format = False):
		try:
			systemCodec = ''
			result = []
			if self.mAudioChannels:
				result.append(self.mAudioChannels)
			if self.audioSystem() and (self.audioSystem(full = False) == 'DD' or self.audioSystem(full = False) == 'DTS'):
				systemCodec += self.audioSystem(full = False)
			if self.audioCodec():
				if systemCodec: systemCodec += '-'
				systemCodec += self.audioCodec(full = False)
			if systemCodec:
				result.append(systemCodec)
			if self.audioDubbed():
				result.append(self.labelAudioDubbed(format = format))
			audioLanguages = self.audioLanguages()
			if audioLanguages:
				languages = []
				for l in audioLanguages:
					if l: languages.append(l[0].upper())
				if len(languages) > 1 or (len(languages) == 1 and not tools.Language.isUniversal(languages[0])):
					if len(languages) == 1:
						result.append(languages[0])
					else:
						label = tools.Settings.getInteger('interface.language.stream')
						if label == 0: result.append('-'.join(languages))
						else: result.append(interface.Translation.string(35035))
			if len(result) == 0: return None
			else: return ' '.join(result)
		except:
			tools.Logger.error()

	def __formatSize(self, estimate = False):
		if self.mSize:
			estimated = ''
			size = self.mSize
			if estimate and self.mPack and (self.mPackCount == None or self.mPackCount > 1):
				estimated = '~ '
				size = self.__size(estimate = estimate)

			units = list(Metadata.DictionarySize)
			if size < 1024:
				sizeUnit = units[0]
				sizeValue = size
				sizePlaces = 0
			elif size < 1048576:
				sizeUnit = units[1]
				sizeValue = size / 1024.0
				sizePlaces = 0
			elif size < 1073741824:
				sizeUnit = units[2]
				sizeValue = size / 1048576.0
				sizePlaces = 0
			elif size < 1099511627776:
				sizeUnit = units[3]
				sizeValue = size / 1073741824.0
				sizePlaces = 1
			else:
				sizeUnit = units[4]
				sizeValue = size / 1099511627776.0
				sizePlaces = 2

			return ('%s%.*f %s') % (estimated, sizePlaces, sizeValue, sizeUnit)
		else:
			return None

	def __formatSeeds(self, label = LabelFull):
		if label == Metadata.LabelNone:
			return None
		elif not self.mSeeds is None:
			seeds = str(self.mSeeds)
			if label == Metadata.LabelMini: return seeds
			if label == Metadata.LabelShort: return seeds + list(Metadata.DictionarySeeds)[0][:1].upper()
			seeds += ' ' + list(Metadata.DictionarySeeds)[0]
			if self.mSeeds == 0 or self.mSeeds > 1: seeds += 's'
			return seeds
		else:
			return None

	def __formatAge(self, label = LabelFull):
		if label == Metadata.LabelNone:
			return None
		elif not self.mAge is None:
			age = str(self.mAge)
			if label == Metadata.LabelMini: return age
			if label == Metadata.LabelShort: return age + list(Metadata.DictionaryAge)[0][:1].upper()
			age += ' ' + list(Metadata.DictionaryAge)[0]
			if self.mAge == 0 or self.mAge > 1: age += 's'
			return age
		else:
			return None

	def __formatPopularity(self, label = LabelFull):
		if label == Metadata.LabelNone:
			return None
		elif not self.mPopularity is None:
			popularity = int(self.mPopularity * 100)
			popularity = str(popularity)
			if label == Metadata.LabelMini: return popularity
			popularity += '%'
			if label == Metadata.LabelShort: return popularity
			popularity = '+' + popularity
			return popularity
		else:
			return None


# Online resources:
#	MetaInfo: +- 50KB
#	FFmpeg: +- 300KB - 400KB
#	Manual: +- 250KB
#	Samba/Network: 3MB

class Extractor(object):

	CommandInitialized = False
	CommandMediainfo = None
	CommandFfmpeg = None

	SizeOnline = 256000 # 250KB
	SizeLocal = 5242880 # 5MB

	def __init__(self, sizeMaximum = SizeOnline): # sizeMaximum is the maximum size to retrive if the file is online.
		self.mTemporaryPath = None
		self.mSizeMaximum = sizeMaximum
		if self.mSizeMaximum <= sizeMaximum:
			self.mSizeChunk = int(math.floor(self.mSizeMaximum / 4))
		else:
			self.mSizeChunk = int(math.floor(self.mSizeMaximum / 8))

		if not Extractor.CommandInitialized:
			Extractor.CommandMediainfo = self.__detectMediainfo()
			if Extractor.CommandMediainfo:
				Extractor.CommandMediainfo += self.__parametersMediainfo()
			Extractor.CommandFfmpeg = self.__detectFfmpeg()
			if Extractor.CommandFfmpeg:
				Extractor.CommandFfmpeg += self.__parametersFfmpeg()
			Extractor.CommandInitialized = True

	def __del__(self):
		self.__stop()
		self.__delete()

	def __delete(self):
		if self.mTemporaryPath:
			return tools.File.delete(self.mTemporaryPath, force = True)
		return False

	def __emptyDictionary(self, dictionary):
		return len(dictionary) == 0

	def __concatenateDictionary(self, dictionary1, dictionary2, dictionary3):
		if not dictionary1: dictionary1 = {}
		if not dictionary2: dictionary2 = {}
		if not dictionary3: dictionary3 = {}
		return dict(dictionary3.items() + dictionary2.items() + dictionary1.items()) # Only updates values if non-exisitng. Updates from back to front.

	def __fullMetadata(self, metadata):
		return not metadata == None and 'video' in metadata and 'audio' in metadata

	def __execute(self, command, timeout = 30):
		try:
			self.mProcess = None
			self.mResult = None
			def run():
				try:
					self.mProcess = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
					self.mResult = self.mProcess.stdout.read().decode('utf-8')
				except:
					pass

			thread = threading.Thread(target = run)
			thread.start()
			thread.join(timeout)
			if thread.is_alive():
				try:
					self.__stop()
					thread.join()
				except:
					pass

			return self.mResult
		except:
			return None

	def __stop(self):
		try:
			processId = self.mProcess.pid
			self.mProcess.terminate()
			self.mProcess.kill()
			os.killpg(processId, signal.SIGKILL) # Force kill by OS, aka Ctrl-C.
		except:
			pass

	def __detectMediainfo(self):
		if 'MediaInfo --Help' in self.__execute('mediainfo'): # Nativley installed
			return 'mediainfo'
		else:
			prefix = None
			path = path = os.path.join(tools.System.pathBinaries(), 'resources', 'data', 'mediainfo')

			if sys.platform == 'win32' or sys.platform == 'win64' or sys.platform == 'windows':
				path = os.path.join(path, 'windows', 'mediainfo.exe')
			elif sys.platform == 'darwin' or sys.platform == 'mac' or sys.platform == 'macosx':
				path = os.path.join(path, 'mac', 'mediainfo')
			else:
				# LD_LIBRARY_PATH to load the libraries from same directory instead of common library path.
				bits, _ = platform.architecture()
				if '64' in bits:
					path = os.path.join(path, 'linux64')
					prefix = 'LD_LIBRARY_PATH=' + path
					path = os.path.join(path, 'mediainfo')
				else:
					path = os.path.join(path, 'linux32')
					prefix = 'LD_LIBRARY_PATH=' + path
					path = os.path.join(path, 'mediainfo')

			if os.path.exists(path):
				if prefix:
					path = prefix + ' ' + path
				if 'MediaInfo --Help' in self.__execute(path):
					return path
		return None

	def __detectFfmpeg(self):
		if 'ffprobe version' in self.__execute('ffprobe'): # Nativley installed
			return 'ffprobe'
		else:
			return None

	def __parametersMediainfo(self):
		return ' --Full "%s"'

	def __parametersFfmpeg(self):
		return ' -loglevel quiet -print_format json -show_format -show_streams -show_error "%s"'

	def __extractChunked(self, link, single = False, timeout = 30, network = False):
		result = None
		self.mTemporaryPath = tools.System.temporaryRandom(directory = 'metadata')

		result = None
		if network:
			tools.File.copy(link, self.mTemporaryPath, Extractor.SizeLocal)
		else:
			neter = network.Networker(link)
			data = ''
			while len(data) < self.mSizeMaximum:
				dataNew = neter.data(start = len(data), size = self.mSizeChunk, timeout = timeout)
				if dataNew:
					data += dataNew
					f = open(self.mTemporaryPath, 'w+')
					f.write(data)
					f.close()

					result = self.extractMediainfo(self.mTemporaryPath, timeout = timeout)
					if not self.__fullMetadata(result):
						result = self.extractFfmpeg(self.mTemporaryPath, timeout = timeout)
						if not self.__fullMetadata(result):
							result = self.extractHachoir(self.mTemporaryPath)
					if self.__fullMetadata(result):
						break
				else:
					break
				if single:
					break

		if not self.__fullMetadata(result):
			result1 = self.extractMediainfo(self.mTemporaryPath, timeout = timeout)
			result2 = self.extractFfmpeg(self.mTemporaryPath, timeout = timeout)
			result3 = self.extractHachoir(self.mTemporaryPath)
			result = self.__concatenateDictionary(result1, result2, result3)

		# Will only show the info of the downloaded chunk, instead of the actual file.
		if 'size' in result:
			del result['size']
		if 'name' in result:
			del result['name']

		self.__delete()
		return result

	def extract(self, pathOrLink, timeout = 30):
		result = {}
		if not isinstance(pathOrLink, basestring):
			return result

		try:
			if tools.File.network(pathOrLink):
				result = self.__extractChunked(link = pathOrLink, network = True)
			else:
				isLink = pathOrLink.startswith('http:') or pathOrLink.startswith('https:') or pathOrLink.startswith('ftp:') or pathOrLink.startswith('ftps:')
				if isLink:
					# Do not use MediaInfo and FFmpeg both, since they are both slow. Rather fallback to manual.
					start = time.time()
					if Extractor.CommandMediainfo:
						result = self.extractMediainfo(pathOrLink, timeout = timeout)
					elif Extractor.CommandFfmpeg:
						result = self.extractMediainfo(pathOrLink, timeout = timeout)
					ellapsed = time.time() - start

					if not result or self.__emptyDictionary(result):
						timeout = int(timeout / 2)
						result = self.__extractChunked(pathOrLink, single = (ellapsed > timeout), timeout = timeout)

				else:
					result1 = self.extractMediainfo(pathOrLink, timeout = timeout)
					result2 = self.extractFfmpeg(pathOrLink, timeout = timeout)
					result3 = self.extractHachoir(pathOrLink)
					result = self.__concatenateDictionary(result1, result2, result3)
		except:
			pass
		return result

	def extractMediainfo(self, pathOrLink, timeout = 30):
		if not Extractor.CommandMediainfo:
			return None
		try:
			data = self.__execute(Extractor.CommandMediainfo % pathOrLink, timeout = timeout)
			return self.__parseMediainfo(data)
		except:
			return None

	def extractFfmpeg(self, pathOrLink, timeout = 30):
		if not Extractor.CommandFfmpeg:
			return None
		try:
			data = self.__execute(Extractor.CommandFfmpeg % pathOrLink, timeout = timeout)
			data = json.loads(data)
			return self.__parseFfmpeg(data)
		except:
			return None

	def extractHachoir(self, path):
		try:
			return self.__parseHachoir(path)
		except:
			return None

	def __parseMediainfo(self, data):
		try:
			info = {}

			resultGeneral = re.search('(General\s*\n([\s\S]*?).*\n\s*\n)', data, re.S)
			if resultGeneral :
				resultGeneral = resultGeneral.group(0)
				try:
					name = re.search("Complete name\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
					if name: info['name'] = name.group(1)
				except: pass
				try:
					container = re.search("Format\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
					info['container'] = container.group(1)
				except: pass
				try:
					size = re.search("File size\s*:\s*(\d+)\.?\d*.*\n", resultGeneral, re.S)
					if size: info['size'] = int(size.group(1))
				except: pass
				try:
					duration = re.search("Duration\s*:\s*(\d+)\.?\d*.*\n", resultGeneral, re.S)
					if duration: info['duration'] = int(int(duration.group(1)) / 1000)
				except: pass
				try:
					bitrate = re.search("Overall bit rate\s*:\s*(\d+)\.?\d*.*\n", resultGeneral, re.S)
					if bitrate: info['bitrate'] = int(bitrate.group(1))
				except: pass
				try:
					codec = re.search("Internet media type\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
					if codec: info['mime'] = codec.group(1)
				except: pass

			# Video

			resultVideo = re.search("(Video[\s\#\d]*\s*\n([\s\S]*?).*\n\s*\n)", data, re.S)
			if resultVideo:
				infoVideo = {}
				resultVideo = resultVideo.group(0)
				if not 'mime' in info or not info['mime']:
					try:
						codec = re.search("Internet media type\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultVideo, re.S)
						if codec: infoVideo['mime'] = codec.group(1)
					except: pass
				try:
					codec = re.search("Codec\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultVideo, re.S)
					if codec: infoVideo['codec'] = codec.group(1)
				except: pass
				try:
					bitrate = re.search("Bit rate\s*:\s*(\d+).*\n", resultVideo, re.S)
					if bitrate: infoVideo['bitrate'] = int(bitrate.group(1))
				except: pass
				try:
					width = re.search("Width\s*:\s*(\d+).*\n", resultVideo, re.S)
					if width: infoVideo['width'] = int(width.group(1))
				except: pass
				try:
					height = re.search("Height\s*:\s*(\d+).*\n", resultVideo, re.S)
					if height: infoVideo['height'] = int(height.group(1))
				except: pass
				try:
					aspectratio = re.search("Display aspect ratio\s*:\s*([\d\.]+).*\n", resultVideo, re.S)
					if aspectratio: infoVideo['aspectratio'] = round(float(aspectratio.group(1)), 3)
				except: pass
				try:
					framerate = re.search("Frame rate\s*:\s*([\d\.]+).*\n", resultVideo, re.S)
					if framerate: infoVideo['framerate'] = round(float(framerate.group(1)), 3)
				except: pass
				try:
					framecount = re.search("Frame count\s*:\s*(\d+)\.?\d*.*\n", resultVideo, re.S)
					if framecount: infoVideo['framecount'] = int(framecount.group(1))
				except: pass
				if not self.__emptyDictionary(infoVideo):
					info['video'] = infoVideo

			# Audio

			resultAudio = re.search("(Audio[\s\#\d]*\s*\n([\s\S]*?).*\n\s*\n)", data, re.S)
			if resultAudio:
				infoAudio = {}
				resultAudio = resultAudio.group(0)
				try:
					codec = re.search("Codec\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultAudio, re.S)
					if codec: infoAudio['codec'] = codec.group(1)
				except: pass
				try:
					bitrate = re.search("Bit rate\s*:\s*(\d+).*\n", resultAudio, re.S)
					if bitrate: infoAudio['bitrate'] = int(bitrate.group(1))
				except: pass
				try:
					channels = re.search("Channel\(s\)\s*:\s*(\d+).*\n",   resultAudio, re.S)
					if channels: infoAudio['channels'] = int(channels.group(1))
				except: pass
				try:
					samplerate = re.search("Sampling rate\s*:\s*([\w\_\-\\\/\@\. ]+).*\n", resultAudio, re.S)
					if samplerate: infoAudio['samplerate'] = int(samplerate.group(1))
				except: pass
				if not self.__emptyDictionary(infoAudio):
					info['audio'] = infoAudio

			# Subtitle
			if re.search("(Text[\s\#\d]*\s*\n([\s\S]*?).*\n\s*\n)", data, re.S):
				info['subtitle'] = True

			# Partial Files
			if not 'video' in info or not 'codec' in info['video'] and resultGeneral:
				if not 'video' in info: infoVideo = {}
				else: infoVideo = info['video']
				try:
					codec = re.search("Codec\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
					infoVideo['codec'] = codec.group(1)
				except: pass
				if not 'codec' in infoVideo or not infoVideo['codec']:
					try:
						codec = re.search("Format\s*:\s*([\w\_\-\\\/\. ]+).*\n", resultGeneral, re.S)
						infoVideo['codec'] = codec.group(1)
					except: pass
				if not self.__emptyDictionary(infoVideo):
					info['video'] = infoVideo

			if self.__emptyDictionary(info):
				info = None
			return info
		except:
			return None

	def __parseFfmpeg(self, data):
		try:
			info = {}
			indexVideo = None
			indexAudio = None
			indexSubtitle = None

			try:
				for item in data['streams']:
					if item['codec_type'] == 'video':
						indexVideo = item['index']
						break
			except: pass

			try:
				for item in data['streams']:
					if item['codec_type'] == 'audio':
						indexAudio = item['index']
						break
			except: pass

			try:
				for item in data['streams']:
					if item['codec_type'] == 'subtitle':
						indexSubtitle = item['index']
						break
			except: pass

			# File

			try: info['name'] = os.path.basename(data['format']['filename'])
			except: pass
			try: info['container'] = data['format']['format_name']
			except: pass
			try: info['size'] = int(data['format']['size'])
			except: pass
			try: info['duration'] = int(data['format']['duration'])
			except: pass
			try: info['bitrate'] = int(data['format']['bit_rate'])
			except: pass

			# Video

			if not indexVideo == None:
				infoVideo = {}
				try: infoVideo['codec'] = data['streams'][indexVideo]['codec_name']
				except: pass
				try: infoVideo['bitrate'] = int(data['streams'][indexVideo]['bit_rate'])
				except: pass
				try: infoVideo['width'] = int(data['streams'][indexVideo]['width'])
				except: pass
				try: infoVideo['height'] = int(data['streams'][indexVideo]['height'])
				except: pass
				try:
					aspectratio = data['streams'][indexVideo]['display_aspect_ratio']
					aspectratio = aspectratio.split(':')
					aspectratio = float(aspectratio[0]) / float(aspectratio[1])
					aspectratio = round(aspectratio, 3)
					infoVideo['aspectratio'] = aspectratio
				except: pass
				try:
					framerate = data['streams'][indexVideo]['r_frame_rate']
					framerate = framerate.split('/')
					framerate = float(framerate[0]) / float(framerate[1])
					framerate = round(framerate, 3)
					infoVideo['framerate'] = framerate
				except: pass
				try: infoVideo['framecount'] = int(data['streams'][indexVideo]['nb_read_frames'])
				except: pass
				if not self.__emptyDictionary(infoVideo):
					info['video'] = infoVideo

			# Audio

			if not indexAudio == None:
				infoAudio = {}
				try: infoAudio['codec'] = data['streams'][indexAudio]['codec_name']
				except: pass
				try: infoAudio['bitrate'] = int(data['streams'][indexAudio]['bit_rate'])
				except: pass
				try: infoAudio['channels'] = int(data['streams'][indexAudio]['channels'])
				except: pass
				try: infoAudio['samplerate'] = int(data['streams'][indexAudio]['sample_rate'])
				except: pass
				if not self.__emptyDictionary(infoAudio):
					info['audio'] = infoAudio

			# Subtitle

			if not indexSubtitle == None:
				info['subtitle'] = True

			if self.__emptyDictionary(info):
				info = None
			return info
		except:
			return None

	def __parseHachoir(self, path):
		try:
			info = {}
			parser = createParser(unicode(path))
			if parser:
				try:
					metadata = extractMetadata(parser)
				except:
					metadata = None
				if metadata:

					# File

					for item in metadata:
						if item.key == 'filename':
							try: info['name'] = os.path.basename(item.values[0].value)
							except: pass
						elif item.key == 'title' and (not 'name' in info or not info['name'] or info['name'] == ''):
							try: info['name'] = item.values[0].value
							except: pass
						elif item.key == 'file_type':
							try: info['container'] = item.values[0].value
							except: pass
						elif item.key == 'mime_type':
							try: info['mime'] = item.values[0].value
							except: pass
						elif item.key == 'file_size':
							try: info['size'] = item.values[0].value
							except: pass
						elif item.key == 'duration':
							try: info['duration'] = int(item.values[0].value.total_seconds())
							except: pass
						elif item.key == 'bit_rate':
							try: info['bitrate'] = item.values[0].value
							except: pass

					try:
						groups = metadata.groups()
					except:
						groups = None

					if groups:
						for key, value in groups.iteritems():

							# Video

							if 'video' in key:
								infoVideo = {}
								for item in value:
									if item.key == 'compression':
										try: infoVideo['codec'] = item.values[0].value
										except: pass
									if item.key == 'bit_rate':
										try: infoVideo['bitrate'] = int(item.values[0].value)
										except: pass
									if item.key == 'width':
										try: infoVideo['width'] = int(item.values[0].value)
										except: pass
									if item.key == 'height':
										try: infoVideo['height'] = int(item.values[0].value)
										except: pass
									if item.key == 'aspect_ratio':
										try: infoVideo['aspectratio'] = item.values[0].value
										except: pass
									if item.key == 'frame_rate':
										try: infoVideo['framerate'] = round(item.values[0].value, 3)
										except: pass
								if not self.__emptyDictionary(infoVideo):
									info['video'] = infoVideo

							# Audio

							if 'audio' in key:
								infoAudio = {}
								for item in value:
									if item.key == 'compression':
										try: infoAudio['codec'] = item.values[0].value
										except: pass
									if item.key == 'bit_rate':
										try: infoAudio['bitrate'] = int(item.values[0].value)
										except: pass
									if item.key == 'nb_channel':
										try: infoAudio['channels'] = int(item.values[0].value)
										except: pass
									if item.key == 'sample_rate':
										try: infoAudio['samplerate'] = int(item.values[0].value)
										except: pass
								if not self.__emptyDictionary(infoAudio):
									info['audio'] = infoAudio

							# Subtitle

							if 'subtitle' in key:
								info['subtitle'] = True

			# Hachoir only closes files in Python 3, not in Python 2. Manually close it, otherwise the file cannot be deleted.
			# https://bitbucket.org/haypo/hachoir/issues/33/open-file-handles-never-closed
			parser.stream._input.close()

			if self.__emptyDictionary(info):
				info = None
			return info
		except:
			return None
