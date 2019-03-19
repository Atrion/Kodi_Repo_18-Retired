import sys
import xbmc

if __name__ == '__main__':
    item = sys.listitem
    message = item.getLabel()
    path = item.getPath()

    if 'action=showSeasons' in path:
        path = path.replace('action=showSeasons', 'action=shufflePlay')

    if 'action=smartPlay' in path:
        path = path.replace('action=smartPlay', 'action=shufflePlay')

    xbmc.executebuiltin('RunPlugin(%s)' % path)
