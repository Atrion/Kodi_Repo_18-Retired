import xbmc, xbmcaddon, xbmcgui, xbmcplugin, os, sys, xbmcvfs, glob
import shutil
import urllib2,urllib
import re
import uservar
import time
import datetime
try:    from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database
from datetime import date
from resources.libs import wizard as wiz

ADDON_ID       = uservar.ADDON_ID
ADDONTITLE     = uservar.ADDONTITLE
ADDON          = wiz.addonId(ADDON_ID)
DIALOG         = xbmcgui.Dialog()
HOME           = xbmc.translatePath('special://home/')
ADDONS         = os.path.join(HOME,      'addons')
USERDATA       = os.path.join(HOME,      'userdata')
PLUGIN         = os.path.join(ADDONS,    ADDON_ID)
PACKAGES       = os.path.join(ADDONS,    'packages')
ADDONDATA      = os.path.join(USERDATA,  'addon_data', ADDON_ID)
TRAKTFOLD      = os.path.join(ADDONDATA, 'trakt')
ICON           = os.path.join(PLUGIN,    'icon.png')
TODAY          = datetime.date.today()
TOMORROW       = TODAY + datetime.timedelta(days=1)
THREEDAYS      = TODAY + datetime.timedelta(days=3)
TRAKT_EXODUS   = wiz.getS('exodus')
TRAKT_SALTS    = wiz.getS('salts')
TRAKT_SALTSHD  = wiz.getS('saltshd')
TRAKT_ROYALWE  = wiz.getS('royalwe')
TRAKT_VELOCITY = wiz.getS('velocity')
TRAKT_VELOKIDS = wiz.getS('velocitykids')
KEEPTRAKT      = wiz.getS('keeptrakt')
TRAKTSAVE      = wiz.getS('lastsave')
EXODUS         = 'plugin.video.exodus'
VELOCITY       = 'plugin.video.velocity'
VELOCITYKIDS   = 'plugin.video.velocitykids'
SALTS          = 'plugin.video.salts'
SALTSHD        = 'plugin.video.saltshd.lite'
ROYALWE        = 'plugin.video.theroyalwe'
PATHSALTS      = os.path.join(ADDONS, SALTS)
PATHSALTSHD    = os.path.join(ADDONS, SALTSHD)
PATHEXODUS     = os.path.join(ADDONS, EXODUS)
PATHVELOCITY   = os.path.join(ADDONS, VELOCITY)
PATHVELOCITYKI = os.path.join(ADDONS, VELOCITYKIDS)
PATHROYALWE    = os.path.join(ADDONS, ROYALWE)

def traktUser(who):
	user=None
	if who == 'exodus'       and os.path.exists(PATHEXODUS):     ADD_EXODUS       = wiz.addonId(EXODUS);       user = ADD_EXODUS.getSetting('trakt.user')
	if who == 'velocity'     and os.path.exists(PATHVELOCITY):   ADD_VELOCITY     = wiz.addonId(VELOCITY);     user = ADD_VELOCITY.getSetting('trakt_username')
	if who == 'velocitykids' and os.path.exists(PATHVELOCITYKI): ADD_VELOCITYKIDS = wiz.addonId(VELOCITYKIDS); user = ADD_VELOCITYKIDS.getSetting('trakt_username')
	if who == 'salts'        and os.path.exists(PATHSALTS):      ADD_SALTS        = wiz.addonId(SALTS);        user = ADD_SALTS.getSetting('trakt_user')
	if who == 'saltshd'      and os.path.exists(PATHSALTSHD):    ADD_SALTSHD      = wiz.addonId(SALTSHD);      user = ADD_SALTSHD.getSetting('trakt_user')
	if who == 'royalwe'      and os.path.exists(PATHROYALWE):    ADD_ROYALWE      = wiz.addonId(ROYALWE);      user = ADD_ROYALWE.getSetting('trakt_account')
	return user
		
