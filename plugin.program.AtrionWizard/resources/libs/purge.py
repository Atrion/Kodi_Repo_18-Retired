def purgeDb(name):
	dbfile = name.replace('.db','').translate(None, digits)
	if dbfile not in ['Addons', 'ADSP', 'Epg', 'MyMusic', 'MyVideos', 'Textures', 'TV', 'ViewModes']: return False
	textfile = os.path.join(DATABASE, name)
	if os.path.exists(textfile):
		try:
			textdb = database.connect(textfile)
			textexe = textdb.cursor()
		except Exception, e:
			log(str(e))
			return False
	else: log('%s not found.' % textfile); return False
	dbtables = { 
		'Addons':'addon|addonextra|addonlinkrepo|blacklist|broken|dependencies|diabled|package|repo|system',
		'ADSP':'addons|modes|settings',
		'Epg' :'epg|epgtags|lastepgscan',
		'MyMusic':'epg|epgtags|lastepgscan',		
		'MyVideos':'epg|epgtags|lastepgscan',
		'Textures':'path|sizes|texture',
		'TV':'channelgroups|channels|map_channelgroups_channels',
		'ViewModes':'view',
		}
	tables = dbtables[dbfile].split('|')
	for table in tables:
		textexe.execute("DROP TABLE IF EXISTS %s" % table)
		textexe.execute("VACUUM")
		textdb.commit()
		
	if dbfile == "Addons":
		textexe.execute("""CREATE TABLE addon (id integer primary key, type text,name text, summary text, description text, stars integer,path text, addonID text, icon text, version text, changelog text, fanart text, author text, disclaimer text,minversion text)"""); textdb.commit()
		textexe.execute("""CREATE TABLE addonextra (id integer, key text, value text)"""); textdb.commit()
		textexe.execute("""CREATE TABLE addonlinkrepo (idRepo integer, idAddon integer)"""); textdb.commit()
		textexe.execute("""CREATE TABLE blacklist (id integer primary key, addonID text)"""); textdb.commit()
		textexe.execute("""CREATE TABLE broken (id integer primary key, addonID text, reason text)"""); textdb.commit()
		textexe.execute("""CREATE TABLE dependencies (id integer, addon text, version text, optional boolean)"""); textdb.commit()
		textexe.execute("""CREATE TABLE disabled (id integer primary key, addonID text)"""); textdb.commit()
		textexe.execute("""CREATE TABLE package (id integer primary key, addonID text, filename text, hash text)"""); textdb.commit()
		textexe.execute("""CREATE TABLE repo (id integer primary key, addonID text,checksum text, lastcheck text, version text)"""); textdb.commit()
		textexe.execute("""CREATE TABLE system (id integer primary key, addonID text)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idxAddon ON addon(addonID)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idxAddonExtra ON addonextra(id)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX idxBlack ON blacklist(addonID)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX idxBroken ON broken(addonID)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idxDependencies ON dependencies(id)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX idxDisabled ON disabled(addonID)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX idxPackage ON package(filename)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX ix_addonlinkrepo_1 ON addonlinkrepo ( idAddon, idRepo )"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX ix_addonlinkrepo_2 ON addonlinkrepo ( idRepo, idAddon )"""); textdb.commit()
		
	elif dbfile == "ADSP":
		textexe.execute("""CREATE TABLE addons (idAddon integer primary key, sName varchar(64), sUid varchar(32))"""); textdb.commit()
		textexe.execute("""CREATE TABLE modes (idMode integer primary key, iType integer, iPosition integer, iStreamTypeFlags integer, iBaseType integer, bIsEnabled bool, sOwnIconPath varchar(255), sOverrideIconPath varchar(255), iModeName integer, iModeSetupName integer, iModeHelp integer, iModeDescription integer, sAddonModeName varchar(64), iAddonId integer, iAddonModeNumber integer, bHasSettings bool)"""); textdb.commit()
		textexe.execute("""CREATE TABLE settings (id integer primary key, strPath varchar(255), strFileName varchar(255), MasterStreamTypeSel integer, MasterStreamType integer, MasterBaseType integer, MasterModeId integer)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX idx_mode_iAddonId_iAddonModeNumber on modes(iAddonId, iAddonModeNumber)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX ix_settings ON settings (id)"""); textdb.commit()
		
	elif dbfile == "Epg":
		textexe.execute("""CREATE TABLE epg (idEpg integer primary key, sName varchar(64),sScraperName varchar(32))"""); textdb.commit()
		textexe.execute("""CREATE TABLE epgtags (idBroadcast integer primary key, iBroadcastUid integer, idEpg integer, sTitle varchar(128), sPlotOutline text, sPlot text, sOriginalTitle varchar(128), sCast varchar(255), sDirector varchar(255), sWriter varchar(255), iYear integer, sIMDBNumber varchar(50), sIconPath varchar(255), iStartTime integer, iEndTime integer, iGenreType integer, iGenreSubType integer, sGenre varchar(128), iFirstAired integer, iParentalRating integer, iStarRating integer, bNotify bool, iSeriesId integer, iEpisodeId integer, iEpisodePart integer, sEpisodeName varchar(128), iFlags integer)"""); textdb.commit()
		textexe.execute("""CREATE TABLE lastepgscan (idEpg integer primary key, sLastScan varchar(20))"""); textdb.commit()
		textexe.execute("""CREATE INDEX idx_epg_iEndTime on epgtags(iEndTime)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX idx_epg_idEpg_iStartTime on epgtags(idEpg, iStartTime desc)"""); textdb.commit()
		
	elif dbfile == "Textures":
		textexe.execute("""CREATE TABLE path (id integer primary key, url text, type text, texture text)"""); textdb.commit()
		textexe.execute("""CREATE TABLE sizes (idtexture integer, size integer, width integer, height integer, usecount integer, lastusetime text)"""); textdb.commit()
		textexe.execute("""CREATE TABLE texture (id integer primary key, url text, cachedurl text, imagehash text, lasthashcheck text)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idxPath ON path(url, type)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idxSize ON sizes(idtexture, size)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idxSize2 ON sizes(idtexture, width, height)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idxTexture ON texture(url)"""); textdb.commit()
		textexe.execute("""CREATE TRIGGER textureDelete AFTER delete ON texture FOR EACH ROW BEGIN delete from sizes where sizes.idtexture=old.id; END"""); textdb.commit()
		
	elif dbfile == "TV":
		textexe.execute("""CREATE TABLE channelgroups (idGroup integer primary key,bIsRadio bool, iGroupType integer, sName varchar(64), iLastWatched integer, bIsHidden bool, iPosition integer)"""); textdb.commit()
		textexe.execute("""CREATE TABLE channels (idChannel integer primary key, iUniqueId integer, bIsRadio bool, bIsHidden bool, bIsUserSetIcon bool, bIsUserSetName bool, bIsLocked bool, sIconPath varchar(255), sChannelName varchar(64), bIsVirtual bool, bEPGEnabled bool, sEPGScraper varchar(32), iLastWatched integer,iClientId integer, idEpg integer)"""); textdb.commit()
		textexe.execute("""CREATE TABLE map_channelgroups_channels (idChannel integer, idGroup integer, iChannelNumber integer, iSubChannelNumber integer)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idx_channelgroups_bIsRadio on channelgroups(bIsRadio)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX idx_channels_iClientId_iUniqueId on channels(iClientId, iUniqueId)"""); textdb.commit()
		textexe.execute("""CREATE UNIQUE INDEX idx_idGroup_idChannel on map_channelgroups_channels(idGroup, idChannel)"""); textdb.commit()
	
	elif dbfile == "MyMusic":
		return False
		
	elif dbfile == "MyVideos":
		return False		
		
	elif dbfile == "ViewModes":
		textexe.execute("""CREATE TABLE view (idView integer primary key,window integer,path text,viewMode integer,sortMethod integer,sortOrder integer,sortAttributes integer,skin text)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idxViews ON view(path)"""); textdb.commit()
		textexe.execute("""CREATE INDEX idxViewsWindow ON view(window)"""); textdb.commit()
	log('%s DB Flush Complete' % name)