import xbmc, xbmcaddon, xbmcgui, xbmcplugin, os, sys, xbmcvfs, glob
import shutil
import urllib2,urllib
import re
import uservar
import time
import fnmatch
import datetime
try:    from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database
from datetime import date
from resources.libs import extract, downloader, notify, traktit, skinSwitch, uploadLog, wizard as wiz

ADDON_ID       = uservar.ADDON_ID
ADDONTITLE     = uservar.ADDONTITLE
ADDON          = wiz.addonId(ADDON_ID)
VERSION        = wiz.addonInfo(ADDON_ID,'version')
DIALOG         = xbmcgui.Dialog()
DP             = xbmcgui.DialogProgress()
HOME           = xbmc.translatePath('special://home/')
ADDONS         = os.path.join(HOME,     'addons')
USERDATA       = os.path.join(HOME,     'userdata')
PLUGIN         = os.path.join(ADDONS,   ADDON_ID)
PACKAGES       = os.path.join(ADDONS,   'packages')
ADDONDATA      = os.path.join(USERDATA, 'addon_data', ADDON_ID)
ADVANCED       = os.path.join(USERDATA, 'advancedsettings.xml')
SOURCES        = os.path.join(USERDATA, 'sources.xml')
FAVOURITES     = os.path.join(USERDATA, 'favourites.xml')
PROFILES       = os.path.join(USERDATA, 'profiles.xml')
THUMBS         = os.path.join(USERDATA, 'Thumbnails')
DATABASE       = os.path.join(USERDATA, 'Database')
FANART         = os.path.join(PLUGIN,   'fanart.jpg')
ICON           = os.path.join(PLUGIN,   'icon.png')
ART            = os.path.join(PLUGIN,   'resources', 'art')
SKIN           = xbmc.getSkinDir()
BUILDNAME      = wiz.getS('buildname')
BUILDVERSION   = wiz.getS('buildversion')
BUILDTHEME     = wiz.getS('buildtheme')
BUILDLATEST    = wiz.getS('latestversion')
BUILDCHECK     = wiz.getS('lastbuildcheck')
SHOW15         = wiz.getS('show15')
SHOW16         = wiz.getS('show16')
SEPERATE       = wiz.getS('seperate')
NOTIFY         = wiz.getS('notify')
NOTEID         = wiz.getS('noteid')
NOTEDISMISS    = wiz.getS('notedismiss')
KEEPFAVS       = wiz.getS('keepfavourites')
KEEPSOURCES    = wiz.getS('keepsources')
KEEPPROFILES   = wiz.getS('keepprofiles')
KEEPADVANCED   = wiz.getS('keepadvanced')
KEEPTRAKT      = wiz.getS('keeptrakt')
TRAKTSAVE      = wiz.getS('lastsave')
TRAKT_EXODUS   = wiz.getS('exodus')
TRAKT_SALTS    = wiz.getS('salts')
TRAKT_SALTSHD  = wiz.getS('saltshd')
TRAKT_ROYALWE  = wiz.getS('royalwe')
TRAKT_VELOCITY = wiz.getS('velocity')
TRAKT_VELOKIDS = wiz.getS('velocitykids')
TODAY          = datetime.date.today()
TOMORROW       = TODAY + datetime.timedelta(days=1)
THREEDAYS      = TODAY + datetime.timedelta(days=3)
KODIV          = float(xbmc.getInfoLabel("System.BuildVersion")[:4])
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
EXCLUDES       = uservar.EXCLUDES
BUILDFILE      = uservar.BUILDFILE
UPDATECHECK    = uservar.UPDATECHECK if str(uservar.UPDATECHECK).isdigit() else 1
NEXTCHECK      = TODAY + datetime.timedelta(days=UPDATECHECK)
NOTIFICATION   = uservar.NOTIFICATION
ENABLE         = uservar.ENABLE
AUTOUPDATE     = uservar.AUTOUPDATE
WIZARDFILE     = uservar.WIZARDFILE
HIDECONTACT    = uservar.HIDECONTACT
CONTACT        = uservar.CONTACT
HIDESPACERS    = uservar.HIDESPACERS
COLOR1         = uservar.COLOR1
COLOR2         = uservar.COLOR2
THEME1         = uservar.THEME1
THEME2         = uservar.THEME2
THEME3         = uservar.THEME3
THEME4         = uservar.THEME4
THEME5         = uservar.THEME5
ICONMAINT      = uservar.ICONMAINT
ICONBUILDS     = uservar.ICONBUILDS
ICONCONTACT    = uservar.ICONCONTACT
ICONTRAKT      = uservar.ICONTRAKT
ICONSETTINGS   = uservar.ICONSETTINGS

###########################
###### Menu Items   #######
###########################
#addDir (display,mode,name=None,url=None,menu=None,overwrite=True,fanart=FANART,icon=ICON, themeit=None)
#addFile(display,mode,name=None,url=None,menu=None,overwrite=True,fanart=FANART,icon=ICON, themeit=None)

def index():
	if len(BUILDNAME) > 0:
		version = wiz.checkBuild(BUILDNAME, 'version')
		build = '%s (v%s)' % (BUILDNAME, BUILDVERSION)
		if version > BUILDVERSION: build = '%s [COLOR red][B][UPDATE v%s][/B][/COLOR]' % (build, version)
		addDir(build,'viewbuild',BUILDNAME, themeit=THEME4)
		themefile = wiz.checkBuild(BUILDNAME, 'theme')
		if not themefile == 'http://' and wiz.workingURL(themefile) == True:
			addFile('None' if BUILDTHEME == "" else BUILDTHEME, 'theme', BUILDNAME, themeit=THEME5)
	else: addDir('None', 'builds', themeit=THEME4)
	if HIDESPACERS == 'No': addFile('============================================', '', themeit=THEME3)
	addDir ('Builds'       ,'builds',   icon=ICONBUILDS,   themeit=THEME1)
	addDir ('Maintenance'  ,'maint',    icon=ICONMAINT,    themeit=THEME1)
	addDir ('Trakt Data'   ,'trakt',    icon=ICONTRAKT,    themeit=THEME1)
	if HIDECONTACT == 'No': addFile('Contact'      ,'contact',  icon=ICONCONTACT,  themeit=THEME1)
	addFile('Settings'     ,'settings', icon=ICONSETTINGS, themeit=THEME1)
	setView('movies', 'MAIN')
	
