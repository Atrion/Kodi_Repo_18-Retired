orionIndex = -1
for i in range(len(scrapers)):
    if scrapers[i].name == 'Orion':
        orionIndex = i
        break
orionEnabled = False
orionInfo = [10, 11, 12, 13, 14, 4, 3, 16, 17, 0, 0, 0, 0, 0, 0]
if orionIndex >= 0:
    orionEnabled = scrapers[orionIndex]._is_enabled()
    orionInfo = scrapers[orionIndex]()._settings()
    del scrapers[orionIndex]
new_xml.append('\n\n<!-- [ORION/] -->\n\
<setting label="Orion" type="lsep" />\n\
<setting type="sep" />\n\
<setting id="Orion_enabled" type="bool" label="Enabled" default="' + ('true' if orionEnabled else 'false') + '" />\n\
<setting id="Orion_settings" type="action" label="Settings" option="close" action="RunPlugin(plugin://script.module.orion?action=dialogSettings)" subsetting="true" visible="eq(-1,true)" />\n\
<setting id="Orion_info.1" type="enum" label="Info 1" default="' + str(orionInfo[0]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-2,true)" />\n\
<setting id="Orion_info.2" type="enum" label="Info 2" default="' + str(orionInfo[1]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-3,true)" />\n\
<setting id="Orion_info.3" type="enum" label="Info 3" default="' + str(orionInfo[2]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-4,true)" />\n\
<setting id="Orion_info.4" type="enum" label="Info 4" default="' + str(orionInfo[3]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-5,true)" />\n\
<setting id="Orion_info.5" type="enum" label="Info 5" default="' + str(orionInfo[4]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-6,true)" />\n\
<setting id="Orion_info.6" type="enum" label="Info 6" default="' + str(orionInfo[5]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-7,true)" />\n\
<setting id="Orion_info.7" type="enum" label="Info 7" default="' + str(orionInfo[6]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-8,true)" />\n\
<setting id="Orion_info.8" type="enum" label="Info 8" default="' + str(orionInfo[7]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-9,true)" />\n\
<setting id="Orion_info.9" type="enum" label="Info 9" default="' + str(orionInfo[8]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-10,true)" />\n\
<setting id="Orion_info.10" type="enum" label="Info 10" default="' + str(orionInfo[9]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-11,true)" />\n\
<setting id="Orion_info.11" type="enum" label="Info 11" default="' + str(orionInfo[10]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-12,true)" />\n\
<setting id="Orion_info.12" type="enum" label="Info 12" default="' + str(orionInfo[11]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-13,true)" />\n\
<setting id="Orion_info.13" type="enum" label="Info 13" default="' + str(orionInfo[12]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-14,true)" />\n\
<setting id="Orion_info.14" type="enum" label="Info 14" default="' + str(orionInfo[13]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-15,true)" />\n\
<setting id="Orion_info.15" type="enum" label="Info 15" default="' + str(orionInfo[14]) + '" values="None|Stream Provider|Stream Hoster|Torrent Seeds|File Size|Season Pack|Release Edition|Release Name|Uploader Name|Video Quality|Video Codec|Video 3D|Audio Channels|Audio System|Audio Codec|Audio Languages|Orion Popularity|Orion Age" subsetting="true" visible="eq(-16,true)" />\n\
<!-- [/ORION] -->\n\n\
')
