import sys, xbmc, json

try:
    from urlparse import parse_qsl
    from urllib import quote
except:
    from urllib.parse import parse_qsl, quote

if __name__ == '__main__':

    item = sys.listitem

    path = item.getPath()
    plugin = 'plugin://plugin.video.seren/'
    args = path.split(plugin, 1)

    params = dict(parse_qsl(args[1].replace('?', '')))
    action = params.get('action')
    actionArgs = json.loads(params.get('actionArgs'))

    if 'showInfo' in actionArgs:
        actionArgs = quote(json.dumps(actionArgs['showInfo']))
        path = '%s?action=showSeasons&actionArgs=%s' % (plugin, actionArgs)
    else:
        path = path.replace('action=smartPlay', 'action=showSeasons')

    xbmc.executebuiltin('ActivateWindow(Videos,%s)' % path)