def buildMenu():
	addFile('Kodi Version: %s' % KODIV, '', icon=ICONBUILDS, themeit=THEME3)
	if HIDESPACERS == 'No': addFile('============================================', '', themeit=THEME3)
	working = wiz.workingURL(BUILDFILE)
	if not working == True:
		addFile('Url for txt file not valid', '', icon=ICONBUILDS, themeit=THEME3)
		addFile('%s' % working, '', icon=ICONBUILDS, themeit=THEME3)
	else:	
		link  = wiz.openURL(BUILDFILE).replace('\n','').replace('\r','').replace('\t','')
		match = re.compile('name="(.+?)".+?ersion="(.+?)".+?rl="(.+?)".+?odi="(.+?)".+?con="(.+?)".+?anart="(.+?)"').findall(link)
		if len(match) > 0:
			if SEPERATE == 'true':
				for name, version, url, kodi, icon, fanart in match:
					menu = createMenu('install', name)
					addDir('[%s] %s (v%s)' % (float(kodi), name, version),'viewbuild',name,fanart=fanart,icon=icon, menu=menu, themeit=THEME2)
			else:
				state = '+' if SHOW16 == 'false' else '-'
				addFile('[%s] Jarvis and Above(%s)' % (state, wiz.buildCount('16')), 'showupdate',  '16', themeit=THEME3)
				if SHOW16 == 'true':
					for name, version, url, kodi, icon, fanart in match:
						kodiv = int(float(kodi))
						if kodiv >= 16:
							menu = createMenu('install', name)
							addDir('[%s] %s (v%s)' % (float(kodi), name, version),'viewbuild',name,fanart=fanart,icon=icon, menu=menu, themeit=THEME2)
				state = '+' if SHOW15 == 'false' else '-'
				addFile('[%s] Isengard and Below(%s)' % (state, wiz.buildCount('15')), 'showupdate',  '15', themeit=THEME3)
				if SHOW15 == 'true':
					for name, version, url, kodi, icon, fanart in match:
						kodiv = int(float(kodi))
						if kodiv <= 15:
							menu = createMenu('install', name)
							addDir('[%s] %s (v%s)' % (float(kodi), name, version),'viewbuild',name,fanart=fanart,icon=icon, menu=menu, themeit=THEME2)
		else: addFile('Text file for builds not formated correctly.', '', icon=ICONBUILDS, themeit=THEME3)
	setView('movies', 'MAIN')
	
def viewBuild(name):
	working = wiz.workingURL(BUILDFILE)
	if not working == True:
		addFile('Url for txt file not valid', '', themeit=THEME3)
		addFile('%s' % working, '', themeit=THEME3)
		return 
	if wiz.checkBuild(name, 'version') == False: 
		addFile('Error reading the txt file.', '', themeit=THEME3)
		addFile('%s was not found in the builds list.' % name, '', themeit=THEME3)
		return 
	version     = wiz.checkBuild(name, 'version')
	icon        = wiz.checkBuild(name, 'icon')   if wiz.workingURL(wiz.checkBuild(name, 'icon'))   else ICON
	fanart      = wiz.checkBuild(name, 'fanart') if wiz.workingURL(wiz.checkBuild(name, 'fanart')) else FANART
	build       = '%s (v%s)' % (name, version)
	themefile   = wiz.checkBuild(name, 'theme')
	if BUILDNAME == name and version > BUILDVERSION:
		build = '%s [COLOR red][B][CURRENT v%s][/B][/COLOR]' % (build, BUILDVERSION)
	addFile(build, '', fanart=fanart, icon=icon, themeit=THEME2)
	addFile('===============[ Install ]===================', '', fanart=fanart, icon=icon, themeit=THEME3)
	addFile('Fresh Install'   , 'install', name, 'fresh'   , fanart=fanart, icon=icon, themeit=THEME1)
	addFile('Standard Install', 'install', name, 'normal'  , fanart=fanart, icon=icon, themeit=THEME1)
	addFile('Apply guiFix'    , 'install', name, 'gui'     , fanart=fanart, icon=icon, themeit=THEME1)
	if not themefile == 'http://' and wiz.workingURL(themefile) == True:
		wiz.log(themefile)
		addFile('===============[ Themes ]==================', '', fanart=fanart, icon=icon, themeit=THEME3)
		link  = wiz.openURL(themefile).replace('\n','').replace('\r','').replace('\t','')
		match = re.compile('name="(.+?)".+?rl="(.+?)".+?con="(.+?)".+?anart="(.+?)"').findall(link)
		for themename, themeurl, themeicon, themefanart in match:
			themeicon   = themeicon   if wiz.workingURL(themeicon) == True   else icon
			themefanart = themefanart if wiz.workingURL(themefanart) == True else fanart
			addFile(themename if not themename == BUILDTHEME else "[B]%s (Installed)[/B]" % themename, 'theme', name, themename, fanart=themefanart, icon=themeicon, themeit=THEME3)
	
def maintMenu():
	addFile('Fresh Start'          ,'freshstart',    icon=ICONMAINT, themeit=THEME1)
	addFile('Clear Cache'          ,'clearcache',    icon=ICONMAINT, themeit=THEME1)
	addFile('Clear Packages'       ,'clearpackages', icon=ICONMAINT, themeit=THEME1)
	addFile('Clear Thumbnails'     ,'clearthumb',    icon=ICONMAINT, themeit=THEME1)
	addFile('Purge Databases'      ,'purgedb',       icon=ICONMAINT, themeit=THEME1)
	addFile('Force Update Addons'  ,'forceupdate',   icon=ICONMAINT, themeit=THEME1)
	addFile('Force Close Kodi'     ,'forceclose',    icon=ICONMAINT, themeit=THEME1)
	addFile('Upload Kodi.log'      ,'uploadlog',     icon=ICONMAINT, themeit=THEME1)
	addFile('View Kodi.log'        ,'viewlog',       icon=ICONMAINT, themeit=THEME1)
	setView('movies', 'MAIN')
	