def traktIt(do, who):
	if not os.path.exists(ADDONDATA): os.makedirs(ADDONDATA)
	if not os.path.exists(TRAKTFOLD): os.makedirs(TRAKTFOLD)
	if who == "all":
		if os.path.exists(PATHEXODUS):      trakt_Exodus(do)
		if os.path.exists(PATHVELOCITY):    trakt_Velocity(do)
		if os.path.exists(PATHVELOCITYKI):  trakt_VelocityKids(do)
		if os.path.exists(PATHSALTS):       trakt_Salts(do)
		if os.path.exists(PATHSALTSHD):     trakt_SaltsHD(do)
		if os.path.exists(PATHROYALWE):     trakt_TheRoyalWe(do)
		wiz.setS('lastsave', str(THREEDAYS))
	else:
		if who == "exodus"       and os.path.exists(PATHEXODUS):      trakt_Exodus(do)
		if who == "velocity"     and os.path.exists(PATHVELOCITY):    trakt_Velocity(do)
		if who == "velocitykids" and os.path.exists(PATHVELOCITYKI):  trakt_VelocityKids(do)
		if who == "salts"        and os.path.exists(PATHSALTS):       trakt_Salts(do)
		if who == "saltshd"      and os.path.exists(PATHSALTSHD):     trakt_SaltsHD(do)
		if who == "royalwe"      and os.path.exists(PATHROYALWE):     trakt_TheRoyalWe(do)

def clearSaved(who):
	addonlist = {'salts':'salts_trakt', 'saltshd':'saltshd_trakt', 'exodus':'exodus_trakt', 'royalwe':'royalwe_trakt', 'velocity':'velocity_trakt', 'velocitykids':'velocitykids_trakt'}
	if who == 'all':
		for trakt in addonlist:
			file = os.path.join(TRAKTFOLD, addonlist[trakt])
			if os.path.exists(file): os.remove(file)
			wiz.setS(trakt, '')
			wiz.LogNotify(trakt.upper(),'Trakt Data: [COLOR green]Removed![/COLOR]', 2000, os.path.join(eval('PATH'+trakt.upper()),'icon.png'))
	else:
		file = os.path.join(TRAKTFOLD, addonlist[who])
		if os.path.exists(file): os.remove(file)
		wiz.setS(who, '')
		wiz.LogNotify(who.upper(),'Trakt Data: [COLOR green]Removed![/COLOR]', 2000, os.path.join(eval('PATH'+who.upper()),'icon.png'))
	xbmc.executebuiltin('Container.Refresh')	
		
