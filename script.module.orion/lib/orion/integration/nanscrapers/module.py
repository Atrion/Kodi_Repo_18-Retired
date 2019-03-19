orionIndex = -1
for i in range(len(scrapers)):
    if scrapers[i].name == 'Orion':
        orionIndex = i
        break
orionEnabled = False
orionInfo = 1
if orionIndex >= 0:
    orionEnabled = scrapers[orionIndex]._is_enabled()
    orionInfo = scrapers[orionIndex]._settingInfo()
    del scrapers[orionIndex]
new_xml.append('\n\n<!-- [ORION/] -->\n\
<setting label="Orion" type="lsep" />\n\
<setting type="sep" />\n\
<setting id="Orion_enabled" type="bool" label="Enabled" default="' + ('true' if orionEnabled else 'false') + '" />\n\
<setting id="Orion_settings" type="action" label="Settings" option="close" action="RunPlugin(plugin://script.module.orion?action=dialogSettings)" subsetting="true" visible="eq(-1,true)" />\n\
<setting id="Orion_info" type="enum" label="Label" lvalues="None|All|Provider|Popularity|Age|Popularity & Age" default="' + str(orionInfo) + '" subsetting="true" visible="eq(-2,true)" />\n\
<!-- [/ORION] -->\n\n\
')