def traktMenu():
	trakt = '[COLOR green]ON[/COLOR]' if KEEPTRAKT == 'true' else '[COLOR red]OFF[/COLOR]'
	addFile('[I]Register FREE Account at http://trakt.tv [/I]', '', icon=ICONTRAKT, themeit=THEME3)
	addFile('Save Trakt Data: %s' % trakt, 'traktsettings', icon=ICONTRAKT, themeit=THEME3)
	if HIDESPACERS == 'No': addFile('============================================', '', icon=ICONTRAKT, themeit=THEME3)
	exoi = os.path.join(ADDONS, EXODUS, 'icon.png')   if os.path.exists(PATHEXODUS) else ICONTRAKT
	exof = os.path.join(ADDONS, EXODUS, 'fanart.jpg') if os.path.exists(PATHEXODUS) else FANART
	addFile('[+]-- Exodus',     '', icon=exoi, fanart=exof, themeit=THEME3)
	menu = createMenu('traktaddon', 'Exodus'); menu2 = createMenu('trakt', 'Exodus')
	if not os.path.exists(PATHEXODUS):          addFile('[COLOR red]Addon Data: Not Installed[/COLOR]', '', icon=exoi, fanart=exof, menu=menu)
	elif not traktit.traktUser('exodus'):       addFile('[COLOR red]Addon Data: Not Registered[/COLOR]','authtrakt','exodus', icon=exoi, fanart=exof, menu=menu)
	else:                                       addFile('[COLOR green]Addon Data: %s[/COLOR]' % traktit.traktUser('exodus'),'authtrakt','exodus', icon=exoi, fanart=exof, menu=menu)
	if TRAKT_EXODUS == "":                      addFile('[COLOR red]Saved Data: Not Saved[/COLOR]','savetrakt','exodus', icon=exoi, fanart=exof, menu=menu2)
	else:                                       addFile('[COLOR green]Saved Data: %s[/COLOR]' % TRAKT_EXODUS, '', icon=exoi, fanart=exof, menu=menu2)
	salti = os.path.join(ADDONS, SALTS, 'icon.png')   if os.path.exists(PATHSALTS) else ICONTRAKT
	saltf = os.path.join(ADDONS, SALTS, 'fanart.jpg') if os.path.exists(PATHSALTS) else FANART
	addFile('[+]-- Salts',     '', icon=salti, fanart=saltf, themeit=THEME3)
	menu = createMenu('traktaddon', 'Salts'); menu2 = createMenu('trakt', 'Salts')
	if not os.path.exists(PATHSALTS):           addFile('[COLOR red]Addon Data: Not Installed[/COLOR]', '', icon=salti, fanart=saltf, menu=menu)
	elif not traktit.traktUser('salts'):        addFile('[COLOR red]Addon Data: Not Registered[/COLOR]','authtrakt','salts', icon=salti, fanart=saltf, menu=menu)
	else:                                       addFile('[COLOR green]Addon Data: %s[/COLOR]' % traktit.traktUser('salts'),'authtrakt','salts', icon=salti, fanart=saltf, menu=menu)
	if TRAKT_SALTS == "":                       addFile('[COLOR red]Saved Data: Not Saved[/COLOR]','savetrakt','salts', icon=salti, fanart=saltf, menu=menu2)
	else:                                       addFile('[COLOR green]Saved Data: %s[/COLOR]' % TRAKT_SALTS, '', icon=salti, fanart=saltf, menu=menu2)
	salthdi = os.path.join(ADDONS, SALTSHD, 'icon.png')   if os.path.exists(PATHSALTSHD) else ICONTRAKT
	salthdf = os.path.join(ADDONS, SALTSHD, 'fanart.jpg') if os.path.exists(PATHSALTSHD) else FANART
	addFile('[+]-- Salts HD',     '', icon=salthdi, fanart=salthdf, themeit=THEME3)
	menu = createMenu('traktaddon', 'Salts HD'); menu2 = createMenu('trakt', 'Salts HD')
	if not os.path.exists(PATHSALTSHD):         addFile('[COLOR red]Addon Data: Not Installed[/COLOR]', '', icon=salthdi, fanart=salthdf, menu=menu)
	elif not traktit.traktUser('saltshd'):      addFile('[COLOR red]Addon Data: Not Registered[/COLOR]','authtrakt','saltshd', icon=salthdi, fanart=salthdf, menu=menu)
	else:                                       addFile('[COLOR green]Addon Data: %s[/COLOR]' % traktit.traktUser('saltshd'),'authtrakt','saltshd', icon=salthdi, fanart=salthdf, menu=menu)
	if TRAKT_SALTSHD == "":                     addFile('[COLOR red]Saved Data: Not Saved[/COLOR]','savetrakt','saltshd', icon=salthdi, fanart=salthdf, menu=menu2)
	else:                                       addFile('[COLOR green]Saved Data: %s[/COLOR]' % TRAKT_SALTSHD, '', icon=salthdi, fanart=salthdf, menu=menu2)
	royalwei = os.path.join(ADDONS, ROYALWE, 'icon.png')   if os.path.exists(PATHROYALWE) else ICONTRAKT
	royalwef = os.path.join(ADDONS, ROYALWE, 'fanart.jpg') if os.path.exists(PATHROYALWE) else FANART
	addFile('[+]-- Royal We',     '', icon=royalwei, fanart=royalwef, themeit=THEME3)
	menu = createMenu('traktaddon', 'Royal We'); menu2 = createMenu('trakt', 'Royal We')
	if not os.path.exists(PATHROYALWE):         addFile('[COLOR red]Addon Data: Not Installed[/COLOR]', '', icon=royalwei, fanart=royalwef, menu=menu)
	elif not traktit.traktUser('royalwe'):      addFile('[COLOR red]Addon Data: Not Registered[/COLOR]','authtrakt','royalwe', icon=royalwei, fanart=royalwef, menu=menu)
	else:                                       addFile('[COLOR green]Addon Data: %s[/COLOR]' % traktit.traktUser('royalwe'),'authtrakt','royalwe', icon=royalwei, fanart=royalwef, menu=menu)
	if TRAKT_ROYALWE == "":                     addFile('[COLOR red]Saved Data: Not Saved[/COLOR]','savetrakt','royalwe', icon=royalwei, fanart=royalwef, menu=menu2)
	else:                                       addFile('[COLOR green]Saved Data: %s[/COLOR]' % TRAKT_ROYALWE, '', icon=royalwei, fanart=royalwef, menu=menu2)
	veloi = os.path.join(ADDONS, VELOCITY, 'icon.png')   if os.path.exists(PATHVELOCITY) else ICONTRAKT
	velof = os.path.join(ADDONS, VELOCITY, 'fanart.jpg') if os.path.exists(PATHVELOCITY) else FANART
	addFile('[+]-- Velocity',     '', icon=veloi, fanart=velof, themeit=THEME3)
	menu = createMenu('traktaddon', 'Velocity'); menu2 = createMenu('trakt', 'Velocity')
	if not os.path.exists(PATHVELOCITY):        addFile('[COLOR red]Addon Data: Not Installed[/COLOR]', '', icon=veloi, fanart=velof, menu=menu)
	elif not traktit.traktUser('velocity'):     addFile('[COLOR red]Addon Data: Not Registered[/COLOR]','authtrakt','velocity', icon=veloi, fanart=velof, menu=menu)
	else:                                       addFile('[COLOR green]Addon Data: %s[/COLOR]' % traktit.traktUser('velocity'),'authtrakt','velocity', icon=veloi, fanart=velof, menu=menu)
	if TRAKT_VELOCITY == "":                    addFile('[COLOR red]Saved Data: Not Saved[/COLOR]','savetrakt','velocity', icon=veloi, fanart=velof, menu=menu2)
	else:                                       addFile('[COLOR green]Saved Data: %s[/COLOR]' % TRAKT_VELOCITY, '', icon=veloi, fanart=velof, menu=menu2)
	velokidi = os.path.join(ADDONS, VELOCITYKIDS, 'icon.png')   if os.path.exists(PATHVELOCITYKI) else ICONTRAKT
	velokidf = os.path.join(ADDONS, VELOCITYKIDS, 'fanart.jpg') if os.path.exists(PATHVELOCITYKI) else FANART
	addFile('[+]-- Velocity Kids',     '', icon=velokidi, fanart=velokidf, themeit=THEME3)
	menu = createMenu('traktaddon', 'Velocity Kids'); menu2 = createMenu('trakt', 'Velocity Kids')
	if not os.path.exists(PATHVELOCITYKI):      addFile('[COLOR red]Addon Data: Not Installed[/COLOR]', '', icon=velokidi, fanart=velokidf, menu=menu)
	elif not traktit.traktUser('velocitykids'): addFile('[COLOR red]Addon Data: Not Registered[/COLOR]','authtrakt','velocitykids', icon=velokidi, fanart=velokidf, menu=menu)
	else:                                       addFile('[COLOR green]Addon Data: %s[/COLOR]' % traktit.traktUser('velocitykids'),'authtrakt','velocitykids', icon=velokidi, fanart=velokidf, menu=menu)
	if TRAKT_VELOKIDS == "":                    addFile('[COLOR red]Saved Data: Not Saved[/COLOR]','savetrakt','velocitykids', icon=velokidi, fanart=velokidf, menu=menu2)
	else:                                       addFile('[COLOR green]Saved Data: %s[/COLOR]' % TRAKT_VELOKIDS, '', icon=velokidi, fanart=velokidf, menu=menu2)
	if HIDESPACERS == 'No': addFile('============================================', '', themeit=THEME3)
	addFile('Save All Trakt Data',          'savetrakt',    'all', icon=ICONTRAKT,  themeit=THEME3)
	addFile('Recover All Saved Trakt Data', 'restoretrakt', 'all', icon=ICONTRAKT,  themeit=THEME3)
	addFile('Clear All Saved Trakt Data',   'cleartrakt',   'all', icon=ICONTRAKT,  themeit=THEME3)
	addFile('Clear All Addon Data',         'addontrakt',   'all', icon=ICONTRAKT,  themeit=THEME3)
	setView('movies', 'MAIN')