def trakt_Salts(do):
	SALTSFILE        = os.path.join(TRAKTFOLD, 'salts_trakt')
	SALTSSETTINGS    = os.path.join(USERDATA, 'addon_data', SALTS,'settings.xml')
	SALTS_TRAKT      = ['trakt_oauth_token', 'trakt_refresh_token', 'trakt_user']	
	ADD_SALTS        = wiz.addonId(SALTS)
	TRAKTSALTS       = ADD_SALTS.getSetting('trakt_user')
	if do == 'update':
		if not TRAKTSALTS == '':
			with open(SALTSFILE, 'w') as f:
				for trakt in SALTS_TRAKT: f.write('<trakt>\n\t<id>%s</id>\n\t<value>%s</value>\n</trakt>\n' % (trakt, ADD_SALTS.getSetting(trakt)))
			f.closed
			wiz.setS('salts', ADD_SALTS.getSetting('trakt_user'))
			wiz.LogNotify('SALTS','Trakt Data: [COLOR green]Saved![/COLOR]', 2000, os.path.join(PATHSALTS,'icon.png'))
		else: wiz.LogNotify('SALTS','Trakt Data: [COLOR red]Not Registered![/COLOR]', 2000, os.path.join(PATHSALTS,'icon.png'))
	elif do == 'restore':
		if os.path.exists(SALTSFILE):
			f = open(SALTSFILE,mode='r'); g = f.read().replace('\n','').replace('\r','').replace('\t',''); f.close();
			match = re.compile('<trakt><id>(.+?)</id><value>(.+?)</value></trakt>').findall(g)
			if len(match) > 0:
				for trakt, value in match:
					ADD_SALTS.setSetting(trakt, value)
				wiz.setS('salts', ADD_SALTS.getSetting('trakt_user'))
			wiz.LogNotify('SALTS','Trakt Data: [COLOR green]Restored![/COLOR]', 2000, os.path.join(PATHSALTS,'icon.png'))
		else: wiz.LogNotify('SALTS','Trakt Data: [COLOR red]Not Found![/COLOR]', 2000, os.path.join(PATHSALTS,'icon.png'))
	elif do == 'clearaddon':
		wiz.log('SALTS SETTINGS: %s' % SALTSSETTINGS)
		if os.path.exists(SALTSSETTINGS):
			f = open(SALTSSETTINGS,"r"); lines = f.readlines(); f.close()
			f = open(SALTSSETTINGS,"w")
			for line in lines:
				match = re.compile('<setting.+?id="(.+?)".+?/>').findall(line)
				if len(match) == 0: f.write(line)
				elif match[0] not in SALTS_TRAKT: f.write(line)
				else: wiz.log('Removing Line: %s' % line)
			f.close()
			wiz.LogNotify('SALTS','Addon Data: [COLOR green]Cleared![/COLOR]', 2000, os.path.join(PATHSALTS,'icon.png'))
		else: wiz.LogNotify('SALTS','Addon Data: [COLOR red]Clear Failed![/COLOR]', 2000, os.path.join(PATHSALTS,'icon.png'))
	xbmc.executebuiltin('Container.Refresh')	
	
def trakt_SaltsHD(do):
	SALTSHDFILE      = os.path.join(TRAKTFOLD, 'saltshd_trakt')
	SALTSHDSETTINGS  = os.path.join(USERDATA, 'addon_data', SALTSHD,'settings.xml')
	SALTSHD_TRAKT    = ['trakt_oauth_token', 'trakt_refresh_token', 'trakt_user']	
	ADD_SALTSHD      = wiz.addonId(SALTSHD)
	TRAKTSALTSHD     = ADD_SALTSHD.getSetting('trakt_user')
	if do == 'update':
		if not ADD_SALTSHD.getSetting('trakt_user') == '':
			with open(SALTSHDFILE, 'w') as f:
				for trakt in SALTSHD_TRAKT: f.write('<trakt>\n\t<id>%s</id>\n\t<value>%s</value>\n</trakt>\n' % (trakt, ADD_SALTSHD.getSetting(trakt)))
			f.closed
			wiz.setS('saltshd', ADD_SALTSHD.getSetting('trakt_user'))
			wiz.LogNotify('SALTS HD','Trakt Data: [COLOR green]Saved![/COLOR]', 2000, os.path.join(PATHSALTSHD,'icon.png'))
		else: wiz.LogNotify('SALTS HD','Trakt Data: [COLOR red]Not Registered![/COLOR]', 2000, os.path.join(PATHSALTSHD,'icon.png'))
	elif do == 'restore':
		if os.path.exists(SALTSHDFILE):
			f = open(SALTSHDFILE,mode='r'); g = f.read().replace('\n','').replace('\r','').replace('\t',''); f.close();
			match = re.compile('<trakt><id>(.+?)</id><value>(.+?)</value></trakt>').findall(g)
			if len(match) > 0:
				for trakt, value in match:
					ADD_SALTSHD.setSetting(trakt, value)
				wiz.setS('saltshd', ADD_SALTSHD.getSetting('trakt_user'))
			wiz.LogNotify('SALTSHD','Trakt Data: [COLOR green]Restored![/COLOR]', 2000, os.path.join(PATHSALTSHD,'icon.png'))
		else: wiz.LogNotify('SALTSHD','Trakt Data: [COLOR red]Not Found![/COLOR]', 2000, os.path.join(PATHSALTSHD,'icon.png'))
	elif do == 'clearaddon':
		wiz.log('SALTS HD SETTINGS: %s' % SALTSHDSETTINGS)
		if os.path.exists(SALTSHDSETTINGS):
			f = open(SALTSHDSETTINGS,"r"); lines = f.readlines(); f.close()
			f = open(SALTSHDSETTINGS,"w")
			for line in lines:
				match = re.compile('<setting.+?id="(.+?)".+?/>').findall(line)
				if len(match) == 0: f.write(line)
				elif match[0] not in SALTSHD_TRAKT: f.write(line)
				else: wiz.log('Removing Line: %s' % line)
			f.close()
			wiz.LogNotify('SALTS HD','Addon Data: [COLOR green]Cleared![/COLOR]', 2000, os.path.join(PATHSALTSHD,'icon.png'))
		else: wiz.LogNotify('SALTS HD','Addon Data: [COLOR red]Clear Failed![/COLOR]', 2000, os.path.join(PATHSALTSHD,'icon.png'))
	xbmc.executebuiltin('Container.Refresh')	
	
