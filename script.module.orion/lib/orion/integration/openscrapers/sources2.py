return [(' orion' if i[0] == 'orion' else i[0], i[1]) for i in sourceDict] if __addon__.getSetting('provider.orion.first') == 'true' else sourceDict