###########################
###### Build Install ######
###########################
	
def buildWizard(name, type, theme=None):
	if type == 'gui':
		if name == BUILDNAME:
			yes_pressed=DIALOG.yesno(ADDONTITLE, 'Would you like to apply the guifix for:', '%s?' % name, nolabel='No, Cancel',yeslabel='Yes, Apply Fix')
		else: 
			yes_pressed=DIALOG.yesno("%s - [COLOR red]WARNING!![/COLOR]" % ADDONTITLE, "%s community build is not currently installed." % name, "Would you like to apply the guiFix anyways?.", yeslabel="Yes, Apply", nolabel="No, Cancel")
		if yes_pressed:
			buildzip = wiz.checkBuild(name,'gui')
			zipname = name.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
			if not wiz.workingURL(buildzip) == True: wiz.LogNotify(ADDONTITLE, 'guiFix: [COLOR red]Invalid Zip Url![/COLOR]'); return
			if not os.path.exists(PACKAGES): os.makedirs(PACKAGES)
			DP.create(ADDONTITLE,'Downloading %s GuiFix' % name,'', 'Please Wait')
			lib=os.path.join(PACKAGES, '%s_guisettings.zip' % zipname)
			try: os.remove(lib)
			except: pass
			downloader.download(buildzip, lib, DP)
			time.sleep(2)
			DP.update(0,"", "Installing %s GuiFix" % name)
			extract.all(lib,USERDATA,DP)
			DP.close()
			wiz.killxbmc()
		else:
			wiz.LogNotify(ADDONTITLE, 'guiFix: [COLOR red]Cancelled![/COLOR]')
	elif type == 'fresh':
		freshStart(name)
	elif type == 'normal':
		if url == 'normal' and KEEPTRAKT == 'true':
			if TRAKTSAVE == '' or not TRAKTSAVE > str(TODAY):
				if DIALOG.yesno(ADDONTITLE, 'Would you like to save trakt data before installing' , '%s?' % name , nolabel='No Thanks!',yeslabel='Yes, Save Data'):
					traktit.traktIt('update' , 'all')
				wiz.setS('lastsave', str(THREEDAYS))
		if KODIV < 16 and wiz.checkBuild(name, 'kodi') >= 16:
			yes_pressed = DIALOG.yesno("%s - [COLOR red]WARNING!![/COLOR]" % ADDONTITLE, 'There is a chance that the skin will not appear correctly', 'When installing a %s build on a Kodi %s install' % (wiz.checkBuild(name, 'kodi'), KODIV), 'Would you still like to install: %s v%s?' % (name, wiz.checkBuild(name,'version')), nolabel='No, Cancel',yeslabel='Yes, Install')
		else:
			yes_pressed = DIALOG.yesno(ADDONTITLE, 'Would you like to install:', '%s v%s?' % (name, wiz.checkBuild(name,'version')), nolabel='No, Cancel',yeslabel='Yes, Install')
		if yes_pressed:
			buildzip = wiz.checkBuild(name, 'url')
			zipname = name.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
			if not wiz.workingURL(buildzip) == True: wiz.LogNotify(ADDONTITLE, 'Build Install: [COLOR red]Invalid Zip Url![/COLOR]'); return
			if not os.path.exists(PACKAGES): os.makedirs(PACKAGES)
			DP.create(ADDONTITLE,'Downloading %s ' % name,'', 'Please Wait')
			lib=os.path.join(PACKAGES, '%s.zip' % zipname)
			try: os.remove(lib)
			except: pass
			downloader.download(buildzip, lib, DP)
			time.sleep(2)
			DP.update(0,"", "Installing %s " % name)
			ext = extract.all(lib,HOME,DP)
			percent, errors, error = ext.split('/', 3)
			wiz.setS('buildname', name)
			wiz.setS('buildversion', wiz.checkBuild( name,'version'))
			wiz.setS('buildtheme', '')
			wiz.setS('latestversion', wiz.checkBuild( name,'version'))
			wiz.setS('lastbuildcheck', str(NEXTCHECK))
			wiz.setS('installed', 'true')
			wiz.setS('extract', str(percent))
			wiz.setS('errors', str(errors))
			wiz.log('INSTALLED %s: [ERRORS:%s]' % (percent, errors))
			if int(errors) >= 1:
				yes=DIALOG.yesno(ADDONTITLE, 'INSTALLED %s: [ERRORS:%s]' % (percent, errors), 'Would you like to view the errors?', nolabel='No, Cancel',yeslabel='Yes, View')
				if yes:
					wiz.TextBoxes(ADDONTITLE, error.replace('\t','')); time.sleep(3)
			DP.close()
			themefile = wiz.checkBuild(name, 'theme')
			if not themefile == 'http://' and wiz.workingURL(themefile) == True: buildWizard(name, 'theme')
			DIALOG.ok(ADDONTITLE, "To save changes you now need to force close Kodi, Press OK to force close Kodi")
			wiz.killxbmc()
		else:
			wiz.LogNotify(ADDONTITLE, 'Build Install: [COLOR red]Cancelled![/COLOR]')
	elif type == 'theme':
		if theme == None:
			themefile = wiz.checkBuild(name, 'theme')
			themelist = []
			if not themefile == 'http://' and wiz.workingURL(themefile) == True:
				link  = wiz.openURL(themefile).replace('\n','').replace('\r','').replace('\t','')
				match = re.compile('name="(.+?)"').findall(link)
				if len(match) > 0:
					if DIALOG.yesno(ADDONTITLE, "The Build [%s] comes with %s different themes" % (name, len(match)), "Would you like to install one now?", yeslabel="Yes, Install", nolabel="No Thanks"):
						for themename in match:
							themelist.append(themename)
						wiz.log("Theme List: %s " % str(themelist))
						ret = DIALOG.select(ADDONTITLE, themelist)
						wiz.log("Theme install selected: %s" % ret)
						if not ret == -1: theme = themelist[ret]; installtheme = True
						else: wiz.LogNotify(ADDONTITLE,'Theme Install: [COLOR red]Cancelled![/COLOR]'); return
					else: wiz.LogNotify(ADDONTITLE,'Theme Install: [COLOR red]Cancelled![/COLOR]'); return
			else: wiz.LogNotify(ADDONTITLE,'Theme Install: [COLOR red]None Found![/COLOR]')
		else: installtheme = DIALOG.yesno(ADDONTITLE, 'Would you like to install the theme:', theme, 'for %s v%s?' % (name, wiz.checkBuild(name,'version')), nolabel='No, Cancel',yeslabel='Yes, Install')
		if installtheme:
			themezip = wiz.checkTheme(name, theme, 'url')
			zipname = name.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
			if not wiz.workingURL(themezip) == True: wiz.LogNotify(ADDONTITLE, 'Theme Install: [COLOR red]Invalid Zip Url![/COLOR]'); return
			if not os.path.exists(PACKAGES): os.makedirs(PACKAGES)
			DP.create(ADDONTITLE,'Downloading %s ' % name,'', 'Please Wait')
			lib=os.path.join(PACKAGES, '%s.zip' % zipname)
			try: os.remove(lib)
			except: pass
			downloader.download(themezip, lib, DP)
			time.sleep(2)
			DP.update(0,"", "Installing %s " % name)
			ext = extract.all(lib,HOME,DP)
			percent, errors, error = ext.split('/', 3)
			wiz.setS('buildtheme', theme)
			wiz.log('INSTALLED %s: [ERRORS:%s]' % (percent, errors))
			DP.close()
			if url not in ["fresh", "normal"]: xbmc.executebuiltin("ReloadSkin()"); time.sleep(1); xbmc.executebuiltin("Container.Refresh()") 
		else:
			wiz.LogNotify(ADDONTITLE, 'Theme Install: [COLOR red]Cancelled![/COLOR]')

