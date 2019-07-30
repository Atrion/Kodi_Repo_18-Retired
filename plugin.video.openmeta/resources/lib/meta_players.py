import json
import xbmc, xbmcvfs

class AddonPlayer(object):
	def __init__(self, filename, media, meta):
		self.media = media
		self.title = meta['name']
		self.pluginid = meta.get('plugin')
		self.id = meta.get('id', filename.replace('.json', ''))
		self.order = meta.get('priority')
		self.commands = meta.get(media, [])

	def is_empty(self):
		if self.pluginid and ',' in self.pluginid:
			PLUGINS = [xbmc.getCondVisibility('System.HasAddon(%s)' % p) for p in self.pluginid.split(',')]
			if False in PLUGINS:
				return True
		elif self.pluginid and not xbmc.getCondVisibility('System.HasAddon(%s)' % self.pluginid):
			return True
		return not bool(self.commands)

def get_players(media):
	assert media in ('tvshows', 'movies')
	players = []
	players_path = 'special://profile/addon_data/plugin.video.openmeta/Players/'
	files = [x for x in xbmcvfs.listdir(players_path)[1] if x.endswith('.json')]
	for file in files:
		path = players_path + file
		f = xbmcvfs.File(path)
		content = f.read()
		meta = json.loads(content)
		f.close()
		player = AddonPlayer(file, media, meta)
		if not player.is_empty():
			players.append(player)
	return sort_players(players)

def sort_players(players):
	result = []
	for player in players:
		result.append((player.order, player))
	result.sort()
	return [x[-1] for x in result]

def get_needed_langs(players):
	languages = set()
	for player in players:
		for command_group in player.commands:  
			for command in command_group:
				command_lang = command.get('language', 'en')
				languages.add(command_lang)
	return languages

ADDON_SELECTOR = AddonPlayer('selector', 'any', meta = {'name': 'Selector'})