def trakt_Exodus(do):
	EXODUSFILE      = os.path.join(TRAKTFOLD, 'exodus_trakt')
	EXODUSSETTINGS  = os.path.join(USERDATA, 'addon_data', EXODUS,'settings.xml')
	EXODUS_TRAKT    = ['trakt.user', 'trakt.refresh', 'trakt.token']
	ADD_EXODUS      = wiz.addonId(EXODUS)
	TRAKTEXODUS     = ADD_EXODUS.getSetting('trakt.user')
	if do == 'update':
		if not TRAKTEXODUS == '':
			with open(EXODUSFILE, 'w') as f:
				for trakt in EXODUS_TRAKT: f.write('<trakt>\n\t<id>%s</id>\n\t<value>%s</value>\n</trakt>\n' % (trakt, ADD_EXODUS.getSetting(trakt)))
			f.closed
			wiz.setS('exodus', ADD_EXODUS.getSetting('trakt.user'))
			wiz.LogNotify('Exodus','Trakt: [COLOR green]Saved![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
		else: wiz.LogNotify('Exodus','Trakt Data: [COLOR red]Not Registered![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
	elif do == 'restore':
		if os.path.exists(EXODUSFILE):
			f = open(EXODUSFILE,mode='r'); g = f.read().replace('\n','').replace('\r','').replace('\t',''); f.close();
			match = re.compile('<trakt><id>(.+?)</id><value>(.+?)</value></trakt>').findall(g)
			if len(match) > 0:
				for trakt, value in match:
					ADD_EXODUS.setSetting(trakt, value)
			wiz.setS('exodus', ADD_EXODUS.getSetting('trakt.user'))
			wiz.LogNotify('Exodus','Trakt: [COLOR green]Restored![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
		else: wiz.LogNotify('Exodus','Trakt Data: [COLOR red]Not Found![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
	elif do == 'clearaddon':
		wiz.log('Exodus SETTINGS: %s' % EXODUSSETTINGS)
		if os.path.exists(EXODUSSETTINGS):
			f = open(EXODUSSETTINGS,"r"); lines = f.readlines(); f.close()
			f = open(EXODUSSETTINGS,"w")
			for line in lines:
				match = re.compile('<setting.+?id="(.+?)".+?/>').findall(line)
				if len(match) == 0: f.write(line)
				elif match[0] not in EXODUS_TRAKT: f.write(line)
				else: wiz.log('Removing Line: %s' % line)
			f.close()
			wiz.LogNotify('Exodus','Addon Data: [COLOR green]Cleared![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
		else: wiz.LogNotify('Exodus','Addon Data: [COLOR red]Clear Failed![/COLOR]', 2000, os.path.join(PATHEXODUS,'icon.png'))
	xbmc.executebuiltin('Container.Refresh')
	
def trakt_Velocity(do):
	VELOCITYFILE     = os.path.join(TRAKTFOLD, 'velocity_trakt')
	VELOCITYSETTINGS = os.path.join(USERDATA, 'addon_data', VELOCITY,'settings.xml')
	VELO_TRAKT       = ['trakt_authorized', 'trakt_username', 'trakt_oauth_token', 'trakt_refresh_token']
	ADD_VELOCITY     = wiz.addonId(VELOCITY)
	TRAKTVELOCITY    = ADD_VELOCITY.getSetting('trakt_username')
	if do == 'update':
		if ADD_VELOCITY.getSetting('trakt_authorized') == 'true':
			with open(VELOCITYFILE, 'w') as f:
				for trakt in VELO_TRAKT: f.write('<trakt>\n\t<id>%s</id>\n\t<value>%s</value>\n</trakt>\n' % (trakt, ADD_VELOCITY.getSetting(trakt)))
			f.closed
			wiz.setS('velocity', ADD_VELOCITY.getSetting('trakt_username'))
			wiz.LogNotify('Velocity','Trakt Data: [COLOR green]Saved![/COLOR]', 2000, os.path.join(PATHVELOCITY,'icon.png'))
		else: wiz.LogNotify('Velocity','Trakt Data: [COLOR red]Not Registered![/COLOR]', 2000, os.path.join(PATHVELOCITY,'icon.png'))
	elif do == 'restore':
		if os.path.exists(VELOCITYFILE):
			f = open(VELOCITYFILE,mode='r'); g = f.read().replace('\n','').replace('\r','').replace('\t',''); f.close();
			match = re.compile('<trakt><id>(.+?)</id><value>(.+?)</value></trakt>').findall(g)
			if len(match) > 0:
				for trakt, value in match:
					ADD_VELOCITY.setSetting(trakt, value)
				wiz.setS('velocity', ADD_VELOCITY.getSetting('trakt_username'))
			wiz.LogNotify('Velocity','Trakt Data: [COLOR green]Restored![/COLOR]', 2000, os.path.join(PATHVELOCITY,'icon.png'))
		else: wiz.LogNotify('Velocity','Trakt Data: [COLOR red]Not Found![/COLOR]', 2000, os.path.join(PATHVELOCITY,'icon.png'))
	elif do == 'clearaddon':
		wiz.log('Velocity SETTINGS: %s' % VELOCITYSETTINGS)
		if os.path.exists(VELOCITYSETTINGS):
			f = open(VELOCITYSETTINGS,"r"); lines = f.readlines(); f.close()
			f = open(VELOCITYSETTINGS,"w")
			for line in lines:
				match = re.compile('<setting.+?id="(.+?)".+?/>').findall(line)
				if len(match) == 0: f.write(line)
				elif match[0] not in VELO_TRAKT: f.write(line)
				else: wiz.log('Removing Line: %s' % line)
			f.close()
			wiz.LogNotify('Velocity','Addon Data: [COLOR green]Cleared![/COLOR]', 2000, os.path.join(PATHVELOCITY,'icon.png'))
		else: wiz.LogNotify('Velocity','Addon Data: [COLOR red]Clear Failed![/COLOR]', 2000, os.path.join(PATHVELOCITY,'icon.png'))
	xbmc.executebuiltin('Container.Refresh')
	
def trakt_VelocityKids(do):
	VELOCITYKIDSFILE  = os.path.join(TRAKTFOLD, 'velocitykids_trakt')
	VELOCITYKSETTINGS = os.path.join(USERDATA, 'addon_data', VELOCITYKIDS,'settings.xml')
	VELOKIDS_TRAKT    = ['trakt_authorized', 'trakt_username', 'trakt_oauth_token', 'trakt_refresh_token']
	ADD_VELOCITYKIDS  = wiz.addonId(VELOCITYKIDS)
	TRAKTVELOCITYKIDS = ADD_VELOCITYKIDS.getSetting('trakt_username')
	if do == 'update':
		if ADD_VELOCITYKIDS.getSetting('trakt_authorized') == 'true':
			with open(VELOCITYKIDSFILE, 'w') as f:
				for trakt in VELOKIDS_TRAKT: f.write('<trakt>\n\t<id>%s</id>\n\t<value>%s</value>\n</trakt>\n' % (trakt, ADD_VELOCITYKIDS.getSetting(trakt)))
			f.closed
			wiz.setS('velocitykids', ADD_VELOCITYKIDS.getSetting('trakt_username'))
			wiz.LogNotify('Velocity Kids','Trakt Data: [COLOR green]Saved![/COLOR]', 2000, os.path.join(PATHVELOCITYKI,'icon.png'))
		else: wiz.LogNotify('Velocity Kids','Trakt Data: [COLOR red]Not Registered![/COLOR]', 2000, os.path.join(PATHVELOCITYKI,'icon.png'))
	elif do == 'restore':
		if os.path.exists(VELOCITYKIDSFILE):
			f = open(VELOCITYKIDSFILE,mode='r'); g = f.read().replace('\n','').replace('\r','').replace('\t',''); f.close();
			match = re.compile('<trakt><id>(.+?)</id><value>(.+?)</value></trakt>').findall(g)
			if len(match) > 0:
				for trakt, value in match:
					ADD_VELOCITYKIDS.setSetting(trakt, value)
				wiz.setS('velocitykids', ADD_VELOCITYKIDS.getSetting('trakt_username'))
			wiz.LogNotify('Velocity Kids','Trakt Data: [COLOR green]Restored![/COLOR]', 2000, os.path.join(PATHVELOCITYKI,'icon.png'))
		else: wiz.LogNotify('Velocity Kids','Trakt Data: [COLOR red]Not Found![/COLOR]', 2000, os.path.join(PATHVELOCITYKI,'icon.png'))
	elif do == 'clearaddon':
		wiz.log('Velocity Kids SETTINGS: %s' % VELOCITYKSETTINGS)
		if os.path.exists(VELOCITYKSETTINGS):
			f = open(VELOCITYKSETTINGS,"r"); lines = f.readlines(); f.close()
			f = open(VELOCITYKSETTINGS,"w")
			for line in lines:
				match = re.compile('<setting.+?id="(.+?)".+?/>').findall(line)
				if len(match) == 0: f.write(line)
				elif match[0] not in VELOKIDS_TRAKT: f.write(line)
				else: wiz.log('Removing Line: %s' % line)
			f.close()
			wiz.LogNotify('Velocity Kids','Addon Data: [COLOR green]Cleared![/COLOR]', 2000, os.path.join(PATHVELOCITYKI,'icon.png'))
		else: wiz.LogNotify('Velocity Kids','Addon Data: [COLOR red]Clear Failed![/COLOR]', 2000, os.path.join(PATHVELOCITYKI,'icon.png'))
	xbmc.executebuiltin('Container.Refresh')
	
def trakt_TheRoyalWe(do):
	ROYALWEFILE     = os.path.join(TRAKTFOLD, 'royalwe_trakt')
	ROYALWESETTINGS = os.path.join(USERDATA, 'addon_data', ROYALWE,'settings.xml')
	ROYAL_TRAKT     = ['trakt_authorized', 'trakt_account', 'trakt_client_id', 'trakt_oauth_token', 'trakt_refresh_token', 'trakt_secret']
	ADD_ROYALWE     = wiz.addonId(ROYALWE)
	TRAKTROYAL      = ADD_ROYALWE.getSetting('trakt_account')
	if do == 'update':
		if ADD_ROYALWE.getSetting('trakt_authorized') == 'true':
			with open(ROYALWEFILE, 'w') as f:
				for trakt in ROYAL_TRAKT: f.write('<trakt>\n\t<id>%s</id>\n\t<value>%s</value>\n</trakt>\n' % (trakt, ADD_ROYALWE.getSetting(trakt)))
			f.closed
			wiz.setS('royalwe', ADD_ROYALWE.getSetting('trakt_account'))
			wiz.LogNotify('The Royal We','Trakt Data: [COLOR green]Saved![/COLOR]', 2000, os.path.join(PATHROYALWE,'icon.png'))
		else: wiz.LogNotify('The Royal We','Trakt Data: [COLOR red]Not Registered![/COLOR]', 2000, os.path.join(PATHROYALWE,'icon.png'))
	elif do == 'restore':
		if os.path.exists(ROYALWEFILE):
			f = open(ROYALWEFILE,mode='r'); g = f.read().replace('\n','').replace('\r','').replace('\t',''); f.close();
			match = re.compile('<trakt><id>(.+?)</id><value>(.+?)</value></trakt>').findall(g)
			if len(match) > 0:
				for trakt, value in match:
					ADD_ROYALWE.setSetting(trakt, value)
				wiz.setS('royalwe', ADD_ROYALWE.getSetting('trakt_account'))
			wiz.LogNotify('The Royal We','Trakt Data: [COLOR green]Restored![/COLOR]', 2000, os.path.join(PATHROYALWE,'icon.png'))
		else: wiz.LogNotify('The Royal We','Trakt Data: [COLOR red]Not Found![/COLOR]', 2000, os.path.join(PATHROYALWE,'icon.png'))
	elif do == 'clearaddon':
		wiz.log('The Royal We SETTINGS: %s' % ROYALWESETTINGS)
		if os.path.exists(ROYALWESETTINGS):
			f = open(ROYALWESETTINGS,"r"); lines = f.readlines(); f.close()
			f = open(ROYALWESETTINGS,"w")
			for line in lines:
				match = re.compile('<setting.+?id="(.+?)".+?/>').findall(line)
				if len(match) == 0: f.write(line)
				elif match[0] not in ROYAL_TRAKT: f.write(line)
				else: wiz.log('Removing Line: %s' % line)
			f.close()
			wiz.LogNotify('The Royal We','Addon Data: [COLOR green]Cleared![/COLOR]', 2000, os.path.join(PATHROYALWE,'icon.png'))
		else: wiz.LogNotify('The Royal We','Addon Data: [COLOR red]Clear Failed![/COLOR]', 2000, os.path.join(PATHROYALWE,'icon.png'))
	xbmc.executebuiltin('Container.Refresh')
	
def activateTrakt(name):
	url = None
	if name == 'exodus':
		if os.path.exists(PATHEXODUS): url = 'RunPlugin(plugin://plugin.video.exodus/?action=authTrakt)'
		else: DIALOG.ok(ADDONTITLE, 'Exodus is not currently installed.')
	elif name == 'velocity': 
		if os.path.exists(PATHVELOCITY): url = 'RunPlugin(plugin://plugin.video.velocity/?mode=get_pin)'
		else: DIALOG.ok(ADDONTITLE, 'Velocity is not currently installed.')
	elif name == 'velocitykids': 
		if os.path.exists(PATHVELOCITYKI): url = 'RunPlugin(plugin://plugin.video.velocitykids/?mode=get_pin)'
		else: DIALOG.ok(ADDONTITLE, 'Velocity Kids is not currently installed.')
	elif name == 'salts':
		if os.path.exists(PATHSALTS): url = 'RunPlugin(plugin://plugin.video.salts/?mode=auth_trakt)'
		else: DIALOG.ok(ADDONTITLE, 'SALTS is not currently installed.')
	elif name == 'saltshd': 
		if os.path.exists(PATHSALTSHD): url = 'RunPlugin(plugin://plugin.video.saltshd.lite/?mode=auth_trakt)'
		else: DIALOG.ok(ADDONTITLE, 'SALTS Lite HD is not currently installed.')
	elif name == 'royalwe': 
		if os.path.exists(PATHROYALWE): url = 'RunScript(plugin.video.theroyalwe, ?mode=authorize_trakt)'
		else: DIALOG.ok(ADDONTITLE, 'The Royal We is not currently installed.')
	if not url == None: xbmc.executebuiltin(url)