###########################
###### Misc Functions######
###########################
	
def showHide(ver):
	if ver == '15': wiz.setS('show15', 'true' if SHOW15 == 'false' else 'false')
	elif ver == '16': wiz.setS('show16', 'true' if SHOW16 == 'false' else 'false')
	xbmc.executebuiltin('Container.Refresh()')
	
def percentage(part, whole):
	return 100 * float(part)/float(whole)
	
def createMenu(type, name):
	if type == 'trakt':
		menu_items=[]
		name2 = urllib.quote_plus(name.lower().replace(' ', ''))
		menu_items.append((THEME2 % name,             ' '))
		menu_items.append((THEME2 % 'Save Trakt Data',         'RunPlugin(plugin://%s/?mode=savetrakt&name=%s)' %    (ADDON_ID, name2)))
		menu_items.append((THEME2 % 'Restore Trakt Data',      'RunPlugin(plugin://%s/?mode=restoretrakt&name=%s)' % (ADDON_ID, name2)))
		menu_items.append((THEME2 % 'Clear Trakt Data',        'RunPlugin(plugin://%s/?mode=cleartrakt&name=%s)' %   (ADDON_ID, name2)))
	if type == 'traktaddon':
		menu_items=[]
		name2 = urllib.quote_plus(name.lower().replace(' ', ''))
		menu_items.append((THEME2 % name,             ' '))
		menu_items.append((THEME2 % 'Register Trakt',          'RunPlugin(plugin://%s/?mode=authtrakt&name=%s)' %    (ADDON_ID, name2)))
		menu_items.append((THEME2 % 'Save Trakt Data',         'RunPlugin(plugin://%s/?mode=savetrakt&name=%s)' %    (ADDON_ID, name2)))
		menu_items.append((THEME2 % 'Restore Trakt Data',      'RunPlugin(plugin://%s/?mode=restoretrakt&name=%s)' % (ADDON_ID, name2)))
		menu_items.append((THEME2 % 'Clear Addon Trakt Data',  'RunPlugin(plugin://%s/?mode=addontrakt&name=%s)' %   (ADDON_ID, name2)))
	if type == 'install':
		menu_items=[]
		name2 = urllib.quote_plus(name)
		menu_items.append((THEME2 % name,             ' '))	
		menu_items.append((THEME2 % 'Fresh Install',          'RunPlugin(plugin://%s/?mode=install&name=%s&url=fresh)'  % (ADDON_ID, name2)))
		menu_items.append((THEME2 % 'Normal Install',         'RunPlugin(plugin://%s/?mode=install&name=%s&url=normal)' % (ADDON_ID, name2)))
		menu_items.append((THEME2 % 'Apply guiFix',           'RunPlugin(plugin://%s/?mode=install&name=%s&url=gui)'    % (ADDON_ID, name2)))
	menu_items.append((THEME2 % 'Aftermath Settings', 'RunPlugin(plugin://%s/?mode=settings)' % ADDON_ID))
	return menu_items
	
