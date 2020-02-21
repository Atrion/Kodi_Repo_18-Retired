import xbmcaddon; return [(' ORION' if i[0] == 'ORION' else i[0], i[1]) for i in sourceDict] if xbmcaddon.Addon('plugin.video.scrubsv2').getSetting('provider.orion.first') == 'true' else sourceDict
