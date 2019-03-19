import sys, xbmc, json

try:
    from urlparse import parse_qsl
    from urllib import quote
except:
    from urllib.parse import parse_qsl, quote

if __name__ == '__main__':
    item = sys.listitem
    message = item.getLabel()
    path = item.getPath()
    print(path)
    plugin = 'plugin://plugin.video.seren/'
    args = path.split(plugin, 1)

    params = dict(parse_qsl(args[1].replace('?', '')))
    action = params.get('action')
    actionArgs = json.loads(params.get('actionArgs'))

    trakt_object = {}

    if 'episodeInfo' in actionArgs:
        for i in actionArgs['episodeInfo']:
            print(i)
        trakt_object['episodes'] = [{}]
        trakt_object['episodes'][0]['ids'] = {'trakt': actionArgs['episodeInfo']['ids']['trakt']}
        pass

    elif 'seasonInfo' in actionArgs:
        trakt_object['seasons'] = [{}]
        trakt_object['seasons'][0]['ids'] = {'trakt': actionArgs['seasonInfo']['ids']['trakt']}
        pass

    elif 'info' in actionArgs:

        if 'tvshowtitle' in actionArgs['info']:
            trakt_object['shows'] = [{}]
            trakt_object['shows'][0]['ids'] = {'trakt': actionArgs['ids']['trakt']}
            pass

        else:
            trakt_object['movies'] = [{}]
            trakt_object['movies'][0]['ids'] = {'trakt': actionArgs['ids']['trakt']}

    path = 'RunPlugin(%s?action=traktManager&actionArgs=%s&type=episode)' % (plugin, quote(json.dumps(trakt_object)))
    xbmc.executebuiltin(path)