def viewLogFile():
	log = xbmc.translatePath('special://logpath/kodi.log')
	f = open(log,mode='r'); msg = f.read(); f.close()
	wiz.TextBoxes("%s - kodi.log" % ADDONTITLE, msg)

###########################
###### Fresh Install ######
###########################

def freshStart(install=None):
	if KEEPTRAKT == 'true':
		if TRAKTSAVE == '' or not TRAKTSAVE > str(TODAY):
			if DIALOG.yesno(ADDONTITLE, 'Would you like to save trakt data before doing a fresh install?', nolabel='No Thanks!',yeslabel='Yes, Save Data'):
				traktit.traktIt('update' , 'all')
			wiz.setS('lastsave', str(THREEDAYS))
	if SKIN not in ['skin.confluence', 'skin.estuary']:
		skin = 'skin.estuary' if KODIV >= 17 else 'skin.confluence'
		yes=DIALOG.yesno(ADDONTITLE, "The skin needs to be set back to [COLOR yellow]%s[/COLOR]" % skin[5:], "Before doing a fresh install to clear all Texture files!", "Would you like us to do that for you?", nolabel="No, Thanks", yeslabel="Yes, Swap Skin");
		if yes:	
			skinSwitch.swapSkins(skin)
			while not xbmc.getCondVisibility("Window.isVisible(yesnodialog)"):
				xbmc.sleep(200)
			xbmc.executebuiltin("Action(Left)")
			xbmc.executebuiltin("Action(Select)")
		else: wiz.LogNotify(ADDONTITLE,'Fresh Install: [COLOR red]Cancelled![/COLOR]'); return
	if install: yes_pressed=DIALOG.yesno(ADDONTITLE,"Do you wish to restore your","Kodi configuration to default settings", "Before installing %s?" % install, nolabel='No, Cancel', yeslabel='Yes, Continue')
	else: yes_pressed=DIALOG.yesno(ADDONTITLE,"Do you wish to restore your","Kodi configuration to default settings?", nolabel='No, Cancel', yeslabel='Yes, Continue')
	if yes_pressed:
		xbmcPath=os.path.abspath(HOME)
		DP.create(ADDONTITLE,"Clearing all files and folders:",'', '')
		total_files = sum([len(files) for r, d, files in os.walk(xbmcPath)]); del_file = 0;
		try:
			for root, dirs, files in os.walk(xbmcPath,topdown=True):
				dirs[:] = [d for d in dirs if d not in EXCLUDES]
				for name in files:
					del_file += 1
					fold = root.split('\\')
					x = len(fold)-1
					if name == 'sources.xml' and fold[x] == 'userdata' and KEEPSOURCES == 'true': wiz.log("Keep Sources: %s\\%s" % (root, name))
					elif name == 'favourites.xml' and fold[x] == 'userdata' and KEEPFAVS == 'true': wiz.log("Keep Favourites: %s\\%s" % (root, name))
					elif name == 'profiles.xml' and fold[x] == 'userdata' and KEEPPROFILES == 'true': wiz.log("Keep Profiles: %s\\%s" % (root, name))
					elif name == 'advancedsettings.xml' and fold[x] == 'userdata' and KEEPADVANCED == 'true':  wiz.log("Keep Advanced Settings: %s\\%s" % (root, name))
					elif name == 'kodi.log': wiz.log("Keep kodi.log")
					elif name.endswith('.db'):
						try:os.remove(os.path.join(root,name))
						except: wiz.log('Failed to delete, Purging DB.'); wiz.purgeDb(os.path.join(root,name))
					else:
						DP.update(int(percentage(del_file, total_files)), '', 'File: [COLOR yellow]%s[/COLOR]' % name, '')
						try: os.remove(os.path.join(root,name))
						except: wiz.log("Error removing %s\\%s" % (root, name))
			for root, dirs, files in os.walk(xbmcPath,topdown=True):
				dirs[:] = [d for d in dirs if d not in EXCLUDES]							
				for name in dirs:
					DP.update(100, '', 'Cleaning Up Empty Folder: [COLOR yellow]%s[/COLOR]' % name, '')
					if name not in ["Database","userdata","temp","addons","addon_data"]:
						shutil.rmtree(os.path.join(root,name),ignore_errors=True, onerror=None)
			DP.close()
			wiz.clearS('build')
		except: 
			DIALOG.ok(ADDONTITLE,"Problem found","Your settings has not been changed")
			import traceback
			wiz.log(traceback.format_exc())
			wiz.log("freshstart.main_list NOT removed")
		DP.close()
		if install: 
			DIALOG.ok(ADDONTITLE, "Your current setup for kodi has been cleared!", "Now we will install: %s v%s" % (install, wiz.checkBuild(install,'version')))
			buildWizard(install, 'normal')
		else:
			DIALOG.ok(ADDONTITLE, "The process is complete, you're now back to a fresh Kodi configuration with Aftermath Wizard","Please reboot your system or restart Kodi in order for the changes to be applied.")
			wiz.killxbmc()
	else: wiz.LogNotify(ADDONTITLE,'Fresh Install: [COLOR red]Cancelled![/COLOR]'); xbmc.executebuiltin('Container.Refresh')

############################
###DELETE PACKAGES##########
####THANKS GUYS @ XUNITY####
######MODIFIED BY AFTERMATH#

