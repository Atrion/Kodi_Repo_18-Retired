import zipfile, xbmcaddon, xbmc, uservar
from resources.libs import wizard as wiz

ADDON_ID       = uservar.ADDON_ID
ADDON          = wiz.addonId(ADDON_ID)
KEEPFAVS       = wiz.getS('keepfavourites')
KEEPSOURCES    = wiz.getS('keepsources')
KEEPPROFILES   = wiz.getS('keepprofiles')
KEEPADVANCED   = wiz.getS('keepadvanced')

def all(_in, _out, dp=None):
	if dp: return allWithProgress(_in, _out, dp)
	else: return allNoProgress(_in, _out)

def allNoProgress(_in, _out):
	try:
		zin = zipfile.ZipFile(_in, 'r')
		zin.extractall(_out)
	except Exception, e:
		print str(e)
		return False
	return True

def allWithProgress(_in, _out, dp):
	zin = zipfile.ZipFile(_in,  'r')
	nFiles = float(len(zin.namelist()))
	count = 0; errors = 0; error = '';
	zipit = str(_in).replace('\\', '/').split('/'); zname = zipit[len(zipit)-1].replace('.zip', '')
	try:
		for item in zin.infolist():
			count += 1; update = int(count / nFiles * 100);
			file = str(item).split('/')
			x = len(file)-1
			if file[x] == 'sources.xml' and file[x-1] == 'userdata' and KEEPSOURCES == 'true': dp.update(update, '' ,'Skipping: [COLOR yellow]%s[/COLOR]' % item.filename)
			elif file[x] == 'favourites.xml' and file[x-1] == 'userdata' and KEEPFAVS == 'true': dp.update(update, '' ,'Skipping: [COLOR yellow]%s[/COLOR]' % item.filename)
			elif file[x] == 'profiles.xml' and file[x-1] == 'userdata' and KEEPPROFILES == 'true': dp.update(update, '' ,'Skipping: [COLOR yellow]%s[/COLOR]' % item.filename)
			elif file[x] == 'advancedsettings.xml' and file[x-1] == 'userdata' and KEEPADVANCED == 'true': dp.update(update, '' ,'Skipping: [COLOR yellow]%s[/COLOR]' % item.filename)
			elif file[x] in ["kodi.log", "kodi.old.log", "Thumb.db", ".DS_Store"]: dp.update(update, '' ,'Skipping: [COLOR yellow]%s[/COLOR]' % item.filename)
			else:
				dp.update(update, '[COLOR dodgerblue]%s[/COLOR] [Errors:%s]' % (zname, errors),'Extracting: [COLOR yellow]%s[/COLOR]' % item.filename)
				try:
					zin.extract(item, _out)
				except Exception, e:
					wiz.log('%s / %s' % (e, item.filename))
					errors += 1; error += '%s\n' % e
	except Exception, e:
		wiz.log('%s / %s' % (Exception, e)) 
	if dp.iscanceled(): 
		raise Exception("Canceled")
		dp.close()
	return '%d/%d/%s' % (update, errors, error)