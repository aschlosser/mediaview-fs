#!/usr/bin/env python3

import os, os.path, pprint
from xml.dom.minidom import parse

MEDIA_TYPES = {'tvshow':'TV Shows','movie':'Movies'}

class Media:
    def __init__(self, nfo_path):
        self.base = os.path.dirname(nfo_path)
        dom = parse(nfo_path)
        root = (dom.getElementsByTagName('movie') + dom.getElementsByTagName('tvshow'))[0]
        self.type = MEDIA_TYPES[root.tagName]
        self.tags = {}
        self.tags['Title'] = root.getElementsByTagName('title')[0].firstChild.nodeValue
        self.tags['Genre'] = list(map(lambda x: x.firstChild.nodeValue, root.getElementsByTagName('genre')))

def recursive_media_search(rootdir):
    for root, _, files in os.walk(rootdir, topdown=False):
        for file in files:
            if file.endswith('.nfo'):
                try:
                    m = Media(os.path.join(root, file))
                    yield m
                except:
                    pass


if __name__ == '__main__':
    mcol = {}
    for t in MEDIA_TYPES.values():
        mcol[t] = {'byTitle':{}, 'byGenre':{}}
    for m in recursive_media_search('/mnt/deadpool'):
        mcol[m.type]['byTitle'][m.tags['Title']] = m.base
        for g in m.tags['Genre']:
            if not g in mcol[m.type]['byGenre']:
                mcol[m.type]['byGenre'][g] = {}
            mcol[m.type]['byGenre'][g][m.tags['Title']] = m.base
    pprint.pprint(mcol, indent=4, width=200)