def clearPackages():
	if os.path.exists(PACKAGES):
		try:	
			for root, dirs, files in os.walk(PACKAGES):
				file_count = 0
				file_count += len(files)
				# Count files and give option to delete
				if file_count > 0:
					if DIALOG.yesno("Delete Package Cache Files", str(file_count) + " files found", "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
						for f in files:	os.unlink(os.path.join(root, f))
						for d in dirs: shutil.rmtree(os.path.join(root, d))
						wiz.LogNotify(ADDONTITLE,'Clear Packages: [COLOR green]Success[/COLOR]!')
				else: wiz.LogNotify(ADDONTITLE,'Clear Packages: [COLOR red]None Found![/COLOR]')
		except: wiz.LogNotify(ADDONTITLE,'Clear Packages: [COLOR red]Error[/COLOR]!')
	else: wiz.LogNotify(ADDONTITLE,'Clear Packages: [COLOR red]None Found![/COLOR]')

#############################
###DELETE CACHE##############
####THANKS GUYS @ XUNITY#####

def clearCache():
	wiz.log('############################################################	   DELETING STANDARD CACHE			 ###############################################################')
	xbmc_cache_path = os.path.join(xbmc.translatePath('special://home'), 'cache')
	if os.path.exists(xbmc_cache_path)==True:	
		for root, dirs, files in os.walk(xbmc_cache_path):
			file_count = 0
			file_count += len(files)
			# Count files and give option to delete
			if file_count > 0:
				if DIALOG.yesno("Delete Cache Files", "%s files found" % str(file_count), "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
					for f in files:
						try: os.unlink(os.path.join(root, f))
						except: pass
					for d in dirs:
						try: shutil.rmtree(os.path.join(root, d))
						except: pass
					wiz.LogNotify(ADDONTITLE,'Clear Cache: [COLOR green]Success![/COLOR]')
			else: pass

	if xbmc.getCondVisibility('system.platform.ATV2'):
		atv2_cache_a = os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'Other')
		for root, dirs, files in os.walk(atv2_cache_a):
			file_count = 0
			file_count += len(files)
			if file_count > 0:
				if DIALOG.yesno("Delete ATV2 Cache Files", "%s files found in 'Other'" % str(file_count), "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
					for f in files: os.unlink(os.path.join(root, f))
					for d in dirs: shutil.rmtree(os.path.join(root, d))
					wiz.LogNotify(ADDONTITLE,'Clear Cache: [COLOR green]Success![/COLOR]')
			else: pass
		atv2_cache_b = os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'LocalAndRental')
		for root, dirs, files in os.walk(atv2_cache_b):
			file_count = 0
			file_count += len(files)
			if file_count > 0:
				if DIALOG.yesno("Delete ATV2 Cache Files", "%s files found in 'LocalAndRental'" % str(file_count), "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
					for f in files: os.unlink(os.path.join(root, f))
					for d in dirs: shutil.rmtree(os.path.join(root, d))
					wiz.LogNotify(ADDONTITLE,'Clear Cache: [COLOR green]Success![/COLOR]')
			else: pass
			
	# Set path to Cydia Archives cache files
	# Set path to What th Furk cache files
	wtf_cache_path = os.path.join(xbmc.translatePath('special://profile/addon_data/plugin.video.whatthefurk/cache'), '')
	if os.path.exists(wtf_cache_path)==True:	
		for root, dirs, files in os.walk(wtf_cache_path):
			file_count = 0
			file_count += len(files)
			# Count files and give option to delete
			if file_count > 0:
				if DIALOG.yesno("Delete WTF Cache Files", "%s files found" % str(file_count), "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
					for f in files: os.unlink(os.path.join(root, f))
					for d in dirs: shutil.rmtree(os.path.join(root, d))
					wiz.LogNotify(ADDONTITLE,'Clear Cache: [COLOR green]Success![/COLOR]')
			else: pass		
			
	# Set path to 4oD cache files
	channel4_cache_path= os.path.join(xbmc.translatePath('special://profile/addon_data/plugin.video.4od/cache'), '')
	if os.path.exists(channel4_cache_path)==True:	
		for root, dirs, files in os.walk(channel4_cache_path):
			file_count = 0
			file_count += len(files)		
			# Count files and give option to delete
			if file_count > 0:	
				if DIALOG.yesno("Delete 4oD Cache Files", "%s files found" % str(file_count), "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
					for f in files: os.unlink(os.path.join(root, f))
					for d in dirs: shutil.rmtree(os.path.join(root, d))
					wiz.LogNotify(ADDONTITLE,'Clear Cache: [COLOR green]Success![/COLOR]')
			else: pass
				
	# Set path to BBC iPlayer cache files
	iplayer_cache_path= os.path.join(xbmc.translatePath('special://profile/addon_data/plugin.video.iplayer/iplayer_http_cache'), '')
	if os.path.exists(iplayer_cache_path)==True:	
		for root, dirs, files in os.walk(iplayer_cache_path):
			file_count = 0
			file_count += len(files)
			# Count files and give option to delete
			if file_count > 0:	
				if DIALOG.yesno("Delete BBC iPlayer Cache Files", "%s files found" % str(file_count), "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
					for f in files: os.unlink(os.path.join(root, f))
					for d in dirs: shutil.rmtree(os.path.join(root, d))
					wiz.LogNotify(ADDONTITLE,'Clear Cache: [COLOR green]Success![/COLOR]')
			else: pass			
				
	# Set path to Simple Downloader cache files
	downloader_cache_path = os.path.join(xbmc.translatePath('special://profile/addon_data/script.module.simple.downloader'), '')
	if os.path.exists(downloader_cache_path)==True:	
		for root, dirs, files in os.walk(downloader_cache_path):
			file_count = 0
			file_count += len(files)
			# Count files and give option to delete
			if file_count > 0:
				if DIALOG.yesno("Delete Simple Downloader Cache Files", "%s files found" % str(file_count), "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
					for f in files: os.unlink(os.path.join(root, f))
					for d in dirs: shutil.rmtree(os.path.join(root, d))
					wiz.LogNotify(ADDONTITLE,'Clear Cache: [COLOR green]Success![/COLOR]')
			else: pass
				
	# Set path to ITV cache files
	itv_cache_path = os.path.join(xbmc.translatePath('special://profile/addon_data/plugin.video.itv/Images'), '')
	if os.path.exists(itv_cache_path)==True:	
		for root, dirs, files in os.walk(itv_cache_path):
			file_count = 0
			file_count += len(files)		
			# Count files and give option to delete
			if file_count > 0:
				if DIALOG.yesno("Delete ITV Cache Files", "%s files found" % str(file_count), "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
					for f in files: os.unlink(os.path.join(root, f))
					for d in dirs: shutil.rmtree(os.path.join(root, d))
					wiz.LogNotify(ADDONTITLE,'Clear Cache: [COLOR green]Success![/COLOR]')
			else: pass

	# Set path to temp cache files
	temp_cache_path = os.path.join(xbmc.translatePath('special://home/temp'), '')
	if os.path.exists(temp_cache_path)==True:	
		for root, dirs, files in os.walk(temp_cache_path):
			file_count = 0
			file_count += len(files)
			# Count files and give option to delete
			if file_count > 0:
				if DIALOG.yesno("Delete TEMP dir Cache Files", "%s files found" % str(file_count), "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove'):
					for f in files: os.unlink(os.path.join(root, f))
					for d in dirs: shutil.rmtree(os.path.join(root, d))
					wiz.LogNotify(ADDONTITLE,'Clear Cache: [COLOR green]Success![/COLOR]')
			else: pass
	
	clearThumb()
	
def clearThumb():
	latest = wiz.latestDB('Textures')
	if DIALOG.yesno(ADDONTITLE, "Would you like to delete the %s and Thumbnails folder?" % latest, "They will repopulate on startup", nolabel='No, Cancel',yeslabel='Yes, Remove'):
		try: wiz.removeFile(os.join(DATABASE, latest))
		except: wiz.log('Failed to delete, Purging DB.'); wiz.purgeDb(latest)
		wiz.removeFolder(THUMBS)
		wiz.killxbmc()
	else: wiz.log('Clear thumbnames cancelled')
	
def purgeDb():
	DB = []; display = []
	for dirpath, dirnames, files in os.walk(HOME):
		for f in fnmatch.filter(files, '*.db'):
			if f != 'Thumbs.db':
				found = os.path.join(dirpath, f)
				DB.append(found)
				dir = found.replace('\\', '/').split('/')
				display.append('(%s) %s' % (dir[len(dir)-2], dir[len(dir)-1]))
	#DB = ['Addons', 'ADSP', 'Epg', 'MyMusic', 'MyVideos', 'Textures', 'TV', 'ViewModes']
	if KODIV >= 16: 
		choice = DIALOG.multiselect("Select DB File to Purge", display)
		if choice == None: wiz.LogNotify("Purge Database", "Cancelled")
		elif len(choice) == 0: wiz.LogNotify("Purge Database", "Cancelled")
		else: 
			for purge in choice: wiz.purgeDb(DB[purge])
	else:
		choice = DIALOG.select("Select DB File to Purge", display)
		if choice == -1: wiz.LogNotify("Purge Database", "Cancelled")
		else: wiz.purgeDb(DB[purge])
	
###########################
## Making the Directory####
###########################

def addDir(display,mode,name=None,url=None,menu=None,overwrite=True,fanart=FANART,icon=ICON, themeit=None):
	u='%s?mode=%s' % (sys.argv[0], urllib.quote_plus(mode))
	if not name == None: u += "&name="+urllib.quote_plus(name)
	if not url == None: u += "&url="+urllib.quote_plus(url)
	ok=True
	if themeit: display = themeit % display
	liz=xbmcgui.ListItem(display, iconImage="DefaultFolder.png", thumbnailImage=icon)
	liz.setInfo( type="Video", infoLabels={ "Title": display, "Plot": ADDONTITLE} )
	liz.setProperty( "Fanart_Image", fanart )
	if not menu == None: liz.addContextMenuItems(menu, replaceItems=overwrite)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok
		
def addFile(display,mode,name=None,url=None,menu=None,overwrite=True,fanart=FANART,icon=ICON, themeit=None):
	u='%s?mode=%s' % (sys.argv[0], urllib.quote_plus(mode))
	if not name == None: u += "&name="+urllib.quote_plus(name)
	if not url == None: u += "&url="+urllib.quote_plus(url)
	ok=True
	if themeit: display = themeit % display
	liz=xbmcgui.ListItem(display, iconImage="DefaultFolder.png", thumbnailImage=icon)
	liz.setInfo( type="Video", infoLabels={ "Title": display, "Plot": ADDONTITLE} )
	liz.setProperty( "Fanart_Image", fanart )
	if not menu == None: liz.addContextMenuItems(menu, replaceItems=overwrite)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	return ok

def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]

		return param


params=get_params()
url=None
name=None
mode=None

try:	 mode=urllib.unquote_plus(params["mode"])
except:  pass
try:	 name=urllib.unquote_plus(params["name"])
except:  pass
try:	 url=urllib.unquote_plus(params["url"])
except:  pass
		
wiz.log('[ Version : %s ] [ Mode : %s] [ Name : %s ] [ Url : %s ]' % (VERSION, mode, name, url))

def setView(content, viewType):
	# set content type so library shows more views and info
	if content:
		xbmcplugin.setContent(int(sys.argv[1]), content)
	if wiz.getS('auto-view')=='true':
		xbmc.executebuiltin("Container.SetViewMode(%s)" % wiz.getS(viewType) )

if   mode==None            : index()

elif mode=='builds'        : buildMenu()
elif mode=='showupdate'    : showHide(name)
elif mode=='viewbuild'     : viewBuild(name)
elif mode=='install'       : buildWizard(name, url)
elif mode=='theme'         : buildWizard(name, mode, url)

elif mode=='maint'         : maintMenu()
elif mode=='clearcache'    : clearCache()
elif mode=='clearpackages' : clearPackages()
elif mode=='clearthumb'    : clearThumb()
elif mode=='freshstart'    : freshStart()
elif mode=='forceupdate'   : wiz.forceUpdate()
elif mode=='forceclose'    : wiz.killxbmc()
elif mode=='uploadlog'     : uploadLog.LogUploader()
elif mode=='viewlog'       : viewLogFile()
elif mode=='purgedb'       : purgeDb()

elif mode=='trakt'         : traktMenu()
elif mode=='savetrakt'     : traktit.traktIt('update',      name)
elif mode=='restoretrakt'  : traktit.traktIt('restore',     name)
elif mode=='addontrakt'    : traktit.traktIt('clearaddon',  name)
elif mode=='cleartrakt'    : traktit.clearSaved(name)
elif mode=='authtrakt'     : traktit.activateTrakt(name)
elif mode=='traktsettings' : wiz.setS('keeptrakt', 'false' if KEEPTRAKT == 'true' else 'true'); xbmc.executebuiltin('Container.Refresh()')

elif mode=='contact'       : wiz.TextBoxes(ADDONTITLE, CONTACT)
elif mode=='settings'      : wiz.openS(); xbmc.executebuiltin('Container.Refresh()')

xbmcplugin.endOfDirectory(int(sys.argv[1]))