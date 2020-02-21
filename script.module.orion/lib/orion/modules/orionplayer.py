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
# OrionPlayer
##############################################################################
# Class for handeling play commands submitted through the RPC by the website.
##############################################################################

import xbmc
import xbmcgui
from orion.modules.oriontools import *
from orion.modules.orioninterface import *

class OrionPlayer:

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		pass

	##############################################################################
	# PLAY
	##############################################################################

	@classmethod
	def play(self, data):
		OrionInterface.dialogNotification(title = 32309, message = 33067, icon = OrionInterface.IconInformation, time = 7000, sound = True)
		data = OrionTools.decompress(data, raw = True, base64 = True, url = True)
		if data:
			data = OrionTools.jsonFrom(data)
			if data and OrionTools.isList(data) and len(data) > 0:
				link = data[0]

				meta = {}
				art = {}
				image = None
				rating = None
				votes = 0
				mime = None
				fanart = None

				try: type = data[1]
				except: type = None

				meta['mediatype'] = 'movie' if type == 'movie' else 'episode' if type == 'show' else 'video'
				try: meta['title'] = data[2]
				except: pass
				try: meta['tvshowtitle'] = data[3]
				except: pass
				try: meta['season'] = data[4]
				except: pass
				try: meta['episode'] = data[5]
				except: pass
				try: meta['year'] = data[6]
				except: pass
				try: meta['aired'] = data[7]
				except: pass
				try: meta['imdbnumber'] = ('' if data[8].startsWith('tt') else 'tt') + data[8]
				except: pass
				try: image = data[9]
				except: pass
				try: meta['tagline'] = data[10]
				except: pass
				try: rating = meta['rating'] = data[11]
				except: pass
				try: votes = meta['votes'] = data[12]
				except: pass
				try: meta['duration'] = data[13]
				except: pass
				try: meta['premiered'] = data[14]
				except: pass
				try: meta['mpaa'] = data[15]
				except: pass
				try: meta['genre'] = [i.title() for i in data[16]]
				except: pass
				try: meta['country'] = OrionTools.country(data[17].lower())
				except: pass
				try: meta['studio'] = data[18]
				except: pass
				try: meta['status'] = data[19].title()
				except: pass
				try: meta['size'] = data[20]
				except: pass
				try: mime = data[21]
				except: pass
				try: meta['plot'] = data[22]
				except: pass
				try: meta['trailer'] = data[23]
				except: pass

				meta = {key : value for key, value in OrionTools.iterator(meta) if value}
				if not 'tagline' in meta and 'plot' in meta:
					try: meta['tagline'] = meta['plot'][0 : meta['plot'].find('.') + 1]
					except: pass

				if image:
					art['poster'] = art['thumb'] = image + 'poster'
					fanart = art['fanart'] = image + 'background'
					art['icon'] = art['clearlogo'] = image + 'logo'
					art['clearart'] = image + 'art'

				entry = xbmcgui.ListItem()
				entry.setInfo('video', meta)
				entry.setArt(art)
				if fanart: entry.setAvailableFanart([{'image' : fanart, 'preview' : fanart}])
				if rating: entry.setRating('trakt', rating, votes, True)
				if mime: entry.setMimeType(mime)

				xbmc.Player().play(link, entry)

				return True
		return False
